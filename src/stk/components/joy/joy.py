from pathlib import Path

from pyinfra.operations import files

from stk.links import symlink_file
from stk.pyinfra_adapters import component_deploy
from stk.shells import add_bash_snippet
from stk.systemd import USER_UNIT_DIRECTORY, disable_user_unit

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("joy")
def apply_joy() -> None:
    add_bash_snippet(FILES / "joy.bash")

    # Silences the setup hint of the shared dotfiles
    files.file(name="Ensure ~/.dotfiles exists", path=str(Path.home() / ".dotfiles"))

    symlink_file(FILES / "joy.gitconfig", Path.home() / ".config/git/local.gitconfig")

    # The tmux service stops the tmux server, and everything running in it,
    # when the last session of the user ends
    if (USER_UNIT_DIRECTORY / "tmux.service").exists():
        disable_user_unit("tmux")
