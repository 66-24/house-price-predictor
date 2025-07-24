#!/bin/bash

# This script runs the Dagger pipeline within the dagger-runner Docker container.

# Ensure Docker Hub credentials are set in the environment
if [ -z "$DOCKERHUB_USERNAME" ] || [ -z "$DOCKERHUB_TOKEN" ]; then
  echo "Error: DOCKERHUB_USERNAME and DOCKERHUB_TOKEN must be set as environment variables."
  echo "Example: export DOCKERHUB_USERNAME=\"your_username\""
  echo "         export DOCKERHUB_TOKEN=\"your_token\""
  exit 1
fi

echo "Running Dagger pipeline in Docker container..."

docker run -it --rm \
  --name dagger-runner \
  --network host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD":/app \
  -w /app \
  -e DOCKERHUB_USERNAME="$DOCKERHUB_USERNAME" \
  -e DOCKERHUB_TOKEN="$DOCKERHUB_TOKEN" \
  -e DAGGER_TRACE=true \
  -e DAGGER_TRACE_LISTEN=0.0.0.0:6060 \
  -p 6060:6060 \
  dagger-runner \
  dagger run python dagger_pipeline.py --progress=plain

echo "Dagger pipeline execution finished."

