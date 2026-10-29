from pathlib import Path

import pytest

from devstack.commands import run_command
from devstack.component import Component
from devstack.file_copy import copy_file
from devstack.plain_reporter import PlainReporter
from devstack.pyinfra_adapters import component_deploy
from devstack.reporting import ComponentOutcome
from devstack.runner import RunOptions, run_components

COMPONENT_COUNT = 6
FILES_PER_COMPONENT = 4


def make_component(name: str, source: Path, destination: Path) -> Component:
    @component_deploy(name)
    def apply() -> None:
        for index in range(FILES_PER_COMPONENT):
            copy_file(source, destination / name / f"file-{index}")
        run_command("Pause", "sleep 0.2")

    return Component(name, apply)


@pytest.mark.parametrize("attempt", range(3))
def test_components_with_facts_can_run_concurrently(
    attempt: int, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "source"
    source.write_text(f"content {attempt}")
    destination = tmp_path / "destination"
    components = [
        make_component(f"component{index}", source, destination)
        for index in range(COMPONENT_COUNT)
    ]

    exit_code = run_components(
        components,
        RunOptions(dry_run=False, assume_yes=True, fail_on_change=False, jobs=6),
        PlainReporter(verbosity=0),
    )

    assert exit_code == 0, capsys.readouterr().out
    for component in components:
        for index in range(FILES_PER_COMPONENT):
            copied = destination / component.name / f"file-{index}"
            assert copied.read_text() == f"content {attempt}"


def test_outcomes_enum_is_importable() -> None:
    assert ComponentOutcome.SUCCEEDED.value == "succeeded"
