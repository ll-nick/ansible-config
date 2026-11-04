import subprocess
from pathlib import Path

import pytest

from stk.machine import git_version
from stk.testing import run_with_mise


def test_the_git_config_is_valid() -> None:
    subprocess.run(["git", "config", "--list"], capture_output=True, check=True)


def test_the_git_config_is_linked_into_the_repository() -> None:
    gitconfig = Path.home() / ".gitconfig"

    assert gitconfig.is_symlink()
    assert (
        gitconfig.resolve() == Path(__file__).resolve().parent / "files" / "gitconfig"
    )


def test_delta_runs() -> None:
    assert run_with_mise("delta", "--version").strip()


def test_conflict_style_matches_the_git_version() -> None:
    version = git_version()
    assert version is not None
    expected = "zdiff3" if version >= (2, 35) else "diff3"

    conflict_style = Path.home() / ".config" / "git" / "conflict-style.gitconfig"

    assert expected in conflict_style.read_text()


def _repository_with_remote(directory: Path, url: str) -> Path:
    subprocess.run(["git", "init", "--quiet", str(directory)], check=True)
    subprocess.run(
        ["git", "-C", str(directory), "remote", "add", "origin", url], check=True
    )
    return directory


def _git_output(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def test_github_https_remotes_fetch_over_https_and_push_over_ssh(
    tmp_path: Path,
) -> None:
    repository = _repository_with_remote(tmp_path, "https://github.com/ll-nick/example")

    assert (
        _git_output(repository, "remote", "get-url", "origin")
        == "https://github.com/ll-nick/example"
    )
    assert (
        _git_output(repository, "remote", "get-url", "--push", "origin")
        == "git@github.com:ll-nick/example"
    )


@pytest.mark.parametrize(
    "url", ["https://github.com/ll-nick/example", "git@github.com:ll-nick/example"]
)
def test_github_remotes_use_the_github_identity(tmp_path: Path, url: str) -> None:
    repository = _repository_with_remote(tmp_path, url)

    assert _git_output(repository, "config", "user.name") == "ll-nick"
