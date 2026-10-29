from devstack.mise import install_mise_tools
from devstack.paths import FILES_DIRECTORY

install_mise_tools("fd", FILES_DIRECTORY / "fd" / "mise.toml")
