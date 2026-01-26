#!/usr/bin/env bash

set -e

NO_CONFIRM=false
PLAYBOOK_PATH=""
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
    local width=$((${#title} + 3)) # For some reason this works with piping this script to bash but not with sh
    local top="╭$(printf '─%.0s' $(seq 1 $width))╮"
    local bottom="╰$(printf '─%.0s' $(seq 1 $width))╯"

    printf "\n${COLOR_TITLE}%s${COLOR_RESET}\n" "$top"
    printf "${COLOR_TITLE}│${COLOR_RESET} %s ${COLOR_TITLE}│${COLOR_RESET}\n" "$title"
    printf "${COLOR_TITLE}%s${COLOR_RESET}\n" "$bottom"
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
        printf "  ${COLOR_SUCCESS}✔ Detected distribution: %s${COLOR_RESET}\n" "$DISTRO"
    else
        printf "  ${COLOR_ERROR}✖ Cannot determine the distribution. Exiting.${COLOR_RESET}\n"
        exit 1
    fi
}

ensure_system_package() {
    PACKAGE=$1

    if command -v $PACKAGE > /dev/null 2>&1; then
        printf "  ${COLOR_SUCCESS}✔ %s is already installed.${COLOR_RESET}\n" "$PACKAGE"
        return
    fi

    printf "  ${COLOR_WARN}⚠ %s is not installed.${COLOR_RESET}\n" "$PACKAGE"
    if ! confirm "Do you want to install $PACKAGE? This requires sudo."; then
        printf "  ${COLOR_ERROR}✖ ERROR: %s is required but not installed.${COLOR_RESET}\n" "$PACKAGE"
        exit 1
    fi

    printf "  ${COLOR_INFO}⬇ Installing %s...${COLOR_RESET}\n" "$PACKAGE"
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        sudo apt-get update
        sudo apt-get install -y $PACKAGE
    elif [ "$DISTRO" = "arch" ]; then
        sudo pacman -Syu --noconfirm $PACKAGE
    else
        printf "  ${COLOR_ERROR}✖ Unsupported distribution: %s${COLOR_RESET}\n" "$DISTRO"
        exit 1
    fi

    if ! command -v "$PACKAGE" > /dev/null 2>&1; then
        printf "  ${COLOR_ERROR}✖ ERROR: Failed to install %s.${COLOR_RESET}\n" "$PACKAGE"
        exit 1
    fi

    printf "  ${COLOR_SUCCESS}✔ %s installed successfully.${COLOR_RESET}\n" "$PACKAGE"
}

ensure_mise() {
    if command -v mise > /dev/null 2>&1; then
        printf "  ${COLOR_SUCCESS}✔ mise is already installed.${COLOR_RESET}\n"
        return
    fi

    printf "  ${COLOR_WARN}⚠ mise is not installed.${COLOR_RESET}\n"
    if ! confirm "Do you want to install mise?"; then
        printf "  ${COLOR_ERROR}✖ ERROR: mise is required but not installed.${COLOR_RESET}\n"
        exit 1
    fi

    printf "  ${COLOR_INFO}⬇ Installing mise...${COLOR_RESET}\n"
    curl https://mise.run | sh

    if [ ! -f "$HOME/.local/bin/mise" ]; then
        printf "  ${COLOR_ERROR}✖ ERROR: mise installation failed.${COLOR_RESET}\n"
        exit 1
    fi
}

activate_mise() {
    eval "$($HOME/.local/bin/mise activate --shims)"
    printf "  ${COLOR_SUCCESS}✔ mise activated.${COLOR_RESET}\n"
}

ensure_mise_package() {
    local PACKAGE=$1
    local MISE_DIR="$HOME/.local/share/mise/installs/$PACKAGE"

    if [ -d "$MISE_DIR" ]; then
        printf "  ${COLOR_SUCCESS}✔ %s is already installed via mise.${COLOR_RESET}\n" "$PACKAGE"
        return
    fi

    printf "  ${COLOR_WARN}⚠ %s is not installed via mise.${COLOR_RESET}\n" "$PACKAGE"
    if ! confirm "Do you want to install $PACKAGE using mise?"; then
        printf "  ${COLOR_ERROR}✖ ERROR: %s is required but not installed.${COLOR_RESET}\n" "$PACKAGE"
        exit 1
    fi

    printf "  ${COLOR_INFO}⬇ Installing %s via mise...${COLOR_RESET}\n" "$PACKAGE"
    mise use --global "$PACKAGE"

    if [ ! -d "$MISE_DIR" ]; then
        printf "  ${COLOR_ERROR}✖ ERROR: Failed to install %s via mise.${COLOR_RESET}\n" "$PACKAGE"
        exit 1
    fi

    printf "  ${COLOR_SUCCESS}✔ %s installed successfully via mise.${COLOR_RESET}\n" "$PACKAGE"
}

install_ansible_galaxy_collection() {
    if ansible-galaxy collection list | grep -q 'community.general'; then
        printf "  ${COLOR_SUCCESS}✔ community.general collection is already installed.${COLOR_RESET}\n"
        return
    fi

    printf "  ${COLOR_INFO}⬇ Installing community.general collection...${COLOR_RESET}\n"
    ansible-galaxy collection install community.general
}

validate_playbook_path() {
    if [ -z "$PLAYBOOK_PATH" ]; then
        return
    fi

    print_header "📂 Checking playbook path"
    if [ ! -e "$PLAYBOOK_PATH" ]; then
        printf "  ${COLOR_ERROR}✖ Playbook path does not exist: %s${COLOR_RESET}\n" "$PLAYBOOK_PATH"
        exit 1
    fi
    printf "  ${COLOR_SUCCESS}✔ Using local playbook: %s${COLOR_RESET}\n" "$PLAYBOOK_PATH"
}

run_ansible() {
    if ! confirm "Do you wish to execute the playbook?"; then
        printf "  ${COLOR_WARN}⚠ Skipping Ansible execution.${COLOR_RESET}\n"
        exit 1
    fi

    printf "\n  💬 The playbook installs many tools at the user level.\n\
     Some require sudo for system-wide installation.\n\
     Running without sudo expects those packages pre-installed.\n"

    if [ "$NO_CONFIRM" = true ] && [ -z "$PRIVILEGED_MODE" ]; then
        printf "  ${COLOR_ERROR}✖ ERROR: --no-confirm requires either --privileged or --unprivileged flag.${COLOR_RESET}\n"
        exit 1
    fi

    if [ -z "$PRIVILEGED_MODE" ]; then
        if confirm "Do you want to run Ansible with sudo privileges?"; then
            PRIVILEGED_MODE=true
        else
            PRIVILEGED_MODE=false
        fi
    fi

    PRIVILEGED_FLAGS=()
    if [ "$PRIVILEGED_MODE" = true ]; then
        printf "  ${COLOR_INFO}⬆ Running Ansible with sudo privileges...${COLOR_RESET}\n"
        PRIVILEGED_FLAGS+=(--tags all,privileged -K)
    else
        printf "  ${COLOR_INFO}⬇ Running Ansible without sudo privileges...${COLOR_RESET}\n"
    fi

    if [ -n "$PLAYBOOK_PATH" ]; then
        ansible-playbook "${PRIVILEGED_FLAGS[@]}" "$PLAYBOOK_PATH"
    else
        ansible-pull "${PRIVILEGED_FLAGS[@]}" -U https://github.com/ll-nick/ansible-config.git
    fi

    printf "  ${COLOR_SUCCESS}✔ Ansible execution completed.${COLOR_RESET}\n"
}

main() {
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
                if [ -z "$PLAYBOOK_PATH" ]; then
                    PLAYBOOK_PATH="$1"
                    shift
                else
                    printf "${COLOR_ERROR}✖ Unknown option or multiple paths provided: %s${COLOR_RESET}\n" "$1"
                    exit 1
                fi
                ;;
        esac
    done

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

    validate_playbook_path
    print_header "🚀 Running ansible-pull"
    run_ansible

    printf "\n${COLOR_SUCCESS}✔ Deployment completed successfully!${COLOR_RESET}\n"
}

main "$@"
