import os
import sys
from pathlib import Path

import pytest

from devstack.environment import remove_own_virtual_environment


def test_the_own_environment_is_removed_from_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own_bin_directory = str(Path(sys.prefix) / "bin")
    monkeypatch.setenv("PATH", os.pathsep.join([own_bin_directory, "/usr/bin"]))
    monkeypatch.setenv("VIRTUAL_ENV", sys.prefix)

    remove_own_virtual_environment()

    assert os.environ["PATH"] == "/usr/bin"
    assert "VIRTUAL_ENV" not in os.environ
