# -*- coding: utf-8 -*-
"""Der Schalen-Haken faengt die ECHTEN Fehler und laesst die ECHTE Arbeit durch.

🔴 WARUM DIESER RIEGEL NICHT DIE EICHUNG DES HAKENS WIEDERHOLT. Die Eichung
in `haken_schalenfalle.py` prueft ihn an Faellen, die ICH mir ausgedacht habe
- und wer sich die Faelle ausdenkt, denkt sich dieselbe Luecke zweimal.
Hier stehen stattdessen:

  * die beiden Befehle, die am 29.09.2026 WIRKLICH Schaden angerichtet haben,
    Wort fuer Wort abgeschrieben. Faengt der Haken sie nicht, ist er umsonst
    gebaut.
  * und ein Querschnitt der Befehle, die an diesem Tag richtig gelaufen sind.
    Haelt er einen davon an, wird er abgeschaltet - und dann schuetzt er gar
    nichts mehr. Ein Haken, der bei richtiger Arbeit im Weg steht, ist kein
    strenger Haken, sondern ein toter.

🔴 DIE GEGENPROBEN SIND DER WICHTIGERE TEIL. Ein Haken, der ALLES anhaelt,
besteht jede Koederprobe.
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import haken_schalenfalle as H  # noqa: E402


# ── Die echten Unfaelle vom 29.09.2026 ───────────────────────────────────
# Fall 9: ein Heredoc schmolz `\\s` zu `\s`. Die Riegeldatei war danach
#         kaputt und liess sich nicht einmal einsammeln.
UNFALL_HEREDOC = (
    "cd /c/repos/epkolar-app && python - <<'PY'\n"
    "import io\n"
    "p='tests/test_cdn_integrity_v986.py'\n"
    "zusatz = u'''\n"
    "ARBEITER = re.compile(\n"
    "    r\"workerSrc\\\\s*=\\\\s*[\\\"']https://cdnjs\\\\.cloudflare\\\\.com/\")\n"
    "'''\n"
    "io.open(p,'w',encoding='utf-8',newline='').write(s+zusatz)\n"
    "PY")

# Fall 10: die Schale hat den Begriff in Backticks als BEFEHL ausgefuehrt
#          und aus dem Text ENTFERNT - bei gruener Rueckmeldung.
UNFALL_BACKTICK = (
    "cd /c/Users/technik/.claude/projects/C--Users-technik/memory && "
    "python -c \"\n"
    "import io\n"
    "p='MEMORY.md'; s=io.open(p,encoding='utf-8',newline='').read()\n"
    "paare=[('[11.09.](x.md)',\n"
    "        '[11.09.](x.md) - `changesNotSentForReview=true` liess 473 "
    "Commits im Entwurf.')]\n"
    "\"")

# Und der Commit, der still ausgefallen ist, weil die Meldung selbst
# Anfuehrungszeichen trug.
UNFALL_COMMIT = (
    'git commit -m "Doku: Frage 27 erledigt\n\n'
    'sonst waere die Abwesenheit von "es wurde gar nichts gezeichnet" '
    'nicht zu unterscheiden."')


def _arten(befehl):
    return [a for a, _m in H.pruefe(befehl)]


def test_der_echte_heredoc_unfall_wird_gefangen():
    arten = _arten(UNFALL_HEREDOC)
    assert "backslash" in arten, (
        "Der Befehl, der am 29.09. eine Riegeldatei zerstoert hat, laeuft "
        "durch\n  (gefunden: %s). Dann ist der Haken umsonst gebaut." % arten)


def test_der_echte_backtick_unfall_wird_gefangen():
    arten = _arten(UNFALL_BACKTICK)
    assert "backtick" in arten, (
        "Der Befehl, der am 29.09. `status: completed` aus einer "
        "Gedaechtnisdatei\n  geloescht hat, laeuft durch (gefunden: %s)."
        % arten)


def test_der_echte_commit_unfall_wird_gefangen():
    arten = _arten(UNFALL_COMMIT)
    assert "commit" in arten, (
        "Der Commit, der am 29.09. still ausgefallen ist, laeuft durch "
        "(gefunden: %s)." % arten)


# ── Die echte Arbeit desselben Tages, die durchlaufen MUSS ───────────────
# 🔴 Wort fuer Wort abgeschrieben. Jeder dieser Befehle ist am 29.09.
#    gelaufen und hat getan, was er sollte.
ECHTE_ARBEIT = [
    # Commit-Meldungen gingen ueber eine Datei UND einen GEQUOTETEN Heredoc -
    # dort ist der Backtick sicher, und genau das muss der Haken wissen.
    ("Commit-Meldung per gequotetem Heredoc",
     "cd /c/repos/epkolar-app && cat > \"$TEMP/c987.txt\" <<'EOF'\n"
     "v3.9.987: ein fehlgeschlagener CACHE-Schreibvorgang\n\n"
     "  try{ await _sbPost(\"plz_geo\",{...}); geoMap[plz]={...}; }\n"
     "  catch(_w){ /* Tabelle fehlt/RLS -> still weiter */ }\n"
     "EOF\n"
     "git add index.html && git commit -F \"$TEMP/c987.txt\""),
    ("Zeiger im Gedaechtnis zaehlen (einfacher Backslash, kein doppelter)",
     "PYTHONIOENCODING=utf-8 python -c \"\n"
     "import io,re\n"
     "s=io.open('MEMORY.md',encoding='utf-8',newline='').read()\n"
     "v=set(re.findall(r'\\]\\(([^)]+\\.md)\\)', s))\n"
     "print(len(v))\n\""),
    ("Messlauf mit Pipe, ohne $? zu befragen",
     "cd /c/repos/epkolar-app && PYTHONIOENCODING=utf-8 "
     "python scripts/klammerbilanz.py 2>&1 | tail -10"),
    ("grep mit einfachem Backslash im Muster",
     "grep -oE \"v3\\.9\\.989\" --include=*.py . | head"),
    ("Push mit Unterbefehl in Klammern",
     "SHA=$(git rev-parse HEAD) && git push origin \"$SHA:main\" | tail -1"),
    ("Riegel einsammeln",
     "cd /c/repos/epkolar-app && python -m pytest tests/ -q"),
    ("Datei lesen",
     "sed -n '5336,5360p' index.html | cut -c1-260"),
]


def test_die_echte_arbeit_laeuft_durch():
    """🔴 Der wichtigere Teil. Ein Haken, der ALLES anhaelt, besteht jede
    Koederprobe und wird nach dem zweiten Fehlalarm abgeschaltet."""
    angehalten = []
    for name, befehl in ECHTE_ARBEIT:
        arten = _arten(befehl)
        if arten:
            angehalten.append((name, arten))
    assert not angehalten, (
        "%d Befehle, die am 29.09. richtig gelaufen sind, wuerden "
        "angehalten:\n%s\n"
        "  Ein Haken, der bei richtiger Arbeit im Weg steht, wird "
        "abgeschaltet - und\n  dann schuetzt er gar nichts mehr."
        % (len(angehalten),
           "\n".join("   %s -> %s" % a for a in angehalten)))


def test_die_eigene_eichung_des_hakens_besteht():
    schief = H.eichen()
    assert not schief, (
        "Der Haken besteht seine eigene Eichung nicht:\n%s"
        % "\n".join("   " + s for s in schief))


def test_die_ausgabe_ueberlebt_eine_cp1252_konsole():
    """🔴 DARAN IST DER ERSTE ROHRTEST GESCHEITERT, und zwar am Haken selbst.

    Die Begruendung traegt ein rotes Zeichen. Auf Windows ist die
    Standardausgabe cp1252, dort ist es nicht darstellbar - der Haken stuerzte
    mit `UnicodeEncodeError` ab, gab nichts aus und meldete Rueckgabe 1.

    **Ein Haken, der abstuerzt, schuetzt nicht - er stoert nur.** Und die
    Eichung hat es nicht gesehen, weil sie die Deny-Ausgabe gar nicht
    erzeugt: sie prueft die ENTSCHEIDUNG, nicht das AUSSCHREIBEN. Genau
    deshalb steht diese Probe hier und nicht dort.

    Gemessen wird, dass die ausgeschriebene Zeile reines ASCII ist - dann
    geht sie durch jede Konsole, unabhaengig von deren Zeichensatz.
    """
    import io
    import json as _json
    alt_in, alt_out = sys.stdin, sys.stdout
    try:
        sys.stdin = io.StringIO(_json.dumps(
            {"tool_input": {"command": UNFALL_BACKTICK}}))
        gefangen = io.StringIO()
        sys.stdout = gefangen
        H.main([])
    finally:
        sys.stdin, sys.stdout = alt_in, alt_out
    roh = gefangen.getvalue()
    assert roh.strip(), "Der Haken schreibt gar nichts aus."
    try:
        roh.encode("cp1252")
    except UnicodeEncodeError as e:
        raise AssertionError(
            "Die Ausgabe des Hakens ist auf einer cp1252-Konsole nicht "
            "schreibbar: %s\n  Der Haken stuerzt dort ab, statt zu "
            "schuetzen. `ensure_ascii=True` benutzen." % e)
    d = _json.loads(roh)
    assert d["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_ein_kaputter_haken_laesst_DURCH_statt_zu_blockieren():
    """🔴 Die Richtung, in die ein Haken fehlschlagen muss.

    Bekommt er Unsinn statt JSON, darf er die Arbeit nicht anhalten. Ein
    Haken, der bei einem eigenen Fehler alles blockiert, legt die Sitzung
    lahm - und das ist schlimmer als der Fehler, den er verhueten soll.
    """
    import io
    alt = sys.stdin
    try:
        sys.stdin = io.StringIO("kein json")
        assert H.main([]) == 0
        sys.stdin = io.StringIO('{"tool_input":{}}')
        assert H.main([]) == 0
    finally:
        sys.stdin = alt
