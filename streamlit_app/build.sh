#!/usr/bin/env bash
#Builds the Docker image that provides a nice UI to use the house price predictor service

GIT_SHA_SHORT=$(git rev-parse --short=7 HEAD)
VERSION=v1
TEAM=devops
# Both service and ui images will now be under a single repository
IMAGE=${DOCKER_USERID}/house-price-predictor
BUILD_DATE=$(date -Iseconds)
SOURCE_DATE_EPOCH=$(date +%s)

docker build \
  --build-arg SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg AUTHOR="$AUTHOR" \
  --build-arg VERSION="$VERSION" \
  --build-arg GIT_SHA_SHORT="$GIT_SHA_SHORT" \
  --build-arg TEAM="$TEAM" \
  -t "${IMAGE}:ui-${VERSION}" \
  -t "${IMAGE}:ui-${GIT_SHA_SHORT}" \
  -t "${IMAGE}:ui-${TEAM}" \
  -t "${IMAGE}:ui-latest" .

#Cleanup dangling images
docker image prune -f --filter "label=org.opencontainers.image.title=House Price Predictor UI"

if [[ "$1" == "--push" ]]; then
  docker push --all-tags ${IMAGE}
fi
