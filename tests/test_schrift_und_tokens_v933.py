# -*- coding: utf-8 -*-
"""v3.9.933 Stufe 2a - Archivo selbst gehostet, Token-Objekt UI.

WARUM DIE SCHRIFT INS REPO MUSS
───────────────────────────────
Die CSP erlaubt `style-src 'self' 'unsafe-inline' cdnjs` und
`font-src 'self' cdnjs`. fonts.googleapis.com und fonts.gstatic.com stehen
dort NICHT. Ein Google-Fonts-Link scheitert deshalb STILL - kein Fehler im
Bild, keine Schrift. Das ist die gefaehrlichste Art von Fehler: einer, der
nach nichts aussieht.

Deshalb misst der Riegel hier nicht nur, dass ein @font-face dasteht, sondern
dass die Quelle RELATIV ist und die Datei WIRKLICH EXISTIERT und ein WOFF2
ist (Magic Bytes, nicht Dateiendung).

DER VARIABLE-SCHRIFT-FUND
─────────────────────────
Google liefert Archivo als variable Schrift: alle vier Gewichte zeigen auf
denselben Inhalt. Vier Dateien haetten dieselben 35 kB viermal geladen. Ein
eigener Riegel haelt das fest, damit es niemand "repariert".
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
IDX = WURZEL / "index.html"
FONTS = WURZEL / "fonts"


@pytest.fixture(scope="module")
def roh():
    return io.open(str(IDX), encoding="utf-8", newline="").read()


@pytest.fixture(scope="module")
def kopf(roh):
    return roh[:roh.lower().find("</head>")]


# ── Die Schrift ────────────────────────────────────────────────────────────

def test_es_gibt_font_face_regeln_fuer_archivo(kopf):
    regeln = re.findall(r"@font-face\{[^}]*Archivo[^}]*\}", kopf)
    assert regeln, "Keine @font-face-Regel fuer Archivo im <head>."
    assert len(regeln) == 2, (
        "Erwartet 2 Regeln (latin, latin-ext) - gefunden %d. Archivo ist eine "
        "VARIABLE Schrift: alle Gewichte haben denselben Inhalt. Vier Regeln "
        "wuerden dieselben Bytes viermal laden." % len(regeln))


def test_die_schrift_kommt_aus_dem_repo_und_nicht_von_google(kopf):
    """Der eigentliche Punkt: ueber die CSP kommt nichts von Google herein."""
    for quelle in re.findall(r"@font-face\{[^}]*src:url\('([^']+)'", kopf):
        assert quelle.startswith("./fonts/"), (
            "Schriftquelle %r ist nicht relativ. font-src erlaubt nur 'self' "
            "und cdnjs - alles andere scheitert STILL." % quelle)
    # Gemessen wird das LADEN, nicht das Wort: der erklaerende Kommentar am
    # @font-face-Block nennt beide Hosts ausdruecklich - er sagt ja gerade,
    # dass sie NICHT erlaubt sind. Ein Riegel auf die blosse Zeichenfolge
    # waere hier ein Dauer-Fehlalarm, und ein Riegel, der staendig grundlos
    # rot ist, wird abgeschaltet.
    geladen = re.findall(r"(?:src:\s*)?url\(['\"]?(https?://[^'\")]+)", kopf)
    fremd = [u for u in geladen
             if "fonts.googleapis.com" in u or "fonts.gstatic.com" in u]
    assert not fremd, (
        "Es wird von Google geladen: %s - die CSP erlaubt das nicht, und der "
        "Fehler ist unsichtbar." % fremd)


def test_jede_genannte_schriftdatei_existiert_und_ist_ein_woff2(kopf):
    """Dem Dateinamen wird nicht geglaubt - die Magic Bytes entscheiden."""
    quellen = re.findall(r"@font-face\{[^}]*src:url\('\./([^']+)'", kopf)
    assert quellen, (
        "Keine einzige Schriftquelle gefunden. Das ist kein gruenes Ergebnis, "
        "sondern eine ausgefallene Messung.")
    for q in quellen:
        p = WURZEL / q
        assert p.exists(), "Die Schriftdatei %s fehlt." % q
        with io.open(str(p), "rb") as f:
            magic = f.read(4)
        assert magic == b"wOF2", (
            "%s ist kein WOFF2 (Magic %r) - die Endung sagt nichts." % (q, magic))
        assert p.stat().st_size > 4000, "%s ist verdaechtig klein." % q


def test_die_gewichtsspanne_deckt_alle_vier_schnitte(kopf):
    """400/500/600/700 muessen aus der Achse fallen koennen."""
    spannen = re.findall(r"@font-face\{[^}]*font-weight:(\d+)\s+(\d+)", kopf)
    assert spannen, (
        "Keine Gewichtsspanne gefunden. Mit einem festen font-weight je Datei "
        "braeuchte es vier Dateien - und die haetten alle denselben Inhalt.")
    for a, b in spannen:
        assert int(a) <= 400 and int(b) >= 700, (
            "Die Spanne %s-%s deckt 400 bis 700 nicht ab." % (a, b))


def test_die_zwei_schriftdateien_sind_wirklich_verschieden():
    """KOEDER. Waeren latin und latin-ext dieselbe Datei, waere die Aufteilung
    eine Behauptung ohne Inhalt - und der Riegel darueber wertlos."""
    a = (FONTS / "archivo-var-latin.woff2").read_bytes()
    b = (FONTS / "archivo-var-latin-ext.woff2").read_bytes()
    assert a != b, (
        "latin und latin-ext sind bytegleich - dann trennt die Aufteilung "
        "nichts und eine der beiden Dateien ist reine Ladezeit.")


def test_die_lizenz_liegt_bei():
    """Die SIL OFL verlangt, dass der Lizenztext mitgeliefert wird."""
    p = FONTS / "OFL.txt"
    assert p.exists(), "fonts/OFL.txt fehlt - die OFL verlangt die Beilage."
    txt = io.open(str(p), encoding="utf-8", errors="replace").read()
    assert "SIL OPEN FONT LICENSE" in txt.upper(), "OFL.txt ist nicht die Lizenz."


def test_der_schriftstapel_beginnt_mit_archivo(roh):
    assert "font-family: Archivo, 'Segoe UI', system-ui, sans-serif" in roh, (
        "Der globale Schriftstapel fuehrt Archivo nicht an erster Stelle.")


def test_die_schriften_liegen_im_offline_vorrat():
    """Ohne sie faellt die App OFFLINE auf die Systemschrift zurueck - genau
    dort, wo sie gebraucht wird."""
    sw = io.open(str(WURZEL / "sw.js"), encoding="utf-8", newline="").read()
    m = re.search(r"const ASSETS\s*=\s*\[(.*?)\]", sw, re.S)
    assert m, ("Die ASSETS-Liste in sw.js wurde nicht gefunden. Das ist rot, "
               "nicht gruen - eine nicht gefundene Liste ist kein Beleg dafuer, "
               "dass nichts fehlt.")
    liste = m.group(1)
    for datei in ("archivo-var-latin.woff2", "archivo-var-latin-ext.woff2"):
        assert datei in liste, "%s fehlt im Offline-Vorrat." % datei


# ── Das Token-Objekt ───────────────────────────────────────────────────────

ERWARTET = {
    "grund": "#F2F4F2", "flaeche": "#FFFFFF", "tinte": "#141A16",
    "grau": "#5B6660", "linie": "#E2E6E3", "marke": "#009640",
    "markeTxt": "#00722F", "markeBg": "#E8F4EC", "achtung": "#B4530A",
    "achtungTxt": "#8A3E06", "achtungBg": "#FBEDE1",
    "neutralTxt": "#414B45", "neutralBg": "#EEF1EF",
}


def test_das_token_objekt_traegt_genau_die_vorgegebenen_werte(roh):
    m = re.search(r"const UI=\{(.*?)\};", roh, re.S)
    assert m, "Das Token-Objekt UI wurde nicht gefunden."
    rumpf = m.group(1)
    falsch = []
    for name, wert in ERWARTET.items():
        t = re.search(r'\b%s:"([^"]+)"' % name, rumpf)
        if not t:
            falsch.append("%s fehlt" % name)
        elif t.group(1).upper() != wert.upper():
            falsch.append("%s ist %s statt %s" % (name, t.group(1), wert))
    assert not falsch, "Abweichende Tokens: %s" % "; ".join(falsch)


def test_keine_schriftgroesse_unter_zwoelf_im_token_objekt(roh):
    m = re.search(r"const UI=\{(.*?)\};", roh, re.S)
    groessen = [int(x) for x in re.findall(r"\bf[A-Za-z]+:(\d+)", m.group(1))]
    assert groessen, "Keine Schriftgroessen im Token-Objekt."
    assert min(groessen) >= 12, (
        "Die kleinste Groesse ist %d - 12 ist die Untergrenze." % min(groessen))


def test_die_drei_regeln_stehen_als_kommentar_am_objekt(roh):
    """Ein Token ohne seine Regel ist nur eine Zahl.

    Wer spaeter #009640 fuer eine Statusampel benutzt, macht daraus ein Gruen,
    das mal Logo und mal 'in Ordnung' heisst - und dann keines von beidem.
    """
    i = roh.find("const UI={")
    umfeld = roh[max(0, i - 1600):i]
    for wort in ("NIE Statusampel", "HELLIGKEIT", "tabular-nums"):
        assert wort in umfeld, (
            "Die Regel %r steht nicht am Token-Objekt." % wort)


def test_die_tokens_sind_noch_nicht_global_ausgerollt(roh):
    """Diese Stufe legt die Groessen NUR an. Ein globaler Farb-Sweep ueber
    30.000 Zeilen mit Inline-Styles waere nicht mehr pruefbar - deshalb
    wandert je Ansicht eine eigene Stufe."""
    assert roh.count("const UI={") == 1, "Es gibt mehr als ein Token-Objekt."
