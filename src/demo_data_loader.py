"""
demo_data_loader.py
Demo verilerini (ticket, kullanici, printer, ERP, yazilim, KB) yukler.
Ayrica 'Reset Demo Data' ozelligini saglar: fake desktop temizlenir,
ticket durumlari 'Open' yapilir ve audit log silinir.
"""

from __future__ import annotations

from pathlib import Path

from . import utils


def load_tickets() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "tickets.json", default=[])


def load_users() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "users.json", default=[])


def load_printers() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "printers.json", default=[])


def load_erp_orders() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "mock_erp_orders.json", default=[])


def load_software_inventory() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "software_inventory.json", default=[])


def load_knowledge_base() -> list[dict]:
    return utils.read_json(utils.DATA_DIR / "knowledge_base.json", default=[])


def get_user(username: str) -> dict | None:
    """Kullaniciyi username ile bulur."""
    for user in load_users():
        if user.get("username") == username:
            return user
    return None


def get_ticket(ticket_id: str) -> dict | None:
    """Ticket'i ticket_id ile bulur."""
    for ticket in load_tickets():
        if ticket.get("ticket_id") == ticket_id:
            return ticket
    return None


def reset_demo_data() -> dict:
    """
    Demo ortamini baslangic durumuna dondurur:
      1) Tum ticket durumlarini 'Open' yapar.
      2) Fake desktop klasorlerine kopyalanmis dosyalari siler (.gitkeep kalir).
      3) Audit log dosyasini temizler.
    Not: Silme islemi SADECE fake_desktops ve fake_logs icinde yapilir.
    """
    summary = {"tickets_reset": 0, "desktop_files_removed": 0, "log_cleared": False}

    # 1) Ticket durumlarini sifirla ve kapatma sirasinda eklenen alanlari temizle
    tickets = load_tickets()
    for ticket in tickets:
        ticket["status"] = "Open"
        for stale_key in ("resolution", "resolved_at", "updated_at"):
            ticket.pop(stale_key, None)
    utils.write_json(utils.DATA_DIR / "tickets.json", tickets)
    summary["tickets_reset"] = len(tickets)

    # 2) Fake desktop dosyalarini temizle (guvenlik: yalnizca DESKTOP_DIR icinde)
    for desktop in utils.DESKTOP_DIR.glob("*/Desktop"):
        if not utils.safe_within(utils.DESKTOP_DIR, desktop):
            continue
        for item in desktop.iterdir():
            if item.name == ".gitkeep":
                continue
            if item.is_file() and utils.safe_within(utils.DESKTOP_DIR, item):
                try:
                    item.unlink()
                    summary["desktop_files_removed"] += 1
                except OSError:
                    pass

    # 3) Audit log temizle
    log_file = utils.LOGS_DIR / "action_log.jsonl"
    if log_file.exists() and utils.safe_within(utils.LOGS_DIR, log_file):
        try:
            log_file.unlink()
            summary["log_cleared"] = True
        except OSError:
            pass

    return summary


def list_desktop_files(username: str) -> list[str]:
    """Bir kullanicinin fake desktop'undaki dosyalari listeler (.gitkeep haric)."""
    desktop = utils.DESKTOP_DIR / username / "Desktop"
    if not desktop.exists():
        return []
    return sorted(
        f.name for f in desktop.iterdir() if f.is_file() and f.name != ".gitkeep"
    )


def list_mailbox_attachments(username: str) -> list[str]:
    """Bir kullanicinin fake mailbox eklerini listeler."""
    attach_dir = utils.MAILBOX_DIR / username / "attachments"
    if not attach_dir.exists():
        return []
    return sorted(f.name for f in attach_dir.iterdir() if f.is_file())
