#!/usr/bin/env bash
# Create a fresh episode without overwriting an existing directory.
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
P="${1:?usage: new_episode.sh <new-directory> [voice]}"
V="${2:-jessica}"
[ ! -e "$P" ] || { echo "directory already exists" >&2; exit 1; }
cp -R "$SK/assets/template" "$P"
cd "$P"
cp brand.example.json brand.json
python3 - "$V" <<'PYVOICE'
import json,sys
with open('audio/vo/voice.json','w') as f:
    json.dump({'voice':sys.argv[1], 'engine':'eleven'}, f)
PYVOICE
npm install --no-audit --no-fund
echo "ready: edit brand.json and write SCRIPT.md from SCRIPT.example.md"
