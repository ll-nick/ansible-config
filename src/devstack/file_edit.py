from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def replace_line(
    path: Path, pattern: str, line: str, *, sudo: bool = False
) -> OperationMeta:
    return files.line(
        name=f"Set {line} in {path.name}",
        path=str(path),
        line=pattern,
        replace=line,
        _sudo=sudo,
    )
