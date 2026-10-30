from devstack.testing import run_with_mise


def test_uv_runs() -> None:
    assert run_with_mise("uv", "--version").strip()
