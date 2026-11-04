from dataclasses import dataclass
from pathlib import Path

from stk.engine.component import Component


@dataclass(frozen=True)
class Setup:
    """What a configuration hands stk."""

    components: tuple[Component, ...]
    # The git checkout of the configuration, which `stk update` pulls
    checkout: Path
