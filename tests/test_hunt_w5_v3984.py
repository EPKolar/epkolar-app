"""v3.9.126 — Hunt-Welle 5 (Finder I/J/K): Sync-Duplikat, Render-Perf, de-AT-Formate."""


def test_serviceheft_no_double_write(index_html):
    # J-P1: upd-PUT schrieb das Array, zusätzlicher POST hängte den Eintrag beim Sync ERNEUT an
    assert 'serviceheft:[e,...(f.serviceheft||[])]}));SQ.push({url:"/api/fahrzeuge/"+sel,method:"POST",body:e});' not in index_html, (
        "Serviceheft-Doppel-Write: der redundante SQ-POST muss entfernt bleiben"
    )
    assert "serviceheft-Array bereits per PUT" in index_html  # Kommentar-Anker


def test_projlist_hours_lookup(index_html):
    # I-P2: O(entries)-Lookup statt 3x O(Projekte*entries) pro Tastendruck
    assert "const hoursByProject=_react.useMemo.call(void 0, ()=>{const m={};entries.forEach(" in index_html
    assert index_html.count("hoursByProject[p.id]||0") == 3  # totalH + Kacheln + Liste
    assert "const h=entries.filter(x=>x.p===p.id).reduce" not in index_html


def test_vzeit_pe_memoized(index_html):
    assert "const pe=_react.useMemo.call(void 0, ()=>entries.filter(x=>x.p===p.id),[entries,p.id]);" in index_html


def test_de_at_formats(index_html):
    # K: keine rohen ISO-Daten/de-ohne-AT/€-Suffixe mehr an den gemeldeten Stellen
    assert 'ord.datum?fdt(ord.datum):"—"' in index_html
    assert 'pvOrder.datum?fdt(pvOrder.datum):"—"' in index_html
    assert '.toLocaleString("de")' not in index_html  # alle auf de-AT
    assert '_n(s.kosten,2)+" €"' not in index_html    # Suffix-€ vereinheitlicht
