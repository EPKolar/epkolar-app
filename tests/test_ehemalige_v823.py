# -*- coding: utf-8 -*-
"""v3.9.823 — Mitarbeiter-Tab: Sektion "Ehemalige" (default zugeklappt) + Austritts-Badge.

Ausgetretene Mitarbeiter sollen die aktive Liste nicht mehr zumüllen, aber NICHT gelöscht werden —
an ihnen hängen Zeiteinträge, Abwesenheiten und Scheine; die Worker-Zeile ist die einzige
Namensauflösung (siehe Daten-Vorfall 23.07.). Prädikat wörtlich wie fieldM: austritt < heute.
"""
import json
from conftest import run_node_snippet

# Praedikat wie im Code: _maEhemalig(m) = !!(m && m.austritt && austritt.slice(0,10) < heute)
_PART = ("(function(list,heute){var eh=function(m){return !!(m&&m.austritt&&String(m.austritt).slice(0,10)<heute);};"
         "return {aktiv:list.filter(function(m){return !eh(m);}).map(function(m){return m.id;}),"
         "ehemalig:list.filter(eh).map(function(m){return m.id;})};})")


def _partition(node_exe, list_js, heute="2026-07-23"):
    snip = "process.stdout.write(JSON.stringify(" + _PART + "(" + list_js + ",'" + heute + "')))"
    return json.loads(run_node_snippet(node_exe, snip))


# ── 1) Partitionierung ───────────────────────────────────────────────────────
def test_partition_grundfaelle(node_exe):
    liste = ("[{id:'ohne'},"
             "{id:'leer',austritt:''},"
             "{id:'heute',austritt:'2026-07-23'},"
             "{id:'gestern',austritt:'2026-07-22'},"
             "{id:'zukunft',austritt:'2026-12-31'}]")
    r = _partition(node_exe, liste)
    # Kein Austritt / leerer Austritt -> aktiv
    assert "ohne" in r["aktiv"] and "leer" in r["aktiv"]
    # Austritt = HEUTE -> noch aktiv (letzter Arbeitstag zaehlt)
    assert "heute" in r["aktiv"], "Austritt heute muss noch aktiv sein (letzter Arbeitstag)"
    # Austritt in der Zukunft -> aktiv
    assert "zukunft" in r["aktiv"]
    # Austritt gestern -> ehemalig
    assert r["ehemalig"] == ["gestern"], "nur der gestern Ausgetretene gehoert in 'Ehemalige'"


def test_partition_lueckenlos_und_ueberschneidungsfrei(node_exe):
    liste = ("[{id:'a'},{id:'b',austritt:''},{id:'c',austritt:'2026-07-23'},"
             "{id:'d',austritt:'2026-07-22'},{id:'e',austritt:'2020-01-01'},{id:'f',austritt:'2027-01-01'}]")
    r = _partition(node_exe, liste)
    alle = set(r["aktiv"]) | set(r["ehemalig"])
    assert alle == {"a", "b", "c", "d", "e", "f"}, "Partition ist nicht lueckenlos"
    assert not (set(r["aktiv"]) & set(r["ehemalig"])), "Partition ueberschneidet sich"
    assert len(r["aktiv"]) + len(r["ehemalig"]) == 6, "jeder Worker muss in GENAU einem Block landen"


# ── 2) Sektion: default zugeklappt, bei 0 Ehemaligen kein Render ─────────────
def test_sektion_default_zugeklappt(index_html):
    assert "const [showEhem,setShowEhem]=_react.useState.call(void 0, false);" in index_html, \
        "Klapp-State fehlt oder startet nicht zugeklappt"
    # Kein Persist (kein localStorage fuer den Klapp-State).
    i = index_html.index("const [showEhem,setShowEhem]")
    assert "localStorage" not in index_html[i:i + 300], "Klapp-State darf NICHT persistiert werden"


def test_sektion_nur_bei_vorhandenen_ehemaligen(index_html):
    assert "if(_alt.length>0)_out.push(" in index_html, "Sektion wird auch bei 0 Ehemaligen gerendert"
    assert 'Ehemalige ("+_alt.length+")' in index_html, "Sektions-Titel mit Anzahl fehlt"


def test_ein_renderer_fuer_beide_bloecke(index_html):
    """Klick/Detail/Bearbeiten muss in 'Ehemalige' identisch funktionieren -> derselbe Renderer."""
    assert "const _row=m=>{const projCount=" in index_html, "kein gemeinsamer Zeilen-Renderer"
    assert "const _out=_akt.map(_row);" in index_html, "Aktive nutzen den Renderer nicht"
    assert "_alt.map(_row)" in index_html, "Ehemalige nutzen den Renderer nicht"
    assert "return monteure.map(m=>{const projCount=" not in index_html, "alter Direkt-map noch vorhanden"


# ── 3) Badge fuer BEIDE Rollen ───────────────────────────────────────────────
def test_badge_liste_und_detail_fuer_beide_rollen(index_html):
    assert "const _maBadge=m=>_maEhemalig(m)?React.createElement('span'" in index_html, "Badge-Helper fehlt"
    assert '"Ausgetreten "+fdt(m.austritt)' in index_html, "Badge nutzt nicht fdt() / falscher Text"
    # Liste: Badge haengt in der Zeile (rollenunabhaengig, kein isAdmin-Gate davor).
    assert "}}, m.r, _maBadge(m), m.fs&&" in index_html, "Badge fehlt in der Listenzeile"
    # Detail: Badge auch im ADMIN-Zweig (das war die Luecke).
    i = index_html.index('isAdmin?React.createElement(\'div\', { style: {display:"flex",alignItems:"center",gap:6}}, React.createElement(\'input\', { type: "date"')
    seg = index_html[i:i + 500]
    assert "_maBadge(selM)" in seg, "Admin sieht im Detail weiterhin nur das Datumsfeld ohne Kennzeichnung"
    # Nicht-Admin-Zweig byte-identisch.
    assert 'React.createElement(\'span\', { style: {color:selM.austritt?COLORS.ERROR:V.dm}}, selM.austritt?fdt(selM.austritt):"aktiv")' in index_html, \
        "Nicht-Admin-Zweig wurde veraendert"
