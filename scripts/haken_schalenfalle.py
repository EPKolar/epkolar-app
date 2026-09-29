# -*- coding: utf-8 -*-
"""Haken: haelt Schalenbefehle an, in denen die Schale den Text FRISST.

🔴 WARUM ES DIESEN HAKEN GIBT. Am 29.09.2026 habe ich denselben Fehler
ZWEIMAL innerhalb einer Stunde gemacht - obwohl die Regel dazu im Gedaechtnis
stand und ich sie am selben Tag noch einmal aufgeschrieben hatte. Das ist
genau die Regel „eine Regel zu KENNEN verhindert den Fehler nicht": sie muss
in ein WERKZEUG.

  Fall 9:  ein Heredoc schmolz `\\\\s` zu `\\s` -> SyntaxError, die Riegeldatei
           war kaputt und liess sich nicht einmal einsammeln.
  Fall 10: `python -c "... `changesNotSentForReview=true` ..."` - die Schale
           hat den Begriff in Backticks als BEFEHL ausgefuehrt und aus dem
           Text ENTFERNT. Der Lauf meldete Erfolg und druckte eine plausible
           Bytezahl. Sichtbar wurde es nur durch Nachlesen der Datei.

🔴 UND DIE PRAEMISSE IST GEMESSEN, NICHT ERINNERT. Bevor dieser Haken
Befehle anhaelt, wurde am 29.09. nachgemessen, welche Form wirklich frisst:

    Form                 zwei Backslashes      Backtick
    'einfach'            bleibt                bleibt
    "doppelt"            SCHMILZT              WIRD AUSGEFUEHRT
    <<'HEREDOC'          SCHMILZT              bleibt
    <<HEREDOC            SCHMILZT              WIRD AUSGEFUEHRT

Deshalb faengt der Haken NICHT jeden Backslash ab - in einfachen
Anfuehrungszeichen ist alles sicher, und ein einzelnes `\\s` ueberlebt auch
den Heredoc. Ein Haken, der richtige Befehle verbietet, wird abgeschaltet,
und dann schuetzt er gar nichts mehr.

WAS ER ANHAELT (jeweils mit dem Weg, der funktioniert):
  1. `\\\\` in einem doppelt gequoteten Bereich oder in einem Heredoc
  2. ein nackter Backtick in einem doppelt gequoteten Bereich oder in einem
     UNgequoteten Heredoc
  3. `git commit -m` mit Anfuehrungszeichen oder Zeilenumbruch in der Meldung
     (am 29.09. ist genau daran ein Commit still ausgefallen)
  4. `$?` hinter einer Pipe - das ist der Rueckgabewert des LETZTEN Glieds

Aufruf als Haken:  echo '<json>' | python scripts/haken_schalenfalle.py
Selbstprobe:       python scripts/haken_schalenfalle.py --eichen
"""
import json
import re
import sys

EINF, DOPP, HEREDOC_ROH, HEREDOC_Q, NORMAL = "'", '"', "H", "h", " "


def zustaende(befehl):
    """Je Zeichen den Quotierzustand. Kein Regex - Quotierung ist ein Zustand.

    Zurueck: Liste gleicher Laenge mit NORMAL / EINF / DOPP / HEREDOC_ROH /
    HEREDOC_Q.
    """
    n = len(befehl)
    aus = [NORMAL] * n
    i = 0
    zustand = NORMAL
    heredoc_wort = None
    while i < n:
        c = befehl[i]
        if zustand in (HEREDOC_ROH, HEREDOC_Q):
            aus[i] = zustand
            if c == "\n":
                # Steht die Endmarke allein in der naechsten Zeile?
                rest = befehl[i + 1:]
                zeile = rest.split("\n", 1)[0].strip()
                if zeile == heredoc_wort:
                    for k in range(i + 1, i + 1 + len(rest.split("\n", 1)[0])):
                        aus[k] = NORMAL
                    i = i + 1 + len(rest.split("\n", 1)[0])
                    zustand, heredoc_wort = NORMAL, None
                    continue
            i += 1
            continue
        if zustand == EINF:
            aus[i] = EINF
            if c == "'":
                zustand = NORMAL
            i += 1
            continue
        if zustand == DOPP:
            aus[i] = DOPP
            if c == "\\" and i + 1 < n:
                aus[i + 1] = DOPP
                i += 2
                continue
            if c == '"':
                zustand = NORMAL
            i += 1
            continue
        # NORMAL
        m = re.match(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", befehl[i:])
        if m:
            for k in range(i, i + m.end()):
                aus[k] = NORMAL
            heredoc_wort = m.group(2)
            zustand = HEREDOC_Q if m.group(1) else HEREDOC_ROH
            i += m.end()
            continue
        if c == "'":
            zustand = EINF
        elif c == '"':
            zustand = DOPP
        elif c == "\\" and i + 1 < n:
            aus[i] = NORMAL
            aus[i + 1] = NORMAL
            i += 2
            continue
        aus[i] = NORMAL if zustand == NORMAL else zustand
        i += 1
    return aus


def _zeile(befehl, i):
    return befehl.count("\n", 0, i) + 1


def pruefe(befehl):
    """Liste von (Kennung, Meldung). Leer heisst: der Befehl darf laufen."""
    z = zustaende(befehl)
    n = len(befehl)
    befunde = []

    # 1. Zwei Backslashes dort, wo die Schale einen davon frisst.
    for i in range(n - 1):
        if befehl[i] == "\\" and befehl[i + 1] == "\\" and \
                z[i] in (DOPP, HEREDOC_ROH, HEREDOC_Q):
            befunde.append((
                "backslash",
                "Zeile %d: `\\\\` in %s - die Schale macht daraus EINEN "
                "Backslash.\n"
                "Gemessen am 29.09.: das gilt auch fuer <<'HEREDOC'. Ein "
                "Regex-Kuerzel wird dabei\nzu einem anderen Zeichen, und die "
                "Datei ist kaputt, ohne dass der Lauf es meldet.\n"
                "STATTDESSEN: den Text mit dem Write- oder Edit-Werkzeug "
                "schreiben. Oder, wenn es\nunbedingt die Schale sein muss, "
                "den Textteil in EINFACHE Anfuehrungszeichen -\ndort bleibt "
                "alles stehen."
                % (_zeile(befehl, i),
                   "doppelten Anfuehrungszeichen" if z[i] == DOPP
                   else "einem Heredoc")))
            break

    # 2. Nackter Backtick, wo die Schale ihn ausfuehrt.
    for i in range(n):
        if befehl[i] == "`" and z[i] in (DOPP, HEREDOC_ROH):
            # In DOPP ist ein escapeter Backtick harmlos; `zustaende` hat das
            # Zeichen dann schon als Paar uebersprungen.
            if i > 0 and befehl[i - 1] == "\\":
                continue
            befunde.append((
                "backtick",
                "Zeile %d: ein nackter Backtick in %s - die Schale FUEHRT "
                "den Inhalt AUS\nund ersetzt ihn durch dessen Ausgabe. "
                "Steht dort Prosa statt eines Befehls, wird\nder Begriff "
                "aus dem Text GELOESCHT, und der Lauf meldet trotzdem "
                "Erfolg.\n"
                "Genau so ist am 29.09. `status: completed` aus einer "
                "Gedaechtnisdatei verschwunden.\n"
                "STATTDESSEN: Write/Edit, oder EINFACHE Anfuehrungszeichen, "
                "oder <<'HEREDOC'\n(dort bleibt der Backtick stehen - "
                "gemessen)."
                % (_zeile(befehl, i),
                   "doppelten Anfuehrungszeichen" if z[i] == DOPP
                   else "einem UNgequoteten Heredoc")))
            break

    # 3. `git commit -m` mit Anfuehrungszeichen oder Umbruch in der Meldung.
    m = re.search(r"git\s+commit\b[^\n|;&]*?\s-m\s+(['\"])", befehl)
    if m:
        auf = m.end() - 1
        q = m.group(1)
        j = auf + 1
        while j < n and not (befehl[j] == q and befehl[j - 1] != "\\"):
            j += 1
        meldung = befehl[auf + 1:j]
        if '"' in meldung or "\n" in meldung:
            befunde.append((
                "commit",
                "Die Commit-Meldung enthaelt Anfuehrungszeichen oder einen "
                "Zeilenumbruch.\n"
                "Am 29.09. hat genau das einen Commit STILL ausfallen "
                "lassen: die Zeichenkette\nendete am inneren "
                "Anfuehrungszeichen, `git commit` bekam Unsinn, und weil die "
                "Ausgabe\ndurch ein `grep` lief, sah es aus wie ein "
                "Durchlauf ohne Treffer.\n"
                "STATTDESSEN: die Meldung in eine Datei schreiben und "
                "`git commit -F <datei>` benutzen."))

    # 4. `$?` hinter einer ECHTEN Pipe.
    # 🔴 DER ERSTE ENTWURF HAT HIER JEDES `|` GEZAEHLT - und der Haken hat
    #    damit, kaum eingetragen, meinen eigenen `jq`-Befehl angehalten:
    #        jq -e '.hooks.PreToolUse[] | select(...)' settings.json; echo $?
    #    Das `|` steht dort in EINFACHEN Anfuehrungszeichen, es ist der
    #    Operator von `jq`, nicht der der Schale. Ein Haken, der richtige
    #    Arbeit anhaelt, wird abgeschaltet - also wird der Quotierzustand
    #    mitgelesen, so wie bei den drei Pruefungen darueber auch.
    # 🔴 UND DER ZWEITE FEHLALARM, am selben Abend: ich hatte
    #        python version_stempeln.py | tail -2 && python torkette.py > log
    #        2>&1; echo "[Code $?]"
    #    Die Pipe gehoert zum ERSTEN Befehl, das `$?` zum zweiten - der ist
    #    in eine Datei umgeleitet, nicht gepipet. Der Haken hat trotzdem
    #    angehalten, weil er nur fragte "gibt es irgendwo vorher eine Pipe".
    #    Gefragt werden muss: steht in dem Befehl, der UNMITTELBAR vor
    #    diesem `$?` gelaufen ist, eine Pipe? Zwei Fehlalarme in wenigen
    #    Stunden, und jeder ist eine Gelegenheit, den Haken abzuschalten.
    echte_pipes = [i for i in range(n)
                   if befehl[i] == "|" and z[i] == NORMAL
                   and not (i + 1 < n and befehl[i + 1] == "|")
                   and not (i > 0 and befehl[i - 1] == "|")]
    trenner = [i for i in range(n)
               if z[i] == NORMAL and (
                   befehl[i] in ";\n"
                   or befehl.startswith("&&", i)
                   or befehl.startswith("||", i))]
    if echte_pipes and "$?" in befehl:
        fp = befehl.rindex("$?")
        # Die Grenzen des Befehls, der vor diesem `$?` gelaufen ist.
        davor = [t for t in trenner if t < fp]
        ende = davor[-1] if davor else 0
        anfang = davor[-2] if len(davor) > 1 else 0
        vorheriger = befehl[anfang:ende]
        if any(anfang <= p < ende for p in echte_pipes) or (
                not davor and echte_pipes):
            befunde.append((
                "pipe",
                "`$?` steht hinter einer Pipe - das ist der Rueckgabewert "
                "des LETZTEN Glieds,\nnicht des Werkzeugs davor. `pytest ... "
                "| tail` meldet den Code von `tail`, also\nfast immer 0. "
                "Das Urteil gehoert aus der LOGDATEI oder aus einem Lauf "
                "ohne Pipe\n(`befehl > datei; echo $?`)."))
    return befunde


# ── Selbstprobe ──────────────────────────────────────────────────────────
# 🔴 Ein Haken ohne Eichung ist schlimmer als keiner: er laeuft bei JEDEM
#    Befehl, und wenn er nichts sieht, sieht das aus wie Sicherheit.
KOEDER = [
    ("backslash", 'python -c "import re; re.compile(\\"a\\\\\\\\s\\")"'),
    ("backslash", "cat > x <<'PY'\nr = '\\\\s'\nPY"),
    ("backtick", 'python -c "print(\'a `echo XX` b\')"'),
    ("backtick", "cat > x <<PY\nein `wort` hier\nPY"),
    ("commit", 'git commit -m "sagte \\"nein\\" dazu"'),
    ("pipe", "pytest tests/ | tail -3; echo $?"),
]
GEGENPROBEN = [
    "python -c 'print(\"a \\\\s b\")'",          # einfache Quotes: sicher
    "cat > x <<'PY'\nein `wort` bleibt hier\nPY",  # Backtick im gequoteten HD
    "grep -n 'foo' index.html | head -5",         # Pipe ohne $?
    "git commit -F /tmp/meldung.txt",             # der richtige Weg
    'echo "ein \\`escapeter\\` Backtick"',        # escapet -> harmlos
    "git log --oneline -3",
    # 🔴 DER FALL, AN DEM DER HAKEN AM 29.09. SOFORT NACH DEM EINTRAGEN
    #    danebengegriffen hat: das `|` gehoert `jq`, nicht der Schale.
    "jq -e '.hooks.PreToolUse[] | select(.matcher == \"Bash\") "
    "| .hooks[] | .command' ~/.claude/settings.json; echo \"[jq $?]\"",
    # Und die verwandte Form: `||` ist keine Pipe.
    "python x.py 2>/dev/null || true; echo $?",
    # 🔴 DER ZWEITE FEHLALARM vom 29.09.: die Pipe gehoert zum ERSTEN
    #    Befehl, das `$?` zum zweiten - der ist umgeleitet, nicht gepipet.
    "python version_stempeln.py 3.9.989 | tail -2 && "
    "python torkette.py > log 2>&1; echo \"[Code $?]\"",
]


def eichen():
    schief = []
    for erwartet, befehl in KOEDER:
        arten = [a for a, _m in pruefe(befehl)]
        if erwartet not in arten:
            schief.append("KOEDER %-10s nicht gefunden in %r (gefunden: %s)"
                          % (erwartet, befehl[:60], arten or "nichts"))
    for befehl in GEGENPROBEN:
        arten = [a for a, _m in pruefe(befehl)]
        if arten:
            schief.append("GEGENPROBE faelschlich angehalten (%s): %r"
                          % (arten, befehl[:60]))
    return schief


def main(argv):
    # Auch die Eichausgabe traegt Zeichen, die cp1252 nicht kennt.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                 # ältere Fassungen kennen das nicht
        pass
    if "--eichen" in argv:
        schief = eichen()
        print("Eichung: %d Koeder, %d Gegenproben"
              % (len(KOEDER), len(GEGENPROBEN)))
        for s in schief:
            print("   \U0001F534 " + s)
        if schief:
            print("\nDer Haken ist NICHT geeicht. Er laeuft bei jedem Befehl "
                  "mit; sieht er nichts,\nsieht das aus wie Sicherheit.")
            return 2
        print("   \U0001F7E2 alle %d richtig" % (len(KOEDER)
                                                 + len(GEGENPROBEN)))
        return 0

    try:
        daten = json.load(sys.stdin)
    except Exception:
        return 0                      # 🔴 Im Zweifel DURCHLASSEN.
    befehl = ((daten.get("tool_input") or {}).get("command") or "")
    if not befehl:
        return 0
    befunde = pruefe(befehl)
    if not befunde:
        return 0
    grund = ("\U0001F534 DIE SCHALE FRISST DEN TEXT.\n\n"
             + "\n\n".join(m for _a, m in befunde)
             + "\n\nDas ist keine Stilfrage: am 29.09.2026 ist derselbe "
               "Fehler ZWEIMAL in einer\nStunde passiert, beide Male bei "
               "einer Nebensache, beide Male mit gruener\nRueckmeldung. "
               "Geprueft mit scripts/haken_schalenfalle.py --eichen.")
    # 🔴 `ensure_ascii=True` IST HIER KEINE STILFRAGE. Der erste Rohrtest hat
    #    den Haken zum ABSTUERZEN gebracht: auf Windows ist die Standard-
    #    ausgabe cp1252, und das rote Zeichen in der Begruendung ist dort
    #    nicht darstellbar -> UnicodeEncodeError, Rueckgabe 1, keine Ausgabe.
    #    Ein Haken, der abstuerzt, schuetzt nicht - er stoert nur. Die
    #    JSON-Schreibweise `\uXXXX` ist reines ASCII und geht durch jede
    #    Konsole. Der Riegel dazu heisst
    #    test_die_ausgabe_ueberlebt_eine_cp1252_konsole.
    sys.stdout.write(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": grund}}, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
