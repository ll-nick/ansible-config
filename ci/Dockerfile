FROM ubuntu

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    curl \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash tester \
    && echo "tester ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/tester

USER tester
ENV PATH="/home/tester/.local/bin:${PATH}"
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

COPY --chown=tester:tester . /workspace
WORKDIR /workspace

RUN --mount=type=secret,id=github_token,env=GITHUB_TOKEN \
    uv run --no-dev devstack apply --yes
