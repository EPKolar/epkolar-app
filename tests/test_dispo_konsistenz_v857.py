"""
v3.9.857 — zwei Dispo-Konsistenz/Anzeige-Fixes (Dispo-Hunt-Agent).

(P3) Vollabwesenheit an einem Vorab-BVH-Tag: der Setter (:5189) setzte `art="vorab"`
     unabhängig von der Abwesenheit; der Renderer (:9891) zeigt bei `art==="vorab"`
     IMMER "🏗 Baustelle" und ignoriert den Fehlgrund-Chip → ein volltags abwesender
     Monteur erschien wie eingeplant. Fix: `art="vorab"` nur wenn `absAbz<normMin`.
(P2) Fix-Termine-ohne-Zeit: der Ablauf-fahrtMin (:9839) nahm die rohe `kundPlz`
     (Rechnungsadresse) statt der #24-aufgelösten Baustellen-PLZ (`_dispoScheinPlz`,
     wie das km-Label :9860) → für Verwalter-Kunden falsche Startzeit.
"""


def test_p3_vorab_nur_ohne_vollabwesenheit(index_html):
    # der neue Guard auf absAbz<normMin ist da
    assert 'else if(absAbz<t.normMin){art={art:"vorab",bvh:(belRow.bvh||"Baustelle")};' in index_html
    # der alte, abwesenheits-blinde else-Zweig ist weg
    assert 'else{art={art:"vorab",bvh:(belRow.bvh||"Baustelle")};var vorabAbz=' not in index_html


def test_p2_fixtermin_nutzt_baustellen_plz(index_html):
    # der fahrtMin der Fix-Termine loest die PLZ jetzt via _dispoScheinPlz auf
    assert 'var _fp=(_dispoScheinPlz(_fsp.arbeitsort||"",_fsp.kundPlz||"",(_fsp.arbeitsanweisungen||"")+" "+(_fsp.stoerungsmelder||""),(_built.ortIdx||[])).plz)||"";' in index_html
    # die alte rohe-kundPlz-Variante im _combItems-map ist weg
    assert 'var _fp=_scheinById(f.scheinId).kundPlz||"";return {buendelKey:_bk(f.scheinId),fahrtMin' not in index_html
