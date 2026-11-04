from pathlib import Path

from stk.engine.component import Component
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools
from stk.machine import git_version
from stk_config.components.mise.mise import MISE

FILES = Path(__file__).resolve().parent / "files"
CONFIG_FILE_NAMES = (
    "gitconfig-github.com",
    "gitconfig-gitlab.com",
    "gitignore",
    "delta.gitconfig",
)
FIRST_VERSION_WITH_ZDIFF3 = (2, 35)


def apply_git() -> None:
    config_directory = Path.home() / ".config" / "git"

    symlink_file(FILES / "gitconfig", Path.home() / ".gitconfig")
    for name in CONFIG_FILE_NAMES:
        symlink_file(FILES / name, config_directory / name)

    install_mise_tools("git", FILES / "mise.toml")

    version = git_version()
    supports_zdiff3 = version is None or version >= FIRST_VERSION_WITH_ZDIFF3
    conflict_style = (
        "conflict-style-modern.gitconfig"
        if supports_zdiff3
        else "conflict-style.gitconfig"
    )
    symlink_file(FILES / conflict_style, config_directory / "conflict-style.gitconfig")


GIT = Component(
    "git",
    apply_git,
    depends_on=(MISE,),
    system_packages=("git",),
)
