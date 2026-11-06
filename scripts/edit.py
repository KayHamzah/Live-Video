"""Build the Stew Ayam / Food Engine Cooven short (1080x1920, 30fps)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]           # folder with the raw clips
WORK = sys.argv[2]          # output/work folder
os.makedirs(WORK, exist_ok=True)
W, H, FPS, XF = 1080, 1920, 30, 0.3
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"

# (clip, source start, duration, caption)
# caption = (label, [lines]); each line is a list of (text, bold)
SEGS = [
    ("VID_20261105_122607", 0.0, 3.2, "TITLE"),
    ("VID_20261105_114402", 0.3, 3.0, ("PANASKAN COOVEN", [[("Masa: ", 0), ("15 minit", 1)]])),
    ("VID_20261105_114423", 0.0, 3.0, ("LANGKAH 1", [[("Masukkan ", 0), ("minyak", 1)]])),
    ("VID_20261105_114758", 6.0, 4.0, ("LANGKAH 2", [[("Masukkan ", 0), ("ayam", 1)]])),
    ("VID_20261105_115433", 1.5, 3.5, ("LANGKAH 3", [[("Goreng ayam", 1)], [("hingga berubah warna", 0)]])),
    ("VID_20261105_115944", 0.8, 3.5, ("LANGKAH 4", [[("Masukkan ", 0), ("bawang", 1), (" + ", 0), ("halia", 1)]])),
    ("VID_20261105_120052", 0.8, 3.5, ("LANGKAH 5", [[("Masukkan ", 0), ("kentang", 1)], [("+ ", 0), ("lobak merah", 1)]])),
    ("VID_20261105_120052", 13.2, 3.0, ("LANGKAH 6", [[("Tutup ", 0), ("penutup", 1)]])),
    ("VID_20261105_120122", 1.4, 2.8, ("TETAPAN COOVEN", [[("Suhu: ", 0), ("140°C", 1)], [("Masa: ", 0), ("25 minit", 1)]])),
    ("VID_20261105_120914", 26.0, 3.5, ("LANGKAH 7", [[("Masukkan ", 0), ("air", 1)]])),
    ("VID_20261105_121112", 1.5, 3.2, ("LANGKAH 8", [[("Masukkan ", 0), ("sos & perasa", 1)]])),
    ("VID_20261105_121352", 0.0, 3.2, ("LANGKAH 9", [[("Pekatkan kuah", 1)], [("dengan bancuhan tepung", 0)]])),
    ("VID_20261105_121407", 6.0, 3.2, ("SAMBUNG MASAK", [[("Suhu: ", 0), ("140°C", 1)], [("Masa: ", 0), ("20 minit", 1)]])),
    ("VID_20261105_122008", 6.2, 3.0, None),
    ("VID_20261105_122105", 0.8, 4.0, ("LANGKAH 10", [[("Capsicum kuning", 1)], [("+ ", 0), ("Cili", 1), (" + ", 0), ("Daun bawang", 1)]])),
    ("VID_20261105_122105", 12.0, 3.0, ("GAUL RATA", [[("Kacau hingga ", 0), ("sebati", 1)]])),
    ("VID_20261105_122620", 1.0, 4.5, ("SIAP!", [[("Stew ayam ", 0), ("pekat & berkuah", 1)]])),
    ("VID_20261105_122607", 3.6, 3.6, "OUTRO"),
]


def font(w, s):
    return ImageFont.truetype(FONT.format(w), s)


def run_width(runs, reg, bold):
    return sum((bold if b else reg).getlength(t) for t, b in runs)


def card(label, lines, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lab_f, reg, bold = font("SemiBold", 34), font("Medium", 58), font("ExtraBold", 58)
    pad, x0, y0, lh = 44, 72, 250, 78
    tw = max([lab_f.getlength(label) + 6 * len(label)] + [run_width(r, reg, bold) for r in lines])
    ch = pad * 2 + 46 + 26 + lh * len(lines) - 14
    # frosted dark card
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x0 - 6, y0 + 10, x0 + tw + pad * 2 + 6, y0 + ch + 16], 34, fill=(0, 0, 0, 90))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x0 + tw + pad * 2, y0 + ch], 30, fill=(12, 12, 12, 150))
    x, y = x0 + pad, y0 + pad
    # thin accent rule + spaced label
    d.rounded_rectangle([x, y + 12, x + 34, y + 16], 2, fill=(255, 255, 255, 230))
    lx = x + 50
    for c in label:
        d.text((lx, y), c, font=lab_f, fill=(255, 255, 255, 215))
        lx += lab_f.getlength(c) + 6
    y += 46 + 26
    for runs in lines:
        cx = x
        for t, b in runs:
            f = bold if b else reg
            d.text((cx, y), t, font=f, fill=(255, 255, 255, 255 if b else 225))
            cx += f.getlength(t)
        y += lh
    img.save(path)


def centered(lines, path, y_center):
    """lines: list of (text, font, alpha, tracking)"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hts = [f.size * 1.25 for _, f, _, _ in lines]
    y = y_center - sum(hts) / 2
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(txt)
    for (t, f, a, tr), h in zip(lines, hts):
        w = sum(f.getlength(c) + tr for c in t) - tr
        x = (W - w) / 2
        for c in t:
            d.text((x, y), c, font=f, fill=(255, 255, 255, a))
            x += f.getlength(c) + tr
        y += h
    sh = txt.copy()
    sh = Image.merge("RGBA", [Image.new("L", (W, H), 0)] * 3 + [txt.getchannel("A").point(lambda v: int(v * 0.75))])
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
    img = Image.alpha_composite(img, txt)
    img.save(path)


def gradient(path, top=True):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = g.load()
    for yy in range(H):
        if top:
            a = max(0, 1 - yy / 900) ** 1.6 * 150
        else:
            a = max(0, (yy - 900) / 1020) ** 1.6 * 170 + max(0, 1 - yy / 700) ** 2 * 90
        for xx in range(W):
            px[xx, yy] = (0, 0, 0, int(a))
    g.save(path)


def sh(cmd):
    print(" ".join(cmd)[:200], flush=True)
    subprocess.run(cmd, check=True)


# 1) cut + grade + gentle push-in for each segment
parts = []
for i, (clip, ss, du, _) in enumerate(SEGS):
    out = f"{WORK}/seg{i:02d}.mp4"
    parts.append(out)
    zoom = f"scale=w='trunc({W}*(1.0+0.05*t/{du})/2)*2':h=-2:eval=frame,crop={W}:{H}"
    vf = (f"fps={FPS},scale={W}:{H}:flags=lanczos,{zoom},"
          "eq=contrast=1.05:saturation=1.14:brightness=0.005:gamma=0.98,"
          "unsharp=5:5:0.4,format=yuv420p")
    sh(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-t", str(du), "-i", f"{SRC}/{clip}.mp4",
        "-vf", vf, "-af", "aresample=48000,highpass=f=80", "-ac", "2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-c:a", "aac", "-b:a", "256k", out])

# 2) timeline offsets
starts, t = [], 0.0
for i, s in enumerate(SEGS):
    starts.append(t)
    t += s[2] - XF
total = t + XF
print("TOTAL", total)

# 3) caption overlays
overlays = []  # (png, t_in, t_out)
gradient(f"{WORK}/grad_top.png", True)
gradient(f"{WORK}/grad_end.png", False)
for i, (clip, ss, du, cap) in enumerate(SEGS):
    a, b = starts[i] + 0.45, starts[i] + du - XF - 0.15
    if cap == "TITLE":
        p = f"{WORK}/cap{i:02d}.png"
        centered([("RESIPI MUDAH", font("SemiBold", 34), 220, 9),
                  ("Stew Ayam", font("ExtraBold", 132), 255, -2),
                  ("bersama Food Engine Cooven", font("Medium", 44), 235, 0)], p, 560)
        overlays += [(f"{WORK}/grad_top.png", 0, b + 0.2), (p, 0.25, b)]
    elif cap == "OUTRO":
        p = f"{WORK}/cap{i:02d}.png"
        centered([("Semudah ini memasak", font("Medium", 60), 235, 0),
                  ("menggunakan", font("Medium", 60), 235, 0),
                  ("Food Engine Cooven!", font("ExtraBold", 84), 255, -1)], p, 1330)
        overlays += [(f"{WORK}/grad_end.png", starts[i] + 0.2, total), (p, starts[i] + 0.5, total)]
    elif cap:
        p = f"{WORK}/cap{i:02d}.png"
        card(cap[0], cap[1], p)
        overlays += [(p, a, b)]

# 4) xfade chain + overlays + audio mix
inputs, fc = [], []
for p in parts:
    inputs += ["-i", p]
music = f"{WORK}/music.wav"
sh([sys.executable, "-I", os.path.join(os.path.dirname(__file__), "music.py"), music, f"{total + 0.5:.2f}"])
inputs += ["-i", music]
mi = len(parts)
for k, (png, _, _) in enumerate(overlays):
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", png]

v, a = "[0:v]", "[0:a]"
for i in range(1, len(parts)):
    off = starts[i]
    trans = "fade" if i not in (1, len(parts) - 1) else "fadeblack" if False else "fade"
    fc.append(f"{v}[{i}:v]xfade=transition={trans}:duration={XF}:offset={off:.3f}[v{i}]")
    fc.append(f"{a}[{i}:a]acrossfade=d={XF}[a{i}]")
    v, a = f"[v{i}]", f"[a{i}]"
for k, (png, tin, tout) in enumerate(overlays):
    idx = mi + 1 + k
    fo = max(tin + 0.3, tout - 0.3)
    fc.append(f"[{idx}:v]format=rgba,fade=in:st={tin:.3f}:d=0.3:alpha=1,"
              f"fade=out:st={fo:.3f}:d=0.3:alpha=1[o{k}]")
    fc.append(f"{v}[o{k}]overlay=0:0:shortest=1[w{k}]")
    v = f"[w{k}]"
fc.append(f"{v}fade=in:st=0:d=0.25,fade=out:st={total - 0.6:.3f}:d=0.6,format=yuv420p[vout]")
# original kitchen sound (ASMR texture) kept clear, music ducked underneath
fc.append(f"{a}loudnorm=I=-20:TP=-3:LRA=11,volume=1.0[amb]")
fc.append(f"[{mi}:a]aresample=48000,volume=0.30[mus]")
fc.append(f"[amb][mus]amix=inputs=2:normalize=0:duration=first,"
          f"afade=t=out:st={total - 1.2:.3f}:d=1.2,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")

final = f"{WORK}/Stew_Ayam_Food_Engine_Cooven.mp4"
sh(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc),
    "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.3f}",
    "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M", "-profile:v", "high", "-pix_fmt", "yuv420p",
    "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final])
print("DONE", final)
