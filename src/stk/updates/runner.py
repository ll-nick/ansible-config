from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import Console

from stk.enablement import SUDO_ENTRY, sudo_is_enabled
from stk.updates.step import (
    CommandFailedError,
    StepOutcome,
    UpdateContext,
    UpdateStep,
)
from stk.updates.timestamps import record_update


@dataclass(frozen=True)
class UnavailableStep:
    name: str
    reason: str


@dataclass(frozen=True)
class UpdatePlan:
    steps: tuple[UpdateStep, ...]
    unavailable: tuple[UnavailableStep, ...]


def plan_update_steps(steps: Sequence[UpdateStep]) -> UpdatePlan:
    sudo_enabled = sudo_is_enabled()
    runnable: list[UpdateStep] = []
    unavailable: list[UnavailableStep] = []
    for step in steps:
        unmet_requirement = step.unmet_requirement()
        if step.uses_sudo and not sudo_enabled:
            unavailable.append(
                UnavailableStep(step.name, f"needs `stk enable {SUDO_ENTRY}`")
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
