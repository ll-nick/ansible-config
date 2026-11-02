from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files

from stk.log_file_reporter import state_directory


def replaced_files_directory(destination: Path) -> Path:
    return state_directory() / "replaced-files" / destination.parent.relative_to("/")


def symlink_file(source: Path, destination: Path) -> OperationMeta:
    """Make `destination` a symlink to `source`, moving away whatever is there.

    For files of this repository, edits on the machine land in the repository
    and pulled changes apply immediately.
    The mode is whatever git tracks for `source`.
    """
    # Not next to the replaced file, as a backup there would still be picked up:
    # the bash config sources everything in its directory, in sorted order
    backup_directory = replaced_files_directory(destination)
    if destination.exists() and not destination.is_symlink():
        backup_directory.mkdir(parents=True, exist_ok=True)
    return files.link(
        name=f"Link {destination} to {source.name}",
        path=str(destination),
        target=str(source),
        force=True,
        force_backup_dir=str(backup_directory),
    )
