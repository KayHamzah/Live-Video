#!/usr/bin/env bash
# Draft-render each short and make a light 720x1280 preview copy for review.
# usage: tools/render_previews.sh [video-id ...]   (default: every project with assets/clip.mp4)
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p previews
ids=("$@")
if [ ${#ids[@]} -eq 0 ]; then
  for d in */assets/clip.mp4; do ids+=("${d%%/*}"); done
fi
for id in "${ids[@]}"; do
  start=$(date +%s)
  if (cd "$id" && npx hyperframes render -q draft -f 30 -w 4 -o "renders/draft.mp4" >render.log 2>&1); then
    ffmpeg -nostdin -v error -y -i "$id/renders/draft.mp4" -vf "scale=720:1280:flags=lanczos" \
      -c:v libx264 -preset medium -crf 25 -c:a aac -b:a 128k -movflags +faststart "previews/$id.mp4"
    echo "$id ok $(( $(date +%s) - start ))s $(ffprobe -v error -show_entries format=duration -of csv=p=0 "previews/$id.mp4")s"
  else
    echo "$id FAILED (see $id/render.log)"
  fi
done
