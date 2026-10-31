from pathlib import Path

from devstack.generated_file import write_generated_file
from devstack.mise import install_mise_tools, mise_exec
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("zoxide")
def apply_zoxide() -> None:
    install_mise_tools("zoxide", FILES / "mise.toml")
    add_bash_snippet(FILES / "zoxide.bash")
    write_generated_file(
        Path.home() / ".local/share/nushell/vendor/autoload/zoxide.nu",
        mise_exec("zoxide", "init", "--cmd", "cd", "nushell"),
    )
