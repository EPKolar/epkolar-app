# -*- coding: utf-8 -*-
"""Gate 5: die geschuetzten Funktionen muessen byte-identisch bleiben.

WOZU
────
Fuenf Funktionen tragen Lohn- und Eskalationslogik und duerfen im UI-Umbau
unter keinen Umstaenden mitwandern:

    _ezEffTage        Entfernungszulage, effektive Tage (lohnnah)
    _asEskalierbar    Arbeitsschein-Eskalation
    _dispoPlan        Dispo-Planung
    _maIstEhemalig    wer ist ausgeschieden (Listen)
    _maWaehlbar       wer ist waehlbar (Zuweisungsfelder)

Dazu zwei weitere Tabu-Funktionen, die nicht in der Pflichtliste stehen, aber
genauso wenig angefasst werden duerfen: _juprowaPush, _juprowaSanitize.

WARUM md5 UND NICHT "kommt noch vor"
────────────────────────────────────
Ein Riegel, der nur die ANWESENHEIT des Namens prueft, bleibt gruen, waehrend
der Rumpf umgeschrieben wird. Gemessen wird deshalb der Rumpf.

WAS GEMESSEN WIRD
─────────────────
Die ersten 4000 Zeichen ab `function <name>`. Das ist laenger als jede der
sieben Funktionen und damit ein Fingerabdruck des Rumpfes samt Umfeld. Wird
eine Funktion laenger oder kuerzer, aendert sich die Summe ebenfalls - das ist
gewollt.

FAIL-CLOSED
───────────
Findet das Skript eine Funktion NICHT, ist das rot, nicht gruen. Eine
verschwundene Funktion ist der schlimmste denkbare Fall, und "nicht gefunden"
darf nie wie "nichts zu beanstanden" aussehen.

AUFRUF
──────
    python scripts/md5_geschuetzt.py            vergleicht gegen die Tabelle
    python scripts/md5_geschuetzt.py --zeigen   gibt die Summen aus
"""
import hashlib
import io
import re
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(WURZEL, "index.html")

# Ausgangsstand 25.09.2026, Commit f5e632f (vor Stufe 0 des UI-Umbaus).
SOLL = {
    "_ezEffTage":       "619e773271bb534233765f37bb7207ac",
    "_asEskalierbar":   "97382c7a333d77e7a2eb19c93c08f1c2",
    "_dispoPlan":       "dd24f646d3c331b28be2366b29a2a6aa",
    "_maIstEhemalig":   "e55c5728c9effe85af2c1ed10539aed0",
    "_maWaehlbar":      "4b69b19ec07e68b8ba7dbe765c7a7b2c",
    "_juprowaPush":     "0bf3b57737d6f5a57827ddabce167c89",
    "_juprowaSanitize": "e53a24a07082abe6e9910a091ea5dd08",
}

LAENGE = 4000


def summen(quelle):
    """Gibt {name: md5} zurueck; fehlende Funktionen als None.

    🔴 v3.9.961 MIT WORTGRENZE. Vorher stand hier ein schlichtes
    `quelle.find("function " + name)` - und das trifft auch
    `function _maWaehlbarX`. Eine Umbenennung, die den Namen VERLAENGERT,
    wurde damit nicht als "NICHT GEFUNDEN" gemeldet, sondern als "VERAENDERT":
    es wurde ein anderer Rumpf gehasht, und die Summe wich ab. Der Schutz hielt
    also in der Wirkung - die Diagnose war falsch. Stuende neben einer
    geloeschten Funktion eine aehnlich benannte, waere die Meldung vollends
    irrefuehrend gewesen.
    Gefunden von einem Koeder, der genau das nachstellte
    (tests/test_geschuetzte_funktionen_v961.py).

    Die Fundstellen der sieben echten Funktionen aendern sich NICHT - hinter
    ihrem Namen steht immer eine oeffnende Klammer. Gegengemessen beim Umbau:
    alle sieben Summen unveraendert.
    """
    ergebnis = {}
    for name in SOLL:
        m = re.search(r"function\s+" + re.escape(name) + r"\s*\(", quelle)
        if m is None:
            ergebnis[name] = None
            continue
        i = m.start()
        ergebnis[name] = hashlib.md5(
            quelle[i:i + LAENGE].encode("utf-8")).hexdigest()
    return ergebnis


def main(argv):
    s = io.open(ZIEL, encoding="utf-8", newline="").read()
    if len(s) < 1_000_000:
        print("index.html ist nur %d Bytes gross - Datenverlust, keine "
              "md5-Frage." % len(s))
        return 1
    ist = summen(s)

    if "--zeigen" in argv:
        for name in sorted(ist):
            print("%-18s %s" % (name, ist[name] or "NICHT GEFUNDEN"))
        return 0

    schlimm = []
    for name in sorted(SOLL):
        if ist[name] is None:
            schlimm.append("%s: NICHT GEFUNDEN - die Funktion ist weg." % name)
        elif ist[name] != SOLL[name]:
            schlimm.append("%s: VERAENDERT\n    soll %s\n    ist  %s"
                           % (name, SOLL[name], ist[name]))
    if schlimm:
        print("GESCHUETZTE FUNKTIONEN VERAENDERT - Abbruchregel greift:")
        for z in schlimm:
            print("  " + z)
        return 1
    print("Die %d geschuetzten Funktionen sind unveraendert." % len(SOLL))
    return 0


if __name__ == "__main__":
    # v3.9.995: DIE KONSOLE VERTRAEGT NICHT JEDES ZEICHEN. Auf Windows
    # laeuft sie auf cp1252; ein Symbol in der Ausgabe beendet das Tor
    # dann mit einem UnicodeEncodeError - und zwar oft auf dem
    # ERFOLGSZWEIG, beim Hinschreiben des gruenen Punktes. Die Torkette
    # liest den Rueckgabewert und meldet ROT, obwohl die Messung selbst
    # in Ordnung war. Am 30.09.2026 ist genau das zwei Toren passiert.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
