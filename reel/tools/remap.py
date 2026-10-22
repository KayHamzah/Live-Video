"""Shift caption and beat times onto the frame-accurate durations of the assembled pieces."""
import json, subprocess, sys, glob
edl = json.load(open(sys.argv[1])); caps = json.load(open(sys.argv[2])); pieces = sorted(glob.glob(sys.argv[3] + "/p*.mov"))
real = [float(subprocess.check_output(["ffprobe","-v","error","-select_streams","v","-show_entries","stream=duration","-of","csv=p=0",p])) for p in pieces]
plan_starts, real_starts, t, r = [], [], 0.0, 0.0
for c, d in zip(edl["cuts"], real):
    plan_starts.append(t); real_starts.append(r); t += c["src_out"] - c["src_in"]; r += d
def remap(x):
    k = max(i for i, s in enumerate(plan_starts) if s <= x + 1e-6)
    return round(real_starts[k] + (x - plan_starts[k]), 3)
for w in caps: w["start"], w["end"] = remap(w["start"]), remap(w["end"])
for b in edl["beats"]: b["start"] = remap(b["start"])
for i, b in enumerate(edl["beats"]): b["end"] = edl["beats"][i+1]["start"] if i+1 < len(edl["beats"]) else round(r, 3)
edl["duration"] = round(r, 3); edl["cut_starts"] = [round(s, 3) for s in real_starts]
json.dump(edl, open(sys.argv[4] + "/edl.json", "w"), indent=1)
json.dump(caps, open(sys.argv[4] + "/captions.json", "w"), indent=1, ensure_ascii=False)
print("duration", round(r, 3)); [print(b) for b in edl["beats"]]
