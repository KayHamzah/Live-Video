#!/usr/bin/env bash
# Render the edited dendeng video: slow-mo + boomerang, warm colour grade,
# slow push-in, and animated title/caption overlays.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IN="${1:-$ROOT/input/VID_20261022_205427.mp4}"
OUT="${2:-$ROOT/output/dendeng_food_engine_cooven.mp4}"
BUILD="$ROOT/build"

python3 "$ROOT/scripts/make_overlays.py" "$BUILD"
mkdir -p "$(dirname "$OUT")"

# 1) Base clip: half speed (60fps -> smooth 30fps slow-mo), then play it back
#    in reverse so the 3.4s source becomes a ~13.7s seamless loop.
ffmpeg -v error -y -i "$IN" -an \
  -filter_complex "[0:v]setpts=2*PTS,fps=30,format=yuv420p,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]" \
  -map "[v]" -c:v libx264 -crf 12 -preset fast "$BUILD/base.mp4"

D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$BUILD/base.mp4")

# Caption windows (seconds)
T0=0.2                 # title in
C1=1.3;  C1E=4.6       # Masak 2 jam tanpa kacau
C2=4.8;  C2E=7.9       # pun tak berkerak
C3=8.1;  C3E=11.0      # lembut & sedap
SC=11.2                # Smart Cook (until end)

# Fade in/out with a short ease-out slide up (or down for the title).
slide() { # $1 start, $2 offset px
  echo "if(lt(t,$1),$2,if(lt(t,$1+0.4),$2*pow(1-(t-$1)/0.4,2),0))"
}
ov() { # $1 label, $2 start, $3 end
  echo "[$1]format=rgba,fade=in:st=$2:d=0.35:alpha=1,fade=out:st=$(echo "$3-0.3" | bc):d=0.3:alpha=1[$1f]"
}

ffmpeg -v error -y -i "$BUILD/base.mp4" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/shade.png" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/title.png" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/cap1.png" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/cap2.png" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/cap3.png" \
  -loop 1 -framerate 30 -t "$D" -i "$BUILD/smartcook.png" \
  -f lavfi -t "$D" -i anullsrc=r=48000:cl=stereo \
  -filter_complex "
    [0:v]eq=contrast=1.08:saturation=1.3:gamma=1.03,
         colorbalance=rs=0.05:bs=-0.05:rm=0.03:bm=-0.03,
         unsharp=5:5:0.5,
         scale=w='trunc(1080*(1+0.07*t/$D)/2)*2':h=-2:eval=frame,
         crop=1080:1920,vignette=PI/5,setsar=1[g];
    [g][1:v]overlay=0:0[s];
    [2:v]format=rgba,fade=in:st=$T0:d=0.4:alpha=1[t];
    $(ov 3:v "$C1" "$C1E" | sed 's/\[3:vf\]/[c1]/');
    $(ov 4:v "$C2" "$C2E" | sed 's/\[4:vf\]/[c2]/');
    $(ov 5:v "$C3" "$C3E" | sed 's/\[5:vf\]/[c3]/');
    [6:v]format=rgba,fade=in:st=$SC:d=0.35:alpha=1[sc];
    [s][t]overlay=x=0:y='-1*$(slide $T0 50)':eval=frame[o1];
    [o1][c1]overlay=x=0:y='$(slide $C1 60)':eval=frame:enable='between(t,$C1,$C1E)'[o2];
    [o2][c2]overlay=x=0:y='$(slide $C2 60)':eval=frame:enable='between(t,$C2,$C2E)'[o3];
    [o3][c3]overlay=x=0:y='$(slide $C3 60)':eval=frame:enable='between(t,$C3,$C3E)'[o4];
    [o4][sc]overlay=x=0:y='$(slide $SC 60)':eval=frame:enable='gte(t,$SC)',
         fade=in:st=0:d=0.3,fade=out:st=$(echo "$D-0.35" | bc):d=0.35,format=yuv420p[v]
  " \
  -map "[v]" -map 7:a -t "$D" \
  -c:v libx264 -profile:v high -crf 18 -preset slow -r 30 \
  -c:a aac -b:a 128k -movflags +faststart "$OUT"

echo "Wrote $OUT"
