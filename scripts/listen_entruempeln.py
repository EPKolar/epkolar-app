# -*- coding: utf-8 -*-
"""Aus den Listen soll nur noch stehen, was OFFEN ist.

Auftrag von Sebastian am 30.09.2026: "alles was gruen ist raus".

🔴 EIN NAIVER FILTER HAETTE OFFENES GELOESCHT. Beim Messen kamen sofort zwei
Faelle heraus, die "erledigt" enthalten und trotzdem offen sind:

  * `## ~~24. Drei CSS-Regeln pflegen Bauteile, die es nicht gibt~~ —
    **bleibt offen**` - durchgestrichen UND offen;
  * `## Was in der Schriftfrage NICHT erledigt ist` - das Wort steht in der
    Verneinung.

Deshalb wird hier nichts nach Merkmalen geraten: die zu entfernenden
Abschnitte stehen NAMENTLICH in zwei Tafeln, und das Werkzeug bricht ab,
wenn eine davon nicht genau einmal gefunden wird.

🔴 UND ZWEI ARTEN VON GRUEN SIND NICHT DASSELBE. Ein kurierter Befund kann
weg - er steht jetzt im Code und in einem Riegel. Ein Abschnitt
"nachgemessen und in Ordnung - nicht zweimal pruefen" darf NICHT weg: er
verhindert, dass jemand dieselbe Messung noch einmal faehrt. Solche
Abschnitte werden ans ENDE verschoben, unter eine eigene Ueberschrift, statt
geloescht zu werden.

Was entfernt wird, bleibt in der git-Historie. Der Kopf jeder Datei sagt,
unter welchem Stand man es findet.
"""
import io
import os
import re
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Was RAUS kommt, namentlich ------------------------------------------
RAUS = {
    "docs/ENTSCHEIDUNGEN-OFFEN.md": [
        "### ~~15. Das Klammertor beurteilt",
        "### ~~17. Sieben Skripte kommen von einer fremden CDN",
        "### ~~27. Die Kiosk-Wochenplantafel hat denselben Austrittsfehler",
        "## ~~18. App-Hülle auf 12 px~~",
        "## ~~19. `svg text` in den Diagrammen~~",
        "## ~~23. Das Ringdiagramm verliert Einträge~~",
        # 🔴 DIESE DREI HAETTE ICH FAST STEHENLASSEN. Die Fragen 18, 19 und 23
        # stehen ZWEIMAL in der Datei: einmal als urspruengliche Frage, und
        # einmal weiter unten als Nachtrag, der ihre Erledigung festhaelt. Ein
        # erster Lauf entfernte nur die Nachtraege - danach stand die Frage
        # ohne jede Antwort da, also SCHLECHTER als vorher. Gefunden beim
        # Nachlesen des Ergebnisses, nicht beim Planen.
        "### 18. Soll die App-Hülle auf 12 px gehoben werden?",
        "### 19. Soll `svg text` in den Diagrammen auf 12 px?",
        "### 23. 🔴 Das Ringdiagramm verliert Einträge",
    ],
    "docs/befunde/BUGHUNT_2026-09-30.md": [
        "### 🔴🔴 Z6 — Eine Stunde Anwesenheit",
        "### 🔴🔴 D1 — Eine fehlgeschlagene Zeitübernahme",
        "### 🔴 D2 — Der Wächter gegen den stillen Schreibfehler",
        "### 🔴 D3 — Ein Mangelfoto kann lautlos verschwinden",
        "### 🔴 Z1 — Am Jahreswechsel bucht die Zeiterfassung",
        "### 🔴 Z3 — Die Team-Zeitachse zeigt 2027",
        "### 🔴 B1 — Krankmeldungen werden über den NAMEN",
        "### 🔴 B2 — Jede Leseabfrage hört bei 5000 Zeilen auf",
        "### 🔴 B3 — Der Artikelkatalog fordert 10 000 Zeilen",
    ],
}

# --- Was NACH HINTEN wandert, statt zu verschwinden -----------------------
ANS_ENDE = {
    "docs/befunde/BUGHUNT_2026-09-30.md": [
        "### ✅ Neun Klassen nachgemessen und in Ordnung",
        "### ✅ 28 Stellen nachgemessen und in Ordnung",
        "### ✅ Der leere Zustand ist sauber",
    ],
}

ENDE_KOPF = (
    "## Nachschlagen — hier ist nichts zu tun\n\n"
    "Diese Abschnitte stehen absichtlich noch da, obwohl sie „grün\" sind:\n"
    "sie halten fest, was **nachgemessen und in Ordnung** war. Wer sie\n"
    "löscht, lädt dazu ein, dieselbe Messung noch einmal zu fahren.\n")

# Abschnitte, die trotz "erledigt" im Text OFFEN sind - sie duerfen NIE in
# eine der Tafeln oben geraten. Der Riegel unten prueft das.
NIEMALS = [
    "## ~~24. Drei CSS-Regeln pflegen Bauteile, die es nicht gibt~~",
    "## Was in der Schriftfrage NICHT erledigt ist",
]


def _ebene(zeile):
    m = re.match(r"^(#{1,6}) ", zeile)
    return len(m.group(1)) if m else 0


def abschnitt(zeilen, start):
    """Von der Ueberschrift bis zur naechsten gleich- oder hoeherrangigen."""
    e = _ebene(zeilen[start])
    for i in range(start + 1, len(zeilen)):
        k = _ebene(zeilen[i])
        if k and k <= e:
            return i
    return len(zeilen)


def eichen():
    """🔴 Selbstprobe: erkennt das Werkzeug Abschnittsgrenzen richtig?"""
    z = ["# A", "text", "### B", "b1", "#### C", "c1", "### D", "d1", "## E"]
    faelle = [
        ("K1 ### endet vor naechstem ###", abschnitt(z, 2), 6),
        ("K2 #### endet vor ###", abschnitt(z, 4), 6),
        ("K3 letzter ### endet vor ##", abschnitt(z, 6), 8),
        ("K4 # reicht bis zum Ende", abschnitt(["# A", "x", "y"], 0), 3),
        ("G1 kein Kopf -> Ebene 0", _ebene("kein Kopf"), 0),
        ("G2 Raute ohne Leerzeichen zaehlt nicht", _ebene("#kein Kopf"), 0),
    ]
    schief = [(n, i, s) for n, i, s in faelle if i != s]
    for n, i, s in schief:
        print("   ROT   %-38s erwartet %r, gemessen %r" % (n, s, i))
    if schief:
        print("\n%d von %d Proben falsch - dieses Werkzeug MISST NICHT."
              % (len(schief), len(faelle)))
        return 2
    print("   Eichung: %d Proben - vier Koeder, zwei Gegenproben" % len(faelle))
    print("   alle %d richtig\n" % len(faelle))
    return 0


def kopf_sha():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=WURZEL, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return (r.stdout or "").strip() or "unbekannt"
    except Exception:
        return "unbekannt"


def bearbeite(rel, sha, trocken):
    pfad = os.path.join(WURZEL, rel)
    t = io.open(pfad, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in t else "\n"
    zeilen = t.split(nl)
    vorher = len(zeilen)

    # 🔴 Sperre: nichts entfernen, was ausdruecklich offen ist.
    for n in NIEMALS:
        for tafel in (RAUS.get(rel, []), ANS_ENDE.get(rel, [])):
            for e in tafel:
                if n.startswith(e) or e.startswith(n):
                    print("   \U0001F534 %r steht in einer Tafel, ist aber "
                          "als OFFEN gekennzeichnet." % n)
                    return None

    def finde(praefix):
        tr = [i for i, z in enumerate(zeilen) if z.startswith(praefix)]
        if len(tr) != 1:
            print("   \U0001F534 %r kommt %dx vor - erwartet genau einmal."
                  % (praefix[:60], len(tr)))
            return None
        return tr[0]

    entfernen, verschieben = [], []
    for p in RAUS.get(rel, []):
        i = finde(p)
        if i is None:
            return None
        entfernen.append((i, abschnitt(zeilen, i)))
    for p in ANS_ENDE.get(rel, []):
        i = finde(p)
        if i is None:
            return None
        verschieben.append((i, abschnitt(zeilen, i)))

    bewahrt = []
    for a, b in verschieben:
        bewahrt.extend(zeilen[a:b])

    weg = set()
    for a, b in entfernen + verschieben:
        weg.update(range(a, b))
    neu = [z for i, z in enumerate(zeilen) if i not in weg]

    hinweis = [
        "",
        "> **Entrümpelt am 30.09.2026** — hier steht nur noch, was OFFEN ist.",
        "> Die %d erledigten Abschnitte sind entfernt; sie stehen unverändert"
        % len(entfernen),
        "> in der git-Historie, zuletzt vollständig unter `%s`." % sha,
        "",
    ]
    # Hinweis direkt unter die Titelzeile.
    for i, z in enumerate(neu):
        if _ebene(z) == 1:
            neu = neu[:i + 1] + hinweis + neu[i + 1:]
            break

    if bewahrt:
        neu += ["", "---", ""] + ENDE_KOPF.split("\n") + [""] + bewahrt

    # Die Titelzeile zaehlt mit - eine Ueberschrift, die eine veraltete Zahl
    # nennt, ist selbst eine falsche Aussage.
    offen = sum(1 for z in neu if re.match(r"^#{2,4} (?:🔴 )?\d+[a-z]?\. ", z))
    for i, z in enumerate(neu):
        if _ebene(z) == 1 and "Offene Entscheidungen" in z:
            neu[i] = ("# Offene Entscheidungen — %d offene Fragen "
                      "(Stand 30.09.2026)" % offen)
            break

    print("   %-40s %4d -> %4d Zeilen  (%d entfernt, %d ans Ende)"
          % (rel, vorher, len(neu), len(entfernen), len(verschieben)))
    if not trocken:
        io.open(pfad, "w", encoding="utf-8", newline="").write(nl.join(neu))
    return len(neu)


def main(argv):
    if eichen() != 0:
        return 2
    if "--eichen" in argv:
        return 0
    trocken = "--trocken" in argv
    sha = kopf_sha()
    print("Stand vor dem Entruempeln: %s%s\n"
          % (sha, "   (TROCKENLAUF)" if trocken else ""))
    for rel in RAUS:
        if bearbeite(rel, sha, trocken) is None:
            print("\n\U0001F534 ABBRUCH - nichts geschrieben.")
            return 2
    print("\nFertig.")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
