from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files

EXECUTABLE_MODE = "755"


def copy_file(source: Path, destination: Path, *, mode: str = "644") -> OperationMeta:
    return files.put(
        name=f"Copy {source.name} to {destination}",
        src=str(source),
        dest=str(destination),
        mode=mode,
    )


def ensure_file_exists(path: Path) -> OperationMeta:
    return files.file(name=f"Ensure {path} exists", path=str(path), present=True)
