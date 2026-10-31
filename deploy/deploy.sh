#!/bin/sh
# Bootstraps devstack on a fresh machine.
# Only needs curl and git (installed on Debian and Ubuntu if missing);
# everything else is set up by devstack itself.
#
# Can be piped into a shell: curl <url> | sh

set -eu

REPOSITORY_URL="https://github.com/ll-nick/devstack.git"
CHECKOUT_DIRECTORY="$HOME/.config/devstack"

NO_CONFIRM=false
PRIVILEGED=false
BRANCH=""

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
  -y, --no-confirm      Automatically answer yes to all prompts.
  --privileged          Also apply the parts that need root (requires sudo).
  --branch <name>       Check out this branch of the repository.
  --repository <url>    Clone from this repository instead of the default.
  -h, --help            Show this help message and exit.
EOF
}

print_header() {
    title="$1"
    char_count=$(printf '%s' "$title" | LC_ALL=C.UTF-8 wc -m)
    width=$((char_count + 3))
    top="╭$(printf '─%.0s' $(seq 1 "$width"))╮"
    bottom="╰$(printf '─%.0s' $(seq 1 "$width"))╯"

    printf "\n${COLOR_TITLE}%s${COLOR_RESET}\n" "$top"
    printf "${COLOR_TITLE}│${COLOR_RESET} %s ${COLOR_TITLE}│${COLOR_RESET}\n" "$title"
    printf "${COLOR_TITLE}%s${COLOR_RESET}\n" "$bottom"
}

fail() {
    printf "  ${COLOR_ERROR}✖ %s${COLOR_RESET}\n" "$1"
    exit 1
}

confirm() {
    if [ "$NO_CONFIRM" = true ]; then
        return 0
    fi

    printf "  ${COLOR_INFO}➤ %s${COLOR_RESET} [y/N] " "$1"
    # Reading from stderr allows to execute the script by piping it to sh
    # See https://stackoverflow.com/a/54396662
    read -r response <&2
    case "$response" in
        [yY][eE][sS] | [yY]) return 0 ;;
        *) return 1 ;;
    esac
}

is_debian_based() {
    [ -f /etc/os-release ] && grep -qiE '^ID(_LIKE)?=.*(debian|ubuntu)' /etc/os-release
}

ensure_system_package() {
    package="$1"

    if command -v "$package" > /dev/null 2>&1; then
        printf "  ${COLOR_SUCCESS}✔ %s is already installed.${COLOR_RESET}\n" "$package"
        return
    fi

    printf "  ${COLOR_WARN}⚠ %s is not installed.${COLOR_RESET}\n" "$package"
    is_debian_based || fail "Cannot install $package on this distribution, please install it manually."
    confirm "Do you want to install $package? This requires sudo." \
        || fail "$package is required but not installed."

    sudo apt-get update
    sudo apt-get install -y "$package"
    command -v "$package" > /dev/null 2>&1 || fail "Failed to install $package."
    printf "  ${COLOR_SUCCESS}✔ %s installed successfully.${COLOR_RESET}\n" "$package"
}

ensure_uv() {
    if command -v uv > /dev/null 2>&1; then
        printf "  ${COLOR_SUCCESS}✔ uv is already installed.${COLOR_RESET}\n"
        return
    fi

    printf "  ${COLOR_WARN}⚠ uv is not installed.${COLOR_RESET}\n"
    confirm "Do you want to install uv?" || fail "uv is required but not installed."

    printf "  ${COLOR_INFO}⬇ Installing uv...${COLOR_RESET}\n"
    # The shell configuration is managed by devstack, so the installer must not touch it
    curl -LsSf https://astral.sh/uv/install.sh | UV_NO_MODIFY_PATH=1 sh
    command -v uv > /dev/null 2>&1 || fail "uv installation failed."
}

ensure_checkout() {
    if [ -d "$CHECKOUT_DIRECTORY/.git" ]; then
        printf "  ${COLOR_INFO}⬇ Updating %s...${COLOR_RESET}\n" "$CHECKOUT_DIRECTORY"
        git -C "$CHECKOUT_DIRECTORY" fetch origin
        if [ -n "$BRANCH" ]; then
            git -C "$CHECKOUT_DIRECTORY" checkout "$BRANCH"
        fi
        git -C "$CHECKOUT_DIRECTORY" pull --ff-only
    else
        printf "  ${COLOR_INFO}⬇ Cloning into %s...${COLOR_RESET}\n" "$CHECKOUT_DIRECTORY"
        mkdir -p "$(dirname "$CHECKOUT_DIRECTORY")"
        if [ -n "$BRANCH" ]; then
            git clone --branch "$BRANCH" "$REPOSITORY_URL" "$CHECKOUT_DIRECTORY"
        else
            git clone "$REPOSITORY_URL" "$CHECKOUT_DIRECTORY"
        fi
    fi
}

run_devstack() {
    confirm "Do you wish to apply the configuration?" || fail "Nothing applied."

    printf "\n  💬 Most tools are installed at the user level.\n\
     A few system packages require sudo.\n\
     Without it, those packages are expected to be installed already.\n"

    if [ "$NO_CONFIRM" = false ] && [ "$PRIVILEGED" = false ]; then
        if confirm "Do you want to also apply the privileged parts (requires sudo)?"; then
            PRIVILEGED=true
        fi
    fi

    set -- apply
    [ "$NO_CONFIRM" = true ] && set -- "$@" --yes
    [ "$PRIVILEGED" = true ] && set -- "$@" --privileged

    cd "$CHECKOUT_DIRECTORY"
    # When piped into a shell, stdin is the script and must not be read by prompts
    if [ -t 0 ]; then
        uv run --quiet --no-dev stk "$@"
    elif (: < /dev/tty) 2> /dev/null; then
        uv run --quiet --no-dev stk "$@" < /dev/tty
    else
        uv run --quiet --no-dev stk "$@" < /dev/null
    fi
}

main() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -y | --no-confirm)
                NO_CONFIRM=true
                shift
                ;;
            --privileged)
                PRIVILEGED=true
                shift
                ;;
            --branch)
                [ -n "${2:-}" ] || fail "--branch requires a branch name."
                BRANCH="$2"
                shift 2
                ;;
            --repository)
                [ -n "${2:-}" ] || fail "--repository requires a URL."
                REPOSITORY_URL="$2"
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

    print_header "📦 Checking system packages"
    ensure_system_package curl
    ensure_system_package git

    print_header "🔧 Checking uv"
    ensure_uv

    print_header "📥 Fetching devstack"
    ensure_checkout

    print_header "🚀 Applying devstack"
    run_devstack

    printf "\n${COLOR_SUCCESS}✔ Deployment completed successfully!${COLOR_RESET}\n"
}

main "$@"
