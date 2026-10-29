from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def copy_file(source: Path, destination: Path) -> OperationMeta:
    files.directory(
        name=f"Ensure {destination.parent} exists",
        path=str(destination.parent),
    )
    return files.put(
        name=f"Copy {source.name} to {destination}",
        src=str(source),
        dest=str(destination),
        mode="644",
    )
