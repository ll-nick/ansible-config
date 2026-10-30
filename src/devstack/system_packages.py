import dataclasses
from collections.abc import Sequence

from pyinfra.operations import apt, pacman

from devstack.component import Component, SystemPackages
from devstack.machine import distribution_ids
from devstack.pyinfra_adapters import component_deploy

SYSTEM_PACKAGES_COMPONENT_NAME = "system-packages"
APT_CACHE_SECONDS = 3600


class UnsupportedDistributionError(RuntimeError):
    def __init__(self, identifiers: frozenset[str]) -> None:
        super().__init__(
            "System packages are only supported on Debian-based and Arch-based"
            + f" distributions (found: {', '.join(sorted(identifiers)) or 'unknown'})"
        )


def packages_for_this_machine(
    all_packages: Sequence[SystemPackages],
) -> tuple[str, list[str]]:
    identifiers = distribution_ids()
    manager = "apt" if "debian" in identifiers else "pacman"
    if "debian" not in identifiers and "arch" not in identifiers:
        raise UnsupportedDistributionError(identifiers)

    names: list[str] = []
    for packages in all_packages:
        distribution_specific = packages.debian if manager == "apt" else packages.arch
        for name in (*packages.common, *distribution_specific):
            if name not in names:
                names.append(name)
    return manager, names


def system_packages_component(components: Sequence[Component]) -> Component | None:
    wanted = [
        component.system_packages
        for component in components
        if component.unmet_requirement() is None
    ]
    if not any(packages != SystemPackages() for packages in wanted):
        return None

    @component_deploy(SYSTEM_PACKAGES_COMPONENT_NAME)
    def apply_system_packages() -> None:
        manager, names = packages_for_this_machine(wanted)
        if not names:
            return
        if manager == "apt":
            apt.packages(
                name="Install apt packages",
                packages=names,
                update=True,
                cache_time=APT_CACHE_SECONDS,
                _sudo=True,
            )
        else:
            pacman.packages(
                name="Install pacman packages",
                packages=names,
                update=True,
                _sudo=True,
            )

    return Component(SYSTEM_PACKAGES_COMPONENT_NAME, apply_system_packages)


def with_system_packages(components: Sequence[Component]) -> list[Component]:
    installer = system_packages_component(components)
    if installer is None:
        return list(components)

    needing_packages = {
        component.name
        for component in components
        if component.system_packages != SystemPackages()
        and component.unmet_requirement() is None
    }
    return [
        installer,
        *(
            dataclasses.replace(
                component, depends_on=(*component.depends_on, installer.name)
            )
            if component.name in needing_packages
            else component
            for component in components
        ),
    ]
