# -*- coding: utf-8 -*-
"""Messung zu `docs/befunde/DIE_31_VERDACHTE.md`, Teil 1: die MUSTER.

Fuer jeden Verdacht mit einer entscheidenden leeren Grundgesamtheit wird das
Suchmuster des Riegels WOERTLICH uebernommen und drei Dinge gemessen:

  1. die tatsaechliche Groesse der Grundgesamtheit im heutigen index.html,
  2. ein KOEDER JE SCHREIBWEISE - findet das Muster den eingebauten Fall?
     Es gibt zwei Erzeuger (`React.createElement(` und der Kuerzel `h(`) und
     zwei Anfuehrungszeichen. Ein Muster, das eine Form nicht kennt, meldet
     "kommt nicht vor" - nicht unterscheidbar von einem echten Befund.
  3. eine GEGENPROBE - ein Fall, der NICHT gemeldet werden darf.

`index.html` wird NUR GELESEN. Kein Koeder wird in die Datei geschrieben;
die Koeder laufen gegen Zeichenketten im Speicher.

Aufruf:
    python scripts/befund_31_muster.py            # Messung
    python scripts/befund_31_muster.py --selbstprobe   # nur die Eichungen
"""
import io
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WURZEL, "scripts"))
import code_scan  # noqa: E402

INDEX = os.path.join(WURZEL, "index.html")


def _index():
    with io.open(INDEX, "r", encoding="utf-8") as f:
        return f.read()


def _kopf(roh):
    """Wie die Vorrichtung `kopf` in tests/test_schrift_und_tokens_v933.py."""
    return roh[:roh.lower().find("</head>")]


# ═══════════════════════════════════════════════════════════════════════════
# Die Muster, WOERTLICH aus den Riegeln uebernommen
# ═══════════════════════════════════════════════════════════════════════════

# D21  tests/test_projekt_cache_v927.py Z264
M_ODB = r'ODB\.(save|load|get|set)\(\s*"%s'
M_ODB_ZAEHLER = r'ODB\.(?:saveProj|loadProj)\(\s*"%s'
ODB_PRAEFIXE = ("docs_", "folders_", "fotos_", "bt_")

# D22  tests/test_schrift_und_tokens_v933.py Z67
M_GELADEN = r"(?:src:\s*)?url\(['\"]?(https?://[^'\")]+)"
M_FONTFACE = r"@font-face\{[^}]*src:url\('([^']+)'"

# D28  tests/test_zulagen_saetze_v768.py Z94
M_TAGGELD = r"'([^']*Taggeld[^']*)'|\"([^\"]*Taggeld[^\"]*)\""

# D29-D33  tests/test_zusammengesetzte_knopfnamen_v960.py Z125 / Z148
M_KNOPF_V960 = r"createElement\('button'\s*,"
M_CLASS_V960 = r'className:\s*"([\w-]+)"'

# D05  tests/test_d9_seitenueberschriften_v956.py Z145
M_UEBERSCHRIFT = r"""(?:createElement|(?<![A-Za-z0-9_$.])h)\(\s*['"](h[123])['"]"""


def _zeile(n, t, *rest):
    print("   %-58s %s" % (n, t), *rest)


def _probe(name, muster, text, erwartet_treffer, regex_flags=0):
    """Ein Koeder: MUSS (erwartet=True) bzw. darf NICHT (False) treffen."""
    n = len(re.findall(muster, text, regex_flags))
    ok = (n > 0) == erwartet_treffer
    _zeile(name, "%s  n=%d  (erwartet %s)"
           % ("OK " if ok else "LUECKE", n, "Treffer" if erwartet_treffer else "kein Treffer"))
    return ok


# ═══════════════════════════════════════════════════════════════════════════

def d21(roh):
    print("")
    print("D21  tests/test_projekt_cache_v927.py::"
          "test_die_projektbezogenen_listen_gehen_ueber_saveProj_und_loadProj")
    print("     Grundgesamtheit: ODB.save/load/get/set mit zusammengesetztem Namen")
    gesamt = 0
    for p in ODB_PRAEFIXE:
        n = len(re.findall(M_ODB % re.escape(p), roh))
        z = len(re.findall(M_ODB_ZAEHLER % re.escape(p), roh))
        _zeile("  %-10s verdaechtig=%d   saveProj/loadProj=%d" % (p, n, z), "")
        gesamt += n
    print("     ==> tatsaechliche Groesse der gesuchten Menge: %d" % gesamt)
    print("     KOEDER je Schreibweise:")
    ok = []
    ok.append(_probe('ODB.save("docs_x") - doppelte Anfuehrung',
                     M_ODB % "docs_", 'ODB.save("docs_x",1);', True))
    ok.append(_probe("ODB.save('docs_x') - EINFACHE Anfuehrung",
                     M_ODB % "docs_", "ODB.save('docs_x',1);", True))
    ok.append(_probe("ODB.save( docs_x ) - Leerraum nach der Klammer",
                     M_ODB % "docs_", 'ODB.save(  "docs_x",1);', True))
    ok.append(_probe("GEGENPROBE ODB.saveProj(\"docs_\") darf NICHT treffen",
                     M_ODB % "docs_", 'ODB.saveProj("docs_a",1);', False))
    ok.append(_probe('GEGENPROBE ODB.save("andere_") darf NICHT treffen',
                     M_ODB % "docs_", 'ODB.save("andere_x",1);', False))
    return gesamt, ok


def d22(roh):
    print("")
    print("D22  tests/test_schrift_und_tokens_v933.py::"
          "test_die_schrift_kommt_aus_dem_repo_und_nicht_von_google")
    kopf = _kopf(roh)
    print("     Grundgesamtheit: absolute url(...) im <head>  (Kopf: %d Zeichen)"
          % len(kopf))
    n_abs = len(re.findall(M_GELADEN, kopf))
    n_url = len(re.findall(r"url\(", kopf))
    n_ff = len(re.findall(M_FONTFACE, kopf))
    print("     url( im Kopf: %d   davon absolut (http/https): %d   "
          "@font-face-Quellen: %d" % (n_url, n_abs, n_ff))
    g = len(re.findall(r"fonts\.(?:gstatic|googleapis)\.com", kopf))
    print("     Nennungen von fonts.gstatic/googleapis im Kopf (Prosa): %d" % g)
    print("     KOEDER je Schreibweise:")
    ok = []
    ok.append(_probe("url('https://fonts.gstatic.com/..') einfach",
                     M_GELADEN, "src:url('https://fonts.gstatic.com/a.woff2')", True))
    ok.append(_probe('url("https://fonts.googleapis.com/..") doppelt',
                     M_GELADEN, 'src:url("https://fonts.googleapis.com/css")', True))
    ok.append(_probe("url(https://fonts.gstatic.com/..) ohne Anfuehrung",
                     M_GELADEN, "url(https://fonts.gstatic.com/a.woff2)", True))
    ok.append(_probe("GEGENPROBE url('./fonts/a.woff2') darf NICHT treffen",
                     M_GELADEN, "src:url('./fonts/a.woff2')", False))
    ok.append(_probe("GEGENPROBE Prosa-Nennung ohne url( darf NICHT treffen",
                     M_GELADEN, "/* nicht von fonts.gstatic.com laden */", False))
    print("     ZWEITE FORM, die das Muster NICHT kennt (Messung, kein Koeder):")
    for name, txt in (("@import 'https://fonts.googleapis.com/..'",
                       "@import 'https://fonts.googleapis.com/css2?family=X';"),
                      ('<link href="https://fonts.gstatic.com/..">',
                       '<link rel=stylesheet href="https://fonts.gstatic.com/x.css">')):
        n = len(re.findall(M_GELADEN, txt))
        _zeile("  " + name, "n=%d  %s" % (n, "gesehen" if n else "NICHT GESEHEN"))
    return n_abs, ok


def d28(roh):
    print("")
    print("D28  tests/test_zulagen_saetze_v768.py::test_keine_taggeld_anzeige_mehr")
    zeilen = roh.split("\n")
    gepruefte = 0
    treffer = 0
    for z in zeilen:
        r = z.strip()
        if "const APP_VERSION=" in z or r.startswith("/*") or r.startswith("*") \
                or r.startswith("//"):
            continue
        gepruefte += 1
        treffer += len(re.findall(M_TAGGELD, z))
    print("     Grundgesamtheit: %d Zeilen, davon %d geprueft "
          "(Kommentarzeilen uebersprungen)" % (len(zeilen), gepruefte))
    print("     Wort 'Taggeld' im GANZEN Text: %d   davon in Anzeige-Zeichenketten: %d"
          % (len(re.findall("Taggeld", roh)), treffer))
    print("     KOEDER je Schreibweise:")
    ok = []
    ok.append(_probe("'Taggeld alt' einfache Anfuehrung",
                     M_TAGGELD, "const x='Taggeld alt';", True))
    ok.append(_probe('"Taggeld alt" doppelte Anfuehrung',
                     M_TAGGELD, 'const x="Taggeld alt";', True))
    ok.append(_probe("GEGENPROBE 'taggeldAb6h' (klein) darf NICHT treffen",
                     M_TAGGELD, "const x={taggeldAb6h:1};", False))
    print("     ZWEITE FORM, die das Muster NICHT kennt (Messung, kein Koeder):")
    for name, txt in (("Vorlagenliteral `Taggeld alt`", "const x=`Taggeld alt`;"),
                      ("Verkettung 'Tag'+'geld'", "const x='Tag'+'geld';")):
        n = len(re.findall(M_TAGGELD, txt))
        _zeile("  " + name, "n=%d  %s" % (n, "gesehen" if n else "NICHT GESEHEN"))
    bt = len(re.findall(r"`[^`]*Taggeld[^`]*`", roh))
    print("     Vorlagenliterale mit 'Taggeld' im heutigen Bestand: %d" % bt)
    return treffer, ok


def d29(roh):
    print("")
    print("D29-D33  tests/test_zusammengesetzte_knopfnamen_v960.py Z125 / Z148")
    print("     Grundgesamtheit: button-Elemente im Code")
    eigene = len(re.findall(M_KNOPF_V960, roh))
    ok_e, gef, erw = code_scan.eichen_knoepfe()
    amtlich = code_scan.knopf_stellen(roh)
    print("     Muster des Riegels  createElement\\('button'\\s*, : %d" % eigene)
    print("     code_scan.knopf_stellen (geeicht %s, %d/%d Formen): %d"
          % ("OK" if ok_e else "GESCHEITERT", gef, erw, len(amtlich)))
    print("     ==> der Riegel sieht %d von %d Knoepfen (%.1f %%)"
          % (eigene, len(amtlich),
             100.0 * eigene / len(amtlich) if amtlich else 0.0))
    print("     KOEDER je Schreibweise fuer das Knopf-Muster des Riegels:")
    ok = []
    ok.append(_probe("React.createElement('button',", M_KNOPF_V960,
                     "React.createElement('button', {a:1})", True))
    ok.append(_probe('React.createElement("button",', M_KNOPF_V960,
                     'React.createElement("button", {a:1})', True))
    ok.append(_probe("h('button',  (Kuerzel)", M_KNOPF_V960,
                     "h('button', {a:1})", True))
    ok.append(_probe('h("button",  (Kuerzel, doppelt)', M_KNOPF_V960,
                     'h("button", {a:1})', True))
    print("     KOEDER je Schreibweise fuer das className-Muster des Riegels:")
    ok.append(_probe('className:"btn"  doppelt', M_CLASS_V960,
                     'className:"btn"', True))
    ok.append(_probe("className:'btn'  EINFACH", M_CLASS_V960,
                     "className:'btn'", True))
    ok.append(_probe("GEGENPROBE classNameX:\"btn\" darf NICHT treffen",
                     M_CLASS_V960, 'classNameX:"btn"', False))
    print("     Bestand: className mit EINFACHEN Anfuehrungszeichen im Code:")
    einfach = code_scan.nur_code_stellen(roh, r"className:\s*'", regex=True)
    doppelt = code_scan.nur_code_stellen(roh, r'className:\s*"', regex=True)
    print("        className:'...' = %d      className:\"...\" = %d"
          % (len(einfach), len(doppelt)))
    return eigene, ok


def d05(roh):
    print("")
    print("D05  tests/test_d9_seitenueberschriften_v956.py::"
          "test_die_vier_offenen_ansichten_haben_keine_erfundene_ueberschrift")
    n = len(re.findall(M_UEBERSCHRIFT, roh))
    print("     h1/h2/h3-Elemente im GANZEN Text (beide Erzeuger, beide "
          "Anfuehrungszeichen): %d" % n)
    print("     KOEDER je Schreibweise:")
    ok = []
    ok.append(_probe("React.createElement('h2',", M_UEBERSCHRIFT,
                     "React.createElement('h2', 'x')", True))
    ok.append(_probe('React.createElement("h2",', M_UEBERSCHRIFT,
                     'React.createElement("h2", "x")', True))
    ok.append(_probe("h('h2',  (Kuerzel)", M_UEBERSCHRIFT, "h('h2', 'x')", True))
    ok.append(_probe('h("h2",  (Kuerzel, doppelt)', M_UEBERSCHRIFT, 'h("h2","x")', True))
    ok.append(_probe("GEGENPROBE search('h2') darf NICHT treffen",
                     M_UEBERSCHRIFT, "search('h2')", False))
    ok.append(_probe("GEGENPROBE obj.h('h2') darf NICHT treffen",
                     M_UEBERSCHRIFT, "obj.h('h2')", False))
    return n, ok


def selbstprobe():
    """Eichung des Messgeraets selbst - an einem GEBAUTEN Text, nicht am Bestand."""
    print("SELBSTPROBE DES MESSGERAETS")
    ok = []
    ok.append(_probe("code_scan.eichen_elemente", r"x",
                     "x" if code_scan.eichen_elemente()[0] else "", True))
    ok.append(_probe("code_scan.eichen_knoepfe", r"x",
                     "x" if code_scan.eichen_knoepfe()[0] else "", True))
    o, g, e = code_scan.eichen(_index())
    _zeile("code_scan.eichen (Zeichenketten) am Bestand",
           "%s  %d/%d" % ("OK " if o else "GESCHEITERT", g, e))
    ok.append(o)
    return ok


def main(argv):
    roh = _index()
    print("index.html: %d Zeichen, %d Zeilen" % (len(roh), roh.count("\n") + 1))
    print("=" * 78)
    alle = selbstprobe()
    if "--selbstprobe" in argv:
        return 0 if all(alle) else 1
    print("=" * 78)
    for fn in (d05, d21, d22, d28, d29):
        _, ok = fn(roh)
        alle += ok
    print("")
    print("=" * 78)
    print("Koeder/Gegenproben gesamt: %d, davon richtig: %d, LUECKEN: %d"
          % (len(alle), sum(1 for x in alle if x), sum(1 for x in alle if not x)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
