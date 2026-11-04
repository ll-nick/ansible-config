from pathlib import Path

from pyinfra.api.operation import OperationMeta

from stk.helpers.links import symlink_file


def add_bash_snippet(source: Path) -> OperationMeta:
    return symlink_file(source, Path.home() / ".config" / "bash" / source.name)


def add_nushell_snippet(source: Path) -> OperationMeta:
    return symlink_file(
        source, Path.home() / ".config" / "nushell" / "autoload" / source.name
    )
