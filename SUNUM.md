# Staj Sunumu — MCP-Based AI Helpdesk Agent Demo
### 10 Slaytlik Sunum Akisi (Turkce)

> Teknik terimler bilincli olarak Ingilizce birakilmistir: MCP, AI Agent, Ticket
> Automation, Risk Engine, Audit Log, Tool Calling, Mock ERP, Endpoint Automation.

---

## Slayt 1 — Kapak
**Baslik:** MCP-Based AI Helpdesk Agent Demo — Yapay Zeka Destekli IT Ticket Otomasyonu

- Staj projesi / konsept prototipi
- Amac: IT helpdesk surecinin AI ile otomasyonunu **guvenli** sekilde gostermek
- Tamamen **local** calisan bir demo
- Hazirlayan: Tevfik Efe Aydin — Klimasan Stajı

**Konusma notu:** "Bugun size bilgi islem ekiplerine gelen tekrar eden ticketlarin
yapay zeka ile nasil otomatiklestirilebilecegini gosteren bir demo prototipi
sunacagim. Onemle belirtmek isterim: bu proje gercek sirket sistemlerine baglanmaz,
tamamen local ve guvenli bir gosterimdir."

**Demo ekrani:** — (Kapak slayti; henuz uygulama acilmaz)

---

## Slayt 2 — Problem
**Baslik:** IT Helpdesk'te Tekrar Eden Ticket Yuku

- Ticketlarin buyuk kismi **standart ve tekrar eden** taleplerden olusur
- Ornek: "Maildeki dosyayi masaustume atar misin?", "Yaziciya cikti gonderemiyorum",
  "VPN'e baglanamiyorum", "Disk dolu", "Program kurulu mu?"
- Her biri: oku → anla → sistemi kontrol et → islemi yap → cevap yaz → kapat
- Bu dongu **zaman alir** ve otomasyona cok uygundur

**Konusma notu:** "Bilgi islem personelinin gununun onemli bir kismi bu tur basit
ama tekrar eden ticketlarla geciyor. Her ticket icin ayni adimlar tekrarlaniyor.
Sorumuz su: bu surecin ne kadarini yapay zeka guvenli bir sekilde ustlenebilir?"

**Demo ekrani:** Uygulamayi ac → sol paneldeki **Ticket dropdown**'i goster (8 ornek
ticket listesi burada gorunur).

---

## Slayt 3 — Cozum: AI Agent + Ticket Automation
**Baslik:** Yapay Zeka Destekli Ticket Otomasyonu

- **AI Agent** ticketi okur ve niyetini (intent) anlar
- Kategori ve **risk seviyesini** belirler
- Eksik bilgi varsa kullaniciya **soru uretir** (clarification)
- Uygun **tool**'u secer, guvenliyse islemi yapar
- Turkce **cevap taslagi** uretir, **audit log** tutar, ticket'i kapatir

**Konusma notu:** "Cozumumuz bir AI Agent. Fakat bu bir sohbet botu degil — gercek
bir IT ticket otomasyon prototipi. Agent, ticketi bastan sona bir helpdesk uzmani
gibi ele aliyor: okuyor, siniflandiriyor, risk degerlendirmesi yapiyor ve ancak
guvenliyse aksiyon aliyor."

**Demo ekrani:** Bir ticket sec (**TCK-001**) → sol panelde **Analyze / Run / Reply /
Close / Reset** butonlarini goster.

---

## Slayt 4 — MCP ve Tool Calling Nedir?
**Baslik:** MCP Mantigi ve Tool Calling

- **MCP (Model Context Protocol):** AI modelinin dis arac/veri kaynaklarina standart
  bir sozlesme ile eristigi mimari
- Bu demoda gercek MCP server yok — **MCP mantigi simule** edildi
- Her tool ayri bir fonksiyon; standart girdi/cikti sozlesmesi var
- AI **sinirsiz erisemez**; yalnizca **tanimli tool'lari** cagirabilir (Tool Calling)
- Ornek tool'lar: `search_mailbox`, `copy_attachment_to_desktop`, `check_mock_erp_order`

**Konusma notu:** "MCP, yapay zeka ile araclar arasindaki koprudur. Buradaki kritik
guvenlik ilkesi su: AI dogrudan dosya sistemine ya da sunuculara erisemez. Sadece
bizim tanimladigimiz, sinirli ve guvenli tool'lari cagirabilir. Yani AI'nin ne
yapabilecegini biz belirliyoruz."

**Demo ekrani:** **TCK-001**'de **Analyze Ticket**'a bas → ana paneldeki **AI Analysis**
bolumunde `Selected Tool` alanini goster (`copy_attachment_to_desktop`).

---

## Slayt 5 — Mimari
**Baslik:** Sistem Mimarisi

- **Streamlit UI** → kullanici arayuzu
- **AI Agent** → Ollama (varsa) veya **rule-based fallback**
- **Risk Engine** → Low / Medium / High kararlari
- **MCP Tools** → 11 simule tool; **Response Generator** → cevap taslagi
- **Audit Logger** → her islem JSONL log'a yazilir
- Veri: `data/*.json` + fake ortam: `demo_environment/*`

**Konusma notu:** "Mimari modulerdir. Her katmanin tek bir sorumlulugu var. En onemli
detay: AI ne siniflandirirsa siniflandirsin, risk karari her zaman bagimsiz bir Risk
Engine tarafindan yeniden dogrulanir. AI'ya korsuz guvenmiyoruz."

**Demo ekrani:** **AI Analysis** bolumunu tam goster: `Category`, `Intent`,
`Risk Level` (renkli rozet), `Confidence`, `Reasoning Summary`.

---

## Slayt 6 — Guvenlik Tasarimi (Ana Vurgu)
**Baslik:** Guvenlik: "Yetenek Degil, Kontrollu Yetenek"

- **Gercek sirket verisi kullanilmadi** — mail, SAP/ERP, kullanici PC'si yok
- Demo **tamamen local ve guvenli**; her sey fake klasorlerde simule edilir
- AI **dogrudan sistemlere sinirsiz erisemez** — sadece tanimli tool'lari kullanir
- **Riskli islemler otomatik yapilmaz:** High = blocked, Medium = onay gerekir
- **Dosya silme tool'u hic yazilmadi**; **her islem loglanir** (Audit Log)

**Konusma notu:** "Bu slayt projenin kalbi. AI agent'larla ilgili en buyuk endise
kontrolsuz erisim. Biz bunu tasarimla cozduk: yuksek riskli hicbir islem otomatik
calismaz, dosya silme yetenegi hic yok ve tum dosya islemleri fake klasorlerle
sinirli. Yani mesele AI'ya guc vermek degil, ona kontrollu guc vermek."

**Demo ekrani:** **TCK-008** (admin yetkisi) sec → **Analyze** → **Run Safe Action** →
ekranda **Blocked / High risk** uyarisini goster. AI'nin islemi **reddettigini** vurgula.

---

## Slayt 7 — Canli Demo: Basarili Senaryo
**Baslik:** Demo 1 — Mail Eki → Masaustu (Otomatik Cozum)

- **TCK-001:** "Maildeki rapor dosyasini masaustume tasir misiniz?"
- AI kategori: **Mail Attachment Transfer**, risk: **Low**
- Tool: `copy_attachment_to_desktop` → `rapor.xlsx` kopyalanir
- Turkce cevap taslagi uretilir, ticket **Resolved** olur
- Islem **Audit Log**'a yazilir

**Konusma notu:** "Simdi uctan uca basarili bir akis gosterecegim. Dikkat edin —
dosya gercekten fake masaustu klasorune kopyalaniyor, cevap otomatik uretiliyor ve
ticket kapaniyor. Hepsi loglaniyor."

**Demo ekrani:** **TCK-001** → **Analyze** → **Run Safe Action** → **Generate Reply**
→ **Close Ticket**. En altta **Demo Environment Preview**'da dosyanin **Fake Desktop**'ta
belirdigini goster; **Audit Logs** tablosunu goster.

---

## Slayt 8 — Canli Demo: Belirsizlik ve Read-Only
**Baslik:** Demo 2 — AI Ne Zaman DURUR?

- **TCK-002:** Coklu ekli dosya → AI islem yapmaz, **soru sorar** (clarification)
- **TCK-004:** ERP uretim emri sorgusu → **read-only** okuma (Mock ERP)
- **TCK-003 / TCK-005:** Medium risk → otomatik calismaz; "**IT onayi ver**" kutusu isaretlenince calisir
- AI belirsizlikte **aksiyon almaz**, once netlestirme ister
- Read-only islemler guvenlidir ama yine de loglanir

**Konusma notu:** "Iyi bir agent, ne zaman duracagini bilen agent'tir. TCK-002'de
birden fazla dosya oldugu icin AI tahmin yurutmuyor, kullaniciya soruyor. TCK-004'te
ise sadece okuma yapiyor, hicbir sey degistirmiyor. Bu, guvenli otomasyonun temel
ilkesi."

**Demo ekrani:** **TCK-002** → **Analyze** → **Run Safe Action** (clarification cikar) →
sonra **TCK-004** → **Analyze** → **Run** (Mock ERP status okunur, `100234 = Open`).

---

## Slayt 9 — Teknik Detay: Dayaniklilik
**Baslik:** Her Ortamda Calisan Demo

- AI motoru: **Ollama** local model (varsa) — ornek `qwen3:8b`
- Model yoksa **rule-based fallback** devreye girer → demo **bozulmaz**
- Kod **moduler**: her fonksiyonun tek sorumlulugu var
- Hatalar `try/except` ile yakalanir, yollar `pathlib` ile yonetilir
- Tek komutla calisir: `streamlit run app.py`

**Konusma notu:** "Sunum ortaminda internet ya da GPU olmayabilir. Bu yuzden sistemi
iki modlu tasarladim: Ollama varsa gercek bir LLM kullaniyor, yoksa kural tabanli
mod devreye giriyor. Boylece demo her ortamda ayni sekilde calisiyor — su an gordugunuz
gibi."

**Demo ekrani:** Sayfanin ustundeki **AI Motoru rozeti**ni goster (Ollama aktif /
rule-based demo mode). **Reset Demo Data** butonuna basip demoyu sifirla.

---

## Slayt 10 — Gelecek Entegrasyonlar & Kapanis
**Baslik:** Konsepten Gercek Sisteme

- **Ticket sistemi:** Jira / ServiceNow / OTRS entegrasyonu
- **Mail:** Microsoft Graph API ile gercek attachment okuma
- **Endpoint Automation:** Intune / SCCM ile cihaz islemleri
- **SAP / ERP:** read-only API entegrasyonu
- Role-based authorization, human approval workflow, SIEM/log monitoring, KPI dashboard

**Konusma notu:** "Bu bir konsept prototipi; amac fikri ve guvenlik mimarisini
gostermek. Ayni yapi gelecekte gercek ticket sistemi, Microsoft Graph, Intune/SCCM,
SAP/ERP ve mail sistemleriyle entegre edilebilir — cunku tool tabanli mimari tam da
bunun icin tasarlandi. Ozetle: guvenli, kontrollu ve genisletilebilir bir AI otomasyon
temeli sunuyorum. Tesekkurler, sorulari memnuniyetle alirim."

**Demo ekrani:** — (Kapanis slayti) veya soru-cevap sirasinda merak edilen ticket'i
canli gosterebilirsin.

---

### Sunum Ipuclari
- **Toplam sure:** ~8-10 dakika sunum + 3-4 dakika demo.
- Demo oncesi mutlaka **Reset Demo Data** ile temiz baslat.
- En etkili final: **TCK-001 (basari)** → **TCK-002 (durus)** → **TCK-008 (engelleme)**.
- Bir sey ters giderse: rule-based mode her zaman calisir, panige gerek yok.
