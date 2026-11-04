import shlex
from pathlib import Path

from stk.engine.component import Component
from stk.helpers.commands import run_command
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet
from stk_config.components.bash.bash import BASH
from stk_config.components.mise.mise import MISE
from stk_config.components.nushell.nushell import NUSHELL

FILES = Path(__file__).resolve().parent / "files"


def apply_bat() -> None:
    config_directory = Path.home() / ".config" / "bat"

    install_mise_tools("bat", FILES / "mise.toml")

    dark_theme = symlink_file(
        FILES / "Catppuccin Mocha.tmTheme",
        config_directory / "themes" / "Catppuccin Mocha.tmTheme",
    )
    light_theme = symlink_file(
        FILES / "Catppuccin Latte.tmTheme",
        config_directory / "themes" / "Catppuccin Latte.tmTheme",
    )
    config = symlink_file(FILES / "config", config_directory / "config")

    run_command(
        "Rebuild bat cache",
        shlex.join(mise_exec("bat", "cache", "--build")),
        when_any_changed=[dark_theme, light_theme, config],
    )

    add_bash_snippet(FILES / "bat.bash")
    add_nushell_snippet(FILES / "bat.nu")


BAT = Component("bat", apply_bat, depends_on=(MISE, BASH, NUSHELL))
