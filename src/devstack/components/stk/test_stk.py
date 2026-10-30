import os
from pathlib import Path


def test_the_shim_is_installed_and_executable() -> None:
    shim = Path.home() / ".local/bin/stk"

    assert os.access(shim, os.X_OK)
