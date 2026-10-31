import pytest

from devstack import machine


def test_a_local_x_display_counts_as_a_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    assert machine.has_display()


def test_a_forwarded_x_display_does_not_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPLAY", "localhost:10.0")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    assert not machine.has_display()


def test_wayland_counts_as_a_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")

    assert machine.has_display()


def test_no_display_variables_means_no_display(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)

    assert not machine.has_display()


def test_os_release_is_parsed() -> None:
    fields = machine.parse_os_release(
        '# comment\nNAME="Ubuntu"\nID=ubuntu\nID_LIKE="debian"\n'
    )

    assert fields["ID"] == "ubuntu"
    assert fields["ID_LIKE"] == "debian"


def test_distribution_requirements_follow_the_os_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        machine, "distribution_ids", lambda: frozenset({"ubuntu", "debian"})
    )

    assert machine.runs_distribution("debian", "arch").is_met()
    assert not machine.runs_distribution("arch").is_met()
    assert not machine.does_not_run_distribution("ubuntu").is_met()
    assert machine.does_not_run_distribution("nixos").is_met()


def test_host_requirements_compare_the_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(machine, "hostname", lambda: "workstation")

    assert machine.host_is("workstation").is_met()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("glibc 2.39", (2, 39)),
        ("git version 2.43.0", (2, 43, 0)),
        ("no digits here", None),
    ],
)
def test_versions_are_parsed(text: str, expected: tuple[int, ...] | None) -> None:
    assert machine.parse_version(text) == expected
