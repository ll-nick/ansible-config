from pathlib import Path

from devstack.machine import JOY_HOSTNAME, host_is
from devstack.testing import skip_unless


@skip_unless(host_is(JOY_HOSTNAME))
def test_the_machine_local_git_config_is_installed() -> None:
    assert (Path.home() / ".config/git/local.gitconfig").exists()
