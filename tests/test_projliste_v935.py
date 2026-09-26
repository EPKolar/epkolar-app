# -*- coding: utf-8 -*-
"""v3.9.935 Stufe 2c - Projektliste fertig: Chips, Desktop-Spalten, Emoji.

DER EMOJI-RIEGEL IST PRAEZISIERT, NICHT AUFGEWEICHT
───────────────────────────────────────────────────
Der Auftrag verlangt "kein Emoji mehr im Markup dieser Ansicht". Wortwoertlich
ist das in ProjList nicht erfuellbar, und zwar aus drei Gruenden, die jeder
einzeln nachgesehen wurden:

  MELDUNGSTEXTE   Zehn Emoji stehen in Zeichenketten, die an
                  `window.__toast(...)` gehen ("Projektname ist Pflicht",
                  "Projekt archiviert", "Projekt geloescht"). Das sind keine
                  Markup-Knoten, sondern Strings - ein SVG laesst sich dort
                  nicht einsetzen.
  DAS FORMULAR    Das Anlage-/Bearbeiten-Formular steckt in derselben
                  Komponente und ist vom Auftrag ausdruecklich ausgenommen.
  EIN KOMMENTAR   U+2192 steht in einem Changelog-Kommentar und ist gar kein
                  Markup.

Gemessen wird deshalb: kein Emoji als KIND eines React-Elements der
Listen-Ansicht. Die drei Gruppen sind namentlich ausgenommen, und der Riegel
faengt, wenn eine NEUE Stelle dazukommt - die Ausnahmeliste ist eine Zahl,
die stimmen muss, keine Pauschale.
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF←-⇿☀-➿"
                   "⬀-⯿✓✕⊞☰]")


@pytest.fixture(scope="module")
def rumpf():
    s = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    b = _extract_fn(s, "ProjList")
    assert b, "ProjList nicht gefunden - das ist rot, nicht gruen."
    return b


# ── Die Filter-Chips ──────────────────────────────────────────────────────

def test_die_vier_filter_bleiben_vollstaendig(rumpf):
    """Auch die mit Zaehler 0. Ein leerer Status ist eine Information."""
    for l in ('l:"Aktiv"', 'l:"Abgeschlossen"', 'l:"Archiv"', 'l:"Alle"'):
        assert l in rumpf, "Der Filter %s ist verschwunden." % l
    for c in ("counts.aktiv", "counts.abgeschlossen", "counts.archiv"):
        assert c in rumpf, "Der Zaehler %s ist verschwunden." % c


def test_die_chips_tragen_eine_eigene_marke(rumpf):
    """Ohne Marke ist die AUSWAHL nicht von der DARSTELLUNG zu trennen.

    Beide Ansichtsumschalter tragen seit v3.9.935 ebenfalls aria-pressed -
    ein Pruefstand, der darauf sucht, fand sechs Chips statt vier und zwei
    aktive statt einen. Genau so ist es passiert.
    """
    assert "'data-epk': \"filter-chip\"" in rumpf, (
        "Die Filter-Chips tragen keine eigene Marke.")


def test_die_chip_leiste_bricht_nicht_um_und_kann_rollen(rumpf):
    i = rumpf.find("'data-epk': \"filter-chip\"")
    leiste = rumpf[max(0, i - 2600):i]
    assert 'flexWrap:"nowrap"' in leiste, "Die Chip-Leiste bricht um."
    assert 'overflowX:"auto"' in leiste, "Die Chip-Leiste kann nicht rollen."


def test_der_aktive_chip_ist_flaeche_tinte(rumpf):
    i = rumpf.find("'data-epk': \"filter-chip\"")
    stil = rumpf[i:i + 620]
    assert "tab===t.id?UI.tinte:UI.flaeche" in stil, (
        "Der aktive Chip traegt nicht die Flaeche tinte.")
    assert "tab===t.id?UI.flaeche:UI.neutralTxt" in stil, (
        "Die Schrift des aktiven Chips ist nicht weiss.")


# ── Die Desktop-Spalten ───────────────────────────────────────────────────

SPALTEN = ["Projekt", "Kunde / Ort", "Gewerk", "Stunden", "Auftragssumme",
           "Fortschritt", "Aktionen"]


@pytest.mark.parametrize("kopf", SPALTEN)
def test_jede_spalte_hat_ihren_kopf(rumpf, kopf):
    assert '"%s")' % kopf in rumpf, (
        "Der Spaltenkopf %r fehlt in der Listenansicht." % kopf)


def test_die_stunden_stehen_in_ihrer_eigenen_spalte(rumpf):
    """Vorher standen sie in der Projektzelle hinter der PA-Nummer.

    Eine Zahl mitten im Text muss das Auge suchen; eine rechtsbuendige
    Spalte kann man vergleichen.
    """
    i = rumpf.find('"Stunden")')
    assert i > 0
    # In der Projektzelle darf _n(h,1) nicht mehr neben p.nr stehen.
    assert 'p.nr, " · " , _n(h,1), "h"' not in rumpf, (
        "Die Stunden stehen noch in der Projektzelle.")
    assert '_n(h,1), " h")' in rumpf, "Die Stundenspalte rechnet nichts."


def test_die_kopfzeile_ist_ruhig(rumpf):
    i = rumpf.find('background:"#FAFBFA"')
    assert i > 0, "Die Kopfzeile liegt nicht auf #FAFBFA."
    kopf = rumpf[i:i + 200]
    assert "fontSize:UI.fKlein" in kopf and "fontWeight:600" in kopf, (
        "Die Kopfzeile ist nicht 13px/600.")
    assert "textTransform" not in kopf, (
        "Die Kopfzeile steht wieder in Grossbuchstaben - das liest sich "
        "langsamer, und eine Kopfzeile ueberfliegt man hundertmal.")


# ── Emoji im Markup ───────────────────────────────────────────────────────

# Namentlich ausgenommen, jede Gruppe im Modulkopf begruendet.
AUSNAHMEN = {
    "⚠": 6,        # Toast: Pflichtfelder
    "✅": 2,        # Toast: angelegt / aktualisiert
    "✏": 2,        # Toast "Bearbeitung gestartet" + Formularueberschrift
    "\U0001f4e6": 1,    # Toast: archiviert
    "\U0001f5d1": 1,    # Toast: geloescht
    "\U0001f3d7": 1,    # Formularueberschrift "Neues Projekt"
    "\U0001f464": 1,    # Formular "Kundenkontakt"
    "\U0001f517": 1,    # Formular "Kundenportal"
    "\U0001f4be": 1,    # Formular, Speichern-Knopf
    "→": 1,        # in einem Changelog-Kommentar
}


def test_im_markup_der_ansicht_steht_kein_emoji_mehr(rumpf):
    """Praezisiert, nicht aufgeweicht - die Begruendung steht im Modulkopf.

    Die Ausnahmeliste ist eine ZAHL, die stimmen muss. Kommt ein Emoji
    dazu oder vermehrt sich eines, ist der Riegel rot.
    """
    ist = {}
    for m in EMOJI.finditer(rumpf):
        ist[m.group(0)] = ist.get(m.group(0), 0) + 1
    neu = {c: n for c, n in ist.items() if c not in AUSNAHMEN}
    assert not neu, (
        "Neue Emoji im Markup der Projektliste: %s"
        % {("U+%04X" % ord(c)): n for c, n in neu.items()})
    mehr = {c: (n, AUSNAHMEN[c]) for c, n in ist.items()
            if c in AUSNAHMEN and n > AUSNAHMEN[c]}
    assert not mehr, (
        "Ausgenommene Emoji haben sich vermehrt (ist, erlaubt): %s"
        % {("U+%04X" % ord(c)): v for c, v in mehr.items()})


def test_die_ausnahmen_sind_noch_da(rumpf):
    """KOEDER. Waeren alle Emoji weg, ginge der Riegel darueber genauso
    durch - und die Ausnahmeliste waere eine Behauptung ueber nichts."""
    ist = {}
    for m in EMOJI.finditer(rumpf):
        ist[m.group(0)] = ist.get(m.group(0), 0) + 1
    fehlen = [("U+%04X" % ord(c)) for c in AUSNAHMEN if c not in ist]
    assert not fehlen, (
        "Diese ausgenommenen Emoji sind verschwunden: %s. Entweder wurde ein "
        "Meldungstext oder ein Formularteil angefasst - beides war Tabu - "
        "oder die Ausnahmeliste ist veraltet." % fehlen)


def test_die_umschalter_sind_ikonen_mit_beschriftung(rumpf):
    """Icon-only heisst: das Label muss ans ELEMENT, nicht ins Bild."""
    for wie, label in (("raster", "Kachelansicht"), ("liste", "Listenansicht")):
        assert '_ik("%s",17)' % wie in rumpf, "Die Ikone %s fehlt." % wie
        assert '\'aria-label\': "%s"' % label in rumpf, (
            "Dem Umschalter %s fehlt das aria-label." % wie)


def test_das_suchfeld_traegt_die_lupe_nicht_im_platzhalter(rumpf):
    """Ein placeholder ist ein Attribut und nimmt keinen Knoten auf.

    Ein Vorleseprogramm liest dort 'Lupe Projekt Komma Kunde'.
    """
    m = re.search(r'placeholder: "([^"]*Projekt, Kunde[^"]*)"', rumpf)
    assert m, "Das Suchfeld wurde nicht gefunden."
    assert not EMOJI.search(m.group(1)), (
        "Im Platzhalter steht wieder ein Emoji: %r" % m.group(1))
    assert '\'aria-label\': "Projekte durchsuchen"' in rumpf, (
        "Dem Suchfeld fehlt das aria-label.")
