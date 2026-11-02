# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal setup for every machine the owner works on, run on localhost.
Written in Python (3.14, managed with uv) on top of pyinfra, used as a library rather than through its CLI.
Installs and configures a dev environment, preferring user-level installs through mise (`~/.local/bin`) and minimal root.
Tested on Ubuntu (CI) and known to work on NixOS (system packages are Debian only).
This repo is the basis of all the owner's machines, so changes need to be careful and verified.

## Commands

```bash
uv run poe check          # ruff lint + format check, basedpyright, lock check
uv run poe fix            # apply lint and format fixes
uv run pytest             # unit tests + component tests
uv run stk apply -n       # dry run: show the plan and stop
uv run stk apply [names]  # apply components (and their dependencies)
uv run stk apply --skip sudo    # one run without sudo (or --skip <component>)
uv run stk enable [names]       # choose what this machine gets (default, components, sudo)
ci/run.sh all             # Docker: build + apply, verify (pytest), idempotency check
ci/run.sh shell           # shell in the image from the last build
ci/vm.sh                  # disposable desktop VM for display, systemd and sudo tests
```

The command is `stk` (`stk.cli:cli`).
Subcommands: `apply`, `list`, `update`, `check`.

## Architecture

All code lives in `src/stk/`.

**Components** (`components/<name>/{<name>.py, files/, test_<name>.py}`) are the unit of the setup.
Each module exposes an `apply_<name>` function decorated with `@component_deploy("<name>")`
and is registered in `components/__init__.py` as a `Component` with
`depends_on`, `requires` (machine conditions, see `machine.py`) and `system_packages`.
Typical component: install via mise (`install_mise_tools`), clone a config repo from GitHub,
link files and shell snippets, generate init scripts.

**pyinfra use.**
Components may call pyinfra directly.
Shared pyinfra use lives in helper modules in `src/stk/` and the engine (`runner`, `pyinfra_adapters`).
Add a helper when it removes duplication or makes a component easier to read, not to hide pyinfra.

**Two phases.**
pyinfra first prepares a component (runs facts, evaluates the Python in `apply_*`, queues operations), then executes the queued operations.
Plain Python in a component runs at prepare time, so it sees the machine as it is before the component runs.
Tools a component installs itself are therefore not available to prepare-time checks.
Each component gets a fresh pyinfra `State`, prepared right before it executes, so it sees the effects of the components before it.

**Engine.**
`runner.py` plans all components, optionally asks for confirmation, then runs them one at a time in dependency order.
A failed component makes its dependents SKIPPED; independent components continue.
Components with unmet `requires` are NOT_APPLICABLE (not a failure).

**Enabling.**
`enablement.py` keeps what a machine gets in `~/.local/state/stk/enabled`: component names, groups (`default` holds every component that does not say otherwise), `sudo` and exclusions (`-name`, written by `stk disable` for a component a group selects).
Disabling a component also leaves out whatever depends on it.
`requires` says what a machine can do; this says what it should get.
`stk apply` and `stk update` fail without that file, so losing it can only ever reduce what happens.

**Privileged mode.**
With `sudo` enabled, `stk apply` checks without root whether there is work needing it (`pending_sudo_work`), lists it, and only then asks for the password (`sudo.py`).
Components declare root work in two ways, which run before everything else and can sit next to user-level work in the same component:
apt package names in `system_packages`, merged into one synthetic `system-packages` component, and `privileged_tasks`, which each get a synthetic `<name>-privileged` component the owner depends on.
A task pairs an `is_pending` check that must work without root with an `apply` whose operations all run with sudo.
It therefore cannot use tools that components install in the same run.
Everything else must work without root.

**Reporting.**
Components are reported through the `Reporter` protocol (`reporting.py`): `RichReporter`, which only animates on terminals, always combined with `LogFileReporter`.
Keep success output minimal and never hide errors.

**Update steps** (`updates/`) run sequentially against the terminal (`stk update`).
A component can carry an `update` step (`Component.update`), which only applies where the component does.
The core steps (`system`, `dotfiles`, `flatpak` in `updates/registry.py`) belong to no component and run first.
Like `stk apply`, `stk update` shows its plan and asks once; the steps themselves never prompt (except before pushing a version bump).
`stk check` reports their timestamps.
Steps are written against the `UpdateContext` protocol so they can be tested with a recording fake.

**Bootstrap.**
`deploy/deploy.sh` installs mise, uses it to install uv, clones the repo to `~/.config/stk` (the permanent checkout, `checkout.py`) and runs `stk apply`.
The `stk` component installs `~/.local/bin/stk`, a shim that runs the CLI from that checkout.

## Conventions

- Tests are colocated with the code; component tests verify the applied result (e.g. the tool runs, a generated file exists) and use `skip_unless(requirement)` when the component is not applicable everywhere.
  Tests assume the machine was applied, so they run in the Docker harness, not on a bare checkout.
- Prefer separate files in a component's `files/` over inline content.
- Files from `files/` are symlinked (`symlink_file`), not copied, so edits on the machine land in the repository.
  They point into the tree `stk` runs from, normally `~/.config/stk`; applying from another clone re-points them.
  The executable bit comes from git, so scripts need mode 755 in the index.
  systemd units are copied instead, and files a tool rewrites itself are merged (`claude` settings).
- Helpers write files with explicit modes (`644`, `755`) so results do not depend on the umask.
- Linting policy: fix properly first, then a line-level ignore with a reason, never disable rules globally.
  Untyped pyinfra calls are confined to a few adapter modules with line-level ignores.
- Keep `pyinfra<4` pinned: the engine relies on pyinfra internals.
- `HOME=` does not sandbox mise (it reads the config via the passwd entry); use Docker for hermetic tests.
- A change is only done when `uv run poe check`, `uv run pytest` and `ci/run.sh all` are green.
