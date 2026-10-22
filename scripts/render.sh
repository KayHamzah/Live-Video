#!/usr/bin/env bash
# Render the edited dendeng video: two clips joined with crossfades, warm
# colour grade, slow push-in, and animated title/caption overlays.
#
#   clip 1 (slow-mo)  ->  clip 2 (spatula shows the pot bottom)  ->  clip 1 reversed
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IN1="${1:-$ROOT/input/VID_20261022_205427.mp4}"
IN2="${2:-$ROOT/input/VID_20261022_231432.mp4}"
OUT="${3:-$ROOT/output/dendeng_food_engine_cooven.mp4}"
BUILD="$ROOT/build"
XF=0.5                 # crossfade length (s)

python3 "$ROOT/scripts/make_overlays.py" "$BUILD"
mkdir -p "$(dirname "$OUT")"

dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }

# 1) Base clip. Clip 1 at half speed (60fps -> smooth 30fps slow-mo), clip 2
#    at 0.6x, then clip 1 again in reverse for the ending.
D1=$(echo "$(dur "$IN1")*2" | bc -l)
D2=$(echo "$(dur "$IN2")/0.6" | bc -l)
O1=$(echo "$D1-$XF" | bc -l)
O2=$(echo "$D1+$D2-2*$XF" | bc -l)
NORM="fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,format=yuv420p,settb=AVTB"
ffmpeg -v error -y -i "$IN1" -i "$IN2" -an \
  -filter_complex "
    [0:v]setpts=2*PTS,$NORM,split[a][b];[b]reverse,setpts=PTS-STARTPTS[r];
    [1:v]setpts=PTS/0.6,$NORM[c];
    [a][c]xfade=transition=fade:duration=$XF:offset=$O1[ac];
    [ac][r]xfade=transition=fade:duration=$XF:offset=$O2[v]" \
  -map "[v]" -c:v libx264 -crf 12 -preset fast "$BUILD/base.mp4"

D=$(dur "$BUILD/base.mp4")

# Caption windows (seconds)
T0=0.2                                   # title in
C1=1.3;  C1E=$O1                         # Masak 2 jam tanpa kacau (clip 1)
C2=$(echo "$O1+0.5" | bc -l); C2E=$O2    # pun tak berkerak (clip 2)
C3=$(echo "$O2+0.5" | bc -l)             # lembut & sedap (clip 1 reversed)
C3E=$(echo "$C3+3.4" | bc -l)
SC=$(echo "$C3E+0.2" | bc -l)            # Smart Cook (until end)

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
