from pathlib import Path

import pytest
from rich.console import Console

from stk.component import Component
from stk.links import replaced_files_directory, symlink_file
from stk.pyinfra_adapters import component_deploy
from stk.rich_reporter import RichReporter
from stk.runner import RunOptions, run_components


def link_with_a_run(source: Path, destination: Path) -> None:
    @component_deploy("linking")
    def apply() -> None:
        symlink_file(source, destination)

    exit_code = run_components(
        [Component("linking", apply)],
        RunOptions(dry_run=False, assume_yes=True, fail_on_change=False),
        RichReporter(Console(), 0),
    )

    assert exit_code == 0


@pytest.fixture(autouse=True)
def separate_state_directory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


def test_a_replaced_file_moves_out_of_its_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_text("new")
    config_directory = tmp_path / "config"
    config_directory.mkdir()
    destination = config_directory / "snippet.bash"
    destination.write_text("old")

    link_with_a_run(source, destination)

    assert destination.resolve() == source
    assert list(config_directory.iterdir()) == [destination]
    backups = list(replaced_files_directory(destination).iterdir())
    assert [backup.read_text() for backup in backups] == ["old"]
    assert backups[0].name.startswith("snippet.bash.")


def test_a_correct_link_stays_without_a_backup(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.write_text("new")
    destination = tmp_path / "link"
    destination.symlink_to(source)

    link_with_a_run(source, destination)

    assert destination.resolve() == source
    assert not replaced_files_directory(destination).exists()
