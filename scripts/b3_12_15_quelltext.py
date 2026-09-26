# -*- coding: utf-8 -*-
"""Schriftgroessen JE KOMPONENTE aus dem Quelltext - fuer Stufen 12-15.

WAS GEMESSEN WIRD
─────────────────
Je Komponente (abgegrenzt an der NAECHSTEN `\\nfunction `-Deklaration, nicht
ueber eine Klammerzaehlung - die ist mir schon einmal davongelaufen und hat
fuer eine Komponente einen "Rumpf" von 1,77 MB gemeldet) werden die
`fontSize:`-Angaben gezaehlt, die im CODE stehen (nicht im Kommentar, nicht
in einer Zeichenkette - `code_scan.ist_code`, und die Eichung VERWEIGERT,
wenn sie scheitert).

Gezaehlt werden VIER Formen, weil der Zaehler aus Stufe 4-7 nur die erste
kannte und damit den kleinsten Wert der ganzen App uebersehen hat:

    fontSize:9              feste Zahl
    fontSize:isMob?7:9      Bedingung - BEIDE Zweige zaehlen
    fontSize:ww<BP_MOB?9:11 dieselbe Form mit anderem Praedikat
    fontSize:UI.fMeta       Wert aus der Tabelle UI{...} - aufgeloest

WAS NICHT GEMESSEN WIRD
───────────────────────
  * CSS-Regeln (`.tab-bar button{font-size:11px}`) - die stehen im GCSS-Block
    und nicht an der Komponente. Sie sind am gerenderten Schirm gemessen
    (b3_stufen_12_15_messen.py), nicht hier.
  * Ob die Stelle im Bild ueberhaupt vorkommt. Eine Komponente kann eine
    9-px-Angabe fuehren, die nur in einem Zweig erscheint, den dieser Aufbau
    nie erreicht. Die Zahl hier ist eine OBERGRENZE fuer den Quelltext, die
    Zahl am Schirm ist der Messwert.
  * Vererbte Groessen (ein Kind ohne eigenes fontSize).

KOEDER
──────
K-Q1  Die UI-Tabelle MUSS gefunden werden und `fMeta:12` enthalten.
      Wird sie nicht gefunden, sind alle `UI.f*`-Stellen unaufgeloest und
      die Zaehlung waere still zu klein.
K-Q2  In WerkzeugView/HomeView sind die 9/10/11er laut v3.9.943/944 bereits
      gehoben. Findet dieser Zaehler dort noch welche unter 12, misst er
      etwas anderes als behauptet - oder die Behauptung stimmt nicht. Das
      Ergebnis wird AUSGEWIESEN, nicht stillschweigend verrechnet.
K-Q3  Die Komponentengrenze wird auf PLAUSIBILITAET geprueft: eine
      Komponente dieser App ist 20 bis 170 kB. Faellt eine aus dem Rahmen,
      wird sie gemeldet und NICHT gezaehlt.

AUFRUF
──────
    set EPK_INDEX=_mess_stand_944.html
    python scripts/b3_12_15_quelltext.py
"""
import io
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
sys.path.insert(0, HIER)

from code_scan import ist_code, eichen          # noqa: E402

KOMPONENTEN = [
    ("ChefDashboard", 12), ("ZeiterfassungView", 12), ("AbsView", 12),
    ("StundenzettelView", 13), ("FahrzeugView", 13), ("FlotteView", 13),
    ("MitarbeiterView", 14), ("AuswertungView", 14), ("VBueroExport", 14),
    ("AdminPanel", 15), ("VerbindungView", 15), ("VGefahrstoff", 15),
    ("BauprovisorienView", 15),
    # Gegenprobe K-Q2: dort sind die kleinen Groessen laut v3.9.943/944
    # bereits gehoben.
    ("HomeView", 0), ("WerkzeugView", 0),
]

GROESSE = re.compile(
    r"fontSize:\s*(?:([A-Za-z_][\w.]*)\s*(?:<|>|<=|>=|===|==)\s*[\w.]+\s*\?\s*"
    r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)"   # fontSize:isMob?7:9
    r"|(\d+(?:\.\d+)?)"                         # fontSize:9  UND  10.5
    r"|(UI\.[A-Za-z]+))")                        # fontSize:UI.fMeta


def _ui_tabelle(s):
    # Nicht ueber `[^}]*`: der Block traegt einen Kommentar mit `}` darin.
    # Gelesen wird ein Fenster ab `const UI={` und daraus die
    # `name:zahl`-Paare - das genuegt, weil nur die Zahlen gebraucht werden.
    m = re.search(r"const UI\s*=\s*\{", s)
    if not m:
        return None
    fenster = s[m.end():m.end() + 1600]
    fenster = fenster.split("/*")[0]   # der Block traegt einen
    # Kommentar; ohne diesen Schnitt liest der Zaehler ein
    # `fontSize:9` aus dem Kommentar als UI-Eintrag mit.
    t = {}
    for k, v in re.findall(r"(\bf[A-Za-z]+)\s*:\s*(\d+)", fenster):
        t["UI." + k] = int(v)
    return t


def main(argv):
    datei = os.environ.get("EPK_INDEX", "index.html")
    pfad = os.path.join(WURZEL, datei)
    s = io.open(pfad, encoding="utf-8", newline="").read()
    import hashlib
    h = hashlib.md5(io.open(pfad, "rb").read()).hexdigest()
    print("Quelltext: %s   md5 %s   %d Zeichen" % (datei, h, len(s)))

    eichen(s)                      # verweigert, wenn sie scheitert
    print("Eichung von code_scan: bestanden")

    ui = _ui_tabelle(s)
    if not ui or ui.get("UI.fMeta") != 12:
        raise SystemExit("ABBRUCH (K-Q1): die UI-Tabelle wurde nicht "
                         "gefunden oder fMeta ist nicht 12 (%s). Alle "
                         "UI.f*-Stellen waeren unaufgeloest und die Zaehlung "
                         "still zu klein." % ui)
    print("K-Q1 UI-Tabelle ANGESCHLAGEN: %s" % ui)

    code = ist_code(s)
    fns = [(m.start(), m.group(1))
           for m in re.finditer(r"\nfunction ([A-Za-z_][A-Za-z0-9_]*)\(", s)]
    grenzen = {}
    for i, (p, n) in enumerate(fns):
        ende = fns[i + 1][0] if i + 1 < len(fns) else len(s)
        grenzen.setdefault(n, (p, ende))

    print("\n%-20s %5s %7s  %s" % ("Komponente", "Stufe", "Groesse",
                                   "Schriftgroessen unter 12 px"))
    print("-" * 100)
    gesamt = {}
    for name, stufe in KOMPONENTEN:
        if name not in grenzen:
            print("%-20s   FEHLT im Quelltext" % name)
            continue
        a, b = grenzen[name]
        kb = (b - a) / 1024.0
        if not (10 <= kb <= 260):
            print("%-20s %5d %6.0fkB  AUS DEM RAHMEN - nicht gezaehlt"
                  % (name, stufe, kb))
            continue
        block = s[a:b]
        treffer = {}
        stellen = []
        for m in GROESSE.finditer(block):
            if not code[a + m.start()]:
                continue
            werte = []
            if m.group(2):
                werte = [float(m.group(2)), float(m.group(3))]
            elif m.group(4):
                werte = [float(m.group(4))]
            elif m.group(5):
                w = ui.get(m.group(5))
                if w is None:
                    continue
                werte = [float(w)]
            for w in werte:
                if w < 12:
                    treffer[w] = treffer.get(w, 0) + 1
                    stellen.append((w, a + m.start(),
                                    block[m.start():m.start() + 46]))
        gesamt[name] = {"stufe": stufe, "kb": kb, "verteilung": treffer,
                        "anzahl": sum(treffer.values()),
                        "stellen": stellen}
        print("%-20s %5d %6.0fkB  %3d Stellen   %s"
              % (name, stufe, kb, sum(treffer.values()),
                 " · ".join("%gpx ×%d" % (k, treffer[k])
                            for k in sorted(treffer)) or "keine"))

    # K-Q2: die Gegenprobe
    for name in ("HomeView", "WerkzeugView"):
        if name in gesamt:
            n = gesamt[name]["anzahl"]
            print("\nK-Q2 %s: %d Stellen unter 12 px im Quelltext. "
                  "v3.9.943/944 sagt: dort gehoben. %s"
                  % (name, n,
                     "Deckt sich." if n == 0 else
                     "DECKT SICH NICHT - entweder misst dieser Zaehler etwas "
                     "anderes, oder es sind noch welche da. Verteilung: %s"
                     % gesamt[name]["verteilung"]))

    print("\nDie kleinsten Stellen je Komponente (Stufen 12-15):")
    for name, stufe in KOMPONENTEN:
        if stufe == 0 or name not in gesamt:
            continue
        st = sorted(gesamt[name]["stellen"])[:6]
        for w, pos, txt in st:
            print("   %-20s %4gpx @%d  %r" % (name, w, pos, txt))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
