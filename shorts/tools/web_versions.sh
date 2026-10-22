#!/usr/bin/env bash
# 1080x1920 copies capped near 13.5 MB (two-pass), small enough to host in the gallery page.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p web
for f in final/*"(upload).mp4"; do
  id=$(basename "$f" " (upload).mp4")
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  vk=$(python3 -c "print(int(13.5*8*1024/$dur - 128 - 40))")
  ( cd /tmp && ffmpeg -nostdin -v error -y -i "$OLDPWD/$f" -c:v libx264 -preset medium -b:v ${vk}k -pass 1 -passlogfile "/tmp/x264_$id" -an -f null /dev/null && \
    ffmpeg -nostdin -v error -y -i "$OLDPWD/$f" -c:v libx264 -preset medium -b:v ${vk}k -pass 2 -passlogfile "/tmp/x264_$id" \
      -c:a aac -b:a 128k -movflags +faststart "$OLDPWD/web/$id.mp4" )
  echo "$id $(du -m "web/$id.mp4" | cut -f1)MB ${vk}k"
done
