from pathlib import Path

from stk.commands import run_command
from stk.component import Component
from stk.plain_reporter import PlainReporter
from stk.pyinfra_adapters import component_deploy
from stk.runner import RunOptions, run_components


def test_a_command_is_retried_until_it_succeeds(tmp_path: Path) -> None:
    attempts = tmp_path / "attempts"

    @component_deploy("flaky")
    def apply() -> None:
        run_command(
            "Fail on the first attempt",
            f"echo attempt >> {attempts} && [ $(wc -l < {attempts}) -ge 2 ]",
            retries=1,
        )

    exit_code = run_components(
        [Component("flaky", apply)],
        RunOptions(dry_run=False, assume_yes=True, fail_on_change=False, jobs=1),
        PlainReporter(verbosity=0),
    )

    assert exit_code == 0
    assert len(attempts.read_text().splitlines()) == 2
