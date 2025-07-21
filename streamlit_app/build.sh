#!/usr/bin/env bash
#Builds the Docker image that provides a nice UI to use the house price predictor service

GIT_SHA_SHORT=$(git rev-parse --short=7 HEAD)
VERSION=v1
TEAM=devops
#Both service and ui images will now be under house-price-predictor
IMAGE=${DOCKER_USERID}/house-price-predictor/house-price-predictor-ui
BUILD_DATE=$(date -Iseconds)
SOURCE_DATE_EPOCH=$(date +%s)

docker build \
  --build-arg SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg AUTHOR="$AUTHOR" \
  --build-arg VERSION="$VERSION" \
  --build-arg GIT_SHA_SHORT="$GIT_SHA_SHORT" \
  --build-arg TEAM="$TEAM" \
  -t "${IMAGE}:${VERSION}" \
  -t "${IMAGE}:${GIT_SHA_SHORT}" \
  -t "${IMAGE}:${TEAM}" .

#Cleanup dangling images
docker image prune -f --filter "label=org.opencontainers.image.title=House Price Predictor UI"

if [[ "$1" == "--push" ]]; then
  for tag in $VERSION $GIT_SHA_SHORT $TEAM; do
    docker push ${IMAGE}:${tag}
  done
fi