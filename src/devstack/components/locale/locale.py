import re
from pathlib import Path

from gevent import subprocess

from devstack.commands import run_command
from devstack.file_edit import replace_line
from devstack.pyinfra_adapters import component_deploy

LOCALE_GEN_PATH = Path("/etc/locale.gen")
LOCALES = ("de_DE.UTF-8", "en_US.UTF-8")


@component_deploy("locale")
def apply_locale() -> None:
    enabled_locales = [
        replace_line(
            LOCALE_GEN_PATH,
            rf"^#?\s*{re.escape(locale)} UTF-8",
            f"{locale} UTF-8",
            sudo=True,
            extended_regex=True,
        )
        for locale in LOCALES
    ]
    # Also retries after a failed generation, when the file is already edited
    missing_locales = any(not locale_is_generated(locale) for locale in LOCALES)
    run_command(
        "Generate locales",
        "locale-gen",
        when_any_changed=() if missing_locales else enabled_locales,
        sudo=True,
    )


def locale_is_generated(locale: str) -> bool:
    try:
        completed = subprocess.run(
            ["locale", "-a"], capture_output=True, text=True, check=True
        )
    except OSError, subprocess.CalledProcessError:
        return False
    normalized = locale.replace("UTF-8", "utf8").lower()
    return normalized in completed.stdout.lower().split()
