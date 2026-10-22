"""Write compositions/captions.html from data/captions.json.

Groups are written into the HTML (not built at runtime) so each one is an
editable, timed element in Studio. Re-run after changing data/captions.json:

    python3 tools/build_captions.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_WORDS = 4
MIN_GAP = 0.15  # a pause this long starts a new group
LEAD = 0.08  # group shows slightly before its first word
TAIL = 0.25  # and lingers after its last word, never past the next group
# Words that stay gold for the whole group: the numbers and objects the tips hinge on.
KEYWORDS = {
    "tulang", "penat.", "mengemas", "rajin", "membasuh", "baking", "paper", "cuci",
    "orange", "serai.", "kayu", "manis", "tebal", "dada", "77", "180", "minyak.",
    "serap", "rosak", "siap", "normal", "kicap,", "brown", "sugar", "sendiri", "Jimat", "duit",
}


def groups_from(words):
    groups, cur = [], []
    for i, w in enumerate(words):
        if cur and (
            len(cur) >= MAX_WORDS
            or w["beat"] != cur[-1]["beat"]
            or w.get("cut") != cur[-1].get("cut")
            or w["start"] - cur[-1]["end"] >= MIN_GAP
            or cur[-1]["text"][-1] in ".,?!"
        ):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def main():
    words = json.loads((ROOT / "data/captions.json").read_text())
    groups = groups_from(words)
    markup, tweens = [], []
    for gi, g in enumerate(groups):
        nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else g[-1]["end"] + TAIL
        start = max(0.1, round(g[0]["start"] - LEAD, 3))
        end = round(min(nxt - LEAD, g[-1]["end"] + TAIL), 3)
        end = max(end, start + 0.3)
        spans = []
        for wi, w in enumerate(g):
            cls = "cap-word key" if w["text"] in KEYWORDS else "cap-word"
            spans.append(f'<span id="cw-{gi}-{wi}" class="{cls}">{html.escape(w["text"])}</span>')
            ws = round(w["start"] - start, 3)
            we = round(max(w["end"], w["start"] + 0.12) - start, 3)
            tweens.append(f'  tl.to("#cw-{gi}-{wi}", {{ scale: 1.06, color: GOLD, duration: 0.08, ease: "power2.out" }}, {start + ws:.3f});')
            if w["text"] not in KEYWORDS:
                tweens.append(f'  tl.to("#cw-{gi}-{wi}", {{ scale: 1, color: CREAM, duration: 0.12, ease: "power1.inOut" }}, {start + we:.3f});')
            else:
                tweens.append(f'  tl.to("#cw-{gi}-{wi}", {{ scale: 1, duration: 0.12, ease: "power1.inOut" }}, {start + we:.3f});')
        markup.append(
            f'    <div id="cg-{gi}" class="clip cap-group" data-start="{start}" data-duration="{round(end - start, 3)}">'
            f'<div class="cap-line">{" ".join(spans)}</div></div>'
        )
        tweens.append(f'  tl.fromTo("#cg-{gi} .cap-line", {{ opacity: 0, y: 18 }}, {{ opacity: 1, y: 0, duration: 0.14, ease: "power3.out" }}, {start:.3f});')
        tweens.append(f'  tl.to("#cg-{gi} .cap-line", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {max(start, end - 0.1):.3f});')
    duration = round(groups[-1][-1]["end"] + TAIL + 0.5, 3)
    out = TEMPLATE.replace("%DURATION%", str(duration)).replace("%GROUPS%", "\n".join(markup)).replace("%TWEENS%", "\n".join(tweens))
    (ROOT / "compositions/captions.html").write_text(out)
    print(f"{len(groups)} caption groups, {len(words)} words -> compositions/captions.html")


TEMPLATE = """<template>
  <style>
    #captions {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    /* Bottom of the 168-1330 px platform-safe band, clear of the speaker's face. */
    .cap-group {
      position: absolute;
      left: 0;
      right: 0;
      top: 1150px;
      height: 170px;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: visible;
    }
    .cap-line {
      max-width: 900px;
      text-align: center;
      font-family: "Montserrat", sans-serif;
      font-weight: 800;
      font-size: 66px;
      line-height: 1.12;
      letter-spacing: -0.01em;
      color: #fff6e8;
      -webkit-text-stroke: 10px rgba(20, 12, 6, 0.92);
      paint-order: stroke fill;
      text-shadow:
        0 0 2px rgba(20, 12, 6, 0.95),
        0 3px 0 rgba(20, 12, 6, 0.9),
        0 6px 18px rgba(0, 0, 0, 0.55);
      overflow: visible;
    }
    .cap-word {
      display: inline-block;
      margin: 0 0.09em;
      transform-origin: 50% 70%;
    }
    .cap-word.key {
      color: #f4bf55;
    }
  </style>
  <div id="captions" data-composition-id="captions" data-width="1080" data-height="1920" data-duration="%DURATION%">
%GROUPS%
  </div>
  <script>
  const GOLD = "#f4bf55";
  const CREAM = "#fff6e8";
  const tl = gsap.timeline({ paused: true });
%TWEENS%
  window.__timelines = window.__timelines || {};
  window.__timelines["captions"] = tl;
  </script>
</template>
"""

if __name__ == "__main__":
    main()
