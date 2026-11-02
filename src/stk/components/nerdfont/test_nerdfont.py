from stk.components.nerdfont.nerdfont import FONTS_DIRECTORY
from stk.machine import HAS_DISPLAY
from stk.testing import skip_unless


@skip_unless(HAS_DISPLAY)
def test_the_font_is_installed() -> None:
    assert any(FONTS_DIRECTORY.glob("JetBrainsMono*"))
