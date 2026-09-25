# -*- coding: utf-8 -*-
"""Archivo als woff2 ins Repo holen - reproduzierbar, nicht von Hand.

WARUM SELBST HOSTEN (CSP-Grund, nicht Geschmack)
────────────────────────────────────────────────
Die Content-Security-Policy dieser App erlaubt

    style-src  'self' 'unsafe-inline' cdnjs
    font-src   'self' cdnjs

`fonts.googleapis.com` und `fonts.gstatic.com` stehen dort NICHT. Ein
Google-Fonts-Link scheitert also STILL: kein Fehler im Bild, keine Schrift.
Die Dateien muessen im Repo liegen, sonst faellt die App auf der Baustelle
auf die Systemschrift zurueck - und offline sowieso.

LIZENZ
──────
Archivo steht unter der SIL Open Font License 1.1. Selbsthosten ist
ausdruecklich erlaubt; die Lizenz wird als fonts/OFL.txt mitgelegt.

WELCHE SCHNITTE
───────────────
400 Regular, 500 Medium, 600 SemiBold, 700 Bold, je latin und latin-ext.
Vietnamese wird NICHT geholt - die App ist deutschsprachig, und jede
ungenutzte Datei ist Ladezeit auf einer Baustellenverbindung. latin-ext
bleibt, weil es die osteuropaeischen Namen im Mitarbeiterstamm traegt.

AUFRUF
──────
    python scripts/schrift_holen.py            holt und schreibt fonts/
    python scripts/schrift_holen.py --pruefen  nur nachsehen, nichts laden
"""
import hashlib
import io
import os
import re
import sys
import urllib.request

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(WURZEL, "fonts")

CSS_URL = ("https://fonts.googleapis.com/css2?family=Archivo:"
           "wght@400;500;600;700&display=swap")
# Ohne modernen User-Agent liefert Google TTF statt WOFF2.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

GEWOLLT = {"latin", "latin-ext"}


def _hol(url, kopf=None):
    req = urllib.request.Request(url, headers=kopf or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def zerlege(css):
    """(subset, gewicht, url) je @font-face - der Reihe nach, wie im CSS."""
    aus = []
    for block in re.finditer(
            r"/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}", css, re.S):
        subset, rumpf = block.group(1), block.group(2)
        g = re.search(r"font-weight:\s*(\d+)", rumpf)
        u = re.search(r"url\((https://[^)]+\.woff2)\)", rumpf)
        r = re.search(r"unicode-range:\s*([^;]+);", rumpf)
        if g and u:
            aus.append((subset, int(g.group(1)), u.group(1),
                        (r.group(1).strip() if r else "")))
    return aus


def main(argv):
    css = _hol(CSS_URL).decode("utf-8")
    alle = zerlege(css)
    if not alle:
        raise SystemExit(
            "Aus dem CSS liess sich kein einziger @font-face lesen. Das ist "
            "kein gruenes Ergebnis, sondern eine ausgefallene Messung.")
    noetig = [x for x in alle if x[0] in GEWOLLT]
    print("%d @font-face im CSS, %d davon gebraucht (%s)"
          % (len(alle), len(noetig), ", ".join(sorted(GEWOLLT))))
    erwartet = len(GEWOLLT) * 4
    if len(noetig) != erwartet:
        raise SystemExit("Erwartet %d Schnitte, gefunden %d - NICHTS geladen."
                         % (erwartet, len(noetig)))
    if "--pruefen" in argv:
        for s, g, u, _ur in noetig:
            print("  %-10s %d  %s" % (s, g, u[-40:]))
        return 0

    os.makedirs(ZIEL, exist_ok=True)

    # GEMESSEN, NICHT ANGENOMMEN: Google liefert Archivo als VARIABLE Schrift.
    # Alle vier Gewichte zeigen auf denselben Inhalt (gleiche md5), nur unter
    # vier verschiedenen URLs. Wer daraus vier Dateien macht, laesst dieselben
    # 35 kB VIERMAL ueber eine Baustellenverbindung laden - und merkt es nie,
    # weil optisch alles stimmt. Geholt wird deshalb je Subset EINE Datei mit
    # der Gewichtsspanne 100 900; der Browser schneidet 400/500/600/700
    # daraus. Erkannt wird das an der Inhaltssumme, nicht am Dateinamen.
    inhalte = {}
    stuecke = []
    for subset, gewicht, url, ur in sorted(noetig, key=lambda x: (x[0], x[1])):
        roh = _hol(url)
        if len(roh) < 4000 or roh[:4] != b"wOF2":
            raise SystemExit("%s/%d ist kein WOFF2 (%d Bytes) - NICHTS "
                             "geschrieben." % (subset, gewicht, len(roh)))
        summe = hashlib.md5(roh).hexdigest()
        inhalte.setdefault(subset, {}).setdefault(summe, []).append((gewicht, roh, ur))

    for subset in sorted(inhalte):
        fassungen = inhalte[subset]
        if len(fassungen) == 1:
            summe, eintraege = list(fassungen.items())[0]
            gewichte = sorted(g for g, _r, _u in eintraege)
            _g, roh, ur = eintraege[0]
            name = "archivo-var-%s.woff2" % subset
            spanne = "100 900"
            print("  %-28s %6d Bytes  %s  EINE Datei fuer %s"
                  % (name, len(roh), summe[:12],
                     "/".join(str(g) for g in gewichte)))
        else:
            # Statische Schnitte - dann doch je Gewicht eine Datei.
            for summe, eintraege in fassungen.items():
                g, roh, ur = eintraege[0]
                name = "archivo-%d-%s.woff2" % (g, subset)
                spanne = str(g)
                with io.open(os.path.join(ZIEL, name), "wb") as f:
                    f.write(roh)
                print("  %-28s %6d Bytes  %s" % (name, len(roh), summe[:12]))
                stuecke.append(
                    "@font-face{font-family:'Archivo';font-style:normal;"
                    "font-weight:%s;font-display:swap;"
                    "src:url('./fonts/%s') format('woff2');unicode-range:%s}"
                    % (spanne, name, ur))
            continue
        with io.open(os.path.join(ZIEL, name), "wb") as f:
            f.write(roh)
        stuecke.append(
            "@font-face{font-family:'Archivo';font-style:normal;"
            "font-weight:%s;font-display:swap;"
            "src:url('./fonts/%s') format('woff2');unicode-range:%s}"
            % (spanne, name, ur))

    css_datei = os.path.join(ZIEL, "archivo.css.txt")
    with io.open(css_datei, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(stuecke) + "\n")
    print("\n%d @font-face-Regeln geschrieben: %s" % (len(stuecke), css_datei))
    print("Er gehoert in den bestehenden <style> im <head> von index.html.")

    lizenz = os.path.join(ZIEL, "OFL.txt")
    if not os.path.exists(lizenz):
        try:
            txt = _hol("https://raw.githubusercontent.com/google/fonts/main/"
                       "ofl/archivo/OFL.txt")
            with io.open(lizenz, "wb") as f:
                f.write(txt)
            print("Lizenz geholt: fonts/OFL.txt (%d Bytes)" % len(txt))
        except Exception as e:                                # noqa: BLE001
            print("Lizenztext nicht geholt (%s) - MUSS nachgetragen werden, "
                  "die OFL verlangt die Beilage." % e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
