import json
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def parse_json_object(text: str) -> dict[str, object]:
    parsed: dict[str, object] = json.loads(text)  # pyright: ignore[reportAny]
    return parsed


def merge_json_settings(
    existing_text: str | None, managed: Mapping[str, object]
) -> str:
    existing = parse_json_object(existing_text) if existing_text else {}
    merged = {**existing, **managed}
    return json.dumps(merged, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_merged_json_settings(
    destination: Path, managed: Mapping[str, object]
) -> OperationMeta:
    existing_text = destination.read_text() if destination.exists() else None
    return files.put(
        name=f"Merge managed settings into {destination}",
        src=StringIO(merge_json_settings(existing_text, managed)),
        dest=str(destination),
        mode="644",
    )
