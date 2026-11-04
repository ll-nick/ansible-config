from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.generated_file import write_generated_file
from stk.helpers.github import clone_github_repository
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet

FILES = Path(__file__).resolve().parent / "files"


def apply_leadr() -> None:
    autoload_directory = Path.home() / ".local/share/nushell/vendor/autoload"

    install_mise_tools("leadr", FILES / "mise.toml")
    clone_github_repository("ll-nick/leadr-config", Path.home() / ".config/leadr")

    add_bash_snippet(FILES / "leadr.bash")
    write_generated_file(
        autoload_directory / "leadr.nu",
        mise_exec("leadr", "--nu"),
    )
    symlink_file(FILES / "leadr_env.nu", autoload_directory / "leadr_env.nu")


LEADR = Component("leadr", apply_leadr, depends_on=(MISE, BASH, NUSHELL))
