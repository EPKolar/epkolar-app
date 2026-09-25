# -*- coding: utf-8 -*-
"""v3.9.934 Stufe 2b - Projektliste: Groessen, Aktionsmenue, Kennzahlenzeile.

WAS HIER GESICHERT WIRD
───────────────────────
1. Keine Schrift unter 12 px in dieser Ansicht.
2. Die drei Aktionen sind erhalten - nur woanders.
3. Loeschen ist kein Nachbar von Bearbeiten und nicht der erste Eintrag.
4. Icon-Knoepfe sind beschriftet (fuer den Bildschirmleser).
5. Die Kennzahlenzeile haelt die Auftragssumme hinter `_seeBetrag`.
6. **`_kz` steht hinter seinen Quellen** - der wichtigste Riegel hier.

ZU PUNKT 6, WEIL ES GENAU SO PASSIERT IST
─────────────────────────────────────────
Beim Bauen stand `_kz` bei den Merkern oben, also VOR `hoursByProject`. Die
Abhaengigkeitsliste `[projects,hoursByProject]` wird beim Rendern ausgewertet
und las damit eine `const` vor ihrer Initialisierung:

    Cannot access 'hoursByProject' before initialization

ViewBoundary fing es, der Projekte-Tab zeigte einen Fehler statt der Liste.
`node_check.py` blieb dabei GRUEN - es parst die Bloecke und fuehrt sie nicht
aus. Gefunden hat es erst der Browserlauf.

Dieselbe Falle wie v3.9.672 (`_gridCols` vor `isMob`), dieselbe Komponente.
Zweimal dieselbe Falle heisst: sie braucht einen Riegel, keine Ermahnung.
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn  # noqa: E402


@pytest.fixture(scope="module")
def rumpf():
    s = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    b = _extract_fn(s, "ProjList")
    assert b, ("ProjList nicht gefunden. Das ist rot, nicht gruen - ein leerer "
               "Rumpf sieht sonst aus wie eine Ansicht ohne Maengel.")
    return b


# ── 1. Lesbarkeit ─────────────────────────────────────────────────────────

def test_keine_schrift_unter_zwoelf_px(rumpf):
    zahlen = [int(x) for x in re.findall(r"fontSize:\s*(\d+)", rumpf)]
    klein = sorted(set(x for x in zahlen if x < 12))
    assert not klein, (
        "Schriftgroessen unter 12 px in der Projektliste: %s. 12 ist die "
        "Untergrenze - das ist Meta- und Beschriftungstext, den man im "
        "Gegenlicht auf einer Baustelle lesen koennen muss." % klein)


def test_die_untergrenze_kommt_aus_dem_token(rumpf):
    """KOEDER zum Riegel darueber.

    Waeren die zwoelf Stellen einfach auf eine getippte 12 gesetzt, ginge der
    Riegel oben genauso durch - aber die Untergrenze haette keinen Ort mehr.
    """
    assert rumpf.count("fontSize:UI.fMeta") >= 12, (
        "Nur %d Stellen nehmen UI.fMeta. Dann steht die Untergrenze wieder "
        "verstreut als Zahl im Code." % rumpf.count("fontSize:UI.fMeta"))


# ── 2. Die drei Aktionen sind erhalten ────────────────────────────────────

@pytest.mark.parametrize("ruf", ["editProject(p)", "archiveP(p.id)", "deleteP(p.id)"])
def test_jede_der_drei_aktionen_ist_noch_da(rumpf, ruf):
    """Der Bestandsschutz in einem Satz: ein Knopf darf anders aussehen und
    woanders stehen - seine Funktion bleibt."""
    assert ruf in rumpf, (
        "Die Aktion %s ist aus der Projektliste verschwunden." % ruf)


def test_die_archiv_bedingung_ist_unveraendert(rumpf):
    """`p.status!=="archiv"` entscheidet, OB archiviert werden kann. Solche
    Bedingungen sind Tabu - geaendert wird nur das WIE."""
    assert 'p.status!=="archiv"' in rumpf, (
        "Die Bedingung am Archivieren ist weg. Dann liesse sich ein bereits "
        "archiviertes Projekt noch einmal archivieren.")


# ── 3. Loeschen steht nicht neben Bearbeiten ──────────────────────────────

def test_loeschen_ist_kein_nachbar_von_bearbeiten(rumpf):
    """Drei gleich grosse Knoepfe sagten: das tut man gleich oft.

    Tatsaechlich oeffnet man ein Projekt hundertmal, bevor man es einmal
    loescht - und Loeschen stand unmittelbar daneben, gleich gross, auf einem
    Telefon, mit Handschuh, in der Sonne.
    """
    i_edit = rumpf.find("editProject(p)")
    i_del = rumpf.find("deleteP(p.id)")
    assert i_edit >= 0 and i_del >= 0
    dazwischen = rumpf[min(i_edit, i_del):max(i_edit, i_del)]
    assert "_meS" in dazwischen or "menuitem" in dazwischen, (
        "Zwischen Bearbeiten und Loeschen liegt kein Menue mehr - sie stehen "
        "wieder als Geschwister nebeneinander.")


def test_loeschen_ist_nicht_der_erste_menueeintrag(rumpf):
    i_edit = rumpf.find("editProject(p)")
    i_del = rumpf.find("deleteP(p.id)")
    assert i_edit < i_del, (
        "Loeschen steht vor Bearbeiten im Menue. Der gefaehrlichste Eintrag "
        "gehoert nicht an die Stelle, auf die der Daumen zuerst faellt.")


def test_loeschen_ist_abgesetzt(rumpf):
    """Abgesetzt heisst: eigene Farbe und eine Linie davor - nicht versteckt."""
    assert "_meS(true)" in rumpf, "Loeschen traegt nicht den Warnstil."
    assert "UI.achtungTxt" in rumpf, "Der Warnstil nimmt nicht achtungTxt."


# ── 4. Icon-Knoepfe sind beschriftet ──────────────────────────────────────

def test_jeder_icon_knopf_traegt_ein_aria_label(rumpf):
    """Ein SVG traegt aria-hidden - beschriftet wird der KNOPF.

    Gemessen wird ICON-OHNE-TEXT, nicht "enthaelt ein Icon". Die drei
    Menueeintraege tragen Ikone UND Beschriftung ("Bearbeiten",
    "Archivieren", "Loeschen") - die braucht kein aria-label, ihr Text IST
    der Name. Der erste Anlauf dieses Riegels hat sie beanstandet und damit
    das Falsche gemessen.

    Ohne Beschriftung liest ein Bildschirmleser nur "Schaltflaeche".
    """
    ohne = []
    for m in re.finditer(r"React\.createElement\('button',\s*\{", rumpf):
        stueck = rumpf[m.start():m.start() + 1200]
        inhalt = stueck.split("React.createElement('button'", 1)[1][:900]
        if "_ik(" not in inhalt:
            continue                      # gar keine Ikone
        # Sichtbarer Text: eine Zeichenkette mit Buchstaben, die als Kind
        # uebergeben wird - erkennbar an dem Komma davor.
        hat_text = re.search(r',\s*"[^"]*[A-Za-zÄÖÜäöüß][^"]*"\s*\)', inhalt)
        if hat_text:
            continue                      # Ikone MIT Text - der Text ist der Name
        if "aria-label" not in inhalt:
            ohne.append(inhalt[:100])
    assert not ohne, (
        "%d Knopf/Knoepfe mit NUR einer Ikone und ohne aria-label: %s"
        % (len(ohne), ohne[:3]))


def test_der_aktionsknopf_meldet_seinen_zustand(rumpf):
    """aria-expanded sagt dem Bildschirmleser, ob das Menue offen ist."""
    assert "'aria-haspopup':\"menu\"" in rumpf, "Der Knopf sagt nicht, dass er ein Menue oeffnet."
    assert "'aria-expanded'" in rumpf, "Der Knopf meldet seinen Zustand nicht."


# ── 5. Die Kennzahlenzeile ────────────────────────────────────────────────

def test_die_auftragssumme_bleibt_hinter_see_betrag(rumpf):
    """Monteure duerfen die Auftragssumme nicht sehen (v3.9.456).

    Eine neue Zeile, die sie ungefragt zeigt, waere ein Datenleck - und zwar
    ein huebsches.
    """
    i = rumpf.find("fmt$(_kz.betrag)")
    assert i > 0, "Die Summe steht nicht in der Kennzahlenzeile."
    davor = rumpf[max(0, i - 260):i]
    assert "_seeBetrag" in davor, (
        "Die Auftragssumme in der Kennzahlenzeile haengt NICHT an _seeBetrag. "
        "Monteure wuerden sie sehen.")


def test_die_kennzahlen_kommen_aus_den_vorhandenen_quellen(rumpf):
    """Keine neue Berechnung, keine andere Rundung - der Bestandsschutz
    verbietet beides ausdruecklich."""
    m = re.search(r"const _kz=_react\.useMemo\.call\(void 0, \(\)=>\{(.*?)\},"
                  r"\[projects,hoursByProject\]\);", rumpf, re.S)
    assert m, "Die Kennzahlen-Berechnung wurde nicht gefunden."
    rumpf_kz = m.group(1)
    assert "hoursByProject[p.id]" in rumpf_kz, "Die Stunden kommen aus einer anderen Quelle."
    assert "p.betrag" in rumpf_kz, "Der Betrag kommt aus einer anderen Quelle."
    assert 'p.status==="aktiv"' in rumpf_kz, "Die Zahl der aktiven Projekte kommt woanders her."


# ── 6. TDZ - der Riegel, der hier gefehlt hat ─────────────────────────────

def test_jede_berechnung_steht_hinter_ihren_quellen(rumpf):
    """DER Riegel dieser Stufe. Zweimal dieselbe Falle in derselben Ansicht.

    `node_check.py` PARST die <script>-Bloecke und fuehrt sie nicht aus. Eine
    const, die vor ihrer Initialisierung gelesen wird, ist syntaktisch
    tadellos und zur Laufzeit ein Absturz, den ViewBoundary faengt - der Tab
    zeigt dann einen Fehler statt der Liste, bei gruenem Tor.
    """
    paare = [
        ("hoursByProject", "_kz"),
        ("isMob", "_gridCols"),
    ]
    for quelle, nutzer in paare:
        i_q = rumpf.find("const %s=" % quelle)
        i_n = rumpf.find("const %s=" % nutzer)
        assert i_q >= 0, "Die Quelle %s wurde nicht gefunden." % quelle
        assert i_n >= 0, "Der Nutzer %s wurde nicht gefunden." % nutzer
        assert i_q < i_n, (
            "TDZ: %s steht VOR seiner Quelle %s. Beim Rendern wird die "
            "Abhaengigkeit gelesen, bevor die const initialisiert ist - "
            "'Cannot access %s before initialization'. node_check bleibt "
            "dabei gruen." % (nutzer, quelle, quelle))


def test_der_tdz_riegel_kann_rot_werden(rumpf):
    """KOEDER. Ein Riegel, der eine Reihenfolge prueft, muss bei vertauschter
    Reihenfolge anschlagen - sonst prueft er nichts."""
    i_q = rumpf.find("const hoursByProject=")
    i_n = rumpf.find("const _kz=")
    vertauscht = rumpf[:i_q] + rumpf[i_n:] + rumpf[i_q:i_n]
    assert vertauscht.find("const _kz=") < vertauscht.find("const hoursByProject="), (
        "Die Umkehrprobe hat die Reihenfolge nicht wirklich vertauscht - dann "
        "sagt der Riegel darueber nichts aus.")
