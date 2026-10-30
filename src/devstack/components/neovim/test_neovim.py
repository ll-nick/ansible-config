from devstack.testing import run_with_mise


def test_neovim_runs() -> None:
    assert "NVIM" in run_with_mise("nvim", "--version")


def test_tree_sitter_runs() -> None:
    assert run_with_mise("tree-sitter", "--version").strip()
