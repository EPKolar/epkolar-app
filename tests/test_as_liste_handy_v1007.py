# -*- coding: utf-8 -*-
"""v3.9.1007 - Arbeitsschein-Liste am Handy: erster Schein im ersten Bild.

Gemessen (Playwright, Offline-Sitzung, 18 gesaete Scheine, 11 davon OFFA-
verwaist, also MIT Hinweisbalken):
    412x915  erste Karte y 1010 -> 672 (Unterkante 841, ganz sichtbar)
    360x800  erste Karte y 1150 -> 722 (ohne Hinweisbalken 640)

Drei Griffe, alle reine Geometrie:
  1. Kachelblock am Handy einklappbar (zu beim ersten Oeffnen). NICHT quer
     rollbar - v3.9.930 hat das Querrollen genau hier zurueckgenommen, weil
     es den Reiter-Wisch toetet.
  2. Sortierung neben dem Filter-Aufklapper statt eigener Zeile.
  3. Schnellfilter-Chips etwas schmaler gepolstert (bleiben umbrechend).
"""
import re

from _hilfen import nur_code


def _as_view(html):
    i = html.find("function ArbeitsscheinView(")
    assert i != -1
    # Fester Ausschnitt statt "bis zur naechsten function": in der Ansicht
    # steht ein Druck-Template mit "function sharePdf(){" am Zeilenanfang.
    return html[i:i + 260000]


def test_kachelblock_haengt_nur_am_handy_am_klapper(index_html):
    v = nur_code(_as_view(index_html))
    assert "(!isMob||_kachelAuf)&&React.createElement('div', { className: \"kpi-grid epk-leiste epk-kachelband\"" in v, (
        "Der Kachelblock ist nicht (mehr) an (!isMob||_kachelAuf) gebunden - "
        "dann ist er am Handy wieder immer offen oder am Rechner weg.")


def test_der_klapper_nennt_gesamt_und_offen(index_html):
    v = _as_view(index_html)
    i = v.find("isMob&&React.createElement('button', { type: \"button\", onClick: ()=>{const n=!_kachelAuf;")
    assert i != -1, "Der Klapper fehlt."
    k = v[i:i + 1400]
    assert "aria-expanded" in k
    assert "stats.total" in k and "stats.offen" in k, (
        "Zugeklappt muss die Leiste wenigstens Gesamt und Offen nennen - sonst "
        "nimmt das Einklappen Zahlen zurueck.")


def test_der_klapper_ist_nicht_quer_rollbar(index_html):
    """Die Eigenschaft aus v3.9.930: keine quer rollende Flaeche im Kopf der
    Liste. Gilt fuer Klapper UND Chipzeile."""
    v = nur_code(_as_view(index_html))
    a = v.find("isMob&&React.createElement('button', { type: \"button\", onClick: ()=>{const n=!_kachelAuf;")
    b = v.find("quickFilter===chip.key", a)
    assert a != -1 and b != -1
    assert not re.search(r"overflowX\s*:\s*\"(auto|scroll)\"", v[a:b + 600])


def test_es_gibt_genau_eine_sortierauswahl_mit_allen_sieben_feldern(index_html):
    v = nur_code(_as_view(index_html))
    assert v.count("React.createElement('select', { value: sortCol") == 1
    i = v.find("React.createElement('select', { value: sortCol")
    s = v[i:i + 1600]
    for f in ("nummer", "aufgenommen", "terminBestaetigt", "terminVorschlag",
              "scheinstatus", "kundName", "monteur"):
        assert ("value: \"%s\"" % f) in s, f
    assert "'aria-label': \"Sortieren nach\"" in s
    # die Logik ist dieselbe wie vorher (Richtung wechselt bei gleicher Spalte)
    assert "if(c===sortCol)setSortDir(d=>d===\"asc\"?\"desc\":\"asc\");" in s


def test_die_sortierung_steht_neben_dem_filterknopf(index_html):
    v = nur_code(_as_view(index_html))
    f = v.find("isMob&&(()=>{const _n=(filterStatus!==")
    s = v.find("React.createElement('select', { value: sortCol")
    assert 0 < f < s < f + 2500, "Sortierung steht nicht direkt neben dem Filterknopf."
    assert "Mobile-Sort-Dropdown" not in index_html or v.count("\"Sortieren:\"") == 0


def test_richtungsknopf_ist_ein_tippziel(index_html):
    v = nur_code(_as_view(index_html))
    i = v.find("setSortDir(d=>d===\"asc\"?\"desc\":\"asc\"), 'aria-label'")
    assert i != -1
    assert "minWidth:44,minHeight:44" in v[i:i + 500]


def test_selbsttest_riegel_schlagen_an(index_html):
    kaputt = index_html.replace("(!isMob||_kachelAuf)&&React.createElement('div', { className: \"kpi-grid",
                                "React.createElement('div', { className: \"kpi-grid", 1)
    assert kaputt != index_html
    try:
        test_kachelblock_haengt_nur_am_handy_am_klapper(kaputt)
    except AssertionError:
        pass
    else:
        raise AssertionError("Umkehrprobe: der Klapper-Riegel wuerde nicht anschlagen")
