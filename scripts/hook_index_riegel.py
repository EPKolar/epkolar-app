# -*- coding: utf-8 -*-
"""PostToolUse-Hook: nach jedem Schreiben auf index.html die zwei Tore fahren.

WOZU
────
index.html ist eine einzige Datei von ~3,58 MB ohne Bauschritt. Ein
misslungener Ersatz faellt deshalb nicht beim Uebersetzen auf, sondern erst,
wenn die Seite nicht mehr laedt - oder gar nicht, weil der Fehler in einem
Zweig sitzt, den niemand oeffnet. Am 29.08.2026 hat ein abgebrochener
Schreibvorgang die Datei auf 0 Bytes gekuerzt und BEIDE Tore meldeten gruen
(eine leere Datei parst fehlerfrei); seither tragen beide eine
Lebenszeichen-Schranke. Dieser Hook fuehrt sie unmittelbar nach dem Schreiben,
nicht erst vor dem Commit - dazwischen liegen sonst weitere Aenderungen, die
den Verursacher verdecken.

WAS ER MISST
────────────
  scripts/node_check.py     jeder <script>-Block parst (node --check)
  scripts/_bracket_check.py Klammerbilanz () -1 / {} 0 / [] 0

FAIL-CLOSED
───────────
Laesst sich ein Tor ueberhaupt nicht fahren (kein Python, kein node, Datei
weg), wird GESPERRT, nicht durchgewunken. Ein Riegel, der bei eigenem Ausfall
gruen meldet, ist die Fehlerform, die dieses Repo am haeufigsten getroffen hat:
nichts gefunden heisst dann "keine Fehler".

KEINE PIPES
───────────
`$?` nach einer Pipe ist der Code des LETZTEN Glieds - vier belegte Faelle
allein am 24.09. Deshalb laeuft hier jedes Tor als eigener Prozess und sein
Rueckgabewert wird einzeln gelesen.
"""
import json
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TORE = [
    ("node_check", os.path.join(WURZEL, "scripts", "node_check.py")),
    ("bracket_check", os.path.join(WURZEL, "scripts", "_bracket_check.py")),
]


def _sperre(grund):
    """Meldet zurueck und beendet. `decision: block` reicht den Grund an
    Claude weiter, `systemMessage` zeigt ihn Sebastian im Fenster."""
    json.dump({
        "decision": "block",
        "reason": grund,
        "systemMessage": "index.html-Riegel ROT - siehe Begruendung.",
    }, sys.stdout)
    sys.exit(0)


def betrifft_index(eingabe):
    """True, wenn dieser Werkzeugaufruf index.html geschrieben hat.

    Geprueft werden beide Felder: `tool_input.file_path` (was verlangt wurde)
    und `tool_response.filePath` (was tatsaechlich geschrieben wurde). Sie
    koennen auseinandergehen, und massgeblich ist, was auf der Platte steht.
    """
    pfade = []
    for quelle, schluessel in (("tool_input", "file_path"),
                               ("tool_response", "filePath")):
        teil = eingabe.get(quelle) or {}
        if isinstance(teil, dict) and teil.get(schluessel):
            pfade.append(str(teil[schluessel]))
    return any(os.path.basename(p).lower() == "index.html" for p in pfade)


def main():
    roh = sys.stdin.read()
    try:
        eingabe = json.loads(roh) if roh.strip() else {}
    except ValueError:
        # Unlesbare Eingabe ist KEIN Freifahrtschein: dann ist der Hook
        # kaputt, nicht die Datei sauber.
        _sperre("index.html-Riegel: die Hook-Eingabe war kein JSON (%r). "
                "Der Riegel konnte nicht messen - deshalb sperrt er."
                % roh[:200])

    if not betrifft_index(eingabe):
        return 0

    rot = []
    for name, skript in TORE:
        if not os.path.exists(skript):
            rot.append("%s: das Riegelskript fehlt (%s)" % (name, skript))
            continue
        try:
            r = subprocess.run([sys.executable, skript], cwd=WURZEL,
                               capture_output=True, text=True, timeout=180)
        except Exception as e:                       # noqa: BLE001
            rot.append("%s: liess sich nicht fahren (%s)" % (name, e))
            continue
        if r.returncode != 0:
            ausgabe = ((r.stdout or "") + (r.stderr or "")).strip()
            rot.append("%s: exit %d\n%s" % (name, r.returncode, ausgabe[-1500:]))

    if rot:
        _sperre(
            "index.html wurde geschrieben, aber die Tore sind ROT.\n\n"
            + "\n\n".join(rot)
            + "\n\nDie Aenderung steht bereits in der Datei. Entweder die "
              "Ursache beheben oder zuruecknehmen:\n"
              "    git checkout -- index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
