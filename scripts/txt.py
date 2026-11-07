import json,glob,os,sys
S,out=sys.argv[1],sys.argv[2]
def mmss(t): return f"{int(t//60):02d}:{int(t%60):02d}"
def mmss1(t): return f"{int(t//60):02d}:{t%60:04.1f}"
CAP={
"01":("Ramai ingat ini oven, air fryer atau multi cooker. Sebenarnya ia boleh masak macam-macam, dan inner pot muat 8 liter.","#cooven #periukpintar #dapurmudah #resipimudah"),
"02":("Makaroni mentah terus masuk bersama kuah. Tak perlu rebus asing. Sukatan air: 400–500g pasta, 1200–1300 ml.","#onepotpasta #resipipasta #cooven #masakmudah"),
"03":("Untuk yang sibuk bekerja: peruntukkan satu hari seminggu untuk prep kuah. Frozen ikut portion, hari biasa tinggal masak.","#mealprep #ibubekerja #tipsdapur #cooven"),
"04":("Ayam + kuah percik mentah terus masuk, tekan Smart Cook 30 minit, tinggal. Dia renih dan bakar dalam satu fungsi.","#ayampercik #smartcook #cooven #resipimudah"),
"05":("Dulu sushi bake perlukan dua alat. Sekarang masak nasi, campur bahan dan bakar dalam satu periuk je.","#sushibake #onepot #cooven #masakmudah"),
"06":("Lauk beku terus masuk, tak perlu tambah air. Tekan P2 atau P3, tinggal. Datang balik dah cair, nampak macam baru masak.","#laukbeku #tipsdapur #cooven #smartcook"),
"07":("Suhu kekal stabil, tumis tak hangit, dan bila habis timer dia auto switch off. Tak perlu risau terlupa tutup api.","#tipsdapur #dapurselamat #cooven #masakmudah"),
"08":("5,000 batang keropok lekor dan 100 pizza dari tengah hari sampai petang, non stop, guna 3 unit sahaja.","#keropoklekor #kenduri #cooven #masakbanyak"),
"09":("Kek steam crack, telur pecah? Puncanya suhu. Di sini boleh pilih suhu tinggi, sederhana atau rendah ikut jenis kuih.","#kuihmuih #steam #cooven #tipsdapur"),
"10":("Masukkan bahan sebelum tidur, set slow cook. Esok pagi lauk dah siap. Sesuai untuk sahur bulan puasa.","#slowcook #sahur #bulanpuasa #cooven"),
}
L=["PELAN 10 SHORT VIDEO — LIVE COOVEN","Format: 9:16, 1080x1920, 30–60 saat","Hook & tajuk: bold, hitam putih sahaja","CTA akhir: Follow untuk tips seterusnya","","Timestamp KLIP = masa dalam rakaman LIVE asal","Timestamp SUBTITLE = masa dalam video pendek",""]
for f in sorted(glob.glob(S+"/specs/*.json")):
    sp=json.load(open(f)); vid=sp["id"]; n=vid[:2]; r=json.load(open(f"{S}/out/{vid}.json"))
    hook=sp["hook"].replace("\\N"," ")
    L+=["━━━━━━━━━━━━━━━━━━━━",f"VIDEO {n} — {sp['title'].upper()}",f"Fail: {vid}.mp4  |  Durasi: {r['duration']:.0f} saat","",
        f"HOOK (0–3s, bold):","{}".format(hook),"",f"TAJUK (label atas, bold):",sp["title"],"","SUSUNAN KLIP:"]
    for i,s in enumerate(sp["segs"]): L.append(f"{i+1}. {mmss1(s[0])} – {mmss1(s[1]+0.6)}  {s[2].replace('|',' ')}")
    L+=["","SUBTITLE:"]
    for a,b,t in r["cues"]:
        if a<2.85: continue
        L.append(f"{mmss(a)}  {t}")
    c,h=CAP[n]
    L+=["","CAPTION POSTING:",f"{hook} {c}","",h,""]
L+=["━━━━━━━━━━━━━━━━━━━━","IDEA VIDEO TAMBAHAN",
"1. Roast + temperature probe (50:45 – 51:35)","2. Pizza 6 minit (53:37 – 54:14)","3. Kapasiti 8L (57:30 – 58:36)","4. Cheese pull mac & cheese (39:23 – 40:01)","",
"NOTA","- Nama jenama ditulis \"Cooven\" ikut logo mesin. Tukar jika ejaan rasmi berbeza.","- Subtitle dari transkripsi automatik yang disemak. Sila tonton sekali sebelum posting."]
open(out,"w").write("\n".join(L)+"\n")
