#!/usr/bin/env bash
# Accept an export file, or read base64 from stdin. Pass --config when needed.
set -euo pipefail
exec python3 "$(dirname "$0")/pull.py" "$@"
