from pyinfra.operations import server

from devstack.mise import MISE_INSTALL_SCRIPT_URL, mise_executable
from devstack.pyinfra_adapters import component_deploy


@component_deploy("mise")
def apply_mise() -> None:
    if not mise_executable().exists():
        server.shell(
            name="Install mise",
            commands=[f"curl -fsSL {MISE_INSTALL_SCRIPT_URL} | sh"],
        )
