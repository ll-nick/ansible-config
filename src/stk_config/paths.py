from pathlib import Path

# Where bootstrapping clones the repository; `stk` always runs from here
PERMANENT_CHECKOUT = Path.home() / ".config" / "stk"
# The shim the stk component installs, which runs stk from the permanent checkout
STK_SHIM = Path.home() / ".local/bin/stk"
