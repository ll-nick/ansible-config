import os
import shutil
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import final

import pytest
from rich.console import Console

from stk.cli import COMPONENTS
from stk.components.mise.mise import update_mise
from stk.enablement import enable
from stk.engine.component import Component
from stk.engine.requirement import Requirement
from stk.engine.update_step import (
    CommandFailedError,
    StepOutcome,
    UpdateContext,
    UpdateStep,
)
from stk.updates.check import collect_freshness, describe_age
from stk.updates.registry import (
    CORE_UPDATE_STEPS,
    all_update_steps,
    component_update_steps,
)
from stk.updates.runner import plan_update_steps, run_update_steps
from stk.updates.steps import system
from stk.updates.timestamps import last_update, record_update
from stk.updates.version_bump import commit_and_offer_push


@final
class RecordingContext:
    def __init__(self, *, answers: bool = True) -> None:
        self.bump_versions: bool = False
        self.may_use_sudo: bool = True
        self.answers: bool = answers
        self.nothing_staged: bool = False
        self.commands: list[list[str]] = []
        self.environments: list[Mapping[str, str] | None] = []

    def section(self, _title: str, /) -> None:
        pass

    def confirm(self, _question: str, /) -> bool:
        return self.answers

    def note(self, _message: str, /) -> None:
        pass

    def succeeds(
        self, command: Sequence[str], *, working_directory: Path | None = None
    ) -> bool:
        del working_directory
        self.commands.append(list(command))
        return self.nothing_staged

    def run(
        self,
        command: Sequence[str],
        *,
        working_directory: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        del working_directory
        self.commands.append(list(command))
        self.environments.append(environment)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))


def test_step_names_are_unique() -> None:
    names = [step.name for step in all_update_steps(COMPONENTS)]

    assert len(names) == len(set(names))


def test_core_steps_run_before_component_steps_and_mise_before_its_dependents() -> None:
    names = [step.name for step in all_update_steps(COMPONENTS)]

    assert names[: len(CORE_UPDATE_STEPS)] == [step.name for step in CORE_UPDATE_STEPS]
    assert names.index("mise") < names.index("tmux")
    assert names.index("mise") < names.index("neovim")


def test_a_component_step_needs_its_component_to_apply_here() -> None:
    not_applicable = Requirement("another machine", lambda: False)
    components = (
        Component(
            "first",
            lambda: None,
            requires=(not_applicable,),
            update=UpdateStep("first", lambda _: StepOutcome.UPDATED),
        ),
        Component("second", lambda: None),
    )

    (step,) = component_update_steps(components)

    assert step.unmet_requirement() == not_applicable


def test_sudo_and_impossible_steps_are_left_out_of_the_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    enable(())
    steps = [
        UpdateStep("available", lambda _: StepOutcome.UPDATED),
        UpdateStep("root", lambda _: StepOutcome.UPDATED, uses_sudo=True),
        UpdateStep(
            "impossible",
            lambda _: StepOutcome.UPDATED,
            requires=(Requirement("a thing", lambda: False),),
        ),
    ]

    plan = plan_update_steps(steps)

    assert [step.name for step in plan.steps] == ["available"]
    assert {entry.name: entry.reason for entry in plan.unavailable} == {
        "root": "needs `stk enable sudo`",
        "impossible": "needs a thing",
    }

    enable(("sudo",))

    assert [step.name for step in plan_update_steps(steps).steps] == [
        "available",
        "root",
    ]


def test_timestamps_round_trip() -> None:
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

    record_update("mise", moment)

    assert last_update("mise") == moment
    assert last_update("tmux") is None


@pytest.mark.parametrize(
    ("elapsed", "expected"),
    [
        (timedelta(hours=1, minutes=5), "1 hour ago"),
        (timedelta(hours=5), "5 hours ago"),
        (timedelta(days=1, hours=3), "1 day ago"),
        (timedelta(days=9), "9 days ago"),
    ],
)
def test_ages_are_described(elapsed: timedelta, expected: str) -> None:
    assert describe_age(elapsed) == expected


def test_stale_and_never_updated_steps_are_flagged() -> None:
    now = datetime(2026, 1, 20, tzinfo=UTC)
    record_update("mise", now - timedelta(days=1))
    record_update("tmux", now - timedelta(days=10))
    steps = [
        UpdateStep(name, lambda _: StepOutcome.UPDATED)
        for name in ("mise", "tmux", "neovim")
    ]

    freshness = {
        entry.step_name: entry.is_stale
        for entry in collect_freshness(steps, timedelta(days=7), now)
    }

    assert freshness == {"mise": False, "tmux": True, "neovim": True}


def test_sudo_steps_are_not_reported_where_sudo_is_not_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    enable(())
    steps = [
        UpdateStep("system", lambda _: StepOutcome.UPDATED, uses_sudo=True),
        UpdateStep("mise", lambda _: StepOutcome.UPDATED),
    ]

    names = [e.step_name for e in collect_freshness(steps, timedelta(days=7))]

    assert names == ["mise"]


def test_a_skipped_step_is_not_recorded_and_a_failure_does_not_stop_the_rest() -> None:
    def failing(_context: UpdateContext) -> StepOutcome:
        raise CommandFailedError(["boom"], 1)

    steps = [
        UpdateStep("skipped", lambda _: StepOutcome.SKIPPED),
        UpdateStep("failing", failing),
        UpdateStep("updated", lambda _: StepOutcome.UPDATED),
    ]

    succeeded = run_update_steps(steps, RecordingContext(), Console(quiet=True))

    assert not succeeded
    assert last_update("skipped") is None
    assert last_update("failing") is None
    assert last_update("updated") is not None


def test_mise_is_updated_with_prebuilt_binaries() -> None:
    context = RecordingContext()

    assert update_mise(context) is StepOutcome.UPDATED

    assert [command[1:] for command in context.commands] == [
        ["self-update", "--yes"],
        ["upgrade", "--yes"],
    ]
    assert all(
        env == {"MISE_NODE_COMPILE": "false", "MISE_PYTHON_COMPILE": "false"}
        for env in context.environments
    )


def test_apt_upgrade_runs_without_further_prompts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def fake_which(name: str) -> str:
        return f"/usr/bin/{name}"

    monkeypatch.setattr(shutil, "which", fake_which)
    context = RecordingContext()

    system.update_system(context)

    assert context.commands == [
        ["sudo", "apt", "update"],
        ["sudo", "apt", "upgrade", "--yes"],
    ]


def test_environment_is_not_modified() -> None:
    before = dict(os.environ)

    update_mise(RecordingContext())

    assert dict(os.environ) == before


def test_version_bumps_without_changes_are_not_committed() -> None:
    context = RecordingContext()
    context.nothing_staged = True

    commit_and_offer_push(context, Path("/repository"), "flake.lock")

    assert ["git", "commit", "-m", "Version bump"] not in context.commands


def test_version_bumps_with_changes_are_committed() -> None:
    context = RecordingContext()

    commit_and_offer_push(context, Path("/repository"), "flake.lock")

    assert ["git", "commit", "-m", "Version bump"] in context.commands


def test_steps_that_cannot_run_here_are_not_reported_as_stale() -> None:
    impossible = Requirement("a thing", lambda: False)
    steps = [
        UpdateStep("possible", lambda _: StepOutcome.UPDATED),
        UpdateStep("impossible", lambda _: StepOutcome.UPDATED, requires=(impossible,)),
    ]

    names = [entry.step_name for entry in collect_freshness(steps, timedelta(days=7))]

    assert names == ["possible"]
