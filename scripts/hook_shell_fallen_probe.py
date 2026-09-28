# -*- coding: utf-8 -*-
"""Selbstprobe des Shell-Fallen-Hakens: Koeder UND Gegenprobe.

🔴 Die Proben stehen HIER und nicht in einer Shell-Zeile, weil die Faelle,
die dieser Haken faengt, in einer Shell-Zeile nicht sauber zu schreiben sind.
Wer den Koeder durch dieselbe Falle schickt, die er pruefen will, misst die
Falle statt den Haken.
"""
import io
import json
import os
import subprocess
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
HAKEN = os.path.join(HIER, "hook_shell_fallen.py")
BT = chr(96)          # Backtick, ohne ihn hinschreiben zu muessen

# (Name, Befehl, muss_verweigert_werden)
FAELLE = [
    # ── A: HEAD:main ─────────────────────────────────────────────────────
    ("A1 push HEAD:main", "git push origin HEAD:main", True),
    ("A2 push mit SHA", "git push origin 4526b70:main", False),
    ("A3 SHA aus Variable",
     "SHA=$(git rev-parse HEAD) && git push origin $SHA:main", False),
    # ── B: Backtick in doppelten Anfuehrungszeichen ──────────────────────
    ("B1 Backtick in doppelten",
     'python -c "s=s.replace(' + BT + "!important" + BT + ', 1)"', True),
    ("B2 Backtick in EINFACHEN (harmlos)",
     "echo 'ein " + BT + "Wort" + BT + " in einfachen ist Text'", False),
    ("B3 $( ) statt Backtick", 'echo "heute ist $(date)"', False),
    ("B4 geschuetzter Backtick", 'echo "ein \\' + BT + ' geschuetzt"', False),
    # ── C: langes git commit -m ──────────────────────────────────────────
    ("C1 lange Meldung",
     'git add a.py && git commit -m "' + ("wort " * 90) + '"', True),
    ("C2 mehrzeilige Meldung",
     'git add a.py && git commit -m "erste Zeile\nzweite Zeile"', True),
    ("C3 kurze Meldung", 'git add a.py && git commit -m "kurz"', False),
    ("C4 lange Meldung, aber -F",
     'git add a.py && git commit -F msg.txt  # ' + ("x" * 400), False),
    # ── D: unquoted Heredoc mit Backtick ─────────────────────────────────
    ("D1 unquoted Heredoc",
     "python - <<PY\nprint('" + BT + "date" + BT + "')\nPY", True),
    ("D2 quoted Heredoc",
     "python - <<'PY'\nprint('" + BT + "date" + BT + "')\nPY", False),
    # ── Gegenproben: ganz normale Befehle ────────────────────────────────
    ("Z1 normaler Aufruf", "python -m pytest tests/ -q", False),
    ("Z2 git add einzeln", "git add index.html sw.js", False),
]


def fragen(befehl):
    last = subprocess.run(
        [sys.executable, HAKEN],
        input=json.dumps({"tool_name": "Bash",
                          "tool_input": {"command": befehl}}),
        capture_output=True, text=True, encoding="utf-8")
    if last.returncode != 0:
        return "ABSTURZ: " + (last.stderr or "")[:120]
    aus = (last.stdout or "").strip()
    if not aus:
        return False
    try:
        return json.loads(aus)["hookSpecificOutput"]["permissionDecision"] \
            == "deny"
    except Exception:
        return "UNLESBAR: " + aus[:120]


def main():
    fehler = 0
    for name, befehl, soll in FAELLE:
        ist = fragen(befehl)
        if ist is True or ist is False:
            ok = (ist == soll)
        else:
            ok, fehler = False, fehler + 1
            print("  ROT  %-34s %s" % (name, ist))
            continue
        if not ok:
            fehler += 1
        print("  %s %-34s soll %s, ist %s"
              % ("OK  " if ok else "ROT ", name,
                 "VERWEIGERN" if soll else "schweigen",
                 "verweigert" if ist else "schweigt"))
    print("\n%d von %d Proben gruen" % (len(FAELLE) - fehler, len(FAELLE)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
