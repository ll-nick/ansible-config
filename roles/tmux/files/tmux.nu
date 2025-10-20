def tm [] {
    do { tmux attach } catch { tmux new -s main }
}

