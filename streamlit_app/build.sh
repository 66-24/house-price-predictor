#!/usr/bin/env bash
#Builds the Docker image that provides a nice UI to use the house price predictor service
DOCKER_USERID='celestialseeker'
GIT_SHA_SHORT=$(git rev-parse --short=7 HEAD)
VERSION=v1
TEAM=devops
IMAGE=${DOCKER_USERID}/house-price-predictor-ui

docker build \
  --build-arg SOURCE_DATE_EPOCH=$(date +%s) \
  -t ${IMAGE}:${VERSION} \
  -t ${IMAGE}:${GIT_SHA_SHORT} \
  -t ${IMAGE}:${TEAM} .


if [[ "$1" == "--push" ]]; then
  for tag in $VERSION $GIT_SHA_SHORT $TEAM; do
    docker push ${IMAGE}:${tag}
  done
fi