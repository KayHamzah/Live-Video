#!/usr/bin/env bash
# Cut the source per edl.json and join the pieces into one seek-friendly 1080x1920 clip.
# usage: assemble.sh <source.mp4> <edl.json> <work_dir> <out.mp4>
set -euo pipefail
SRC=$1 EDL=$2 WORK=$3 OUT=$4
mkdir -p "$WORK/pieces"
rm -f "$WORK/pieces/"*.mov
i=0
python3 -c "
import json,sys
for c in json.load(open('$EDL'))['cuts']: print(c['src_in'], c['src_out'])
" | while read -r IN OUTT; do
  DUR=$(python3 -c "print(round($OUTT-$IN,3))")
  FO=$(python3 -c "print(round($OUTT-$IN-0.015,3))")
  P=$(printf "%s/pieces/p%02d.mp4" "$WORK" "$i")
  ffmpeg -nostdin -v error -y -ss "$IN" -i "$SRC" -t "$DUR" \
    -vf "fps=30,scale=1080:1920:flags=lanczos,setsar=1" \
    -af "aresample=48000,afade=t=in:d=0.015,afade=t=out:st=$FO:d=0.015" \
    -c:v libx264 -preset medium -crf 16 -g 30 -pix_fmt yuv420p \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
    -c:a pcm_s16le -ar 48000 -ac 2 "${P%.mp4}.mov"
    i=$((i+1))
done
# join with the concat filter (the concat demuxer drifts A/V by ~0.1 s per piece),
# then normalize speech loudness for social (-16 LUFS, -1.5 dBTP)
N=$(ls "$WORK/pieces/"p*.mov | wc -l)
INPUTS=$(for f in "$WORK/pieces/"p*.mov; do printf -- '-i %q ' "$f"; done)
FC=$(python3 -c "
n=$N
print(''.join(f'[{i}:v]setpts=PTS-STARTPTS[v{i}];[{i}:a]asetpts=PTS-STARTPTS[a{i}];' for i in range(n))
      + ''.join(f'[v{i}][a{i}]' for i in range(n))
      + f'concat=n={n}:v=1:a=1[v][a];[a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[an]')")
eval ffmpeg -nostdin -v error -y $INPUTS -filter_complex "'$FC'" -map "'[v]'" -map "'[an]'" \
  -c:v libx264 -preset medium -crf 16 -g 30 -pix_fmt yuv420p \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -b:a 192k -movflags +faststart "'$OUT'"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
