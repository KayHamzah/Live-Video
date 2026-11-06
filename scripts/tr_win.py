import sys, json, whisper, torch, subprocess, numpy as np
torch.set_num_threads(4)
src, out = sys.argv[1], sys.argv[2]
wins = [(100,145),(262,288),(636,672),(712,802),(2005,2042),(2372,2405),(480,536),(550,606),(845,917),(975,1025),
        (1130,1186),(1240,1322),(1380,1432),(1855,1906),(2940,3026),(3045,3095),(3215,3262),(3440,3520)]
m = whisper.load_model("medium"); print("loaded", flush=True)
with open(out,"w") as f:
  for a,b in wins:
    pcm = subprocess.run(["ffmpeg","-v","error","-ss",str(a),"-t",str(b-a),"-i",src,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    au = np.frombuffer(pcm,np.int16).astype(np.float32)/32768
    r = m.transcribe(au, language="ms", word_timestamps=True, fp16=False, condition_on_previous_text=False,
        initial_prompt="Live masak dengan Cooven. Smart cook, slow cook, sous vide, air crisp, inner pot, one pot pasta.")
    for s in r["segments"]:
        f.write(json.dumps({"s":round(s["start"]+a,2),"e":round(s["end"]+a,2),"t":s["text"].strip(),
          "w":[[round(w["start"]+a,2),round(w["end"]+a,2),w["word"]] for w in s.get("words",[])]},ensure_ascii=False)+"\n"); f.flush()
    print("win",a,b,flush=True)
print("DONE",flush=True)
