import os
from pathlib import Path

# Where bootstrapping clones the repository; `stk` always runs from here
PERMANENT_CHECKOUT = Path.home() / ".config" / "stk"


def state_directory() -> Path:
    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home) if state_home else Path.home() / ".local" / "state"
    return base / "stk"
