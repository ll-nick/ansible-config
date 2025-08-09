#!/usr/bin/env bash

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
    PACKAGE=$1

    if command -v $PACKAGE > /dev/null 2>&1; then
        echo "$PACKAGE is already installed."
        return
    fi

    echo "$PACKAGE is not installed."
    if ! confirm "Do you want to install $PACKAGE? This requires sudo."; then
        echo "Skipping $PACKAGE installation."
        return
    fi

    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        sudo apt-get update
        sudo apt-get install -y $PACKAGE
    elif [ "$DISTRO" = "arch" ]; then
        sudo pacman -Syu --noconfirm $PACKAGE
    else
        echo "Unsupported distribution: $DISTRO"
        exit 1
    fi
}

install_mise() {
    if command -v mise > /dev/null 2>&1; then
        echo "mise is already installed."
        return
    fi

    echo "mise is not installed."
    echo "mise is used to install ansible and its dependencies in an isolated environment."
    if ! confirm "Do you want to install mise?"; then
        echo "Skipping mise installation."
        return
    fi

    curl https://mise.run | sh
}

activate_mise() {
    eval "$($HOME/.local/bin/mise activate --shims)"
}

install_mise_package() {
    PACKAGE=$1

    if command -v $PACKAGE > /dev/null 2>&1; then
        echo "$PACKAGE is already installed."
        return
    fi

    echo "$PACKAGE is not installed."
    if confirm "Do you want to install $PACKAGE using mise?"; then
        mise use --global $PACKAGE
    else
        echo "Skipping $PACKAGE installation."
    fi
}

run_ansible() {
    echo "All set to run ansible-pull."
    if ! confirm "Do you wish to execute the playbook?"; then
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

    install_package "curl"
    install_package "git"

    install_mise
    activate_mise

    install_mise_package "python"
    install_mise_package "pipx"
    install_mise_package "ansible"

    # Additional tasks required for the playbook
    ansible-galaxy collection install community.general

    run_ansible

    echo "Deployment completed successfully."
}

main
