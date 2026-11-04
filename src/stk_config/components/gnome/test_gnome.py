from stk.helpers.dconf import read_dconf_value
from stk.machine import HAS_DISPLAY
from stk.testing import skip_unless


@skip_unless(HAS_DISPLAY)
def test_dark_mode_is_enabled() -> None:
    assert read_dconf_value("/org/gnome/desktop/interface/color-scheme") == (
        "'prefer-dark'"
    )
