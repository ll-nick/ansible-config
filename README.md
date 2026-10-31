# 🛠️ devstack

This repository contains my personal setup used to configure and manage my systems consistently and efficiently.

## 📦 Contents

The setup is written in Python on top of [pyinfra](https://pyinfra.com/) and is meant to be run on localhost.
It is designed to install as many tools as possible on the user level.

A very limited amount of tasks require root privileges for system-wide installation of basic dependencies,
which can be deployed using the `--privileged` mode.
Running without these privileges expects those packages to be installed already.

The config is [continuously tested on the latest Ubuntu](https://github.com/ll-nick/devstack/actions/workflows/ci.yml).
It is also known to work on NixOS (without `--privileged`).

## 🚀 Usage

I'm not sure why you would want to use my config but don't let that stop you!

The only requirements are `curl` and `git`.
The bootstrap script installs [uv](https://docs.astral.sh/uv/) if needed,
clones this repository to `~/.config/devstack` and applies the configuration:

```bash
curl -fsSL https://raw.githubusercontent.com/ll-nick/devstack/main/deploy/deploy.sh | sh
```

Check `deploy.sh --help` for its options, for example `--privileged`.

From then on, everything runs through the `stk` command:
`stk apply` applies the configuration (or only some components, e.g. `stk apply neovim`)
and `stk update` keeps everything up to date.
Check `stk --help` for details.
Everything is idempotent, so running it again will not cause any harm.

## ♥️ Acknowledgements

Thanks to Jay from [Learn Linux TV](https://www.learnlinux.tv/) who [helped me get started](https://www.youtube.com/watch?v=gIDywsGBqf4)
back when this was an Ansible playbook.
