"""Snap cut points to the quietest 10 ms frame within a search window.

usage: snap.py audio16k.wav t1 t2 ... [--win 0.25]
prints: requested -> snapped (rms dB at snapped, min dB of window)
"""
import sys, wave
import numpy as np

path = sys.argv[1]
args = sys.argv[2:]
win = 0.25
if "--win" in args:
    i = args.index("--win")
    win = float(args[i + 1])
    args = args[:i] + args[i + 2:]

w = wave.open(path)
sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = sr // 100


def rms_db(t):
    a = int(t * sr)
    seg = x[max(0, a - hop // 2): a + hop // 2]
    return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)


for t in map(float, args):
    cands = np.arange(t - win, t + win + 1e-6, 0.01)
    dbs = np.array([rms_db(c) for c in cands])
    best = cands[int(np.argmin(dbs))]
    print(f"{t:9.2f} -> {best:9.2f}  ({dbs.min():6.1f} dB, at req {rms_db(t):6.1f} dB)")
