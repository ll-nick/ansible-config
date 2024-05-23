#!/bin/sh

set -e

confirm() {
    printf "%s [y/N] " "$1"
    # Reading from stderr allows to execute the script by piping it to sh
    # See https://stackoverflow.com/a/54396662
    read response <&2
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

install_package() {
    COMMAND=$1
    DEBIAN_PACKAGE=$2
    ARCH_PACKAGE=$3

    if command -v $COMMAND >/dev/null 2>&1; then
        echo "$COMMAND is already installed."
        return
    fi

    echo "$COMMAND is not installed."
    if ! confirm "Do you want to install $COMMAND? This requires sudo."; then
        echo "Skipping $COMMAND installation."
        return
    fi

    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        sudo apt-get update
        sudo apt-get install -y $DEBIAN_PACKAGE
    elif [ "$DISTRO" = "arch" ]; then
        sudo pacman -Syu --noconfirm $ARCH_PACKAGE
    else
        echo "Unsupported distribution: $DISTRO"
        exit 1
    fi
}

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Cannot determine the distribution. Exiting."
    exit 1
fi

# Install ansible dependencies
install_package "git" "git" "git"
install_package "python3" "python3" "python"
install_package "pip3" "python3-pip" "python-pip"

# Install Ansible
if ! python3 -m pip show ansible >/dev/null 2>&1; then
  echo "Ansible is not installed."
  if confirm "Do you want to install ansible?"; then
    python3 -m pip install --user ansible
  else
    echo "Skipping Ansible installation."
  fi
else
  echo "Ansible is already installed."
fi

# Add pip user base binary directory to PATH
export PATH="$HOME/.local/bin:$PATH"

# Run ansible-pull
if ! confirm "All set to run ansible-pull. Do you wish to execute the playbook?"; then
    echo "Skipping ansible-pull execution."
    exit 1
fi

# Ask if the user wants to run it with sudo privileges
echo -e "\nThe playbook installs as many tools as possible at the user level.\n\
However, some dependencies require sudo privileges for system-wide installation.\n\
Running the playbook without these privileges expects those packages to be pre-installed."

if confirm "Do you want to run ansible-pull with sudo privileges?"; then
    echo "Running ansible-pull with sudo..."
    ansible-pull -U https://github.com/ll-nick/ansible-config.git --tags all,privileged -K
else
    echo "Running ansible-pull..."
    ansible-pull -U https://github.com/ll-nick/ansible-config.git
fi

echo "Deployment completed successfully."

