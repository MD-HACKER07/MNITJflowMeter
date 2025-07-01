#!/bin/bash

# Build the Docker image
echo "Building Docker image..."
docker build -t cicflowmeter-builder -f Dockerfile.build .

# Create a temporary container to copy the built files
CONTAINER_ID=$(docker create cicflowmeter-builder)

# Create output directory if it doesn't exist
mkdir -p dist_docker

# Copy the built executable from the container
echo "Copying built files..."
docker cp $CONTAINER_ID:/app/dist/CICFlowMeter ./dist_docker/

# Clean up the container
echo "Cleaning up..."
docker rm $CONTAINER_ID

echo "Build complete! The executable is in the dist_docker/ directory."
