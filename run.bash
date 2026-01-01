#!/usr/bin/env bash
# Change to the directory containing this script, then run the module
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
exec python3 -m src.main "$@"
