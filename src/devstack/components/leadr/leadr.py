from pathlib import Path

from devstack.file_copy import copy_file
from devstack.generated_file import write_generated_file
from devstack.github import clone_github_repository
from devstack.mise import install_mise_tools, mise_exec
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("leadr")
def apply_leadr() -> None:
    autoload_directory = Path.home() / ".local/share/nushell/vendor/autoload"

    install_mise_tools("leadr", FILES / "mise.toml")
    clone_github_repository("ll-nick/leadr-config", Path.home() / ".config/leadr")

    add_bash_snippet(FILES / "leadr.bash")
    write_generated_file(
        autoload_directory / "leadr.nu",
        mise_exec("leadr", "--nu"),
    )
    copy_file(FILES / "leadr_env.nu", autoload_directory / "leadr_env.nu")
