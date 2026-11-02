from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import git

GITHUB_URL_PREFIX = "https://github.com/"


def clone_github_repository(repository: str, destination: Path) -> OperationMeta:
    return clone_repository(f"{GITHUB_URL_PREFIX}{repository}", destination)


def clone_repository(
    url: str, destination: Path, *, ignore_errors: bool = True
) -> OperationMeta:
    return git.repo(
        name=f"Clone {url}",
        src=url,
        dest=str(destination),
        _ignore_errors=ignore_errors,
    )
