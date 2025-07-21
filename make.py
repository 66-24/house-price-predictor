#!/usr/bin/env python3
import typer
import subprocess
from datetime import datetime
import time
import os

app = typer.Typer()

# Get DOCKER_USERID from environment
docker_userid = os.getenv("DOCKER_USERID")
if not docker_userid:
    print("Error: DOCKER_USERID environment variable not set.")
    raise typer.Exit(code=1)

IMAGE_NAME = f"{docker_userid}/house-price-predictor/house-price-predictor-service"
VERSION = "1.0.0"
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
def build(
    version: str = VERSION,
    team: str = "devops",
    author: str = typer.Option(None, help="Author of the image. Defaults to git user.name."),
    push: bool = typer.Option(False, "--push", help="Push the image to the repository.")
):
    """Build Docker image with all required ARGS and optionally push to a repository."""
    if author is None:
        try:
            author = run("git config --get user.name", capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            author = "Unknown"

    git_sha = run("git rev-parse --short HEAD", capture_output=True)
    build_date = datetime.utcnow().isoformat() + "Z"
    source_date_epoch = str(int(time.time()))

    build_args = {
        "SOURCE_DATE_EPOCH": source_date_epoch,
        "BUILD_DATE": build_date,
        "AUTHOR": author,
        "VERSION": version,
        "GIT_SHA_SHORT": git_sha,
        "TEAM": team,
        "IMAGE_NAME": IMAGE_NAME,
    }

    build_args_str = " ".join([f'--build-arg {k}="{v}"' for k, v in build_args.items()])

    tags = [
        f"{IMAGE_NAME}:v{version}",
        f"{IMAGE_NAME}:{git_sha}",
        f"{IMAGE_NAME}:latest",
        f"{IMAGE_NAME}:{team}"
    ]
    tag_args = " ".join([f"-t {t}" for t in tags])

    build_cmd = f"docker build {tag_args} {build_args_str} ."
    print(f"Running build command:\n{build_cmd}")
    run(build_cmd)

    if push:
        print("\nPushing images...")
        for t in tags:
            run(f"docker push {t}")
        print("Images pushed successfully.")


@app.command()
def delete():
    """Delete all images for the repo"""
    run(f"docker rmi -f $(docker images -q --filter=reference='{IMAGE_NAME}:*')")

@app.command()
def cleanup():
    """Delete all but latest images"""
    cmd = (
        f"docker images --format '{{{{.Repository}}}} {{{{.Tag}}}} {{{{.ID}}}}' | "
        f"grep '^{IMAGE_NAME} ' | grep -v ' latest' | awk '{{print $3}}' | xargs -r docker rmi"
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
