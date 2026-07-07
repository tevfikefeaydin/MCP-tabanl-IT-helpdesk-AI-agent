"""
risk_engine.py
Ticket kategorisine ve secilen tool'a gore risk seviyesini belirler.

Risk seviyeleri:
  Low    -> Read-only kontrol, siniflandirma, cevap taslagi, fake dosya kopyalama, ERP status.
  Medium -> Endpoint ayari simulasyonu, printer reconnect, disk temizligi onerisi, program kurulum onerisi.
  High   -> Admin yetkisi, dosya silme, yetki degistirme, antivirus/firewall degisikligi, write action.

Kurallar:
  - High risk HICBIR ZAMAN otomatik calismaz (blocked = True).
  - Medium risk onay gerektirir (requires_approval = True).
  - Low risk otomatik calisabilir ama yine de loglanir.
"""

from __future__ import annotations

# Kategori bazli varsayilan risk haritasi
CATEGORY_RISK = {
    "Mail Attachment Transfer": "Low",
    "ERP Production Order Check": "Low",
    "Software Inventory Check": "Low",
    "Printer Issue": "Medium",
    "Disk Space": "Medium",
    "VPN Issue": "Low",  # Sadece cevap taslagi uretilir, otomatik aksiyon yok
    "High Risk Access Request": "High",
    "General IT Support": "Low",
}

# Tool bazli risk (tool secildiyse kategoriye gore daha guvenli karar verir)
TOOL_RISK = {
    "read_ticket": "Low",
    "search_mailbox": "Low",
    "copy_attachment_to_desktop": "Low",
    "check_printer_status": "Low",
    "reconnect_printer": "Medium",
    "check_mock_erp_order": "Low",
    "check_software_installed": "Low",
    "check_disk_status": "Medium",
    "generate_clarification_question": "Low",
    "close_ticket": "Low",
}

# High risk tetikleyen anahtar kelimeler (ekstra guvenlik katmani)
HIGH_RISK_KEYWORDS = [
    "admin",
    "administrator",
    "yetki",
    "sil",
    "delete",
    "format",
    "antivirus",
    "firewall",
    "sifre sifirla",
    "password reset",
]

_LEVEL_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def _max_level(a: str, b: str) -> str:
    """Iki risk seviyesinden yuksek olani doner."""
    return a if _LEVEL_ORDER.get(a, 0) >= _LEVEL_ORDER.get(b, 0) else b


def assess_risk(category: str, selected_tool: str | None = None, ticket_text: str = "") -> dict:
    """
    Risk degerlendirmesi yapar.

    Doner:
      {
        "risk_level": "Low" | "Medium" | "High",
        "requires_approval": bool,
        "blocked": bool,
        "reason": str
      }
    """
    # 1) Kategori bazli baslangic
    level = CATEGORY_RISK.get(category, "Low")

    # 2) Tool bazli seviye ile birlestir (daha yuksek olani al)
    if selected_tool and selected_tool in TOOL_RISK:
        level = _max_level(level, TOOL_RISK[selected_tool])

    # 3) High-risk anahtar kelime taramasi (metin tabanli ek guvenlik)
    text_lower = (ticket_text or "").lower()
    if any(kw in text_lower for kw in HIGH_RISK_KEYWORDS):
        level = _max_level(level, "High")

    # 4) Karar kurallari
    if level == "High":
        return {
            "risk_level": "High",
            "requires_approval": True,
            "blocked": True,
            "reason": "Bu islem yuksek riskli oldugu icin otomatik gerceklestirilemez ve bilgi islem yetkilisi onayi gerektirir.",
        }
    if level == "Medium":
        return {
            "risk_level": "Medium",
            "requires_approval": True,
            "blocked": False,
            "reason": "Bu islem endpoint/konfigurasyon degisikligi icerdigi icin IT onayi onerilir.",
        }
    return {
        "risk_level": "Low",
        "requires_approval": False,
        "blocked": False,
        "reason": "Dusuk riskli read-only/guvenli islem. Otomatik calistirilabilir, yine de loglanir.",
    }
