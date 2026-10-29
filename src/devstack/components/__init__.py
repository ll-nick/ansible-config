from devstack.component import Component
from devstack.components.bat.bat import apply_bat
from devstack.components.fd.fd import apply_fd
from devstack.components.mise.mise import apply_mise

COMPONENTS: tuple[Component, ...] = (
    Component("mise", apply_mise),
    Component("fd", apply_fd, depends_on=("mise",)),
    Component("bat", apply_bat, depends_on=("mise",)),
)
