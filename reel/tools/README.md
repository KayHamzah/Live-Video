# Reel build tools

Pipeline for cutting the 87-minute live into the ~86 s reel in `../index.html`.

1. Transcribe the source with word timestamps (faster-whisper, `large-v3-turbo`, `language="ms"`) to `transcript.jsonl`.
2. `python3 build_edl.py transcript.jsonl <work>`: the beats (hook, tips, jokes) as source ranges; drops pauses over 0.35 s; writes `edl.json` + `captions.json`.
3. `bash assemble.sh <source.mp4> <work>/edl.json <work> ../assets/main.mp4`: cuts, upscales to 1080x1920@30, joins, loudness -16 LUFS.
4. `python3 remap.py <work>/edl.json <work>/captions.json <work>/pieces ../data`: snaps caption times to the frame-accurate pieces.
5. `python3 build_captions.py`: writes `../compositions/captions.html` from `../data/captions.json`.

The source video and `assets/main.mp4` are not committed (too large).
