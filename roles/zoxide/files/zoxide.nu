mkdir ($nu.data-dir | path join "vendor/autoload")
mise exec zoxide -- zoxide init nushell | save -f ($nu.data-dir | path join "vendor/autoload/zoxide.nu")

