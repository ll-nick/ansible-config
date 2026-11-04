from pathlib import Path


def test_bashrc_links_into_the_cloned_config() -> None:
    bashrc = Path.home() / ".bashrc"

    assert bashrc.is_symlink()
    assert bashrc.resolve() == Path.home() / ".config" / "bash" / ".bashrc"
