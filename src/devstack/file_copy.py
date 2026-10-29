from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def copy_file(source: Path, destination: Path) -> OperationMeta:
    return files.put(
        name=f"Copy {source.name} to {destination}",
        src=str(source),
        dest=str(destination),
        mode="644",
    )
