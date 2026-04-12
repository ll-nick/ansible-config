#!/usr/bin/env bash
# Usage:
#   ci/run.sh [build|deploy|verify|idempotency|all|shell] [cache-dir]
#
# Defaults: command=all, cache-dir=~/.cache/ansible-ci-home
#
# Examples:
#   ci/run.sh                          # full local run
#   ci/run.sh deploy ~/.cache/ci       # deploy only, custom cache
#   ci/run.sh build                    # rebuild image only

set -e

COMMAND="${1:-all}"
CACHE_DIR="${2:-$HOME/.cache/ansible-ci-home}"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="ansible-ci"

ci_build() {
    docker build -f "$WORKSPACE/ci/Dockerfile" -t "$IMAGE" "$WORKSPACE"
}

ci_deploy() {
    mkdir -p "$CACHE_DIR"
    docker run --rm \
        -v "$WORKSPACE:/workspace:ro" \
        -v "$CACHE_DIR:/root" \
        -e ANSIBLE_BECOME_PASS="" \
        -e DEBIAN_FRONTEND=noninteractive \
        "$IMAGE" \
        bash /workspace/deploy/deploy.sh --no-confirm --privileged --playbook-path /workspace
}

ci_verify() {
    docker run --rm \
        -v "$WORKSPACE:/workspace:ro" \
        -v "$CACHE_DIR:/root" \
        "$IMAGE" \
        bash -c '
            export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
            for tool in mise bat delta eza fd fzf lazygit leadr node nvim nu rg starship stk tmux uv zoxide; do
                command -v "$tool" || { echo "MISSING binary: $tool"; exit 1; }
            done
            for config in \
                "$HOME/.config/bat/config" \
                "$HOME/.config/nushell" \
                "$HOME/.config/starship"; do
                [ -e "$config" ] || { echo "MISSING config: $config"; exit 1; }
            done
            echo "All checks passed."
        '
}

ci_shell() {
    mkdir -p "$CACHE_DIR"
    docker run -it --rm \
        -v "$WORKSPACE:/workspace:ro" \
        -v "$CACHE_DIR:/root" \
        -e ANSIBLE_BECOME_PASS="" \
        -e DEBIAN_FRONTEND=noninteractive \
        "$IMAGE" \
        bash
}

ci_idempotency() {
    docker run --rm \
        -v "$WORKSPACE:/workspace:ro" \
        -v "$CACHE_DIR:/root" \
        -e ANSIBLE_BECOME_PASS="" \
        -e DEBIAN_FRONTEND=noninteractive \
        "$IMAGE" \
        bash -c '
            export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
            cd /workspace
            ansible-playbook local.yml 2>&1 | tee /tmp/idempotency.txt
            grep -qE "✱ Changed +\| +0" /tmp/idempotency.txt \
                || { echo "FAIL: playbook is not idempotent"; exit 1; }
            echo "Idempotency check passed."
        '
}

case "$COMMAND" in
    build) ci_build ;;
    deploy) ci_deploy ;;
    verify) ci_verify ;;
    idempotency) ci_idempotency ;;
    shell) ci_shell ;;
    all)
        ci_build
        ci_deploy
        ci_verify
        ci_idempotency
        ;;
    *)
        printf "Unknown command: %s\n" "$COMMAND"
        printf "Usage: %s [build|deploy|verify|idempotency|all|shell] [cache-dir]\n" "$0"
        exit 1
        ;;
esac
