# Live-Video

10 short video premium (9:16, 1080×1920, 34–59s) daripada rakaman LIVE Cooven.

- `videos/` — 10 video siap untuk TikTok / Instagram Reels.
- `EDIT_PLAN.md` — pelan editing penuh: sudut kandungan, hook, tajuk, susunan klip ikut timestamp sumber, dan subtitle ikut masa output.
- `specs/` — spesifikasi setiap video (potongan + subtitle). Edit dan render semula dengan `scripts/render2.py`.
- `scripts/` — transkripsi (Whisper) dan render (ffmpeg + ASS subtitle).

Render semula satu video:

```
python3 scripts/render2.py specs/02-one-pot-pasta.json <live.mp4> <words.jsonl> videos/
```
