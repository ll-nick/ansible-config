import json
import os
import subprocess
from pathlib import Path

from devstack.mise import mise_exec
from devstack.testing import run_with_mise

AUTOLOAD_DIRECTORY = Path.home() / ".local/share/nushell/vendor/autoload"


def test_nushell_runs() -> None:
    assert run_with_mise("nu", "--version").strip()


def test_generated_init_files_exist() -> None:
    assert (AUTOLOAD_DIRECTORY / "carapace.nu").read_text().strip()


def test_every_session_activates_mise_with_its_own_path(tmp_path: Path) -> None:
    environment = {**os.environ, "PATH": f"/session/directory:{os.environ['PATH']}"}
    # A login shell runs config.nu, but only an interactive one reads the autoload files
    subprocess.run(
        [*mise_exec("nu"), "--login", "--commands", "null"],
        capture_output=True,
        check=True,
        env=environment,
    )
    activation = tmp_path / "mise_activation.nu"
    activation.write_text((AUTOLOAD_DIRECTORY / "00_mise.nu").read_text())

    completed = subprocess.run(
        [
            *mise_exec("nu"),
            "--no-config-file",
            "--commands",
            f"use {activation}; $env.PATH | to json",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )

    assert "/session/directory" in json.loads(completed.stdout)
