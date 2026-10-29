from devstack.component import Component
from devstack.components.bash.bash import apply_bash
from devstack.components.bat.bat import apply_bat
from devstack.components.fd.fd import apply_fd
from devstack.components.mise.mise import apply_mise
from devstack.components.nushell.nushell import apply_nushell

COMPONENTS: tuple[Component, ...] = (
    Component("mise", apply_mise),
    Component("bash", apply_bash),
    Component("nushell", apply_nushell, depends_on=("mise",)),
    Component("fd", apply_fd, depends_on=("mise",)),
    Component("bat", apply_bat, depends_on=("mise", "bash", "nushell")),
)
