import subprocess

import pytest

from devstack.machine import runs_distribution


@pytest.mark.skipif(
    not runs_distribution("debian").is_met(),
    reason="locales are only managed on Debian",
)
def test_the_configured_locales_exist() -> None:
    available = subprocess.run(
        ["locale", "-a"], capture_output=True, text=True, check=True
    ).stdout

    assert "de_DE.utf8" in available
    assert "en_US.utf8" in available
