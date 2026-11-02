from pathlib import Path

from stk.mise import install_mise_tools
from stk.pyinfra_adapters import component_deploy
from stk.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("fzf")
def apply_fzf() -> None:
    install_mise_tools("fzf", FILES / "mise.toml")
    add_bash_snippet(FILES / "fzf.bash")
    add_nushell_snippet(FILES / "fzf.nu")
