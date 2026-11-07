import json,glob,os,sys
S=sys.argv[1]; out=sys.argv[2]
def mmss(t): return f"{int(t//60):02d}:{t%60:04.1f}"
ANGLE={
"01":"Perkenalan produk — tepis salah faham (bukan oven/air fryer/multi cooker), kapasiti 8L.",
"02":"Demo one pot pasta — makaroni mentah terus masak bersama kuah + sukatan air.",
"03":"Tips meal prep hujung minggu untuk ibu bekerja.",
"04":"Smart Cook — ayam percik tanpa proses leceh (rebus + bakar dalam satu fungsi).",
"05":"Sushi bake satu periuk — banding cara lama (2 alat) vs Smart Cook.",
"06":"Panaskan lauk beku tanpa air dan tanpa steam.",
"07":"Fungsi Cooker vs dapur gas — suhu stabil, tak hangit, auto switch off.",
"08":"Bukti sosial — 5,000 keropok lekor + 100 pizza dengan 3 unit.",
"09":"Fungsi steam dengan kawalan suhu (telur, kek, apam).",
"10":"Slow cook semalaman — sesuai untuk sahur bulan puasa.",
}
L=["# Pelan Editing — 10 Short Video daripada LIVE Cooven","",
"Sumber: rakaman LIVE 61:36 (720×1280, 60fps). Semua timestamp **SUMBER** merujuk kepada rakaman asal; timestamp **OUTPUT** merujuk kepada video pendek.","",
"## Gaya (semua video)","",
"- Format 9:16, 1080×1920, 30fps, H.264 + AAC 192k, loudness −14 LUFS (standard TikTok/Reels).",
"- Font: **Inter Bold** (hook & tajuk), Inter Medium (subtitle). Warna hitam & putih sahaja.",
"- **Hook (0–3s):** teks bold hitam atas kotak putih, di ruang kabinet bawah — tidak tutup muka/produk.",
"- **Tajuk:** label kecil bold hitam atas putih di bahagian paling atas, kekal sepanjang video.",
"- **Subtitle:** putih dengan outline hitam nipis, satu baris pendek, di atas kabinet gelap (kontras tinggi).",
"- **End card wajib (2.5s terakhir):** skrin hitam, label kecil \"TIP DAPUR\", garis putih pendek, dan teks bold putih \"Follow Kay sekarang untuk lebih banyak tips\".",
"- Potongan: jump-cut pada sempadan perkataan; klip berselang-seli antara framing 100% dan zoom halus 107% untuk sorok jump-cut. Tiada transition/sticker/emoji.",
"- Audio: suara asal sahaja, high-pass 80Hz, denoise ringan, compressor lembut. Fade 30–50ms di setiap potongan untuk elak bunyi 'klik'. Tiada muzik (boleh tambah instrumental lembut ~−28dB di app jika mahu).","",
"## Ringkasan","","| # | Fail | Sudut kandungan | Hook | Durasi |","|---|---|---|---|---|"]
specs={os.path.basename(f)[:-5]:json.load(open(f)) for f in glob.glob(S+"/specs/*.json")}
rows=[];body=[]
for vid in sorted(specs):
    sp=specs[vid]; r=json.load(open(f"{S}/out/{vid}.json")); n=vid[:2]
    hook=sp["hook"].replace("\\N"," ")
    L.append(f"| {n} | `videos/{vid}.mp4` | {ANGLE[n]} | **{hook}** | {r['duration']:.0f}s |")
    body+=["",f"## {n}. {sp['title']}","",f"- **Sudut:** {ANGLE[n]}",f"- **Hook (0:00–0:03, bold):** **{hook}**",f"- **Tajuk (label atas, bold):** **{sp['title']}**","- **End card:** Follow Kay sekarang untuk lebih banyak tips (2.5s)",f"- **Durasi:** {r['duration']:.1f}s","",
      "**Susunan klip (potong dari rakaman asal):**","","| Klip | Sumber mula | Sumber tamat | Isi |","|---|---|---|---|"]
    for i,s in enumerate(sp["segs"]):
        body.append(f"| {i+1} | {mmss(s[0])} | {mmss(s[1])} | {s[2].replace('|',' ')} |")
    body+=["","**Subtitle (masa OUTPUT):**","","| Mula | Tamat | Teks |","|---|---|---|"]
    for a,b,t in r["cues"]:
        if a<2.85: t+=" *(dibawa oleh kad hook)*"
        body.append(f"| {mmss(a)} | {mmss(b)} | {t} |")
L+=body
L+=["","## Idea tambahan (belum dibuat)","",
"- **Roast + temperature probe** (50:45–51:35) — ayam golek auto-detect masak sampai ke tulang.",
"- **Pizza 6 minit** (53:37–54:14) — lebih cepat daripada tunggu delivery.",
"- **Kapasiti 8L** (57:30–58:36) — 2 ekor ayam, 2kg bihun, 2kg nasi sekali masak.",
"- **Hasil mac & cheese / cheese pull** (39:23–40:01) — visual paling 'sedap' dalam live, sesuai sebagai B-roll.",
"","## Nota","",
"- Subtitle disemak manual daripada transkripsi automatik (Whisper). Nama penuh jenama yang disebut dalam live ditulis sebagai **Cooven** (ejaan pada logo produk) — sila betulkan jika ejaan rasmi berbeza.",
"- Satu frasa kurang jelas dalam audio (\"kenduri … di Johor\", video 08) ditulis tanpa perkataan yang tidak pasti.",
"- Video 03 ~62s termasuk end card (diluluskan Kay).",
"- Skrip `scripts/` boleh dijalankan semula untuk render ulang selepas edit `specs/*.json`."]
open(out,"w").write("\n".join(L)+"\n"); print("ok")
