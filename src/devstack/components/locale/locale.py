import re
from pathlib import Path

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
        )
        for locale in LOCALES
    ]
    run_command(
        "Generate locales", "locale-gen", when_any_changed=enabled_locales, sudo=True
    )
