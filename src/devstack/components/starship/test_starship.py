from devstack.testing import run_with_mise


def test_starship_runs() -> None:
    assert run_with_mise("starship", "--version").strip()
