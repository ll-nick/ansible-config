from pathlib import Path

from stk.engine.component import Component
from stk.helpers.generated_file import write_generated_file
from stk.helpers.mise import install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet
from stk_config.components.bash.bash import BASH
from stk_config.components.mise.mise import MISE
from stk_config.components.nushell.nushell import NUSHELL

FILES = Path(__file__).resolve().parent / "files"


def apply_zoxide() -> None:
    install_mise_tools("zoxide", FILES / "mise.toml")
    add_bash_snippet(FILES / "zoxide.bash")
    write_generated_file(
        Path.home() / ".local/share/nushell/vendor/autoload/zoxide.nu",
        mise_exec("zoxide", "init", "--cmd", "cd", "nushell"),
    )


ZOXIDE = Component("zoxide", apply_zoxide, depends_on=(MISE, BASH, NUSHELL))
