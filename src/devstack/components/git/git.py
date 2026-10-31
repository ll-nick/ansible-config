from pathlib import Path

from devstack.links import link_repository_file
from devstack.machine import git_version
from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"
CONFIG_FILE_NAMES = (
    "gitconfig-github.com",
    "gitconfig-gitlab.com",
    "gitignore",
    "delta.gitconfig",
)
FIRST_VERSION_WITH_ZDIFF3 = (2, 35)


@component_deploy("git")
def apply_git() -> None:
    config_directory = Path.home() / ".config" / "git"

    link_repository_file(FILES / "gitconfig", Path.home() / ".gitconfig")
    for name in CONFIG_FILE_NAMES:
        link_repository_file(FILES / name, config_directory / name)

    install_mise_tools("git", FILES / "mise.toml")

    version = git_version()
    supports_zdiff3 = version is None or version >= FIRST_VERSION_WITH_ZDIFF3
    conflict_style = (
        "conflict-style-modern.gitconfig"
        if supports_zdiff3
        else "conflict-style.gitconfig"
    )
    link_repository_file(
        FILES / conflict_style, config_directory / "conflict-style.gitconfig"
    )
