import sys, json, whisper
audio, model_name, out = sys.argv[1], sys.argv[2], sys.argv[3]
offset = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
m = whisper.load_model(model_name, device="cpu")
r = m.transcribe(audio, language="ms", fp16=False, word_timestamps=True,
                 condition_on_previous_text=False, verbose=False,
                 initial_prompt="Live masak dalam periuk Cooven.")
with open(out, "w") as f:
    for s in r["segments"]:
        d = {"start": round(s["start"]+offset,2), "end": round(s["end"]+offset,2), "text": s["text"].strip(),
             "words": [[round(w["start"]+offset,2), round(w["end"]+offset,2), w["word"]] for w in s.get("words", [])]}
        f.write(json.dumps(d, ensure_ascii=False) + "\n")
