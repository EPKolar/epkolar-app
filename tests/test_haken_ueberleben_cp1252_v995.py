# -*- coding: utf-8 -*-
"""Jeder Haken muss seine eigene Meldung AUSSPRECHEN koennen.

🔴 DER BEFUND, DER DIESEN RIEGEL AUSGELOEST HAT: `hook_python_crlf.py` ist am
30.09.2026 an seiner EIGENEN Meldung abgestuerzt. Die Windows-Konsole laeuft
auf cp1252; das 🔴 im Text liess sich dort nicht schreiben,
`json.dumps(..., ensure_ascii=False)` gab es roh aus, und der Haken endete mit

    UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f534'

statt mit einer Warnung. **Ein Haken, der beim Melden stirbt, meldet nie** -
und weil ein abgestuerzter Haken den Lauf nicht anhaelt, sieht das von aussen
aus wie „nichts gefunden". Genau die Form, vor der er schuetzen soll.

🔴 **ZWEI VON VIER HAKEN HATTEN DIE VORKEHRUNG, EINER NICHT.** Die Regel war
notiert, in zwei Skripten umgesetzt - und beim dritten wieder nicht. Deshalb
misst dieser Riegel nicht EINEN Haken, sondern die KLASSE: jeder verdrahtete
Haken wird mit seinem eigenen Ausloeser unter cp1252 gefahren, und wer dabei
stirbt oder schweigt, faellt auf.

**Gemessen wird die WIRKUNG, nicht die Anwesenheit einer Zeile.** Ein
`reconfigure`-Aufruf im Quelltext beweist nichts - er koennte nach der ersten
Ausgabe stehen, in einem Zweig liegen, der nicht laeuft, oder in einem
Kommentar. Hier wird der Haken wirklich gestartet, mit
`PYTHONIOENCODING=cp1252`, und seine Ausgabe gelesen.

🔴 **DIE TAFEL IST EINE SPERRE:** jeder verdrahtete Haken MUSS hier einen
Ausloeser haben. Kommt ein Haken dazu und niemand traegt ihn ein, wird dieser
Riegel rot - statt den neuen Haken stillschweigend ungemessen zu lassen.
"""
import io
import json
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KONF = os.path.join(WURZEL, ".claude", "settings.json")
SKRIPTE = os.path.join(WURZEL, "scripts")

# Je Haken: der Ausloeser, der ihn zum SPRECHEN bringt. Ein Haken, der bei
# dieser Eingabe schweigt, ist hier so verdaechtig wie einer, der abstuerzt -
# dann stimmt der Ausloeser nicht mehr mit dem Haken ueberein.
AUSLOESER = {
    "hook_python_crlf.py": {
        "tool_name": "Write",
        "tool_input": {"file_path": "__PYDATEI__"}},
    # 🔴 MEIN ERSTER AUSLOESER WAR FALSCH, nicht der Haken: `\\` in EINFACHEN
    # Anfuehrungszeichen ist keine Falle - dort bleibt alles stehen, und der
    # Haken liest den Anfuehrungszustand richtig mit. Er hat zu Recht
    # geschwiegen. Jetzt steht hier Fall A1 aus seiner eigenen, geeichten
    # Selbstprobe (scripts/hook_shell_fallen_probe.py).
    "hook_shell_fallen.py": {
        "tool_name": "Bash",
        "tool_input": {"command": "git push origin HEAD:main"}},
    "hook_git_add_riegel.py": {
        "tool_name": "Bash",
        "tool_input": {"command": "git add -A"}},
    "hook_index_riegel.py": None,   # siehe test_der_index_haken_ist_ausgenommen
}

# Eine Python-Datei, die ohne newline='' schreibt - der Ausloeser fuer den
# CRLF-Haken.
KOEDER_PY = (
    "# -*- coding: utf-8 -*-\n"
    "import io\n"
    "io.open('x.txt', 'w', encoding='utf-8').write('hallo')\n")


def _verdrahtete():
    k = json.loads(io.open(KONF, encoding="utf-8", newline="").read())
    aus = set()
    for _, gruppen in (k.get("hooks") or {}).items():
        for g in gruppen:
            for h in g.get("hooks", []):
                for stueck in h.get("command", "").replace("\\", "/").split("/"):
                    s = stueck.strip('"')
                    if s.startswith("hook_") and s.endswith(".py"):
                        aus.add(s)
    return aus


def test_die_tafel_deckt_jeden_verdrahteten_haken():
    """🔴 Die Sperre: ein neuer Haken darf nicht ungemessen durchrutschen."""
    fehlt = sorted(_verdrahtete() - set(AUSLOESER))
    assert not fehlt, (
        "\U0001F534 Diese verdrahteten Haken haben hier KEINEN Ausloeser: "
        "%s\n  Ohne Eintrag wird nicht gemessen, ob sie ihre eigene Meldung "
        "aussprechen koennen -\n  und ein Haken, der beim Melden stirbt, "
        "meldet nie." % fehlt)
    tot = sorted(set(AUSLOESER) - _verdrahtete())
    assert not tot, (
        "\U0001F534 Diese Eintraege zeigen auf Haken, die in KEINER "
        "Konfiguration stehen: %s\n  Der Riegel misst dann etwas, das nie "
        "laeuft." % tot)


def _fahre(name, eingabe, tmp_path):
    """Den Haken unter cp1252 starten und seine Ausgabe zurueckgeben."""
    p = os.path.join(SKRIPTE, name)
    roh = json.dumps(eingabe)
    if "__PYDATEI__" in roh:
        py = tmp_path / "koeder_ohne_newline.py"
        io.open(str(py), "w", encoding="utf-8", newline="").write(KOEDER_PY)
        roh = roh.replace("__PYDATEI__", str(py).replace("\\", "\\\\"))
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, p], input=roh, capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       cwd=WURZEL, env=umg, timeout=300)
    return r


def test_jeder_haken_spricht_unter_cp1252(tmp_path):
    kaputt = []
    stumm = []
    for name in sorted(_verdrahtete()):
        eingabe = AUSLOESER.get(name)
        if eingabe is None:
            continue
        r = _fahre(name, eingabe, tmp_path)
        if "UnicodeEncodeError" in (r.stderr or "") or r.returncode != 0:
            kaputt.append((name, (r.stderr or "").strip().splitlines()[-1:]))
            continue
        aus = (r.stdout or "").strip()
        if not aus:
            stumm.append(name)
            continue
        try:
            j = json.loads(aus.splitlines()[-1])
        except ValueError:
            kaputt.append((name, ["Ausgabe ist kein JSON: %s" % aus[:120]]))
            continue
        spricht = bool(j.get("systemMessage")) or bool(
            (j.get("hookSpecificOutput") or {}).get("permissionDecisionReason"))
        if not spricht:
            stumm.append(name)
    assert not kaputt, (
        "\U0001F534 Diese Haken sterben an ihrer EIGENEN Meldung, sobald die "
        "Konsole cp1252\n  spricht - also auf jedem gewoehnlichen "
        "Windows-Fenster: %s\n"
        "  Der Lauf haelt dabei NICHT an. Von aussen sieht ein abgestuerzter "
        "Haken aus wie\n  'nichts gefunden' - genau die Form, vor der er "
        "schuetzen soll.\n"
        "  Kur: `sys.stdout.reconfigure(encoding=\"utf-8\", "
        "errors=\"replace\")` VOR der ersten\n"
        "  Ausgabe UND `ensure_ascii=True` im json.dumps. Beides, nicht "
        "eines von beiden." % kaputt)
    assert not stumm, (
        "\U0001F534 Diese Haken schweigen bei ihrem eigenen Ausloeser: %s\n"
        "  Entweder trifft der Ausloeser nicht mehr (dann gehoert die Tafel "
        "hier berichtigt)\n  oder der Haken hat aufgehoert zu greifen. "
        "Beides ist ein Befund." % stumm)


def test_koeder_ein_haken_ohne_vorkehrung_wuerde_auffallen(tmp_path):
    """🔴 Die Selbstprobe: der Riegel muss einen kaputten Haken SEHEN.

    Ohne sie belegt ein gruener Lauf nichts - er koennte auch gruen sein,
    weil das Messverfahren selbst nicht greift (falsche Umgebungsvariable,
    falsch gelesene Ausgabe, abgefangener Fehler).
    """
    p = tmp_path / "hook_koeder.py"
    io.open(str(p), "w", encoding="utf-8", newline="").write(
        "# -*- coding: utf-8 -*-\n"
        "import json, sys\n"
        "sys.stdin.read()\n"
        "print(json.dumps({'systemMessage': '\\U0001F534 rot'},"
        " ensure_ascii=False))\n")
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, str(p)], input="{}",
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=umg, timeout=120)
    assert r.returncode != 0 and "UnicodeEncodeError" in (r.stderr or ""), (
        "Der Koeder ist NICHT abgestuerzt. Dann misst dieser Riegel die "
        "cp1252-Falle nicht -\n  und ein gruener Lauf bedeutet nichts. "
        "Vermutlich wirkt PYTHONIOENCODING nicht\n  (PYTHONUTF8 gesetzt? "
        "Konsole schon auf utf-8?).")


def test_der_index_haken_ist_ausgenommen_und_warum():
    """🔴 Eine AUSNAHME gehoert benannt, nicht weggelassen.

    `hook_index_riegel.py` faehrt nach jedem Schreiben auf index.html die
    beiden Tore - das dauert Minuten und braucht eine echte 3,7-MB-Datei.
    Ihn hier zu starten hiesse, die Torkette in der Torkette zu fahren.
    Seine Ausgabe ist dafuer schon ASCII, und das wird hier gemessen.
    """
    t = io.open(os.path.join(SKRIPTE, "hook_index_riegel.py"),
                encoding="utf-8", newline="").read()
    assert "ensure_ascii=False" not in t, (
        "\U0001F534 hook_index_riegel.py gibt Nicht-ASCII roh aus. Weil er "
        "hier nicht gefahren\n  werden kann, ist das die einzige Messung, die "
        "bleibt - und sie ist jetzt rot.")
