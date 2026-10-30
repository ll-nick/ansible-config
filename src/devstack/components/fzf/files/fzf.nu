$env.FZF_DEFAULT_OPTS = ([
  # General
  "--border=none"
  "--tabstop=4"

  # List section
  "--cycle"
  "--list-label=' Results '"
  "--list-border='rounded'"
  "--pointer=' '"
  "--marker=' '"
  "--gutter=' '"

  # Input section
  "--input-border='rounded'"
  "--info='inline-right'"

  # Preview section
  "--preview-label=' Preview '"
  "--preview-window='right,border-rounded,'" 

  # Footer section
  "--footer-border='rounded'"

  # Colors
  "--color=bg+:#313244,bg:#1E1E2E,spinner:#F5E0DC,hl:#F38BA8"
  "--color=fg:#CDD6F4,header:#F38BA8,info:#CBA6F7,pointer:#F5E0DC"
  "--color=marker:#B4BEFE,fg+:#CDD6F4,prompt:#CBA6F7,hl+:#F38BA8"
  "--color=selected-bg:#45475A"
  "--color=border:#89B4FA,label:#CDD6F4"

  # Keybindings
  "--bind 'ctrl-d:preview-half-page-down'"
  "--bind 'ctrl-u:preview-half-page-up'"

  "--bind 'ctrl-r:change-preview-window(80%|40%)'"
  "--bind 'ctrl-t:toggle-preview'"
] | str join " ")

$env.config.keybindings ++= [{
    name: history_fzf
    modifier: control
    keycode: char_r
    mode: [emacs , vi_normal, vi_insert]
    event: {
      send: executehostcommand
      cmd: "commandline edit --replace (
        open $nu.history-path | query db 'select distinct command_line from history group by command_line order by max(start_timestamp) desc'
            | get command_line
            | str join (char -i 0)
            | fzf
                --read0
                --scheme=history
                --query (commandline)
                --height=40%
                --input-label=' History Search '
            | decode utf-8
            | str trim
        )
    "
    }
  }
]

