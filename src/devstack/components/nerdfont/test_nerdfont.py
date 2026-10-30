from devstack.components.nerdfont.nerdfont import FONTS_DIRECTORY
from devstack.machine import HAS_DISPLAY
from devstack.testing import skip_unless


@skip_unless(HAS_DISPLAY)
def test_the_font_is_installed() -> None:
    assert any(FONTS_DIRECTORY.glob("JetBrainsMono*"))
