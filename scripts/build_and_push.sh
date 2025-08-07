#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Echo commands
set -x

echo "Logging in to Docker Hub..."
docker login

echo "Building and pushing Docker image..."
echo "------------------------------------"
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t wonsky/topn-db:latest \
    --push \
    .
echo "------------------------------------"
echo "Done!"
