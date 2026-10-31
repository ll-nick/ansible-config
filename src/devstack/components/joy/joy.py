from pathlib import Path

from devstack.file_copy import ensure_file_exists
from devstack.links import link_repository_file
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet
from devstack.systemd import USER_UNIT_DIRECTORY, disable_user_unit

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("joy")
def apply_joy() -> None:
    add_bash_snippet(FILES / "joy.bash")

    # Silences the setup hint of the shared dotfiles
    ensure_file_exists(Path.home() / ".dotfiles")

    link_repository_file(
        FILES / "joy.gitconfig", Path.home() / ".config/git/local.gitconfig"
    )
    link_repository_file(FILES / "stk-skip", Path.home() / ".config/stk/skip")

    # The tmux service stops the tmux server, and everything running in it,
    # when the last session of the user ends
    if (USER_UNIT_DIRECTORY / "tmux.service").exists():
        disable_user_unit("tmux")
