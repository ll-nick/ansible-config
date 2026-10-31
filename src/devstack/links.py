from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def symlink_file(source: Path, destination: Path) -> OperationMeta:
    """Make `destination` a symlink to `source`, replacing whatever is there.

    For files of this repository, edits on the machine land in the repository
    and pulled changes apply immediately.
    The mode is whatever git tracks for `source`.
    """
    return files.link(
        name=f"Link {destination} to {source.name}",
        path=str(destination),
        target=str(source),
        force=True,
    )
