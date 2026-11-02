import json
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

from pyinfra.api.operation import OperationMeta
from pyinfra.operations import files


def parse_json_object(text: str) -> dict[str, object]:
    parsed: dict[str, object] = json.loads(text)  # pyright: ignore[reportAny]
    return parsed


def merge_settings(
    existing: Mapping[str, object], managed: Mapping[str, object]
) -> dict[str, object]:
    merged = dict(existing)
    for key, managed_value in managed.items():
        existing_value = merged.get(key)
        if isinstance(existing_value, dict) and isinstance(managed_value, dict):
            merged[key] = merge_settings(
                existing_value,  # pyright: ignore[reportUnknownArgumentType]
                managed_value,  # pyright: ignore[reportUnknownArgumentType]
            )
        else:
            merged[key] = managed_value
    return merged


def merge_json_settings(
    existing_text: str | None, managed: Mapping[str, object]
) -> str:
    existing = parse_json_object(existing_text) if existing_text else {}
    merged = merge_settings(existing, managed)
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
