from pathlib import Path

from pyinfra.api.operation import OperationMeta

from devstack.links import link_repository_file


def add_bash_snippet(source: Path) -> OperationMeta:
    return link_repository_file(source, Path.home() / ".config" / "bash" / source.name)


def add_nushell_snippet(source: Path) -> OperationMeta:
    return link_repository_file(
        source, Path.home() / ".config" / "nushell" / "autoload" / source.name
    )
