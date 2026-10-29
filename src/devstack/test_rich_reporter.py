from io import StringIO

from rich.console import Console

from devstack.reporting import (
    ComponentOutcome,
    ComponentResult,
    OperationDescription,
    OperationResult,
    RunFailure,
)
from devstack.rich_reporter import RichReporter


def make_console() -> tuple[Console, StringIO]:
    output = StringIO()
    console = Console(file=output, force_terminal=False, width=100, color_system=None)
    return console, output


def operation(
    component: str,
    name: str,
    changed: bool,
    ignored_error_output: str | None = None,
) -> OperationResult:
    return OperationResult(
        OperationDescription(component, name),
        changed=changed,
        duration_seconds=0.1,
        ignored_error_output=ignored_error_output,
    )


def run(
    reporter: RichReporter,
    results: list[ComponentResult],
    operations_by_component: dict[str, list[OperationResult]],
) -> None:
    reporter.run_started([result.component_name for result in results])
    for result in results:
        reporter.component_started(result.component_name)
        for operation_result in operations_by_component.get(result.component_name, []):
            reporter.operation_finished(operation_result)
        reporter.component_finished(result)
    reporter.run_finished(results, 1.5)
    reporter.close()


def succeeded(name: str, operations: list[OperationResult]) -> ComponentResult:
    return ComponentResult(name, ComponentOutcome.SUCCEEDED, operations, 0.5)


def test_a_settled_machine_prints_a_single_line() -> None:
    console, output = make_console()
    operations = {"bat": [operation("bat", "Copy config", changed=False)]}

    run(RichReporter(console, 0), [succeeded("bat", operations["bat"])], operations)

    expected = "✔ 1 components up to date · 1 operations · 1.5 s"
    assert output.getvalue().strip() == expected


def test_changes_are_listed_and_unchanged_operations_stay_hidden() -> None:
    console, output = make_console()
    operations = {
        "bat": [
            operation("bat", "Copy config", changed=True),
            operation("bat", "Copy theme", changed=False),
        ]
    }

    run(RichReporter(console, 0), [succeeded("bat", operations["bat"])], operations)

    text = output.getvalue()
    assert "✱ bat" in text
    assert "Copy config" in text
    assert "Copy theme" not in text


def test_verbose_output_includes_unchanged_operations() -> None:
    console, output = make_console()
    operations = {"bat": [operation("bat", "Copy theme", changed=False)]}

    run(RichReporter(console, 1), [succeeded("bat", operations["bat"])], operations)

    assert "Copy theme" in output.getvalue()


def test_failures_are_always_shown_with_their_output_and_in_the_summary() -> None:
    console, output = make_console()
    failure = RunFailure(
        OperationDescription("nushell", "Install tools"),
        "Operation failed",
        ["mise ERROR could not download", "Error: executed 0 commands"],
    )
    failed = ComponentResult(
        "nushell", ComponentOutcome.FAILED, [], 2.0, failure=failure
    )

    run(RichReporter(console, 0), [failed], {})

    text = output.getvalue()
    assert "✘ nushell" in text
    assert "Install tools" in text
    assert "mise ERROR could not download" in text
    assert "1 failed" in text
    assert "nushell: Install tools — mise ERROR could not download" in text


def test_skipped_components_name_the_reason() -> None:
    console, output = make_console()
    skipped = ComponentResult(
        "bat",
        ComponentOutcome.SKIPPED,
        [],
        0.0,
        skipped_because="dependency nushell did not succeed",
    )

    run(RichReporter(console, 0), [skipped], {})

    text = output.getvalue()
    assert "⤼ bat" in text
    assert "dependency nushell did not succeed" in text


def test_ignored_errors_are_shown_as_warnings() -> None:
    console, output = make_console()
    operations = {
        "bash": [
            operation(
                "bash",
                "Clone ll-nick/bash-config",
                changed=False,
                ignored_error_output="Repository not found.",
            )
        ]
    }

    run(RichReporter(console, 0), [succeeded("bash", operations["bash"])], operations)

    text = output.getvalue()
    assert "! Clone ll-nick/bash-config (error ignored)" in text
    assert "Repository not found." in text
    assert "1 warnings" in text
