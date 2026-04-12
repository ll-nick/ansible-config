#!/usr/bin/env bash
# Usage:
#   ci/run.sh [build|verify|idempotency|all|shell]
#
# Defaults: command=all
#
# Examples:
#   ci/run.sh          # full local run
#   ci/run.sh shell    # drop into a shell in the built image

set -e

COMMAND="${1:-all}"
WORKSPACE="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="ansible-ci"

ci_build() {
    docker build --no-cache -f "$WORKSPACE/ci/Dockerfile" -t "$IMAGE" "$WORKSPACE"
}

ci_verify() {
    docker run --rm \
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

ci_idempotency() {
    docker run --rm \
        -e ANSIBLE_BECOME_PASS="" \
        -e DEBIAN_FRONTEND=noninteractive \
        "$IMAGE" \
        bash -c '
            export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
            cd /workspace
            ansible-playbook local.yml -e "{\"run_privileged\": true}" 2>&1 | tee /tmp/idempotency.txt
            grep -qE "✱ Changed +\| +0" /tmp/idempotency.txt \
                || { echo "FAIL: playbook is not idempotent"; exit 1; }
            echo "Idempotency check passed."
        '
}

ci_shell() {
    docker run -it --rm \
        -e ANSIBLE_BECOME_PASS="" \
        -e DEBIAN_FRONTEND=noninteractive \
        "$IMAGE" \
        bash
}

case "$COMMAND" in
    build) ci_build ;;
    verify) ci_verify ;;
    idempotency) ci_idempotency ;;
    shell) ci_shell ;;
    all)
        ci_build
        ci_verify
        ci_idempotency
        ;;
    *)
        printf "Unknown command: %s\n" "$COMMAND"
        printf "Usage: %s [build|verify|idempotency|all|shell]\n" "$0"
        exit 1
        ;;
esac
