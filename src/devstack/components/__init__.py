from devstack.component import Component
from devstack.components.bash.bash import apply_bash
from devstack.components.bat.bat import apply_bat
from devstack.components.fd.fd import apply_fd
from devstack.components.git.git import apply_git
from devstack.components.locale.locale import apply_locale
from devstack.components.mise.mise import apply_mise
from devstack.components.nushell.nushell import apply_nushell
from devstack.machine import runs_distribution
from devstack.run_settings import PRIVILEGED

COMPONENTS: tuple[Component, ...] = (
    Component("mise", apply_mise),
    Component("bash", apply_bash),
    Component(
        "git",
        apply_git,
        depends_on=("mise",),
        system_packages=("git",),
    ),
    Component("nushell", apply_nushell, depends_on=("mise",)),
    Component("fd", apply_fd, depends_on=("mise",)),
    Component("bat", apply_bat, depends_on=("mise", "bash", "nushell")),
    Component(
        "locale",
        apply_locale,
        requires=(PRIVILEGED, runs_distribution("debian")),
        system_packages=("locales",),
    ),
)
