from dataclasses import dataclass
from pathlib import Path

from pyinfra.operations import files

from devstack.file_copy import copy_file
from devstack.github import clone_github_repository
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet

FILES = Path(__file__).resolve().parent / "files"


@dataclass(frozen=True)
class SymbolicLink:
    link_name: str
    target_name: str


SYMBOLIC_LINKS = (
    SymbolicLink(".bashrc", ".bashrc"),
    SymbolicLink(".profile", ".bash_profile"),
    SymbolicLink(".bash_profile", ".bash_profile"),
)


@component_deploy("bash")
def apply_bash() -> None:
    config_directory = Path.home() / ".config" / "bash"

    clone_github_repository("ll-nick/bash-config", config_directory)

    for symbolic_link in SYMBOLIC_LINKS:
        files.link(
            name=f"Link ~/{symbolic_link.link_name}",
            path=str(Path.home() / symbolic_link.link_name),
            target=str(config_directory / symbolic_link.target_name),
            force=True,
        )

    copy_file(FILES / "inputrc", Path.home() / ".inputrc")
    add_bash_snippet(FILES / "1_mise.bash")
