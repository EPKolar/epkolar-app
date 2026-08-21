"""
Struktur-Konsolidierung (v3.9.831): Mangel<->Ticket-Status-Maps EINMAL.

Die beiden Status-Maps lagen je 2x inline dupliziert (Drift-Risiko im
bidirektionalen Mangel<->Ticket-Sync). Jetzt als Modul-Konstanten
_MANGEL2TICKET_ST / _TICKET2MANGEL_ST, an allen 4 Stellen referenziert.
"""
import re
import json
from conftest import run_node_snippet


def test_map_literale_nur_noch_einmal(index_html):
    # Jedes Map-Objektliteral existiert genau 1x (= die Modul-Konstante)
    m2t = index_html.count('{offen:"offen","in Behebung":"in_bearbeitung",behoben:"erledigt"}')
    t2m = index_html.count('offen:"offen",in_bearbeitung:"in Behebung",erledigt:"behoben",abgenommen:"behoben",abgeschlossen:"behoben",storniert:"behoben"')
    assert m2t == 1, f"Mangel->Ticket-Map-Literal {m2t}x statt 1x (Duplikat übrig)"
    assert t2m == 1, f"Ticket->Mangel-Map-Literal {t2m}x statt 1x (Duplikat übrig)"


def test_konstanten_definiert_und_referenziert(index_html):
    assert "const _MANGEL2TICKET_ST=" in index_html
    assert "const _TICKET2MANGEL_ST=" in index_html
    # alle 4 vormals inline Stellen verweisen jetzt auf die Konstanten
    assert "_DEF2TICKET_ST=_MANGEL2TICKET_ST" in index_html
    assert "_sm=_MANGEL2TICKET_ST" in index_html
    assert "_ds=_TICKET2MANGEL_ST[_u.status]" in index_html
    assert "_dst=_TICKET2MANGEL_ST[u.status]" in index_html


def test_maps_sind_saubere_inverse_via_node(index_html, node_exe):
    """Round-Trip: die 3 Defect-Status müssen über beide Maps auf sich selbst
    abbilden; jeder Ticket->Mangel-Wert muss ein gültiger MANGEL_ST-Wert sein."""
    m1 = re.search(r"const _MANGEL2TICKET_ST=(\{[^;]+\});", index_html)
    m2 = re.search(r"const _TICKET2MANGEL_ST=(\{[^;]+\});", index_html)
    assert m1 and m2, "Konstanten-Definitionen nicht extrahierbar"
    snippet = (
        "const M2T=" + m1.group(1) + ";const T2M=" + m2.group(1) + ";"
        + 'const MANGEL_ST=["offen","in Behebung","behoben"];'
        + "const rt=MANGEL_ST.map(d=>({d,back:T2M[M2T[d]]}));"
        + "const allValid=Object.values(T2M).every(v=>MANGEL_ST.indexOf(v)>=0);"
        + "console.log(JSON.stringify({rtOk: rt.every(r=>r.back===r.d), allValid}));"
    )
    out = json.loads(run_node_snippet(node_exe, snippet))
    assert out["rtOk"], "Status-Round-Trip Mangel->Ticket->Mangel nicht identisch"
    assert out["allValid"], "Ticket->Mangel-Map liefert einen ungültigen MANGEL_ST-Wert"
