"""Write a CapCut-ready editing plan (Markdown) from the specs.

Usage: python3 make_plan.py <transcript.jsonl> <out.md>
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from render import load_words, make_cleaner


def mmss(t):
    return f"{int(t // 60):02d}:{t % 60:04.1f}"


words = load_words(sys.argv[1])
out = ["# Food Engine Cooven: Editing Plan for 10 Shorts", "",
       "Source: rakaman LIVE (48:37, 720×1280). Every timestamp below refers to that LIVE recording.",
       "Ready-made MP4s are in `output/`. This plan lets you rebuild or tweak any video in CapCut.", "",
       "## Gaya standard (semua video)", "",
       "- Kanvas 9:16, 1080 × 1920, 30 fps.",
       "- **Shot presenter**: penuh skrin, zoom-in perlahan 4–12% sepanjang klip (keyframe *Scale*).",
       "- **Shot kuali (top view)**: crop bahagian kamera atas (kotak landskap), besarkan selebar skrin, "
       "letak di atas latar HITAM (y ≈ 380–1220 px). Teks di ruang hitam.",
       "- Font: **Inter**. Hook = Inter ExtraBold 88 px, putih atas kotak hitam, tengah bawah (≈ y 1300). "
       "Subtitle = Inter Medium 54 px, putih atas kotak hitam separa lutsinar, ≈ y 1560. "
       "Label langkah = Inter SemiBold 46 px, hitam atas kotak putih, tengah atas.",
       "- Warna hitam & putih sahaja. Tiada sticker, emoji atau transition berlebihan; cut biasa + fade 0.25 s di awal/akhir.",
       "- Audio: suara asal sahaja, *Reduce noise* ON, loudness ≈ -14 LUFS. Muzik latar pilihan (instrumental lembut, -25 dB).",
       "- Klip **senyap** = B-roll tanpa suara di hujung untuk CTA.", ""]
for p in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "specs", "*.json"))):
    spec = json.load(open(p, encoding="utf-8"))
    clean = make_cleaner(spec)
    total = sum(c["e"] - c["s"] for c in spec["clips"])
    name = os.path.basename(p)[:-5]
    out += [f"## {name[:2]}. {spec['title']}  ({total:.0f} s)", "",
            f"**Hook (0–3 s):** **{spec['hook'].replace(chr(92) + 'N', ' ')}**  ",
            f"**Sub-hook:** {spec.get('sub', '-')}  ",
            f"**CTA (hujung):** {spec.get('cta', '-')}  ",
            f"**Fail siap:** `output/{name}.mp4`", "",
            "| # | Masa video | Audio dari LIVE | Visual dari LIVE | Shot | Label atas skrin | Dialog / subtitle |",
            "|---|---|---|---|---|---|---|"]
    t = 0.0
    for i, c in enumerate(spec["clips"], 1):
        d = c["e"] - c["s"]
        vs = c.get("v", c["s"])
        said = " ".join(w for w in (clean(s, w) for s, e, w in words if c["s"] - 0.08 <= s < c["e"] - 0.08) if w)
        said = said.replace(" -", "-")
        if c.get("mute"):
            said, audio = "*(senyap, B-roll untuk CTA)*", "-"
        else:
            audio = f"{mmss(c['s'])}–{mmss(c['e'])}"
        shot = "Kuali (top view)" if c.get("mode") == "pan" else "Presenter"
        shot += f", zoom {c.get('zoom', 1.0):.2f}×" if c.get("zoom", 1.0) != 1.0 else ""
        out.append(f"| {i} | {mmss(t)}–{mmss(t + d)} | {audio} | {mmss(vs)}–{mmss(vs + d)} | {shot} | "
                   f"{c.get('label', '')} | {said} |")
        t += d
    out.append("")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out))
