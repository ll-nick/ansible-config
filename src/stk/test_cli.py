from collections.abc import Sequence
from pathlib import Path

import pytest
from click.testing import CliRunner

from stk import cli as cli_module
from stk.cli import cli, enabled_components
from stk.component import Component
from stk.enablement import enabled_file
from stk.runner import RunOptions


def test_list_shows_components_with_their_dependencies() -> None:
    result = CliRunner().invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "mise" in result.output
    assert "bat (needs mise, bash, nushell)" in result.output


def test_unknown_component_is_a_usage_error() -> None:
    result = CliRunner().invoke(cli, ["apply", "nope"])

    assert result.exit_code == 2
    assert "Unknown components: nope" in result.output


@pytest.fixture
def machine_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))


@pytest.fixture
def recorded_runs(monkeypatch: pytest.MonkeyPatch) -> list[RunOptions]:
    runs: list[RunOptions] = []

    def record_run(
        _components: Sequence[Component], options: RunOptions, _reporter: object
    ) -> int:
        runs.append(options)
        return 0

    monkeypatch.setattr(cli_module, "isolate_mise_from_the_caller", lambda: None)
    monkeypatch.setattr(cli_module, "run_components", record_run)
    return runs


def use_sudo_work(monkeypatch: pytest.MonkeyPatch, work: list[str]) -> None:
    def pending_work(_components: Sequence[Component]) -> list[str]:
        return work

    monkeypatch.setattr(cli_module, "pending_sudo_work", pending_work)


def forbid_asking_for_the_password(monkeypatch: pytest.MonkeyPatch) -> None:
    def obtain_password_unexpectedly() -> None:
        pytest.fail("must not ask for the password")

    monkeypatch.setattr(
        cli_module, "obtain_sudo_password", obtain_password_unexpectedly
    )


@pytest.mark.usefixtures("machine_state")
def test_apply_fails_when_nothing_is_enabled(recorded_runs: list[RunOptions]) -> None:
    result = CliRunner().invoke(cli, ["apply"])

    assert result.exit_code == 2
    assert "stk enable" in result.output
    assert not recorded_runs


@pytest.mark.usefixtures("machine_state")
def test_update_and_check_fail_when_nothing_is_enabled() -> None:
    assert CliRunner().invoke(cli, ["update", "-n"]).exit_code == 2
    assert CliRunner().invoke(cli, ["check"]).exit_code == 2


@pytest.mark.usefixtures("machine_state")
def test_enable_rejects_unknown_names() -> None:
    result = CliRunner().invoke(cli, ["enable", "nope"])

    assert result.exit_code == 2
    assert "Unknown names: nope" in result.output


@pytest.mark.usefixtures("machine_state")
def test_a_component_that_is_not_enabled_is_rejected(
    recorded_runs: list[RunOptions],
) -> None:
    CliRunner().invoke(cli, ["enable"])
    CliRunner().invoke(cli, ["disable", "default"])

    result = CliRunner().invoke(cli, ["apply", "fd"])

    assert result.exit_code == 2
    assert "stk enable fd" in result.output
    assert not recorded_runs


@pytest.mark.usefixtures("machine_state")
def test_disable_rejects_unknown_names_but_cleans_up_stale_entries() -> None:
    CliRunner().invoke(cli, ["enable"])

    result = CliRunner().invoke(cli, ["disable", "nope"])

    assert result.exit_code == 2
    assert "Unknown names: nope" in result.output

    enabled_file().write_text("default\nremoved\n")

    assert CliRunner().invoke(cli, ["disable", "removed"]).exit_code == 0
    assert enabled_file().read_text() == "default\n"


@pytest.mark.usefixtures("machine_state")
def test_a_disabled_component_of_the_default_group_is_not_applied(
    recorded_runs: list[RunOptions],
) -> None:
    CliRunner().invoke(cli, ["enable"])

    result = CliRunner().invoke(cli, ["disable", "fd"])

    assert result.exit_code == 0
    assert "-fd" in result.output
    assert "fd" not in [component.name for component in enabled_components()]
    assert "stk enable fd" in CliRunner().invoke(cli, ["apply", "fd"]).output
    assert not recorded_runs


@pytest.mark.usefixtures("machine_state")
def test_disabling_a_dependency_also_leaves_out_its_dependents() -> None:
    CliRunner().invoke(cli, ["enable"])

    result = CliRunner().invoke(cli, ["disable", "ripgrep"])

    enabled_names = [component.name for component in enabled_components()]
    assert "ripgrep" not in enabled_names
    assert "neovim" not in enabled_names
    assert "git" in enabled_names
    assert "Left out for needing a disabled component" in result.output
    assert "neovim" in result.output


@pytest.mark.usefixtures("machine_state")
def test_sudo_is_requested_when_there_is_work_for_it(
    monkeypatch: pytest.MonkeyPatch, recorded_runs: list[RunOptions]
) -> None:
    CliRunner().invoke(cli, ["enable", "sudo"])
    use_sudo_work(monkeypatch, ["locale: generate"])
    monkeypatch.setattr(cli_module, "obtain_sudo_password", lambda: "secret")

    result = CliRunner().invoke(cli, ["apply"])

    assert result.exit_code == 0
    assert "locale: generate" in result.output
    assert recorded_runs[0].sudo_password == "secret"


@pytest.mark.usefixtures("machine_state")
@pytest.mark.parametrize(
    ("enabled", "arguments", "work"),
    [
        (("sudo",), ["apply"], []),
        (("sudo",), ["apply", "--skip", "sudo"], ["locale: generate"]),
        (("sudo",), ["apply", "--dry-run"], ["locale: generate"]),
        ((), ["apply"], ["locale: generate"]),
    ],
)
def test_sudo_is_not_requested_otherwise(
    monkeypatch: pytest.MonkeyPatch,
    recorded_runs: list[RunOptions],
    enabled: tuple[str, ...],
    arguments: list[str],
    work: list[str],
) -> None:
    CliRunner().invoke(cli, ["enable", *enabled])
    use_sudo_work(monkeypatch, work)
    forbid_asking_for_the_password(monkeypatch)

    result = CliRunner().invoke(cli, arguments)

    assert result.exit_code == 0
    assert recorded_runs[0].sudo_password is None


@pytest.mark.usefixtures("machine_state")
def test_skipping_a_component_also_skips_its_dependents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    applied: list[str] = []

    def record_components(
        components: Sequence[Component], _options: RunOptions, _reporter: object
    ) -> int:
        applied.extend(component.name for component in components)
        return 0

    monkeypatch.setattr(cli_module, "isolate_mise_from_the_caller", lambda: None)
    monkeypatch.setattr(cli_module, "run_components", record_components)
    forbid_asking_for_the_password(monkeypatch)
    CliRunner().invoke(cli, ["enable"])

    result = CliRunner().invoke(cli, ["apply", "--skip", "mise"])

    assert result.exit_code == 0
    assert "Also skipping dependents" in result.output
    assert "mise" not in applied
    assert "git" not in applied
    assert "bash" in applied
