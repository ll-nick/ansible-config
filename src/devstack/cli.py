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
@click.option("--plain", is_flag=True, help="Use plain output even on a terminal.")
@click.option("-v", "--verbose", count=True, help="Show unchanged operations.")
def apply(
    component_names: tuple[str, ...],
    dry_run: bool,
    yes: bool,
    fail_on_change: bool,
    jobs: int,
    plain: bool,
    verbose: int,
) -> None:
    """Apply COMPONENT_NAMES (default: all) together with their dependencies."""
    try:
        components = select_components(component_names)
    except UnknownComponentError as error:
        raise click.UsageError(str(error)) from error

    options = RunOptions(
        dry_run=dry_run, assume_yes=yes, fail_on_change=fail_on_change, jobs=jobs
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
        dependencies = ", ".join(component.depends_on)
        suffix = f" (needs {dependencies})" if dependencies else ""
        click.echo(f"{component.name}{suffix}")
