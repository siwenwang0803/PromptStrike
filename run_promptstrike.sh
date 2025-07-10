#!/bin/bash
# Helper script to run PromptStrike with proper environment

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [[ -d ".venv" ]]; then
    source .venv/bin/activate
fi

python -m promptstrike.cli "$@"
