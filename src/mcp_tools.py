"""
mcp_tools.py
MCP (Model Context Protocol) mantigini SIMULE eden tool koleksiyonu.

Onemli guvenlik ilkeleri:
  - Hicbir tool gercek sistemlere baglanmaz.
  - Dosya islemleri SADECE demo_environment ve data klasorleri icinde yapilir.
  - Dosya kopyalama sadece fake mailbox -> fake desktop arasinda olur.
  - Dosya SILME tool'u BILINCLI olarak yazilmamistir.

Her tool ortak formatta sonuc doner:
  {
    "success": bool,
    "tool_name": str,
    "message": str,
    "details": dict
  }
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import demo_data_loader as loader
from . import utils


def _result(success: bool, tool_name: str, message: str, details: dict | None = None) -> dict:
    """Standart tool cikti formatini uretir."""
    return {
        "success": success,
        "tool_name": tool_name,
        "message": message,
        "details": details or {},
    }


# ---------------------------------------------------------------------------
# 1) read_ticket
# ---------------------------------------------------------------------------
def read_ticket(ticket_id: str) -> dict:
    """Ticket detayini okur (read-only)."""
    ticket = loader.get_ticket(ticket_id)
    if ticket is None:
        return _result(False, "read_ticket", f"{ticket_id} bulunamadi.", {})
    return _result(True, "read_ticket", f"{ticket_id} okundu.", {"ticket": ticket})


# ---------------------------------------------------------------------------
# 2) search_mailbox
# ---------------------------------------------------------------------------
def search_mailbox(username: str, keyword: str | None = None) -> dict:
    """
    Fake mailbox eklerini arar. keyword verilirse dosya adi/mail konusuna gore filtreler.
    Birden fazla eslesme donerse cagiran taraf clarification'a karar verebilir.
    """
    mails = utils.read_json(utils.MAILBOX_DIR / username / "mails.json", default=[])
    matches: list[dict] = []
    for mail in mails:
        for attachment in mail.get("attachments", []):
            if keyword:
                haystack = f"{attachment} {mail.get('subject', '')}".lower()
                if keyword.lower() not in haystack:
                    continue
            matches.append(
                {
                    "attachment": attachment,
                    "mail_subject": mail.get("subject", ""),
                    "mail_id": mail.get("mail_id", ""),
                }
            )
    return _result(
        True,
        "search_mailbox",
        f"{len(matches)} ekli dosya bulundu.",
        {"matches": matches, "count": len(matches)},
    )


# ---------------------------------------------------------------------------
# 3) copy_attachment_to_desktop
# ---------------------------------------------------------------------------
def copy_attachment_to_desktop(username: str, filename: str) -> dict:
    """
    Fake mailbox eklentisini fake desktop'a KOPYALAR (tasima degil, guvenli kopya).
    Yol guvenligi: kaynak mailbox icinde, hedef desktop icinde olmali.
    """
    source = utils.MAILBOX_DIR / username / "attachments" / filename
    dest_dir = utils.DESKTOP_DIR / username / "Desktop"
    dest = dest_dir / filename

    # Guvenlik kontrolleri
    if not utils.safe_within(utils.MAILBOX_DIR, source):
        return _result(False, "copy_attachment_to_desktop", "Kaynak yol gecersiz.", {})
    if not utils.safe_within(utils.DESKTOP_DIR, dest):
        return _result(False, "copy_attachment_to_desktop", "Hedef yol gecersiz.", {})
    if not source.exists():
        return _result(
            False,
            "copy_attachment_to_desktop",
            f"{filename} mailbox'ta bulunamadi.",
            {"source": str(source)},
        )

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
    except OSError as exc:
        return _result(False, "copy_attachment_to_desktop", f"Kopyalama hatasi: {exc}", {})

    return _result(
        True,
        "copy_attachment_to_desktop",
        f"{filename} fake desktop'a kopyalandi.",
        {
            "source": str(source.relative_to(utils.PROJECT_ROOT)),
            "destination": str(dest.relative_to(utils.PROJECT_ROOT)),
        },
    )


# ---------------------------------------------------------------------------
# 4) check_printer_status
# ---------------------------------------------------------------------------
def check_printer_status(printer_name: str) -> dict:
    """Printer durumunu printers.json'dan okur (read-only)."""
    for printer in loader.load_printers():
        if printer.get("printer_name") == printer_name:
            return _result(
                True,
                "check_printer_status",
                f"{printer_name} durumu: {printer.get('status')}.",
                {"printer": printer},
            )
    return _result(False, "check_printer_status", f"{printer_name} bulunamadi.", {})


# ---------------------------------------------------------------------------
# 5) reconnect_printer
# ---------------------------------------------------------------------------
def reconnect_printer(printer_name: str) -> dict:
    """
    Printer yeniden tanimlama islemini SIMULE eder.
    Gercek bir ag/print spooler islemi yapilmaz; sadece demo mesaji donulur.
    """
    for printer in loader.load_printers():
        if printer.get("printer_name") == printer_name:
            return _result(
                True,
                "reconnect_printer",
                f"{printer_name} yeniden tanimlanmis olarak simule edildi.",
                {
                    "printer": printer_name,
                    "simulated_action": "reconnect",
                    "note": "Gercek yazici islemi yapilmadi (demo).",
                },
            )
    return _result(False, "reconnect_printer", f"{printer_name} bulunamadi.", {})


# ---------------------------------------------------------------------------
# 6) check_mock_erp_order
# ---------------------------------------------------------------------------
def check_mock_erp_order(order_id: str) -> dict:
    """Mock ERP uretim emri durumunu okur (read-only)."""
    for order in loader.load_erp_orders():
        if str(order.get("order_id")) == str(order_id):
            return _result(
                True,
                "check_mock_erp_order",
                f"{order_id} numarali uretim emri durumu: {order.get('status')}.",
                {"order": order},
            )
    return _result(False, "check_mock_erp_order", f"{order_id} numarali emir bulunamadi.", {})


# ---------------------------------------------------------------------------
# 7) check_software_installed
# ---------------------------------------------------------------------------
def check_software_installed(username: str, software_name: str) -> dict:
    """Kullanici cihazinda bir yazilimin kurulu olup olmadigini kontrol eder (read-only)."""
    user = loader.get_user(username)
    if user is None:
        return _result(False, "check_software_installed", f"{username} kullanicisi bulunamadi.", {})

    device = user.get("device_name")
    for record in loader.load_software_inventory():
        if record.get("device_name") == device:
            installed = record.get("installed_software", [])
            found = any(software_name.lower() in s.lower() for s in installed)
            return _result(
                True,
                "check_software_installed",
                (
                    f"{software_name} cihazda kurulu."
                    if found
                    else f"{software_name} cihazda kurulu degil."
                ),
                {"device": device, "installed": found, "software_list": installed},
            )
    return _result(False, "check_software_installed", f"{device} cihazi envanterde yok.", {})


# ---------------------------------------------------------------------------
# 8) check_disk_status
# ---------------------------------------------------------------------------
def check_disk_status(username: str) -> dict:
    """
    Disk kullanimini SIMULE eder. Gercek disk okunmaz; demo icin sabit deger donulur.
    """
    user = loader.get_user(username)
    device = user.get("device_name") if user else "UNKNOWN-DEVICE"
    simulated = {
        "device": device,
        "drive": "C:",
        "total_gb": 256,
        "used_gb": 233,
        "usage_percent": 91,
    }
    return _result(
        True,
        "check_disk_status",
        f"{device} C: diski kullanim orani %{simulated['usage_percent']} (simule).",
        simulated,
    )


# ---------------------------------------------------------------------------
# 9) generate_clarification_question
# ---------------------------------------------------------------------------
def generate_clarification_question(ticket: dict) -> dict:
    """
    Eksik bilgi durumunda kullaniciya sorulacak netlestirme sorusunu uretir.
    """
    question = (
        "Birden fazla ekli dosya bulundu. Hangi dosyayi kastettiginizi "
        "dosya adi veya mail konu basligi ile paylasabilir misiniz?"
    )
    return _result(
        True,
        "generate_clarification_question",
        question,
        {"ticket_id": ticket.get("ticket_id", "")},
    )


# ---------------------------------------------------------------------------
# 10) close_ticket
# ---------------------------------------------------------------------------
def close_ticket(ticket_id: str, resolution_text: str) -> dict:
    """
    Ticket durumunu 'Resolved' yapar ve cozum metnini kaydeder.
    Yalnizca data/tickets.json guncellenir.
    """
    tickets = loader.load_tickets()
    updated = False
    for ticket in tickets:
        if ticket.get("ticket_id") == ticket_id:
            ticket["status"] = "Resolved"
            ticket["resolution"] = resolution_text
            ticket["resolved_at"] = utils.now_str()
            updated = True
            break

    if not updated:
        return _result(False, "close_ticket", f"{ticket_id} bulunamadi.", {})

    utils.write_json(utils.DATA_DIR / "tickets.json", tickets)
    return _result(
        True,
        "close_ticket",
        f"{ticket_id} durumu 'Resolved' olarak guncellendi.",
        {"ticket_id": ticket_id, "new_status": "Resolved"},
    )


# ---------------------------------------------------------------------------
# 11) write_audit_log
# ---------------------------------------------------------------------------
def write_audit_log(action_data: dict) -> dict:
    """
    Audit log kaydini fake_logs/action_log.jsonl dosyasina ekler.
    (audit_logger modulu de bunu kullanir; dogrudan cagirim icin de mevcuttur.)
    """
    log_file = utils.LOGS_DIR / "action_log.jsonl"
    ok = utils.append_jsonl(log_file, action_data)
    return _result(
        ok,
        "write_audit_log",
        "Audit log kaydedildi." if ok else "Audit log yazilamadi.",
        {"log_file": str(log_file.relative_to(utils.PROJECT_ROOT))},
    )


# Tool kayit defteri: MCP server'daki tool listesini temsil eder.
AVAILABLE_TOOLS = {
    "read_ticket": read_ticket,
    "search_mailbox": search_mailbox,
    "copy_attachment_to_desktop": copy_attachment_to_desktop,
    "check_printer_status": check_printer_status,
    "reconnect_printer": reconnect_printer,
    "check_mock_erp_order": check_mock_erp_order,
    "check_software_installed": check_software_installed,
    "check_disk_status": check_disk_status,
    "generate_clarification_question": generate_clarification_question,
    "close_ticket": close_ticket,
    "write_audit_log": write_audit_log,
}
