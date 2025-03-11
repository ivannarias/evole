#!/bin/bash

# Define variables
image_name="internal-network"

# docker extra arguments
extra_args=""

if [ -n "$MAC" ]; then
 extra_args+=" --mac-address $MAC"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker and try again."
    exit 1
fi

# Check if the Docker image exists, if not, build it
if ! docker image inspect "$image_name" &>/dev/null; then
    echo "Docker image '$image_name' not found. Building..."
    docker build -t "$image_name" .
fi

# Get current working directory
current=$(pwd)

# If no parameters are provided, start an interactive shell inside the container
if [ "$#" -eq 0 ]; then
    echo "No script provided. Starting an interactive shell inside the Docker container..."
    
    # Check if Bash is available inside the container, otherwise use sh
    shell_cmd="bash"
    if ! docker run --rm "$image_name" bash -c "exit" &>/dev/null; then
        shell_cmd="sh"
    fi
    
    docker run -it -v "$current:/scripts" "$image_name" "$shell_cmd"
    exit 0
fi

# Ensure the first argument (script name) is provided and exists
script_name="$1"
if [ ! -f "$script_name" ]; then
    echo "Error: The specified script '$script_name' does not exist."
    exit 1
fi
shift  # Remove script name from arguments list

# Run the Docker container with the script and additional arguments
docker run -it -v "$current:/scripts" $extra_args "$image_name" python3 "/scripts/$script_name" "$@"

