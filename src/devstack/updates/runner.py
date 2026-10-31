from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import Console

from devstack.updates.step import (
    CommandFailedError,
    StepOutcome,
    UpdateContext,
    UpdateStep,
)
from devstack.updates.timestamps import record_update, skipped_step_names


@dataclass(frozen=True)
class UnavailableStep:
    name: str
    reason: str


@dataclass(frozen=True)
class UpdatePlan:
    steps: tuple[UpdateStep, ...]
    unavailable: tuple[UnavailableStep, ...]


def plan_update_steps(steps: Sequence[UpdateStep]) -> UpdatePlan:
    skipped_names = skipped_step_names()
    runnable: list[UpdateStep] = []
    unavailable: list[UnavailableStep] = []
    for step in steps:
        unmet_requirement = step.unmet_requirement()
        if step.name in skipped_names:
            unavailable.append(
                UnavailableStep(step.name, "disabled in ~/.config/stk/skip")
            )
        elif unmet_requirement is not None:
            unavailable.append(
                UnavailableStep(step.name, f"needs {unmet_requirement.description}")
            )
        else:
            runnable.append(step)
    return UpdatePlan(tuple(runnable), tuple(unavailable))


def run_update_steps(
    steps: Sequence[UpdateStep], context: UpdateContext, console: Console
) -> bool:
    """Runs the steps in order and returns whether all of them succeeded."""
    all_succeeded = True
    for step in steps:
        try:
            outcome = step.run(context)
        except CommandFailedError as error:
            console.print(f"[red]✘[/] {step.name} failed: {error}")
            all_succeeded = False
            continue
        if outcome is StepOutcome.UPDATED:
            record_update(step.name)
    return all_succeeded
