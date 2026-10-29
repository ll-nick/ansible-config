from click.testing import CliRunner

from devstack.cli import cli


def test_list_shows_components_with_their_dependencies() -> None:
    result = CliRunner().invoke(cli, ["list"])

    assert result.exit_code == 0
    assert "mise" in result.output
    assert "bat (needs mise, bash, nushell)" in result.output


def test_unknown_component_is_a_usage_error() -> None:
    result = CliRunner().invoke(cli, ["apply", "nope"])

    assert result.exit_code == 2
    assert "Unknown components: nope" in result.output
