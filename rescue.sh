#!/bin/bash
REQ="/Users/USER/AG/ultra-code/.ipc_request.txt"
RES="/Users/USER/AG/ultra-code/.ipc_response.txt"
while true; do
  if [ -f "$REQ" ]; then
    CMD=$(cat "$REQ")
    rm "$REQ"
    echo "Rescued stuck command: $CMD. **CRITICAL**: You are running the OLD app backend! You MUST completely quit the app (Cmd+Q) and start it again so the new features work properly!" > "$RES"
  fi
  sleep 1
done
