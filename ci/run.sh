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
IMAGE="devstack-ci"

ci_build() {
    docker build \
        ${GITHUB_TOKEN:+--secret id=github_token,env=GITHUB_TOKEN} \
        -f "$WORKSPACE/ci/Dockerfile" -t "$IMAGE" "$WORKSPACE"
}

ci_verify() {
    docker run --rm ${GITHUB_TOKEN:+-e GITHUB_TOKEN} "$IMAGE" uv run pytest
}

ci_idempotency() {
    docker run --rm ${GITHUB_TOKEN:+-e GITHUB_TOKEN} "$IMAGE" \
        uv run --no-dev devstack apply --yes --privileged --fail-on-change
}

ci_shell() {
    docker run -it --rm ${GITHUB_TOKEN:+-e GITHUB_TOKEN} "$IMAGE" bash
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
