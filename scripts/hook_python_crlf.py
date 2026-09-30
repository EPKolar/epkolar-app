# -*- coding: utf-8 -*-
"""PostToolUse-Haken: eine Python-Datei, die ohne `newline=''` schreibt.

🔴 DER GEMESSENE SCHADEN: Pythons `io.open(p, 'w')` stellt auf Windows JEDE
Zeile der geschriebenen Datei auf CRLF um. Am 26.09.2026 hat ein Skript damit
EIN Wort geaendert und 10.389 Zeilen. Neunzehn Dateien waren betroffen, und
die Zahl war erst im VIERTEN Durchgang vollstaendig. Gefunden wurde es an
einem ganz anderen Riegel, der `\\n}\\n` suchte.

Dieser Haken BLOCKIERT NICHT - er meldet. Es gibt Faelle, in denen CRLF
richtig ist (eine Datei, die ohnehin CRLF fuehrt, mit `newline=''` gelesen und
geschrieben). Aber es gibt keinen Fall, in dem man es nicht WISSEN will.

Er laeuft nach Write/Edit und sieht nur die eben geschriebene Datei an.
"""
import io
import json
import os
import re
import sys

# Ein Schreibaufruf ohne newline=... - beide Schreibweisen, open und io.open.
SCHREIBT = re.compile(
    r"(?:io\.)?open\s*\(\s*([^()]*?)\s*,\s*['\"][rwa]?\+?[wa]\+?[bt]?['\"]"
    r"([^()]*)\)")


def main():
    try:
        daten = json.load(sys.stdin)
    except Exception:
        return 0
    ein = daten.get("tool_input") or {}
    ant = daten.get("tool_response") or {}
    pfad = ant.get("filePath") or ein.get("file_path") or ""
    if not pfad.endswith(".py") or not os.path.exists(pfad):
        return 0
    try:
        text = io.open(pfad, encoding="utf-8", newline="").read()
    except Exception:
        return 0

    fund = []
    for m in SCHREIBT.finditer(text):
        ganz = m.group(0)
        if "newline=" in ganz:
            continue
        if "'b'" in ganz or '"b"' in ganz or "b'" in ganz or 'b"' in ganz:
            continue          # binaer schreibt ohnehin unveraendert
        zeile = text.count("\n", 0, m.start()) + 1
        fund.append((zeile, ganz[:70]))

    if not fund:
        return 0
    liste = "\n".join("      Zeile %d: %s" % z for z in fund[:6])
    print(json.dumps({
        "systemMessage":
            "\U0001F534 %s schreibt an %d Stelle(n) OHNE newline='':\n%s\n"
            "  Auf Windows stellt das JEDE Zeile der Zieldatei auf CRLF um. Am "
            "26.09.2026 hat\n"
            "  ein Skript so EIN Wort geaendert und 10.389 Zeilen - in "
            "neunzehn Dateien, und\n"
            "  die Zahl war erst im vierten Durchgang vollstaendig.\n"
            "  Wenn CRLF hier richtig ist: schreib es als newline='' hin und "
            "sag im Kommentar,\n"
            "  warum. Wenn nicht: newline='' ergaenzen."
            % (os.path.basename(pfad), len(fund), liste),
        "suppressOutput": True}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    # 🔴 v3.9.995: DIESER HAKEN IST AN SEINER EIGENEN MELDUNG ABGESTUERZT.
    # Die Windows-Konsole laeuft auf cp1252; das 🔴 in der Meldung liess sich
    # dort nicht schreiben, `ensure_ascii=False` gab es roh aus, und der Haken
    # endete mit einem UnicodeEncodeError STATT mit einer Warnung. Ein Haken,
    # der beim Melden stirbt, meldet NIE - und das faellt nur auf, wenn ihn
    # jemand misst. Hier hat es der eigene Riegel gefunden, nicht ein Nutzer.
    # Zwei Schutzschichten, wie bei haken_schalenfalle.py und
    # gedaechtnis_pruefen.py: der Strom wird auf utf-8 umgestellt, UND die
    # Ausgabe bleibt reines ASCII, falls sich der Strom nicht umstellen laesst
    # (umgeleitet, eingebettet, fremde Schale).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
