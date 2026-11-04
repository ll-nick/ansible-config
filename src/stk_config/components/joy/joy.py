from pathlib import Path

from pyinfra.operations import files

from stk.engine.component import Component
from stk.helpers.links import symlink_file
from stk.helpers.shells import add_bash_snippet
from stk.helpers.systemd import USER_UNIT_DIRECTORY, disable_user_unit
from stk.machine import host_is
from stk_config.components.bash.bash import BASH
from stk_config.components.git.git import GIT

FILES = Path(__file__).resolve().parent / "files"
JOY_HOSTNAME = "mrtjoy"


def apply_joy() -> None:
    add_bash_snippet(FILES / "joy.bash")

    # Silences the setup hint of the shared dotfiles
    files.file(name="Ensure ~/.dotfiles exists", path=str(Path.home() / ".dotfiles"))

    symlink_file(FILES / "joy.gitconfig", Path.home() / ".config/git/local.gitconfig")

    # The tmux service stops the tmux server, and everything running in it,
    # when the last session of the user ends
    if (USER_UNIT_DIRECTORY / "tmux.service").exists():
        disable_user_unit("tmux")


JOY = Component(
    "joy",
    apply_joy,
    depends_on=(BASH, GIT),
    requires=(host_is(JOY_HOSTNAME),),
)
