"""Cut one short from the live and write its HyperFrames project.

    python3 tools/make_short.py <source.mp4> <work_dir> [video-id ...]

For each video in specs.json (with data/<id>.words.json from asr_ranges.py):
  1. split each source range at pauses longer than MAX_GAP, so only speech is kept
  2. cut the pieces from the source with a natural grade baked in (CPU renders of the
     realtime grade are ~7x slower), light fan-noise reduction, 1080x1920 @ 30 fps
  3. join them with the concat filter and normalise speech to -14 LUFS
  4. write <id>/ : index.html (footage + gentle push-ins), compositions/text.html
     (bold hook, key-point labels, end card) and compositions/subs.html (subtitles)
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "template"
MAX_GAP = 0.30
PAD_IN, PAD_OUT = 0.06, 0.12
FPS = 30
END_CARD = 2.2
TITLE_END = 3.4
PIP_ORIGIN = "44% 22%"  # centre of the overhead close-up inset in the live layout

GRADE = (
    "eq=gamma=1.08:contrast=1.05:saturation=1.04,"
    "huesaturation=colors=m+b:saturation=-0.3:strength=1,"
    "colorbalance=rm=0.03:bm=-0.03:rh=0.015:bh=-0.02,"
    "curves=all='0/0.015 0.5/0.52 1/0.985',unsharp=5:5:0.35"
)
DENOISE = "highpass=f=80,afftdn=nf=-28:nr=8"

# Whisper spellings of the brand and terms, fixed for on-screen text (audio is untouched).
GLOBAL_FIX = [
    ("food in jengkuven", "Cooven"), ("food engine cooven", "Cooven"), ("food engine kuven", "Cooven"),
    ("food engine coven", "Cooven"), ("food engine cover", "Cooven"), ("food agent coven", "Cooven"),
    ("food agent kuvert", "Cooven"), ("food energy kuvert", "Cooven"), ("food energy kuburn", "Cooven"),
    ("food engine kuven", "Cooven"), ("food engine kuban", "Cooven"), ("food engine kubel", "Cooven"),
    ("food engine kuman", "Cooven"), ("food engine kubun", "Cooven"), ("food engine kuvert", "Cooven"),
    ("food engine cuven", "Cooven"), ("food engine cuvert", "Cooven"), ("food engine oven", "Cooven"),
    ("food engine proven", "Cooven"), ("food injil cover", "Cooven"), ("food engine", "Cooven"),
    ("pot engine coven", "Cooven"), ("pot aging cover", "Cooven"), ("4g cooper", "Cooven"), ("4g cover", "Cooven"),
    ("4 engine cuven", "Cooven"), ("4 engine", "Cooven"), ("for engine cover", "Cooven"),
    ("kuven", "Cooven"), ("kuvert", "Cooven"), ("coven", "Cooven"), ("cuven", "Cooven"), ("cuvert", "Cooven"),
    ("kuburn", "Cooven"), ("kubun", "Cooven"), ("kuban", "Cooven"), ("kubel", "Cooven"), ("cooven", "Cooven"),
    ("food agent cooven", "Cooven"), ("food engine cooker", "Cooven"), ("food engine cook", "Cooven"),
    ("food engine cooven", "Cooven"), ("food engine kooven", "Cooven"),
    ("pot ujin kooven", "Cooven"), ("foodijing cover", "Cooven"), ("kooven", "Cooven"),
    ("prop", "probe"), ("prop,", "probe,"), ("kee", "K"), ("singki", "sinki"), ("browning sugar", "brown sugar"),
    ("seikur", "seekor"), ("seko", "seekor"), ("eko", "ekor"), ("cucu", "cucur"), ("diorang", "dia orang"),
]


def norm(t):
    return re.sub(r"[^\w]", "", t.lower())


def apply_fixes(words, fixes):
    """Replace token sequences (matched case- and punctuation-insensitively).

    The replacement words share the matched span's time evenly; the last matched
    token's trailing punctuation is kept."""
    for src, dst in fixes:
        s, d = src.split(), dst.split()
        out, i = [], 0
        while i < len(words):
            if [norm(w[2]) for w in words[i:i + len(s)]] == [norm(x) for x in s]:
                span = words[i:i + len(s)]
                a, b = span[0][0], span[-1][1]
                tail = re.search(r"[.,?!]+$", span[-1][2])
                step = (b - a) / len(d)
                for k, t in enumerate(d):
                    text = t + (tail.group(0) if tail and k == len(d) - 1 and not t[-1] in ".,?!" else "")
                    out.append([round(a + k * step, 3), round(a + (k + 1) * step, 3), text])
                i += len(s)
            else:
                out.append(words[i])
                i += 1
        words = out
    return words


def join_hyphens(words):
    out = []
    for w in words:
        if w[2].startswith("-") and out:
            out[-1] = [out[-1][0], w[1], out[-1][2] + w[2]]
        else:
            out.append(list(w))
    return out


def plan(video, ranges):
    """Pieces (source in/out + words) for one video: pauses and 'skip' spans removed."""
    skips = video.get("skip", [])

    def skipped(w):
        mid = (w[0] + w[1]) / 2
        return any(a <= mid <= b for a, b in skips)

    pieces = []
    for spec_range, rg in zip(video["ranges"], ranges):
        focus = spec_range[2] if len(spec_range) > 2 else "frame"
        group = []
        for w in rg["words"]:
            if skipped(w):
                if group:
                    pieces.append((group, focus))
                group = []
                continue
            if group and w[0] - group[-1][1] > MAX_GAP:
                pieces.append((group, focus))
                group = []
            group.append(w)
        if group:
            pieces.append((group, focus))
    out = []
    for group, focus in pieces:
        src_in = max(0.0, group[0][0] - PAD_IN)
        src_out = group[-1][1] + PAD_OUT
        out.append({"in": round(src_in, 3), "out": round(src_out, 3), "words": group, "focus": focus})
    # padding must never pull a skipped word back in
    for a, b in zip(out, out[1:]):
        if a["out"] > b["in"] and a["in"] < b["in"]:
            mid = round((a["words"][-1][1] + b["words"][0][0]) / 2, 3)
            a["out"], b["in"] = min(a["out"], mid), max(b["in"], mid)
    return out


def run(cmd):
    subprocess.run(cmd, check=True)


def probe_duration(path, stream="v"):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", "stream=duration",
        "-of", "csv=p=0", str(path)]).decode().strip())


def cut(source, pieces, work, out_mp4):
    work.mkdir(parents=True, exist_ok=True)
    for f in work.glob("p*.mov"):
        f.unlink()
    for i, p in enumerate(pieces):
        dur = p["out"] - p["in"]
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{p['in']:.3f}", "-i", str(source), "-t", f"{dur:.3f}",
             "-vf", f"fps={FPS},scale=1080:1920:flags=lanczos,setsar=1,{GRADE}",
             "-af", f"aresample=48000,{DENOISE},afade=t=in:d=0.02,afade=t=out:st={max(0, dur - 0.03):.3f}:d=0.03",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-g", str(FPS), "-pix_fmt", "yuv420p",
             "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
             "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", str(work / f"p{i:02d}.mov")])
    files = sorted(work.glob("p*.mov"))
    real = [probe_duration(f) for f in files]
    n = len(files)
    fc = "".join(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];[{i}:a]asetpts=PTS-STARTPTS[a{i}];" for i in range(n))
    fc += "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a];"
    fc += "[a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[an]"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
    for f in files:
        cmd += ["-i", str(f)]
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[an]", "-c:v", "libx264", "-preset", "fast",
            "-crf", "17", "-g", str(FPS), "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out_mp4)]
    run(cmd)
    return real


def subtitle_lines(words, max_chars=30):
    """Short single lines. A sentence (ended by punctuation, a pause or a cut) is split
    into the fewest lines that fit, with the breaks balanced so no word hangs alone."""
    sentences, cur = [], []
    for w in words:
        if cur and (w["start"] - cur[-1]["end"] > 0.25 or w["piece"] != cur[-1]["piece"]):
            sentences.append(cur)
            cur = []
        cur.append(w)
        if w["text"][-1] in ".?!":
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    lines = []
    for i, sent in enumerate(sentences):
        if i == 0 or sentences[i - 1][-1]["text"][-1] in ".?!":
            sent[0]["text"] = sent[0]["text"][0].upper() + sent[0]["text"][1:]
        total = len(" ".join(w["text"] for w in sent))
        n = max(1, -(-total // max_chars))
        # break before the word whose centre passes each 1/n mark of the sentence's length
        line, pos, k = [], 0, 1
        for w in sent:
            centre = pos + len(w["text"]) / 2
            if line and k < n and centre > total * k / n:
                lines.append(line)
                line, k = [], k + 1
            line.append(w)
            pos += len(w["text"]) + 1
        lines.append(line)
    return lines


def build(video, source, work_root):
    ranges = json.loads((ROOT / "data" / f"{video['id']}.words.json").read_text())
    fixes = GLOBAL_FIX + [tuple(f) for f in video.get("fix", [])]
    for rg in ranges:
        rg["words"] = apply_fixes(join_hyphens(rg["words"]), fixes)
        rg["words"] = [w for w in rg["words"] if w[2]]
    pieces = plan(video, ranges)
    proj = ROOT / video["id"]
    (proj / "assets").mkdir(parents=True, exist_ok=True)
    work = work_root / video["id"]
    if os.environ.get("LAYOUT_ONLY") and (proj / "assets" / "clip.mp4").exists() and len(list(work.glob("p*.mov"))) == len(pieces):
        real = [probe_duration(f) for f in sorted(work.glob("p*.mov"))]
    else:
        real = cut(source, pieces, work, proj / "assets" / "clip.mp4")

    # words on the output timeline
    words, starts, t = [], [], 0.0
    for k, (p, d) in enumerate(zip(pieces, real)):
        starts.append(round(t, 3))
        for s, e, text in p["words"]:
            words.append({"text": text, "start": round(t + s - p["in"], 3), "end": round(t + e - p["in"], 3), "piece": k})
        t += d
    clip_dur = round(t, 3)
    total = round(clip_dur + END_CARD, 3)

    # camera: a slow push on every piece; overhead close-ups punch in on the inset
    cam = ['tl.set("#cam", { scale: 1, transformOrigin: "50% 42%" }, 0);']
    for k, (p, s, d) in enumerate(zip(pieces, starts, real)):
        if p["focus"] == "pip":
            cam.append(f'tl.set("#cam", {{ scale: 1.3, transformOrigin: "{PIP_ORIGIN}" }}, {s:.3f});')
            cam.append(f'tl.to("#cam", {{ scale: 1.36, duration: {d - 0.04:.3f}, ease: "none" }}, {s:.3f});')
        else:
            a, b = (1.0, 1.035) if k % 2 == 0 else (1.035, 1.0)
            cam.append(f'tl.set("#cam", {{ scale: {a}, transformOrigin: "50% 42%" }}, {s:.3f});')
            cam.append(f'tl.to("#cam", {{ scale: {b}, duration: {d - 0.04:.3f}, ease: "none" }}, {s:.3f});')

    # key-point labels: shown from the first time their word is spoken, never under the hook title
    points_html, points_js, busy_until = [], [], TITLE_END + 0.2
    for i, (label, word) in enumerate(video.get("points", [])):
        hit = next((w for w in words if norm(w["text"]).startswith(norm(word))), None)
        if not hit:
            print(f"  ! point '{label}': word '{word}' not spoken", file=sys.stderr)
            continue
        start = round(max(hit["start"], busy_until), 3)
        dur = round(min(3.2, clip_dur - start - 0.2), 3)
        if dur < 1.2:
            continue
        busy_until = start + dur + 0.3
        points_html.append(f'    <div id="pt-{i}" class="clip point" data-start="{start}" data-duration="{dur}"><span>{html.escape(label)}</span></div>')
        points_js.append(f'  tl.fromTo("#pt-{i} span", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.45, ease: "power2.out" }}, {start});')
        points_js.append(f'  tl.to("#pt-{i} span", {{ opacity: 0, duration: 0.35, ease: "power2.in" }}, {start + dur - 0.35:.3f});')

    # subtitles
    subs_html, subs_js = [], []
    lines = subtitle_lines(words)
    for i, line in enumerate(lines):
        nxt = lines[i + 1][0]["start"] if i + 1 < len(lines) else line[-1]["end"] + 0.3
        start = round(max(0.1, line[0]["start"] - 0.05), 3)
        end = round(min(nxt - 0.03, line[-1]["end"] + 0.3, clip_dur), 3)
        end = max(end, start + 0.35)
        text = " ".join(w["text"] for w in line)
        subs_html.append(f'    <div id="sb-{i}" class="clip sub" data-start="{start}" data-duration="{round(end - start, 3)}"><span>{html.escape(text)}</span></div>')
        subs_js.append(f'  tl.fromTo("#sb-{i} span", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.1, ease: "power1.out" }}, {start});')

    title_html = "<br />".join(html.escape(x) for x in video["title"].split("\n"))
    fill = {
        "%ID%": video["id"], "%SERIES%": html.escape(video["series"]), "%TITLE%": title_html,
        "%CLIP_DUR%": str(clip_dur), "%TOTAL%": str(total), "%END_START%": str(clip_dur),
        "%CAM%": "\n      ".join(cam), "%POINTS%": "\n".join(points_html), "%POINTS_JS%": "\n".join(points_js),
        "%SUBS%": "\n".join(subs_html), "%SUBS_JS%": "\n".join(subs_js), "%SUBS_DUR%": str(clip_dur),
        "%TITLE_END%": str(TITLE_END), "%END_DUR%": str(END_CARD), "%END_TEXT%": html.escape(video.get("end", "Follow Kay sekarang untuk lebih banyak tips")),
    }
    for src in TEMPLATE.rglob("*"):
        if src.is_dir():
            continue
        dst = proj / src.relative_to(TEMPLATE)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix in (".html", ".json"):
            text = src.read_text()
            for k, v in fill.items():
                text = text.replace(k, v)
            dst.write_text(text)
        else:
            shutil.copy(src, dst)
    (proj / "edit.json").write_text(json.dumps({
        "pieces": [{"src_in": p["in"], "src_out": p["out"], "out_start": s, "out_dur": round(d, 3)}
                   for p, s, d in zip(pieces, starts, real)],
        "subtitles": [{"start": l[0]["start"], "end": l[-1]["end"], "text": " ".join(w["text"] for w in l)} for l in lines],
        "duration": total,
    }, ensure_ascii=False, indent=1))
    print(f"{video['id']}: {len(pieces)} cuts, {clip_dur:.1f}s + {END_CARD}s end = {total:.1f}s", flush=True)
    return total


def main():
    source, work_root, only = Path(sys.argv[1]), Path(sys.argv[2]), set(sys.argv[3:])
    videos = json.loads((ROOT / "specs.json").read_text())["videos"]
    for v in videos:
        if not only or v["id"] in only:
            build(v, source, work_root)


if __name__ == "__main__":
    main()
