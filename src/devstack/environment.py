import os
import sys
from pathlib import Path


def remove_own_virtual_environment() -> None:
    """Keeps the virtual environment devstack runs in out of what it generates.

    `uv run` puts the environment's bin directory first on PATH, and tools like
    `mise activate` would bake that into the shell setup of every future session.
    """
    own_bin_directory = Path(sys.prefix) / "bin"
    os.environ.pop("VIRTUAL_ENV", None)
    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    os.environ["PATH"] = os.pathsep.join(
        entry for entry in path_entries if Path(entry) != own_bin_directory
    )
