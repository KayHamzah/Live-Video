"""Build edl.json (clips + subtitle cues + overlays) for render.py.

Subtitle cues come from large-v3 word timestamps, remapped to the output timeline,
grouped into short single lines.
"""
import json, re, sys

clips_path, words_path, out_path = sys.argv[1:4]  # argv[4]: hand-authored cues (tsv)
clips = json.load(open(clips_path))
words = []
for l in open(words_path):
    words += json.loads(l)["words"]
words.sort()

# visual treatment per clip: zoom start/end and zoom centre (x, y fractions)
LOOK = {
    "hook":       dict(zoom=[1.00, 1.07], center=[0.5, 0.80]),
    "problem":    dict(zoom=[1.00, 1.02]),
    "problem_b":  dict(zoom=[1.10, 1.12], center=[0.5, 0.30]),
    "minyak":     dict(zoom=[1.08, 1.08], center=[0.5, 0.75]),
    "sos_b":      dict(zoom=[1.08, 1.08], center=[0.5, 0.75]),
    "air2":       dict(zoom=[1.08, 1.10], center=[0.5, 0.75]),
    "rendam":     dict(zoom=[1.08, 1.08], center=[0.5, 0.75]),
    "airfryer_b": dict(zoom=[1.08, 1.08], center=[0.5, 0.30]),
    "hasil":      dict(zoom=[1.00, 1.05], center=[0.5, 0.80]),
    "masa":       dict(zoom=[1.06, 1.06], center=[0.5, 0.70]),
    "tutup_ayat": dict(zoom=[1.00, 1.04], center=[0.5, 0.30]),
}

# word-level clean-ups: drop fillers / fragments heard at cut edges, fix spellings
DROP = {"aa", "ah", "eh", "okey", "ok", "okay", "ok,", "okay,", "okey,"}
FIX = {"rely": "relai", "holland": "Holland", "minit.": "minit.", "Yang": ""}
NUMS = [
    (r"empat ratus lima puluh gram", "450 gram"),
    (r"tiga ratus gram", "300 gram"),
    (r"dua ratus empat puluh", "240°C"),
    (r"\b2 sudu besar", "2 sudu besar"),
]

out_t = 0.0
edl_clips, toks = [], []
marks = {}
for c in clips:
    d = c["out"] - c["in"]
    marks[c["id"]] = (out_t, out_t + d)
    edl_clips.append({"in": c["in"], "out": c["out"], **LOOK.get(c["id"], {})})
    for s, e, w in words:
        mid = (s + e) / 2
        if c["in"] <= mid < c["out"]:
            w = w.strip()
            if w.lower() in DROP or w.lower().strip(",.?") in DROP:
                continue
            w = FIX.get(w, w)
            if not w:
                continue
            toks.append([max(out_t, out_t + s - c["in"]), min(out_t + d, out_t + e - c["in"]), w, c["id"]])
    out_t += d
total = out_t

subs = []
for row in open(sys.argv[4]):
    a, b, text = row.rstrip("\n").split("\t")
    subs.append({"start": float(a), "end": min(float(b), total), "text": text})


def span(first, last=None):
    return marks[first][0], marks[last or first][1]


def chip(first, last, text):
    a, b = span(first, last)
    return {"start": a + 0.05, "end": b - 0.05, "style": "Chip", "text": text}


ha, hb = span("hook")
ea, eb = span("tutup_ayat")
overlays = [
    {"start": 0.0, "end": hb, "style": "Hook", "text": "Nasi Goreng\\NTerus Dari Beras"},
    {"start": 0.35, "end": hb, "style": "HookSub", "text": "Tanpa nasi sejuk"},
    chip("bawang", "minyak", "1   Bawang Holland ½ biji  ·  Minyak 50 g"),
    chip("telur", "telur", "2   Telur, scramble"),
    chip("sos", "kicap", "3   Sos tiram  ·  Light soy sauce"),
    chip("air1", "air2", "4   Air 450 g  ·  Beras basmati 300 g"),
    chip("beras", "rendam", "5   Masukkan beras, tak perlu rendam"),
    chip("tutup", "smartcook", "6   Smart Cook P2  ·  25 min"),
    chip("airfryer", "airfryer_b", "7   Tukar ke penutup air fryer"),
    chip("hasil", "hasil", "Tak berkerak"),
    chip("suhu", "masa", "8   240°C  ·  5 minit"),
    {"start": ea + 0.1, "end": eb, "style": "Recap",
     "text": "Resepi\\NBeras basmati 300 g  ·  Air 450 g  ·  Minyak 50 g\\NSmart Cook P2 25 min  →  240°C 5 min"},
]

json.dump({"clips": edl_clips, "subs": subs, "overlays": overlays, "total": total},
          open(out_path, "w"), ensure_ascii=False, indent=1)
for s in subs:
    print(f"{s['start']:6.2f}-{s['end']:6.2f}  {s['text']}")
print("total", round(total, 2))
