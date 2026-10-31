#!/usr/bin/env bash
# Fetch Claude Code usage limits from Anthropic API and write JSON to stdout

CREDS_FILE="${HOME}/.claude/.credentials.json"

[ -f "$CREDS_FILE" ] || exit 1

access_token=$(jq -r '.claudeAiOauth.accessToken // empty' "$CREDS_FILE")

[ -n "$access_token" ] || exit 1

# Keep the User-Agent's version in sync with the installed CLI instead of pinning a snapshot
claude_version=$(claude --version 2>/dev/null | cut -d' ' -f1)

curl -sf \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "User-Agent: claude-code/${claude_version:-0.0.0}" \
    -H "Authorization: Bearer ${access_token}" \
    -H "anthropic-beta: oauth-2025-04-20" \
    "https://api.anthropic.com/api/oauth/usage"
