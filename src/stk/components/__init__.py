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
from stk.components.locale.locale import GENERATE_LOCALES
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
from stk.engine.component import Component
from stk.machine import (
    HAS_DISPLAY,
    HAS_INKSCAPE,
    JOY_HOSTNAME,
    host_is,
    runs_distribution,
)

MISE = Component("mise", apply_mise, update=MISE_UPDATE)
BASH = Component("bash", apply_bash)
GIT = Component(
    "git",
    apply_git,
    depends_on=(MISE,),
    system_packages=("git",),
)
NUSHELL = Component("nushell", apply_nushell, depends_on=(MISE,))
FD = Component("fd", apply_fd, depends_on=(MISE,))
BAT = Component("bat", apply_bat, depends_on=(MISE, BASH, NUSHELL))
LOCALE = Component(
    "locale",
    requires=(runs_distribution("debian"),),
    system_packages=("locales",),
    privileged_tasks=(GENERATE_LOCALES,),
)
RIPGREP = Component("ripgrep", apply_ripgrep, depends_on=(MISE,))
UV = Component("uv", apply_uv, depends_on=(MISE,))
EZA = Component("eza", apply_eza, depends_on=(MISE, BASH, NUSHELL))
FZF = Component("fzf", apply_fzf, depends_on=(MISE, BASH, NUSHELL))
LAZYGIT = Component("lazygit", apply_lazygit, depends_on=(MISE, BASH, NUSHELL))
ZOXIDE = Component("zoxide", apply_zoxide, depends_on=(MISE, BASH, NUSHELL))
STARSHIP = Component("starship", apply_starship, depends_on=(MISE, BASH, NUSHELL))
NODEJS = Component(
    "nodejs",
    apply_nodejs,
    depends_on=(MISE,),
    system_packages=("libatomic1",),
)
NEOVIM = Component(
    "neovim",
    apply_neovim,
    depends_on=(MISE, BASH, NUSHELL, FD, RIPGREP, NODEJS),
    system_packages=("gcc", "make", "unzip"),
    update=NEOVIM_UPDATE,
)
LEADR = Component("leadr", apply_leadr, depends_on=(MISE, BASH, NUSHELL))
CLAUDE = Component("claude", apply_claude, depends_on=(MISE, BASH, NUSHELL))
TMUX = Component(
    "tmux",
    apply_tmux,
    depends_on=(MISE, BASH, NUSHELL),
    system_packages=("xclip",),
    update=TMUX_UPDATE,
)
INKFLOW = Component(
    "inkflow",
    apply_inkflow,
    depends_on=(MISE, BASH, NUSHELL, NEOVIM),
    requires=(HAS_DISPLAY, HAS_INKSCAPE),
)
JOY = Component(
    "joy",
    apply_joy,
    depends_on=(BASH, GIT),
    requires=(host_is(JOY_HOSTNAME),),
)
NERDFONT = Component(
    "nerdfont",
    apply_nerdfont,
    requires=(HAS_DISPLAY,),
    system_packages=("fontconfig", "fonts-noto", "unzip"),
)
KITTY = Component(
    "kitty",
    apply_kitty,
    depends_on=(MISE,),
    requires=(HAS_DISPLAY,),
)
GNOME = Component(
    "gnome",
    apply_gnome,
    depends_on=(MISE,),
    requires=(HAS_DISPLAY,),
    system_packages=("unzip",),
)
STK = Component("stk", apply_stk)

COMPONENTS: tuple[Component, ...] = (
    MISE,
    BASH,
    GIT,
    NUSHELL,
    FD,
    BAT,
    LOCALE,
    RIPGREP,
    UV,
    EZA,
    FZF,
    LAZYGIT,
    ZOXIDE,
    STARSHIP,
    NODEJS,
    NEOVIM,
    LEADR,
    CLAUDE,
    TMUX,
    INKFLOW,
    JOY,
    NERDFONT,
    KITTY,
    GNOME,
    STK,
)
