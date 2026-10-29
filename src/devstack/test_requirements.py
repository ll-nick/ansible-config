from collections.abc import Sequence
from typing import override

import pytest
from click.testing import CliRunner

from devstack import cli as cli_module
from devstack.component import Component, Requirement
from devstack.plain_reporter import PlainReporter
from devstack.reporting import ComponentOutcome, ComponentResult
from devstack.runner import RunOptions, run_components

UNMET = Requirement("a display", lambda: False)
MET = Requirement("a shell", lambda: True)


def noop() -> None:
    pass


class RecordingReporter(PlainReporter):
    def __init__(self) -> None:
        super().__init__(verbosity=0)
        self.outcomes: dict[str, ComponentOutcome] = {}

    @override
    def component_finished(self, result: ComponentResult) -> None:
        self.outcomes[result.component_name] = result.outcome
        super().component_finished(result)


def test_unmet_requirement_is_reported_and_met_one_is_not() -> None:
    assert Component("a", noop, requires=(MET, UNMET)).unmet_requirement() is UNMET
    assert Component("b", noop, requires=(MET,)).unmet_requirement() is None
    assert Component("c", noop).unmet_requirement() is None


def test_not_applicable_components_are_no_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    reporter = RecordingReporter()

    exit_code = run_components(
        [Component("gui", noop, requires=(UNMET,)), Component("cli", noop)],
        RunOptions(dry_run=False, assume_yes=True, fail_on_change=False),
        reporter,
    )

    assert exit_code == 0
    assert reporter.outcomes["gui"] is ComponentOutcome.NOT_APPLICABLE
    assert reporter.outcomes["cli"] is ComponentOutcome.SUCCEEDED
    assert "gui" not in capsys.readouterr().out


def test_dependents_of_a_not_applicable_component_are_skipped() -> None:
    reporter = RecordingReporter()

    exit_code = run_components(
        [
            Component("gui", noop, requires=(UNMET,)),
            Component("theme", noop, depends_on=("gui",)),
        ],
        RunOptions(dry_run=False, assume_yes=True, fail_on_change=False),
        reporter,
    )

    assert reporter.outcomes["theme"] is ComponentOutcome.SKIPPED
    assert exit_code == 1


def test_explicitly_requesting_an_inapplicable_component_is_a_usage_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gui = Component("gui", noop, requires=(UNMET,))

    def select_gui(_names: Sequence[str]) -> tuple[Component, ...]:
        return (gui,)

    monkeypatch.setattr(cli_module, "select_components", select_gui)

    result = CliRunner().invoke(cli_module.cli, ["apply", "gui"])

    assert result.exit_code == 2
    assert "gui is not applicable here (requires a display)" in result.output
