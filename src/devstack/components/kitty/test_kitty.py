from pathlib import Path

from devstack.machine import HAS_DISPLAY, does_not_run_distribution
from devstack.testing import skip_unless


@skip_unless(HAS_DISPLAY)
@skip_unless(does_not_run_distribution("nixos"))
def test_the_desktop_file_points_at_the_installed_kitty() -> None:
    desktop_file = Path.home() / ".local/share/applications/kitty.desktop"

    assert "mise/installs" in desktop_file.read_text()
