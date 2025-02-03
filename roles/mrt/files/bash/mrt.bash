source /opt/mrtsoftware/setup.bash
source /opt/mrtros/setup.bash

alias kitvpn='sudo openvpn --config ~/Documents/kit.ovpn'
alias mensa='kit-mensa-cli'
alias rf='rosbag_fancy'
alias windows='vboxmanage startvm windows10'

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

if  [ -f ~/.lazygit_ws_tools/lazygit_ws_tools.sh ]; then
    source ~/.lazygit_ws_tools/lazygit_ws_tools.sh
fi

