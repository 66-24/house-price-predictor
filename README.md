# 🏠 House Price Predictor – An MLOps Learning Project

Welcome to the **House Price Predictor** project! This is a real-world, end-to-end MLOps use case designed to help you master the art of building and operationalizing machine learning pipelines.

You'll start from raw data and move through data preprocessing, feature engineering, experimentation, model tracking with MLflow, and optionally using Jupyter for exploration – all while applying industry-grade tooling.

> 🚀 **Want to master MLOps from scratch?**  
Check out the [MLOps Bootcamp at School of DevOps](https://schoolofdevops.com) to level up your skills.

---

## 📦 Project Structure

```
house-price-predictor/
├── configs/                # YAML-based configuration for models
├── data/                   # Raw and processed datasets
├── deployment/
│   └── mlflow/             # Docker Compose setup for MLflow
├── models/                 # Trained models and preprocessors
├── notebooks/              # Optional Jupyter notebooks for experimentation
├── src/
│   ├── data/               # Data cleaning and preprocessing scripts
│   ├── features/           # Feature engineering pipeline
│   ├── models/             # Model training and evaluation
├── requirements.txt        # Python dependencies
└── README.md               # You’re here!
```

---

## 🛠️ Setting up a Learning / Development Environment

To begin, ensure the following tools are installed on your system:

- [Python 3.11](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [Visual Studio Code](https://code.visualstudio.com/) or your preferred editor
- [UV – Python package and environment manager](https://github.com/astral-sh/uv)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) **or** [Podman Desktop](https://podman-desktop.io/)

---

## 🚀 Preparing Your Environment

1. **Fork this repo** on GitHub.

2. **Clone your forked copy:**

   ```bash
   # Replace xxxxxx with your GitHub username or org
   git clone https://github.com/xxxxxx/house-price-predictor.git
   cd house-price-predictor
   ```

3. **Setup Python Virtual Environment using UV:**

   ```bash
   uv venv --python python3.11
   source .venv/bin/activate
   ```

4. **Install dependencies:**

   ```bash
   uv pip install -r requirements.txt
   ```

---

## 📊 Set up MLflow for Experiment Tracking

To track experiments and model runs:

```bash
cd deployment/mlflow
docker compose -f mlflow-docker-compose.yml up -d
docker compose ps
```

> 🐧 **Using Podman?** Use this instead:

```bash
podman compose -f mlflow-docker-compose.yml up -d
podman compose ps
```

Access the MLflow UI at [http://localhost:5555](http://localhost:5555)

---

## 📒 Using JupyterLab (Optional)

If you prefer an interactive experience, launch JupyterLab with:

```bash
uv python -m jupyterlab
# or
python -m jupyterlab
```

---

## 🔁 Model Workflow

### 🧹 Step 1: Data Processing

Clean and preprocess the raw housing dataset:

```bash
python src/data/run_processing.py   --input data/raw/house_data.csv   --output data/processed/cleaned_house_data.csv
```

---

### 🧠 Step 2: Feature Engineering

Apply transformations and generate features:

```bash
python src/features/engineer.py   --input data/processed/cleaned_house_data.csv   --output data/processed/featured_house_data.csv   --preprocessor models/trained/preprocessor.pkl
```

---

### 📈 Step 3: Modeling & Experimentation

Train your model and log everything to MLflow:

```bash
python src/models/train_model.py   --config configs/model_config.yaml   --data data/processed/featured_house_data.csv   --models-dir models   --mlflow-tracking-uri http://localhost:5555
```

---

### 🐳 Docker Image Naming Convention

To avoid issues with Docker reusing incorrect layers when building images for different services, this project uses unique image names for each service rather than relying solely on tags within a single repository.

- **FastAPI Backend Service:** The Docker image for the FastAPI backend is named:
    `[your-docker-id]/house-price-predictor-service`

- **Streamlit Frontend Service:** The Docker image for the Streamlit frontend is named:
    `[your-docker-id]/house-price-predictor-ui`

This convention ensures that Docker treats each service's image as distinct, preventing build and caching conflicts that can arise when multiple services share the same base image name with only different tags.

### 🛠️ Recovery Steps for Docker Build Issues

If you encounter persistent issues with Docker reusing old layers or unexpected behavior after builds, you can try the following recovery steps:

1. **Clear Docker Build Cache:**

    ```bash
    docker builder prune --all
    ```

2. **Comprehensive Docker System Cleanup:** (Use with caution, this removes all unused Docker data)

    ```bash
    docker system prune --all --volumes --force
    ```

3. **Delete Remote Repositories (if applicable):** If you have pushed images with problematic layers to Docker Hub or another registry, you might need to manually delete the affected repositories from the registry's web interface. To do this on Docker Hub, navigate to each service's repository, then go to **Settings**, and you will find the delete option there. This ensures that `docker compose up` or `docker pull` commands do not fetch the old, problematic images.

---

## Dagger CI Pipeline Setup

The Dagger pipeline runs within a carefully configured, self-contained Docker environment to ensure consistent and secure execution. This is necessary because Dagger is not directly compatible with the Nix-based `devenv` shell. The `devenv` setup is used only as a convenient wrapper for scripts that manage this containerized workflow.

### The `dagger-runner` Environment

All pipeline logic executes inside the `dagger-runner` container, built from `Dockerfile.dagger-runner`. This Dockerfile is specifically crafted to create a secure Docker-in-Docker environment for a non-root user. Here is how it works:

1. **Docker CLI Installation**: The `docker-ce-cli` package is installed by the `root` user from Docker's official repository. This is only the first step and is not sufficient on its own.

2. **Non-Root User and Path**: For security, the container switches to a non-root user named `dockeruser`. After the switch, the container's `PATH` is explicitly updated to include `/usr/bin`, ensuring the `docker` executable is available to this new user.

3. **Docker Socket Permissions (GID Matching)**: The most critical piece is granting the `dockeruser` permission to use the host's Docker socket. This is achieved by matching the group ID (GID):
    - The `devenv script dagger_build_runner_image` command dynamically gets the GID of the `docker` group from the host machine.
    - This GID is passed into the `docker build` process as a build argument.
    - The Dockerfile then creates a `docker` group inside the container with that specific GID and adds `dockeruser` to it.

This GID matching gives the non-root `dockeruser` the exact permissions required to interact with the mounted Docker socket, creating a secure and functional Docker-in-Docker setup.

### Dagger Pipeline Internals

When the pipeline runs, Dagger performs several actions to ensure security and efficiency:

- **Secret Management**: When publishing the Docker image, credentials like `DOCKERHUB_TOKEN` are passed to Dagger as secrets. Dagger ensures these secrets are encrypted before being transmitted to the engine and only makes them available to the specific commands that need them. They are never stored in the final image or logs.

- **Efficient Image Pushing**: Before uploading an image layer, Dagger first sends a `HEAD` request to the container registry (e.g., Docker Hub). This checks if the layer with the same digest already exists. If it does, Dagger skips the upload for that layer, saving significant time and bandwidth.

### Running and Debugging the Pipeline

After entering the development environment with `devenv shell`, the custom scripts defined in `devenv.nix` are directly available as commands.

#### Building and Running

1. **Build the Runner Image**: First, build the `dagger-runner` container image. This only needs to be done once, or whenever you change `Dockerfile.dagger-runner`.

    ```bash
    dagger_build_runner_image
    ```

2. **Execute the Pipeline**: Run the entire MLOps pipeline. This command starts the `dagger-runner` container and executes the `dagger_pipeline.py` script inside it. The underlying `run_dagger_pipeline.sh` script is configured to output logs in plain text via the `--progress=plain` flag.

    ```bash
    dagger_run_pipeline
    ```

#### Viewing Logs

- **Tailing Runner Logs**: The `run_dagger_pipeline.sh` script runs the container in the foreground, so all output is streamed directly to your terminal. If you were to modify it to run in detached mode (`-d`), you could tail the logs using the container name specified in the script (`dagger-runner`):

    ```bash
    docker logs -f dagger-runner
    ```

- **Dagger Engine Tracing**: The `run_dagger_pipeline.sh` script correctly configures the Dagger engine to export OpenTelemetry traces on port `6060`. While traces are generated, we have not yet successfully configured a local Jaeger instance to consume and visualize them. For a reliable and out-of-the-box observability solution, the recommended approach is to use [Dagger Cloud](https://dagger.cloud/).

---

## Docker Compose Notes

Here are some important notes regarding the `docker-compose.yaml` configuration:

- **Environment Variable Overrides:** Docker Compose uses `.env` files by default for environment variable overrides. Shell variables will take precedence over those defined in `.env` files.
  - To specify a different environment file, use: `docker compose --env-file .env_dev up`

- **Viewing Substituted Configuration:** To see the Docker Compose file after all variable substitutions have been applied, you can use:

    ```bash
    docker compose config
    ```

- **Build Section in Production:** The `build` section in `docker-compose.yaml` is primarily for local development. It can cause issues with image naming if not handled carefully, as it might build images with invalid names locally (e.g., `${DOCKER_USER_ID}:${SERVICE_VERSION}`). For production deployments, it's generally recommended to remove the `build` section from your compose file and instead use pre-built images from a registry. For this reason, it's a good practice to construct the full image URL (including the registry and repository) directly within your `.env_xxxx` files for different environments.

---

## Building FastAPI and Streamlit

🐉💣 **Important Note on Docker Compose and Image Layers** 💣🐉

**What NOT to do:** Initially, this project attempted to use a single base image name (e.g., `[your-docker-id]/house-price-predictor`) and differentiate services solely by tags (e.g., `house-price-predictor:service-latest` and `house-price-predictor:ui-latest`).

**What happens if you do:** Docker's caching mechanism can get confused when multiple services share the same base image name, even with different tags. This often leads to Docker reusing incorrect layers, resulting in both services running the *same* application (e.g., both the backend and UI containers might end up running the Streamlit frontend).

Here's an example of what you might see in your Docker Compose logs if this issue occurs, where both `house-price-predictor-service-1` and `house-price-predictor-ui-1` are running the Streamlit UI:

```
[+] Running 4/4
 ✔ house-price-predictor-ui                                         Built                                                                                                                                                                                                                                                                      0.0s
 ✔ house-price-predictor-service                                    Built                                                                                                                                                                                                                                                                      0.0s
 ✔ Container house-price-predictor-house-price-predictor-service-1  Recreated                                                                                                                                                                                                                                                                  0.0s
 ✔ Container house-price-predictor-house-price-predictor-ui-1       Recreated                                                                                                                                                                                                                                                                  0.0s
Attaching to house-price-predictor-service-1, house-price-predictor-ui-1
house-price-predictor-service-1  | 
house-price-predictor-service-1  | Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
house-price-predictor-service-1  | 
house-price-predictor-service-1  | 
house-price-predictor-service-1  |   You can now view your Streamlit app in your browser.
house-price-predictor-service-1  | 
house-price-predictor-service-1  |   URL: http://0.0.0.0:8501
house-price-predictor-service-1  | 
house-price-predictor-ui-1       | 
house-price-predictor-ui-1       | Collecting usage statistics. To deactivate, set browser.gatherUsageStats to false.
house-price-predictor-ui-1       | 
house-price-predictor-ui-1       | 
house-price-predictor-ui-1       |   You can now view your Streamlit app in your browser.
house-price-predictor-ui-1       | 
house-price-predictor-ui-1       |   URL: http://0.0.0.0:8501
house-price-predictor-ui-1       |
```

**To mitigate this**, we've adopted unique image names for each service (`house-price-predictor-service` and `house-price-predictor-ui`). If you encounter issues with stale layers, consider using `docker compose build --no-cache` or `docker system prune -a` (use with caution as this removes all unused Docker data) to ensure a clean build.

The code for both the apps are available in `src/api` and `streamlit_app` already. To build and launch these apps

- Add a  `Dockerfile` in the root of the source code for building FastAPI  
- Add `streamlit_app/Dockerfile` to package and build the Streamlit app  
- Add `docker-compose.yaml` in the root path to launch both these apps. be sure to provide `API_URL=http://fastapi:8000` in the streamlit app's environment.

Once you have launched both the apps, you should be able to access streamlit web ui and make predictions.

You could also test predictions with FastAPI directly using `./make.py test`.  
[make.py](make.py) is used to make it easier to run Docker commands to interact with House Price Predictor FastAPI app.
> `Makefile` uses tabs (not spaces) and I found this made it harder to use. My VSCode setup uses spaces instead of tabs!

```bash
curl -X POST "http://localhost:8000/predict" \
-H "Content-Type: application/json" \
-d '{
  "sqft": 1500,
  "bedrooms": 3,
  "bathrooms": 2,
  "location": "suburban",
  "year_built": 2000,
  "condition": fair
}'

```

Be sure to replace `http://localhost:8000/predict` with actual endpoint based on where its running.

## Errors with Joblib

The version of the `joblib` library in the Docker files should match the version used to create the model `pkl` files.

Run `pip list` to get a list of all the installed packages and match versions against requirements.txt

```bash
/usr/local/lib/python3.11/site-packages/sklearn/base.py:318: UserWarning: Trying to unpickle estimator DecisionTreeRegressor from version 1.6.1 when using version 1.2.2. This might lead to breaking code or invalid results. Use at your own risk. For more info please refer to:
https://scikit-learn.org/stable/model_persistence.html#security-maintainability-limitations
  warnings.warn(
Traceback (most recent call last):
  File "/app/inference.py", line 11, in <module>
    model = joblib.load(MODEL_PATH)
            ^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/joblib/numpy_pickle.py", line 658, in load
    obj = _unpickle(fobj, filename, mmap_mode)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/joblib/numpy_pickle.py", line 577, in _unpickle
    obj = unpickler.load()
          ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/pickle.py", line 1213, in load
    dispatch[key[0]](self)
  File "/usr/local/lib/python3.11/site-packages/joblib/numpy_pickle.py", line 415, in load_build
    self.stack.append(array_wrapper.read(self))
                      ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/joblib/numpy_pickle.py", line 252, in read
    array = self.read_array(unpickler)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/joblib/numpy_pickle.py", line 152, in read_array
    array = pickle.load(unpickler.file_handle)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ModuleNotFoundError: No module named 'numpy._core'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/bin/uvicorn", line 8, in <module>
    sys.exit(main())
             ^^^^^^
  File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1442, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1363, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/click/core.py", line 1226, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/click/core.py", line 794, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/uvicorn/main.py", line 410, in main
    run(
  File "/usr/local/lib/python3.11/site-packages/uvicorn/main.py", line 578, in run
    server.run()
  File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 61, in run
    return asyncio.run(self.serve(sockets=sockets))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/uvicorn/server.py", line 68, in serve
    config.load()
  File "/usr/local/lib/python3.11/site-packages/uvicorn/config.py", line 473, in load
    self.loaded_app = import_from_string(self.app)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/site-packages/uvicorn/importer.py", line 21, in import_from_string
    module = importlib.import_module(module_str)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1204, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1176, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1147, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 690, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 940, in exec_module
  File "<frozen importlib._bootstrap>", line 241, in _call_with_frames_removed
  File "/app/main.py", line 3, in <module>
    from inference import predict_price, batch_predict
  File "/app/inference.py", line 14, in <module>
    raise RuntimeError(f"Error loading model or preprocessor: {str(e)}")
RuntimeError: Error loading model or preprocessor: No module named 'numpy._core'
```

## 🧠 Learn More About MLOps

This project is part of the [**MLOps Bootcamp**](https://schoolofdevops.com) at School of DevOps, where you'll learn how to:

- Build and track ML pipelines
- Containerize and deploy models
- Automate training workflows using GitHub Actions or Argo Workflows
- Apply DevOps principles to Machine Learning systems

🔗 [Get Started with MLOps →](https://schoolofdevops.com)

---

## 🤝 Contributing

We welcome contributions, issues, and suggestions to make this project even better. Feel free to fork, explore, and raise PRs!

---

### Using Devenv

#### List all installed python packages

```bash
pip list
```

Happy Learning!  
— Team **School of DevOps**
