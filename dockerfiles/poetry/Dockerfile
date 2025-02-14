# Use the official Python slim image
FROM python:3.11-slim

ENV POETRY_VERSION=1.8.4 \
    POETRY_HOME="/home/testuser/.local" \
    PATH="/home/testuser/.local/bin:$PATH"

# Install dependencies for Poetry and Python
RUN apt-get update && apt-get install -y make curl git && apt-get clean

RUN mkdir -p /home/testuser/app

# Create a test user and set permissions
RUN useradd -m -d /home/testuser -s /bin/bash testuser
RUN chown -R testuser:testuser /home/testuser

# Set working directory
WORKDIR /home/testuser/app

# # Copy only the necessary folders for your project
# COPY --chown=testuser:testuser plugins/ plugins/
# COPY --chown=testuser:testuser provisioner/ provisioner/
# COPY --chown=testuser:testuser provisioner_shared/ provisioner_shared/
# COPY --chown=testuser:testuser scripts/ scripts/
# COPY --chown=testuser:testuser pyproject.toml poetry.lock ./

# # Copy other required files
# COPY --chown=testuser:testuser .dockerignore .gitignore .coveragerc .gitattributes .gitmodules conftest.py Makefile poetry.lock \
#     poetry.toml pyproject.toml pytest.ini run_e2e_tests.py ./

# Dummy git index for the scanning script tool to work (searches for .git at root folder)
# RUN mkdir -p .git && chown -R testuser:testuser .git

# Switch to test user
USER testuser

# Install a specific version of Poetry (1.8.4)
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry self update $POETRY_VERSION

# # Verify files and install dependencies
# RUN cd /home/testuser/app && ls -lah && make dev-mode
# RUN poetry --version

# # Install dependencies with Poetry
# RUN poetry install --no-root

RUN pwd && ls -lah

RUN mkdir -p /home/testuser/app/.venv/ && touch /home/testuser/app/.venv/pyvenv.cfg && echo 'home = /usr/bin/python3.11' > /home/testuser/app/.venv/pyvenv.cfg

# Default command (can be overridden)
CMD ["poetry", "run", "coverage", "run", "-m", "pytest"]
