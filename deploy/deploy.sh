#!/usr/bin/env bash

set -e

NO_CONFIRM=false
PRIVILEGED_MODE=""
PLAYBOOK_PATH=""

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
  -y, --no-confirm          Automatically answer yes to all prompts.
  --privileged              Run ansible with sudo privileges (non-interactive).
  --unprivileged            Run ansible without sudo privileges (non-interactive).
  --playbook-path <dir>     Run ansible-playbook from a local directory instead of ansible-pull.
  -h, --help                Show this help message and exit.
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

ensure_mise_packages() {
    local CONF_D="$HOME/.config/mise/conf.d"

    if [ -d "$HOME/.local/share/mise/installs/python" ] &&
        command -v ansible > /dev/null 2>&1; then
        printf "  ${COLOR_SUCCESS}✔ Required tools are already installed via mise.${COLOR_RESET}\n"
        return
    fi

    if ! confirm "Do you want to install required tools (python, pipx, ansible) using mise?"; then
        printf "  ${COLOR_ERROR}✖ ERROR: Required tools are not installed.${COLOR_RESET}\n"
        exit 1
    fi

    mkdir -p "$CONF_D"

    cat > "$CONF_D/ansible.toml" << 'EOF'
[tools]
python = { version = "latest", install_env = { MISE_PYTHON_COMPILE = "false" } }
pipx = "latest"
ansible = "latest"
EOF

    printf "  ${COLOR_INFO}⬇ Installing mise packages...${COLOR_RESET}\n"
    mise install
    printf "  ${COLOR_SUCCESS}✔ Required tools installed.${COLOR_RESET}\n"
}

install_ansible_galaxy_collection() {
    if ansible-galaxy collection list | grep -q 'community.general'; then
        printf "  ${COLOR_SUCCESS}✔ community.general collection is already installed.${COLOR_RESET}\n"
        return
    fi

    printf "  ${COLOR_INFO}⬇ Installing community.general collection...${COLOR_RESET}\n"
    ansible-galaxy collection install community.general
}

run_ansible() {
    if ! confirm "Do you wish to execute the playbook?"; then
        printf "  ${COLOR_WARN}⚠ Skipping ansible execution.${COLOR_RESET}\n"
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
        if confirm "Do you want to run ansible with sudo privileges?"; then
            PRIVILEGED_MODE=true
        else
            PRIVILEGED_MODE=false
        fi
    fi

    if [ -n "$PLAYBOOK_PATH" ]; then
        printf "  ${COLOR_INFO}📂 Running ansible-playbook from local path: %s${COLOR_RESET}\n" "$PLAYBOOK_PATH"
        cd "$PLAYBOOK_PATH"
        if [ "$PRIVILEGED_MODE" = true ]; then
            if [ -n "${ANSIBLE_BECOME_PASS+x}" ]; then
                ansible-playbook local.yml --tags all,privileged
            else
                ansible-playbook local.yml --tags all,privileged -K
            fi
        else
            ansible-playbook local.yml
        fi
    else
        if [ "$PRIVILEGED_MODE" = true ]; then
            printf "  ${COLOR_INFO}⬆ Running ansible-pull with sudo privileges...${COLOR_RESET}\n"
            ansible-pull -U https://github.com/ll-nick/ansible-config.git --tags all,privileged -K
        else
            printf "  ${COLOR_INFO}⬇ Running ansible-pull without sudo privileges...${COLOR_RESET}\n"
            ansible-pull -U https://github.com/ll-nick/ansible-config.git
        fi
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
            --playbook-path)
                if [ -z "$2" ]; then
                    printf "${COLOR_ERROR}✖ --playbook-path requires a directory argument.${COLOR_RESET}\n"
                    exit 1
                fi
                PLAYBOOK_PATH="$2"
                shift 2
                ;;
            -h | --help)
                print_help
                exit 0
                ;;
            *)
                printf "${COLOR_ERROR}✖ Unknown option: %s${COLOR_RESET}\n" "$1"
                print_help
                exit 1
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
    ensure_mise_packages
    install_ansible_galaxy_collection

    print_header "🚀 Running ansible"
    run_ansible

    printf "\n${COLOR_SUCCESS}✔ Deployment completed successfully!${COLOR_RESET}\n"
}

main "$@"
