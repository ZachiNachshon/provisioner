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
FROM python:3.11-slim

# Enable testing mode for provisioner Ansible based tests
ENV PROVISIONER_TESTING_MODE_ENABLED="true"

ENV TEST_SDSIT_OUTPUTS_HOST_PATH="dists/*.tar.gz"
ENV TEST_SDIST_OUTPUTS_CONTAINER_PATH="/tmp/provisioner-sdists/"
ARG E2E_ESSENTIAL_FILES_ARCHIVE_NAME="e2e_docker_essential_files.tar.gz"

RUN mkdir -p ~/.local/bin && chmod +x ~/.local/bin

ENV POETRY_VERSION=1.8.4 \
    POETRY_HOME="/.local" \
    PATH="/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    # sshpass is mandatory for using Ansible with plain password
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in the container
WORKDIR /app

# Install Python uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    . $HOME/.local/bin/env && \
    mkdir -p /app && \
    which uv && \
    uv python install --reinstall 3.11 && \
    uv venv --directory /app

# Dummy git index for the scanning script tool to work (searches for .git at root folder)
RUN mkdir -p /app/.git $TEST_SDIST_OUTPUTS_CONTAINER_PATH

# Install a specific version of Poetry (1.8.4)
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry self update $POETRY_VERSION

# Copy the essentials e2e files archive from the host
COPY ${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} /tmp/

# Extract essential files used for E2E tests while preserving directory structure
RUN tar -xzf /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} -C /app && rm /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME}

# # Verify files and install dependencies
RUN cd /app && ls -lah && make deps-install
RUN poetry --version
RUN pwd && ls -lah

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry config virtualenvs.in-project true \
    # Allows the build-project command to bundle multiple projects into a single package
    && poetry self add poetry-multiproject-plugin \
    # Install pip into Poetry's virtual environment
    && poetry run pip install --upgrade pip

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD [""]

# Don't copy the project code - it will be mounted
