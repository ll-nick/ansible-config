from functools import cache
from pathlib import Path

from gevent import subprocess
from pyinfra.operations import git

GITHUB_SSH_PREFIX = "git@github.com:"
GITHUB_HTTPS_PREFIX = "https://github.com/"
SSH_AUTHENTICATED_EXIT_CODES = (0, 1)


@cache
def github_url_prefix() -> str:
    try:
        completed = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-T",
                "git@github.com",
            ],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return GITHUB_HTTPS_PREFIX
    if completed.returncode in SSH_AUTHENTICATED_EXIT_CODES:
        return GITHUB_SSH_PREFIX
    return GITHUB_HTTPS_PREFIX


def clone_github_repository(repository: str, destination: Path) -> None:
    git.repo(
        name=f"Clone {repository}",
        src=f"{github_url_prefix()}{repository}",
        dest=str(destination),
        _ignore_errors=True,
    )
