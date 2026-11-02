from collections.abc import Iterable, Sequence
from pathlib import Path

from stk.component import DEFAULT_GROUP, Component
from stk.paths import state_directory

SUDO_ENTRY = "sudo"
EXCLUSION_PREFIX = "-"


class NothingEnabledError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            f"Nothing is enabled on this machine ({enabled_file()} does not exist)."
            + " Run `stk enable` to choose what it gets."
        )


def enabled_file() -> Path:
    return state_directory() / "enabled"


def enabled_entries() -> tuple[str, ...]:
    try:
        text = enabled_file().read_text()
    except FileNotFoundError:
        raise NothingEnabledError from None
    return tuple(line.strip() for line in text.splitlines() if line.strip())


def sudo_is_enabled() -> bool:
    try:
        return SUDO_ENTRY in enabled_entries()
    except NothingEnabledError:
        return False


def _write_entries(entries: Iterable[str]) -> None:
    enabled_file().parent.mkdir(parents=True, exist_ok=True)
    enabled_file().write_text("".join(f"{entry}\n" for entry in entries))


def enable(names: Sequence[str]) -> tuple[str, ...]:
    """Adds the names; the first call on a machine also adds the default components."""
    try:
        entries = list(enabled_entries())
    except NothingEnabledError:
        entries = [DEFAULT_GROUP]
    for name in names or (DEFAULT_GROUP,):
        if f"{EXCLUSION_PREFIX}{name}" in entries:
            entries.remove(f"{EXCLUSION_PREFIX}{name}")
        if name not in entries:
            entries.append(name)
    _write_entries(entries)
    return tuple(entries)


def disable(names: Sequence[str], components: Sequence[Component]) -> tuple[str, ...]:
    """Removes the names; a component a group still selects gets an exclusion."""
    entries = [entry for entry in enabled_entries() if entry not in names]
    for component in components:
        exclusion = f"{EXCLUSION_PREFIX}{component.name}"
        if (
            component.name in names
            and exclusion not in entries
            and any(group in entries for group in component.groups)
        ):
            entries.append(exclusion)
    _write_entries(entries)
    return tuple(entries)


def excluded_names(entries: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        entry.removeprefix(EXCLUSION_PREFIX)
        for entry in entries
        if entry.startswith(EXCLUSION_PREFIX)
    )


def valid_entries(components: Sequence[Component]) -> frozenset[str]:
    return frozenset(
        {
            SUDO_ENTRY,
            *(component.name for component in components),
            *(group for component in components for group in component.groups),
        }
    )


def enabled_component_names(
    entries: Sequence[str], components: Sequence[Component]
) -> tuple[str, ...]:
    excluded = excluded_names(entries)
    return tuple(
        component.name
        for component in components
        if component.name not in excluded
        and (
            component.name in entries
            or any(group in entries for group in component.groups)
        )
    )
