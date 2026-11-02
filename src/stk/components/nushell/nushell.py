from pathlib import Path

from stk.engine.pyinfra_adapters import component_deploy
from stk.helpers.generated_file import write_generated_file
from stk.helpers.github import clone_github_repository
from stk.helpers.mise import install_mise_tools, mise_exec

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("nushell")
def apply_nushell() -> None:
    autoload_directory = Path.home() / ".local/share/nushell/vendor/autoload"

    install_mise_tools("nushell", FILES / "mise.toml")
    clone_github_repository("ll-nick/nushell-config", Path.home() / ".config/nushell")

    write_generated_file(
        autoload_directory / "carapace.nu",
        mise_exec("carapace", "_carapace", "nushell"),
    )
