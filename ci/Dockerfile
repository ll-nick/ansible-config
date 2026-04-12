FROM ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    && rm -rf /var/lib/apt/lists/*

COPY . /workspace

RUN --mount=type=secret,id=github_token,env=GITHUB_TOKEN \
    ANSIBLE_BECOME_PASS="" DEBIAN_FRONTEND=noninteractive \
    bash /workspace/deploy/deploy.sh --no-confirm --privileged --playbook-path /workspace
