from pathlib import Path

from stk.engine.component import Component
from stk.helpers.mise import install_mise_tools
from stk_config.components.mise.mise import MISE

FILES = Path(__file__).resolve().parent / "files"


def apply_nodejs() -> None:
    install_mise_tools("nodejs", FILES / "mise.toml")


NODEJS = Component(
    "nodejs",
    apply_nodejs,
    depends_on=(MISE,),
    system_packages=("libatomic1",),
)
