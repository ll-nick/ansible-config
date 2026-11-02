from dataclasses import dataclass
from pathlib import Path

from stk.engine.pyinfra_adapters import component_deploy
from stk.helpers.github import clone_github_repository
from stk.helpers.links import symlink_file
from stk.helpers.shells import add_bash_snippet

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
        symlink_file(
            config_directory / symbolic_link.target_name,
            Path.home() / symbolic_link.link_name,
        )

    symlink_file(FILES / "inputrc", Path.home() / ".inputrc")
    add_bash_snippet(FILES / "1_mise.bash")
