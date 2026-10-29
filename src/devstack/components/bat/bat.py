from pathlib import Path

from pyinfra.operations import server
from pyinfra.operations.util import any_changed

from devstack.file_copy import copy_file
from devstack.mise import install_mise_tools, mise_executable
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("bat")
def apply_bat() -> None:
    config_directory = Path.home() / ".config" / "bat"

    install_mise_tools("bat", FILES / "mise.toml")

    dark_theme = copy_file(
        FILES / "Catppuccin Mocha.tmTheme",
        config_directory / "themes" / "Catppuccin Mocha.tmTheme",
    )
    light_theme = copy_file(
        FILES / "Catppuccin Latte.tmTheme",
        config_directory / "themes" / "Catppuccin Latte.tmTheme",
    )
    config = copy_file(FILES / "config", config_directory / "config")

    server.shell(
        name="Rebuild bat cache",
        commands=[f"{mise_executable()} exec -- bat cache --build"],
        _if=any_changed(dark_theme, light_theme, config),
    )

    add_bash_snippet(FILES / "bat.bash")
    add_nushell_snippet(FILES / "bat.nu")
