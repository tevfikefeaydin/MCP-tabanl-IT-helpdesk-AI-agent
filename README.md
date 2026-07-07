# MCP-Based AI Helpdesk Agent Demo
### MCP Tabanli Yapay Zeka Destekli Bilgi Islem Ticket Otomasyonu

Bilgi islem ekiplerine gelen tekrar eden ve dusuk riskli ticketlarin yapay zeka
destekli analiz edilmesini ve **guvenli, simule edilmis tool'lar** araciligiyla
cozume yonlendirilmesini gosteren bir **demo** uygulamasidir.

> Bu proje bir staj sunumu icin gelistirilmis bir **konsept prototipidir**.
> Gercek sirket sistemlerine (mail, SAP/ERP, kullanici bilgisayari) **baglanmaz**.

---

## 1. Project Title / Proje Adi
**ai-helpdesk-agent-demo** — "MCP-Based AI Helpdesk Agent Demo"

## 2. Project Purpose / Amac
IT helpdesk ekiplerine gelen standart ticketlarin (mail eki tasima, yazici sorunu,
disk kontrolu, yazilim envanteri, ERP durum sorgusu vb.) bir AI agent tarafindan
nasil analiz edilip, risk seviyesine gore guvenli sekilde cozulebilecegini gostermek.

## 3. Problem Definition / Problem Tanimi
Bilgi islem ekiplerine gelen ticketlarin buyuk bir kismi standart ve tekrar edendir.
Personel ticketi okur, niyeti anlar, ilgili sistemi kontrol eder, islemi yapar,
kullaniciya cevap yazar ve ticketi kapatir. Bu surec zaman alir ve otomasyona uygundur.

## 4. Proposed Solution / Onerilen Cozum
AI agent bu surecin tamamini simule eder:
1. Ticketi okur → 2. Niyeti/kategoriyi belirler → 3. Risk seviyesini hesaplar →
4. Eksik bilgi varsa soru uretir → 5. Uygun simule tool'u secer →
6. Guvenliyse fake klasorlerde islem yapar → 7. Cevap taslagi uretir →
8. Audit log tutar → 9. Ticket durumunu gunceller.

## 5. What is MCP in this demo? / Bu demoda MCP nedir?
**MCP (Model Context Protocol)**, bir AI modelinin dis dunyadaki arac/veri
kaynaklarina standart bir sozlesme ile eristigi bir mimaridir. Bu demoda gercek bir
MCP server kurulmaz; bunun yerine `src/mcp_tools.py` icinde **MCP mantigi simule
edilir**: her tool ayri bir fonksiyondur, standart bir girdi/cikti sozlesmesine sahiptir
ve agent bu tool'lardan hangisini cagiracagina karar verir. Boylece "AI + arac cagirma"
mimarisi guvenli bir ortamda gosterilir.

## 6. Architecture / Mimari
```
Streamlit UI (app.py)
        |
        v
   AI Agent (src/ai_agent.py)  --> Ollama (varsa)  /  Rule-based fallback
        |
        +--> Risk Engine (src/risk_engine.py)      Low / Medium / High kararlari
        +--> MCP Tools   (src/mcp_tools.py)         11 simule tool
        +--> Response Gen(src/response_generator.py) Turkce cevap taslagi
        +--> Audit Logger(src/audit_logger.py)      JSONL denetim kaydi
        |
        v
   Local Data (data/*.json)  +  Fake Env (demo_environment/*)
```
**Guvenlik kapilari:** High risk asla otomatik calismaz; Medium risk onay gerektirir;
her islem loglanir; LLM'in verdigi risk karari her zaman `risk_engine` tarafindan
tekrar dogrulanir.

## 7. Folder Structure / Klasor Yapisi
```
ai-helpdesk-agent-demo/
├── app.py                     # Streamlit arayuzu
├── requirements.txt
├── README.md
├── data/                      # Simule veri (ticket, user, printer, ERP, software, KB)
│   ├── tickets.json
│   ├── users.json
│   ├── printers.json
│   ├── mock_erp_orders.json
│   ├── software_inventory.json
│   └── knowledge_base.json
├── demo_environment/
│   ├── fake_mailbox/<user>/   # mails.json + attachments/ (sahte ekler)
│   ├── fake_desktops/<user>/  # Desktop/ (kopyalanan dosyalarin gidecegi yer)
│   └── fake_logs/             # action_log.jsonl (audit)
├── src/
│   ├── __init__.py
│   ├── utils.py               # JSON okuma/yazma, path (pathlib), zaman
│   ├── demo_data_loader.py    # veri yukleme + reset
│   ├── mcp_tools.py           # 11 simule MCP tool
│   ├── risk_engine.py         # risk seviyesi + onay kurallari
│   ├── ai_agent.py            # Ollama/rule-based analiz + aksiyon
│   ├── response_generator.py  # Turkce cevap taslaklari
│   ├── audit_logger.py        # denetim loglari
│   └── ticket_manager.py      # ticket durum yonetimi
└── screenshots/
```

## 8. Setup Instructions / Kurulum
```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## 9. How to Run / Nasil Calistirilir
```bash
streamlit run app.py
```
Tarayicida `http://localhost:8501` acilir.

**Ollama (opsiyonel):** Local LLM ile calistirmak isterseniz:
```bash
ollama run qwen3:8b
```
Ollama yoksa uygulama **otomatik olarak rule-based demo mode** ile calisir; demo bozulmaz.
Model adini `src/ai_agent.py` icindeki `DEFAULT_MODEL` degiskeninden degistirebilirsiniz.

## 10. Demo Scenarios / Demo Senaryolari
| Ticket | Kategori | Risk | Beklenen davranis |
|--------|----------|------|-------------------|
| **TCK-001** | Mail Attachment Transfer | Low | `rapor.xlsx` fake mailbox'tan fake desktop'a kopyalanir, cevap uretilir |
| **TCK-002** | Mail Attachment Transfer | Low | Coklu ek → **clarification** (dosya adi sorulur), islem yapilmaz |
| **TCK-003** | Printer Issue | Medium | Muhasebe_HP_01 icin `reconnect` — otomatik calismaz, "IT onayi ver" kutusu ile calistirilir |
| **TCK-004** | ERP Production Order Check | Low | `100234` emri **read-only** okunur, durumu gosterilir |
| **TCK-005** | Disk Space | Medium | Disk kullanimi simule edilir, temizlik onerisi (onay ister) |
| **TCK-006** | VPN Issue | Low | KB'den troubleshooting cevap taslagi, otomatik aksiyon **yok** |
| **TCK-007** | Software Inventory Check | Low | Excel kurulu mu envanterden kontrol edilir |
| **TCK-008** | High Risk Access Request | High | Admin yetki talebi → **blocked**, otomatik calismaz |

## 11. Security Notes / Guvenlik Notlari
- Demo **gercek sirket sistemlerine baglanmaz**.
- Gercek mail hesabi, gercek SAP/ERP, gercek kullanici bilgisayari kullanilmaz.
- Tum islemler local **fake klasorler** uzerinde simule edilir.
- Dosya kopyalama sadece `fake_mailbox → fake_desktop` arasinda olur; yol guvenligi
  (`safe_within`) ile fake klasor disina cikilmasi engellenir.
- **Dosya silme tool'u bilincli olarak yazilmamistir.**
- **High risk** islemler otomatik calistirilmaz.
- **Medium risk** islemler onay gerektirir.
- Her islem **audit log**'a yazilir.
- Amac gercek deployment degil, **konsept gosterimidir**.

## 12. Limitations / Kisitlar
- Tool'lar gercek islem yapmaz; ciktilar simulasyondur (ornek: disk kullanimi sabittir).
- LLM cikti kalitesi kullanilan modele baglidir; risk kararlari her durumda kural
  motoruyla dogrulanir.
- Ek dosyalari (`.xlsx`, `.pdf`, `.docx`) gercek belge degil, demo placeholder'lardir.

## 13. Future Improvements / Gelecek Gelistirmeler
- Gercek ticket sistemi entegrasyonu (Jira / ServiceNow / OTRS)
- Microsoft Graph API ile mail attachment okuma
- Intune / SCCM ile endpoint automation
- SAP / ERP read-only API entegrasyonu
- Role-based authorization
- Human approval workflow
- Model fine-tuning veya RAG knowledge base
- SIEM / log monitoring entegrasyonu
- Dashboard ve KPI raporlari
- Coklu dil destegi
- SLA onceliklendirme
- Otomatik ticket routing

## 14. Internship Presentation Notes / Sunum Notlari

**Sunum ozeti:**
> Bu proje, bilgi islem ekiplerine gelen tekrar eden ve dusuk riskli ticketlarin yapay
> zeka destekli olarak analiz edilmesini ve guvenli tool'lar araciligiyla cozume
> yonlendirilmesini simule eden bir demo uygulamasidir. Uygulama gercek sirket
> sistemlerine baglanmaz; ticket, mail, masaustu, printer ve ERP surecleri local fake
> verilerle temsil edilir. Amac, MCP benzeri bir tool mimarisiyle AI agent'in ticketi
> nasil okuyabilecegini, dogru aksiyonu nasil secebilecegini, risk seviyesini nasil
> degerlendirebilecegini ve kullaniciya nasil cevap taslagi olusturabilecegini gostermektir.

**Onerilen sunum sirasi:**
1. TCK-001 → basarili otomatik cozum (mail eki → masaustu, cevap, kapatma).
2. TCK-002 → belirsizlik yonetimi (clarification, islem yapmama).
3. TCK-004 → read-only ERP sorgusu (Low risk, guvenli okuma).
4. TCK-003 / TCK-005 → Medium risk: otomatik calismaz, "IT onayi ver" kutusu ile calistirilir.
5. TCK-008 → High risk + otomatik engelleme.
6. Audit Log ve Demo Environment Preview panelleri ile izlenebilirlik.

**Guvenlik anlatimi (nasil aktarilir):**
Agent'in "aksiyon" yetkisi kasitli olarak sinirlandirilmistir. Risk motoru her karari
bagimsiz dogrular; LLM'e korsuz guvenilmez. Yuksek riskli hicbir islem otomatik
calismaz, dosya silme yetenegi hic yoktur ve tum dosya islemleri fake klasorlerle
sinirlidir. Bu, "AI agent'lar tehlikeli olabilir mi?" sorusuna verilen somut bir
guvenlik-tasarimi cevabidir: yetenek degil, **kontrollu yetenek**.
