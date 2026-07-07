"""
response_generator.py
Kullaniciya gonderilecek Turkce, kisa ve kurumsal cevap taslaklarini uretir.

Cevaplar; kategori, risk seviyesi, clarification durumu ve tool sonucuna gore secilir.
"""

from __future__ import annotations

GREETING = "Merhaba,"
SIGNATURE = "Iyi calismalar."


def _wrap(body: str) -> str:
    """Cevabi selam + govde + imza formatinda paketler."""
    return f"{GREETING}\n\n{body}\n\n{SIGNATURE}"


def generate_reply(ticket: dict, analysis: dict, tool_result: dict | None = None) -> str:
    """
    Analiz ve (varsa) tool sonucuna gore cevap taslagi uretir.
    """
    category = analysis.get("category", "General IT Support")

    # 1) Netlestirme gerekiyorsa
    if analysis.get("clarification_needed"):
        return _wrap(
            "Talebinizle ilgili birden fazla ekli dosya bulundugu icin islem otomatik "
            "tamamlanamamistir. Hangi dosyayi kastettiginizi dosya adi veya mail konu "
            "basligi ile paylasabilir misiniz?"
        )

    # 2) Yuksek riskli / engellenmis islem
    if analysis.get("blocked") or category == "High Risk Access Request":
        return _wrap(
            "Bu talep yuksek riskli yetki degisikligi icerdigi icin otomatik olarak "
            "gerceklestirilememektedir. Islem icin bilgi islem yetkilisi onayi gereklidir."
        )

    # 3) Kategori bazli cevaplar
    if category == "Mail Attachment Transfer":
        fname = ""
        if tool_result and tool_result.get("success"):
            dest = tool_result.get("details", {}).get("destination", "")
            fname = dest.split("/")[-1] if dest else ""
        detail = (
            f"Ilgili dosya ({fname}) guvenli demo ortaminda masaustunuze kopyalanmistir."
            if fname
            else "Ilgili rapor dosyasi guvenli demo ortaminda masaustunuze kopyalanmistir."
        )
        return _wrap(detail)

    if category == "Printer Issue":
        return _wrap(
            "Muhasebe yazicisi yeniden tanimlanmis olarak simule edilmistir. "
            "Lutfen tekrar cikti almayi deneyiniz. Sorun devam ederse bilgi islek ekibimize bildiriniz."
        )

    if category == "ERP Production Order Check":
        status_text = ""
        if tool_result and tool_result.get("success"):
            order = tool_result.get("details", {}).get("order", {})
            oid = order.get("order_id", "")
            status = order.get("status", "")
            status_text = f"{oid} numarali uretim emri sistemde '{status}' durumunda gorunmektedir."
        if not status_text:
            status_text = "Belirtilen uretim emri sistemde acik gorunmektedir."
        return _wrap(status_text)

    if category == "Disk Space":
        return _wrap(
            "C diski kullanim orani yuksek gorunmektedir. Gereksiz gecici dosyalarin "
            "temizlenmesi onerilir. Bu islem icin onayiniz gerekmektedir."
        )

    if category == "VPN Issue":
        return _wrap(
            "VPN baglanti sorununuz icin oncelikle internet baglantinizi, kullanici "
            "hesabinizi, MFA dogrulamanizi ve VPN istemci versiyonunuzu kontrol etmenizi "
            "rica ederiz. Sorun devam ederse bilgi islem ekibimiz baglantiyi inceleyecektir."
        )

    if category == "Software Inventory Check":
        installed = None
        if tool_result and tool_result.get("success"):
            installed = tool_result.get("details", {}).get("installed")
        if installed is True:
            return _wrap("Sorgulanan yazilim cihazinizda kurulu gorunmektedir.")
        if installed is False:
            return _wrap(
                "Sorgulanan yazilim cihazinizda kurulu gorunmemektedir. Kurulum talebi "
                "olusturmamizi ister misiniz?"
            )
        return _wrap("Yazilim envanteri kontrol edilmistir. Detaylar tarafiniza iletilecektir.")

    # 4) Genel destek
    return _wrap(
        "Talebiniz alinmistir ve bilgi islem ekibimiz tarafindan degerlendirilmektedir. "
        "En kisa surede tarafiniza donus yapilacaktir."
    )
