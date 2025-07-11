#!/usr/bin/env python3
import typer
import subprocess

app = typer.Typer()

IMAGE_NAME = "dataflow/house-price-predictor"
TAG = "v1"
PORT = 9999

def run(cmd):
    print(f"$ {cmd}")
    subprocess.run(cmd, shell=True, check=True)

@app.command()
def build(tag: str = TAG):
    """Build Docker image"""
    #TODO: $(git rev-parse --short HEAD) for each build
    # --no-cache to rebuild image
    run(f"docker build  -t {IMAGE_NAME}:{tag} .")

@app.command()
def delete():
    """Delete all images for the repo"""
    run(f"docker rmi -f $(docker images -q --filter=reference='{IMAGE_NAME}:*')")

@app.command()
def cleanup():
    """Delete all but latest images"""
    cmd = (
        f"docker images --format '{{{{.Repository}}}} {{{{.Tag}}}} {{{{.ID}}}}' | "
        f"grep '^{IMAGE_NAME} ' | grep -v ' ${TAG}' | awk '{{print $$3}}' | xargs -r docker rmi"
    )
    run(cmd)

@app.command(name="run-container")
def run_container(port: int = PORT, tag: str = TAG):
    """Run container"""
    run(f"docker run --rm -p {port}:8000 {IMAGE_NAME}:{tag}")

@app.command()
def test(port: int = PORT):
    """Test prediction endpoint"""
    data = '{"sqft":1500,"bedrooms":3,"bathrooms":2,"location":"suburban","year_built":2005,"condition":"Good"}'
    run(f"curl -X POST http://localhost:{port}/predict -H 'Content-Type: application/json' -d '{data}'")

@app.command()
def stop_containers():
    """Stop running containers based on the image"""
    cmd = f"docker ps --filter ancestor={IMAGE_NAME}:{TAG} -q"
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    container_ids = [cid for cid in result.stdout.strip().split('\n') if cid]

    if not container_ids:
        print("No running containers to stop.")
        return

    stop_cmd = "docker stop " + " ".join(container_ids)
    print(f"$ {stop_cmd}")
    subprocess.run(stop_cmd, shell=True, check=True)


if __name__ == "__main__":
    app()
