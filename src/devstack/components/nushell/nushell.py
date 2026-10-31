from pathlib import Path

from devstack.generated_file import write_generated_file
from devstack.github import clone_github_repository
from devstack.mise import install_mise_tools, mise_exec, mise_executable
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("nushell")
def apply_nushell() -> None:
    autoload_directory = Path.home() / ".local/share/nushell/vendor/autoload"

    install_mise_tools("nushell", FILES / "mise.toml")
    clone_github_repository("ll-nick/nushell-config", Path.home() / ".config/nushell")

    mise = str(mise_executable())
    write_generated_file(
        autoload_directory / "carapace.nu",
        mise_exec("carapace", "_carapace", "nushell"),
    )
    write_generated_file(autoload_directory / "00_mise.nu", [mise, "activate", "nu"])
