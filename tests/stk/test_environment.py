import os
import sys
from pathlib import Path

import pytest

from stk.environment import (
    isolate_mise_from_the_caller,
    remove_own_virtual_environment,
)


def test_the_own_environment_is_removed_from_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    own_bin_directory = str(Path(sys.prefix) / "bin")
    monkeypatch.setenv("PATH", os.pathsep.join([own_bin_directory, "/usr/bin"]))
    monkeypatch.setenv("VIRTUAL_ENV", sys.prefix)

    remove_own_virtual_environment()

    assert os.environ["PATH"] == "/usr/bin"
    assert "VIRTUAL_ENV" not in os.environ


def test_mise_is_isolated_from_the_caller(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("MISE_EXEC_AUTO_INSTALL", "true")
    monkeypatch.chdir(tmp_path)

    isolate_mise_from_the_caller()

    assert Path.cwd() == home
    assert os.environ["MISE_EXEC_AUTO_INSTALL"] == "false"
