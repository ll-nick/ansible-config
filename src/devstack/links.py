from pathlib import Path

from pyinfra.operations import files


def link_file(link: Path, target: Path) -> None:
    files.link(
        name=f"Link {link.name}",
        path=str(link),
        target=str(target),
        force=True,
    )
