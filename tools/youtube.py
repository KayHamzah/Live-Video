"""Render the long-form 16:9 YouTube edit from an edit list.

Usage: python3 youtube.py <edl.json> <transcript.jsonl> <frames.json> <source.mp4> <out.mp4>

frames.json is the per-second shot classification of the LIVE ([t, "person"|"inset"|"letter", pan_y, score]).
Writes <out>.mp4, <out>.srt and <out>.chapters.txt.

EDL segment keys:
  s, e      audio in/out in the LIVE (seconds)
  cut       [[a, b], ...] ranges inside the segment to drop (stumbles, asides)
  v         take video from here instead (B-roll); mapped 1:1 with the audio
  mode      force "pan" or "person" (default: from frames.json)
  raw       keep everything (no silence removal), for visual moments
  mute      silence the audio (raw visual)
  ch        chapter title; starts a new chapter at this segment
  pt        key point shown while this segment plays
"""
import hashlib, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from render import load_words, make_cleaner, ts, esc

W, H = 1920, 1080
PX, PW = 250, 608          # presenter panel x and width (720x1280 -> 608x1080)
RX = 1010                  # left edge of the text zone beside the panel
GAP = 0.55                 # pauses longer than this are cut
PRE, POST = 0.12, 0.22     # breathing room around speech
FONT = "Inter"

HIGHLIGHT = re.compile(
    r"^(\d+([.,]\d+)?|setengah|minit|jam|gram|ml|°c|steam|p1|broil|cooker|smart|cook|basmati|carrot|"
    r"plastik|masin|gula|garam|effortless|emergency|flip|penyepit|dehydrate|pizza|deep|fry|barbecue|grill|"
    r"oven|roast|sous|vide|slow|crisp|probe|putus|keras|lembut|kerak|serbuk)$", re.I)


def load_frames(path):
    return {t: (k, py) for t, k, py, s in json.load(open(path))}


def shot_at(frames, t):
    k, py = frames.get(int(t), ("person", None))
    return ("pan", py) if k in ("inset", "letter") else ("person", None)


def split_at_shot_changes(spans, seg, frames):
    """Cut a span where the LIVE switches between the presenter cam and the pan cam."""
    shift = seg["v"] - seg["s"] if "v" in seg else 0.0
    out = []
    for a, b in spans:
        cur = a
        for t in range(int(a + shift) + 1, int(b + shift) + 1):
            if shot_at(frames, t)[0] != shot_at(frames, t - 1)[0] and t - shift - cur > 0.3 and b - (t - shift) > 0.3:
                out.append([cur, t - shift])
                cur = t - shift
        out.append([cur, b])
    return out


def expand(edl, words, frames):
    """Turn segments into sub-clips with long pauses removed."""
    subs = []
    for si, seg in enumerate(edl["segments"]):
        cuts = seg.get("cut", [])
        keep = lambda t: not any(a <= t < b for a, b in cuts)
        if seg.get("raw") or seg.get("mute"):
            spans = [[seg["s"], seg["e"]]]
            for a, b in sorted(cuts):
                spans = [p for sp in spans for p in ([sp] if b <= sp[0] or a >= sp[1] else
                                                      [[sp[0], a], [b, sp[1]]])]
            spans = [sp for sp in spans if sp[1] - sp[0] > 0.3]
        else:
            ws = [w for w in words if seg["s"] <= w[0] < seg["e"] and keep(w[0]) and w[2].strip()]
            spans = []
            for s, e, w in ws:
                e = min(e, s + 1.2)  # Whisper sometimes stretches the last word over a pause
                if spans and s - spans[-1][1] <= GAP and not any(spans[-1][1] <= a < s for a, b in cuts):
                    spans[-1][1] = e
                else:
                    spans.append([s, e])
            spans = [[max(seg["s"], a - PRE), min(seg["e"], b + POST)] for a, b in spans]
            for a, b in cuts:  # never pad into a cut
                spans = [[sa if not (a <= sa < b) else b, sb if not (a < sb <= b) else a] for sa, sb in spans]
            merged = []
            for sp in spans:
                if merged and sp[0] <= merged[-1][1] + 0.05:
                    merged[-1][1] = max(merged[-1][1], sp[1])
                else:
                    merged.append(sp)
            spans = [sp for sp in merged if sp[1] - sp[0] > 0.25]
        if not seg.get("mode"):
            spans = split_at_shot_changes(spans, seg, frames)
        for j, (a, b) in enumerate(spans):
            vs = seg["v"] + (a - seg["s"]) if "v" in seg else a
            mode, py = shot_at(frames, vs + (b - a) / 2)
            if seg.get("mode"):
                mode = seg["mode"]
                if mode == "pan" and py is None:
                    py = seg.get("py", 437)
            if seg.get("py") is not None:
                py = seg["py"]
            subs.append({"as": a, "ae": b, "vs": vs, "mode": mode, "py": py, "seg": si,
                         "first": j == 0, "mute": seg.get("mute", False),
                         "chapter": seg.get("ch") if j == 0 else None})
    # Alternate the framing on consecutive jump cuts of the same shot type.
    level = 0
    for i, c in enumerate(subs):
        prev = subs[i - 1] if i else None
        jump = prev and prev["mode"] == c["mode"] and not c["chapter"]
        level = (1 - level) if jump else 0
        c["zoom"] = edl["segments"][c["seg"]].get("zoom") or ([1.0, 1.07][level] if c["mode"] == "pan"
                                                             else [1.0, 1.1][level])
    return subs


def vf_for(c, d, fade_in, fade_out):
    z = c["zoom"]
    if c["mode"] == "pan":
        vf = (f"crop=720:404:0:{c['py']},scale={int(W * z) // 2 * 2}:{int(1080 * z) // 2 * 2}:flags=lanczos,"
              f"crop={W}:{H}")
    else:
        pw, ph = int(PW * z) // 2 * 2, int(1080 * z) // 2 * 2
        vf = (f"scale={pw}:{ph}:flags=lanczos,crop={PW}:1080:(iw-{PW})/2:(ih-1080)*0.25,"
              f"pad={W}:{H}:{PX}:0:black")
    vf += ",eq=contrast=1.04:saturation=1.07,fps=30,format=yuv420p"
    if fade_in:
        vf += ",fade=t=in:st=0:d=0.3"
    if fade_out:
        vf += f",fade=t=out:st={max(d - 0.25, 0):.3f}:d=0.25"
    return vf


def line_split(ws, limit):
    """Split a phrase into balanced lines of at most ~limit characters."""
    text = " ".join(w[2] for w in ws)
    n = max(1, -(-len(text) // limit))
    target, out, cur, acc = len(text) / n, [], [], 0
    for j, w in enumerate(ws):
        cur.append(w)
        acc += len(w[2]) + 1
        if acc >= target * 0.9 and len(ws) - j - 1 >= 2 and not ws[j + 1][2].startswith("-"):
            out.append(cur)
            cur, acc = [], 0
    if cur:
        if out and len(cur) == 1 and len(" ".join(w[2] for w in out[-1] + cur)) <= limit + 6:
            out[-1] += cur  # no single-word orphan line
        else:
            out.append(cur)
    return out


def fmt(ws):
    parts = []
    for _, _, w in ws:
        core = w.lstrip("-")
        if HIGHLIGHT.match(core.strip("?")):
            w = "{\\fn" + FONT + " ExtraBold}" + esc(w) + "{\\fn" + FONT + " Medium}"
        else:
            w = esc(w)
        parts.append(w)
    return " ".join(parts).replace(" -", "-")


def build(edl, subs, words, total, outro):
    clean = make_cleaner(edl)
    ev, srt, chapters = [], [], []
    off = 0.0
    seg_spans = {}
    for c in subs:
        d = c.get("real", c["ae"] - c["as"])
        c["t0"], c["t1"] = off, off + d
        seg_spans.setdefault(c["seg"], []).append(c)
        off += d

    # Title card over the cold open.
    t = edl["title"]
    ev.append(f"Dialogue: 3,{ts(0.15)},{ts(t.get('dur', 5.0))},Title,,0,0,0,,{{\\fad(300,400)}}{esc(t['text'])}")
    if t.get("sub"):
        ev.append(f"Dialogue: 3,{ts(0.5)},{ts(t.get('dur', 5.0))},TitleSub,,0,0,0,,{{\\fad(300,400)}}{esc(t['sub'])}")

    # Chapter labels and key points.
    chap, chap_start = None, 0.0
    chap_ranges = []
    for si, seg in enumerate(edl["segments"]):
        cs = seg_spans.get(si)
        if not cs:
            continue
        if seg.get("ch"):
            if chap:
                chap_ranges.append((chap, chap_start, cs[0]["t0"]))
            chap, chap_start = seg["ch"], cs[0]["t0"]
            chapters.append((cs[0]["t0"], seg["ch"]))
        if seg.get("pt"):
            for c in cs:
                style = "PointR" if c["mode"] == "person" else "PointP"
                ev.append(f"Dialogue: 2,{ts(c['t0'])},{ts(c['t1'])},{style},,0,0,0,,{esc(seg['pt'])}")
    if chap:
        chap_ranges.append((chap, chap_start, total))
    for name, a, b in chap_ranges:
        for c in subs:
            if c["t1"] <= a or c["t0"] >= b:
                continue
            s0, s1 = max(a, c["t0"]), min(b, c["t1"])
            if c["mode"] == "person":
                ev.append(f"Dialogue: 1,{ts(s0)},{ts(s1)},ChapR,,0,0,0,,{esc(name.upper())}")
            elif s0 - a < 4.0:  # on the pan view, flash the chapter for a few seconds only
                ev.append(f"Dialogue: 1,{ts(s0)},{ts(min(s1, a + 4.0))},ChapP,,0,0,0,,{esc(name.upper())}")

    # Subtitles: phrases inside each sub-clip, never across a cut.
    n = 0
    for c in subs:
        if c["mute"]:
            continue
        cw = [(s - c["as"] + c["t0"], min(e, c["ae"]) - c["as"] + c["t0"], clean(s, w))
              for s, e, w in words if c["as"] - 0.05 <= s < c["ae"] - 0.06]
        cw = [w for w in cw if w[2]]
        groups, cur = [], []
        for w in cw:
            if cur and (w[0] - cur[-1][1] > 0.5 or len(cur) >= 14):
                groups.append(cur)
                cur = []
            cur.append(w)
        if cur:
            groups.append(cur)
        limit = 34 if c["mode"] == "person" else 52
        style = "SubR" if c["mode"] == "person" else "SubP"
        lines = [ln for g in groups for ln in line_split(g, limit)]
        for i, ln in enumerate(lines):
            s = ln[0][0]
            e = min(ln[-1][1] + 0.3, lines[i + 1][0][0] if i + 1 < len(lines) else c["t1"])
            txt = fmt(ln)
            plain = " ".join(w[2] for w in ln).replace(" -", "-")
            if i == 0 or re.search(r"[?]$", lines[i - 1][-1][2]):
                txt = re.sub(r"^((\{[^}]*\})?)(\w)", lambda m: m.group(1) + m.group(3).upper(), txt)
                plain = plain[:1].upper() + plain[1:]
            ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},{style},,0,0,0,,{txt}")
            n += 1
            srt.append(f"{n}\n{srt_ts(s)} --> {srt_ts(e)}\n{plain}\n")
    if outro:
        ev.append(f"Dialogue: 3,{ts(total)},{ts(total + outro[1])},Outro,,0,0,0,,{{\\fad(300,300)}}{esc(outro[0])}")

    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{FONT} ExtraBold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,3,28,0,2,160,160,250,1
Style: TitleSub,{FONT} Medium,40,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,1,0,3,14,0,2,200,200,170,1
Style: ChapR,{FONT} SemiBold,30,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,0,0,7,{RX},110,150,1
Style: PointR,{FONT} ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,{RX},140,230,1
Style: ChapP,{FONT} SemiBold,32,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,4,0,3,14,0,7,80,80,70,1
Style: PointP,{FONT} ExtraBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,9,80,80,70,1
Style: SubR,{FONT} Medium,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,1,{RX},110,120,1
Style: SubP,{FONT} Medium,46,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,3,14,0,2,200,200,60,1
Style: Outro,{FONT} ExtraBold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,5,200,200,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + "\n".join(ev) + "\n", "\n".join(srt), chapters


def srt_ts(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"


def main(edl_path, tr, fr, src, out):
    edl = json.load(open(edl_path, encoding="utf-8"))
    words = load_words(tr)
    frames = load_frames(fr)
    subs = expand(edl, words, frames)
    total = sum(c["ae"] - c["as"] for c in subs)
    outro = (edl["outro"], 3.0) if edl.get("outro") else None
    work = os.path.splitext(out)[0] + "_work"
    os.makedirs(work, exist_ok=True)
    base = os.path.splitext(out)[0]
    print(f"{len(subs)} cuts, {total / 60:.1f} min", flush=True)

    parts = []
    for i, c in enumerate(subs):
        d = c["ae"] - c["as"]
        nxt = subs[i + 1] if i + 1 < len(subs) else None
        vf = vf_for(c, d, fade_in=bool(c["chapter"]) or i == 0, fade_out=bool(nxt and nxt["chapter"]))
        vol = ",volume=0" if c["mute"] else ""
        af = (f"highpass=f=80,afftdn=nf=-25{vol},afade=t=in:st=0:d=0.04,afade=t=out:st={d - 0.06:.3f}:d=0.06,"
              f"aresample=48000,aformat=channel_layouts=stereo")
        key = hashlib.md5(f"{c['vs']:.3f}|{c['as']:.3f}|{d:.3f}|{vf}|{af}".encode()).hexdigest()[:12]
        p = os.path.join(work, f"c_{key}.mov")
        parts.append(p)
        if os.path.exists(p):
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{c['vs']:.3f}", "-t", f"{d:.3f}", "-i", src,
                        "-ss", f"{c['as']:.3f}", "-t", f"{d:.3f}", "-i", src, "-map", "0:v", "-map", "1:a",
                        "-vf", vf, "-af", af, "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
                        "-c:a", "pcm_s16le", p + ".tmp.mov"], check=True)
        os.replace(p + ".tmp.mov", p)
    # Each clip ends on a whole frame, so measure the real lengths and time the text from those.
    for c, p in zip(subs, parts):
        c["real"] = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", p], capture_output=True, text=True).stdout)
    total = sum(c["real"] for c in subs)
    ass, srt, chapters = build(edl, subs, words, total, outro)
    open(os.path.join(work, "subs.ass"), "w", encoding="utf-8").write(ass)
    open(base + ".srt", "w", encoding="utf-8").write(srt)
    open(base + ".chapters.txt", "w", encoding="utf-8").write(
        "\n".join(f"{int(t // 60)}:{int(t % 60):02d} {name}" for t, name in chapters) + "\n")
    if outro:
        p = os.path.join(work, "outro.mov")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", str(outro[1]), "-i",
                        f"color=black:s={W}x{H}:r=30", "-f", "lavfi", "-t", str(outro[1]), "-i",
                        "anullsrc=r=48000:cl=stereo", "-vf", "format=yuv420p", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "15", "-c:a", "pcm_s16le", p], check=True)
        parts.append(p)
        total += outro[1]
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-vf", f"ass={os.path.join(work, 'subs.ass')},fade=t=out:st={total - 0.5:.3f}:d=0.5",
                    "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st={total - 0.5:.3f}:d=0.5",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], check=True)
    print(f"{out}: {total / 60:.2f} min")


if __name__ == "__main__":
    main(*sys.argv[1:6])
