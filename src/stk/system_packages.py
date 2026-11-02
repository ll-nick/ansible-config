import dataclasses
import subprocess
from collections.abc import Sequence

from pyinfra.operations import apt

from stk.component import Component
from stk.machine import distribution_ids
from stk.pyinfra_adapters import component_deploy
from stk.run_settings import PRIVILEGED

SYSTEM_PACKAGES_COMPONENT_NAME = "system-packages"
APT_CACHE_SECONDS = 3600


def merged_packages(all_packages: Sequence[tuple[str, ...]]) -> list[str]:
    names: list[str] = []
    for packages in all_packages:
        for name in packages:
            if name not in names:
                names.append(name)
    return names


def _is_applicable_once_privileged(component: Component) -> bool:
    return component.unmet_requirement() in (None, PRIVILEGED)


def installed_packages(names: Sequence[str]) -> frozenset[str]:
    try:
        completed = subprocess.run(
            ["dpkg-query", "--show", "--showformat=${Package} ${Status}\\n", *names],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return frozenset()
    return frozenset(
        line.split()[0]
        for line in completed.stdout.splitlines()
        if line.endswith("install ok installed")
    )


def missing_system_packages(components: Sequence[Component]) -> list[str]:
    if "debian" not in distribution_ids():
        return []
    names = merged_packages(
        [
            component.system_packages
            for component in components
            if _is_applicable_once_privileged(component)
        ]
    )
    if not names:
        return []
    installed = installed_packages(names)
    return [name for name in names if name not in installed]


def pending_sudo_work(components: Sequence[Component]) -> list[str]:
    work: list[str] = []
    missing_packages = missing_system_packages(components)
    if missing_packages:
        work.append(
            f"{SYSTEM_PACKAGES_COMPONENT_NAME}: install {', '.join(missing_packages)}"
        )
    for component in components:
        if component.pending_sudo_work is None:
            continue
        if not _is_applicable_once_privileged(component):
            continue
        description = component.pending_sudo_work()
        if description is not None:
            work.append(f"{component.name}: {description}")
    return work


def system_packages_component(components: Sequence[Component]) -> Component | None:
    wanted = [
        component.system_packages
        for component in components
        if component.unmet_requirement() is None
    ]
    if not any(wanted) or "debian" not in distribution_ids():
        return None

    @component_deploy(SYSTEM_PACKAGES_COMPONENT_NAME)
    def apply_system_packages() -> None:
        apt.packages(
            name="Install apt packages",
            packages=merged_packages(wanted),
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
