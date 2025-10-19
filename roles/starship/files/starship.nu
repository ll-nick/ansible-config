mkdir ($nu.data-dir | path join "vendor/autoload")
mise exec starship -- starship init nu | save -f ($nu.data-dir | path join "vendor/autoload/starship.nu")

$env.STARSHIP_CONFIG = ($env.HOME | path join ".config/starship/starship.toml")

