# BUILD:
#   docker build -f ./dockerfiles/poetry/Dockerfile -t provisioner-poetry-e2e:latest ./dockerfiles/poetry
# 
# RUN:
#   docker run --network=host --rm -it \
#   --name "provisioner-poetry-e2e-manual" \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   -v /path/to/dockerfiles/poetry/dists:/tmp/provisioner-sdists \
#   -w /app \
#   --entrypoint=/bin/bash
#   "provisioner-poetry-e2e"
# 
FROM python:3.11-alpine

# Enable testing mode for provisioner Ansible based tests
ENV PROVISIONER_INSTALLER_PLUGIN_TEST="true" \
    TEST_SDSIT_OUTPUTS_HOST_PATH="dists/*.tar.gz" \
    TEST_SDIST_OUTPUTS_CONTAINER_PATH="/tmp/provisioner-sdists/" \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/.local" \
    PATH="/.local/bin:$PATH"

ARG E2E_ESSENTIAL_FILES_ARCHIVE_NAME="e2e_docker_essential_files.tar.gz"

# Install system dependencies and clean up in the same layer
RUN apk add --no-cache \
    curl \
    bash \
    git \
    openssh-client \
    sshpass \
    build-base \
    libffi-dev \
    openssl-dev \
    python3-dev \
    gcc \
    musl-dev \
    linux-headers \
    && mkdir -p ~/.local/bin && \
    chmod +x ~/.local/bin

# Dummy git index for the scanning script tool to work (searches for .git at root folder)
RUN mkdir -p /app/.git $TEST_SDIST_OUTPUTS_CONTAINER_PATH

# Copy and extract essential files
COPY ${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} /tmp/
RUN tar -xzf /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} -C /app && \
    rm /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME}

# Set working directory in the container
WORKDIR /app

# Install Python uv package manager and set up environment
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    . $HOME/.local/bin/env && \
    mkdir -p /app && \
    which uv && \
    # Skip Python reinstallation since we're using the base image's Python
    uv venv --directory /app && \
    rm -rf /root/.cache/*

# Install Poetry and configure it
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry self update $POETRY_VERSION && \
    poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project true && \
    poetry self add poetry-multiproject-plugin && \
    poetry run pip install --upgrade pip && \
    rm -rf /root/.cache/*

# Verify files and install dependencies
RUN cd /app && \
    ls -lah && \
    make deps-install && \
    poetry --version && \
    pwd && \
    ls -lah && \
    rm -rf /root/.cache/*

# Set up entrypoint
COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD [""]

# Don't copy the project code - it will be mounted
