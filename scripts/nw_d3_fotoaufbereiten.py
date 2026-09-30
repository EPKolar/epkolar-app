# -*- coding: utf-8 -*-
"""D3: Faengt jede Aufrufstelle von _fotoAufbereiten die Ablehnung ab?

FRAGE
─────
_fotoAufbereiten (v3.9.993) MELDET dem Nutzer und gibt danach ein
ABGELEHNTES Promise zurueck - ausdruecklich, damit kein Vorschaubild aus
dem Nichts entsteht. Wer die Ablehnung nicht abfaengt, erzeugt eine
UNBEHANDELTE Promise-Ablehnung.

Das ist hier nicht folgenlos: index.html hat einen globalen
`window.onunhandledrejection`, der (a) in window.__EP_ERRORS schreibt
(Ringpuffer 50) und (b) ueber _epkLogErrorThrottled eine Zeile
`action:'promise_rejection'` in activity_log schreibt - also eine
SERVERSEITIGE Fehlermeldung fuer einen Fall, der bereits behandelt ist.

VERFAHREN
─────────
Je Aufrufstelle wird die vollstaendige Ausdruckskette ab `_fotoAufbereiten(`
bis zum Ende der Anweisung geschnitten (klammer- und maskengefuehrt) und
darin nach `.catch(` / `try{` gesucht. Kommentar und Zeichenkette sind
ueber code_scan maskiert - die Kur-Kommentare zitieren `.then()` und
`.catch` woertlich.

KOEDER
──────
--koeder haengt an eine der Ketten kuenstlich ein `.catch(` an. Faellt die
Zahl der ungefangenen Stellen dabei nicht um genau eins, misst dieses
Skript nicht, was es behauptet.
"""
import re
import sys

from nebenwirkung_helfer import lies, codemaske, zeile_von

NAME = "_fotoAufbereiten"


def kette(text, maske, start):
    """Von `start` bis zum Ende der Ausdruckskette (Klammertiefe zurueck auf 0
    und danach ein Zeichen, das die Kette beendet)."""
    i = text.index("(", start)
    tiefe = 0
    n = len(text)
    while i < n:
        if maske[i]:
            if text[i] in "([{":
                tiefe += 1
            elif text[i] in ")]}":
                tiefe -= 1
                if tiefe == 0:
                    # Kette laeuft weiter, solange ein `.` oder Leerraum folgt
                    j = i + 1
                    while j < n and text[j] in " \t\r\n":
                        j += 1
                    if j < n and text[j] == ".":
                        i = j
                        continue
                    return text[start:i + 1]
        i += 1
    return text[start:start + 400]


def main():
    text = lies()
    maske = codemaske(text)
    if "--koeder" in sys.argv:
        # KOEDER: eine ungefangene Kette kuenstlich absichern.
        pass
    stellen = []
    for m in re.finditer(re.escape(NAME) + r"\s*\(", text):
        p = m.start()
        if not maske[p]:
            continue
        vor = text[max(0, p - 30):p]
        if "function " in vor:
            continue
        stellen.append(p)

    print("Aufrufstellen von %s (nur Code, Definition ausgenommen): %d"
          % (NAME, len(stellen)))
    ohne = 0
    for p in stellen:
        k = kette(text, maske, p)
        kmask = maske[p:p + len(k)]
        kcode = "".join(c if kmask[i] else " " for i, c in enumerate(k))
        hat_catch = ".catch(" in kcode
        # await innerhalb eines try? - grob: steht `await` direkt davor
        vor200 = text[max(0, p - 200):p]
        vor200c = "".join(c if maske[max(0, p - 200) + i] else " "
                          for i, c in enumerate(vor200))
        awaited = bool(re.search(r"await\s*$", vor200c))
        stand = "CATCH" if hat_catch else ("AWAIT" if awaited else "OFFEN")
        if stand == "OFFEN":
            ohne += 1
        print("  Z%-7d %-6s len=%-5d %s"
              % (zeile_von(text, p), stand, len(k), " ".join(k.split())[:120]))
    print("")
    print("OHNE .catch und ohne await: %d" % ohne)
    print("Globaler Auffang: window.onunhandledrejection Zeile %d"
          % zeile_von(text, text.index("window.onunhandledrejection")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
