#!/usr/bin/env bash
# tg_mux.sh <project> <name> <output.mp4>; input is the final vertical render.
set -euo pipefail
P="$1"; N="$2"; O="$3"
ffmpeg -y -loglevel error -i "$P/out/$N-vertical.mp4" \
  -vf scale=720:1280,format=yuv420p -c:v libx264 -crf 29 -preset slow \
  -c:a aac -b:a 96k -movflags +faststart "$O"
ls -lh "$O"
# File size depends on duration/content; measure before uploading.
