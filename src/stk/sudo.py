import getpass
import os

from gevent import subprocess


class SudoUnavailableError(RuntimeError):
    pass


def _sudo_works_without_password() -> bool:
    return subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0


def _sudo_accepts(password: str) -> bool:
    completed = subprocess.run(
        ["sudo", "-S", "-p", "", "-v"],
        input=password + "\n",
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def obtain_sudo_password() -> str | None:
    if os.geteuid() == 0 or _sudo_works_without_password():
        return None
    for _attempt in range(3):
        password = getpass.getpass("sudo password: ")
        if _sudo_accepts(password):
            return password
    raise SudoUnavailableError("sudo did not accept the password")
