from collections.abc import Iterable, Sequence
from pathlib import Path

from stk.component import Component
from stk.log_file_reporter import state_directory

DEFAULT_ALIAS = "default"
SUDO_ENTRY = "sudo"


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
        entries = [DEFAULT_ALIAS]
    for name in names or (DEFAULT_ALIAS,):
        if name not in entries:
            entries.append(name)
    _write_entries(entries)
    return tuple(entries)


def disable(names: Sequence[str]) -> tuple[str, ...]:
    entries = tuple(entry for entry in enabled_entries() if entry not in names)
    _write_entries(entries)
    return entries


def valid_entries(components: Sequence[Component]) -> frozenset[str]:
    return frozenset(
        {DEFAULT_ALIAS, SUDO_ENTRY, *(component.name for component in components)}
    )


def enabled_component_names(
    entries: Sequence[str], components: Sequence[Component]
) -> tuple[str, ...]:
    return tuple(
        component.name
        for component in components
        if component.name in entries
        or (DEFAULT_ALIAS in entries and not component.optional)
    )
