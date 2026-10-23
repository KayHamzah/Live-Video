"""Render the short from an edit decision list (edl.json).

edl.json:
  clips:    [{"in": sec, "out": sec, "zoom": [z0, z1], "center": [x, y], "vin": sec}]
            source timestamps; zoom/center/vin optional (vin = picture start for B-roll)
  subs:     [{"start": out_sec, "end": out_sec, "text": str}]          output timeline
  overlays: [{"start", "end", "style", "text"}]                        title / hook / step chips
"""
import json, subprocess, sys, os

SRC, EDL, OUT, WORK = sys.argv[1:5]
W, H, FPS = 1080, 1920, 30
edl = json.load(open(EDL))
os.makedirs(WORK, exist_ok=True)


def run(cmd):
    subprocess.run(cmd, check=True)


# 1. cut each clip to an intermediate with identical format
parts = []
for i, c in enumerate(edl["clips"]):
    # whole frames only, and audio trimmed to exactly the same length, so A/V can't drift across cuts
    nframes = round((c["out"] - c["in"]) * FPS)
    dur = nframes / FPS
    z0, z1 = c.get("zoom", [1.0, 1.0])
    # slow, subtle punch-in centred on (cx, cy) as fractions of the frame
    cx, cy = c.get("center", [0.5, 0.5])
    zexpr = f"({z0}+({z1}-{z0})*t/{dur:.3f})"
    vf = (
        f"fps={FPS},scale={W}:{H}:flags=lanczos,"
        f"scale=w='trunc({W}*{zexpr}/2)*2':h='trunc({H}*{zexpr}/2)*2':eval=frame:flags=lanczos,"
        f"crop={W}:{H}:x='(iw-{W})*{cx}':y='(ih-{H})*{cy}',"
        "unsharp=5:5:0.45:5:5:0,setsar=1,format=yuv420p"
    )
    fade = 0.04
    af = (
        "aresample=48000,highpass=f=80,afftdn=nr=8:nf=-40,"
        f"apad,atrim=0:{dur:.6f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d={fade},afade=t=out:st={dur - fade:.3f}:d={fade}"
    )
    p = f"{WORK}/part_{i:02d}.mp4"
    # optional "vin": take the picture from another moment (B-roll) under this clip's voice
    vin = c.get("vin", c["in"])
    run(["ffmpeg", "-v", "error", "-y",
         "-ss", f"{vin:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", SRC,
         "-ss", f"{c['in']:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", SRC,
         "-map", "0:v", "-map", "1:a",
         "-vf", vf, "-af", af, "-frames:v", str(nframes), "-c:v", "libx264", "-preset", "medium", "-crf", "16",
         "-c:a", "pcm_s16le", "-ac", "2", p])
    parts.append(p)

with open(f"{WORK}/concat.txt", "w") as f:
    for p in parts:
        f.write(f"file '{p}'\n")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/concat.txt",
     "-c", "copy", f"{WORK}/joined.mkv"])


# 2. subtitles + overlays as one ASS file
def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


# Colours are &HAABBGGRR. Only black and white are used.
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter Medium,52,&H00FFFFFF,&H00FFFFFF,&H50000000,&H00000000,0,0,0,0,100,100,0.5,0,3,14,0,2,90,90,{H - 1252},1
Style: Hook,Inter ExtraBold,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H70000000,-1,0,0,0,100,100,-1,0,1,0,5,8,70,70,240,1
Style: HookSub,Inter,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H60000000,0,0,0,0,100,100,2,0,1,0,4,8,70,70,500,1
Style: Chip,Inter Medium,46,&H00000000,&H00000000,&H14FFFFFF,&H00000000,0,0,0,0,100,100,0.5,0,3,18,0,8,70,70,250,1
Style: Recap,Inter Medium,42,&H00000000,&H00000000,&H14FFFFFF,&H00000000,0,0,0,0,100,100,0.5,0,3,18,0,8,60,60,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for o in edl["overlays"]:
    fad = r"{\fad(180,180)}"
    ass += f"Dialogue: 1,{ts(o['start'])},{ts(o['end'])},{o['style']},,0,0,0,,{fad}{o['text']}\n"
for s in edl["subs"]:
    ass += f"Dialogue: 0,{ts(s['start'])},{ts(s['end'])},Sub,,0,0,0,,{s['text']}\n"
open(f"{WORK}/subs.ass", "w").write(ass)

# 3. final pass: burn text, dark top gradient behind title for contrast, loudness to -14 LUFS
# the gradient is rendered once as a still; per-frame geq is far too slow
grad_png = f"{WORK}/gradient.png"
band = edl.get("hook_band")  # [y, height]: soft dark band behind a title placed lower in the frame
if band:
    gy, gh, galpha = band[0], band[1], "150*sin(PI*Y/H)"
else:
    gy, gh, galpha = 0, 760, "180*pow(1-Y/H\\,1.3)"
run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{gh}", "-frames:v", "1",
     "-vf", f"format=rgba,geq=r=0:g=0:b=0:a='{galpha}'", grad_png])
fc = (
    f"[0:v][1:v]overlay=0:{gy}:shortest=1:enable='lt(t,{edl['overlays'][0]['end']:.2f})',ass={WORK}/subs.ass:fontsdir=/usr/share/fonts,format=yuv420p[v];"
    + "[0:a]acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,"
      "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]"
)
run(["ffmpeg", "-v", "error", "-y", "-i", f"{WORK}/joined.mkv", "-loop", "1", "-i", grad_png,
     "-filter_complex", fc, "-shortest",
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
     "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT])
print("rendered", OUT)
