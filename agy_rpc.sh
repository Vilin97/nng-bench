#!/bin/sh
# POST a JSON request to the running Antigravity language server (Connect protocol). usage: agy_rpc.sh <Method> [json]
pid=$(ps eww -A | grep "ANTIGRAVITY_LS_ADDRESS=" | grep -v grep | head -1 | awk '{print $1}')
envs=$(ps eww -p "$pid" | tr ' ' '\n')
addr=$(echo "$envs" | grep "^ANTIGRAVITY_LS_ADDRESS=" | cut -d= -f2-)
tok=$(echo "$envs" | grep "^ANTIGRAVITY_CSRF_TOKEN=" | cut -d= -f2-)
body=${2:-"{}"}
curl -s -m 20 -X POST "http://$addr/exa.language_server_pb.LanguageServerService/$1" \
  -H "Content-Type: application/json" -H "x-codeium-csrf-token: $tok" -d "$body"
