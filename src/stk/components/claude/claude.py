from pathlib import Path

from stk.components.bash.bash import BASH
from stk.components.mise.mise import MISE
from stk.components.nushell.nushell import NUSHELL
from stk.engine.component import Component
from stk.helpers.json_settings import write_merged_json_settings
from stk.helpers.links import symlink_file
from stk.helpers.mise import install_mise_tools
from stk.helpers.shells import add_bash_snippet, add_nushell_snippet

FILES = Path(__file__).resolve().parent / "files"


def apply_claude() -> None:
    config_directory = Path.home() / ".claude"

    install_mise_tools("claude", FILES / "mise.toml")

    symlink_file(FILES / "CLAUDE.md", config_directory / "CLAUDE.md")
    symlink_file(
        FILES / "statusline-command.sh", config_directory / "statusline-command.sh"
    )
    symlink_file(
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


CLAUDE = Component("claude", apply_claude, depends_on=(MISE, BASH, NUSHELL))
