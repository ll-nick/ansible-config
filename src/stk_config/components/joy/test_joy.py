from pathlib import Path

from stk.machine import host_is
from stk.testing import skip_unless
from stk_config.components.joy.joy import JOY_HOSTNAME


@skip_unless(host_is(JOY_HOSTNAME))
def test_the_machine_local_git_config_is_installed() -> None:
    assert (Path.home() / ".config/git/local.gitconfig").exists()
