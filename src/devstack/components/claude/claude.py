from pathlib import Path

from devstack.json_settings import write_merged_json_settings
from devstack.links import link_repository_file
from devstack.mise import install_mise_tools
from devstack.pyinfra_adapters import component_deploy
from devstack.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


@component_deploy("claude")
def apply_claude() -> None:
    config_directory = Path.home() / ".claude"

    install_mise_tools("claude", FILES / "mise.toml")

    link_repository_file(FILES / "CLAUDE.md", config_directory / "CLAUDE.md")
    link_repository_file(
        FILES / "statusline-command.sh", config_directory / "statusline-command.sh"
    )
    link_repository_file(
        FILES / "fetch-usage-limits.sh", config_directory / "fetch-usage-limits.sh"
    )

    # Merged with the existing settings, as Claude Code writes to this file itself
    write_merged_json_settings(
        config_directory / "settings.json",
        {
            "statusLine": {
                "type": "command",
                "command": f"bash {config_directory}/statusline-command.sh",
            },
            "enabledPlugins": {"frontend-design@claude-plugins-official": False},
            "tui": "fullscreen",
            "editorMode": "vim",
            "preferredNotifChannel": "notifications_disabled",
            "remoteControlAtStartup": True,
            "inputNeededNotifEnabled": True,
            "agentPushNotifEnabled": True,
            "useAutoModeDuringPlan": False,
        },
    )

    add_bash_snippet(FILES / "claude.bash")
    add_nushell_snippet(FILES / "claude.nu")
