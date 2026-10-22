"""Build the reel's cut list and caption words from the word-level transcript.

Each beat is a list of source ranges (seconds). Inside a range, any gap between
words longer than MAX_GAP is cut out so awkward pauses disappear. Output:
  edl.json      - ordered cuts [{src_in, src_out, beat}] plus beat timings on the new timeline
  captions.json - [{text, start, end, beat}] on the new timeline
"""
import json
import sys

MAX_GAP = 0.35
PAD_IN = 0.06
PAD_OUT = 0.10

BEATS = [
    ("hook", [(4664.20, 4671.45)]),
    ("premise", [(4345.70, 4350.00)]),
    ("tip-lapik", [(520.20, 525.45), (541.90, 544.50), (551.45, 555.10)]),
    ("joke-oven", [(2227.65, 2234.10)]),
    ("tip-aroma", [(1169.80, 1171.30), (1172.00, 1179.50)]),
    ("tip-probe", [(818.10, 820.95), (822.10, 826.95), (2520.45, 2524.25)]),
    ("tip-180", [(1510.35, 1512.65), (1514.05, 1519.70), (1547.75, 1552.90), (2449.05, 2451.40)]),
    ("joke-dapur", [(2643.90, 2650.35)]),
    ("reveal", [(4541.20, 4543.40), (4545.20, 4548.94), (4550.68, 4552.90)]),
    ("closer", [(5111.15, 5117.40), (5119.94, 5120.90)]),
]

# Whisper spellings fixed for on-screen captions (spoken audio is untouched).
FIX = {
    "cucu": "cucur", "Cooper": "Cooven", "4G": "", "seko": "seekor", "mi": "ni",
    "jalur": "kawal", "Bakker's": "Baker's", "marinakan": "perap",
}


def load_words(path):
    words = []
    for line in open(path):
        seg = json.loads(line)
        for s, e, w in seg["words"]:
            words.append((s, e, w.strip()))
    return words


def main(transcript, out_dir):
    words = load_words(transcript)
    cuts, caps, beats = [], [], []
    t = 0.0
    for beat, ranges in BEATS:
        beat_start = t
        for a, b in ranges:
            ws = [w for w in words if w[0] >= a - 0.01 and w[1] <= b + 0.01]
            # split the range at long pauses
            groups, cur = [], [ws[0]]
            for prev, w in zip(ws, ws[1:]):
                if w[0] - prev[1] > MAX_GAP:
                    groups.append(cur)
                    cur = [w]
                else:
                    cur.append(w)
            groups.append(cur)
            for g in groups:
                src_in = max(a, g[0][0] - PAD_IN)
                src_out = min(b, g[-1][1] + PAD_OUT)
                cuts.append({"src_in": round(src_in, 3), "src_out": round(src_out, 3), "beat": beat})
                for s, e, w in g:
                    text = " ".join(FIX.get(p, p) for p in w.split()).strip()
                    if not text:
                        continue
                    if text.startswith("-") and caps:  # "Kadang" "-kadang" -> "Kadang-kadang"
                        caps[-1]["text"] += text
                        caps[-1]["end"] = round(t + e - src_in, 3)
                        continue
                    caps.append({"text": text, "start": round(t + s - src_in, 3),
                                                  "end": round(t + e - src_in, 3), "beat": beat, "cut": len(cuts) - 1})
                t += src_out - src_in
        beats.append({"beat": beat, "start": round(beat_start, 3), "end": round(t, 3)})
    json.dump({"cuts": cuts, "beats": beats, "duration": round(t, 3)},
              open(f"{out_dir}/edl.json", "w"), indent=1)
    json.dump(caps, open(f"{out_dir}/captions.json", "w"), indent=1, ensure_ascii=False)
    for bt in beats:
        print(f"{bt['beat']:<12} {bt['start']:6.2f} -> {bt['end']:6.2f}  ({bt['end'] - bt['start']:.1f}s)")
    print("cuts:", len(cuts), "duration:", round(t, 2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
