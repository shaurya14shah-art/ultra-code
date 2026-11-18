#!/bin/bash
REQ_FILE="/Users/USER/AG/ultra-code/.ipc_request.txt"
echo "Listening for IDE IPC Requests..."
while true; do
  if [ -f "$REQ_FILE" ]; then
    echo "--- INCOMING IPC REQUEST ---"
    cat "$REQ_FILE"
    rm "$REQ_FILE"
    exit 0
  fi
  sleep 1
done
