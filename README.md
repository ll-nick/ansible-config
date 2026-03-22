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
A very limited amount of tasks require root privileges for system-wide installation of basic dependencies which can be deployed using the `privileged` tag, see below.
Running the playbook without these privileges expects those packages to be installed already.

The config is tested on
- Arch Linux
- NixOS[^1]
- Ubuntu 24.04

[^1]: kitty needs to be installed via nixpkgs.

## 🚀 Usage

I'm not sure why you would want to use my config but don't let that stop you!

Clone and apply the configuration using `ansible-pull`:

```bash
ansible-pull -U https://github.com/ll-nick/ansible-config.git
```

To also deploy tasks that require root privileges, use:

```bash
ansible-pull -U https://github.com/ll-nick/ansible-config.git --tags all,privileged --ask-become-pass
```

To run individual roles, specify the role name as a tag (e.g. `--tags neovim`).

For first time usage, there is also a [bash script](deploy/deploy.sh) that can be used
 to interactively install the required dependencies (including ansible itself), then execute the playbook.
I host that script using the accompanying Docker file to set everything up in one go using `curl mydomain.com | bash`.

The ansible playbook only installs packages initially, then sets up the `stk` command which handles updating everything in one go.
Check `stk --help` for details.
All tasks in the playbook are idempotent though, so running it again will not cause any harm.

## ♥️ Acknowledgements

Thanks to Jay from [Learn Linux TV](https://www.learnlinux.tv/) who [helped me get started](https://www.youtube.com/watch?v=gIDywsGBqf4).

For the callback plugin, I took some inspiration from Townk's [ansible-beautiful-output](https://github.com/Townk/ansible-beautiful-output).
