#!/bin/sh
# Bootstraps stk on a fresh machine.
# Only needs curl and git (installed on Debian and Ubuntu if missing);
# everything else is set up by stk itself.
#
# Can be piped into a shell: curl <url> | sh

set -eu

REPOSITORY_URL="https://github.com/ll-nick/stk.git"
CHECKOUT_DIRECTORY="$HOME/.config/stk"
MISE_EXECUTABLE="$HOME/.local/bin/mise"

NO_CONFIRM=false
ENABLED_NAMES=""
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
  --enable <name>       Also enable this on the machine, e.g. sudo. Repeatable.
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

ensure_mise() {
    if [ -x "$MISE_EXECUTABLE" ]; then
        printf "  ${COLOR_SUCCESS}✔ mise is already installed.${COLOR_RESET}\n"
        return
    fi

    printf "  ${COLOR_WARN}⚠ mise is not installed.${COLOR_RESET}\n"
    confirm "Do you want to install mise?" || fail "mise is required but not installed."

    printf "  ${COLOR_INFO}⬇ Installing mise...${COLOR_RESET}\n"
    curl -fsSL https://mise.jdx.dev/install.sh | sh
    [ -x "$MISE_EXECUTABLE" ] || fail "mise installation failed."
}

ensure_uv() {
    printf "  ${COLOR_INFO}⬇ Installing uv through mise...${COLOR_RESET}\n"
    # From the home directory, as a mise config in the current directory could get in the way
    (cd "$HOME" && "$MISE_EXECUTABLE" install --quiet uv@latest)
    UV_EXECUTABLE="$(cd "$HOME" && "$MISE_EXECUTABLE" --quiet which --tool uv@latest uv)" \
        || fail "uv installation failed."
}

normalized_repository_url() {
    printf '%s' "$1" | sed -e 's#^git@github.com:#https://github.com/#' -e 's#\.git$##'
}

fail_unless_checkout_of_this_repository() {
    if [ -d "$CHECKOUT_DIRECTORY/.git" ]; then
        origin="$(git -C "$CHECKOUT_DIRECTORY" remote get-url origin 2> /dev/null || true)"
        if [ "$(normalized_repository_url "$origin")" = "$(normalized_repository_url "$REPOSITORY_URL")" ]; then
            return
        fi
    fi
    fail "$CHECKOUT_DIRECTORY exists but is not a checkout of $REPOSITORY_URL. Please move or remove it and run this script again."
}

ensure_checkout() {
    if [ -e "$CHECKOUT_DIRECTORY" ] || [ -L "$CHECKOUT_DIRECTORY" ]; then
        fail_unless_checkout_of_this_repository
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

run_stk_in_checkout() {
    (
        cd "$CHECKOUT_DIRECTORY"
        # When piped into a shell, stdin is the script and must not be read by prompts
        if [ -t 0 ]; then
            "$UV_EXECUTABLE" run --quiet --no-dev stk "$@"
        elif (: < /dev/tty) 2> /dev/null; then
            "$UV_EXECUTABLE" run --quiet --no-dev stk "$@" < /dev/tty
        else
            "$UV_EXECUTABLE" run --quiet --no-dev stk "$@" < /dev/null
        fi
    )
}

run_stk() {
    confirm "Do you wish to apply the configuration?" || fail "Nothing applied."

    case " $ENABLED_NAMES " in
        *" sudo "*) ;;
        *)
            printf "\n  💬 Most tools are installed at the user level.\n\
     A few system packages require sudo.\n\
     Without it, those packages are expected to be installed already.\n"
            if [ "$NO_CONFIRM" = false ] && confirm "May this machine use sudo?"; then
                ENABLED_NAMES="$ENABLED_NAMES sudo"
            fi
            ;;
    esac

    # shellcheck disable=SC2086 # The names are separated by spaces
    run_stk_in_checkout enable $ENABLED_NAMES

    set -- apply
    [ "$NO_CONFIRM" = true ] && set -- "$@" --yes
    run_stk_in_checkout "$@"
}

main() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            -y | --no-confirm)
                NO_CONFIRM=true
                shift
                ;;
            --enable)
                [ -n "${2:-}" ] || fail "--enable requires a name."
                ENABLED_NAMES="$ENABLED_NAMES $2"
                shift 2
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

    print_header "🔧 Checking mise and uv"
    ensure_mise
    ensure_uv

    print_header "📥 Fetching stk"
    ensure_checkout

    print_header "🚀 Applying stk"
    run_stk

    printf "\n${COLOR_SUCCESS}✔ Deployment completed successfully!${COLOR_RESET}\n"
}

main "$@"
