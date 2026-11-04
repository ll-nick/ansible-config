from stk.machine import HAS_DISPLAY
from stk.testing import skip_unless
from stk_config.components.nerdfont.nerdfont import FONTS_DIRECTORY


@skip_unless(HAS_DISPLAY)
def test_the_font_is_installed() -> None:
    assert any(FONTS_DIRECTORY.glob("JetBrainsMono*"))
