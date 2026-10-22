"""Write PLAN.md: the timestamped edit plan of every short, from specs.json + <id>/edit.json.

Usable on its own to rebuild any short in another editor (CapCut, Premiere, etc.).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def ts(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(int(m), 60)
    return f"{h}:{m:02d}:{s:05.2f}" if h else f"{m:02d}:{s:05.2f}"


def main():
    videos = json.loads((ROOT / "specs.json").read_text())["videos"]
    out = ["# Pelan edit: short video daripada rakaman live", "",
           "Masa sumber (`sumber`) ialah kedudukan dalam rakaman live 87 minit. "
           "Masa output (`output`) ialah kedudukan dalam short video. "
           "Gaya: teks hitam & putih, Inter; tajuk/hook bold (0–3.4 s); subtitle ringan, satu baris pendek; "
           "zoom-in halus pada setiap potongan; end card hitam 2.2 s.", ""]
    for v in videos:
        e = ROOT / v["id"] / "edit.json"
        if not e.exists():
            continue
        edit = json.loads(e.read_text())
        title = v["title"].replace("\n", " ")
        out += [f"## {v['id']}: {title}", "",
                f"- Siri: {v['series']}",
                f"- Tempoh: {edit['duration']:.1f} s",
                f"- Hook / tajuk (bold, 0.0–3.4 s): **{title}**",
                f"- Label isi penting: " + "; ".join(p[0] for p in v.get("points", [])), "",
                "| # | Sumber | Output | Tempoh |", "|---|---|---|---|"]
        for i, p in enumerate(edit["pieces"], 1):
            out.append(f"| {i} | {ts(p['src_in'])} – {ts(p['src_out'])} | {ts(p['out_start'])} | {p['out_dur']:.2f} s |")
        out += ["", "<details><summary>Subtitle</summary>", "", "| Output | Teks |", "|---|---|"]
        for s in edit["subtitles"]:
            out.append(f"| {ts(s['start'])} – {ts(s['end'])} | {s['text']} |")
        out += ["", "</details>", ""]
    (ROOT / "PLAN.md").write_text("\n".join(out))
    print("wrote PLAN.md")


if __name__ == "__main__":
    main()
