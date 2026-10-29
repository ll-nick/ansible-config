from pathlib import Path

from pyinfra.operations import server
from pyinfra.operations.util import any_changed

from devstack.file_copy import copy_file
from devstack.mise import install_mise_tools, mise_executable
from devstack.shells import add_bash_snippet, add_nushell_snippet

BAT_FILES = Path(__file__).resolve().parent / "files"
BAT_CONFIG_DIRECTORY = Path.home() / ".config" / "bat"

install_mise_tools("bat", BAT_FILES / "mise.toml")

dark_theme = copy_file(
    BAT_FILES / "Catppuccin Mocha.tmTheme",
    BAT_CONFIG_DIRECTORY / "themes" / "Catppuccin Mocha.tmTheme",
)
light_theme = copy_file(
    BAT_FILES / "Catppuccin Latte.tmTheme",
    BAT_CONFIG_DIRECTORY / "themes" / "Catppuccin Latte.tmTheme",
)
config = copy_file(BAT_FILES / "config", BAT_CONFIG_DIRECTORY / "config")

server.shell(
    name="Rebuild bat cache",
    commands=[f"{mise_executable()} exec -- bat cache --build"],
    _if=any_changed(dark_theme, light_theme, config),
)

add_bash_snippet(BAT_FILES / "bat.bash")
add_nushell_snippet(BAT_FILES / "bat.nu")
