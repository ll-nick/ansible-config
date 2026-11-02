from collections.abc import Sequence
from datetime import timedelta

import click
from rich.console import Console

from stk.component import Component
from stk.components import COMPONENTS
from stk.composite_reporter import CompositeReporter
from stk.enablement import (
    SUDO_ENTRY,
    NothingEnabledError,
    disable,
    enable,
    enabled_component_names,
    enabled_entries,
    sudo_is_enabled,
    valid_entries,
)
from stk.environment import (
    isolate_mise_from_the_caller,
    remove_own_virtual_environment,
)
from stk.log_file_reporter import LogFileReporter
from stk.plain_reporter import PlainReporter
from stk.registry import UnknownComponentError, select_components, without_skipped
from stk.reporting import Reporter
from stk.rich_reporter import RichReporter
from stk.run_settings import PRIVILEGED, RunSettings, configure_run_settings
from stk.runner import RunOptions, run_components
from stk.sudo import SudoUnavailableError, obtain_sudo_password
from stk.system_packages import missing_system_packages, pending_sudo_work
from stk.updates.check import check_updates, send_notification
from stk.updates.context import TerminalUpdateContext
from stk.updates.registry import all_update_steps
from stk.updates.runner import plan_update_steps, run_update_steps


@click.group()
def cli() -> None:
    remove_own_virtual_environment()


def require_enabled_entries() -> tuple[str, ...]:
    try:
        return enabled_entries()
    except NothingEnabledError as error:
        raise click.UsageError(str(error)) from error


def enabled_components() -> tuple[Component, ...]:
    names = enabled_component_names(require_enabled_entries(), COMPONENTS)
    return select_components(names) if names else ()


def reject_unknown_entries(names: Sequence[str]) -> None:
    unknown_names = [name for name in names if name not in valid_entries(COMPONENTS)]
    if unknown_names:
        known_names = ", ".join(sorted(valid_entries(COMPONENTS)))
        raise click.UsageError(
            f"Unknown names: {', '.join(unknown_names)} (known: {known_names})"
        )


@cli.command("enable")
@click.argument("names", nargs=-1)
def enable_command(names: tuple[str, ...]) -> None:
    """Choose what this machine gets: components, `default` and `sudo`.

    Without NAMES, enables the default components. The first call on a machine
    always includes them; use `stk disable default` to opt out.
    """
    reject_unknown_entries(names)
    click.echo(f"Enabled: {', '.join(enable(names)) or 'nothing'}")


@cli.command("disable")
@click.argument("names", nargs=-1, required=True)
def disable_command(names: tuple[str, ...]) -> None:
    """Stop applying NAMES on this machine. Nothing installed is removed."""
    require_enabled_entries()
    click.echo(f"Enabled: {', '.join(disable(names)) or 'nothing'}")


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
    "--skip",
    "skipped_names",
    multiple=True,
    help=f"Leave out a component and its dependents, or `{SUDO_ENTRY}`. Repeatable.",
)
@click.option("--plain", is_flag=True, help="Use plain output even on a terminal.")
@click.option("-v", "--verbose", count=True, help="Show unchanged operations.")
def apply(
    component_names: tuple[str, ...],
    dry_run: bool,
    yes: bool,
    fail_on_change: bool,
    skipped_names: tuple[str, ...],
    plain: bool,
    verbose: int,
) -> None:
    """Apply COMPONENT_NAMES (default: all enabled) together with their dependencies.

    Asks for sudo only if `sudo` is enabled and something needs it.
    """
    reject_unknown_entries(skipped_names)
    try:
        requested = select_components(component_names) if component_names else ()
    except UnknownComponentError as error:
        raise click.UsageError(str(error)) from error
    enabled = enabled_components()
    enabled_names = {component.name for component in enabled}
    for name in component_names:
        if name not in enabled_names:
            raise click.UsageError(
                f"{name} is not enabled on this machine, run `stk enable {name}`"
            )

    entries = require_enabled_entries()
    for entry in entries:
        if entry not in valid_entries(COMPONENTS):
            click.echo(f"Ignoring unknown name in the enabled list: {entry}", err=True)

    components, dependents = without_skipped(
        requested or enabled, [name for name in skipped_names if name != SUDO_ENTRY]
    )
    if dependents:
        click.echo(f"Also skipping dependents: {', '.join(dependents)}")
    if not components:
        click.echo("Nothing to apply")
        raise SystemExit(0)

    sudo_allowed = sudo_is_enabled() and SUDO_ENTRY not in skipped_names
    sudo_work = pending_sudo_work(components) if sudo_allowed else []
    if sudo_work:
        click.echo(f"Needs sudo (--skip {SUDO_ENTRY} to leave out):")
        for description in sudo_work:
            click.echo(f"  {description}")
    if not sudo_is_enabled():
        missing_packages = missing_system_packages(components)
        if missing_packages:
            click.echo(
                f"Not installing {', '.join(missing_packages)}:"
                + f" run `stk enable {SUDO_ENTRY}` if this machine may use sudo"
            )

    # A dry run must not ask for a password, so it leaves out what needs one
    privileged = bool(sudo_work) and not dry_run
    configure_run_settings(RunSettings(privileged=privileged))
    for component in components:
        requirement = component.unmet_requirement()
        if requirement is PRIVILEGED and sudo_allowed:
            continue
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
        except EOFError:
            raise click.UsageError(
                f"Cannot ask for the sudo password here, use --skip {SUDO_ENTRY}."
            ) from None

    isolate_mise_from_the_caller()

    options = RunOptions(
        dry_run=dry_run,
        assume_yes=yes,
        fail_on_change=fail_on_change,
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
    try:
        enabled_names = {component.name for component in enabled_components()}
    except click.UsageError:
        enabled_names = None
    for component in COMPONENTS:
        details: list[str] = []
        if component.depends_on:
            details.append(f"needs {', '.join(component.depends_on)}")
        for requirement in component.requires:
            details.append(f"requires {requirement.description}")
        if component.unmet_requirement() not in (None, PRIVILEGED):
            details.append("not applicable here")
        if enabled_names is not None and component.name not in enabled_names:
            details.append("not enabled")
        suffix = f" ({'; '.join(details)})" if details else ""
        click.echo(f"{component.name}{suffix}")


@cli.command()
@click.argument("step_names", nargs=-1)
@click.option("-n", "--dry-run", is_flag=True, help="Show the plan and stop.")
@click.option("-b", "--bump", is_flag=True, help="Bump versions of locked components.")
@click.option("-y", "--yes", is_flag=True, help="Skip the confirmation prompt.")
@click.option(
    "--skip",
    "skipped_names",
    multiple=True,
    help=f"Leave out a step, or everything using `{SUDO_ENTRY}`. Repeatable.",
)
def update(
    step_names: tuple[str, ...],
    dry_run: bool,
    bump: bool,
    yes: bool,
    skipped_names: tuple[str, ...],
) -> None:
    """Update the system and the tools (default: all STEP_NAMES)."""
    all_steps = all_update_steps(enabled_components())
    known_names = [step.name for step in all_steps]
    unknown_names = [
        name
        for name in (*step_names, *skipped_names)
        if name not in (*known_names, SUDO_ENTRY)
    ]
    if unknown_names:
        raise click.UsageError(
            f"Unknown steps: {', '.join(unknown_names)}"
            + f" (known: {', '.join(known_names)})"
        )
    plan = plan_update_steps(
        [
            step
            for step in all_steps
            if (not step_names or step.name in step_names)
            and step.name not in skipped_names
            and not (step.uses_sudo and SUDO_ENTRY in skipped_names)
        ]
    )

    console = Console()
    for unavailable in plan.unavailable:
        console.print(f"[yellow]![/] {unavailable.name} skipped: {unavailable.reason}")
    if not plan.steps:
        console.print("Nothing to update")
        raise SystemExit(0)
    described_steps = [
        f"{step.name} (sudo)" if step.uses_sudo else step.name for step in plan.steps
    ]
    console.print(f"Will update: {', '.join(described_steps)}")
    if dry_run:
        raise SystemExit(0)

    context = TerminalUpdateContext(
        console,
        assume_yes=yes,
        bump_versions=bump,
        may_use_sudo=SUDO_ENTRY not in skipped_names
        and not any(
            step.uses_sudo and step.name in skipped_names for step in all_steps
        ),
    )
    if not yes:
        try:
            confirmed = context.confirm("Proceed?")
        except EOFError:
            console.print("Cannot ask for confirmation without a terminal, use --yes.")
            raise SystemExit(1) from None
        if not confirmed:
            raise SystemExit(1)

    succeeded = run_update_steps(plan.steps, context, console)
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
    try:
        components = enabled_components()
    except click.UsageError as error:
        if notify:
            send_notification(Console(), "stk has nothing enabled", error.message)
        raise
    check_updates(
        all_update_steps(components),
        Console(),
        reminder_time=timedelta(days=reminder_days),
        notify=notify,
    )
