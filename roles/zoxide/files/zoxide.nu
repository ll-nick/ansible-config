mkdir ($nu.data-dir | path join "vendor/autoload")
mise exec zoxide -- zoxide init --cmd cd nushell | save -f ($nu.data-dir | path join "vendor/autoload/zoxide.nu")

