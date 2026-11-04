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
ENV PATH="/home/tester/.local/share/mise/shims:/home/tester/.local/bin:${PATH}"
RUN curl -fsSL https://mise.jdx.dev/install.sh | sh

COPY --chown=tester:tester . /workspace
WORKDIR /workspace

RUN --mount=type=secret,id=github_token,env=GITHUB_TOKEN \
    mise install uv@latest \
    && "$(mise which --tool uv@latest uv)" run --no-dev stk enable sudo \
    && "$(mise which --tool uv@latest uv)" run --no-dev stk apply --yes
