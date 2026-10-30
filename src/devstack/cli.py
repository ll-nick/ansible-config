from datetime import timedelta

import click
from rich.console import Console

from devstack.components import COMPONENTS
from devstack.composite_reporter import CompositeReporter
from devstack.log_file_reporter import LogFileReporter
from devstack.plain_reporter import PlainReporter
from devstack.registry import UnknownComponentError, select_components
from devstack.reporting import Reporter
from devstack.rich_reporter import RichReporter
from devstack.runner import RunOptions, run_components
from devstack.sudo import SudoUnavailableError, obtain_sudo_password
from devstack.updates import UPDATE_STEPS
from devstack.updates.check import check_updates
from devstack.updates.context import TerminalUpdateContext
from devstack.updates.runner import run_update_steps


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("component_names", nargs=-1)
@click.option("-n", "--dry-run", is_flag=True, help="Show the plan and stop.")
@click.option("-y", "--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.option(
    "--fail-on-change",
    is_flag=True,
    help="Exit with status 3 if any operation changed something.",
)
@click.option(
    "-j",
    "--jobs",
    default=4,
    show_default=True,
    help="Components to apply concurrently.",
)
@click.option(
    "--privileged",
    is_flag=True,
    help="Also apply the parts that need root (installs system packages via sudo).",
)
@click.option("--plain", is_flag=True, help="Use plain output even on a terminal.")
@click.option("-v", "--verbose", count=True, help="Show unchanged operations.")
def apply(
    component_names: tuple[str, ...],
    dry_run: bool,
    yes: bool,
    fail_on_change: bool,
    jobs: int,
    privileged: bool,
    plain: bool,
    verbose: int,
) -> None:
    """Apply COMPONENT_NAMES (default: all) together with their dependencies."""
    try:
        components = select_components(component_names)
    except UnknownComponentError as error:
        raise click.UsageError(str(error)) from error
    for component in components:
        requirement = component.unmet_requirement()
        if component.name in component_names and requirement is not None:
            raise click.UsageError(
                f"{component.name} is not applicable here "
                + f"(requires {requirement.description})"
            )

    sudo_password = None
    if privileged:
        try:
            sudo_password = obtain_sudo_password()
        except SudoUnavailableError as error:
            raise click.UsageError(str(error)) from error

    options = RunOptions(
        dry_run=dry_run,
        assume_yes=yes,
        fail_on_change=fail_on_change,
        jobs=jobs,
        privileged=privileged,
        sudo_password=sudo_password,
    )
    log_file_reporter = LogFileReporter()
    terminal_reporter = build_terminal_reporter(verbose, plain, log_file_reporter)
    reporter = CompositeReporter([terminal_reporter, log_file_reporter])
    raise SystemExit(run_components(components, options, reporter))


def build_terminal_reporter(
    verbosity: int, plain: bool, log_file_reporter: LogFileReporter
) -> Reporter:
    console = Console()
    if plain or not console.is_terminal or console.is_dumb_terminal:
        return PlainReporter(verbosity, log_path=log_file_reporter.log_path)
    return RichReporter(console, verbosity, log_path=log_file_reporter.log_path)


@cli.command("list")
def list_components() -> None:
    """List the available components."""
    for component in COMPONENTS:
        details: list[str] = []
        if component.depends_on:
            details.append(f"needs {', '.join(component.depends_on)}")
        for requirement in component.requires:
            details.append(f"requires {requirement.description}")
        if component.unmet_requirement() is not None:
            details.append("not applicable here")
        suffix = f" ({'; '.join(details)})" if details else ""
        click.echo(f"{component.name}{suffix}")


@cli.command()
@click.argument("step_names", nargs=-1)
@click.option("-b", "--bump", is_flag=True, help="Bump versions of locked components.")
@click.option("-y", "--yes", is_flag=True, help="Assume yes for all prompts.")
def update(step_names: tuple[str, ...], bump: bool, yes: bool) -> None:
    """Update the system and the tools (default: all STEP_NAMES)."""
    known_names = [step.name for step in UPDATE_STEPS]
    unknown_names = [name for name in step_names if name not in known_names]
    if unknown_names:
        raise click.UsageError(
            f"Unknown steps: {', '.join(unknown_names)}"
            + f" (known: {', '.join(known_names)})"
        )
    steps = [step for step in UPDATE_STEPS if not step_names or step.name in step_names]

    console = Console()
    context = TerminalUpdateContext(console, assume_yes=yes, bump_versions=bump)
    succeeded = run_update_steps(steps, context, console)
    if succeeded and not step_names:
        console.print("\n[green]✔[/] All updates completed")
    raise SystemExit(0 if succeeded else 1)


@cli.command()
@click.option(
    "-r",
    "--reminder-days",
    default=7,
    show_default=True,
    help="Days after which a step counts as out of date.",
)
@click.option("-n", "--notify", is_flag=True, help="Send a desktop notification.")
def check(reminder_days: int, notify: bool) -> None:
    """Show when each update step last ran."""
    check_updates(
        UPDATE_STEPS,
        Console(),
        reminder_time=timedelta(days=reminder_days),
        notify=notify,
    )
