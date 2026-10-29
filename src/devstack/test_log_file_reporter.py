from pathlib import Path

from devstack.log_file_reporter import LAST_RUN_LINK_NAME, LogFileReporter
from devstack.reporting import (
    ComponentOutcome,
    ComponentResult,
    OperationDescription,
    OperationResult,
)


def test_log_contains_operations_with_their_output(tmp_path: Path) -> None:
    reporter = LogFileReporter(tmp_path)
    description = OperationDescription("bat", "Rebuild bat cache")

    reporter.run_started(["bat"])
    reporter.operation_finished(
        OperationResult(description, True, 0.4, stdout="cache built", stderr="warn")
    )
    reporter.component_finished(
        ComponentResult("bat", ComponentOutcome.SUCCEEDED, [], 0.5)
    )
    reporter.run_finished([], 0.5)
    reporter.close()

    log = reporter.log_path.read_text()
    assert "bat | Rebuild bat cache: changed" in log
    assert "stdout: cache built" in log
    assert "stderr: warn" in log
    assert (tmp_path / LAST_RUN_LINK_NAME).resolve() == reporter.log_path.resolve()


def test_old_logs_are_pruned(tmp_path: Path) -> None:
    runs_directory = tmp_path / "runs"
    runs_directory.mkdir()
    for index in range(30):
        (runs_directory / f"20200101-0000{index:02d}.log").write_text("old")

    reporter = LogFileReporter(tmp_path)
    reporter.run_started([])
    reporter.close()

    assert len(list(runs_directory.glob("*.log"))) == 20
