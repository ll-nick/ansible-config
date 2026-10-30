alias vs = nvim --listen /tmp/nvim.sock
$env.INKFLOW_EDIT_CMD = "nvim --server /tmp/nvim.sock --remote {path}"
$env.INKFLOW_EDIT_CMD_SVG = "inkflow-edit-svg {path}"
