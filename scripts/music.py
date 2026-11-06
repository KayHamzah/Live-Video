"""Synthesize an original, royalty-free soft lo-fi/chill bed for the edit."""
import sys, wave
import numpy as np

SR = 44100
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
BPM = 84
beat = 60 / BPM
N = int(SR * (DUR + 2))
rng = np.random.default_rng(7)
out = np.zeros((N, 2))

def midi(n):
    return 440 * 2 ** ((n - 69) / 12)

# Fmaj7 - Em7 - Dm7 - Cmaj7 (one bar = 4 beats each)
chords = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
bar = 4 * beat
t_all = np.arange(N) / SR

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    sig = sig[: N - i]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    out[i:i + len(sig), 0] += sig * gain * l
    out[i:i + len(sig), 1] += sig * gain * r

# Pad
nbars = int(DUR / bar) + 2
for b in range(nbars):
    ch = chords[b % 4]
    L = int(bar * SR * 1.15)
    t = np.arange(L) / SR
    env = np.minimum(1, t / 0.6) * np.minimum(1, np.maximum(0, (bar * 1.15 - t) / 0.7))
    s = np.zeros(L)
    for n in ch:
        f = midi(n)
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * f * (1 + det / 100) * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    s = np.convolve(s, np.ones(24) / 24, mode="same")
    add(s * env, b * bar, pan=0.0, gain=0.018)
    # bass
    f = midi(ch[0] - 12)
    for k in (0, 2.5):
        Lb = int(beat * 1.4 * SR)
        tb = np.arange(Lb) / SR
        sb = np.sin(2 * np.pi * f * tb) * np.exp(-tb * 2.2) * np.minimum(1, tb / 0.01)
        add(sb, b * bar + k * beat, gain=0.09)
    # arpeggio pluck (8ths)
    pattern = [0, 2, 1, 3, 2, 1, 3, 2]
    for k, p in enumerate(pattern):
        if (b + k) % 5 == 4:
            continue
        f = midi(ch[p] + 12)
        Lp = int(0.9 * SR)
        tp = np.arange(Lp) / SR
        sp = (np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(2 * np.pi * 2 * f * tp) * np.exp(-tp * 6)) * np.exp(-tp * 4.5)
        sp *= np.minimum(1, tp / 0.004)
        add(sp, b * bar + k * beat / 2, pan=(-0.35 if k % 2 else 0.35), gain=0.028)
    # drums: soft kick 1 & 3, rim on 2 & 4, shaker 8ths
    for k in (0, 2):
        Lk = int(0.35 * SR)
        tk = np.arange(Lk) / SR
        fk = 50 + 70 * np.exp(-tk * 30)
        sk = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-tk * 9)
        add(sk, b * bar + k * beat, gain=0.16)
    for k in (1, 3):
        Ls = int(0.18 * SR)
        ts = np.arange(Ls) / SR
        ns = rng.standard_normal(Ls)
        ns = ns - np.convolve(ns, np.ones(6) / 6, mode="same")
        add(ns * np.exp(-ts * 28), b * bar + k * beat, gain=0.035)
    for k in range(8):
        Lh = int(0.06 * SR)
        th = np.arange(Lh) / SR
        nh = rng.standard_normal(Lh)
        nh = nh - np.convolve(nh, np.ones(3) / 3, mode="same")
        add(nh * np.exp(-th * 70), b * bar + k * beat / 2 + 0.012, pan=0.3, gain=(0.018 if k % 2 else 0.011))

# Simple reverb
irL = int(1.6 * SR)
ti = np.arange(irL) / SR
for c in range(2):
    ir = rng.standard_normal(irL) * np.exp(-ti * 3.2)
    ir = np.convolve(ir, np.ones(8) / 8, mode="same")
    ir /= np.sqrt(np.sum(ir ** 2))
    n2 = 1 << int(np.ceil(np.log2(N + irL)))
    wet = np.fft.irfft(np.fft.rfft(out[:, c], n2) * np.fft.rfft(ir, n2), n2)[:N]
    out[:, c] = out[:, c] + 0.28 * wet

out = out[: int(SR * DUR)]
fade_in, fade_out = int(0.8 * SR), int(2.5 * SR)
out[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
out[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
out /= np.max(np.abs(out)) / 0.89
pcm = (out * 32767).astype(np.int16)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
