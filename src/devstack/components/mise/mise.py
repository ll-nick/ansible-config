from devstack.commands import run_command
from devstack.mise import MISE_INSTALL_SCRIPT_URL, mise_executable
from devstack.pyinfra_adapters import component_deploy


@component_deploy("mise")
def apply_mise() -> None:
    if not mise_executable().exists():
        # Downloading first, as a failing curl in a pipe would run an empty script
        run_command(
            "Install mise",
            'installer="$(mktemp)"'
            + " && trap 'rm -f \"$installer\"' EXIT"
            + f' && curl -fsSL {MISE_INSTALL_SCRIPT_URL} -o "$installer"'
            + ' && sh "$installer"',
        )
