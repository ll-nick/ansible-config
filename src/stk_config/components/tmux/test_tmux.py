from stk.helpers.systemd import USER_UNIT_DIRECTORY
from stk.testing import run_with_mise


def test_tmux_runs() -> None:
    assert "tmux" in run_with_mise("tmux", "-V")


def test_the_old_session_service_is_gone() -> None:
    assert not (USER_UNIT_DIRECTORY / "tmux.service").exists()
