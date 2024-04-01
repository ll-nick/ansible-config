source /opt/mrtsoftware/setup.bash
source /opt/mrtros/setup.bash

alias codews='code $(mrt catkin locate)'
alias kitvpn='sudo openvpn --config ~/Documents/kit.ovpn'
alias mensa='kit-mensa-cli'
alias rf='rosbag_fancy'

function mrtf {
  local cmd
  cmd=$(mrt --list | fzf | sed 's/\ \ \ .*//') &&
    bind '"\e[0n": "'"$cmd"'"' &&
    printf '\e[5n'
}

