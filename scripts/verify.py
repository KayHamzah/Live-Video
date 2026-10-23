import json, subprocess, sys
clips_path, wav_in, wav_out = sys.argv[1:4]
c = json.load(open(clips_path))
parts = "".join(f"[0:a]atrim={x['in']}:{x['out']},asetpts=PTS-STARTPTS[a{i}];" for i, x in enumerate(c))
fc = parts + "".join(f"[a{i}]" for i in range(len(c))) + f"concat=n={len(c)}:v=0:a=1[o]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav_in, "-filter_complex", fc, "-map", "[o]", wav_out], check=True)
t = 0
for x in c:
    d = x["out"] - x["in"]
    print(f"{x['id']:11s} out {t:6.2f}-{t + d:6.2f}")
    t += d
print("total", round(t, 2))
