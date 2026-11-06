"""Render one premium short from a spec.
spec: {id,title,hook,cta,segs:[[first_word_t,last_word_t,"cue|cue|..."]]}
Each seg is cut on word boundaries; each '|' cue is timed to its share of the seg's words."""
import sys, json, subprocess, os, bisect
spec=json.load(open(sys.argv[1])); src=sys.argv[2]; W=json.loads(open(sys.argv[3]).readline())["w"]; outdir=os.path.abspath(sys.argv[4])
tmp=os.path.join(outdir,"tmp_"+spec["id"]); os.makedirs(tmp,exist_ok=True)
Wd,Ht,FPS=1080,1920,30
starts=[w[0] for w in W]
def near(t):
    i=min(range(max(0,bisect.bisect_left(starts,t)-2),min(len(W),bisect.bisect_left(starts,t)+2)),key=lambda j:abs(W[j][0]-t)); return i
def ts(t):
    t=max(t,0); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"
parts=[]; cues=[]; out_t=0
for k,(t0,t1,text) in enumerate(spec["segs"]):
    i0,i1=near(t0),near(t1)
    a=W[i0][0]-0.12
    if i0>0: a=max(a,W[i0-1][1]+0.02)
    end_last=min(W[i1][1],W[i1][0]+1.2)
    b=end_last+0.22
    if i1+1<len(W): b=min(b,W[i1+1][0]-0.03)
    b=max(b,end_last+0.05)
    dur=b-a
    p=os.path.join(tmp,f"c{k}.mp4")
    z=1.0 if k%2==0 else 1.07
    sw,sh=int(Wd*z)//2*2,int(Ht*z)//2*2
    vf=f"scale={sw}:{sh}:flags=lanczos,crop={Wd}:{Ht}:(iw-{Wd})/2:(ih-{Ht})*0.3,fps={FPS},setsar=1"
    af=f"afade=t=in:d=0.03,afade=t=out:st={max(dur-0.05,0):.3f}:d=0.05"
    subprocess.run(["ffmpeg","-y","-v","error","-ss",f"{a:.3f}","-t",f"{dur:.3f}","-i",src,"-vf",vf,"-af",af,
      "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p","-c:a","pcm_s16le","-ar","48000",p.replace(".mp4",".mov")],check=True)
    parts.append(p.replace(".mp4",".mov"))
    ws=W[i0:i1+1]; lines=text.split("|"); M=sum(len(l.split()) for l in lines); N=len(ws); c=0
    for ln in lines:
        n=len(ln.split()); j0=min(N-1,int(c*N/M)); j1=max(j0,min(N-1,int(round((c+n)*N/M))-1)); c+=n
        cues.append([out_t+ws[j0][0]-a, out_t+min(ws[j1][1],ws[j1][0]+1.0)-a, ln.strip()])
    out_t+=dur
total=out_t
for i in range(len(cues)):   # close small gaps so cues don't flicker
    nxt=cues[i+1][0] if i+1<len(cues) else total
    cues[i][1]=min(nxt-0.02, cues[i][1]+0.35) if nxt-cues[i][1]<0.8 else cues[i][1]+0.25
HOOK_END=spec.get("hook_end",3.0)
ass=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {Wd}
PlayResY: {Ht}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,Inter,78,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,-0.5,0,3,24,0,2,80,80,420,1
Style: Title,Inter,42,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,3,13,0,8,90,90,110,1
Style: Sub,Inter Medium,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,3,1.2,2,100,100,330,1
Style: Cta,Inter,42,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1.5,0,3,15,0,2,90,90,560,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ass+=f"Dialogue: 2,{ts(0)},{ts(HOOK_END)},Hook,,0,0,0,,{{\\fad(120,200)}}{spec['hook']}\n"
ass+=f"Dialogue: 2,{ts(HOOK_END-0.2)},{ts(total)},Title,,0,0,0,,{{\\fad(300,0)}}{spec['title']}\n"
for s,e,t in cues:
    if s<HOOK_END-0.15: continue   # hook card carries the opening line
    ass+=f"Dialogue: 1,{ts(s)},{ts(e)},Sub,,0,0,0,,{t}\n"
if spec.get("cta"):
    ass+=f"Dialogue: 3,{ts(total-3.2)},{ts(total)},Cta,,0,0,0,,{{\\fad(250,0)}}{spec['cta']}\n"
assp=os.path.join(tmp,"subs.ass"); open(assp,"w").write(ass)
lst=os.path.join(tmp,"list.txt"); open(lst,"w").write("".join(f"file '{p}'\n" for p in parts))
out=os.path.join(outdir,spec["id"]+".mp4")
subprocess.run(["ffmpeg","-y","-v","error","-f","concat","-safe","0","-i",lst,
  "-vf",f"ass={assp}:fontsdir=/usr/share/fonts/opentype/inter,format=yuv420p",
  "-af","highpass=f=80,afftdn=nr=6:nf=-42,acompressor=threshold=-22dB:ratio=2.2:attack=8:release=180,loudnorm=I=-14:TP=-1.5:LRA=8",
  "-c:v","libx264","-preset","slow","-crf","18","-profile:v","high","-r",str(FPS),"-c:a","aac","-b:a","192k","-ar","48000",
  "-movflags","+faststart",out],check=True)
json.dump({"duration":round(total,2),"cues":[[round(s,2),round(e,2),t] for s,e,t in cues],
  "cuts":[[round(x,2) for x in s[:2]] for s in spec["segs"]]},open(os.path.join(outdir,spec["id"]+".json"),"w"),ensure_ascii=False,indent=1)
print(spec["id"],f"{total:.1f}s")
