"""v3.9.480 — Bauwochenbericht: KW absteigend + Excel-Scope-Auswahl."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_kwlist_sorted_descending():
    # neueste KW zuerst (Key "YYYY-WW" → b.localeCompare(a) = absteigend, jahr-aware)
    assert "[...kwSet].sort((a,b)=>b.localeCompare(a))" in HTML, "kwList wird nicht absteigend sortiert"


def test_scope_modal_defined():
    assert "window._bwbScopeModal=function(kwList)" in HTML, "Scope-Auswahl-Modal fehlt"
    assert "Alles — alle " in HTML and "(neueste)" in HTML, "Scope-Optionen unvollständig"


def test_generatebwb_accepts_scope():
    assert "const generateBWB=(proj,useFilters,scopeKW)=>" in HTML, "generateBWB nimmt keinen Scope-Param"
    assert 'if(scopeKW&&scopeKW!=="all"){kwList=kwList.filter(k=>k===scopeKW);}' in HTML, "Scope-Filter fehlt"


def test_grand_total_uses_scope_entries():
    # Rollen-Gesamtübersicht muss scopeEntries statt pEntries summieren (Summe nur exportierte KWs)
    assert "const scopeEntries=pEntries.filter(e=>" in HTML, "scopeEntries fehlt"
    assert "const rolleTotal=scopeEntries.filter(e=>rWorkers.find(rw=>rw.id===e.monteur))" in HTML, "Grand-Total nutzt nicht scopeEntries"


def test_inline_excel_button_opens_scope_modal():
    assert "await window._bwbScopeModal(_gd.kwList)" in HTML, "Inline-Excel-Button öffnet die Scope-Auswahl nicht"
