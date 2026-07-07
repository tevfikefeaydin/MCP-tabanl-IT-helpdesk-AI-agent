"""
ai_agent.py
Ticket'i analiz eden AI agent.

Iki calisma modu vardir:
  1) Ollama modu  -> localhost:11434 uzerinde model varsa LLM ile analiz.
  2) Rule-based   -> Model yoksa anahtar kelime tabanli fallback (demo her ortamda calisir).

Agent ciktisi her zaman ayni JSON semasindadir:
  {
    "category", "intent", "risk_level", "confidence",
    "clarification_needed", "selected_tool", "reasoning_summary",
    "recommended_action", "can_execute_automatically", "engine"
  }
"""

from __future__ import annotations

import json
import re

from . import demo_data_loader as loader
from . import mcp_tools
from . import risk_engine

# Ollama ayarlari (config gibi degistirilebilir)
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"

# Kategori -> (intent, tool) esleme tablosu
CATEGORY_MAP = {
    "Mail Attachment Transfer": ("copy_mail_attachment_to_desktop", "copy_attachment_to_desktop"),
    "Printer Issue": ("reconnect_printer", "reconnect_printer"),
    "ERP Production Order Check": ("check_production_order_status", "check_mock_erp_order"),
    "Disk Space": ("check_endpoint_disk", "check_disk_status"),
    "VPN Issue": ("provide_vpn_troubleshooting", None),
    "Software Inventory Check": ("check_installed_software", "check_software_installed"),
    "High Risk Access Request": ("request_admin_privileges", None),
    "General IT Support": ("general_support", None),
}

# Rule-based siniflandirma icin anahtar kelimeler
KEYWORD_RULES = [
    ("High Risk Access Request", ["admin", "administrator", "yetki"]),
    ("VPN Issue", ["vpn"]),
    ("Printer Issue", ["yazici", "printer", "cikti", "yazıcı", "çıktı"]),
    ("ERP Production Order Check", ["uretim emri", "üretim emri", "order", "emir", "is emri"]),
    ("Disk Space", ["disk", "dolu", "c diski", "depolama"]),
    ("Software Inventory Check", ["kurulu", "excel", "program", "yazilim", "yazılım"]),
    ("Mail Attachment Transfer", ["mail", "dosya", "masaustu", "masaüstü", "ek", "attachment"]),
]


# ---------------------------------------------------------------------------
# Ollama yardimcilari
# ---------------------------------------------------------------------------
def is_ollama_available(timeout: float = 1.0) -> bool:
    """Ollama endpoint'i erisilebilir mi kontrol eder. Yoksa sessizce False doner."""
    try:
        import requests  # yerel import: requests kurulu degilse fallback

        base = OLLAMA_URL.replace("/api/generate", "/api/tags")
        resp = requests.get(base, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def _build_prompt(ticket_text: str) -> str:
    """LLM'e gonderilecek prompt sablonu (yalnizca gecerli JSON istenir)."""
    return f"""You are an enterprise IT helpdesk ticket analysis agent.
Analyze the ticket and return ONLY valid JSON. Do not include chain-of-thought.
Return a short reasoning_summary only.

Ticket:
{ticket_text}

Available categories:
- Mail Attachment Transfer
- Printer Issue
- ERP Production Order Check
- Disk Space
- VPN Issue
- Software Inventory Check
- High Risk Access Request
- General IT Support

Return JSON with keys:
category, intent, risk_level, confidence, clarification_needed,
selected_tool, reasoning_summary, recommended_action, can_execute_automatically

Important:
High risk actions must never be executed automatically.
If the request is ambiguous, set clarification_needed true.
If multiple possible files are found, ask for clarification.
"""


def _query_ollama(ticket_text: str, model: str, timeout: float = 30.0) -> dict | None:
    """Ollama'ya sorar ve JSON cevabini parse eder. Basarisiz olursa None doner."""
    try:
        import requests

        payload = {
            "model": model,
            "prompt": _build_prompt(ticket_text),
            "stream": False,
            "format": "json",
        }
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        if resp.status_code != 200:
            return None
        raw = resp.json().get("response", "")
        # Cevap icindeki ilk JSON blogunu ayikla
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        return json.loads(match.group(0))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Rule-based siniflandirma
# ---------------------------------------------------------------------------
def _classify_category(text: str) -> str:
    """Anahtar kelimelere gore kategori belirler. Oncelik sirasi risklidir->genel."""
    lower = text.lower()
    for category, keywords in KEYWORD_RULES:
        if any(kw in lower for kw in keywords):
            return category
    return "General IT Support"


def _extract_order_id(text: str) -> str | None:
    """Metinden uretim emri numarasini (5-6 haneli) cikarir."""
    match = re.search(r"\b(\d{5,6})\b", text)
    return match.group(1) if match else None


def _extract_software_name(text: str) -> str:
    """Metinden yazilim adini tahmin eder (basit eslesme)."""
    lower = text.lower()
    known = {
        "excel": "Microsoft Excel",
        "word": "Microsoft Word",
        "teams": "Microsoft Teams",
        "chrome": "Google Chrome",
        "sap": "SAP GUI",
        "adobe": "Adobe Reader",
    }
    for key, name in known.items():
        if key in lower:
            return name
    return "Belirtilen yazilim"


def _resolve_mail_target(requester: str, text: str) -> dict:
    """
    Mail attachment senaryosu icin hedef dosyayi cozer.
    Doner: {"clarification": bool, "target_file": str|None, "matches": list, "keyword": str|None}
    """
    attachments = loader.list_mailbox_attachments(requester)
    lower = text.lower()

    # Dosya adi govdesine gore eslesme ara (ornek: "rapor" -> rapor.xlsx)
    matched = [a for a in attachments if a.split(".")[0].lower() in lower]

    if len(matched) == 1:
        return {"clarification": False, "target_file": matched[0], "matches": attachments, "keyword": matched[0].split(".")[0]}
    if len(matched) == 0 and len(attachments) == 1:
        # Tek dosya varsa netlestirmeye gerek yok
        return {"clarification": False, "target_file": attachments[0], "matches": attachments, "keyword": None}
    # 0 eslesme ve coklu dosya YA DA coklu eslesme -> netlestirme gerekli
    return {"clarification": True, "target_file": None, "matches": attachments, "keyword": None}


def _rule_based_analyze(ticket: dict) -> dict:
    """Kural tabanli tam analiz. Ollama yoksa veya basarisizsa kullanilir."""
    text = f"{ticket.get('title', '')} {ticket.get('description', '')}"
    requester = ticket.get("requester", "")
    category = _classify_category(text)
    intent, tool = CATEGORY_MAP.get(category, ("general_support", None))

    clarification_needed = False
    recommended_action = "Ilgili kayitlar kontrol edilecek."
    confidence = 0.85

    if category == "Mail Attachment Transfer":
        resolved = _resolve_mail_target(requester, text)
        if resolved["clarification"]:
            clarification_needed = True
            tool = "generate_clarification_question"
            intent = "ask_which_attachment"
            recommended_action = "Kullanicidan hangi dosyayi kastettigini netlestirmesi istenecek."
            confidence = 0.6
        else:
            target = resolved["target_file"]
            recommended_action = f"{target} dosyasi fake mailbox'tan fake desktop'a kopyalanacak."
            confidence = 0.92

    elif category == "Printer Issue":
        recommended_action = "Ilgili yazici bulunup 'printer reconnect' islemi simule edilecek."
        confidence = 0.88

    elif category == "ERP Production Order Check":
        order_id = _extract_order_id(text)
        recommended_action = f"{order_id or 'Belirtilen'} numarali uretim emri durumu read-only olarak okunacak."
        confidence = 0.9

    elif category == "Disk Space":
        recommended_action = "Endpoint disk durumu simule edilerek kontrol edilecek. Temizlik onerisi sunulacak."
        confidence = 0.87

    elif category == "VPN Issue":
        recommended_action = "Knowledge base'den VPN sorun giderme adimlari cevap taslagi olarak sunulacak. Otomatik aksiyon yok."
        confidence = 0.86

    elif category == "Software Inventory Check":
        sw = _extract_software_name(text)
        recommended_action = f"{sw} cihazda kurulu mu envanterden kontrol edilecek."
        confidence = 0.9

    elif category == "High Risk Access Request":
        recommended_action = "Yuksek riskli yetki talebi. Otomatik aksiyon engellenecek, IT onayi istenecek."
        confidence = 0.95

    # Risk degerlendirmesi
    risk = risk_engine.assess_risk(category, tool, text)

    # Otomatik calisabilir mi? Sadece Low risk, guvenli tool'lar otomatik calisir.
    # High/blocked, Medium/onay-gerektiren veya clarification varsa otomatik calismaz.
    can_execute = (
        not risk["blocked"]
        and not risk["requires_approval"]
        and not clarification_needed
        and tool is not None
        and tool != "generate_clarification_question"
    )

    return {
        "category": category,
        "intent": intent,
        "risk_level": risk["risk_level"],
        "confidence": confidence,
        "clarification_needed": clarification_needed,
        "selected_tool": tool,
        "reasoning_summary": _short_reason(category, clarification_needed),
        "recommended_action": recommended_action,
        "can_execute_automatically": can_execute,
        "requires_approval": risk["requires_approval"],
        "blocked": risk["blocked"],
        "risk_reason": risk["reason"],
        "engine": "rule-based",
    }


def _short_reason(category: str, clarification: bool) -> str:
    """Kisa reasoning_summary (tam chain-of-thought verilmez)."""
    if clarification:
        return "Birden fazla olasi dosya bulundugu icin islem netlestirme gerektiriyor."
    reasons = {
        "Mail Attachment Transfer": "Ticket mail ekinin masaustune tasinmasini istiyor ve dosya tespit edildi.",
        "Printer Issue": "Ticket yazici cikti sorununu tarif ediyor.",
        "ERP Production Order Check": "Ticket bir uretim emrinin durumunu soruyor (read-only).",
        "Disk Space": "Ticket disk doluluk uyarisini bildiriyor.",
        "VPN Issue": "Ticket VPN baglanti sorununu tarif ediyor.",
        "Software Inventory Check": "Ticket bir yazilimin kurulu olup olmadigini soruyor.",
        "High Risk Access Request": "Ticket yuksek riskli yetki degisikligi talep ediyor.",
        "General IT Support": "Ticket genel IT destek kategorisine giriyor.",
    }
    return reasons.get(category, "Ticket analiz edildi.")


# ---------------------------------------------------------------------------
# Genel giris noktasi
# ---------------------------------------------------------------------------
def analyze_ticket(ticket: dict, use_ollama: bool = True, model: str = DEFAULT_MODEL) -> dict:
    """
    Ticket'i analiz eder. Once Ollama denenir (istenirse), basarisizsa rule-based fallback.
    Her durumda ayni JSON semasi doner.
    """
    # Rule-based sonucu her zaman referans/dogrulama icin hazirla
    base = _rule_based_analyze(ticket)

    if use_ollama and is_ollama_available():
        text = f"{ticket.get('title', '')}\n{ticket.get('description', '')}"
        llm = _query_ollama(text, model)
        if llm:
            # LLM ciktisini rule-based iskelet uzerine guvenli sekilde birlestir.
            merged = base.copy()
            for key in [
                "category",
                "intent",
                "risk_level",
                "confidence",
                "clarification_needed",
                "selected_tool",
                "reasoning_summary",
                "recommended_action",
                "can_execute_automatically",
            ]:
                if key in llm and llm[key] is not None:
                    merged[key] = llm[key]

            # GUVENLIK: risk kararini her zaman risk_engine dogrular (LLM'e korsuz guvenilmez).
            risk = risk_engine.assess_risk(
                merged.get("category", base["category"]),
                merged.get("selected_tool"),
                text,
            )
            merged["risk_level"] = risk["risk_level"]
            merged["requires_approval"] = risk["requires_approval"]
            merged["blocked"] = risk["blocked"]
            merged["risk_reason"] = risk["reason"]
            if risk["blocked"] or risk["requires_approval"] or merged.get("clarification_needed"):
                merged["can_execute_automatically"] = False
            merged["engine"] = f"ollama:{model}"
            return merged

    return base


# ---------------------------------------------------------------------------
# Aksiyon calistirma (analiz -> dogru tool cagrisi)
# ---------------------------------------------------------------------------
def execute_action(ticket: dict, analysis: dict) -> dict:
    """
    Analize gore secilen simule tool'u calistirir.

    Guvenlik kapilari:
      - blocked (High risk) ise hicbir tool calismaz.
      - clarification gerekiyorsa netlestirme sorusu uretilir.
    Doner: mcp_tools standart sonuc formati.
    """
    # High risk / engellenmis -> aksiyon yok
    if analysis.get("blocked"):
        return mcp_tools._result(
            False,
            "blocked",
            "Yuksek riskli islem otomatik calistirilamaz. IT onayi gereklidir.",
            {"risk_level": analysis.get("risk_level")},
        )

    # Netlestirme gerekiyor -> soru uret
    if analysis.get("clarification_needed"):
        return mcp_tools.generate_clarification_question(ticket)

    tool = analysis.get("selected_tool")
    requester = ticket.get("requester", "")
    text = f"{ticket.get('title', '')} {ticket.get('description', '')}"

    if tool == "copy_attachment_to_desktop":
        resolved = _resolve_mail_target(requester, text)
        target = resolved.get("target_file")
        if not target:
            return mcp_tools.generate_clarification_question(ticket)
        return mcp_tools.copy_attachment_to_desktop(requester, target)

    if tool == "reconnect_printer":
        printer = _resolve_printer(ticket)
        return mcp_tools.reconnect_printer(printer)

    if tool == "check_mock_erp_order":
        order_id = _extract_order_id(text)
        if not order_id:
            return mcp_tools._result(False, "check_mock_erp_order", "Emir numarasi tespit edilemedi.", {})
        return mcp_tools.check_mock_erp_order(order_id)

    if tool == "check_disk_status":
        return mcp_tools.check_disk_status(requester)

    if tool == "check_software_installed":
        software = _extract_software_name(text)
        return mcp_tools.check_software_installed(requester, software)

    # VPN / genel -> sadece bilgi, tool yok
    return mcp_tools._result(
        True,
        "no_tool",
        "Bu kategori icin otomatik tool calistirilmadi; cevap taslagi uretilecek.",
        {"category": analysis.get("category")},
    )


def _resolve_printer(ticket: dict) -> str:
    """Ticket'in departmanina/metnine gore ilgili yaziciyi bulur."""
    text = f"{ticket.get('title', '')} {ticket.get('description', '')}".lower()
    for printer in loader.load_printers():
        if printer.get("department", "").lower() in text:
            return printer["printer_name"]
    # Varsayilan: muhasebe yazicisi (demo senaryosu TCK-003)
    return "Muhasebe_HP_01"
