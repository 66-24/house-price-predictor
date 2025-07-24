import subprocess
import time
import dagger
import os
import sys

# Define constants
PYTHON_VERSION = "3.11-slim"
MLFLOW_PORT = 5000
# When binding a service in Dagger, the service name becomes the hostname
MLFLOW_TRACKING_URI = f"http://mlflow_server:{MLFLOW_PORT}"
DOCKERHUB_REPO = "house-price-predictor-service"



async def main():
    """
    Orchestrates the MLOps pipeline using Dagger.
    """
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        # Get the current project directory as a Dagger Directory object
        # This mounts your local project into the Dagger engine
        src = client.host().directory(".")

        # --- Stage 1: Data Processing ---
        print("\n--- Stage 1: Data Processing (Cleaning & Feature Engineering) ---")
        data_processing_output = await data_processing_stage(client, src)
        processed_data_file = data_processing_output["processed_data"]
        preprocessor_file = data_processing_output["preprocessor"]
        print("Data Processing completed. Artifacts ready.")

        # --- Stage 2: Model Training ---
        print("\n--- Stage 2: Model Training ---")
        trained_model_dir = await model_training_stage(client, src, processed_data_file, preprocessor_file)
        print("Model Training completed. Trained model ready.")

        # --- Stage 3: Build and Publish Docker Image ---
        print("\n--- Stage 3: Build and Publish Docker Image ---")
        published_image_ref = await build_and_publish_stage(client, src, trained_model_dir)
        print(f"Docker Image published: {published_image_ref}")

        # --- Stage 4: Image Vulnerability Scan ---
        print("\n--- Stage 4: Image Vulnerability Scan ---")
        await image_vulnerability_scan_stage(client, published_image_ref)
        print("Image Vulnerability Scan completed.")

        print("\n--- MLOps Pipeline Completed Successfully ---")

async def data_processing_stage(client: dagger.Client, src: dagger.Directory) -> dict[str, dagger.File]:
    """
    Performs data cleaning and feature engineering.
    Returns a dictionary containing the processed data file and preprocessor file.
    """
    # Base Python container with project mounted and dependencies installed
    python_base = (
        client.container()
        .from_(f"python:{PYTHON_VERSION}")
        .with_mounted_directory("/house-price-predictor", src)
        # .with_mounted_cache("/root/.cache/pip", client.cache_volume("pip_cache"))
        .with_workdir("/house-price-predictor")
        .with_exec(["python", "-m", "pip", "install", "--upgrade", "pip"])
        .with_exec(["python", "-m", "pip", "install", "-r", "requirements.txt"])
    )
    
    # Run Data Cleaning script
    data_cleaning_container = python_base.with_exec([
        "python", "src/data/run_processing.py",
        "--output-file", "data/processed/cleaned_house_data.csv",
        "--input-file", "data/raw/house_data.csv"
    ])

    # Run Feature Engineering script
    feature_engineering_container = data_cleaning_container.with_exec([
        "python", "src/features/engineer.py",
        "--input", "data/processed/cleaned_house_data.csv",
        "--output", "data/processed/featured_house_data.csv",
        "--preprocessor", "models/preprocessor.pkl"
    ])

    # Get the output files as Dagger File objects
    processed_data_file = feature_engineering_container.file("data/processed/featured_house_data.csv")
    preprocessor_file = feature_engineering_container.file("models/preprocessor.pkl")

    # Optional: Export to host for local inspection (uncomment if needed)
    # await processed_data_file.export("dagger_output/featured_house_data.csv")
    # await preprocessor_file.export("dagger_output/preprocessor.pkl")

    return {"processed_data": processed_data_file, "preprocessor": preprocessor_file}

async def model_training_stage(
    client: dagger.Client,
    src: dagger.Directory,
    processed_data_file: dagger.File,
    preprocessor_file: dagger.File
) -> dagger.Directory:
    """
    Trains the machine learning model, using MLflow for tracking.
    Returns the directory containing the trained model.
    """
    # Base Python container with project mounted and dependencies installed
    # python_base = (
    #     client.container()
    #     .from_(f"python:{PYTHON_VERSION}")
    #     .with_mounted_directory("/app", src)
    #     .with_workdir("/app")
    #     .with_exec(["python", "-m", "pip", "install", "--upgrade", "pip"])
    #     .with_exec(["pip", "install", "-r", "requirements.txt"])
    # )

    python_base = (
        client.container()
          .from_(f"python:{PYTHON_VERSION}")
          # mount your code under its real project name so any root‑checks pass
          .with_mounted_directory("/house-price-predictor", src)
          .with_workdir("/house-price-predictor")
          # cache pip downloads between runs
        #   .with_mounted_cache("/root/.cache/pip", client.cache_volume("pip_cache"))
          # always drive pip via Python to guarantee the right interpreter
          .with_exec(["python", "-m", "pip", "install", "--upgrade", "pip"])
          .with_exec(["python", "-m", "pip", "install", "-r", "requirements.txt"])
    )

    # Mount processed data and preprocessor from previous stage into the container
    training_container = (
        python_base
        .with_file("data/processed/featured_house_data.csv", processed_data_file)
        .with_file("models/preprocessor.pkl", preprocessor_file)
    )

    # Define MLflow service container
    mlflow_service = (
        client.container()
        .from_("ghcr.io/mlflow/mlflow:latest")
        .with_exposed_port(MLFLOW_PORT)
        .with_mounted_cache("/root/.cache/mlflow", client.cache_volume("mlflow_cache"))
        .as_service(
            args = [
            "mlflow", "server",
            "--host", "0.0.0.0",
            "--backend-store-uri", "sqlite:///mlflow.db",
            "--default-artifact-root", "/tmp/mlruns"
        ])
    )

    # mlflow_service = mlflow_container.as_service()

    # Run Model Training script, binding to the MLflow service
    training_result = (
        training_container
        .with_service_binding("mlflow_server", mlflow_service) # Bind the service by name
        .with_env_variable("MLFLOW_TRACKING_URI", MLFLOW_TRACKING_URI) # Set tracking URI for the script
        .with_exec([
            "python", "src/models/train_model.py",
            "--config", "configs/model_config.yaml",
            "--data", "data/processed/featured_house_data.csv",
            "--models-dir", "models",
            "--mlflow-tracking-uri", MLFLOW_TRACKING_URI # Pass to script as well
        ])
    )

    # Get the directory containing the trained model
    trained_model_dir = training_result.directory("models/trained")

    # Optional: Export to host for local inspection (uncomment if needed)
    # await trained_model_dir.export("dagger_output/trained_model")

    return trained_model_dir

async def build_and_publish_stage(
    client: dagger.Client,
    src: dagger.Directory,
    trained_model_dir: dagger.Directory
) -> str: # Returns the published image reference string
    """
    Builds the Docker image for the prediction service, runs a health check,
    and publishes it to Docker Hub.
    """
    # Get necessary files/directories from the source context for Docker build
    dockerfile = src.file("Dockerfile")
    src_api_dir = src.directory("src/api")
    configs_dir = src.directory("configs")
    data_raw_dir = src.directory("data/raw") # Assuming Dockerfile copies raw data

    # Get Docker Hub credentials from host environment variables
    # These will be passed as Dagger Secrets for security
    dockerhub_username = os.environ.get("DOCKERHUB_USERNAME")
    dockerhub_token = os.environ.get("DOCKERHUB_TOKEN")

    if not dockerhub_username or not dockerhub_token:
        raise ValueError("DOCKERHUB_USERNAME and DOCKERHUB_TOKEN environment variables must be set.")

    # Create Dagger Secret objects for credentials
    dockerhub_username_secret = client.set_secret("DOCKERHUB_USERNAME", dockerhub_username)
    dockerhub_token_secret = client.set_secret("DOCKERHUB_TOKEN", dockerhub_token)

    # Get short GIT SHA for tagging
    # RuntimeError: git failed: fatal: detected dubious ownership in repository at '/app'
    # To add an exception for this directory, call:
    # 	git config --global --add safe.directory /app

    full_sha = await get_full_sha()
    git_sha_short = full_sha[:7]

    image_sha_tag = f"{dockerhub_username}/{DOCKERHUB_REPO}:{git_sha_short}"
    image_latest_tag = f"{dockerhub_username}/{DOCKERHUB_REPO}:latest"

    # Prepare the build context for the Dockerfile
    # This includes all directories/files that the Dockerfile might COPY from the context
    build_context = client.directory() \
        .with_directory("src/api", src_api_dir) \
        .with_directory("models/trained", trained_model_dir) \
        .with_directory("configs", configs_dir) \
        .with_directory("data/raw", data_raw_dir) \
        .with_file("Dockerfile", dockerfile) \
        .with_file("requirements.txt", src.file("requirements.txt")) 

    # Build the Docker image
    print(f"Building Docker image: {image_sha_tag}")
    built_image = await client.container().build(
        context=build_context,
        dockerfile="Dockerfile", # Path to Dockerfile within the build context
        # If your Dockerfile uses ARG, pass them here:
        # build_args=[
        #     dagger.BuildArg(name="GIT_SHA_SHORT", value=git_sha_short),
        #     # ... other build args
        # ]
        build_args=[
            dagger.BuildArg("CACHEBUST", str(time.time()))],
    )

    # Health check: Run the service and then curl it
    print("Running health check on the built image...")
    service_container = (
        
        built_image
        .with_exposed_port(8000)
        # Use insecure_root_capabilities if the app needs root for binding low ports etc.
        # Or ensure the app runs as a non-root user and binds to a higher port.
        .as_service(
            args=["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"], 
            insecure_root_capabilities=True)
    )

    # Use a separate container to curl the service
    health_check_result = await (
        client.container()
        .from_("alpine/curl")
        .with_service_binding("app_service", service_container) # Bind the app service
        .with_exec(["sh", "-c", "sleep 10 && curl -f http://app_service:8000/health"]) # Wait and curl
        .stdout()
    )
    print(f"Health check output: {health_check_result.strip()}")
    password_secret = client.set_secret("dockerhub_token", os.getenv("DOCKERHUB_TOKEN"))
    
    built_image = built_image.with_registry_auth (
        "docker.io",
         os.getenv("DOCKERHUB_USERNAME"),
        password_secret
    )

    # Publish the image with both SHA and latest tags
    print(f"Publishing image {image_sha_tag} and {image_latest_tag}...")
    tags = [image_sha_tag, image_latest_tag]
    published = [ await built_image.publish(tag) for tag in tags]

    return published[0]  # Return the first tag (SHA tag) as the reference

async def get_full_sha():
    # Spawn git in a truly non‑blocking way
    # RuntimeError: git failed: fatal: detected dubious ownership in repository at '/app'
    # To add an exception for this directory, call:
    # 	git config --global --add safe.directory /app
    proc = await asyncio.create_subprocess_exec(
        "git", "-c", f"safe.directory={os.getcwd()}", "rev-parse", "HEAD",
        cwd=os.getcwd(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"git failed: {stderr.decode().strip()}")
    return stdout.decode().strip()

async def image_vulnerability_scan_stage(client: dagger.Client, image_ref: str):
    """
    Scans the published Docker image for vulnerabilities using Trivy.
    """
    print(f"Scanning image: {image_ref}")
    trivy_container = (
        client.container()
        .from_("aquasec/trivy:latest")
        # Mount Docker socket if Trivy needs to access local Docker daemon (often not needed for remote images)
        # .with_unix_socket("/var/run/docker.sock", client.host().unix_socket("/var/run/docker.sock"))
        .with_exec(["trivy", "image", "--severity", "HIGH,CRITICAL", image_ref])
    )
    scan_output = await trivy_container.stdout()
    print(scan_output)
    # Note: Trivy's exit code is not directly propagated here if it's run via with_exec.
    # If you want to fail the pipeline on vulnerabilities, you'd parse scan_output
    # and raise an exception if critical vulnerabilities are found.
    # For now, it just prints the report.

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())