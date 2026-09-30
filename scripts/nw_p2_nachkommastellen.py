# -*- coding: utf-8 -*-
"""P2: Rundung 1 -> 2 Nachkommastellen - wo bleibt der Rest des Blattes?

FRAGE
─────
v3.9.992 stellte VIER Stellen der Stundenbestaetigung von `_n(x,1)` auf
`_n(x,2)`, damit die gedruckten Tageszellen zur Summe passen ("ein
unterschriebenes Blatt, das nicht aufgeht").

Betroffen ist aber nicht die geaenderte Stelle, sondern JEDE ANDERE Zahl
DESSELBEN Blattes: bleibt eine davon auf einer Stelle, geht das Blatt an
dieser Zeile weiterhin nicht auf - und sieht jetzt zusaetzlich uneinheitlich
aus.

VERFAHREN
─────────
Das Blatt ist ein Vorlagenliteral (Template-Literal). Gemessen wird der
Rumpf von `exportWochenStz` - Anfang aus der Codemaske gesucht, Ende ueber
klammergefuehrtes Zaehlen (nur dort, wo die Maske Code sagt). Darin wird
JEDER Aufruf `_n(...,N)` gezaehlt und nach N geordnet.

Die Kur-Kommentare ZITIEREN die alte Form ("1 -> 2 Nachkommastellen"),
darum laeuft die Suche ueber die Codemaske.

KOEDER
──────
--koeder setzt in einer KOPIE des Textes eine der `_n(x,2)`-Stellen auf
`_n(x,1)` zurueck. Steigt die Zahl der 1-Stellen-Fundstellen dabei nicht um
genau eins, misst dieses Skript nicht, was es behauptet.
"""
import re
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von


def rumpf(text, maske, name):
    m = None
    for mm in re.finditer(r"(const|function|var|let)\s+" + re.escape(name) + r"\s*[=(]", text):
        if maske[mm.start()]:
            m = mm
            break
    if not m:
        return None, None
    i = text.index("{", m.end() - 1)
    tiefe = 0
    n = len(text)
    j = i
    while j < n:
        if maske[j]:
            if text[j] == "{":
                tiefe += 1
            elif text[j] == "}":
                tiefe -= 1
                if tiefe == 0:
                    return i, j
        j += 1
    return i, n


def zaehle(text, maske, a, b, titel):
    print("=== %s  (Zeile %d bis %d, %d Zeichen) ==="
          % (titel, zeile_von(text, a), zeile_von(text, b), b - a))
    nach = {}
    for mm in re.finditer(r"_n\(", text[a:b]):
        p = a + mm.start()
        if not maske[p]:
            continue
        # Stellenangabe: letztes Argument vor der schliessenden Klammer
        tiefe = 0
        j = text.index("(", p)
        k = j
        while k < b:
            if maske[k]:
                if text[k] == "(":
                    tiefe += 1
                elif text[k] == ")":
                    tiefe -= 1
                    if tiefe == 0:
                        break
            k += 1
        arg = text[j + 1:k]
        mz = re.search(r",\s*(\d+)\s*$", arg)
        stellen = mz.group(1) if mz else "-"
        nach.setdefault(stellen, []).append((zeile_von(text, p), " ".join(arg.split())[:90]))
    for s in sorted(nach):
        print("  Nachkommastellen=%s : %d Stellen" % (s, len(nach[s])))
    for s in sorted(nach):
        for z, a2 in nach[s]:
            print("    N=%s  Z%-7d _n(%s)" % (s, z, a2))
    return nach


def main():
    text = lies()
    maske = codemaske(text)
    if "--koeder" in sys.argv:
        # KOEDER: eine der kurierten Stellen zurueckdrehen - in der KOPIE.
        alt = '${/* v3.9.992: 1 -> 2 Stellen, damit die Summe zu den Tageszellen darueber passt. */_n(weekTotal,2)}'
        neu = '${/* v3.9.992: 1 -> 2 Stellen, damit die Summe zu den Tageszellen darueber passt. */_n(weekTotal,1)}'
        if alt not in text:
            print("KOEDER GESCHEITERT: Ankertext nicht gefunden - die Messung sagt nichts.")
            return 2
        text = text.replace(alt, neu, 1)
        maske = codemaske(text)
        print("KOEDER AKTIV: _n(weekTotal,2) kuenstlich auf 1 zurueckgedreht.\n")

    # Die Funktionsgrenze ueber Klammerzaehlung TRAEGT HIER NICHT: code_scan
    # kennt keine Regex-Literale, und ein `{` in einem solchen laesst den
    # Rumpf bis zum Dateiende laufen (gemessen: 25676 bis 30431). Deshalb
    # wird das GEDRUCKTE BLATT ueber seine eigenen Textmarken abgegrenzt -
    # die Vorlagenliterale `const html=` bis `</body></html>`;
    bereiche = [
        ("Wochen-Stundenbestaetigung (exportWochenStz, das Blatt aus P2)",
         "const exportWochenStz", "</body></html>`;"),
        ("Tages-Stundenbestaetigung (exportTagesStz, der Zwilling)",
         "const exportTagesStz", "</body></html>`;"),
    ]
    for titel, anf, ende in bereiche:
        a = text.index(anf)
        b = text.index(ende, a) + len(ende)
        zaehle(text, maske, a, b, titel)
        print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
