"""
Buero-Rolle braucht in den Arbeitsscheinen Admin-Parität fuer die Einteilung.

BUG (User-Report 21.08.2026): Die Damen im Buero koennen bei den Arbeitsscheinen
keine Monteurs-Timeline / keinen Kalender der Monteure sehen — "muss gehen wie
admin, die machen die Einteilung".

Ursache: Die Komponente ArbeitsscheinView definiert ihr lokales isAdmin als
`curUser.role==="admin"||curUser.role==="projektleiter"` — buero fehlt. Der
Dispo-Tab wird buero zwar gezeigt (explizite Rollen-Liste ["admin","buero",
"projektleiter"]), aber der Kalender-Monteur-Auswaehler haengt an isAdmin und
faellt fuer Nicht-Admin auf ein festes Badge der EIGENEN monteurId zurueck ->
buero (ohne monteurId) sieht einen leeren Kalender und kann keinen Monteur waehlen.

Das Abwesenheiten-Pendant nimmt buero laengst in sein isAdmin auf (v3.9.453,
"buero darf Urlaub genehmigen"); der Dispo-Tab ist fuer buero bereits geoeffnet.
9884 ist die vergessene Stelle.

Invariante: In ArbeitsscheinView muss buero dieselbe Einteilungs-Sicht wie
admin/projektleiter bekommen (isAdmin schliesst buero ein). isMonteurRole bleibt
auf monteur/helfer beschraenkt -> die Monteur-Schutzriegel (isMonteurRole&&!isAdmin)
aendern sich fuer buero nicht.
"""


def _component_body(index_html, header):
    start = index_html.find(header)
    assert start != -1, f"Komponente {header!r} nicht gefunden"
    # bis zum naechsten Top-Level `\nfunction ` (Spalte 0)
    nxt = index_html.find("\nfunction ", start + len(header))
    return index_html[start : nxt if nxt != -1 else len(index_html)]


def test_arbeitsscheinview_isAdmin_schliesst_buero_ein(index_html):
    body = _component_body(index_html, "function ArbeitsscheinView(")
    i = body.find("const isAdmin=")
    assert i != -1, "kein `const isAdmin=` in ArbeitsscheinView"
    expr = body[i : body.find(";", i)]
    for rolle in ("admin", "projektleiter", "buero"):
        assert rolle in expr, (
            f"ArbeitsscheinView.isAdmin muss '{rolle}' enthalten, damit das Buero "
            f"die Einteilung (Kalender/Monteurs-Timeline) wie admin sieht. "
            f"Gefunden: {expr!r}"
        )


def test_isMonteurRole_bleibt_ohne_buero(index_html):
    """Sicherung: buero darf NICHT zur Monteur-Rolle werden — sonst kippen die
    Monteur-Schutzriegel (isMonteurRole&&!isAdmin) in die falsche Richtung."""
    body = _component_body(index_html, "function ArbeitsscheinView(")
    i = body.find("const isMonteurRole=")
    assert i != -1, "kein `const isMonteurRole=` in ArbeitsscheinView"
    expr = body[i : body.find(";", i)]
    assert "buero" not in expr, f"buero darf keine Monteur-Rolle sein: {expr!r}"


def test_dispo_tab_bleibt_fuer_buero_sichtbar(index_html):
    """Regressionsschutz: der Dispo-Tab war fuer buero schon geoeffnet; das darf
    beim Fix nicht verloren gehen."""
    assert '["admin","buero","projektleiter"]' in index_html, (
        "Dispo-Tab-Rollenliste (admin/buero/projektleiter) nicht mehr vorhanden"
    )
