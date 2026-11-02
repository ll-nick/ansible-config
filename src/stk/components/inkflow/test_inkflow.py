import os
from pathlib import Path

from stk.machine import HAS_DISPLAY, HAS_INKSCAPE
from stk.testing import skip_unless


@skip_unless(HAS_DISPLAY)
@skip_unless(HAS_INKSCAPE)
def test_the_editor_script_is_executable() -> None:
    script = Path.home() / ".local/bin/inkflow-edit-svg"

    assert os.access(script, os.X_OK)
