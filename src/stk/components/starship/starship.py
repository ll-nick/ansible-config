from pathlib import Path

from stk.generated_file import write_generated_file
from stk.github import clone_github_repository
from stk.mise import install_mise_tools, mise_exec
from stk.pyinfra_adapters import component_deploy
from stk.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("starship")
def apply_starship() -> None:
    install_mise_tools("starship", FILES / "mise.toml")
    clone_github_repository("ll-nick/starship-config", Path.home() / ".config/starship")
    add_bash_snippet(FILES / "prompt.bash")
    add_nushell_snippet(FILES / "starship.nu")
    write_generated_file(
        Path.home() / ".local/share/nushell/vendor/autoload/starship.nu",
        mise_exec("starship", "init", "nu"),
    )
