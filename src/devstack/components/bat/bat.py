import shlex
from pathlib import Path

from devstack.commands import run_command
from devstack.links import link_repository_file
from devstack.mise import install_mise_tools, mise_exec
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("bat")
def apply_bat() -> None:
    config_directory = Path.home() / ".config" / "bat"

    install_mise_tools("bat", FILES / "mise.toml")

    dark_theme = link_repository_file(
        FILES / "Catppuccin Mocha.tmTheme",
        config_directory / "themes" / "Catppuccin Mocha.tmTheme",
    )
    light_theme = link_repository_file(
        FILES / "Catppuccin Latte.tmTheme",
        config_directory / "themes" / "Catppuccin Latte.tmTheme",
    )
    config = link_repository_file(FILES / "config", config_directory / "config")

    run_command(
        "Rebuild bat cache",
        shlex.join(mise_exec("bat", "cache", "--build")),
        when_any_changed=[dark_theme, light_theme, config],
    )

    add_bash_snippet(FILES / "bat.bash")
    add_nushell_snippet(FILES / "bat.nu")
