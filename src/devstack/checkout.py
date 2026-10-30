from pathlib import Path

# Where bootstrapping clones the repository; `stk` always runs from here
PERMANENT_CHECKOUT = Path.home() / ".config" / "devstack"
