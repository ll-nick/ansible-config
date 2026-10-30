from functools import cache
from pathlib import Path

from gevent import subprocess
from pyinfra.api.operation import OperationMeta
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


def clone_github_repository(repository: str, destination: Path) -> OperationMeta:
    return clone_repository(f"{github_url_prefix()}{repository}", destination)


def clone_repository(
    url: str, destination: Path, *, ignore_errors: bool = True
) -> OperationMeta:
    return git.repo(
        name=f"Clone {url}",
        src=url,
        dest=str(destination),
        _ignore_errors=ignore_errors,
    )
