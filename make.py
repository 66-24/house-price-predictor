#!/usr/bin/env python3

"""
Utility script to build and push Docker images for the House Price Predictor backend service.
"""
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

IMAGE_NAME = f"{docker_userid}/house-price-predictor-service"
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
    push_flag: bool = typer.Option(False, "--push", help="Push the image to the repository after build.")
):
    """Build a Docker image with all required ARGS and optionally push to a repository."""
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

    if push_flag:
        # After a successful build, call the push command
        push()



@app.command()
def push():
    """
    Push the Docker image with all its tags to the repository.
    This command uses the more efficient `--all-tags` flag.
    """
    print("\nLogging into Docker Hub...")
    try:
        run("docker login")
    except subprocess.CalledProcessError:
        print("Docker login failed. Please double check $DOCKER_TOKEN is setup and valid.")
        raise typer.Exit(code=1)

    print(f"\nPushing all tags for {IMAGE_NAME}...")
    try:
        run(f"docker push --all-tags {IMAGE_NAME}")
        print("Images pushed successfully.")
    except subprocess.CalledProcessError:
        print("\nDocker push failed.")
        print("Please check the following:")
        print(f"1. The image '{IMAGE_NAME}' exists locally (you can check with 'docker images').")
        print(f"2. The repository '{IMAGE_NAME}' exists on Docker Hub.")
        print("3. You have the necessary permissions to push to this repository.")
        raise typer.Exit(code=1)


@app.command()
def delete():
    """Delete all images for the repo"""
    run(f"docker rmi -f $(docker images -q --filter=reference='{IMAGE_NAME}:*')")

@app.command()
def cleanup():
    """Delete all but latest images"""
    cmd = (
        f"docker images --format '{{{{.Repository}}}} {{{{.Tag}}}} {{{{.ID}}}}' | "
        f"grep '^{IMAGE_NAME} ' | grep -v ' service-latest' | awk '{{print $3}}' | xargs -r docker rmi"
    )
    run(cmd)

@app.command(name="run-container")
def run_container(port: int = PORT, tag: str = "service-latest"):
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
    # `r""" make the python string raw. So \n is preserved. Else will get expanded to a newline resulting in
    #     printf "%s    %s
    # ", id, tags[id];
    # when it should be printf "%s\t%s\n", id, tags[id];

    # | $1 (repo:tag)                                                                | $2 (id)      |
    # | ---------------------------------------------------------------------------- | ------------ |
    # | celestialseeker/house-price-predictor/house-price-predictor-service:affb243  | 47135ea4c4e4 |
    # | celestialseeker/house-price-predictor/house-price-predictor-service:devops   | 47135ea4c4e4 |
    # | celestialseeker/house-price-predictor/house-price-predictor-service:latest   | 47135ea4c4e4 |
    # | celestialseeker/house-price-predictor/house-price-predictor-service:v1.0.0   | 47135ea4c4e4 |
    #     Becomes
    # 47135ea4c4e4    affb243,devops,latest,v1.0.0



    awk_script = r"""
        {
            # $1 is "repo:tag", $2 is "id"
            # 1. Split "repo:tag" into array 'a' using ":" as the delimiter.
            split($1, a, ":");
            
            # 2. Use the image ID ($2) as the key for our 'tags' array.
            #    Append the new tag (a[2]) to the existing list.
            #    The ternary operator adds a comma *only if* a tag already exists.
            tags[$2] = tags[$2] (tags[$2] ? "," : "") a[2];
        }
        END {
            # 3. After processing all lines, loop through the 'tags' array
            #    and print the final ID and the concatenated tag list.
            for (id in tags) {
                printf "%s\t%s\n", id, tags[id];
            }
        }
        """

    cmd = f"""
            docker images --format '{{{{.Repository}}}}:{{{{.Tag}}}} {{{{.ID}}}}' \
                | grep '^{IMAGE_NAME}:' \
                | sort -u \
                | awk '{awk_script}' \
                | while read id tags; do
                      created=$(docker inspect --format='{{{{.Created}}}}' "$id");
                      printf "%s\t%s\t%s\t%s\n" "$(echo "$id" | cut -c1-12)" "{IMAGE_NAME}" "$tags" "$created";
                  done \
                | column -t -s $'\\t'
            """

    run(cmd)





if __name__ == "__main__":
    app()
