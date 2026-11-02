import dataclasses
import subprocess
from collections.abc import Sequence

from pyinfra.operations import apt

from stk.engine.component import Component, PrivilegedTask
from stk.engine.pyinfra_adapters import component_deploy, deploy_as_root
from stk.machine import distribution_ids

SYSTEM_PACKAGES_COMPONENT_NAME = "system-packages"
PRIVILEGED_COMPONENT_SUFFIX = "-privileged"
APT_CACHE_SECONDS = 3600


def merged_packages(all_packages: Sequence[tuple[str, ...]]) -> list[str]:
    names: list[str] = []
    for packages in all_packages:
        for name in packages:
            if name not in names:
                names.append(name)
    return names


def _applicable(components: Sequence[Component]) -> list[Component]:
    return [
        component for component in components if component.unmet_requirement() is None
    ]


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


def _missing_system_packages(components: Sequence[Component]) -> list[str]:
    if "debian" not in distribution_ids():
        return []
    names = merged_packages([component.system_packages for component in components])
    if not names:
        return []
    installed = installed_packages(names)
    return [name for name in names if name not in installed]


def _pending_tasks(component: Component) -> list[PrivilegedTask]:
    return [task for task in component.privileged_tasks if task.is_pending()]


def pending_sudo_work(components: Sequence[Component]) -> list[str]:
    applicable = _applicable(components)
    work: list[str] = []
    missing_packages = _missing_system_packages(applicable)
    if missing_packages:
        work.append(
            f"{SYSTEM_PACKAGES_COMPONENT_NAME}: install {', '.join(missing_packages)}"
        )
    for component in applicable:
        work.extend(
            f"{component.name}: {task.description}"
            for task in _pending_tasks(component)
        )
    return work


def _system_packages_component(components: Sequence[Component]) -> Component | None:
    wanted = [component.system_packages for component in components]
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


def _privileged_component(
    component: Component, depends_on: tuple[str, ...]
) -> Component | None:
    tasks = _pending_tasks(component)
    if not tasks:
        return None
    name = f"{component.name}{PRIVILEGED_COMPONENT_SUFFIX}"

    def apply_tasks() -> None:
        for task in tasks:
            task.apply()

    return Component(name, deploy_as_root(name, apply_tasks), depends_on=depends_on)


def with_privileged_work(components: Sequence[Component]) -> list[Component]:
    applicable = _applicable(components)
    installer = _system_packages_component(applicable)
    installer_names = () if installer is None else (installer.name,)

    privileged_by_owner = {
        component.name: privileged
        for component in applicable
        if (privileged := _privileged_component(component, installer_names))
    }

    def with_root_dependencies(component: Component) -> Component:
        if component.unmet_requirement() is not None:
            return component
        privileged = privileged_by_owner.get(component.name)
        privileged_names = () if privileged is None else (privileged.name,)
        # Everyone waits, not just those declaring packages: mise installs the tools of
        # all components together, and any of them may need a package to run
        return dataclasses.replace(
            component,
            depends_on=(*component.depends_on, *installer_names, *privileged_names),
        )

    return [
        *([] if installer is None else [installer]),
        *privileged_by_owner.values(),
        *(with_root_dependencies(component) for component in components),
    ]
