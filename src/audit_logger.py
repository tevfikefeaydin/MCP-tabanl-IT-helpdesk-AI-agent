"""
audit_logger.py
Tum agent/tool islemlerini denetim (audit) kaydi olarak tutar.
Kayitlar demo_environment/fake_logs/action_log.jsonl dosyasina JSONL formatinda yazilir.
"""

from __future__ import annotations

from . import utils

LOG_FILE = utils.LOGS_DIR / "action_log.jsonl"


def log_action(
    ticket_id: str,
    requester: str,
    category: str,
    risk_level: str,
    tool_called: str | None,
    action_status: str,
    message: str,
    auto_executed: bool,
    approval_required: bool,
) -> dict:
    """
    Tek bir audit kaydi olusturur ve dosyaya ekler. Kaydi geri doner.
    """
    record = {
        "timestamp": utils.now_str(),
        "ticket_id": ticket_id,
        "requester": requester,
        "category": category,
        "risk_level": risk_level,
        "tool_called": tool_called or "-",
        "action_status": action_status,
        "message": message,
        "auto_executed": auto_executed,
        "approval_required": approval_required,
    }
    utils.append_jsonl(LOG_FILE, record)
    return record


def get_recent_logs(limit: int = 10) -> list[dict]:
    """
    Son 'limit' kadar audit kaydini (en yeni ustte) doner.
    """
    records = utils.read_jsonl(LOG_FILE)
    return list(reversed(records))[:limit]


def clear_logs() -> bool:
    """Audit log dosyasini temizler (yalnizca fake_logs icinde)."""
    if LOG_FILE.exists() and utils.safe_within(utils.LOGS_DIR, LOG_FILE):
        try:
            LOG_FILE.unlink()
            return True
        except OSError:
            return False
    return True
