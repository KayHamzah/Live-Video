"""Re-transcribe every source range in specs.json for subtitle-grade words.

The first full pass used greedy decoding; here each range is decoded again with
beam search and a vocabulary prompt, so brand names and cooking terms come out
right. Writes data/<id>.words.json: one word list per range, in source seconds.

    python3 tools/asr_ranges.py <ct2-model-dir> <audio16k.wav> [video-id ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import whisper
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parent.parent
SR = 16000
MARGIN = 0.4
PROMPT = (
    "Live masak bersama Kak. Cooven, cooker dan oven. Temperature probe, deep fry, smart cook, "
    "sous vide, steam, rice, air crisp, dehydrate, pizza, slow cook, broil, roast, barbecue, grill. "
    "Cucur jagung gluten free, inner pot, baking paper, kayu manis, bunga lawang, star anise, "
    "buah pelaga, bunga cengkih, serai, white peppercorn, gula kabung, oyster sauce, kicap."
)


def main(model_dir, wav, only):
    specs = json.loads((ROOT / "specs.json").read_text())["videos"]
    audio = whisper.load_audio(wav)
    model = WhisperModel(model_dir, device="cpu", compute_type="int8", cpu_threads=4)
    out_dir = ROOT / "data"
    out_dir.mkdir(exist_ok=True)
    for v in specs:
        if only and v["id"] not in only:
            continue
        ranges = []
        for r in v["ranges"]:
            a, b = r[0], r[1]
            s0 = max(0.0, a - MARGIN)
            clip = audio[int(s0 * SR): int((b + MARGIN) * SR)]
            segs, _ = model.transcribe(clip, language="ms", beam_size=5, word_timestamps=True,
                                       condition_on_previous_text=False, initial_prompt=PROMPT,
                                       vad_filter=False)
            words = []
            for s in segs:
                for w in s.words:
                    ws, we = s0 + w.start, s0 + w.end
                    if a <= (ws + we) / 2 <= b:
                        words.append([round(ws, 3), round(we, 3), w.word.strip()])
            ranges.append({"range": r, "words": words})
        (out_dir / f"{v['id']}.words.json").write_text(json.dumps(ranges, ensure_ascii=False, indent=1))
        text = " ".join(w[2] for rg in ranges for w in rg["words"])
        print(f"== {v['id']}\n{text}\n", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], set(sys.argv[3:]))
