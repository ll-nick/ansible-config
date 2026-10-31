from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def link_file(link: Path, target: Path) -> None:
    files.link(
        name=f"Link {link.name}",
        path=str(link),
        target=str(target),
        force=True,
    )


def link_repository_file(source: Path, destination: Path) -> OperationMeta:
    """Make `destination` a symlink to a file of this repository.

    Edits on the machine land in the repository and pulled changes apply immediately.
    The mode is whatever git tracks for `source`.
    """
    return files.link(
        name=f"Link {destination} to {source.name}",
        path=str(destination),
        target=str(source),
        force=True,
    )
