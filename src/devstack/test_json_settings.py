import json

from devstack.json_settings import merge_json_settings, parse_json_object


def test_managed_settings_override_and_unmanaged_settings_survive() -> None:
    existing = json.dumps({"theme": "dark", "editorMode": "default"})

    merged = parse_json_object(merge_json_settings(existing, {"editorMode": "vim"}))

    assert merged == {"theme": "dark", "editorMode": "vim"}


def test_missing_settings_start_from_the_managed_ones() -> None:
    merged = parse_json_object(merge_json_settings(None, {"editorMode": "vim"}))

    assert merged == {"editorMode": "vim"}
