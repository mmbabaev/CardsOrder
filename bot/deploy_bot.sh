#!/bin/bash
# Release deploy — delegates to unified deploy script with --release flag
exec "$(dirname "$0")/deploy_bot_debug.sh" --release "$@"
