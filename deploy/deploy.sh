#!/usr/bin/env bash

set -e

NO_CONFIRM=false
PRIVILEGED_MODE=""

COLOR_TITLE='\033[1;34m'   # Bold Blue
COLOR_INFO='\033[0;36m'    # Cyan
COLOR_WARN='\033[0;33m'    # Yellow
COLOR_ERROR='\033[0;31m'   # Red
COLOR_SUCCESS='\033[0;32m' # Green
COLOR_RESET='\033[0m'

print_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  -y, --no-confirm   Automatically answer yes to all prompts.
  --privileged       Run ansible-pull with sudo privileges (non-interactive).
  --unprivileged     Run ansible-pull without sudo privileges (non-interactive).
  -h, --help         Show this help message and exit.
EOF
}

print_header() {
    local title="$1"
    local width=$((${#title}))
    local top="╭$(printf '─%.0s' $(seq 1 $width))╮"
    local bottom="╰$(printf '─%.0s' $(seq 1 $width))╯"

    echo -e "\n${COLOR_TITLE}${top}${COLOR_RESET}"
    echo -e "${COLOR_TITLE}│${COLOR_RESET} ${title} ${COLOR_TITLE}│${COLOR_RESET}"
    echo -e "${COLOR_TITLE}${bottom}${COLOR_RESET}"
}

confirm() {
    if [ "$NO_CONFIRM" = true ]; then
        return 0
    fi

    printf "  ${COLOR_INFO}➤ %s${COLOR_RESET} [y/N] " "$1"
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
        echo -e "  ${COLOR_SUCCESS}✔ Detected distribution: $DISTRO${COLOR_RESET}"
    else
        echo -e "  ${COLOR_ERROR}✖ Cannot determine the distribution. Exiting.${COLOR_RESET}"
        exit 1
    fi
}

ensure_system_package() {
    PACKAGE=$1

    if command -v $PACKAGE > /dev/null 2>&1; then
        echo -e "  ${COLOR_SUCCESS}✔ $PACKAGE is already installed.${COLOR_RESET}"
        return
    fi

    echo -e "  ${COLOR_WARN}⚠ $PACKAGE is not installed.${COLOR_RESET}"
    if ! confirm "Do you want to install $PACKAGE? This requires sudo."; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: $PACKAGE is required but not installed.${COLOR_RESET}"
        exit 1
    fi

    echo -e "  ${COLOR_INFO}⬇ Installing $PACKAGE...${COLOR_RESET}"
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        sudo apt-get update
        sudo apt-get install -y $PACKAGE
    elif [ "$DISTRO" = "arch" ]; then
        sudo pacman -Syu --noconfirm $PACKAGE
    else
        echo -e "  ${COLOR_ERROR}✖ Unsupported distribution: $DISTRO${COLOR_RESET}"
        exit 1
    fi

    # Verify install
    if ! command -v "$PACKAGE" > /dev/null 2>&1; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: Failed to install $PACKAGE.${COLOR_RESET}"
        exit 1
    fi

    echo -e "  ${COLOR_SUCCESS}✔ $PACKAGE installed successfully.${COLOR_RESET}"
}

ensure_mise() {

    if command -v mise > /dev/null 2>&1; then
        echo -e "  ${COLOR_SUCCESS}✔ mise is already installed.${COLOR_RESET}"
        return
    fi

    echo -e "  ${COLOR_WARN}⚠ mise is not installed.${COLOR_RESET}"
    if ! confirm "Do you want to install mise?"; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: mise is required but not installed.${COLOR_RESET}"
        exit 1
    fi

    echo -e "  ${COLOR_INFO}⬇ Installing mise...${COLOR_RESET}"
    curl https://mise.run | sh

    # Verify install
    if [ ! -f "$HOME/.local/bin/mise" ]; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: mise installation failed.${COLOR_RESET}"
        exit 1
    fi
}

activate_mise() {
    eval "$($HOME/.local/bin/mise activate --shims)"
    echo -e "  ${COLOR_SUCCESS}✔ mise activated.${COLOR_RESET}"
}

ensure_mise_package() {
    local PACKAGE=$1
    local MISE_DIR="$HOME/.local/share/mise/installs/$PACKAGE"

    if [ -d "$MISE_DIR" ]; then
        echo -e "  ${COLOR_SUCCESS}✔ $PACKAGE is already installed via mise.${COLOR_RESET}"
        return
    fi

    echo -e "  ${COLOR_WARN}⚠ ${PACKAGE} is not installed via mise.${COLOR_RESET}"
    if ! confirm "Do you want to install $PACKAGE using mise?"; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: $PACKAGE is required but not installed.${COLOR_RESET}"
        exit 1
    fi

    echo -e "  ${COLOR_INFO}⬇ Installing $PACKAGE via mise...${COLOR_RESET}"
    mise use --global "$PACKAGE"

    if [ ! -d "$MISE_DIR" ]; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: Failed to install $PACKAGE via mise.${COLOR_RESET}"
        exit 1
    fi

    echo -e "  ${COLOR_SUCCESS}✔ $PACKAGE installed successfully via mise.${COLOR_RESET}"
}

install_ansible_galaxy_collection() {
    if ansible-galaxy collection list | grep -q 'community.general'; then
        echo -e "  ${COLOR_SUCCESS}✔ community.general collection is already installed.${COLOR_RESET}"
        return
    fi

    echo -e "  ${COLOR_INFO}⬇ Installing community.general collection...${COLOR_RESET}"
    ansible-galaxy collection install community.general
}

run_ansible() {
    if ! confirm "Do you wish to execute the playbook?"; then
        echo -e "  ${COLOR_WARN}⚠ Skipping ansible-pull execution.${COLOR_RESET}"
        exit 1
    fi

    # Ask if the user wants to run it with sudo privileges
    echo -e "\n  💬 The playbook installs many tools at the user level.\n\
     Some require sudo for system-wide installation.\n\
     Running without sudo expects those packages pre-installed.\n"

    if [ "$NO_CONFIRM" = true ] && [ -z "$PRIVILEGED_MODE" ]; then
        echo -e "  ${COLOR_ERROR}✖ ERROR: --no-confirm requires either --privileged or --unprivileged flag.${COLOR_RESET}"
        exit 1
    fi

    if [ -z "$PRIVILEGED_MODE" ]; then
        if confirm "Do you want to run ansible-pull with sudo privileges?"; then
            PRIVILEGED_MODE=true
        else
            PRIVILEGED_MODE=false
        fi
    fi

    if [ "$PRIVILEGED_MODE" = true ]; then
        echo -e "  ${COLOR_INFO}⬆ Running ansible-pull with sudo privileges...${COLOR_RESET}"
        ansible-pull -U https://github.com/ll-nick/ansible-config.git --tags all,privileged -K
    else
        echo -e "  ${COLOR_INFO}⬇ Running ansible-pull without sudo privileges...${COLOR_RESET}"
        ansible-pull -U https://github.com/ll-nick/ansible-config.git
    fi

    echo -e "  ${COLOR_SUCCESS}✔ ansible-pull execution completed.${COLOR_RESET}"
}

main() {
    # Parse options
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -y | --no-confirm)
                NO_CONFIRM=true
                shift
                ;;
            --privileged)
                PRIVILEGED_MODE=true
                shift
                ;;
            --unprivileged)
                PRIVILEGED_MODE=false
                shift
                ;;
            -h | --help)
                print_help
                exit 0
                ;;
            *)
                echo -e "${COLOR_ERROR}✖ Unknown option: $1${COLOR_RESET}"
                print_help
                exit 1
                ;;
        esac
    done

    # Ensure local binary directory is on PATH
    export PATH="$HOME/.local/bin:$PATH"

    print_header "🔍 Detecting Linux Distribution"
    detect_distro

    print_header "📦 Checking system packages"
    ensure_system_package "curl"
    ensure_system_package "git"

    print_header "🔧 Checking mise installation"
    ensure_mise
    activate_mise

    print_header "🧰 Checking mise packages"
    MISE_PYTHON_COMPILE=false ensure_mise_package "python"
    ensure_mise_package "pipx"
    ensure_mise_package "ansible"
    install_ansible_galaxy_collection

    print_header "🚀 Running ansible-pull"
    run_ansible

    echo -e "\n${COLOR_SUCCESS}✔ Deployment completed successfully!${COLOR_RESET}\n"
}

main "$@"
