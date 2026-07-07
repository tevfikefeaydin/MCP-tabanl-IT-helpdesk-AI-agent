"""
ticket_manager.py
Ticket yasam dongusunu yonetir: listeleme, okuma, durum guncelleme, kapatma.
Tum degisiklikler data/tickets.json uzerinde yapilir.
"""

from __future__ import annotations

from . import demo_data_loader as loader
from . import mcp_tools
from . import utils


def list_tickets() -> list[dict]:
    """Tum ticket'lari doner."""
    return loader.load_tickets()


def get_ticket(ticket_id: str) -> dict | None:
    """Tek bir ticket'i doner."""
    return loader.get_ticket(ticket_id)


def update_status(ticket_id: str, new_status: str) -> bool:
    """
    Ticket durumunu gunceller (Open / In Progress / Resolved / Blocked).
    Basarili olursa True doner.
    """
    tickets = loader.load_tickets()
    updated = False
    for ticket in tickets:
        if ticket.get("ticket_id") == ticket_id:
            ticket["status"] = new_status
            ticket["updated_at"] = utils.now_str()
            updated = True
            break
    if updated:
        utils.write_json(utils.DATA_DIR / "tickets.json", tickets)
    return updated


def resolve_ticket(ticket_id: str, resolution_text: str) -> dict:
    """
    Ticket'i 'Resolved' yapar (mcp_tools.close_ticket araciligiyla).
    """
    return mcp_tools.close_ticket(ticket_id, resolution_text)
