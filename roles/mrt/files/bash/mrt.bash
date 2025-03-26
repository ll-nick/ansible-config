alias kitvpn='sudo openvpn --config ~/Documents/kit.ovpn'
alias mensa='kit-mensa-cli'
alias mrt='distrobox enter mrt-box'
alias windows='vboxmanage startvm windows10'

function kssh {
    if klist -s; then
        echo "Kerberos ticket found."
    else
        echo "No Kerberos ticket found. Run kinit."
        kinit
    fi

    krenew -b -K 60 > /dev/null 2>&1
    ssh "$@"
}

if [ -f ~/.sqfs_tools/sqfs_tools.sh ]; then
    source ~/.sqfs_tools/sqfs_tools.sh
fi
