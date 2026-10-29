from pathlib import Path

from devstack.testing import run_with_mise

AUTOLOAD_DIRECTORY = Path.home() / ".local/share/nushell/vendor/autoload"


def test_nushell_runs() -> None:
    assert run_with_mise("nu", "--version").strip()


def test_generated_init_files_exist() -> None:
    assert (AUTOLOAD_DIRECTORY / "carapace.nu").read_text().strip()
    assert (AUTOLOAD_DIRECTORY / "00_mise.nu").read_text().strip()
