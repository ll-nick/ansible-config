from devstack.component import Component
from devstack.components.bat.bat import apply_bat
from devstack.components.fd.fd import apply_fd

COMPONENTS: tuple[Component, ...] = (
    Component("fd", apply_fd),
    Component("bat", apply_bat),
)
