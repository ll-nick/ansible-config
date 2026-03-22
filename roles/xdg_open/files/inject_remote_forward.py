#!/usr/bin/env python3
"""Inject RemoteForward into every Host block in ~/.ssh/config.

Usage: inject_remote_forward.py <port> <socket_path>

Idempotent: skips blocks that already have a RemoteForward on the given port.
Skips 'Host *' and 'Match' blocks.
"""
import os
import re
import sys

port = sys.argv[1]
socket_path = sys.argv[2]
forward_line = f"  RemoteForward 127.0.0.1:{port} {socket_path}\n"
marker = f"RemoteForward 127.0.0.1:{port}"

config_path = os.path.expanduser("~/.ssh/config")
if not os.path.exists(config_path):
    sys.exit(0)

with open(config_path) as f:
    lines = f.readlines()

result = []
changed = False
i = 0

while i < len(lines):
    line = lines[i]
    m = re.match(r'^Host\s+(.+)', line, re.IGNORECASE)
    if m and m.group(1).strip() != '*':
        # Collect the block (lines until next Host/Match keyword)
        block = []
        j = i + 1
        while j < len(lines) and not re.match(r'^(Host|Match)\s+', lines[j], re.IGNORECASE):
            block.append(lines[j])
            j += 1
        result.append(line)
        if not any(marker in bl for bl in block):
            result.append(forward_line)
            changed = True
        result.extend(block)
        i = j
    else:
        result.append(line)
        i += 1

if changed:
    with open(config_path, "w") as f:
        f.writelines(result)
    sys.exit(2)  # signal "changed" to Ansible
