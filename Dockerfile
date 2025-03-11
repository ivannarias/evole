# Use the latest Alpine Linux as base image
FROM alpine:latest

# Install Python 3 and pip
RUN apk add --no-cache python3 bash py3-pip

# Set Python as the default command
CMD ["bash"]

