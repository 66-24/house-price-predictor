#!/usr/bin/env python3
import typer
import subprocess
from datetime import datetime
import time

app = typer.Typer()

IMAGE_NAME = "dataflow/house-price-predictor"
# TODO: Extract from pom.xml
TAG = "1.0.0-SNAPSHOT"

PORT = 9999

def run(cmd: str, capture_output: bool = False) -> str | None:
    # print(f"$ {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        capture_output=capture_output
    )
    return result.stdout.strip() if capture_output else None



@app.command()
def build(tag: str = TAG, team_name: str = "devops"):
    """Build Docker image with version, SHA, team tag, and latest"""
    git_sha = run("git rev-parse --short HEAD", capture_output=True)
    build_date = datetime.utcnow().isoformat() + "Z"
    source_date_epoch = str(int(time.time()))

    tags = [
        f"{IMAGE_NAME}:v{tag}",           # e.g. v1.0.0
        f"{IMAGE_NAME}:{git_sha}",        # e.g. ae91f3a
        f"{IMAGE_NAME}:latest",
        f"{IMAGE_NAME}:{team_name}"       # e.g. devops
    ]

    tag_args = ' '.join(f"-t {t}" for t in tags)
    run(
        f"docker build {tag_args} "
        f"--build-arg TEAM_NAME={team_name} "
        f"--build-arg BUILD_DATE={build_date} "
        f"--build-arg SOURCE_DATE_EPOCH={source_date_epoch} ."
    )

@app.command()
def delete():
    """Delete all images for the repo"""
    run(f"docker rmi -f $(docker images -q --filter=reference='{IMAGE_NAME}:*')")

@app.command()
def cleanup():
    """Delete all but latest images"""
    cmd = (
        f"docker images --format '{{{{.Repository}}}} {{{{.Tag}}}} {{{{.ID}}}}' | "
        f"grep '^{IMAGE_NAME} ' | grep -v ' latest' | awk '{{print $$3}}' | xargs -r docker rmi"
    )
    run(cmd)

@app.command(name="run-container")
def run_container(port: int = PORT, tag: str = "latest"):
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
    cmd = f"docker ps --filter ancestor={IMAGE_NAME} -q"
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    container_ids = [cid for cid in result.stdout.strip().split('\n') if cid]

    if not container_ids:
        print("No running containers to stop.")
        return

    stop_cmd = "docker stop " + " ".join(container_ids)
    print(f"$ {stop_cmd}")
    subprocess.run(stop_cmd, shell=True, check=True)

@app.command()
def list():
    """Lists versions of the image with tags and build time"""
    cmd = (
        f"docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.ID}}}}' | "
        f"grep '^{IMAGE_NAME}:' | sort | uniq | "
        "awk '{tags[$2] = tags[$2] \" \" $1} "
        "END {for (id in tags) print id, tags[id]}' | "
        "while read id tags; do "
        f"created=$(docker inspect --format='{{{{.Created}}}}' $id); "
        "printf \"%s\\t%s\\t%s\\n\" \"$id\" \"$tags\" \"$created\"; "
        "done | column -t -s $'\\t'"
    )
    run(cmd)





if __name__ == "__main__":
    app()
