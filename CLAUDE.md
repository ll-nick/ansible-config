# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal setup for every machine the owner works on, run on localhost.
Written in Python (3.14, managed with uv) on top of pyinfra, used as a library rather than through its CLI.
Installs and configures a dev environment, preferring user-level installs through mise (`~/.local/bin`) and minimal root.
Tested on Ubuntu (CI) and known to work on NixOS (unprivileged only).
This repo is the basis of all the owner's machines, so changes need to be careful and verified.

## Commands

```bash
uv run poe check          # ruff lint + format check, basedpyright, lock check
uv run poe fix            # apply lint and format fixes
uv run pytest             # unit tests + component tests
uv run stk apply -n       # dry run: show the plan and stop
uv run stk apply [names]  # apply components (and their dependencies)
uv run stk apply --privileged   # also install system packages via sudo
ci/run.sh all             # Docker: build + apply, verify (pytest), idempotency check
ci/run.sh shell           # shell in the image from the last build
```

`stk` and `devstack` are the same entry point (`devstack.cli:cli`).
Subcommands: `apply`, `list`, `update`, `check`.

## Architecture

All code lives in `src/devstack/`.

**Components** (`components/<name>/{<name>.py, files/, test_<name>.py}`) are the unit of the setup.
Each module exposes an `apply_<name>` function decorated with `@component_deploy("<name>")`
and is registered in `components/__init__.py` as a `Component` with
`depends_on`, `requires` (machine conditions, see `machine.py`) and `system_packages`.
Typical component: install via mise (`install_mise_tools`), clone a config repo from GitHub,
link files and shell snippets, generate init scripts.

**Components must not import pyinfra.**
A nested `components/ruff.toml` bans it.
All pyinfra use is confined to the helper modules (`file_copy`, `commands`, `shells`, `mise`, `links`, `github`, `generated_file`, `file_edit`, `systemd`, `dconf`, `archives`, `json_settings`, `system_packages`) and the engine (`runner`, `pyinfra_adapters`).
Add a helper rather than calling pyinfra from a component.

**Two phases.**
pyinfra first prepares a component (runs facts, evaluates the Python in `apply_*`, queues operations), then executes the queued operations.
Plain Python in a component runs at prepare time, so it sees the machine as it is before the component runs.
Tools a component installs itself are therefore not available to prepare-time checks.
Each component gets a fresh pyinfra `State`, prepared right before it executes, so it sees the effects of components it depends on.

**Engine.**
`runner.py` plans all components in parallel, optionally asks for confirmation, then `scheduler.py` runs components concurrently (`--jobs`) as gevent greenlets, respecting `depends_on`.
A failed component makes its dependents SKIPPED; independent components continue.
Components with unmet `requires` are NOT_APPLICABLE (not a failure).
pyinfra keeps its current state in a process-wide global, which `pyinfra_adapters.py` replaces with per-greenlet-tree storage; do not remove it (there is a regression test).
Use `gevent.subprocess` for subprocesses during prepare, not threads.

**Privileged mode.**
`--privileged` obtains the sudo password up front (`sudo.py`) and enables privileged parts.
Components declare apt package names in `system_packages`; the runner merges them into one synthetic `system-packages` component that runs first.
Privileged operations use `_sudo=True`; everything else must work without root.

**Reporting.**
Components are reported through the `Reporter` protocol (`reporting.py`): `RichReporter` on terminals, `PlainReporter` otherwise, always combined with `LogFileReporter`.
Keep success output minimal and never hide errors.

**Update steps** (`updates/`) are the second registered unit besides components.
They are interactive and run sequentially against the terminal (`stk update`): system, mise, dotfiles (pull this repo and re-run `stk apply`), tmux, neovim, flatpak.
`stk check` reports their timestamps.
Steps are written against the `UpdateContext` protocol so they can be tested with a recording fake.

**Bootstrap.**
`deploy/deploy.sh` installs uv, clones the repo to `~/.config/devstack` (the permanent checkout, `checkout.py`) and runs `stk apply`.
The `stk` component installs `~/.local/bin/stk`, a shim that runs the CLI from that checkout.

## Conventions

- Tests are colocated with the code; component tests verify the applied result (e.g. the tool runs, a generated file exists) and use `skip_unless(requirement)` when the component is not applicable everywhere.
  Tests assume the machine was applied, so they run in the Docker harness, not on a bare checkout.
- Prefer separate files in a component's `files/` over inline content.
- Files from `files/` are symlinked (`link_repository_file`), not copied, so edits on the machine land in the repository.
  They point into the tree `stk` runs from, normally `~/.config/devstack`; applying from another clone re-points them.
  The executable bit comes from git, so scripts need mode 755 in the index.
  systemd units are copied instead, and files a tool rewrites itself are merged (`claude` settings).
- Helpers write files with explicit modes (`644`, `755`) so results do not depend on the umask.
- Linting policy: fix properly first, then a line-level ignore with a reason, never disable rules globally.
  Untyped pyinfra/gevent calls are confined to a few adapter modules with line-level ignores.
- Keep `pyinfra<4` pinned: the engine relies on pyinfra internals.
- `HOME=` does not sandbox mise (it reads the config via the passwd entry); use Docker for hermetic tests.
- A change is only done when `uv run poe check`, `uv run pytest` and `ci/run.sh all` are green.
