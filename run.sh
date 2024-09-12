#!/bin/bash

# Stop and remove all running containers
docker ps -aq | xargs -r docker stop | xargs -r docker rm

# Build the Docker image (only needed for the first time or when Dockerfile changes)
docker build -t agent-app .

# Run the Docker container with volume mounting
docker run -d \
  -p 5001:5001 \
  --env-file .env \
  -v "$(pwd):/app" \
  agent-app