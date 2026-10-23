"""Split subtitle lines longer than MAX chars at the word nearest the middle (in place).

usage: split_subs.py subs.tsv [...]
Timing is divided in proportion to the characters on each side.
"""
import sys

MAX = 30
for path in sys.argv[1:]:
    out = []
    for row in open(path):
        if not row.strip():
            continue
        a, b, text = row.rstrip("\n").split("\t")
        a, b = float(a), float(b)
        stack = [(a, b, text)]
        while stack:
            s, e, t = stack.pop(0)
            if len(t) <= MAX or " " not in t:
                out.append((s, e, t))
                continue
            spaces = [i for i, ch in enumerate(t) if ch == " "]
            cut = min(spaces, key=lambda i: abs(i - len(t) / 2))
            left, right = t[:cut], t[cut + 1:]
            m = s + (e - s) * len(left) / (len(left) + len(right))
            stack[:0] = [(s, m, left), (m, e, right)]
    with open(path, "w") as f:
        for s, e, t in out:
            f.write(f"{s:.2f}\t{e:.2f}\t{t}\n")
    print(path, "max", max(len(t) for _, _, t in out))
