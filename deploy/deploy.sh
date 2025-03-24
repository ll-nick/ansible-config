#!/bin/sh

set -e

confirm() {
    printf "%s [y/N] " "$1"
    # Reading from stderr allows to execute the script by piping it to sh
    # See https://stackoverflow.com/a/54396662
    read response <&2
    case "$response" in
        [yY][eE][sS] | [yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    else
        echo "Cannot determine the distribution. Exiting."
        exit 1
    fi
}

install_package() {
    COMMAND=$1
    DEBIAN_PACKAGE=$2
    ARCH_PACKAGE=$3

    if command -v $COMMAND > /dev/null 2>&1; then
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

install_pipx() {
    VENV_DIR="$HOME/.local/venvs/pipx"
    if [ -f "$VENV_DIR/bin/pipx" ]; then
        echo "pipx is already installed."
        return
    fi

    echo "pipx is not installed."
    if ! confirm "Do you want to install pipx using a virtual environment?"; then
        echo "Skipping pipx installation."
        return
    fi

    # Create the virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment for pipx at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi

    # Activate the virtual environment and install pipx
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install pipx

    echo "pipx installed successfully in virtual environment at $VENV_DIR"
}

install_ansible() {
    if $HOME/.local/venvs/pipx/bin/pipx list | grep -q ansible; then
        echo "Ansible is already installed via pipx."
        return
    fi

    echo "Ansible is not installed via pipx."
    if confirm "Do you want to install Ansible using pipx?"; then
        $HOME/.local/venvs/pipx/bin/pipx install ansible-core
    else
        echo "Skipping Ansible installation."
    fi
}

run_ansible() {
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
}

main() {
    # Ensure local binary directory is on PATH
    export PATH="$HOME/.local/bin:$PATH"

    detect_distro

    install_package "git" "git" "git"
    install_package "python3" "python3" "python"
    install_package "pip3" "python3-pip" "python-pip"
    install_pipx
    install_ansible

    run_ansible

    echo "Deployment completed successfully."
}

main
