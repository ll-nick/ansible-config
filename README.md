# 🛠️ Personal Ansible Configuration

This repository contains my personal Ansible setup used to configure and manage my systems consistently and efficiently.

## 📦 Contents

The playbook is meant to be run on localhost via `ansible-pull`.  
It is designed to install as many tools as possible on the user level and

<details>
<summary>to look good doing so 😎</summary>

![stdout during playbook execution](assets/stdout.png)

</details>

---
A very limited amount of tasks require root privileges for system-wide installation of basic dependencies which can be deployed using the `privileged` mode, see below.
Running the playbook without these privileges expects those packages to be installed already.

The config is [continuously tested on the latest Ubuntu](https://github.com/ll-nick/ansible-config/actions/workflows/ci.yml).
It is also known to work on the following distributions:
- Arch Linux
- NixOS[^1][^2]

[^1]: kitty needs to be installed via nixpkgs.
[^2]: On NixOS, the `--privileged` mode is not supported.

## 🚀 Usage

I'm not sure why you would want to use my config but don't let that stop you!

Clone and apply the configuration using `ansible-pull`:

```bash
ansible-pull -U https://github.com/ll-nick/ansible-config.git
```

To also deploy tasks that require root privileges, use:

```bash
ansible-pull -U https://github.com/ll-nick/ansible-config.git -e run_privileged=true --ask-become-pass
```

To run individual roles, specify the role name as a tag (e.g. `--tags neovim`).

For first time usage, there is also a [bash script](deploy/deploy.sh) that can be used
to interactively install the required dependencies (including ansible itself), then execute the playbook.

```bash
bash deploy/deploy.sh [OPTIONS]

Options:
  -y, --no-confirm          Automatically answer yes to all prompts.
  --privileged              Also run privileged tasks (requires sudo).
  --playbook-path <dir>     Run ansible-playbook from a local directory instead of ansible-pull.
  --tags <tags>             Limit execution to roles/tasks with the given tags (comma-separated).
```

`curl https://raw.githubusercontent.com/ll-nick/ansible-config/refs/heads/main/deploy/deploy.sh | sh` will get you up and running in one go.  
I host that script using the accompanying Docker file to set everything up in one go using `curl mydomain.com | sh`.

The ansible playbook only installs packages initially, then sets up the `stk` command which handles updating everything in one go.
Check `stk --help` for details.
All tasks in the playbook are idempotent though, so running it again will not cause any harm.

## ♥️ Acknowledgements

Thanks to Jay from [Learn Linux TV](https://www.learnlinux.tv/) who [helped me get started](https://www.youtube.com/watch?v=gIDywsGBqf4).

For the callback plugin, I took some inspiration from Townk's [ansible-beautiful-output](https://github.com/Townk/ansible-beautiful-output).
