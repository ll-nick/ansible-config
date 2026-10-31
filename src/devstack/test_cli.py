from collections.abc import Sequence

import pytest
from click.testing import CliRunner

from devstack import cli as cli_module
from devstack.cli import cli
from devstack.component import Component
from devstack.run_settings import PRIVILEGED


def test_list_shows_components_with_their_dependencies() -> None:
    result = CliRunner().invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "mise" in result.output
    assert "bat (needs mise, bash, nushell)" in result.output


def test_unknown_component_is_a_usage_error() -> None:
    result = CliRunner().invoke(cli, ["apply", "nope"])

    assert result.exit_code == 2
    assert "Unknown components: nope" in result.output


def test_privileged_components_can_be_selected_by_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gated = Component("gated", lambda: None, requires=(PRIVILEGED,))

    def select_gated(_names: Sequence[str]) -> tuple[Component, ...]:
        return (gated,)

    def run_successfully(*_arguments: object) -> int:
        return 0

    monkeypatch.setattr(cli_module, "select_components", select_gated)
    monkeypatch.setattr(cli_module, "obtain_sudo_password", lambda: None)
    monkeypatch.setattr(cli_module, "run_components", run_successfully)

    result = CliRunner().invoke(cli, ["apply", "gated", "--privileged"])

    assert result.exit_code == 0


def test_zero_jobs_are_rejected() -> None:
    result = CliRunner().invoke(cli, ["apply", "--jobs", "0"])

    assert result.exit_code == 2
