from collections.abc import Sequence

from rich.console import Console

from devstack.updates.step import (
    CommandFailedError,
    StepOutcome,
    UpdateContext,
    UpdateStep,
)
from devstack.updates.timestamps import record_update, skipped_step_names


def run_update_steps(
    steps: Sequence[UpdateStep], context: UpdateContext, console: Console
) -> bool:
    """Runs the steps in order and returns whether all of them succeeded."""
    skipped_names = skipped_step_names()
    all_succeeded = True
    for step in steps:
        if step.name in skipped_names:
            console.print(
                f"[blue]⤼[/] {step.name} is disabled on this machine"
                + " (~/.config/stk/skip)"
            )
            continue
        unmet_requirement = step.unmet_requirement()
        if unmet_requirement is not None:
            console.print(
                f"[yellow]![/] {step.name} skipped: needs"
                + f" {unmet_requirement.description}"
            )
            continue
        try:
            outcome = step.run(context)
        except CommandFailedError as error:
            console.print(f"[red]✘[/] {step.name} failed: {error}")
            all_succeeded = False
            continue
        if outcome is StepOutcome.UPDATED:
            record_update(step.name)
    return all_succeeded
