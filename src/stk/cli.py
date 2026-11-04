from collections.abc import Sequence
from datetime import timedelta

import click
from rich import box
from rich.console import Console
from rich.table import Table

from stk.enablement import (
    EXCLUSION_PREFIX,
    SUDO_ENTRY,
    NothingEnabledError,
    disable,
    enable,
    enabled_component_names,
    enabled_entries,
    excluded_names,
    sudo_is_enabled,
    valid_entries,
)
from stk.engine.component import Component
from stk.engine.registry import (
    UnknownComponentError,
    direct_dependencies,
    select_components,
    without_skipped,
)
from stk.engine.runner import RunOptions, run_components
from stk.environment import (
    isolate_mise_from_the_caller,
    remove_own_virtual_environment,
)
from stk.privileged.sudo import SudoUnavailableError, obtain_sudo_password
from stk.privileged.system_packages import pending_sudo_work, with_privileged_work
from stk.reporting.composite_reporter import CompositeReporter
from stk.reporting.log_file_reporter import LogFileReporter
from stk.reporting.rich_reporter import RichReporter
from stk.setup import Setup
from stk.updates.check import check_updates, send_notification
from stk.updates.context import TerminalUpdateContext
from stk.updates.registry import all_update_steps
from stk.updates.runner import plan_update_steps, run_update_steps


@click.group()
@click.pass_context
def cli(context: click.Context) -> None:
    """Apply and update the setup of this machine."""
    # The configuration hands its Setup in as the context object
    handed_in: object = context.obj  # pyright: ignore[reportAny] - click leaves it untyped
    if not isinstance(handed_in, Setup):
        raise TypeError("stk needs a Setup to run, see stk.setup")
    remove_own_virtual_environment()


def require_enabled_entries() -> tuple[str, ...]:
    try:
        return enabled_entries()
    except NothingEnabledError as error:
        raise click.UsageError(str(error)) from error


def resolve_enabled_components(
    available: tuple[Component, ...],
) -> tuple[tuple[Component, ...], tuple[str, ...]]:
    """Returns what is enabled, and what is left out for needing an excluded component.

    Selecting a component pulls in its dependencies, so an exclusion has to be applied
    afterwards to also hold for a dependency of something still enabled.
    """
    entries = require_enabled_entries()
    names = enabled_component_names(entries, available)
    selected = select_components(names, available) if names else ()
    return without_skipped(selected, excluded_names(entries))


def enabled_components(available: tuple[Component, ...]) -> tuple[Component, ...]:
    return resolve_enabled_components(available)[0]


def names_to_enable(name: str, available: tuple[Component, ...]) -> list[str]:
    excluded = excluded_names(require_enabled_entries())
    disabled_dependencies = [
        component.name
        for component in select_components((name,), available)
        if component.name in excluded and component.name != name
    ]
    return [*disabled_dependencies, name]


def report_enabled(entries: Sequence[str], available: tuple[Component, ...]) -> None:
    click.echo(f"Enabled: {', '.join(entries) or 'nothing'}")
    _components, dependents = resolve_enabled_components(available)
    if dependents:
        click.echo(
            f"Left out for needing a disabled component: {', '.join(dependents)}"
        )


def reject_unknown_entries(
    names: Sequence[str], available: tuple[Component, ...]
) -> None:
    unknown_names = [name for name in names if name not in valid_entries(available)]
    if unknown_names:
        known_names = ", ".join(sorted(valid_entries(available)))
        raise click.UsageError(
            f"Unknown names: {', '.join(unknown_names)} (known: {known_names})"
        )


@cli.command("enable")
@click.argument("names", nargs=-1)
@click.pass_obj
def enable_command(setup: Setup, names: tuple[str, ...]) -> None:
    """Choose what this machine gets: components, `default` and `sudo`.

    Without NAMES, enables the default components. The first call on a machine
    always includes them; use `stk disable default` to opt out.
    """
    reject_unknown_entries(names, setup.components)
    report_enabled(enable(names), setup.components)


@cli.command("disable")
@click.argument("names", nargs=-1, required=True)
@click.pass_obj
def disable_command(setup: Setup, names: tuple[str, ...]) -> None:
    """Stop applying NAMES on this machine. Nothing installed is removed.

    Components that depend on a disabled component are left out as well.
    """
    entries = require_enabled_entries()
    # A name stk no longer knows can still be cleaned out of the list
    reject_unknown_entries(
        [name for name in names if name not in entries], setup.components
    )
    report_enabled(disable(names, setup.components), setup.components)


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
@click.option("-v", "--verbose", count=True, help="Show unchanged operations.")
@click.pass_obj
def apply(
    setup: Setup,
    component_names: tuple[str, ...],
    dry_run: bool,
    yes: bool,
    fail_on_change: bool,
    skipped_names: tuple[str, ...],
    verbose: int,
) -> None:
    """Apply COMPONENT_NAMES (default: all enabled) together with their dependencies.

    Asks for sudo only if `sudo` is enabled and something needs it.
    """
    reject_unknown_entries(skipped_names, setup.components)
    try:
        requested = (
            select_components(component_names, setup.components)
            if component_names
            else ()
        )
    except UnknownComponentError as error:
        raise click.UsageError(str(error)) from error
    enabled = enabled_components(setup.components)
    enabled_names = {component.name for component in enabled}
    for name in component_names:
        if name not in enabled_names:
            names = " ".join(names_to_enable(name, setup.components))
            raise click.UsageError(
                f"{name} is not enabled on this machine, run `stk enable {names}`"
            )

    entries = require_enabled_entries()
    for entry in entries:
        if entry.removeprefix(EXCLUSION_PREFIX) not in valid_entries(setup.components):
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
    sudo_work = pending_sudo_work(components) if SUDO_ENTRY not in skipped_names else []
    if sudo_work:
        click.echo(
            f"Needs sudo (--skip {SUDO_ENTRY} to leave out):"
            if sudo_allowed
            else f"Leaving out (`stk enable {SUDO_ENTRY}` if this machine may use it):"
        )
        for description in sudo_work:
            click.echo(f"  {description}")

    # A dry run must not ask for a password, so it leaves out what needs one
    privileged = bool(sudo_work) and sudo_allowed and not dry_run
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
        except EOFError:
            raise click.UsageError(
                f"Cannot ask for the sudo password here, use --skip {SUDO_ENTRY}."
            ) from None

    isolate_mise_from_the_caller()

    options = RunOptions(
        dry_run=dry_run,
        assume_yes=yes,
        fail_on_change=fail_on_change,
        sudo_password=sudo_password,
    )
    log_file_reporter = LogFileReporter()
    terminal_reporter = RichReporter(
        Console(), verbose, log_path=log_file_reporter.log_path
    )
    reporter = CompositeReporter([terminal_reporter, log_file_reporter])
    runnable = with_privileged_work(components) if privileged else components
    raise SystemExit(run_components(runnable, options, reporter))


def component_status(component: Component, enabled_names: set[str] | None) -> str:
    if component.unmet_requirement() is not None:
        return "[yellow]not applicable[/]"
    if enabled_names is None:
        return ""
    if component.name in enabled_names:
        return "[green]enabled[/]"
    return "[dim]not enabled[/]"


def described_requirements(component: Component) -> str:
    return ", ".join(
        requirement.description
        if requirement.is_met()
        else f"[yellow]{requirement.description}[/]"
        for requirement in component.requires
    )


@cli.command("list")
@click.pass_obj
def list_components(setup: Setup) -> None:
    """List the available components."""
    try:
        enabled_names = {
            component.name for component in enabled_components(setup.components)
        }
    except click.UsageError:
        enabled_names = None

    table = Table(box=box.SIMPLE_HEAD, pad_edge=False)
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Needs")
    table.add_column("Requires")
    for component in setup.components:
        table.add_row(
            component.name,
            component_status(component, enabled_names),
            ", ".join(direct_dependencies(component, setup.components)),
            described_requirements(component),
        )

    console = Console()
    console.print(table)
    if enabled_names is None:
        console.print("Nothing is enabled on this machine yet, see `stk enable`.")


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
@click.pass_obj
def update(
    setup: Setup,
    step_names: tuple[str, ...],
    dry_run: bool,
    bump: bool,
    yes: bool,
    skipped_names: tuple[str, ...],
) -> None:
    """Update the system and the tools (default: all STEP_NAMES)."""
    all_steps = all_update_steps(setup.checkout, enabled_components(setup.components))
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
@click.pass_obj
def check(setup: Setup, reminder_days: int, notify: bool) -> None:
    """Show when each update step last ran."""
    try:
        components = enabled_components(setup.components)
    except click.UsageError as error:
        if notify:
            send_notification(Console(), "stk has nothing enabled", error.message)
        raise
    check_updates(
        all_update_steps(setup.checkout, components),
        Console(),
        reminder_time=timedelta(days=reminder_days),
        notify=notify,
    )
