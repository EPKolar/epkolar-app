# -*- coding: utf-8 -*-
"""Riegel fuer das DATEI-Manifest der PWA und die dazugehoerigen Icons (v3.9.931).

WAS HIER GEMESSEN WIRD
──────────────────────
Bis v3.9.930 entstand das Manifest erst zur LAUFZEIT: index.html baute einen
JSON-String, machte daraus ein Blob und haengte es als `<link rel="manifest">`
in den Kopf; die Icons wurden im selben Zug per Canvas gezeichnet und als
data:-URL eingetragen. Nichts davon existierte als Datei - der Service Worker
konnte also nichts davon vorhalten, und `purpose:"maskable"` zeigte auf
DIESELBE Bilddatei wie `purpose:"any"`.

Diese Riegel messen deshalb WIRKUNG, nicht Anwesenheit:

  * nicht "manifest.json ist da", sondern "jede darin genannte Bilddatei ist
    ein PNG, dessen KOPF die zugesagte Kantenlaenge traegt". Der Dateiname
    wird nicht geglaubt - `icon-512.png` mit 64 Bildpunkten ist genau der
    Fehler, der sonst bis auf das Geraet durchrutscht.
  * nicht "es gibt eine maskable-Zeile", sondern "im aeusseren Zehntel der
    maskable-Datei liegt kein einziger Bildpunkt des Motivs". Das ist die
    Zusage, die `purpose:"maskable"` abgibt.

KOEDER
──────
Jeder Riegel hier ist ein SUCHENDER Riegel - er zaehlt Beanstandungen und ist
gruen, wenn er keine findet. Genau diese Bauart wird beim eigenen Ausfall
gruen: findet der PNG-Leser nichts, meldet er "keine Fehler". Deshalb wird
jede Pruefstelle zusaetzlich gegen eine ABSICHTLICH FALSCHE Attrappe gefahren
(`test_koeder_*`). Faellt der Leser aus, werden die Koeder rot - der Ausfall
ist damit sichtbar und nicht mehr als Erfolg getarnt.

BEWUSST NICHT HIER
──────────────────
"Der Laufzeit-Blob-Builder ist raus" und "der head verlinkt manifest.json"
haengen beide an index.html. Die Datei wurde in diesem Lauf nicht angefasst
(paralleler Lauf), darum fehlen diese beiden Riegel noch. Sie gehoeren
nachgezogen, sobald der Kopf umgebaut ist.
"""
import io
import json
import os
import re
import struct
import zlib

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PNG_SIGNATUR = b"\x89PNG\r\n\x1a\n"

# Anteil der Kantenlaenge, der bei einem maskable-Icon frei bleiben MUSS.
# Android beschneidet auf rund 80 % Kantenlaenge - also >=10 % Rand ringsum.
MASKABLE_RAND = 0.10


# ══════════════════════════════════════════════════════════════════════════
# PNG-Leser in reinem Python
# ══════════════════════════════════════════════════════════════════════════
# Warum nicht Pillow: tests/requirements.txt fuehrt nur pytest. Ein
# `pytest.importorskip("PIL")` waere hier die schlimmste aller Loesungen -
# der Riegel wuerde auf jedem Rechner ohne Pillow UEBERSPRUNGEN und damit
# still gruen, obwohl er nichts gemessen hat. struct + zlib genuegen.

def png_kopf(daten):
    """Liest IHDR. Gibt (breite, hoehe, bittiefe, farbtyp, verschraenkt) zurueck.

    Wirft ValueError, wenn es kein PNG ist - NICHT None, denn ein stiller
    Rueckgabewert wuerde vom Aufrufer als "nichts zu beanstanden" gelesen.
    """
    if not daten.startswith(PNG_SIGNATUR):
        raise ValueError("keine PNG-Signatur (erste 8 Bytes: %r)" % (daten[:8],))
    if daten[12:16] != b"IHDR":
        raise ValueError("erster Abschnitt ist nicht IHDR, sondern %r" % (daten[12:16],))
    breite, hoehe, bittiefe, farbtyp, _komp, _filt, verschraenkt = struct.unpack(
        ">IIBBBBB", daten[16:29]
    )
    if breite == 0 or hoehe == 0:
        raise ValueError("IHDR nennt Kantenlaenge 0 (%dx%d)" % (breite, hoehe))
    return breite, hoehe, bittiefe, farbtyp, verschraenkt


def _entfiltern(roh, breite, hoehe, kanaele):
    """Macht die PNG-Zeilenfilter rueckgaengig (Filtertyp 0-4)."""
    bpp = kanaele
    zeilenlaenge = breite * bpp
    ergebnis = []
    vorige = bytearray(zeilenlaenge)
    i = 0
    for y in range(hoehe):
        if i >= len(roh):
            raise ValueError("Bilddaten enden nach %d von %d Zeilen" % (y, hoehe))
        f = roh[i]
        i += 1
        zeile = bytearray(roh[i:i + zeilenlaenge])
        if len(zeile) != zeilenlaenge:
            raise ValueError("Zeile %d ist verkuerzt (%d statt %d)" % (y, len(zeile), zeilenlaenge))
        i += zeilenlaenge
        if f == 0:
            pass
        elif f == 1:
            for x in range(bpp, zeilenlaenge):
                zeile[x] = (zeile[x] + zeile[x - bpp]) & 0xFF
        elif f == 2:
            for x in range(zeilenlaenge):
                zeile[x] = (zeile[x] + vorige[x]) & 0xFF
        elif f == 3:
            for x in range(zeilenlaenge):
                a = zeile[x - bpp] if x >= bpp else 0
                zeile[x] = (zeile[x] + ((a + vorige[x]) >> 1)) & 0xFF
        elif f == 4:
            for x in range(zeilenlaenge):
                a = zeile[x - bpp] if x >= bpp else 0
                b = vorige[x]
                c = vorige[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                if pa <= pb and pa <= pc:
                    pr = a
                elif pb <= pc:
                    pr = b
                else:
                    pr = c
                zeile[x] = (zeile[x] + pr) & 0xFF
        else:
            raise ValueError("unbekannter Zeilenfilter %d in Zeile %d" % (f, y))
        ergebnis.append(bytes(zeile))
        vorige = zeile
    return ergebnis


def png_pixel(daten):
    """Gibt (breite, hoehe, zeilen) zurueck; jede Zeile ist eine Liste von RGBA."""
    breite, hoehe, bittiefe, farbtyp, verschraenkt = png_kopf(daten)
    if bittiefe != 8 or farbtyp not in (2, 6) or verschraenkt != 0:
        raise ValueError(
            "nur 8-Bit RGB/RGBA ohne Verschraenkung lesbar "
            "(bittiefe=%d farbtyp=%d verschraenkt=%d)" % (bittiefe, farbtyp, verschraenkt)
        )
    kanaele = 4 if farbtyp == 6 else 3
    idat = bytearray()
    i = 8
    while i < len(daten):
        laenge = struct.unpack(">I", daten[i:i + 4])[0]
        typ = daten[i + 4:i + 8]
        if typ == b"IDAT":
            idat.extend(daten[i + 8:i + 8 + laenge])
        elif typ == b"IEND":
            break
        i += 12 + laenge
    if not idat:
        raise ValueError("kein IDAT-Abschnitt gefunden")
    roh = zlib.decompress(bytes(idat))
    zeilen = []
    for zeile in _entfiltern(roh, breite, hoehe, kanaele):
        punkte = []
        for x in range(breite):
            o = x * kanaele
            if kanaele == 4:
                punkte.append((zeile[o], zeile[o + 1], zeile[o + 2], zeile[o + 3]))
            else:
                punkte.append((zeile[o], zeile[o + 1], zeile[o + 2], 255))
        zeilen.append(punkte)
    return breite, hoehe, zeilen


def png_schreiben(breite, hoehe, punkt):
    """Kleiner PNG-Schreiber - NUR fuer die Attrappen der Koeder-Faelle."""
    roh = bytearray()
    for y in range(hoehe):
        roh.append(0)
        for x in range(breite):
            roh.extend(punkt(x, y))

    def abschnitt(typ, inhalt):
        return (struct.pack(">I", len(inhalt)) + typ + inhalt
                + struct.pack(">I", zlib.crc32(typ + inhalt) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 6, 0, 0, 0)
    return (PNG_SIGNATUR + abschnitt(b"IHDR", ihdr)
            + abschnitt(b"IDAT", zlib.compress(bytes(roh)))
            + abschnitt(b"IEND", b""))


# ══════════════════════════════════════════════════════════════════════════
# Die Pruefstellen. Jede gibt eine Liste von Beanstandungen zurueck.
# Leere Liste = sauber. Genau diese Funktionen fahren auch die Koeder.
# ══════════════════════════════════════════════════════════════════════════

def masse_beanstanden(daten, zugesagt, name):
    """Stimmt der PNG-KOPF mit der Zusage aus dem Manifest ueberein?"""
    fehler = []
    try:
        breite, hoehe, bittiefe, farbtyp, _v = png_kopf(daten)
    except ValueError as e:
        return ["%s: kein lesbares PNG - %s" % (name, e)]
    if "x" not in zugesagt:
        return ["%s: sizes=%r ist keine Angabe der Form BxH" % (name, zugesagt)]
    zw, zh = zugesagt.split("x", 1)
    if not (zw.isdigit() and zh.isdigit()):
        return ["%s: sizes=%r ist keine Zahlenangabe" % (name, zugesagt)]
    if (breite, hoehe) != (int(zw), int(zh)):
        fehler.append("%s: Kopf sagt %dx%d, das Manifest verspricht %s"
                      % (name, breite, hoehe, zugesagt))
    if bittiefe != 8 or farbtyp not in (2, 6):
        fehler.append("%s: bittiefe=%d farbtyp=%d - vom Browser nicht garantiert lesbar"
                      % (name, bittiefe, farbtyp))
    return fehler


def rand_beanstanden(daten, name, anteil=MASKABLE_RAND):
    """Haelt ein maskable-Icon den Sicherheitsrand ein?

    Gemessen wird der Rahmen aus `anteil` der Kantenlaenge an allen vier
    Seiten: dort darf ausschliesslich die Farbe der Ecke (0,0) stehen.
    Zusaetzlich MUSS im Inneren ueberhaupt etwas anderes liegen - sonst waere
    ein vollstaendig leeres Bild "randtreu" und der Riegel gruen fuer nichts.
    """
    fehler = []
    try:
        breite, hoehe, zeilen = png_pixel(daten)
    except (ValueError, zlib.error) as e:
        return ["%s: Bilddaten nicht lesbar - %s" % (name, e)]

    hintergrund = zeilen[0][0]
    rx = int(breite * anteil)
    ry = int(hoehe * anteil)
    if rx < 1 or ry < 1:
        return ["%s: zu klein (%dx%d), um %d %% Rand zu messen"
                % (name, breite, hoehe, int(anteil * 100))]

    if hintergrund[3] != 255:
        fehler.append("%s: Rand ist durchsichtig (alpha=%d) - maskable-Icons "
                      "duerfen das nicht" % (name, hintergrund[3]))

    verletzt = 0
    erstes = None
    for y in range(hoehe):
        randzeile = y < ry or y >= hoehe - ry
        for x in range(breite):
            if not (randzeile or x < rx or x >= breite - rx):
                continue
            if zeilen[y][x] != hintergrund:
                verletzt += 1
                if erstes is None:
                    erstes = (x, y, zeilen[y][x])
    if verletzt:
        fehler.append("%s: %d Bildpunkte im %d-%%-Rand tragen nicht die "
                      "Hintergrundfarbe %s (erster: x=%d y=%d %s)"
                      % (name, verletzt, int(anteil * 100), hintergrund,
                         erstes[0], erstes[1], erstes[2]))

    # Selbstprobe: ohne Motiv im Inneren misst die Randpruefung nichts.
    inhalt = any(zeilen[y][x] != hintergrund
                 for y in range(ry, hoehe - ry)
                 for x in range(rx, breite - rx))
    if not inhalt:
        fehler.append("%s: innerhalb des Randes steht ueberhaupt kein Motiv - "
                      "das Bild ist einfarbig" % name)
    return fehler


def assets_liste(sw_quelltext):
    """Die Eintraege der ASSETS-Liste aus sw.js.

    Wirft, wenn die Liste nicht gefunden wird. Ein leeres Ergebnis waere sonst
    ununterscheidbar von "Liste enthaelt nichts Beanstandetes".
    """
    m = re.search(r"const\s+ASSETS\s*=\s*\[(.*?)\]\s*;", sw_quelltext, re.S)
    if not m:
        raise ValueError("ASSETS-Liste in sw.js nicht gefunden")
    return [t for t in re.findall(r"['\"]([^'\"]*)['\"]", m.group(1))]


def _ohne_punkt(pfad):
    return pfad[2:] if pfad.startswith("./") else pfad


# ══════════════════════════════════════════════════════════════════════════
# Vorrat
# ══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def manifest():
    pfad = os.path.join(REPO_ROOT, "manifest.json")
    assert os.path.isfile(pfad), (
        "manifest.json fehlt im Repo-Root. Das Manifest darf nicht nur zur "
        "Laufzeit als Blob entstehen - ein Blob-Manifest hat keinen Ursprung, "
        "damit sind start_url und scope nicht pruefbar."
    )
    with io.open(pfad, encoding="utf-8") as f:
        roh = f.read()
    try:
        return json.loads(roh)
    except ValueError as e:
        raise AssertionError("manifest.json ist kein gueltiges JSON: %s" % e)


@pytest.fixture(scope="module")
def sw_quelltext():
    with io.open(os.path.join(REPO_ROOT, "sw.js"), encoding="utf-8") as f:
        return f.read()


def _bytes(name):
    with open(os.path.join(REPO_ROOT, _ohne_punkt(name)), "rb") as f:
        return f.read()


# ══════════════════════════════════════════════════════════════════════════
# (2) manifest.json - Inhalt, Icons, echte Dateien, echte Masse
# ══════════════════════════════════════════════════════════════════════════

def test_manifest_traegt_die_pflichtfelder(manifest):
    for feld in ("name", "short_name", "description", "start_url", "scope",
                 "display", "background_color", "theme_color", "categories",
                 "icons"):
        assert feld in manifest, "manifest.json fuehrt %r nicht" % feld
    assert manifest["display"] == "standalone", manifest["display"]
    assert manifest["background_color"] == "#0f1117", manifest["background_color"]
    assert manifest["theme_color"] == "#009640", manifest["theme_color"]
    assert manifest["categories"], "categories ist leer"


def test_start_url_und_scope_sind_relativ(manifest):
    """Absolute Adressen im Manifest binden die App an EINEN Host.

    Die Laufzeitfassung setzte `location.origin + pathname` ein - das ist auf
    dem Geraet richtig, in einer Datei aber eine feste Zusage. Relativ bleibt
    es unter jedem Ursprung (GitHub Pages, Vorschau, lokal) korrekt.
    """
    for feld in ("start_url", "scope"):
        wert = manifest[feld]
        assert not re.match(r"^[a-zA-Z]+:", wert), (
            "%s=%r ist absolut - das bindet die App an einen Host" % (feld, wert))
        assert not wert.startswith("/"), (
            "%s=%r ist wurzelabsolut - bricht, sobald die App in einem "
            "Unterverzeichnis liegt" % (feld, wert))


def test_manifest_nennt_ein_192er_und_ein_512er_icon(manifest):
    masse = {i.get("sizes") for i in manifest["icons"]}
    assert "192x192" in masse, "kein 192x192-Icon im Manifest (gefunden: %s)" % masse
    assert "512x512" in masse, "kein 512x512-Icon im Manifest (gefunden: %s)" % masse


def test_jedes_icon_ist_zweimal_eingetragen_any_und_maskable(manifest):
    """Je Kantenlaenge muss es genau eine "any"- und eine "maskable"-Zeile geben."""
    for grosse in ("192x192", "512x512"):
        zwecke = [i.get("purpose") for i in manifest["icons"] if i.get("sizes") == grosse]
        assert "any" in zwecke, "%s hat keine purpose=any-Zeile (%s)" % (grosse, zwecke)
        assert "maskable" in zwecke, "%s hat keine purpose=maskable-Zeile (%s)" % (grosse, zwecke)


def test_any_und_maskable_zeigen_nicht_auf_dieselbe_datei(manifest):
    """Genau das war der Fehler der Laufzeitfassung.

    `any` verspricht randlose Ausnutzung der Flaeche, `maskable` verspricht
    >=10 % Sicherheitsrand. Eine Datei kann nicht beides halten - wer sie
    doppelt eintraegt, gibt eine der beiden Zusagen falsch ab.
    """
    for grosse in ("192x192", "512x512"):
        nach_zweck = {}
        for i in manifest["icons"]:
            if i.get("sizes") == grosse:
                nach_zweck.setdefault(i.get("purpose"), set()).add(i.get("src"))
        gemeinsam = nach_zweck.get("any", set()) & nach_zweck.get("maskable", set())
        assert not gemeinsam, (
            "%s: %s ist zugleich als any UND als maskable eingetragen - eine "
            "der beiden Zusagen ist falsch" % (grosse, sorted(gemeinsam)))


def test_jede_genannte_icondatei_existiert_und_haelt_ihre_zusage(manifest):
    """DER Kernriegel: Datei da, echtes PNG, und der KOPF traegt die Masse.

    Dem Dateinamen wird nicht geglaubt. `icon-512.png` mit 64 Bildpunkten
    waere sonst still in Ordnung - und faellt erst auf dem Geraet auf.
    """
    fehler = []
    assert manifest["icons"], "icons-Liste ist leer"
    for eintrag in manifest["icons"]:
        quelle = eintrag.get("src", "")
        assert quelle and not quelle.startswith("data:"), (
            "Icon-Quelle %r ist keine Datei - data:-URLs kann der Service "
            "Worker nicht vorhalten" % quelle[:40])
        pfad = os.path.join(REPO_ROOT, _ohne_punkt(quelle))
        if not os.path.isfile(pfad):
            fehler.append("%s: Datei existiert nicht" % quelle)
            continue
        with open(pfad, "rb") as f:
            fehler.extend(masse_beanstanden(f.read(), eintrag.get("sizes", ""), quelle))
    assert not fehler, "\n".join(fehler)


def test_maskable_icons_halten_den_sicherheitsrand(manifest):
    """Das Motiv darf hoechstens 80 % der Kantenlaenge einnehmen."""
    maskable = [i for i in manifest["icons"] if i.get("purpose") == "maskable"]
    assert maskable, "kein maskable-Icon im Manifest"
    fehler = []
    for eintrag in maskable:
        fehler.extend(rand_beanstanden(_bytes(eintrag["src"]), eintrag["src"]))
    assert not fehler, "\n".join(fehler)


# ══════════════════════════════════════════════════════════════════════════
# (4) sw.js - ASSETS
# ══════════════════════════════════════════════════════════════════════════

def test_sw_assets_enthaelt_manifest_und_alle_icons(manifest, sw_quelltext):
    """Was der Service Worker nicht vorhaelt, fehlt beim ersten Offline-Start."""
    eintraege = {_ohne_punkt(a) for a in assets_liste(sw_quelltext)}
    erwartet = ["manifest.json"] + [_ohne_punkt(i["src"]) for i in manifest["icons"]]
    fehlt = sorted({e for e in erwartet if e not in eintraege})
    assert not fehlt, (
        "ASSETS in sw.js fuehrt nicht: %s (vorhanden: %s)"
        % (fehlt, sorted(eintraege)))


def test_alle_assets_eintraege_existieren_auch(sw_quelltext):
    """`cache.addAll` ist alles-oder-nichts.

    Ein einziger Eintrag, der 404 liefert, laesst die GANZE install-Phase
    scheitern - der Service Worker wird dann nie aktiv und die App hat
    ueberhaupt keinen Offline-Vorrat mehr. Ein Tippfehler in der Liste ist
    darum nicht "ein fehlendes Icon", sondern der Totalausfall.
    """
    fehlt = []
    for eintrag in assets_liste(sw_quelltext):
        rest = _ohne_punkt(eintrag)
        if rest in ("", "/"):
            continue  # './' ist das Verzeichnis selbst
        if not os.path.exists(os.path.join(REPO_ROOT, rest)):
            fehlt.append(eintrag)
    assert not fehlt, "ASSETS nennt Dateien, die es nicht gibt: %s" % fehlt


# ══════════════════════════════════════════════════════════════════════════
# KOEDER - Beweis, dass die Riegel oben ueberhaupt rot werden KOENNEN
# ══════════════════════════════════════════════════════════════════════════
# Jeder Koeder faehrt GENAU DIE FUNKTION, die der echte Riegel faehrt. Waere
# der PNG-Leser kaputt, wuerde er nichts mehr finden - die echten Riegel
# blieben gruen, diese hier werden rot.

def test_koeder_masspruefung_erkennt_die_falsche_zusage():
    """192er Bild, das sich als 512er ausgibt - muss beanstandet werden."""
    attrappe = png_schreiben(192, 192, lambda x, y: (0, 150, 64, 255))
    sauber = masse_beanstanden(attrappe, "192x192", "attrappe.png")
    assert sauber == [], "der eigene Schreiber erzeugt kein lesbares 192er PNG: %s" % sauber
    gelogen = masse_beanstanden(attrappe, "512x512", "attrappe.png")
    assert gelogen, "die Masspruefung haelt 192x192 fuer 512x512 - sie misst nichts"
    assert "192x192" in gelogen[0] and "512x512" in gelogen[0], gelogen


def test_koeder_masspruefung_erkennt_eine_nicht_png_datei():
    beanstandet = masse_beanstanden(b"<html>kein Bild</html>", "192x192", "luege.png")
    assert beanstandet, "eine HTML-Datei gilt der Pruefung als gueltiges PNG"
    assert "PNG" in beanstandet[0], beanstandet


def test_koeder_randpruefung_erkennt_ein_randloses_motiv():
    """Motiv bis an die Kante - genau das darf maskable NICHT."""
    rand_hin = png_schreiben(
        100, 100,
        lambda x, y: (15, 17, 23, 255) if not (11 <= x < 89 and 11 <= y < 89) else (0, 150, 64, 255))
    assert rand_beanstanden(rand_hin, "brav.png") == [], \
        "die Randpruefung beanstandet ein Bild, das den Rand einhaelt"

    randlos = png_schreiben(100, 100, lambda x, y: (0, 150, 64, 255) if 2 <= x < 98 else (15, 17, 23, 255))
    beanstandet = rand_beanstanden(randlos, "randlos.png")
    assert beanstandet, "ein Motiv bis 2 % an die Kante gilt als randtreu - die Pruefung misst nichts"
    assert "Rand" in beanstandet[0], beanstandet


def test_koeder_randpruefung_erkennt_ein_leeres_bild():
    """Ein einfarbiges Bild haelt jeden Rand ein - und ist trotzdem kaputt."""
    leer = png_schreiben(100, 100, lambda x, y: (15, 17, 23, 255))
    beanstandet = rand_beanstanden(leer, "leer.png")
    assert beanstandet, "ein vollstaendig leeres Bild kommt durch die Randpruefung"
    assert "einfarbig" in beanstandet[-1], beanstandet


def test_koeder_randpruefung_erkennt_durchsichtigen_rand():
    durchsichtig = png_schreiben(
        100, 100,
        lambda x, y: (0, 150, 64, 255) if (11 <= x < 89 and 11 <= y < 89) else (0, 0, 0, 0))
    beanstandet = rand_beanstanden(durchsichtig, "glas.png")
    assert beanstandet, "ein durchsichtiger Rand kommt durch"
    assert "durchsichtig" in beanstandet[0], beanstandet


def test_koeder_assets_pruefung_sieht_eine_unvollstaendige_liste():
    """Der Stand VOR dieser Aenderung - die Pruefung muss ihn ablehnen."""
    vorher = "const CACHE_NAME = \"x\";\nconst ASSETS = [\n  './',\n  './index.html'\n];\n"
    eintraege = {_ohne_punkt(a) for a in assets_liste(vorher)}
    assert eintraege == {"", "index.html"}, eintraege
    assert "manifest.json" not in eintraege, (
        "die Extraktion liefert Eintraege, die in der Quelle gar nicht stehen")


def test_koeder_assets_pruefung_schweigt_nicht_bei_ausfall():
    """Findet die Liste nicht statt, MUSS es knallen - nicht [] zurueckgeben.

    Das ist die Selbstprobe des zaehlenden Riegels: ein leeres Ergebnis waere
    sonst ununterscheidbar von "nichts zu beanstanden".
    """
    with pytest.raises(ValueError):
        assets_liste("// sw.js ohne jede Liste\nself.addEventListener('install', function(){});")


def test_koeder_png_leser_liest_zurueck_was_er_schreibt():
    """Rundlauf - faellt der Leser aus, ist er nicht mehr still gruen."""
    daten = png_schreiben(7, 5, lambda x, y: (x * 10, y * 20, 7, 255))
    breite, hoehe, zeilen = png_pixel(daten)
    assert (breite, hoehe) == (7, 5)
    assert zeilen[4][6] == (60, 80, 7, 255), zeilen[4][6]
