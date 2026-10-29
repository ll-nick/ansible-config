from devstack.testing import run_with_mise


def test_catppuccin_themes_are_available() -> None:
    themes = run_with_mise("bat", "--list-themes")

    assert "Catppuccin Mocha" in themes
    assert "Catppuccin Latte" in themes
