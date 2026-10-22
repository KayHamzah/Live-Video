#!/usr/bin/env bash
# Final 1080x1920 render of each short, plus an upload-size copy with audio peaks held at -1.5 dB.
# usage: tools/render_finals.sh [video-id ...]   (default: every project with assets/clip.mp4)
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p final
ids=("$@")
if [ ${#ids[@]} -eq 0 ]; then
  for d in */assets/clip.mp4; do ids+=("${d%%/*}"); done
fi
for id in "${ids[@]}"; do
  start=$(date +%s)
  if (cd "$id" && npx hyperframes render -q high -f 30 -w 4 -o "renders/final.mp4" >render-final.log 2>&1); then
    ffmpeg -nostdin -v error -y -i "$id/renders/final.mp4" -c:v copy \
      -af "alimiter=limit=0.84:attack=2:release=50:level=false,aresample=48000" -c:a aac -b:a 192k \
      -movflags +faststart "final/$id.mp4"
    ffmpeg -nostdin -v error -y -i "final/$id.mp4" -c:v libx264 -preset slow -crf 19 -pix_fmt yuv420p \
      -c:a copy -movflags +faststart "final/$id (upload).mp4"
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "final/$id (upload).mp4")
    echo "$id ok $(( $(date +%s) - start ))s ${dur}s"
  else
    echo "$id FAILED (see $id/render-final.log)"
  fi
done
