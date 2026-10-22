"""Print a video's re-transcribed words with source times, for choosing skip spans.

    python3 tools/words.py <video-id>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for rg in json.loads((ROOT / "data" / f"{sys.argv[1]}.words.json").read_text()):
    print(f"-- range {rg['range']}")
    print(" ".join(f"{w[2]}[{w[0]:.2f}]" for w in rg["words"]))
