# -*- coding: utf-8 -*-
"""v3.9.739 — P1-Bug: die AKTUELLE Woche fehlte in der Dispo.

Sebastian (16.07.): "die aktuelle woche fehlt in der dispo komplett, das ist ein bug, da morgen stoerungen
gefahren werden koennen." _dispoBuildInput ankerte den Horizont auf Montag der FOLGEWOCHE (KW+1), die
laufende Woche war unsichtbar -> heute/morgen nicht planbar. Fix: Anker auf Montag der AKTUELLEN Woche
(KW+0); der Horizont zeigt jetzt laufende Woche + Folgewochen. Vergangene Tage (t.iso < heute) werden
geblockt (keine Kapazitaet in der Vergangenheit, Grund-Chip "vergangen"), heute und morgen bleiben planbar.
"""


def test_anker_ist_aktuelle_woche(index_html):
    # KW+1-Anker (+7) ist weg; Anker = Montag der aktuellen Woche.
    assert "d.setDate(d.getDate()-(dow-1));" in index_html, "Horizont ankert nicht auf die aktuelle Woche"
    assert "d.setDate(d.getDate()-(dow-1)+7)" not in index_html, "alter KW+1-Anker (+7) noch vorhanden"


def test_vergangene_tage_geblockt(index_html):
    start = index_html.index("function _dispoBuildInput(")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    body = index_html[start:end]
    # Vergangene Tage (vor heute) bekommen keine Kapazitaet + einen "vergangen"-Grund.
    assert "t.iso<_heute" in body or "t.iso < _heute" in body, "kein Vergangenheits-Guard je Tag"
    assert "vergangen" in body, "kein 'vergangen'-Grund fuer Tage vor heute"
