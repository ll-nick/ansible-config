import dataclasses
from collections.abc import Sequence

from pyinfra.operations import apt

from devstack.component import Component
from devstack.machine import distribution_ids
from devstack.pyinfra_adapters import component_deploy

SYSTEM_PACKAGES_COMPONENT_NAME = "system-packages"
APT_CACHE_SECONDS = 3600


class UnsupportedDistributionError(RuntimeError):
    def __init__(self, identifiers: frozenset[str]) -> None:
        super().__init__(
            "System packages are only supported on Debian-based distributions"
            + f" (found: {', '.join(sorted(identifiers)) or 'unknown'})"
        )


def ensure_supported_distribution() -> None:
    identifiers = distribution_ids()
    if "debian" not in identifiers:
        raise UnsupportedDistributionError(identifiers)


def packages_for_this_machine(all_packages: Sequence[tuple[str, ...]]) -> list[str]:
    ensure_supported_distribution()

    names: list[str] = []
    for packages in all_packages:
        for name in packages:
            if name not in names:
                names.append(name)
    return names


def system_packages_component(components: Sequence[Component]) -> Component | None:
    wanted = [
        component.system_packages
        for component in components
        if component.unmet_requirement() is None
    ]
    if not any(wanted):
        return None

    @component_deploy(SYSTEM_PACKAGES_COMPONENT_NAME)
    def apply_system_packages() -> None:
        names = packages_for_this_machine(wanted)
        if not names:
            return
        apt.packages(
            name="Install apt packages",
            packages=names,
            update=True,
            cache_time=APT_CACHE_SECONDS,
            _sudo=True,
        )

    return Component(SYSTEM_PACKAGES_COMPONENT_NAME, apply_system_packages)


def with_system_packages(components: Sequence[Component]) -> list[Component]:
    installer = system_packages_component(components)
    if installer is None:
        return list(components)

    # Everyone waits, not just those declaring packages: mise installs the tools of
    # all components together, and any of them may need a package to run
    return [
        installer,
        *(
            dataclasses.replace(
                component, depends_on=(*component.depends_on, installer.name)
            )
            if component.unmet_requirement() is None
            else component
            for component in components
        ),
    ]
