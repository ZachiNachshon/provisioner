#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#           GLOBALS
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
ARG HOME="/usr/runner"
ARG RUNNER_WORKSPACE="${HOME}/workspace"
ARG RUNNER_ENTRYPOINT="runner_dockerized_entrypoint"

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#        ANSIBLE BUILDER
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# FROM debian:buster-slim AS ansible-builder
FROM python:3.9-slim AS ansible-builder
LABEL maintainer="Zachi Nachshon <zachi.nachshon@gmail.com>"

# Can be overridden
ENV RUNNER_CLI_NAME="ansible-playbook"

# Use globals
ARG RUNNER_VERSION

# Add in here how the binary should be installed
RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y python3-pip sshpass git openssh-client libhdf5-dev libssl-dev libffi-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

RUN pip3 install --upgrade pip cffi && \
    pip install ansible-core=="${RUNNER_VERSION}" && \
    pip install mitogen ansible-lint jmespath && \
    pip install --upgrade pywinrm && \
    rm -rf /root/.cache/pip

RUN mkdir -p /etc/ansible && \
    echo 'localhost' > /etc/ansible/hosts

#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#        ANSIBLE RUNNER
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
FROM ansible-builder AS ansible-runner
LABEL maintainer="Zachi Nachshon <zachi.nachshon@gmail.com>"

# Use globals
ARG RUNNER_WORKSPACE
ARG RUNNER_ENTRYPOINT

ENV RUNNER_ARGS=""
ENV DEBUG=""

COPY ${RUNNER_ENTRYPOINT}.sh /usr/local/bin/${RUNNER_ENTRYPOINT}

RUN chmod +x /usr/local/bin/${RUNNER_ENTRYPOINT} \
    && mkdir -p ${RUNNER_WORKSPACE} \
    && mkdir -p ${RUNNER_WORKSPACE}/playbooks \
    && mkdir -p ${RUNNER_WORKSPACE}/resources \
    && mkdir -p ${RUNNER_WORKSPACE}/hosts \
    && mkdir -p ${RUNNER_WORKSPACE}/config

COPY config/ansible.cfg ${RUNNER_WORKSPACE}/config/ansible.cfg
COPY config/callbacks ${RUNNER_WORKSPACE}/config/callbacks

ENV ANSIBLE_CONFIG=${RUNNER_WORKSPACE}/config/ansible.cfg

WORKDIR ${RUNNER_WORKSPACE}

ENTRYPOINT ["runner_dockerized_entrypoint"]
