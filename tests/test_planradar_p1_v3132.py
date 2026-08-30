"""v3.9.132 — PlanRadar Phase 1: is_pdf-Upload + gewerk/assignee-Konsolidierung (layer deprecated-kompat)."""
from _hilfen import nur_code, fundstellen


def test_is_pdf_on_upload(index_html):
    assert "uploaded_by:curUser.name,is_pdf:true}/* v3.9.132 P1a" in index_html
    assert "uploaded_by:curUser.name,is_pdf:false}/* v3.9.132 P1a" in index_html


def test_ticket_writer_populates_gewerk(index_html):
    # gewerk kanonisch zusätzlich befüllt; layer bleibt für Ebenen-Toggle-Kompat
    assert 'gewerk:ticket.gewerk||ticket.layer||"maengel"' in index_html
    assert 'layer:ticket.layer||"maengel"' in index_html  # layer NICHT entfernt


def test_readers_use_gewerk_fallback(index_html):
    """Alle Layer-Reader nutzen gewerk||layer (alte + neue Tickets konsistent).

    v3.9.913 - DIE ZAHL BLEIBT (3), wird aber kommentarblind gezaehlt.

    Warum sie bleibt: die Aussage ist "ALLE Reader" - eine Vollstaendigkeits-
    aussage. Die drei Stellen sind zwar benennbar, aber sie unterscheiden sich
    nur im Umfeld, nicht im Muster; ein VIERTER Reader, der den Fallback
    vergisst, wuerde von benannten Zusicherungen nicht bemerkt. Nur die Zahl
    faellt dann auf.

    Warum kommentarblind: der Riegel stand die ganze Zeit auf `== 3` roh
    gezaehlt - und das war ZUFAELLIG richtig. Beim Nachmessen mit der alten
    Fassung von nur_code() kamen nur 2 heraus; der dritte Treffer schien in
    einem Kommentar zu stecken. Er tat es nicht: der Tabellenzeilen-Reader
    (:18180) fiel einem Fehler in nur_code() zum Opfer - `accept: "image/*"`
    wurde dort als Kommentarbeginn gelesen und verschluckte 49.857 Zeichen
    echten Code. Nach der Korrektur in tests/_hilfen.py sind es wieder 3.
    Die Zahl ist also unveraendert; was sich geaendert hat, ist, dass sie jetzt
    Code zaehlt statt Prosa - haette ein Kommentar das Muster zitiert und ein
    Reader waere entfallen, waere der Riegel gruen geblieben.
    """
    code = nur_code(index_html)
    assert "visibleLayers.includes(t.gewerk||t.layer)" in code
    assert "layers.find(l=>l.id===(ticket.gewerk||ticket.layer))" in code
    assert "(layers || []).find(l => l.id === (ticket.gewerk||ticket.layer))" in code
    # 3 = Excel-Export + Tabellenzeile + Mobile-Karte (v3.9.187).
    assert code.count("layers.find(x=>x.id===(t.gewerk||t.layer))") == 3, (
        "Anzahl der t.gewerk||t.layer-Reader ist %d statt 3. Ist ein vierter "
        "Reader dazugekommen, muss er den Fallback ebenfalls fuehren - sonst "
        "verschwinden alte Tickets ohne gewerk aus der Ebenen-Zuordnung.\n%s"
        % (code.count("layers.find(x=>x.id===(t.gewerk||t.layer))"),
           fundstellen(code, "layers.find(x=>x.id===(t.gewerk||t.layer))"))
    )
