FROM ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY . /workspace

RUN ANSIBLE_BECOME_PASS="" DEBIAN_FRONTEND=noninteractive \
    bash /workspace/deploy/deploy.sh --no-confirm --privileged --playbook-path /workspace
