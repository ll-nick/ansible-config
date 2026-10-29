# Only add this alias in interactive shells to prevent breaking scripts relying on `cat`
if [[ $- == *i* ]]; then
    alias cat="bat"
fi
