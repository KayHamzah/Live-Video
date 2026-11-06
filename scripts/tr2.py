import sys, json, whisper, torch
torch.set_num_threads(4)
audio, out, model = sys.argv[1], sys.argv[2], sys.argv[3]
m = whisper.load_model(model)
print("loaded", flush=True)
r = m.transcribe(audio, language="ms", word_timestamps=True, verbose=False, fp16=False,
    condition_on_previous_text=False, initial_prompt="Live TikTok masak dengan Cooven, periuk dan air fryer.")
with open(out,"w") as f:
    for s in r["segments"]:
        f.write(json.dumps({"s":round(s["start"],2),"e":round(s["end"],2),"t":s["text"].strip(),
          "w":[[round(w["start"],2),round(w["end"],2),w["word"]] for w in s.get("words",[])]},ensure_ascii=False)+"\n")
print("DONE", flush=True)
