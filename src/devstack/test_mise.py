from pathlib import Path

from devstack.mise import declared_mise_tools


def test_tools_are_read_from_a_mise_config(tmp_path: Path) -> None:
    config = tmp_path / "mise.toml"
    config.write_text(
        '[tools]\nripgrep = "latest"\n"pipx:inkflow" = { version = "latest" }\n'
        + '[env]\nFOO = "bar"\n'
    )

    assert declared_mise_tools(config) == {"ripgrep", "pipx:inkflow"}
