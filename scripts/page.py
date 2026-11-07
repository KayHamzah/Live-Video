import json,glob,os,sys,html,re
S=sys.argv[1]; out=sys.argv[2]; assets=json.load(open(sys.argv[3])) if len(sys.argv)>3 and os.path.exists(sys.argv[3]) else {}
exec(re.search(r"CAP=\{.*?\n\}",open(S+"/scripts/txt.py").read(),re.S).group(0))
def mmss(t): return f"{int(t//60)}:{int(t%60):02d}"
e=html.escape
cards=[]
for f in sorted(glob.glob(S+"/specs/*.json")):
    sp=json.load(open(f)); vid=sp["id"]; n=vid[:2]; r=json.load(open(f"{S}/out/{vid}.json"))
    hook=sp["hook"].replace("\\N"," "); c,h=CAP[n]
    caption=f"{hook} {c}\n\n{h}"
    subs="\n".join(f"{mmss(a)}  {t}" for a,b,t in r["cues"] if a>=2.85)
    script=hook+"\n"+" ".join(t for a,b,t in r["cues"] if a>=2.85)
    clips="".join(f"<li><span class=t>{mmss(s[0])}–{mmss(s[1]+0.6)}</span> {e(s[2].replace('|',' '))}</li>" for s in sp["segs"])
    v=assets.get(vid+".mp4",""); p=assets.get(vid+".jpg","")
    media=f'<video controls playsinline preload="none" poster="{p}" src="{v}"></video>' if v else '<div class=ph>Video sedang dimuat naik</div>'
    cards.append(f'''<article class=card id=v{n}>
<div class=media>{media}</div>
<div class=body>
<div class=meta><span class=num>{n}</span><span class=dur>{r['duration']:.0f} saat</span><span class=tag>{e(sp['title'])}</span></div>
<h2>{e(hook)}</h2>
<div class=blk><div class=bh><span>Caption posting</span><button type=button class=cp data-k=cap{n}>Salin</button></div><pre id=cap{n}>{e(caption)}</pre></div>
<div class=blk><div class=bh><span>Skrip subtitle</span><button type=button class=cp data-k=sub{n}>Salin</button></div><pre id=sub{n} class=small>{e(subs)}</pre></div>
<details><summary>Klip dari rakaman LIVE</summary><ol class=clips>{clips}</ol></details>
</div></article>''')
allcap="\n\n━━━━━━━━━━\n\n".join(f"VIDEO {f[-0:]}" for f in [])
page=f'''<title>Short Video Kay</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Layout: one column of video cards on phone, video beside copy blocks on wide screens. Monochrome like the shorts. */
:root{{--bg:#f6f6f4;--surface:#ffffff;--ink:#111111;--muted:#5d5d58;--line:#e2e2dd;--inv:#ffffff;
--display:"Schibsted Grotesk",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#0f0f0e;--surface:#1a1a18;--ink:#f2f2ee;--muted:#a3a39c;--line:#2c2c29;--inv:#0f0f0e;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#0f0f0e;--surface:#1a1a18;--ink:#f2f2ee;--muted:#a3a39c;--line:#2c2c29;--inv:#0f0f0e;color-scheme:dark}}
body{{background:var(--bg);color:var(--ink);font-family:var(--display);font-size:16px;line-height:1.5}}
.wrap{{max-width:1040px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:28px 56px;display:flex;flex-direction:column;gap:28px}}
header{{display:flex;flex-direction:column;gap:10px}}
.eyebrow{{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
h1{{font-size:clamp(30px,7vw,52px);font-weight:800;line-height:1.02;letter-spacing:-.03em;margin:0;text-wrap:balance}}
.lead{{color:var(--muted);margin:0;max-width:60ch}}
nav{{display:flex;flex-wrap:wrap;gap:6px}}
nav a{{font-family:var(--mono);font-size:13px;color:var(--ink);text-decoration:none;border:1px solid var(--line);background:var(--surface);padding:6px 10px;border-radius:999px}}
nav a:focus-visible,button:focus-visible,summary:focus-visible{{outline:2px solid var(--ink);outline-offset:2px}}
.card{{display:grid;grid-template-columns:minmax(0,300px) minmax(0,1fr);gap:24px;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;scroll-margin-top:16px}}
@media (max-width:720px){{.card{{grid-template-columns:minmax(0,1fr)}}}}
.media{{display:flex;justify-content:center}}
video,.ph{{width:100%;max-width:300px;aspect-ratio:9/16;border-radius:10px;background:#000;display:block}}
.ph{{display:flex;align-items:center;justify-content:center;color:#aaa;font-size:14px}}
.body{{display:flex;flex-direction:column;gap:14px;min-width:0}}
.meta{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-family:var(--mono);font-size:12px;color:var(--muted)}}
.num{{background:var(--ink);color:var(--inv);padding:2px 8px;border-radius:4px;font-weight:500}}
.tag{{border:1px solid var(--line);padding:1px 8px;border-radius:4px}}
h2{{font-size:clamp(22px,4.6vw,30px);font-weight:800;letter-spacing:-.02em;line-height:1.1;margin:0;text-wrap:balance}}
.blk{{border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.bh{{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:8px 10px 8px 12px;border-bottom:1px solid var(--line);font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:500}}
button.cp{{font:600 14px var(--display);letter-spacing:0;text-transform:none;background:var(--ink);color:var(--inv);border:0;border-radius:8px;padding:8px 16px;cursor:pointer;min-height:36px}}
button.cp.done{{background:transparent;color:var(--ink);box-shadow:inset 0 0 0 1px var(--ink)}}
pre{{margin:0;padding:12px;white-space:pre-wrap;word-break:break-word;font:15px/1.55 var(--display);user-select:text}}
pre.small{{font:13px/1.6 var(--mono);max-height:220px;overflow:auto}}
details{{font-size:14px}}
summary{{cursor:pointer;color:var(--muted);font-weight:500}}
.clips{{margin:8px 0 0;padding-left:20px;display:flex;flex-direction:column;gap:4px}}
.t{{font-family:var(--mono);font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums;margin-right:4px}}
.note{{font-size:14px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;display:flex;flex-direction:column;gap:6px}}
.note p{{margin:0;max-width:70ch}}
@media (prefers-reduced-motion:no-preference){{button.cp{{transition:background .15s}}}}
</style>
<div class=wrap>
<header>
<span class=eyebrow>LIVE Cooven · 61 min → 10 short video</span>
<h1>Short Video Kay</h1>
<p class=lead>Tonton setiap video, kemudian tekan <b>Salin</b> untuk copy caption atau skrip subtitle. Format 9:16, 36–58 saat. Setiap video berakhir dengan end card <b>Follow Kay sekarang untuk lebih banyak tips</b>.</p>
<nav>{"".join(f'<a href="#v{i:02d}">{i:02d}</a>' for i in range(1,11))}</nav>
</header>
{"".join(cards)}
<div class=note>
<p><b>Idea video seterusnya:</b> roast + temperature probe (50:45), pizza 6 minit (53:37), kapasiti 8L (57:30), cheese pull mac &amp; cheese (39:23).</p>
<p>Video di page ini versi ringan untuk tontonan. Fail kualiti penuh 1080×1920 ada dalam fail yang dihantar sebelum ini. Jenama ditulis "Cooven" ikut logo mesin.</p>
</div>
</div>
<script>
document.addEventListener("click",function(ev){{
  var b=ev.target.closest("button.cp"); if(!b) return;
  var el=document.getElementById(b.dataset.k); var txt=el.innerText;
  function ok(){{b.textContent="Disalin ✓";b.classList.add("done");setTimeout(function(){{b.textContent="Salin";b.classList.remove("done")}},1800)}}
  function sel(){{var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent="Dipilih — tekan Copy"}}
  try{{navigator.clipboard.writeText(txt).then(ok,sel)}}catch(e){{sel()}}
}});
</script>
'''
open(out,"w").write(page); print(len(page))
