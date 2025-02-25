source ~/.rossrc/rossrc.mrt.bash
source ~/.rossrc/cd_hook.bash

mrt() {
    unset -f mrt && rossrc && mrt "$@"
}
