"""v3.9.665 Bauwochenbericht 2-Nachkommastellen (Bug-Hunt-Subagent).

exportBauwochenbericht renderte Stunden-Zellen mit 1 Nachkommastelle, summierte
Zeilen/Gesamt aber aus den UNGERUNDETEN Werten → bei Viertelstunden-Buchungen (.25/.75)
gingen die Spalten im unterschriebenen Kunden-/OeBA-Dokument nicht auf. Der Zwilling
generateBWB nutzt 2 Stellen — jetzt beide konsistent.
"""


def test_bwb_export_zwei_nachkommastellen(index_html):
    assert '${h>0?_n(h,2):""}' in index_html
    assert '${rowSum>0?_n(rowSum,2):""}' in index_html
    assert '${t>0?_n(t,2):""}' in index_html
    assert '${_n(grandTotal,2)}' in index_html


def test_bwb_keine_1dez_reste_in_haupttabelle(index_html):
    # die vier alten 1-Stellen-Ausgaben der BWB-Haupttabelle sind weg
    assert '${h>0?_n(h,1):""}' not in index_html
    assert '${rowSum>0?_n(rowSum,1):""}' not in index_html
    assert '${t>0?_n(t,1):""}' not in index_html
    assert '${_n(grandTotal,1)}' not in index_html


# ── Urlaub-Self-Service-Karte (_absStats) im selben Version-Bundle ──
def test_absstats_wochentagsgenau(index_html):
    # Tage-Umrechnung nutzt jetzt _stdVonTagK (Fr-Volltag = 4,5h -> 1 Tag)
    assert "const _norm=_stdVonTagK(_d);if(!(_norm>0))return;" in index_html
    assert "const dayUnit=(_h>=_norm)?1:0.5;" in index_html
    # 0/fehlende Std = Volltag-Marker = Norm
    assert "if(isNaN(_h)||_h===0)_h=_norm;" in index_html


def test_absstats_abgelehnt_uebersprungen(index_html):
    # v3.9.668: arg null -> approvals (approvals-Prop jetzt durchgereicht); Intent unveraendert
    assert 'if(v.type==="urlaub"&&_resolveApprK(abs,approvals,k)==="abgelehnt")return;' in index_html
    # alte wochentagsblinde Heuristik weg
    assert "const dayUnit=h>0?(h>=8?1:0.5):1;" not in index_html
