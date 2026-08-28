"""
PlanRadar ① — Plan-Gesamtreport-PDF (_genPlanReportPdf, v3.9.828).

Ein Deliverable: der Gesamtplan (pro Plan-Seite) mit ALLEN nummerierten Pins +
eine Legendentabelle (Nr/Titel/Status/Frist/Verantwortlich). Baut auf den
vorhandenen Ticket-PDF-Bausteinen auf; additiv (kein Schema/Backend/Auth).
"""
import re


def test_funktion_existiert(index_html):
    assert "async function _genPlanReportPdf(" in index_html, "_genPlanReportPdf fehlt"


def test_window_export(index_html):
    assert "window._genPlanReportPdf=_genPlanReportPdf" in index_html, (
        "_genPlanReportPdf nicht window-exportiert (Playwright/Runtime-Zugriff)"
    )


def test_button_verdrahtet_und_gegatet(index_html):
    # Button ruft die Funktion mit dem aktuellen Plan + allen Pins (Tickets + Defect-Pins)
    # v3.9.877 NACHGEZOGEN: Basis ist jetzt _nrBase statt planTickets (planTickets war fuer
    # Feldrollen auf die EIGENEN Tickets gefiltert), und die Bildschirm-Nummernkarte
    # _ticketNr wird durchgereicht, damit der PDF nicht neu durchzaehlt - er warf vorher
    # positionslose Tickets weg und verschob dadurch jede folgende Nummer gegen den
    # Bildschirm. Geprueft wird weiterhin dasselbe: Plan + alle Pins + Rollen-Gate.
    marker = "_genPlanReportPdf(selPlan,_nrBase.concat(_defectPins),monteure,layers,p,_ticketNr)"
    i = index_html.find(marker)
    assert i != -1, "Plan-Report-Button nicht korrekt verdrahtet"
    # Gate wie beim Einzel-Ticket-PDF: admin/PL (isAdmin) ODER buero — steht direkt vor dem Button
    window = index_html[max(0, i - 400):i]
    assert 'curUser.role==="buero"' in window and "isAdmin" in window, (
        "Plan-Report-Button-Gate (admin/PL/buero) nicht gefunden"
    )


def _fn_body(index_html, name):
    m = re.search(r"async function " + re.escape(name) + r"\(", index_html)
    assert m, f"{name} nicht gefunden"
    start = m.start()
    nxt = re.search(r"\n(async function |function )", index_html[start + 10:])
    end = start + 10 + nxt.start() if nxt else len(index_html)
    return index_html[start:end]


def test_nutzt_bewaehrte_bausteine(index_html):
    body = _fn_body(index_html, "_genPlanReportPdf")
    for baustein in ("_tkRenderPdfPage", "_tkLoadImg", "_pdfStr", "TICKET_STATUS", "splitTextToSize", "getNumberOfPages"):
        assert baustein in body, f"_genPlanReportPdf nutzt {baustein} nicht (soll auf Vorhandenem aufbauen)"


def test_pin_nummerierung_und_seiten(index_html):
    body = _fn_body(index_html, "_genPlanReportPdf")
    # nummeriert alle Pins 1..N
    assert "_nrById" in body and "i+1" in body, "keine 1..N-Pin-Nummerierung"
    # Legendenseite + Footer-Seitenzahlen
    assert "Legende" in body, "keine Legendenseite"
    assert "addPage" in body, "kein Seitenumbruch/Legendenseite"
