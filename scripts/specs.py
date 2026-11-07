import json,sys,os
CTA="Follow untuk tips seterusnya"
V=[
dict(id="01-bukan-oven",title="Apa Sebenarnya Cooven?",hook="Ini bukan oven.\\NBukan air fryer.",segs=[
 [100.0,100.4,"Ini apa benda?"],
 [108.0,112.3,"Kadang-kadang orang ingat|ini adalah oven,|tapi sebenarnya ini bukan oven."],
 [115.8,118.8,"Ada yang kata ini air fryer,|tapi sebenarnya bukan air fryer."],
 [119.5,122.9,"Ada yang kata ini multi cooker,|tapi sebenarnya ia bukan multi cooker."],
 [123.8,124.5,"So, dia apa?"],
 [269.6,271.5,"Dia bukan sekadar periuk biasa."],
 [137.0,143.1,"Sebenarnya dia boleh masak macam-macam.|Bukan sekadar satu dua menu je,|tapi macam-macam."],
 [3452.1,3455.0,"Dalam inner pot ni,|dia muat 8 liter."],
 [3522.7,3525.9,"Walaupun nampak kecil,|sebenarnya kapasiti dia besar."]]),
dict(id="02-one-pot-pasta",title="One Pot Pasta",hook="Pasta tak perlu\\Nrebus dulu.",segs=[
 [643.8,651.2,"Kita akan letak makaroni tu|mentah-mentah.|Maksudnya, kita tak rebus dulu|pun makaroni tu."],
 [652.7,654.2,"Selalu kalau nak buat makaroni,"],
 [657.1,658.3,"kita kena rebus dulu, kan?"],
 [658.9,659.7,"So yang ini, tak payah."],
 [738.4,745.8,"Cara sukat air dia:|satu pek makaroni atau pasta,|dalam 400 gram ke 500 gram,"],
 [746.9,751.6,"sukatan air dia adalah|1200 ml atau 1300 ml."],
 [756.9,761.8,"Atau letak kuah tu|paras-paras dengan pasta."],
 [771.9,778.1,"Bila dah letak semua,|kita tutup sahaja,|tekan fungsi Smart Cook."],
 [786.5,796.0,"Dia akan tolong renihkan makanan,|tanpa perlu risau dia hangit,|melekat ataupun kering."],
 [2007.9,2009.8,"Pasta dah siap."],
 [2036.5,2037.3,"Cantik je hasil dia."]]),
dict(id="03-meal-prep",title="Tips Meal Prep",hook="Sibuk bekerja?\\NBuat ini hujung minggu.",segs=[
 [481.3,485.3,"Ini tips yang K nak bagi|kepada anda yang mungkin|sibuk bekerja."],
 [493.4,498.8,"Hujung minggu,|kita prep dulu bahan-bahan|yang sepatutnya."],
 [499.5,511.0,"Contoh, this week nak masak|spaghetti bolognese, carbonara,|buat dulu stok kuah siap-siap."],
 [554.0,561.0,"Kalau rajin, at least seminggu|atau dua minggu sekali,|peruntukkan satu hari|untuk buat prepping."],
 [562.2,570.9,"Buatlah kuah bolognese extra,|lepas tu frozen kan.|Per portion pun boleh,|ikut berapa banyak nak makan."],
 [594.4,602.2,"Setiap benda yang kita buat,|kena bijak atur strategi.|Sebab kita busy,|tak sempat nak masak setiap hari."]]),
dict(id="04-ayam-percik",title="Smart Cook: Ayam Percik",hook="Ayam percik,\\Ntanpa leceh.",segs=[
 [852.2,858.6,"Kalau dulu nak buat ayam percik,|rasa sangat-sangat susah,|sangat-sangat leceh.|Kena masak kuah percik dulu."],
 [859.1,865.1,"Lepas tu perap ayam,|golekkan dengan kuah percik,|lepas tu bakar pula. Betul tak?"],
 [865.8,870.8,"Tapi bila guna fungsi Smart Cook|yang ada pada Cooven ni,"],
 [872.7,882.3,"terus letak ayam|dan kuah percik yang mentah,|yang baru blend, belum masak,|terus letak dalam ni."],
 [882.7,890.8,"Tekan Smart Cook,|set masa 30 minit, tinggal.|Tak perlu tengok, tak perlu kacau,|tak perlu nak tunggu pun."],
 [905.9,914.0,"Fungsi Smart Cook ni|gabungan dua kaedah memasak:|merebus atau merenih,|dan juga membakar."]]),
dict(id="05-sushi-bake",title="Sushi Bake One Pot",hook="Sushi bake,\\Nsatu periuk je.",segs=[
 [977.6,981.3,"Sebelum ni, kalau nak masak|sushi bake,"],
 [986.4,992.6,"masak dulu nasi sushi.|Lepas dah masak nasi sushi,|nak kena buat apa pula?|Kena bakar pula dalam oven."],
 [992.8,997.5,"So kena guna dua periuk,|atau dua peralatan yang berbeza."],
 [997.9,1001.9,"Tapi dengan fungsi Smart Cook,|kita hanya guna satu mesin,|satu periuk je."],
 [1002.2,1015.4,"Macam mana nak buat?|Letak beras sushi dalam periuk,|set Smart Cook.|Dah siap masak, tekan-tekan,|campur bahan sushi bake,|tutup, dan dia terus bakarkan."],
 [1015.7,1016.5,"Sangat-sangat mudah."]]),
dict(id="06-lauk-beku",title="Panaskan Lauk Beku",hook="Lauk beku?\\NTak perlu tambah air.",segs=[
 [1135.2,1140.5,"Contoh nak panaskan lauk|daripada freezer,|dia beku-beku, kan?"],
 [1140.9,1146.9,"Selalu panaskan atas dapur gas,|kena letak air sikit,|nak elak hangit. Betul tak?"],
 [1147.2,1156.5,"Tapi dengan fungsi Smart Cook,|tak perlu letak air pun.|Letak je seketul yang beku,|tutup, tekan P2 atau P3,|lepas tu tinggalkan je."],
 [1157.0,1163.5,"Bila datang balik,|dia dah automatik cair.|Nampak cantik, macam baru masak."],
 [1164.3,1166.1,"Tak nampak macam frozen food."],
 [1169.2,1178.6,"Kalau dulu, kita panaskan|guna cara steam.|Sekarang dengan Cooven,|boleh panaskan guna Smart Cook."],
 [1179.1,1183.9,"Barulah smart duduk kat dapur.|Bukan kerja je kena smart,|masak pun kena smart."]]),
dict(id="07-auto-off",title="Tak Hangit, Auto Off",hook="Terlupa tutup api?",segs=[
 [1303.6,1305.2,"Alamak, tadi dah tutup api ke belum?"],
 [1244.6,1248.1,"Bila guna Cooven,|set suhu 100 je."],
 [1248.8,1257.4,"Biar 10, 20, 15, 30 minit.|Walaupun belum masuk bahan,|dia tak akan berasap,|tak akan tiba-tiba hangit."],
 [1259.8,1268.1,"Sebelum ni, tumis bawang putih|atas dapur gas, tak sampai seminit|terus brown.|Tak boleh tinggal, kena sentiasa kacau."],
 [1270.6,1280.6,"Tapi tumis dalam Cooven,|letak je, set masa dan suhu,|lepas tu boleh tinggal,|buat kerja lain."],
 [1285.4,1288.3,"Sebab suhu dia|dah maintain."],
 [1309.6,1318.5,"Bila guna Cooven,|kalau terlupa tutup api pun,|tak ada masalah.|Bila habis timer, dia auto switch off."]]),
dict(id="08-event-besar",title="Diuji Untuk Event Besar",hook="5,000 keropok lekor.\\NHanya 3 unit.",segs=[
 [1402.0,1406.8,"Bayangkan, nak goreng|5,000 batang keropok lekor,|dan nak bakar 100 pizza."],
 [1384.2,1392.5,"Baru-baru ni kita sponsor|100 keping pizza|dan 5,000 batang keropok lekor|dekat kenduri di Johor."],
 [1393.5,1401.6,"Waktu tu kita hanya guna|3 unit Cooven sahaja,|masak dari tengah hari sampai petang,|non stop."],
 [1407.8,1414.0,"Dalam tempoh berapa jam?|Dari pukul 12 sampai 6 petang.|Korang kira sendiri."],
 [1414.4,1423.0,"Hanya guna 3 Cooven, non stop,|tak berhentikan pun,|dan tak ada masalah."],
 [1423.3,1430.2,"Event sebesar itu pun|boleh run dengan Cooven,|apatah lagi masak harian di rumah."]]),
dict(id="09-steam-ikut-suhu",title="Steam Ikut Suhu",hook="Kek steam\\Nselalu crack?",segs=[
 [1878.9,1883.4,"Contoh macam kek,|kalau steam dengan suhu tinggi,|dia akan crack. Betul tak?"],
 [1856.0,1859.3,"Apa beza steam dalam Cooven|dengan steamer lain?"],
 [1860.4,1865.0,"Steamer lain tak boleh set suhu.|Tapi yang ini, boleh set."],
 [1865.6,1869.9,"Nak steam suhu tinggi,|sederhana tinggi,|atau suhu rendah."],
 [1870.8,1878.3,"Ada sesetengah makanan|tak boleh steam suhu terlalu tinggi.|Contoh macam telur,|dia mudah pecah."],
 [1883.8,1895.6,"Ada kuih yang kena steam|dengan low heat.|Tapi ada kuih memang|kena steam dengan api kuat.|Contoh apam, nak bagi merekah cantik,|kena guna api yang kuat."],
 [1896.0,1902.8,"Dengan Cooven, boleh pilih|nak suhu tinggi, rendah,|atau sedang-sedang."]]),
dict(id="10-slow-cook-sahur",title="Slow Cook Untuk Sahur",hook="Masak\\Nsambil tidur.",segs=[
 [2961.1,2962.0,"Boleh masak sambil tidur."],
 [2947.8,2951.3,"Antara yang K suka, fungsi slow cook.|Sebab boleh masak|dalam keadaan kita tidur."],
 [2952.1,2957.9,"Boleh buat gulai daging,|sup ayam, sup ikan,|macam-macam."],
 [2962.7,2964.8,"Masak waktu malam,|pagi esok dah siap."],
 [2970.1,2977.7,"Malam sebelum tidur,|masuk semua bahan, letak daging,|set je slow cook.|Lepas tu tidur dengan tenang."],
 [2982.9,2988.1,"Tak perlu risau, dapur takkan berasap.|Daging akan jadi lembut,|esok pagi masakan dah siap."],
 [2988.7,2997.0,"Waktu paling sesuai guna slow cook?|Bulan puasa nanti, percayalah.|Sebab setiap kali sahur,|lauk dah siap."],
 [2998.6,3002.4,"Bangun sahur, terus hidang,|atau panaskan sikit,|terus hidang."]]),
]
d=sys.argv[1]
for v in V:
    json.dump(v,open(os.path.join(d,v["id"]+".json"),"w"),ensure_ascii=False,indent=1)
print(len(V))
