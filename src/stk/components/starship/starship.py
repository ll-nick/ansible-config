from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.generated_file import write_generated_file
from stk.helpers.github import clone_github_repository
from stk.helpers.mise import install_mise_tools, mise_exec
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


def apply_starship() -> None:
    install_mise_tools("starship", FILES / "mise.toml")
    clone_github_repository("ll-nick/starship-config", Path.home() / ".config/starship")
    add_bash_snippet(FILES / "prompt.bash")
    add_nushell_snippet(FILES / "starship.nu")
    write_generated_file(
        Path.home() / ".local/share/nushell/vendor/autoload/starship.nu",
        mise_exec("starship", "init", "nu"),
    )


STARSHIP = Component("starship", apply_starship, depends_on=(MISE, BASH, NUSHELL))
