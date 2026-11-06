import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=sys.argv[1]; SRC=S+"/src"; OUT=S+"/out"; os.makedirs(OUT,exist_ok=True)
F="/usr/share/fonts/opentype/inter/"
REG=ImageFont.truetype(F+"InterDisplay-Light.otf",78)
BLD=ImageFont.truetype(F+"InterDisplay-ExtraBold.otf",78)
W,H,FPS,XF=1080,1920,30,0.35

def caption(lines,ycenter,path):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    lh=100; widths=[]
    for ln in lines:
        widths.append(sum(d.textlength(t,font=BLD if b else REG) for t,b in ln))
    bw=max(widths)+110; bh=lh*len(lines)+60
    top=int(ycenter*H-bh/2); left=(W-bw)//2
    pill=Image.new("RGBA",(W,H),(0,0,0,0)); pd=ImageDraw.Draw(pill)
    pd.rounded_rectangle([left,top,left+bw,top+bh],radius=46,fill=(0,0,0,165))
    img=Image.alpha_composite(img,pill); d=ImageDraw.Draw(img)
    y=top+30
    for ln,w in zip(lines,widths):
        x=(W-w)/2
        for t,b in ln:
            f=BLD if b else REG
            d.text((x,y+lh/2),t,font=f,fill=(255,255,255,255),anchor="lm"); x+=d.textlength(t,font=f)
        y+=lh
    img.save(path)

# (src, ss, dur, zoom0, zoom1, [(lines, y, t0, t1)])
SEG=[
 ("VID_20261029_075757.mp4",1.2,3.4,1.00,1.12,[([[("Nampak simple,",0)],[("tapi ",0),("sangat berguna.",1)]],0.80,0.25,None)]),
 ("VID_20261029_075640.mp4",9.2,2.8,1.04,1.00,[([[("Reka bentuk ",0),("dua kipas",1)]],0.56,0.2,None)]),
 ("VID_20261029_075640.mp4",4.2,2.6,1.00,1.08,[([[("Kemas & ",0),("minimalist",1)]],0.38,0.2,None)]),
 ("VID_20261029_075705.mp4",3.6,3.0,1.02,1.08,[([[("Kepala kipas",0)],[("boleh dipusing",1)]],0.60,0.2,None)]),
 ("VID_20261029_075705.mp4",6.6,3.0,1.08,1.02,[([[("Laras arah angin",0)],[("ikut selesa",1)]],0.60,0.2,None)]),
 ("VID_20261029_075640.mp4",0.0,3.2,1.00,1.06,[([[("Pakai di leher,",0)],[("tangan bebas",1)]],0.52,0.2,None)]),
 ("VID_20261029_075746.mp4",0.0,2.4,1.00,1.05,[([[("Disertakan ",0),("kad waranti",1)]],0.90,0.15,None)]),
 ("VID_20261029_075757.mp4",2.2,2.8,1.12,1.02,[([[("Teman setia ",0),("cuaca panas",1)]],0.80,0.2,None)]),
 ("VID_20261029_075640.mp4",12.6,4.8,1.00,1.10,[([[("Mungkin ini",0)],[("yang anda perlukan.",1)]],0.52,0.25,2.6),
                                                ([[("Simpan dulu,",0)],[("tengok semula.",1)]],0.52,2.8,None)]),
]
parts=[]
for i,(src,ss,dur,z0,z1,caps) in enumerate(SEG):
    inputs=["-ss",str(ss),"-t",str(dur),"-i",f"{SRC}/{src}"]
    z=f"({z0}+({z1}-{z0})*t/{dur})"
    fc=(f"[0:v]fps={FPS},scale=w='trunc({W}*{z}/2)*2':h='trunc({H}*{z}/2)*2':eval=frame:flags=lanczos,"
        f"crop={W}:{H},eq=contrast=1.06:saturation=0.92:brightness=0.01,unsharp=5:5:0.4,setsar=1[v0]")
    last="v0"
    for k,(lines,y,t0,t1) in enumerate(caps):
        p=f"{OUT}/cap{i}_{k}.png"; caption(lines,y,p)
        t1=t1 if t1 is not None else dur-0.05
        inputs+=["-loop","1","-t",str(dur),"-i",p]
        fc+=(f";[{k+1}:v]format=rgba,fade=in:st={t0}:d=0.35:alpha=1,fade=out:st={t1-0.3}:d=0.3:alpha=1[c{k}]"
             f";[{last}][c{k}]overlay=0:'18*(1-min(1,max(0,(t-{t0})/0.45)))':eval=frame:shortest=1[o{k}]")
        last=f"o{k}"
    o=f"{OUT}/seg{i}.mp4"; parts.append((o,dur))
    subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-filter_complex",fc,"-map",f"[{last}]","-an",
        "-t",str(dur),"-c:v","libx264","-preset","medium","-crf","14","-pix_fmt","yuv420p",o],check=True)
# xfade chain
inp=[]; [inp.extend(["-i",p]) for p,_ in parts]
fc=""; prev="0:v"; off=0
for i in range(1,len(parts)):
    off+=parts[i-1][1]-XF
    fc+=f"[{prev}][{i}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}];"; prev=f"x{i}"
fc+=f"[{prev}]fade=out:st={off+parts[-1][1]-0.5:.3f}:d=0.5,format=yuv420p[vout]"
final=f"{OUT}/kipas_leher_tiktok.mp4"
subprocess.run(["ffmpeg","-v","error","-y",*inp,"-filter_complex",fc,"-map","[vout]","-an","-r",str(FPS),
    "-c:v","libx264","-preset","slow","-crf","20","-profile:v","high","-pix_fmt","yuv420p","-movflags","+faststart",final],check=True)
print(final)
