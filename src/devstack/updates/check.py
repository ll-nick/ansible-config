import shutil
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from rich.console import Console
from rich.table import Table

from devstack.updates.step import UpdateStep
from devstack.updates.timestamps import last_update, skipped_step_names

SECONDS_PER_HOUR = 3600


@dataclass(frozen=True)
class StepFreshness:
    step_name: str
    age_description: str
    is_stale: bool


def describe_age(elapsed: timedelta) -> str:
    if elapsed >= timedelta(days=1):
        days = elapsed.days
        return "1 day ago" if days == 1 else f"{days} days ago"
    hours = int(elapsed.total_seconds() // SECONDS_PER_HOUR)
    return "1 hour ago" if hours == 1 else f"{hours} hours ago"


def collect_freshness(
    steps: Sequence[UpdateStep],
    reminder_time: timedelta,
    now: datetime | None = None,
) -> list[StepFreshness]:
    now = now or datetime.now(UTC)
    skipped_names = skipped_step_names()
    freshness: list[StepFreshness] = []
    for step in steps:
        if step.name in skipped_names:
            continue
        updated_at = last_update(step.name)
        if updated_at is None:
            freshness.append(StepFreshness(step.name, "never", is_stale=True))
            continue
        elapsed = now - updated_at
        freshness.append(
            StepFreshness(step.name, describe_age(elapsed), elapsed >= reminder_time)
        )
    return freshness


def check_updates(
    steps: Sequence[UpdateStep],
    console: Console,
    *,
    reminder_time: timedelta,
    notify: bool,
) -> None:
    freshness = collect_freshness(steps, reminder_time)

    table = Table("step", "last updated", box=None, pad_edge=False)
    for entry in freshness:
        style = "yellow" if entry.is_stale else None
        table.add_row(entry.step_name, entry.age_description, style=style)
    console.print(table)

    stale_names = [entry.step_name for entry in freshness if entry.is_stale]
    if notify and stale_names:
        _send_notification(console, stale_names)


def _send_notification(console: Console, stale_names: Sequence[str]) -> None:
    if shutil.which("notify-send") is None:
        console.print("[yellow]![/] notify-send not found, cannot send a notification")
        return
    subprocess.run(
        [
            "notify-send",
            "System out of date",
            f"{', '.join(stale_names)} haven't been updated recently."
            + " Consider running 'stk update'.",
        ],
        check=False,
    )
