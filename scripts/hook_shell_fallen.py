# -*- coding: utf-8 -*-
"""PreToolUse-Haken fuer Bash: die Shell-Fallen, die in diesem Haus GEMESSEN
Schaden angerichtet haben.

🔴 JEDE REGEL HIER HAT EIN DATUM UND EINEN SCHADEN. Eine Regel ohne Messung
waere eine Attrappe - sie wuerde Arbeit behindern, ohne etwas zu verhindern.

A) `git push ... HEAD:main`
   `HEAD` ist das, was gerade ausgecheckt ist - nicht das, was geprueft wurde.
   Steht der Baum woanders, schiebt man etwas anderes, als man gemessen hat.
   Immer `git push origin <sha>:main`.

B) Ein Backtick INNERHALB doppelter Anfuehrungszeichen
   Bash fuehrt jedes Wort in Backticks als Befehl AUS und ersetzt es durch
   dessen Ausgabe - meist durch nichts. Am 27.09.2026 hat das aus einer
   `python -c "..."`-Zeile heraus acht Woerter aus MEMORY.md GELOESCHT
   (`!important`, `origin/main`, `_kurz(nm,6)` ...), lautlos, mit
   Rueckgabewert 0. Fuer Befehlsersetzung `$( )` nehmen, fuer Prosa und Regex
   das Write-Werkzeug.

C) `git commit -m` mit einer langen oder mehrzeiligen Meldung
   Am 27.09.2026 zersprang eine Meldung an einem inneren doppelten
   Anfuehrungszeichen; `gehoert` wurde als Dateiname gelesen, `dieser` als
   Befehl. Lange deutsche Meldungen gehoeren in eine Datei: `git commit -F`.

D) Ein UNQUOTED Heredoc mit Backticks
   Dieselbe Ausfuehrung wie B, nur im Heredoc. `<<'PY'` statt `<<PY` - und
   auch das schmilzt noch zwei Backslashes zu einem ein.

Der Haken schreibt eine Entscheidung nach stdout und endet IMMER mit 0. Ein
Haken, der abstuerzt, ist ein Haken, der nicht mehr misst.
"""
import json
import re
import sys


def _deny(grund):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": grund}}, ensure_ascii=False))
    sys.exit(0)


def backtick_in_doppelten(cmd):
    """Steht ein nicht geschuetzter Backtick innerhalb doppelter Anfuehrungs-
    zeichen? Gibt den Ausschnitt zurueck oder None.

    Es wird wirklich abgetastet, nicht gesucht: ein Backtick in EINFACHEN
    Anfuehrungszeichen ist harmlos, und nur der Unterschied entscheidet.
    """
    i, n = 0, len(cmd)
    zustand = None          # None | '"' | "'"
    while i < n:
        c = cmd[i]
        if c == "\\" and zustand != "'":
            i += 2
            continue
        if zustand is None:
            if c in "\"'":
                zustand = c
        elif c == zustand:
            zustand = None
        elif zustand == '"' and c == "`":
            return cmd[max(0, i - 40):i + 40]
        i += 1
    return None


def unquoted_heredoc_mit_backtick(cmd):
    """`<<WORT` ohne Anfuehrungszeichen, und irgendwo danach ein Backtick."""
    m = re.search(r"<<-?\s*([A-Za-z_]\w*)\s*$", cmd, re.M)
    if not m:
        return None
    rest = cmd[m.end():]
    return rest[:80] if "`" in rest else None


def main():
    try:
        daten = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = ((daten.get("tool_input") or {}).get("command") or "")
    if not cmd:
        return 0

    # ── A ─────────────────────────────────────────────────────────────────
    if re.search(r"git\s+push\b[^\n;&|]*\bHEAD:", cmd):
        _deny(
            "Verweigert: `git push ... HEAD:main`.\n"
            "  HEAD ist das, was gerade ausgecheckt ist - nicht das, was du "
            "gemessen hast.\n"
            "  Steht der Baum woanders, schiebst du etwas anderes als "
            "geprueft.\n"
            "  Nimm die Nummer, die durch die Tore gegangen ist:\n"
            "      SHA=$(git rev-parse HEAD) && git push origin $SHA:main")

    # ── B ─────────────────────────────────────────────────────────────────
    stelle = backtick_in_doppelten(cmd)
    if stelle:
        _deny(
            "Verweigert: ein Backtick INNERHALB doppelter Anfuehrungszeichen.\n"
            "  Bash fuehrt jedes Wort in Backticks als BEFEHL aus und ersetzt "
            "es durch dessen\n"
            "  Ausgabe - meist durch nichts. Am 27.09.2026 hat genau das aus "
            "einer\n"
            "  `python -c \"...\"`-Zeile heraus acht Woerter aus MEMORY.md "
            "geloescht, lautlos,\n"
            "  mit Rueckgabewert 0.\n"
            "  Fuer Befehlsersetzung: $( ). Fuer Prosa, Regex oder Markdown: "
            "das Write-Werkzeug\n"
            "  und dann `python <datei>`.\n"
            "  Stelle: ..." + stelle.replace("\n", " ") + "...")

    # ── C ─────────────────────────────────────────────────────────────────
    if re.search(r"git\s+commit\b", cmd) and re.search(r"(?<!\w)-m\b", cmd) \
            and "-F" not in cmd:
        if "\n" in cmd or len(cmd) > 400:
            _deny(
                "Verweigert: `git commit -m` mit einer langen oder "
                "mehrzeiligen Meldung.\n"
                "  Am 27.09.2026 zersprang so eine Meldung an einem inneren "
                "doppelten\n"
                "  Anfuehrungszeichen: `gehoert` wurde als Dateiname gelesen, "
                "`dieser` als Befehl.\n"
                "  Schreib die Meldung mit dem Write-Werkzeug in eine Datei "
                "und nimm:\n"
                "      git add <dateien> && git commit -F <meldungsdatei>\n"
                "  (Laenge des Befehls: %d Zeichen, Zeilenumbruch: %s)"
                % (len(cmd), "ja" if "\n" in cmd else "nein"))

    # ── D ─────────────────────────────────────────────────────────────────
    hd = unquoted_heredoc_mit_backtick(cmd)
    if hd:
        _deny(
            "Verweigert: ein UNQUOTED Heredoc (`<<WORT`) mit Backticks "
            "darin.\n"
            "  Bash fuehrt sie als Befehle aus und loescht sie aus dem Text. "
            "Nimm `<<'WORT'`\n"
            "  - und auch das schmilzt noch zwei Backslashes zu einem ein, "
            "also gehoeren\n"
            "  Regex und deutsche Prosa ins Write-Werkzeug.\n"
            "  Stelle: ..." + hd.replace("\n", " ") + "...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
