import shlex
from pathlib import Path

from devstack.commands import run_command
from devstack.file_edit import replace_line
from devstack.github import clone_github_repository
from devstack.machine import distribution_ids
from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"
KITTY_INSTALLATION = (
    Path.home() / ".local/share/mise/installs/github-kovidgoyal-kitty/latest"
)
DESKTOP_FILE_NAMES = ("kitty.desktop", "kitty-open.desktop")


@component_deploy("kitty")
def apply_kitty() -> None:
    applications_directory = Path.home() / ".local/share/applications"

    # kitty is best installed via nixpkgs on NixOS
    if "nixos" not in distribution_ids():
        install_mise_tools("kitty", FILES / "mise.toml")

        if not (applications_directory / "kitty.desktop").exists():
            run_command(
                "Install kitty desktop files",
                _desktop_file_installation_script(applications_directory),
            )
            replace_line(
                Path.home() / ".config/xdg-terminals.list",
                r"^kitty\.desktop$",
                "kitty.desktop",
            )

    clone_github_repository("ll-nick/kitty-config", Path.home() / ".config/kitty")


def _desktop_file_installation_script(applications_directory: Path) -> str:
    icon = KITTY_INSTALLATION / "share/icons/hicolor/256x256/apps/kitty.png"
    executable = KITTY_INSTALLATION / "bin/kitty"
    commands = [f"mkdir -p {shlex.quote(str(applications_directory))}"]
    for name in DESKTOP_FILE_NAMES:
        installed = shlex.quote(str(applications_directory / name))
        source = shlex.quote(str(KITTY_INSTALLATION / "share/applications" / name))
        commands.append(f"cp {source} {installed}")
        commands.append(
            f"sed -i {shlex.quote(f's|Icon=kitty|Icon={icon}|g')} {installed}"
        )
        commands.append(
            f"sed -i {shlex.quote(f's|Exec=kitty|Exec={executable}|g')} {installed}"
        )
    return " && ".join(commands)
