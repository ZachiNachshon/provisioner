# 
# DITCHED THE DOCKERIZED POETRY DUE TO DIFFICULTIES TO MANAGE THE VIRTUAL ENV VOLUMES
# 

# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# #           GLOBALS
# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# ARG HOME="/usr/runner"
# # The installation script appends /bin as the suffix (${HOME}/.local/bin)
# ARG BINARY_HOME="${HOME}/.local"
# ARG RUNNER_WORKSPACE="${HOME}/workspace"
# ARG RUNNER_ENTRYPOINT="runner_dockerized_entrypoint"
# ARG RUNNER_OS_ARCH=""

# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# #         POETRY BUILDER
# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# # Downgrade to Alpine 3.12.x due to issue with Raspberry Pi ARM issue
# # See: https://github.com/gliderlabs/docker-alpine/issues/386#issuecomment-1000644809
# FROM python:3.9-slim AS poetry-python-builder
# LABEL maintainer="Zachi Nachshon <zachi.nachshon@gmail.com>"

# # Can be overridden
# ENV RUNNER_CLI_NAME="poetry"
# ARG RUNNER_VERSION=1.1.12

# # Use globals
# ARG BINARY_HOME

# # Add in here how the binary should be installed
# RUN apt-get update && apt-get install --no-install-recommends -y curl git \
#     && mkdir -p ${BINARY_HOME} \
#     && curl -sSL https://install.python-poetry.org | POETRY_HOME=${BINARY_HOME} POETRY_VERSION=${RUNNER_VERSION} python3 - --force \
#     && chmod +x ${BINARY_HOME}/${RUNNER_CLI_NAME} \
#     && rm -rf /var/lib/apt/lists/*
    
# RUN apk update && apk add --virtual .build-dependencies --no-cache bash openssl curl openssh-server \
    
#     && cd /tmp \
#     && wget -O ${RUNNER_CLI_NAME} "https://github.com/mvdan/sh/releases/download/v${RUNNER_VERSION}/shfmt_v${RUNNER_VERSION}_${RUNNER_OS_ARCH}" \
#     && mv ./${RUNNER_CLI_NAME} ${BINARY_HOME} \
    
#     && rm -rf /tmp/* \
#     && rm -rf /var/lib/apt/lists/*

# ENV PATH=${BINARY_HOME}:$PATH

# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# #         POETRY RUNNER
# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# FROM poetry-python-builder AS poetry-python-runner
# LABEL maintainer="Zachi Nachshon <zachi.nachshon@gmail.com>"

# # Use globals
# ARG RUNNER_WORKSPACE
# ARG RUNNER_ENTRYPOINT

# ENV RUNNER_ARGS=""
# ENV DEBUG=""

# COPY ${RUNNER_ENTRYPOINT}.sh /usr/local/bin/${RUNNER_ENTRYPOINT}

# RUN chmod +x /usr/local/bin/${RUNNER_ENTRYPOINT} \
#     && mkdir -p ${RUNNER_WORKSPACE}

# WORKDIR ${RUNNER_WORKSPACE}

# ENTRYPOINT ["runner_dockerized_entrypoint"]

# ENV PATH=$POETRY_HOME/bin:$PATH

# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# #      PYTHON/POETRY RUNNER
# #-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# FROM python-poetry-base AS python-poetry-runner

# ENV POETRY_WORKSPACE=${HOME}/runner/workspace
# ENV POETRY_ARGS=""
# ENV SILENT="false"

# COPY poetry-entrypoint.sh /usr/local/bin/poetry-entrypoint

# RUN chmod +x /usr/local/bin/poetry-entrypoint \
#     && mkdir -p ${POETRY_WORKSPACE}

# WORKDIR ${POETRY_WORKSPACE}

# ENTRYPOINT ["poetry-entrypoint"]
# # CMD ["poetry"]