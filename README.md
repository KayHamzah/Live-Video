# Live-Video: Food Engine Cooven Shorts

Ten 9:16 short videos (1080 × 1920, 30 fps) cut from the Food Engine Cooven LIVE recording (48 min).
Style: premium minimalist, black and white text only (Inter font), original voice, word-synced Malay subtitles.

| # | Fail (`output/`) | Hook | Isi | Durasi | CTA |
|---|---|---|---|---|---|
| 01 | `01_bihun_goreng_effortless.mp4` | BIHUN GORENG TANPA PENAT KACAU | Resipi penuh bihun goreng Singapore: bahan → tumis → air + carrot → perasakan → bihun → Steam P1 3 minit → hasil | 62 s | Simpan video ini untuk rujukan. |
| 02 | `02_telur_dadar_tanpa_flip.mp4` | TELUR DADAR TANPA PERLU FLIP | Cooker 190°C → tuang telur → bulatkan → tutup air fryer → Broil 250°C 3 minit | 42 s | Nak saya kongsikan teknik yang lain? |
| 03 | `03_bihun_tak_sempat_rendam.mp4` | TAK SEMPAT RENDAM BIHUN? | Rendam dalam plastik semasa menumis + sukatan air = berat bihun | 49 s | Simpan video ini untuk rujukan. |
| 04 | `04_rahsia_bihun_sedap.mp4` | RAHSIA BIHUN TAK TAWAR | Garam + stok, rasa dulu sebelum masuk bihun; terlebih masin → gula, tawar → garam | 45 s | Simpan video ini untuk rujukan. |
| 05 | `05_nasi_goreng_dari_beras.mp4` | NASI GORENG DARIPADA BERAS? | Smart Cook, beras basmati, ± 30 minit | 38 s | Nak saya kongsikan teknik yang lain? |
| 06 | `06_dapur_tak_bersepah.mp4` | LEPAS MASAK, DAPUR TAK BERSEPAH | Dulu dua sudip & dapur bersepah, kini penyepit; inner pot cukup lap | 57 s | Simpan video ini untuk rujukan. |
| 07 | `07_3_menu_bawah_1_jam.mp4` | 3 MENU, TAK SAMPAI 1 JAM | Bihun 10 min, telur dadar 4 min, nasi goreng 30 min | 32 s | Menu mana yang anda nak cuba dulu? |
| 08 | `08_clotted_cream_2_jam.mp4` | CLOTTED CREAM 2 JAM JE? | Fungsi Dehydrate: daun kari, clotted cream, starter sourdough | 37 s | Fungsi mana yang anda paling suka? |
| 09 | `09_pizza_6_minit.mp4` | BAKAR PIZZA DALAM 6 MINIT? | Fungsi Pizza vs oven biasa + Deep Fry minyak tak hitam | 27 s | Fungsi mana yang anda paling suka? |
| 10 | `10_bbq_tanpa_asap.mp4` | BBQ TANPA ARANG, TANPA ASAP | Fungsi Barbecue + Slow Cook sambil tidur | 51 s | Fungsi mana yang anda paling suka? |

Every video ends with a 2.5 s end card: **Follow Kay sekarang untuk lebih banyak tips.**

All claims (times, temperatures, results) are the presenter's own words from the LIVE; nothing was added.

## Files

- `output/`: the finished MP4s.
- `EDITING_PLAN.md`: scene-by-scene plan for each video (LIVE timestamps, shot type, on-screen labels, dialogue) for rebuilding or tweaking in CapCut.
- `specs/*.json`: the edit decision list for each video (source in/out points, B-roll, zoom, labels, hook, CTA, subtitle fixes).
- `tools/render.py`: renders one spec with ffmpeg + libass. `tools/render_all.sh` renders all of them. `tools/make_plan.py` regenerates `EDITING_PLAN.md`. `tools/words.py` prints word timings.

## Re-rendering

Needs ffmpeg with libass, the Inter font, the LIVE MP4, and a word-level transcript (`transcript.jsonl`, produced with Whisper large-v3-turbo, `language="ms"`, `word_timestamps=True`).

```bash
tools/render_all.sh transcript.jsonl live.mp4 output/            # all videos
python3 tools/render.py specs/02_telur_dadar_tanpa_flip.json transcript.jsonl live.mp4 output/02.mp4
python3 tools/make_plan.py transcript.jsonl EDITING_PLAN.md
```

Shot modes: the default is the presenter cam, full frame, with a gentle zoom. `"mode": "pan"` crops the top-down pan camera (picture-in-picture or letterboxed in the LIVE, auto-detected) and places it on a black canvas. `"v"` takes video from another timestamp (B-roll), and `"mute": true` makes a silent tail for the CTA.
