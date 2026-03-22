# xdg_open

Forwards `xdg-open` calls from remote servers to the local machine's browser via an SSH reverse tunnel.

## How it works

**Local machine** (`has_display: true`): two systemd user units create a Unix socket that runs `xdg-open` on each incoming connection.
SSH `RemoteForward` exposes this socket as a TCP port on each remote host.

**Remote machine** (`has_display: false`): a Python shim is installed at `~/.local/bin/xdg-open` (takes priority over `/usr/bin/xdg-open`).
It rewrites `localhost`/`127.0.0.1` in URLs to the remote's hostname, then forwards the URL through the tunnel.
Falls back to the real `xdg-open` if the tunnel is unavailable.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `xdg_open_port` | `19999` | TCP port used by `RemoteForward` |
| `xdg_open_open_cmd` | `flatpak run org.mozilla.firefox` | Command used to open URLs on the local machine |

`RemoteForward` entries are injected into **all existing `Host` blocks** in `~/.ssh/config` automatically.

## Caveats

- **Webserver bind address**: preview plugins (e.g. markdown-preview.nvim) must bind to `0.0.0.0`, not `127.0.0.1`, so the rewritten hostname URL is reachable. Configure this per plugin (`g:mkdp_open_to_the_world = 1` for markdown-preview.nvim).
- **Tunnel lifetime**: `RemoteForward` only exists for the duration of the SSH session. If a tmux session outlives the connection, the shim falls back to the real `xdg-open` on the remote (typically a no-op on headless servers).
- **`xdg_open_open_cmd`**: `xdg-open` and `gio open` do not work from systemd service context with Flatpak browsers. Use `flatpak run <app-id>` directly, or `gtk-launch` for non-Flatpak browsers.
