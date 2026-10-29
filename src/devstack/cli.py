import argparse
import sys
from collections.abc import Sequence

from devstack.components import COMPONENTS
from devstack.plain_reporter import PlainReporter
from devstack.registry import UnknownComponentError, select_components
from devstack.runner import RunOptions, run_components

EXIT_USAGE_ERROR = 2


class ParsedArguments(argparse.Namespace):
    command: str = ""
    components: Sequence[str] = ()
    dry_run: bool = False
    yes: bool = False
    fail_on_change: bool = False
    verbose: int = 0


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devstack")
    subcommands = parser.add_subparsers(dest="command", required=True)

    apply_parser = subcommands.add_parser("apply", help="Apply components")
    apply_parser.add_argument(
        "components", nargs="*", help="Components to apply (default: all)"
    )
    apply_parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Show the plan and stop"
    )
    apply_parser.add_argument(
        "-y", "--yes", action="store_true", help="Skip the confirmation prompt"
    )
    apply_parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit with status 3 if any operation changed something",
    )
    apply_parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Show unchanged operations"
    )

    subcommands.add_parser("list", help="List available components")
    return parser


def apply_components(arguments: ParsedArguments) -> int:
    try:
        components = select_components(arguments.components)
    except UnknownComponentError as error:
        print(error, file=sys.stderr)
        return EXIT_USAGE_ERROR

    options = RunOptions(
        dry_run=arguments.dry_run,
        assume_yes=arguments.yes,
        fail_on_change=arguments.fail_on_change,
    )
    return run_components(components, options, PlainReporter(arguments.verbose))


def main() -> None:
    arguments = build_argument_parser().parse_args(namespace=ParsedArguments())
    if arguments.command == "list":
        for component in COMPONENTS:
            print(component.name)
        raise SystemExit(0)
    raise SystemExit(apply_components(arguments))
