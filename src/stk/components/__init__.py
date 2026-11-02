from stk.component import Component
from stk.components.bash.bash import apply_bash
from stk.components.bat.bat import apply_bat
from stk.components.claude.claude import apply_claude
from stk.components.eza.eza import apply_eza
from stk.components.fd.fd import apply_fd
from stk.components.fzf.fzf import apply_fzf
from stk.components.git.git import apply_git
from stk.components.gnome.gnome import apply_gnome
from stk.components.inkflow.inkflow import apply_inkflow
from stk.components.joy.joy import apply_joy
from stk.components.kitty.kitty import apply_kitty
from stk.components.lazygit.lazygit import apply_lazygit
from stk.components.leadr.leadr import apply_leadr
from stk.components.locale.locale import apply_locale, pending_locale_work
from stk.components.mise.mise import MISE_UPDATE, apply_mise
from stk.components.neovim.neovim import NEOVIM_UPDATE, apply_neovim
from stk.components.nerdfont.nerdfont import apply_nerdfont
from stk.components.nodejs.nodejs import apply_nodejs
from stk.components.nushell.nushell import apply_nushell
from stk.components.ripgrep.ripgrep import apply_ripgrep
from stk.components.starship.starship import apply_starship
from stk.components.stk.stk import apply_stk
from stk.components.tmux.tmux import TMUX_UPDATE, apply_tmux
from stk.components.uv.uv import apply_uv
from stk.components.zoxide.zoxide import apply_zoxide
from stk.machine import (
    HAS_DISPLAY,
    HAS_INKSCAPE,
    JOY_HOSTNAME,
    host_is,
    runs_distribution,
)
from stk.run_settings import PRIVILEGED

COMPONENTS: tuple[Component, ...] = (
    Component("mise", apply_mise, update=MISE_UPDATE),
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
        pending_sudo_work=pending_locale_work,
    ),
    Component("ripgrep", apply_ripgrep, depends_on=("mise",)),
    Component("uv", apply_uv, depends_on=("mise",)),
    Component("eza", apply_eza, depends_on=("mise", "bash", "nushell")),
    Component("fzf", apply_fzf, depends_on=("mise", "bash", "nushell")),
    Component("lazygit", apply_lazygit, depends_on=("mise", "bash", "nushell")),
    Component("zoxide", apply_zoxide, depends_on=("mise", "bash", "nushell")),
    Component("starship", apply_starship, depends_on=("mise", "bash", "nushell")),
    Component(
        "nodejs",
        apply_nodejs,
        depends_on=("mise",),
        system_packages=("libatomic1",),
    ),
    Component(
        "neovim",
        apply_neovim,
        depends_on=("mise", "bash", "nushell", "fd", "ripgrep", "nodejs"),
        system_packages=("gcc", "make", "unzip"),
        update=NEOVIM_UPDATE,
    ),
    Component("leadr", apply_leadr, depends_on=("mise", "bash", "nushell")),
    Component("claude", apply_claude, depends_on=("mise", "bash", "nushell")),
    Component(
        "tmux",
        apply_tmux,
        depends_on=("mise", "bash", "nushell"),
        system_packages=("xclip",),
        update=TMUX_UPDATE,
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
        system_packages=("fontconfig", "fonts-noto", "unzip"),
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
        system_packages=("unzip",),
    ),
    Component("stk", apply_stk),
)
