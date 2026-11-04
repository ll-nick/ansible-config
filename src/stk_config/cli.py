from stk.cli import cli
from stk.engine.registry import discover_components
from stk.setup import Setup
from stk_config.paths import PERMANENT_CHECKOUT

SETUP = Setup(
    components=discover_components("stk_config.components"),
    checkout=PERMANENT_CHECKOUT,
)


def main() -> None:
    cli(obj=SETUP)
