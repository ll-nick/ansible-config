import os
from datetime import UTC, datetime
from pathlib import Path


def _data_home() -> Path:
    configured = os.environ.get("XDG_DATA_HOME")
    return Path(configured) if configured else Path.home() / ".local/share"


def _timestamp_file(step_name: str) -> Path:
    return _data_home() / "stk" / "timestamps" / f"{step_name}.txt"


def record_update(step_name: str, moment: datetime | None = None) -> None:
    timestamp_file = _timestamp_file(step_name)
    timestamp_file.parent.mkdir(parents=True, exist_ok=True)
    moment = moment or datetime.now(UTC)
    timestamp_file.write_text(f"{int(moment.timestamp())}\n")


def last_update(step_name: str) -> datetime | None:
    try:
        seconds = int(_timestamp_file(step_name).read_text().strip())
    except OSError, ValueError:
        return None
    return datetime.fromtimestamp(seconds, tz=UTC)


def skipped_step_names() -> frozenset[str]:
    """Steps not to run on this machine, one per line in ~/.config/stk/skip."""
    try:
        text = (Path.home() / ".config/stk/skip").read_text()
    except OSError:
        return frozenset()
    return frozenset(line.strip() for line in text.splitlines() if line.strip())
