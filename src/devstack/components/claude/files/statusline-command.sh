#!/usr/bin/env bash
# Claude Code status line — Catppuccin Mocha style, mirroring Starship prompt

input=$(cat)

# Catppuccin Mocha palette (ANSI 24-bit)
peach="\033[38;2;250;179;135m"
blue="\033[38;2;137;180;250m"
green="\033[38;2;166;227;161m"
red="\033[38;2;243;139;168m"
overlay1="\033[38;2;127;132;156m"
reset="\033[0m"

# Extract fields from JSON
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')

# Shorten cwd: replace $HOME with ~, keep last 3 components
short_cwd="${cwd/#$HOME/\~}"
component_count=$(echo "$short_cwd" | tr -cd '/' | wc -c)
if [ "$component_count" -gt 3 ]; then
    short_cwd="…/$(echo "$short_cwd" | rev | cut -d'/' -f1-3 | rev)"
fi

# Git branch
git_branch=""
if git -C "$cwd" rev-parse --is-inside-work-tree --quiet 2>/dev/null; then
    branch=$(git -C "$cwd" symbolic-ref --short HEAD 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
    [ -n "$branch" ] && git_branch=" ${blue} ${branch}${reset}"
fi

# Model part
model_part=""
[ -n "$model" ] && model_part=" ${overlay1}|${reset} ${overlay1}${model}${reset}"

# Usage limits (5h / 7d) — cached with background refresh
CACHE_FILE="${HOME}/.claude/cache/usage-limits.json"
CACHE_TTL=300  # 5 minutes

usage_part=""
needs_refresh=0

if [ -f "$CACHE_FILE" ]; then
    cache_age=$(( $(date +%s) - $(stat -c %Y "$CACHE_FILE") ))
    [ "$cache_age" -gt "$CACHE_TTL" ] && needs_refresh=1
    five_h=$(jq -r '.five_hour.utilization // empty' "$CACHE_FILE" 2>/dev/null)
    seven_d=$(jq -r '.seven_day.utilization // empty' "$CACHE_FILE" 2>/dev/null)
else
    needs_refresh=1
fi

[ "$needs_refresh" -eq 1 ] && (bash "${HOME}/.claude/fetch-usage-limits.sh" > "${CACHE_FILE}.tmp" 2>/dev/null && mv "${CACHE_FILE}.tmp" "$CACHE_FILE") &

_usage_color() {
    local val=$1
    local val_int=${val%.*}
    if [ "$val_int" -ge 80 ]; then echo -n "$red"
    elif [ "$val_int" -ge 50 ]; then echo -n "$peach"
    else echo -n "$green"
    fi
}

if [ -n "$five_h" ] && [ -n "$seven_d" ]; then
    fh_int=${five_h%.*}
    sd_int=${seven_d%.*}
    fh_color=$(_usage_color "$five_h")
    sd_color=$(_usage_color "$seven_d")
    usage_part=" ${overlay1}|${reset} ${fh_color}5h:${fh_int}%%${reset} ${overlay1}/${reset} ${sd_color}7d:${sd_int}%%${reset}"
fi

# Context window
ctx_part=""
if [ -n "$used" ]; then
    used_int=${used%.*}
    if [ "$used_int" -ge 80 ]; then ctx_color="$red"
    elif [ "$used_int" -ge 50 ]; then ctx_color="$peach"
    else ctx_color="$green"
    fi
    ctx_part=" ${overlay1}|${reset} ${ctx_color}ctx:${used_int}%%${reset}"
fi

# Vim mode
vim_part=""
if [ -n "$vim_mode" ]; then
    [ "$vim_mode" = "NORMAL" ] && vim_part=" ${blue}[N]${reset}" || vim_part=" ${green}[I]${reset}"
fi

printf "${peach}${short_cwd}${reset}${git_branch}${model_part}${usage_part}${ctx_part}${vim_part}"
