from pathlib import Path

from stk.cli import cli
from stk.engine.registry import discover_components
from stk.setup import Setup


def main() -> None:
    cli(
        obj=Setup(
            components=discover_components("stk_config.components"),
            checkout=Path.home() / ".config" / "stk",
        )
    )
