from devstack.testing import run_with_mise


def test_tmux_runs() -> None:
    assert "tmux" in run_with_mise("tmux", "-V")
