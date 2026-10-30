from devstack.component import Component
from devstack.components.bash.bash import apply_bash
from devstack.components.bat.bat import apply_bat
from devstack.components.claude.claude import apply_claude
from devstack.components.eza.eza import apply_eza
from devstack.components.fd.fd import apply_fd
from devstack.components.fzf.fzf import apply_fzf
from devstack.components.git.git import apply_git
from devstack.components.gnome.gnome import apply_gnome
from devstack.components.inkflow.inkflow import apply_inkflow
from devstack.components.joy.joy import apply_joy
from devstack.components.kitty.kitty import apply_kitty
from devstack.components.lazygit.lazygit import apply_lazygit
from devstack.components.leadr.leadr import apply_leadr
from devstack.components.locale.locale import apply_locale
from devstack.components.mise.mise import apply_mise
from devstack.components.neovim.neovim import apply_neovim
from devstack.components.nerdfont.nerdfont import apply_nerdfont
from devstack.components.nodejs.nodejs import apply_nodejs
from devstack.components.nushell.nushell import apply_nushell
from devstack.components.ripgrep.ripgrep import apply_ripgrep
from devstack.components.starship.starship import apply_starship
from devstack.components.tmux.tmux import apply_tmux
from devstack.components.uv.uv import apply_uv
from devstack.components.zoxide.zoxide import apply_zoxide
from devstack.machine import (
    HAS_DISPLAY,
    HAS_INKSCAPE,
    JOY_HOSTNAME,
    host_is,
    runs_distribution,
)
from devstack.run_settings import PRIVILEGED

COMPONENTS: tuple[Component, ...] = (
    Component("mise", apply_mise),
    Component("bash", apply_bash),
    Component(
        "git",
        apply_git,
        depends_on=("mise",),
        system_packages=("git",),
    ),
    Component("nushell", apply_nushell, depends_on=("mise",)),
    Component("fd", apply_fd, depends_on=("mise",)),
    Component("bat", apply_bat, depends_on=("mise", "bash", "nushell")),
    Component(
        "locale",
        apply_locale,
        requires=(PRIVILEGED, runs_distribution("debian")),
        system_packages=("locales",),
    ),
    Component("ripgrep", apply_ripgrep, depends_on=("mise",)),
    Component("uv", apply_uv, depends_on=("mise",)),
    Component("eza", apply_eza, depends_on=("mise", "bash", "nushell")),
    Component("fzf", apply_fzf, depends_on=("mise", "bash", "nushell")),
    Component("lazygit", apply_lazygit, depends_on=("mise", "bash", "nushell")),
    Component("zoxide", apply_zoxide, depends_on=("mise", "bash", "nushell")),
    Component("starship", apply_starship, depends_on=("mise", "bash", "nushell")),
    Component("nodejs", apply_nodejs, depends_on=("mise",)),
    Component(
        "neovim",
        apply_neovim,
        depends_on=("mise", "bash", "nushell", "ripgrep", "nodejs"),
        system_packages=("gcc", "make", "unzip"),
    ),
    Component("leadr", apply_leadr, depends_on=("mise", "bash", "nushell")),
    Component("claude", apply_claude, depends_on=("mise", "bash", "nushell")),
    Component(
        "tmux",
        apply_tmux,
        depends_on=("mise", "bash", "nushell"),
        system_packages=("xclip",),
    ),
    Component(
        "inkflow",
        apply_inkflow,
        depends_on=("mise", "bash", "nushell", "neovim"),
        requires=(HAS_DISPLAY, HAS_INKSCAPE),
    ),
    Component(
        "joy",
        apply_joy,
        depends_on=("bash", "git"),
        requires=(host_is(JOY_HOSTNAME),),
    ),
    Component(
        "nerdfont",
        apply_nerdfont,
        requires=(HAS_DISPLAY,),
        system_packages=("fontconfig", "fonts-noto"),
    ),
    Component(
        "kitty",
        apply_kitty,
        depends_on=("mise",),
        requires=(HAS_DISPLAY,),
    ),
    Component(
        "gnome",
        apply_gnome,
        depends_on=("mise",),
        requires=(HAS_DISPLAY,),
    ),
)
