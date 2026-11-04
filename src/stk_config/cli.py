from stk.cli import cli
from stk.engine.registry import discover_components
from stk.setup import Setup
from stk_config.paths import PERMANENT_CHECKOUT, STK_SHIM

SETUP = Setup(
    components=discover_components("stk_config.components"),
    checkout=PERMANENT_CHECKOUT,
    command=STK_SHIM,
)


def main() -> None:
    cli(obj=SETUP)
