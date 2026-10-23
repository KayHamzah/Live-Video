"""Workflow for one short, driven by edit/shorts/<slug>/spec.json.

  python3 make_short.py draft  <spec.json> <audio16k.wav>   cut audio, re-transcribe, write subs.draft.tsv
  python3 make_short.py build  <spec.json>                  write edl.json from spec.json + subs.tsv
  python3 make_short.py srt    <spec.json> <out.srt>        export subs.tsv as SRT

spec.json:
  {"title": "Line 1\\NLine 2", "hook_sub": "...", "hook_end": sec (optional),
   "clips": [{"id": "...", "in": sec, "out": sec, "vin": sec?, "zoom": [z0, z1]?, "center": [x, y]?}]}

Durations are rounded to whole frames exactly as render.py does, so subtitle timing matches the render.
"""
import json, os, subprocess, sys

FPS = 30
HERE = os.path.dirname(os.path.abspath(__file__))


def frame_dur(c):
    return round((c["out"] - c["in"]) * FPS) / FPS


def draft(spec_path, wav):
    d = os.path.dirname(spec_path)
    spec = json.load(open(spec_path))
    clips = spec["clips"]
    parts = "".join(f"[0:a]atrim={c['in']}:{c['in'] + frame_dur(c)},asetpts=PTS-STARTPTS[a{i}];"
                    for i, c in enumerate(clips))
    fc = parts + "".join(f"[a{i}]" for i in range(len(clips))) + f"concat=n={len(clips)}:v=0:a=1[o]"
    cut = f"{d}/verify.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-filter_complex", fc, "-map", "[o]", cut], check=True)
    words_out = f"{d}/verify.jsonl"
    subprocess.run([sys.executable, "-I", f"{HERE}/wtranscribe.py", cut, "small", words_out, "0"],
                   check=True, stderr=subprocess.DEVNULL)
    words = [w for l in open(words_out) for w in json.loads(l)["words"]]
    # clip boundaries on the output timeline, to spot words clipped at a cut
    t, bounds = 0.0, []
    for c in clips:
        bounds.append((t, c["id"]))
        t += frame_dur(c)
    lines, cur = [], []
    for w in words:
        cur.append(w)
        text = " ".join(x[2].strip() for x in cur)
        if w[2].strip()[-1:] in ".?!," or len(text) > 22:
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    with open(f"{d}/subs.draft.tsv", "w") as f:
        for ln in lines:
            f.write(f"{ln[0][0]:.2f}\t{ln[-1][1]:.2f}\t{' '.join(x[2].strip() for x in ln)}\n")
    for b, cid in bounds:
        near = [f"{w[2].strip()}[{w[0]:.2f}]" for w in words if b - 1.0 <= w[0] <= b + 1.0]
        print(f"-- cut {cid:12s} @ {b:6.2f}: {' '.join(near)}")
    print("total", round(t, 2))


def build(spec_path):
    d = os.path.dirname(spec_path)
    spec = json.load(open(spec_path))
    clips, prev = [], None
    for c in spec["clips"]:
        e = {k: c[k] for k in ("in", "out", "vin", "zoom", "center") if k in c}
        same_shot = prev is not None and "vin" not in c and "vin" not in prev and 0 <= c["in"] - prev["out"] < 2.5
        if "zoom" not in e:
            if same_shot:
                # punch in/out on a jump cut inside one shot so it reads as an intentional cut
                was_in = clips[-1].get("zoom", [1, 1])[0] > 1.0
                e["zoom"] = [1.0, 1.02] if was_in else [1.08, 1.09]
                e.setdefault("center", [0.5, 0.35])
            else:
                e["zoom"] = [1.0, 1.04]
        clips.append(e)
        prev = c
    total = sum(frame_dur(c) for c in spec["clips"])
    subs = []
    for row in open(f"{d}/subs.tsv"):
        if not row.strip():
            continue
        a, b, text = row.rstrip("\n").split("\t")
        subs.append({"start": float(a), "end": min(float(b), total), "text": text})
    hook_end = spec.get("hook_end", min(4.0, max(2.8, frame_dur(spec["clips"][0]))))
    # hook_y: put the title lower (top edge in px) when a face fills the top of the opening shot
    hy = spec.get("hook_y")
    pos = (lambda y: f"{{\\an8\\pos(540,{y})}}") if hy else (lambda y: "")
    overlays = [{"start": 0.0, "end": hook_end, "style": "Hook", "text": pos(hy) + spec["title"]}]
    if spec.get("hook_sub"):
        overlays.append({"start": 0.35, "end": hook_end, "style": "HookSub",
                         "text": pos(hy + 250 if hy else None) + spec["hook_sub"]})
    edl = {"clips": clips, "subs": subs, "overlays": overlays, "total": total}
    if hy:
        edl["hook_band"] = [hy - 120, 560]
    json.dump(edl, open(f"{d}/edl.json", "w"), ensure_ascii=False, indent=1)
    print("total", round(total, 2), "subs", len(subs))


def srt(spec_path, out):
    d = os.path.dirname(spec_path)

    def ts(t):
        h, r = divmod(t, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"

    rows = [r.rstrip("\n").split("\t") for r in open(f"{d}/subs.tsv") if r.strip()]
    with open(out, "w") as f:
        for i, (a, b, t) in enumerate(rows, 1):
            f.write(f"{i}\n{ts(float(a))} --> {ts(float(b))}\n{t}\n\n")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "draft":
        draft(sys.argv[2], sys.argv[3])
    elif cmd == "build":
        build(sys.argv[2])
    elif cmd == "srt":
        srt(sys.argv[2], sys.argv[3])
