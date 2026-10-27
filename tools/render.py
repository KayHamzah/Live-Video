"""Render a premium-minimal Cooven short from the LIVE source.

Usage: python3 render.py <spec.json> <transcript.jsonl> <source.mp4> <out.mp4>

spec = {
  "hook": "AYAM JUICY, TAK KERING?",           # bold title, shown 0-3s
  "cta": "Simpan video ini untuk rujukan.",     # optional, last ~3s
  "clips": [{"s": 120.0, "e": 131.5, "zoom": 1.15, "label": "optional caption"}],
  "fix": {"wrong": "right"}                    # optional subtitle word fixes
}
"""
import json, re, subprocess, sys, os

W, H = 1080, 1920
FONT = "Inter"

NO_BREAK_AFTER = {"lepas", "dan", "yang", "dengan", "nak", "untuk", "dekat", "macam", "the", "satu", "setengah", "kita"}
PROPER = {"Korea", "Cooven", "Food", "Engine", "Holland", "Singapore", "K", "P1", "Thermomix", "Rabu"}

# Whisper's recurring mishearings in this LIVE (lowercase core word -> correct spelling).
FIXES = {
    "kuven": "Cooven", "kubun": "Cooven", "kubur": "Cooven", "kuburn": "Cooven", "coover": "Cooven",
    "kupul": "Cooven", "kuvert": "Cooven", "injil": "Food Engine", "ijin": "Engine", "uji": "Engine",
    "bihut": "bihun", "bihul": "bihun", "bimun": "bihun", "bihon": "bihun", "mihun": "bihun",
    "dihut": "bihun", "bihan": "bihun", "dihun": "bihun", "lihung": "bihun",
    "kk": "K", "kee": "K", "kim": "K", "key": "K",
    "singapong": "Singapore", "singapau": "Singapore", "singapura": "Singapore",
    "dadah": "dadar", "dada": "dadar", "dadal": "dadar",
    "ladi": "lada", "hollum": "Holland", "brownie": "brown", "mereceh": "merecik",
    "goring": "goreng", "tukat": "Sukat", "tukatan": "sukatan", "jai": "je",
    "copkan": "chopkan", "kutus": "putus", "tastik": "plastik", "kuka": "cooker",
    "suvit": "sous vide", "krebs": "crisp", "rose": "roast", "osen": "onsen",
    "fomentation": "fermentation", "food": "Food", "engine": "Engine", "port": "pot", "flick": "flip",
    "ulit": "uli", "termomix": "Thermomix", "sawadu": "sourdough", "dibu": "bihun", "boring": "goreng",
    "sudik": "sudip", "bukus": "bungkus", "relay": "berderai", "kebeja": "depan meja", "percit": "percik", "seko": "seekor",
}


def load_words(path):
    words = []
    for line in open(path, encoding="utf-8"):
        seg = json.loads(line)
        for s, e, w in seg["words"]:
            words.append((s, e, w.strip()))
    return words


def ts(t):
    t = max(t, 0)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def esc(t):
    return t.replace("{", "(").replace("}", ")").replace("\n", "\\N")


def make_cleaner(spec):
    fix = {**FIXES, **{k.lower(): v for k, v in spec.get("fix", {}).items()}}
    fix_at = {round(float(k), 2): v for k, v in spec.get("fix_at", {}).items()}

    def clean(s, w):
        if round(s, 2) in fix_at:
            return fix_at[round(s, 2)]
        m = re.match(r"^(-?)(.*?)([.,?!]*)$", w)
        dash, core, punct = m.groups()
        core = fix.get(core.lower(), core)
        if core not in PROPER and not core.isupper():
            core = core.lower()
        return dash + core + ("?" if "?" in punct else "")
    return clean


def build_ass(spec, words, total):
    clean = make_cleaner(spec)

    # Remap words in each clip to the output timeline; a phrase never spans a cut.
    lines, offset = [], 0.0
    for c in spec["clips"]:
        cw = []
        for s, e, w in words:
            if c["s"] - 0.08 <= s < c["e"] - 0.08:
                w = clean(s, w)
                if w:
                    cw.append((s - c["s"] + offset, min(e, c["e"]) - c["s"] + offset, w))
        if c.get("mute"):
            cw = []
        groups, cur = [], []
        for wd in cw:  # split on pauses first
            if cur and wd[0] - cur[-1][1] > 0.7:
                groups.append(cur)
                cur = []
            cur.append(wd)
        if cur:
            groups.append(cur)
        for g in groups:  # then into balanced lines of <= ~28 chars
            n = -(-len(" ".join(x[2] for x in g)) // 28)
            target = len(" ".join(x[2] for x in g)) / n
            ln, acc, first = [], 0, True
            for j, wd in enumerate(g):
                ln.append(wd)
                acc += len(wd[2]) + 1
                left = len(g) - j - 1
                if acc >= target * 0.92 and left >= 2 and wd[2].lower() not in NO_BREAK_AFTER \
                        and not g[j + 1][2].startswith("-"):
                    lines.append((ln, first))
                    ln, acc, first = [], 0, False
            if ln:
                lines.append((ln, first))
        offset += c["e"] - c["s"]
        lines.append(offset)  # cut marker: phrases end at the cut
    hook_end = spec.get("hook_dur", 3.0)
    cta = spec.get("cta")
    tail = spec["clips"][-1]
    cta_start = total - spec.get("cta_dur", tail["e"] - tail["s"] if tail.get("mute") else 3.2)

    ev = []
    # Hook: big bold white on black box, safe zone below the machine.
    ev.append(f"Dialogue: 2,{ts(0)},{ts(hook_end)},Hook,,0,0,0,,{{\\fad(150,250)}}{esc(spec['hook'])}")
    if spec.get("sub"):
        ev.append(f"Dialogue: 2,{ts(0.25)},{ts(hook_end)},HookSub,,0,0,0,,{{\\fad(200,250)}}{esc(spec['sub'])}")
    for c_off, c in _clip_offsets(spec):
        if c.get("label"):
            ev.append(f"Dialogue: 1,{ts(c_off + 0.1)},{ts(c_off + min(2.8, c['e'] - c['s']))},Label,,0,0,0,,{{\\fad(150,200)}}{esc(c['label'])}")
    if cta:
        ev.append(f"Dialogue: 2,{ts(cta_start)},{ts(total)},Hook,,0,0,0,,{{\\fad(250,0)}}{esc(cta)}")
    for i, ln in enumerate(lines):
        if isinstance(ln, float):
            continue
        ln, first = ln
        s = ln[0][0]
        nxt = lines[i + 1]
        e = min(ln[-1][1] + 0.3, nxt if isinstance(nxt, float) else nxt[0][0][0])
        if cta and e > cta_start + 0.3:
            continue  # keep screen clean while hook/CTA is up
        text = " ".join(x[2] for x in ln).replace(" -", "-")
        if first:
            text = text[:1].upper() + text[1:]
        text = re.sub(r"\? (\w)", lambda m: "? " + m.group(1).upper(), text)
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Sub,,0,0,0,,{esc(text)}")

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{FONT} ExtraBold,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,3,26,0,2,90,90,520,1
Style: HookSub,{FONT} Medium,44,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,1,0,3,14,0,2,120,120,430,1
Style: Label,{FONT} SemiBold,46,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,2,0,3,14,0,8,80,80,140,1
Style: Sub,{FONT} Medium,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,3,16,0,2,110,110,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + "\n".join(ev) + "\n"


def _clip_offsets(spec):
    off = 0.0
    for c in spec["clips"]:
        yield off, c
        off += c["e"] - c["s"]


def detect_inset(src, t):
    """Find the top edge of the 720x405 top-down pan view (PIP or letterboxed)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(1280, 720).astype(float)
    d = np.abs(np.diff(img, axis=0)).mean(axis=1)  # d[y] = edge between row y and y+1
    best = max(range(0, 1280 - 406), key=lambda y: d[y] + d[y + 405] if y > 0 else d[y + 405])
    return best + 1 if best > 0 else 0


PAN_Y = 380  # where the enlarged pan view sits on the 1080x1920 canvas


def render(spec, words, src, out):
    clips = spec["clips"]
    total = sum(c["e"] - c["s"] for c in clips)
    work = os.path.splitext(out)[0] + "_work"
    os.makedirs(work, exist_ok=True)
    ass = os.path.join(work, "subs.ass")
    open(ass, "w", encoding="utf-8").write(build_ass(spec, words, total))

    parts = []
    for i, c in enumerate(clips):
        d = c["e"] - c["s"]
        z = c.get("zoom", 1.0)
        # Gentle push-in: from 1.0 (or z0) to z over the clip.
        z0 = c.get("zoom_from", 1.0 if z > 1.0 else z)
        fx, fy = c.get("fx", 0.5), c.get("fy", 0.5)
        zexpr = f"({z0}+({z}-{z0})*min(t/{d:.3f}\\,1))"
        if c.get("mode") == "pan":
            py = c.get("py")
            if py is None:
                ys = sorted(detect_inset(src, c.get("v", c["s"]) + d * k) for k in (0.2, 0.5, 0.8))
                py = ys[1]
                c["py"] = py
            ph = 840  # centre 520x404 of the 720x405 top view -> 1080x840
            vf = (f"crop=520:404:{c.get('px', 100)}:{py},scale={W}:{ph}:flags=lanczos,"
                  f"scale=w='trunc({W}*{zexpr}/2)*2':h='trunc({ph}*{zexpr}/2)*2':eval=frame:flags=bicubic,"
                  f"crop={W}:{ph}:x='(iw-{W})*{fx}':y='(ih-{ph})*{fy}',"
                  f"pad={W}:{H}:0:{PAN_Y}:black,"
                  f"eq=contrast=1.04:saturation=1.08,fps=30,format=yuv420p")
        else:
            vf = (f"scale={W}:{H}:flags=lanczos,"
                  f"scale=w='trunc({W}*{zexpr}/2)*2':h='trunc({H}*{zexpr}/2)*2':eval=frame:flags=bicubic,"
                  f"crop={W}:{H}:x='(iw-{W})*{fx}':y='(ih-{H})*{fy}',"
                  f"eq=contrast=1.04:saturation=1.06,fps=30,format=yuv420p")
        mute = ",volume=0" if c.get("mute") else ""
        af = (f"highpass=f=80,afftdn=nf=-25{mute},"
              f"afade=t=in:st=0:d=0.06,afade=t=out:st={d - 0.08:.3f}:d=0.08,"
              f"aresample=48000,aformat=channel_layouts=stereo")
        p = os.path.join(work, f"p{i:02d}.mp4")
        vs = c.get("v", c["s"])
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{vs:.3f}", "-t", f"{d:.3f}", "-i", src,
                        "-ss", f"{c['s']:.3f}", "-t", f"{d:.3f}", "-i", src,
                        "-map", "0:v", "-map", "1:a", "-vf", vf, "-af", af, "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-c:a", "pcm_s16le", p.replace(".mp4", ".mov")], check=True)
        parts.append(p.replace(".mp4", ".mov"))

    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    fade = f"fade=t=in:st=0:d=0.25,fade=t=out:st={total - 0.4:.3f}:d=0.4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-vf", f"ass={ass},{fade}",
                    "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={total - 0.4:.3f}:d=0.4",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-profile:v", "high",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000", out], check=True)
    return total


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    words = load_words(sys.argv[2])
    print(f"{sys.argv[4]}: {render(spec, words, sys.argv[3], sys.argv[4]):.1f}s")
