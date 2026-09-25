# -*- coding: utf-8 -*-
"""v3.9.931 - die beiden Hooks muessen WIRKEN, nicht dastehen.

WOZU
────
Sebastian: "bau dir sauber riegel, tore und hooks, will fehler vermeiden".
Die zwei Hooks in `.claude/settings.json` sind nach der gemessenen Haeufigkeit
meiner eigenen Fehler gebaut:

  hook_index_riegel     index.html hat keinen Bauschritt. Ein misslungener
                        Ersatz faellt erst auf, wenn die Seite nicht laedt.
  hook_git_add_riegel   am 25.09.2026 committete ein Lauf 24 Dateien statt 2,
                        weil zwischen `add` und `commit` ein anderer Lauf den
                        Index bestueckte.

WAS DIESER RIEGEL MISST
───────────────────────
Nicht, dass die Hooks EINGETRAGEN sind - das waere wieder Anwesenheit statt
Wirkung, die haeufigste Krankheit der Riegel in diesem Bestand. Gemessen wird:
der Hook wird GEFAHREN und muss bei einem echten Fehler sperren.

DIE KOEDER
──────────
Zwei Stueck, in beide Richtungen:

  * `test_der_index_riegel_laesst_eine_heile_datei_durch` - sperrte er immer,
    waere "er sperrt bei Fehlern" wertlos.
  * `test_erlaubte_git_befehle_gehen_durch` - besonders die Commit-Meldung, die
    die Regel selbst zitiert: genau dieser Satz steht in der Doku dieses Repos,
    und ein Riegel, der auf die blosse Zeichenfolge sieht, macht daraus einen
    Dauer-Fehlalarm. Ein Riegel, der staendig grundlos rot ist, wird
    abgeschaltet - dann schuetzt er gar nichts mehr.
"""
import io
import json
import shutil
import subprocess
import sys

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
EINSTELLUNGEN = WURZEL / ".claude" / "settings.json"
INDEX_HOOK = WURZEL / "scripts" / "hook_index_riegel.py"
GIT_HOOK = WURZEL / "scripts" / "hook_git_add_riegel.py"


def _fahre(skript, nutzlast, cwd=None):
    """Faehrt einen Hook mit der Nutzlast, die Claude Code ihm schickt."""
    r = subprocess.run([sys.executable, str(skript)],
                       input=json.dumps(nutzlast), capture_output=True,
                       text=True, timeout=300, cwd=str(cwd or WURZEL))
    return r.returncode, (r.stdout or "")


def _sperrt(ausgabe):
    if not ausgabe.strip():
        return False
    d = json.loads(ausgabe)
    return (d.get("decision") == "block"
            or d.get("hookSpecificOutput", {}).get("permissionDecision") == "deny")


def _einstellungen():
    return json.loads(io.open(str(EINSTELLUNGEN), encoding="utf-8").read())


# ── Die Verdrahtung: was in settings.json steht, muss laufen ────────────────

def test_beide_hooks_sind_verdrahtet_und_ihre_skripte_existieren():
    d = _einstellungen()
    befehle = []
    for ereignis in ("PostToolUse", "PreToolUse"):
        for gruppe in d["hooks"][ereignis]:
            for h in gruppe["hooks"]:
                befehle.append((ereignis, gruppe["matcher"], h["command"]))
    assert len(befehle) == 2, befehle
    assert any(e == "PostToolUse" and "Edit" in m and "hook_index_riegel" in b
               for e, m, b in befehle), befehle
    assert any(e == "PreToolUse" and m == "Bash" and "hook_git_add_riegel" in b
               for e, m, b in befehle), befehle
    assert INDEX_HOOK.exists() and GIT_HOOK.exists()


def test_der_bash_hook_laeuft_ohne_if_filter():
    """Ein `if`-Filter waere ein Loch, kein Sparbeitrag.

    `Bash(git add *)` trifft weder `cd x && git add -A` noch
    `git -C pfad add .` - beides sind gaengige Formen. Gemessen kostet der
    Riegel rund 110 ms je Bash-Aufruf; das ist der Preis dafuer, dass er
    ueberhaupt hinsieht.
    """
    h = _einstellungen()["hooks"]["PreToolUse"][0]["hooks"][0]
    assert "if" not in h, (
        "Der Bash-Hook traegt einen if-Filter. Der laesst `cd x && git add -A` "
        "und `git -C pfad add .` durch - der Riegel laeuft dann gar nicht erst "
        "an, und sein Schweigen sieht aus wie ein gruenes Ergebnis.")


# ── Der index.html-Hook ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mini_repo(tmp_path_factory):
    """Ein echtes Mini-Repo: dieselben Skripte, eigene index.html.

    Nur so laesst sich die KAPUTTE Datei messen, ohne die echte anzufassen.
    Alle drei Skripte finden ihre Wurzel ueber das eigene __file__, der Aufbau
    traegt also unveraendert.
    """
    p = tmp_path_factory.mktemp("minirepo")
    (p / "scripts").mkdir()
    for name in ("hook_index_riegel.py", "node_check.py", "_bracket_check.py"):
        shutil.copy(str(WURZEL / "scripts" / name), str(p / "scripts" / name))
    shutil.copy(str(WURZEL / "index.html"), str(p / "index.html"))
    return p


def _nutzlast(pfad):
    return {"tool_name": "Edit", "tool_input": {"file_path": str(pfad)}}


def test_der_index_riegel_laesst_eine_heile_datei_durch(mini_repo):
    """KOEDER. Sperrte er immer, sagte der Fehlerfall darunter nichts aus."""
    code, aus = _fahre(mini_repo / "scripts" / "hook_index_riegel.py",
                       _nutzlast(mini_repo / "index.html"), cwd=mini_repo)
    assert code == 0
    assert not _sperrt(aus), aus


def test_der_index_riegel_sperrt_bei_kaputter_syntax(mini_repo):
    """Die Fehlerform, die diesen Hook ueberhaupt noetig macht."""
    ziel = mini_repo / "index.html"
    heil = io.open(str(ziel), encoding="utf-8", newline="").read()
    try:
        # Eine unbalancierte Klammer in echten Code - nicht in einen Kommentar,
        # sonst misst node --check nichts.
        i = heil.index("APP_VERSION")
        j = heil.index(chr(10), i)
        io.open(str(ziel), "w", encoding="utf-8", newline="").write(
            heil[:j] + " function _kaputt( {" + heil[j:])
        code, aus = _fahre(mini_repo / "scripts" / "hook_index_riegel.py",
                           _nutzlast(ziel), cwd=mini_repo)
        assert _sperrt(aus), "Kaputte Syntax kam durch! Ausgabe: %r" % aus[:400]
        assert "node_check" in aus or "bracket" in aus, aus[:400]
    finally:
        io.open(str(ziel), "w", encoding="utf-8", newline="").write(heil)


def test_der_index_riegel_sperrt_bei_datenverlust(mini_repo):
    """Am 29.08.2026 kuerzte ein Abbruch die Datei auf 0 Bytes - und BEIDE
    Tore meldeten gruen, weil eine leere Datei fehlerfrei parst und
    ausgeglichene Klammern hat. Seither tragen beide eine
    Lebenszeichen-Schranke; hier wird sie gefahren."""
    ziel = mini_repo / "index.html"
    heil = io.open(str(ziel), encoding="utf-8", newline="").read()
    try:
        io.open(str(ziel), "w", encoding="utf-8", newline="").write("")
        code, aus = _fahre(mini_repo / "scripts" / "hook_index_riegel.py",
                           _nutzlast(ziel), cwd=mini_repo)
        assert _sperrt(aus), "Eine leere index.html kam durch! %r" % aus[:400]
    finally:
        io.open(str(ziel), "w", encoding="utf-8", newline="").write(heil)


def test_der_index_riegel_schweigt_bei_fremden_dateien(mini_repo):
    code, aus = _fahre(mini_repo / "scripts" / "hook_index_riegel.py",
                       _nutzlast(WURZEL / "docs" / "HANDOFF.md"), cwd=mini_repo)
    assert code == 0 and not aus.strip(), aus


def test_der_index_riegel_sperrt_wenn_er_selbst_nicht_messen_kann():
    """Fail-closed. Ein Riegel, der bei EIGENEM Ausfall gruen meldet, ist die
    Fehlerform, die diesen Bestand am haeufigsten getroffen hat: nichts
    gefunden heisst dann 'keine Fehler'."""
    r = subprocess.run([sys.executable, str(INDEX_HOOK)], input="kein json",
                       capture_output=True, text=True, timeout=60)
    assert _sperrt(r.stdout), r.stdout


# ── Der git-add-Hook ───────────────────────────────────────────────────────

VERBOTEN = [
    "git add -A",
    "git add -u",
    "git add .",
    "git add --all",
    "git add --update",
    "git add -Av",                                  # gebuendelt
    "git -C /repo add .",                           # Schalter vor dem Unterbefehl
    "cd /repo && git add -A",                       # hinter einem Glied versteckt
    'git add -A && git commit -m "x"',
]

ERLAUBT = [
    "git add scripts/hook_git_add_riegel.py",
    'git add a.py b.py && git commit -m "zwei Dateien"',
    'git commit -m "REGEL: nie git add -A oder git add ."',   # der Fehlalarm
    "git status",
    "git add docs/ENTSCHEIDUNGEN-OFFEN.md",
    "ls -la",
]


@pytest.mark.parametrize("befehl", VERBOTEN)
def test_verbotene_git_add_formen_werden_verweigert(befehl):
    code, aus = _fahre(GIT_HOOK, {"tool_name": "Bash",
                                  "tool_input": {"command": befehl}})
    assert _sperrt(aus), "kam durch: %r" % befehl


@pytest.mark.parametrize("befehl", ERLAUBT)
def test_erlaubte_git_befehle_gehen_durch(befehl):
    """KOEDER. Verweigerte er alles, sagte die Liste darueber nichts aus.

    Der dritte Fall ist der wichtigste: die Regel selbst steht in
    Commit-Meldungen und in der Doku dieses Repos.
    """
    code, aus = _fahre(GIT_HOOK, {"tool_name": "Bash",
                                  "tool_input": {"command": befehl}})
    assert not _sperrt(aus), "falsch verweigert: %r -> %s" % (befehl, aus[:300])
