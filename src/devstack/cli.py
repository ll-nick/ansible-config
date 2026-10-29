import click

from devstack.components import COMPONENTS
from devstack.plain_reporter import PlainReporter
from devstack.registry import UnknownComponentError, select_components
from devstack.runner import RunOptions, run_components


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
@click.option("-v", "--verbose", count=True, help="Show unchanged operations.")
def apply(
    component_names: tuple[str, ...],
    dry_run: bool,
    yes: bool,
    fail_on_change: bool,
    verbose: int,
) -> None:
    """Apply COMPONENT_NAMES (default: all) together with their dependencies."""
    try:
        components = select_components(component_names)
    except UnknownComponentError as error:
        raise click.UsageError(str(error)) from error

    options = RunOptions(dry_run=dry_run, assume_yes=yes, fail_on_change=fail_on_change)
    raise SystemExit(run_components(components, options, PlainReporter(verbose)))


@cli.command("list")
def list_components() -> None:
    """List the available components."""
    for component in COMPONENTS:
        dependencies = ", ".join(component.depends_on)
        suffix = f" (needs {dependencies})" if dependencies else ""
        click.echo(f"{component.name}{suffix}")
