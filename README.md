# 🛠️ devstack

My personal setup,
used to configure and keep up to date every machine I work on.

It installs and configures a dev environment on localhost:
shells, editors, CLI tools, a terminal and (on machines with a display) the desktop.
Everything lives at the user level in `~/.local/bin` and `~/.config` wherever possible,
installed through [mise](https://mise.jdx.dev/).
A very small number of parts need root,
for example system packages and locales.
Those only run in `--privileged` mode.

The setup is written in Python on top of [pyinfra](https://pyinfra.com/),
which is used as a library.
The `stk` command (also available as `devstack`) is the single entry point
for applying the configuration and for keeping everything up to date afterwards.

The config is [continuously tested on the latest Ubuntu](https://github.com/ll-nick/devstack/actions/workflows/ci.yml).
It also works on NixOS, without `--privileged`.

## 🚀 Usage

I'm not sure why you would want to use my config but don't let that stop you!

The only requirements are `curl` and `git`.
The bootstrap script installs [uv](https://docs.astral.sh/uv/) if needed,
clones this repository to `~/.config/devstack` and applies the configuration:

```bash
curl -fsSL https://raw.githubusercontent.com/ll-nick/devstack/main/deploy/deploy.sh | sh
```

```text
Options:
  -y, --no-confirm      Automatically answer yes to all prompts.
  --privileged          Also apply the parts that need root (requires sudo).
  --branch <name>       Check out this branch of the repository.
  --repository <url>    Clone from this repository instead of the default.
```

From then on, everything runs through `stk`:

| Command | |
| --- | --- |
| `stk apply [COMPONENT...]` | Bring the machine in line with the config. Dependencies are included automatically. |
| `stk apply -n` | Show what would change and stop. |
| `stk list` | List the components, their dependencies and whether they apply to this machine. |
| `stk update [STEP...]` | Update the system, mise tools, tmux and neovim plugins, flatpaks and this config. |
| `stk check` | Show when each update step last ran. |

`stk apply` is idempotent, so running it again does no harm.
On a settled machine it takes a few seconds and prints a single line.
Output stays quiet on success, errors are always shown, `-v` adds details,
and every run is logged to `~/.local/state/devstack/runs/` (`last-run.log` links to the latest).

Independent components are applied even if another one fails.
Components that depend on a failed one are skipped.
The exit code is 1 if any component failed or was skipped,
and 3 with `--fail-on-change` if something had to be changed.

## 🧩 Components

A component is a self-contained piece of the setup, such as `neovim` or `tmux`.
Each one lives in `src/devstack/components/<name>/` together with its files and its test:

```text
neovim/
├── neovim.py        what to do
├── files/           configs and snippets that get copied to the machine
└── test_neovim.py   checks that the result works
```

Components declare what they need:

- `depends_on`: other components that have to be applied first.
- `requires`: conditions on the machine, for example a display, systemd, a hostname, or `--privileged`.
  Components whose requirements are not met are not applicable and silently left out.
- `system_packages`: apt packages, installed in a single step before everything else in `--privileged` mode.

See [`src/devstack/components/__init__.py`](src/devstack/components/__init__.py) for the registry.

## 🧪 Development

```bash
uv run poe check     # lint, format check, type check and lock check
uv run poe fix       # apply lint and format fixes
uv run pytest        # tests of the pure logic, and of the result if the machine was applied
ci/run.sh all        # build, verify and check idempotency on a fresh Ubuntu in Docker
```

The tests of a component check the state of the machine it was applied to,
which is why the CI harness applies everything in a container first.
Applying inside Docker is also the safe way to try changes:
`ci/run.sh shell` opens a shell in the image that was just built.

Adding a component means a new folder, an entry in the registry,
and a test that proves the tool or config actually works.
Components never import pyinfra directly, only the helpers in `src/devstack`.
That is enforced by a lint rule and keeps the option open to replace pyinfra later.

## ♥️ Acknowledgements

Thanks to Jay from [Learn Linux TV](https://www.learnlinux.tv/) who [helped me get started](https://www.youtube.com/watch?v=gIDywsGBqf4)
back when this was an Ansible playbook.
