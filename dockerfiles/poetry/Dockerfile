FROM python:3.11-slim

ARG E2E_ESSENTIAL_FILES_ARCHIVE_NAME="e2e_docker_essential_files.tar.gz"

ENV POETRY_VERSION=1.8.4 \
    POETRY_HOME="/.local" \
    PATH="/.local/bin:$PATH"

# Set working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install locales package and generate en_US.UTF-8
# RUN apt-get update && apt-get install -y locales \
#     && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
#     && locale-gen en_US.UTF-8 \
#     && dpkg-reconfigure --frontend=noninteractive locales \
#     && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Set environment variables for locale
# ENV LANG en_US.UTF-8
# ENV LC_ALL en_US.UTF-8

# Use a recognized terminal in the container to support TUI Python libraries terminal environment
# RUN echo 'export TERM=xterm' >> /etc/bash.bashrc

# Dummy git index for the scanning script tool to work (searches for .git at root folder)
RUN mkdir -p /app/.git

# Install a specific version of Poetry (1.8.4)
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry self update $POETRY_VERSION

# Copy the essentials e2e files archive from the host
COPY ${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} /tmp/

# Extract essential files used for E2E tests while preserving directory structure
RUN tar -xzf /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME} -C /app && rm /tmp/${E2E_ESSENTIAL_FILES_ARCHIVE_NAME}

# # Verify files and install dependencies
RUN cd /app && ls -lah && make dev-mode-container && make deps-install
RUN poetry --version
RUN pwd && ls -lah

# Backup the container adjusted Poetry pyproject config into /tmp/app_backup
RUN mkdir -p /tmp/app_backup && cp -r /app/. /tmp/app_backup

# Configure Poetry
RUN poetry config virtualenvs.create false \
    && poetry config virtualenvs.in-project true

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD [""]

# Don't copy the project code - it will be mounted
