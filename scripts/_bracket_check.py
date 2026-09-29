#!/usr/bin/env python3
"""One-shot bracket sanity for index.html.

Baseline (v3.9.12): ( ) -1 / { } 0 / [ ] 0
Strips strings, template literals, comments before counting.

🔴 DIE NOTIZ VOM 18.05.2026 WAR FALSCH. WIDERLEGT AM 29.09.2026.

Sie lautete: "investigated 2026-05-18 and confirmed it is NOT a stripper
artifact ... The drift is a real, stable code-level imbalance in index.html
and should only be touched if a future audit shows it changed."

Der Audit hat stattgefunden. Zustandsbasiert nachgerechnet
(`scripts/klammerbilanz.py`, auf `code_scan.ist_code`):

    alte Maske, Netto ()                     -1
    neue Maske, Netto ()                      0
    NUR vom alten Tor gezaehlt, Netto ()      0
    NUR vom neuen Tor gezaehlt, Netto ()     +1

Das `-1` ist das Spiegelbild eines `+1`, das in der EIGENEN blinden Zone
dieses Streichers liegt. Bei richtiger Zerlegung verschwinden beide.

WARUM DIESER STREICHER BLIND IST: das Vorlagenliteral-Muster steht VOR dem
Kommentarmuster. `index.html` zitiert in Kommentaren mit Backticks, und jeder
einzelne wird als ENDE eines viel frueher geoeffneten Literals gelesen. 24
solche Treffer decken 39,6 % der Datei zu; beurteilt werden 27,9 %.

BELEGT, nicht behauptet: eine einzelne unpaarige `(` in echten Code bei
Zeile 11380 gesetzt -> DIESES Tor bleibt GRUEN (Rueckgabe 0), das
zustandsbasierte findet sie mit Zeilenangabe. Der Beleg laeuft auf einer
Kopie und vergleicht den Abdruck des Originals davor und danach:
`scripts/klammertor_vergleich.py`.

DIESE DATEI BLEIBT TROTZDEM, mit unveraenderter Grundlinie:
`tests/test_klammertor_blindheit_v956.py` misst sie und haelt ihre Blindheit
fest, damit sie nicht weiter waechst. Wer hier am Streicher etwas aendert,
macht jenen Riegel bedeutungslos. Das neue Tor steht DANEBEN in der Kette -
es ersetzt dieses nicht.
"""
import re
import sys
from pathlib import Path

target = Path(sys.argv[1] if len(sys.argv) > 1 else "index.html")
src = target.read_text(encoding="utf-8")

# v3.9.894 LEBENSZEICHEN: Am 29.08. hat ein abgebrochener Schreibvorgang
# index.html auf 0 Bytes gekuerzt - und DIESER Riegel meldete '() 0 / {} 0 /
# [] 0', also eine scheinbar SAUBERE Bilanz statt der erwarteten -1. Eine leere
# Datei hat eben ausgeglichene Klammern. Wer nur auf die Zahlen schaut, haelt
# den Totalverlust fuer eine Verbesserung.
if len(src) < 1_000_000:
    print("index.html ist nur %d Bytes gross - das ist Datenverlust, keine"
          " Klammerbilanz. NICHT committen: git checkout -- index.html"
          % len(src))
    sys.exit(1)

# Order matters: STRINGS before COMMENTS so that '//' inside string literals
# (e.g. URLs like "https://...") is not mis-stripped as a line comment.
# Python re alternation uses leftmost-first match per position, so listing
# string patterns first lets them claim '//' that lives inside quotes before
# the comment pattern can grab it.
patterns = [
    r'"(?:[^"\\]|\\.)*"',
    r"'(?:[^'\\]|\\.)*'",
    r"`(?:[^`\\]|\\.)*`",
    r"/\*[\s\S]*?\*/",
    r"//[^\n]*",
]
stripped = re.sub("|".join(patterns), "", src)

paren = stripped.count("(") - stripped.count(")")
brace = stripped.count("{") - stripped.count("}")
brack = stripped.count("[") - stripped.count("]")

print(f"() {paren}")
print(f"{{}} {brace}")
print(f"[] {brack}")

ok = paren == -1 and brace == 0 and brack == 0
sys.exit(0 if ok else 1)
