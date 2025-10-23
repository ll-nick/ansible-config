mkdir ($nu.data-dir | path join "vendor/autoload")
mise exec carapace -- carapace _carapace nushell | save --force ($nu.data-dir | path join "vendor/autoload/carapace.nu")

