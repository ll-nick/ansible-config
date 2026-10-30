from pathlib import Path

from devstack.json_settings import parse_json_object
from devstack.testing import run_with_mise


def test_claude_runs() -> None:
    assert run_with_mise("claude", "--version").strip()


def test_managed_settings_are_present() -> None:
    settings = parse_json_object((Path.home() / ".claude/settings.json").read_text())

    assert settings["editorMode"] == "vim"
