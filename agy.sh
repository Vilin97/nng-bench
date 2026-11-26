#!/bin/sh
# Run Antigravity's agentapi with the address/token of the running Antigravity app (read from one of its sidecar processes).
pid=$(ps eww -A | grep "ANTIGRAVITY_LS_ADDRESS=" | grep -v grep | head -1 | awk '{print $1}')
envs=$(ps eww -p "$pid" | tr ' ' '\n' | grep -E "^ANTIGRAVITY_(LS_ADDRESS|CSRF_TOKEN|LS_VERSION)=")
exec env $envs "$HOME/.gemini/antigravity/bin/agentapi" "$@"
