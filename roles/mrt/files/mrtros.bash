alias rf='rosbag_fancy'

export ROSMON_DEBUGGER_TERMINAL="tmux new-window -n rosmon-debug"

function mrtf {
    local cmd
    cmd=$(mrt --list | fzf | sed 's/\ \ \ .*//') &&
        bind '"\e[0n": "'"$cmd"'"' &&
        printf '\e[5n'
}

if [ -f ~/.sqfs_tools/sqfs_tools.sh ]; then
    source ~/.sqfs_tools/sqfs_tools.sh
fi

source ~/.rossrc/rossrc.mrt.bash
source ~/.rossrc/cd_hook.bash
