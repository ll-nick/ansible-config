from pathlib import Path

from gevent import subprocess

from devstack.archives import download_and_extract_zip
from devstack.commands import run_command
from devstack.dconf import DconfSetting, apply_dconf_settings
from devstack.file_copy import EXECUTABLE_MODE, copy_file
from devstack.machine import distribution_ids
from devstack.mise import install_mise_tools, mise_executable
from devstack.pyinfra_adapters import component_deploy

FILES = Path(__file__).resolve().parent / "files"
CURSOR_THEME_NAME = "catppuccin-mocha-blue-cursors"
CURSOR_THEME_URL = (
    "https://github.com/catppuccin/cursors/releases/download/v2.0.0/"
    + f"{CURSOR_THEME_NAME}.zip"
)
PAPERWM_UUID = "paperwm@paperwm.github.com"
PAPERWM_KEYBINDINGS_KEY = "/org/gnome/shell/extensions/paperwm/keybindings"
NIXOS_CERTIFICATE_BUNDLE = "/etc/ssl/certs/ca-bundle.crt"
CUSTOM_KEYBINDINGS_KEY = (
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
)
PAPERWM_TOGGLE_KEYBINDING_KEY = f"{CUSTOM_KEYBINDINGS_KEY}/paperwm-toggle"

PAPERWM_KEYBINDINGS = (
    DconfSetting("close-window", "['<Super>BackSpace', '<Super>x']"),
    DconfSetting("move-down", "['<Control><Super>Down', '<Shift><Super>j']"),
    DconfSetting(
        "move-down-workspace", "['<Control><Super>Page_Down', '<Shift><Alt><Super>j']"
    ),
    DconfSetting(
        "move-left",
        "['<Control><Super>comma', '<Shift><Super>comma',"
        + " '<Control><Super>Left', '<Shift><Super>h']",
    ),
    DconfSetting("move-monitor-left", "['<Shift><Alt><Super>h']"),
    DconfSetting("move-monitor-right", "['<Shift><Alt><Super>l']"),
    DconfSetting(
        "move-right",
        "['<Control><Super>period', '<Shift><Super>period',"
        + " '<Control><Super>Right', '<Shift><Super>l']",
    ),
    DconfSetting("move-up", "['<Control><Super>Up', '<Shift><Super>k']"),
    DconfSetting(
        "move-up-workspace", "['<Control><Super>Page_Up', '<Shift><Alt><Super>k']"
    ),
    DconfSetting("new-window", "['<Super>Return']"),
    DconfSetting("switch-down", "['<Super>Down', '<Super>j']"),
    DconfSetting("switch-down-workspace", "['<Super>Page_Down', '<Alt><Super>j']"),
    DconfSetting("switch-left", "['<Super>Left', '<Super>h']"),
    DconfSetting("switch-monitor-left", "['<Alt><Super>h']"),
    DconfSetting("switch-monitor-right", "['<Alt><Super>l']"),
    DconfSetting("switch-right", "['<Super>l']"),
    DconfSetting("switch-up", "['<Super>Up', '<Super>k']"),
    DconfSetting("switch-up-workspace", "['<Super>Page_Up', '<Alt><Super>k']"),
    DconfSetting("toggle-scratch", "['<Shift><Alt><Super>Escape']"),
    DconfSetting("toggle-scratch-layer", "['<Alt><Super>Escape']"),
)


def list_gnome_extensions(*arguments: str) -> str:
    try:
        completed = subprocess.run(
            [str(mise_executable()), "exec", "--", "gext", "list", *arguments],
            capture_output=True,
            text=True,
            check=True,
        )
    except OSError, subprocess.CalledProcessError:
        return ""
    return completed.stdout


@component_deploy("gnome")
def apply_gnome() -> None:
    home = Path.home()

    apply_dconf_settings(
        [
            DconfSetting("/org/gnome/desktop/interface/color-scheme", "'prefer-dark'"),
            # Required for the EurKey layout to work
            DconfSetting("/org/gnome/desktop/input-sources/show-all-sources", "true"),
            DconfSetting(
                "/org/gnome/desktop/input-sources/sources",
                "[('xkb', 'eu'), ('xkb', 'de')]",
            ),
            DconfSetting(
                "/org/gnome/desktop/input-sources/xkb-options",
                "['caps:escape_shifted_capslock']",
            ),
            DconfSetting(
                "/org/gnome/settings-daemon/plugins/media-keys/screensaver",
                "['<Control><Alt>l']",
            ),
        ]
    )

    # Some applications only respect the cursor theme in ~/.icons
    # while others only respect it in ~/.local/share/icons
    for icons_directory in (home / ".icons", home / ".local/share/icons"):
        if not (icons_directory / CURSOR_THEME_NAME).exists():
            download_and_extract_zip(CURSOR_THEME_URL, icons_directory)
    apply_dconf_settings(
        [
            DconfSetting(
                "/org/gnome/desktop/interface/cursor-theme", f"'{CURSOR_THEME_NAME}'"
            )
        ]
    )

    light_wallpaper = home / "Pictures/wallpaper-light.png"
    dark_wallpaper = home / "Pictures/wallpaper-dark.png"
    copy_file(FILES / "wallpaper-light.png", light_wallpaper)
    copy_file(FILES / "wallpaper-dark.png", dark_wallpaper)
    apply_dconf_settings(
        [
            DconfSetting(
                "/org/gnome/desktop/background/picture-uri",
                f"'file:///{light_wallpaper}'",
            ),
            DconfSetting(
                "/org/gnome/desktop/background/picture-uri-dark",
                f"'file:///{dark_wallpaper}'",
            ),
        ]
    )

    install_mise_tools("gnome", FILES / "mise.toml")
    _install_and_enable_paperwm()

    apply_dconf_settings(
        [
            DconfSetting(f"{PAPERWM_KEYBINDINGS_KEY}/{binding.key}", binding.value)
            for binding in PAPERWM_KEYBINDINGS
        ]
    )

    # Lets others who use this account switch to plain GNOME and back
    paperwm_toggle = home / ".local/bin/paperwm-toggle"
    copy_file(FILES / "paperwm-toggle", paperwm_toggle, mode=EXECUTABLE_MODE)
    toggle_key = PAPERWM_TOGGLE_KEYBINDING_KEY
    apply_dconf_settings(
        [
            DconfSetting(CUSTOM_KEYBINDINGS_KEY, f"['{toggle_key}/']"),
            DconfSetting(f"{PAPERWM_TOGGLE_KEYBINDING_KEY}/name", "'Toggle PaperWM'"),
            DconfSetting(
                f"{PAPERWM_TOGGLE_KEYBINDING_KEY}/command", f"'{paperwm_toggle}'"
            ),
            DconfSetting(f"{PAPERWM_TOGGLE_KEYBINDING_KEY}/binding", "'<Super><Alt>p'"),
        ]
    )


def _install_and_enable_paperwm() -> None:
    gext = f"{mise_executable()} exec -- gext"
    if PAPERWM_UUID not in list_gnome_extensions("--only-uuid", "--all"):
        certificates = (
            f"SSL_CERT_FILE={NIXOS_CERTIFICATE_BUNDLE} "
            if "nixos" in distribution_ids()
            else ""
        )
        run_command("Install PaperWM", f"{certificates}{gext} install {PAPERWM_UUID}")
    if PAPERWM_UUID not in list_gnome_extensions("--only-uuid"):
        run_command("Enable PaperWM", f"{gext} enable {PAPERWM_UUID}")
