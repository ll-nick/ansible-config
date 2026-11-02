import re
import subprocess
from pathlib import Path

from stk.engine.component import PrivilegedTask
from stk.helpers.commands import run_command
from stk.helpers.file_edit import replace_line

LOCALE_GEN_PATH = Path("/etc/locale.gen")
LOCALES = ("de_DE.UTF-8", "en_US.UTF-8")


def generate_locales() -> None:
    for locale in LOCALES:
        replace_line(
            LOCALE_GEN_PATH,
            rf"^#?\s*{re.escape(locale)} UTF-8",
            f"{locale} UTF-8",
            extended_regex=True,
        )
    run_command("Generate locales", "locale-gen")


def locales_are_missing() -> bool:
    return any(not locale_is_generated(locale) for locale in LOCALES)


def locale_is_generated(locale: str) -> bool:
    try:
        completed = subprocess.run(
            ["locale", "-a"], capture_output=True, text=True, check=True
        )
    except OSError, subprocess.CalledProcessError:
        return False
    normalized = locale.replace("UTF-8", "utf8").lower()
    return normalized in completed.stdout.lower().split()


GENERATE_LOCALES = PrivilegedTask(
    f"generate {', '.join(LOCALES)}", locales_are_missing, generate_locales
)
