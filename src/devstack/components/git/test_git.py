import subprocess
from pathlib import Path

from devstack.machine import git_version
from devstack.testing import run_with_mise


def test_the_git_config_is_valid() -> None:
    subprocess.run(["git", "config", "--list"], capture_output=True, check=True)


def test_delta_runs() -> None:
    assert run_with_mise("delta", "--version").strip()


def test_conflict_style_matches_the_git_version() -> None:
    version = git_version()
    assert version is not None
    expected = "zdiff3" if version >= (2, 35) else "diff3"

    conflict_style = Path.home() / ".config" / "git" / "conflict-style.gitconfig"

    assert expected in conflict_style.read_text()
