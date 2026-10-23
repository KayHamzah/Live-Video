import sys, json, whisper, numpy as np
audio_path, model_name, out = sys.argv[1], sys.argv[2], sys.argv[3]
windows = [tuple(map(float, w.split("-"))) for w in sys.argv[4:]]
m = whisper.load_model(model_name, device="cpu")
audio = whisper.load_audio(audio_path)
with open(out, "w") as f:
    for a, b in windows:
        clip = audio[int(a*16000):int(b*16000)]
        r = m.transcribe(clip, language="ms", fp16=False, word_timestamps=True,
                         condition_on_previous_text=True, verbose=None)
        for s in r["segments"]:
            d = {"start": round(s["start"]+a,2), "end": round(s["end"]+a,2), "text": s["text"].strip(),
                 "words": [[round(w["start"]+a,2), round(w["end"]+a,2), w["word"]] for w in s.get("words", [])]}
            f.write(json.dumps(d, ensure_ascii=False) + "\n"); f.flush()
        print("done window", a, b, flush=True)
