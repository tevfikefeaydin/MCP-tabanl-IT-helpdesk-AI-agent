"""
app.py
MCP-Based AI Helpdesk Agent Demo - Streamlit arayuzu.

Calistirmak icin:
    streamlit run app.py

Bu demo gercek sirket sistemlerine BAGLANMAZ. Tum ticket, mail, masaustu,
printer ve ERP islemleri local fake verilerle simule edilir.
"""

from __future__ import annotations

import streamlit as st

from src import ai_agent
from src import audit_logger
from src import demo_data_loader as loader
from src import response_generator
from src import ticket_manager

# ---------------------------------------------------------------------------
# Sayfa yapilandirmasi
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MCP-Based AI Helpdesk Agent Demo",
    page_icon="🛠️",
    layout="wide",
)

RISK_COLORS = {"Low": "🟢", "Medium": "🟠", "High": "🔴"}
RISK_BG = {"Low": "#1b5e20", "Medium": "#e65100", "High": "#b71c1c"}


# ---------------------------------------------------------------------------
# Session state yardimcilari
# ---------------------------------------------------------------------------
def init_state() -> None:
    """Session state alanlarini ilk degerleriyle hazirlar."""
    defaults = {
        "analysis": None,
        "tool_result": None,
        "reply": None,
        "active_ticket_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_workflow_state() -> None:
    """Ticket degisince onceki analiz/sonuc/cevabi temizler."""
    st.session_state.analysis = None
    st.session_state.tool_result = None
    st.session_state.reply = None


init_state()

# ---------------------------------------------------------------------------
# Baslik
# ---------------------------------------------------------------------------
st.title("🛠️ MCP-Based AI Helpdesk Agent Demo")
st.caption(
    "Bu demo, gercek sirket sistemlerine baglanmadan IT ticket otomasyon surecini "
    "local ve guvenli sekilde simule eder. (MCP Tabanli Yapay Zeka Destekli Bilgi "
    "Islem Ticket Otomasyonu)"
)

# Ollama durum rozeti
if ai_agent.is_ollama_available():
    st.success(f"AI Motoru: Ollama aktif ({ai_agent.DEFAULT_MODEL})", icon="🤖")
else:
    st.info("AI Motoru: Rule-based demo mode (Ollama bulunamadi - demo bozulmadan calisir)", icon="⚙️")

# ---------------------------------------------------------------------------
# Sol panel (sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Ticket Kontrol Paneli")

    tickets = ticket_manager.list_tickets()
    ticket_options = {f"{t['ticket_id']} - {t['title']}": t["ticket_id"] for t in tickets}

    selected_label = st.selectbox("Ticket Sec", list(ticket_options.keys()))
    selected_id = ticket_options[selected_label]

    # Ticket degistiyse workflow state'i temizle
    if st.session_state.active_ticket_id != selected_id:
        st.session_state.active_ticket_id = selected_id
        clear_workflow_state()

    ticket = ticket_manager.get_ticket(selected_id)

    st.markdown("---")
    analyze_clicked = st.button("🔍 Analyze Ticket", use_container_width=True)
    run_clicked = st.button("⚙️ Run Safe Action", use_container_width=True)
    reply_clicked = st.button("✉️ Generate Reply", use_container_width=True)
    close_clicked = st.button("✅ Close Ticket", use_container_width=True)
    # Medium risk islemler yalnizca acik IT onayi ile calisir
    approve_medium = st.checkbox(
        "IT onayi ver (Medium risk islemler icin)",
        help="Medium risk islemler otomatik calismaz; calistirmak icin bu kutuyu isaretleyin.",
    )
    st.markdown("---")
    reset_clicked = st.button("♻️ Reset Demo Data", use_container_width=True)

    st.markdown("---")
    st.caption(
        "Guvenlik: Hicbir gercek sistem kullanilmaz. Tum islemler fake klasorlerde simule edilir."
    )

# ---------------------------------------------------------------------------
# Buton aksiyonlari
# ---------------------------------------------------------------------------
if reset_clicked:
    summary = loader.reset_demo_data()
    clear_workflow_state()
    st.session_state.active_ticket_id = None
    st.success(
        f"Demo verileri sifirlandi. Ticket: {summary['tickets_reset']}, "
        f"Silinen masaustu dosyasi: {summary['desktop_files_removed']}, "
        f"Log temizlendi: {summary['log_cleared']}"
    )
    st.rerun()

if analyze_clicked and ticket:
    with st.spinner("Ticket analiz ediliyor..."):
        analysis = ai_agent.analyze_ticket(ticket)
    st.session_state.analysis = analysis
    st.session_state.tool_result = None
    st.session_state.reply = None
    # Analiz de audit log'a yazilir (siniflandirma islemi)
    audit_logger.log_action(
        ticket_id=ticket["ticket_id"],
        requester=ticket["requester"],
        category=analysis["category"],
        risk_level=analysis["risk_level"],
        tool_called="analyze_ticket",
        action_status="success",
        message=f"Ticket siniflandirildi: {analysis['category']}",
        auto_executed=False,
        approval_required=analysis.get("requires_approval", False),
    )

if run_clicked and ticket:
    analysis = st.session_state.analysis
    if not analysis:
        st.warning("Once 'Analyze Ticket' butonuna basiniz.")
    elif analysis.get("blocked"):
        st.error("Bu islem yuksek riskli oldugu icin otomatik gerceklestirilemez.")
        st.session_state.tool_result = ai_agent.execute_action(ticket, analysis)
        audit_logger.log_action(
            ticket_id=ticket["ticket_id"],
            requester=ticket["requester"],
            category=analysis["category"],
            risk_level=analysis["risk_level"],
            tool_called=analysis.get("selected_tool"),
            action_status="blocked",
            message="Yuksek riskli islem engellendi.",
            auto_executed=False,
            approval_required=True,
        )
    elif analysis.get("requires_approval") and not approve_medium:
        # Medium risk: acik IT onayi olmadan otomatik calistirilmaz
        st.warning(
            "Bu islem Medium risk seviyesinde oldugu icin IT onayi gerektirir. "
            "Demo modunda otomatik calistirilmadi. Calistirmak icin sol paneldeki "
            "'IT onayi ver' kutusunu isaretleyip tekrar 'Run Safe Action'a basiniz."
        )
        st.session_state.tool_result = {
            "success": False,
            "tool_name": analysis.get("selected_tool"),
            "message": "Approval required: Medium risk islem onay olmadan calistirilmadi.",
            "details": {"risk_level": analysis.get("risk_level")},
        }
        audit_logger.log_action(
            ticket_id=ticket["ticket_id"],
            requester=ticket["requester"],
            category=analysis["category"],
            risk_level=analysis["risk_level"],
            tool_called=analysis.get("selected_tool"),
            action_status="approval_required",
            message="Medium risk islem IT onayi bekliyor (calistirilmadi).",
            auto_executed=False,
            approval_required=True,
        )
    else:
        approved = bool(analysis.get("requires_approval") and approve_medium)
        with st.spinner("Guvenli aksiyon calistiriliyor..."):
            result = ai_agent.execute_action(ticket, analysis)
        st.session_state.tool_result = result
        if approved:
            st.info("IT onayi verildi; Medium risk islem onay ile calistirildi.")
        audit_logger.log_action(
            ticket_id=ticket["ticket_id"],
            requester=ticket["requester"],
            category=analysis["category"],
            risk_level=analysis["risk_level"],
            tool_called=result.get("tool_name"),
            action_status="success" if result.get("success") else "failed",
            message=result.get("message", ""),
            # Onayla calisan Medium islem "otomatik" degildir
            auto_executed=analysis.get("can_execute_automatically", False) and not approved,
            approval_required=analysis.get("requires_approval", False),
        )

if reply_clicked and ticket:
    analysis = st.session_state.analysis
    if not analysis:
        st.warning("Once 'Analyze Ticket' butonuna basiniz.")
    else:
        reply = response_generator.generate_reply(
            ticket, analysis, st.session_state.tool_result
        )
        st.session_state.reply = reply

if close_clicked and ticket:
    analysis = st.session_state.analysis
    tool_result = st.session_state.tool_result
    # Kapatma on kosullari: analiz yapilmis, blocked degil, cevap uretilmis,
    # tool bekleniyorsa basariyla calismis olmali.
    tool_expected = bool(
        analysis
        and not analysis.get("clarification_needed")
        and analysis.get("selected_tool")
        and analysis.get("selected_tool") != "generate_clarification_question"
    )
    if not analysis:
        st.warning("Once 'Analyze Ticket' butonuna basiniz.")
    elif analysis.get("blocked"):
        st.error(
            "Bu ticket yuksek riskli oldugu icin otomatik 'Resolved' yapilamaz. "
            "Kapatilmasi bilgi islem yetkilisi onayi gerektirir."
        )
    elif not st.session_state.reply:
        st.warning("Once 'Generate Reply' ile cevap taslagi uretip kapatiniz.")
    elif tool_expected and not (tool_result and tool_result.get("success")):
        st.warning(
            "Once 'Run Safe Action' ile islemi calistirip basarili oldugunu "
            "dogrulayiniz, sonra ticket'i kapatiniz."
        )
    else:
        resolution = st.session_state.reply
        result = ticket_manager.resolve_ticket(ticket["ticket_id"], resolution)
        if result.get("success"):
            audit_logger.log_action(
                ticket_id=ticket["ticket_id"],
                requester=ticket["requester"],
                category=analysis.get("category", "-"),
                risk_level=analysis.get("risk_level", "-"),
                tool_called="close_ticket",
                action_status="success",
                message="Ticket 'Resolved' olarak kapatildi.",
                auto_executed=False,
                approval_required=analysis.get("requires_approval", False),
            )
            st.success(f"{ticket['ticket_id']} kapatildi (Resolved).")
            st.rerun()
        else:
            st.error(result.get("message", "Ticket kapatilamadi."))

# Ticket'i (olasi guncelleme sonrasi) tekrar oku
ticket = ticket_manager.get_ticket(selected_id) if selected_id else None

# ---------------------------------------------------------------------------
# Ana panel
# ---------------------------------------------------------------------------
if not ticket:
    st.info("Lutfen soldan bir ticket seciniz.")
    st.stop()

# 1) Ticket Information
st.subheader("1. Ticket Information")
info_cols = st.columns(3)
info_cols[0].metric("Ticket ID", ticket["ticket_id"])
info_cols[1].metric("Status", ticket["status"])
info_cols[2].metric("Priority", ticket["priority"])
st.write(f"**Title:** {ticket['title']}")
st.write(f"**Requester:** {ticket['requester']}  |  **Department:** {ticket['department']}")
st.write(f"**Description:** {ticket['description']}")

# 2) AI Analysis
st.subheader("2. AI Analysis")
analysis = st.session_state.analysis
if not analysis:
    st.caption("Analiz icin soldan 'Analyze Ticket' butonuna basiniz.")
else:
    risk = analysis["risk_level"]
    st.markdown(
        f"<div style='padding:10px;border-radius:8px;background-color:{RISK_BG.get(risk, '#333')};"
        f"color:white;display:inline-block;'>Risk Level: {RISK_COLORS.get(risk, '')} <b>{risk}</b></div>",
        unsafe_allow_html=True,
    )
    a_cols = st.columns(2)
    with a_cols[0]:
        st.write(f"**Category:** {analysis['category']}")
        st.write(f"**Intent:** {analysis['intent']}")
        st.write(f"**Confidence:** {analysis['confidence']}")
        st.write(f"**Selected Tool:** {analysis.get('selected_tool') or '-'}")
    with a_cols[1]:
        st.write(f"**Clarification Needed:** {analysis['clarification_needed']}")
        st.write(f"**Can Execute Automatically:** {analysis['can_execute_automatically']}")
        st.write(f"**Requires Approval:** {analysis.get('requires_approval', False)}")
        st.write(f"**Engine:** {analysis.get('engine', '-')}")
    st.info(f"**Reasoning Summary:** {analysis['reasoning_summary']}")
    st.write(f"**Recommended Action:** {analysis['recommended_action']}")

    if analysis.get("requires_approval") and not analysis.get("blocked"):
        st.warning(
            "Onay gerekli: Bu islem Medium risk seviyesindedir. Otomatik calismaz; "
            "calistirmak icin sol paneldeki 'IT onayi ver' kutusunu isaretleyiniz."
        )
    if analysis.get("blocked"):
        st.error(f"Blocked: {analysis.get('risk_reason', '')}")

# 3) Tool Execution Result
st.subheader("3. Tool Execution Result")
result = st.session_state.tool_result
if not result:
    st.caption("Aksiyon icin soldan 'Run Safe Action' butonuna basiniz.")
else:
    status_icon = "✅" if result.get("success") else "❌"
    st.write(f"**Tool Name:** {result.get('tool_name')}")
    st.write(f"**Status:** {status_icon} {'success' if result.get('success') else 'failed/blocked'}")
    st.write(f"**Message:** {result.get('message')}")
    details = result.get("details", {})
    if details.get("source") or details.get("destination"):
        st.write(f"**Source:** {details.get('source', '-')}")
        st.write(f"**Destination:** {details.get('destination', '-')}")
    if details:
        with st.expander("Tool details (JSON)"):
            st.json(details)

# 4) Generated Reply
st.subheader("4. Generated Reply")
reply = st.session_state.reply
if not reply:
    st.caption("Cevap taslagi icin soldan 'Generate Reply' butonuna basiniz.")
else:
    st.text_area("Kullaniciya gonderilecek cevap taslagi", reply, height=160)

# 5) Audit Logs
st.subheader("5. Audit Logs (Son 10 islem)")
logs = audit_logger.get_recent_logs(10)
if not logs:
    st.caption("Henuz kayit yok.")
else:
    st.dataframe(logs, use_container_width=True, hide_index=True)

# 6) Demo Environment Preview
st.subheader("6. Demo Environment Preview")
prev_cols = st.columns(2)
with prev_cols[0]:
    st.markdown("**📬 Fake Mailbox (ekler)**")
    mailbox_files = loader.list_mailbox_attachments(ticket["requester"])
    if mailbox_files:
        for f in mailbox_files:
            st.write(f"- {f}")
    else:
        st.caption("Ek bulunamadi.")
with prev_cols[1]:
    st.markdown("**🖥️ Fake Desktop**")
    desktop_files = loader.list_desktop_files(ticket["requester"])
    if desktop_files:
        for f in desktop_files:
            st.write(f"- {f}")
    else:
        st.caption("Masaustu bos.")

st.markdown("---")
st.caption(
    "Guvenlik notu: Gercek mail hesabi, SAP/ERP, kullanici bilgisayari veya sirket "
    "verisi kullanilmaz. High risk islemler otomatik calismaz; Medium risk onay gerektirir; "
    "her islem audit log'a yazilir. Amac gercek deployment degil, konsept gosterimidir."
)
