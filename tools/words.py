"""Print word-level timings for a time range: python3 words.py transcript.jsonl START END"""
import json, sys
a, b = float(sys.argv[2]), float(sys.argv[3])
line = []
for l in open(sys.argv[1], encoding="utf-8"):
    for s, e, w in json.loads(l)["words"]:
        if a <= s <= b:
            line.append(f"{s:.2f}|{w.strip()}")
            if len(line) == 8:
                print("  ".join(line)); line = []
print("  ".join(line))
