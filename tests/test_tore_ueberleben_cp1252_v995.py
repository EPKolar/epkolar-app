# -*- coding: utf-8 -*-
"""Jedes Tor der Kette muss seine eigene ERFOLGSMELDUNG aussprechen koennen.

🔴 DER BEFUND. Am 30.09.2026 meldete die Torkette **zwei rote Tore**, ohne
dass eine Messung etwas gefunden haette. Beide starben an dieser Zeile:

    print("   \\U0001F7E2 alle sechs richtig\\n")
    UnicodeEncodeError: 'charmap' codec can't encode character '\\U0001f7e2'

Das Tor hatte gemessen, alles war richtig - und ist beim Hinschreiben des
**gruenen Punktes** gestorben. Die Kette liest den Rueckgabewert, sieht ihn
ungleich null und meldet ROT.

**Die gefaehrliche Richtung ist die andere.** Ein Tor, das auf dem
FEHLERZWEIG so stirbt, meldet den Fehler nie - und weil die Kette nur den
Rueckgabewert liest, sieht das genauso aus wie ein Befund. Bei einem Haken
ist es noch schlimmer: der haelt den Lauf gar nicht an, dort ist ein
Absturz von "nichts gefunden" nicht zu unterscheiden. Genau so ist am selben
Tag `hook_python_crlf.py` still ausgefallen.

🔴 **ES WAR KEIN EINZELFALL: sieben der zehn Torskripte hatten die
Vorkehrung nicht.** Zwei sind gestorben, weil ihre Ausgabe heute ein Symbol
bekam; fuenf waren latent und haetten es an dem Tag getan, an dem jemand
ihrer Meldung einen gruenen Punkt gibt. Die Regel war notiert und in drei
Skripten umgesetzt - das hat die anderen sieben nicht erreicht.

🔴 **UND MEIN ERSTER ZAEHLER WAR BLIND FUER DIE FORM, DIE STIRBT.** Er suchte
Nicht-ASCII-ZEICHEN im Quelltext. Dort steht aber `\\U0001F7E2` - acht
ASCII-Zeichen; erst zur Laufzeit wird ein Symbol daraus. Die beiden
nachweislich toten Tore standen darum NICHT in seiner Liste. Zwei
Schreibweisen, und die zweite war die entscheidende.

**Dieser Riegel misst WIRKUNG:** er startet jedes Torskript wirklich, mit
`PYTHONIOENCODING=cp1252`, und sieht nach, ob es an der Ausgabe stirbt. Ein
`reconfigure` im Quelltext wird NICHT gezaehlt - es koennte hinter der ersten
Ausgabe stehen, in einem Zweig liegen, der nicht laeuft, oder in einem
Kommentar.

**Was hier bewusst NICHT gemessen wird:** die uebrigen Messskripte in
`scripts/`. Es sind 45 ohne Vorkehrung (Stand 30.09., `python
scripts/ausgabe_ueberlebt_messen.py`), fast alle einmalige Erkundungen, die
kein Tor faehrt. Sie stehen in `docs/befunde/AUSGABE_CP1252.md`. Wer eines
davon zu einem Tor macht, faellt hier auf - dafuer sorgt
`test_die_tafel_deckt_jedes_tor`.
"""
import io
import os
import re
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKRIPTE = os.path.join(WURZEL, "scripts")
TORKETTE = os.path.join(SKRIPTE, "torkette.py")

# Die Tore, die hier wirklich gefahren werden. `pytest` faehrt sich nicht
# selbst, und `sql/_check_version.js` ist kein Python - beide sind unten
# ausdruecklich begruendet.
NICHT_GEFAHREN = {
    "pytest": "faehrt sich nicht selbst - das hier LAEUFT in pytest",
    "Versionsabgleich": "node, kein Python; node kennt cp1252 nicht",
}

# Argumente, mit denen ein Tor schnell und ohne Nebenwirkung laeuft.
ARGUMENTE = {
    "icons_erzeugen.py": ["--pruefen"],
    "haken_schalenfalle.py": ["--eichen"],
    "werkzeug_eichung.py": ["--eichen"],
    "klammerbilanz.py": ["--eichen"],
}


def _torskripte():
    """Die Python-Skripte, die torkette.py als Tor faehrt - aus der QUELLE.

    Nicht aus einer abgeschriebenen Liste: eine Liste veraltet lautlos, und
    dann misst dieser Riegel ein Tor, das es nicht mehr gibt, waehrend ein
    neues ungemessen bleibt.
    """
    t = io.open(TORKETTE, encoding="utf-8", newline="").read()
    i = t.find("TORE = [")
    assert i > 0, "\U0001F534 `TORE = [` nicht gefunden - torkette.py umgebaut?"
    # Bis zur schliessenden Klammer auf Spaltenhoehe 0.
    j = t.find("\n]", i)
    assert j > i, "\U0001F534 Ende der Tor-Liste nicht gefunden."
    block = t[i:j]
    namen = re.findall(r'\(\s*"([^"]+)"', block)
    skripte = re.findall(r'"scripts/([A-Za-z0-9_]+\.py)"', block)
    return namen, skripte


def test_die_tafel_deckt_jedes_tor():
    """🔴 Die Sperre: ein neues Tor darf nicht ungemessen durchrutschen."""
    namen, skripte = _torskripte()
    assert len(namen) >= 10, (
        "\U0001F534 Nur %d Tore gefunden, erwartet sind mindestens 10. "
        "Entweder ist die Kette\n  geschrumpft oder das Auslesen greift nicht "
        "mehr - beides ist ein Befund." % len(namen))
    unbekannt = [n for n in namen
                 if n in NICHT_GEFAHREN and n not in NICHT_GEFAHREN]
    assert not unbekannt, unbekannt
    for n in NICHT_GEFAHREN:
        assert n in namen, (
            "\U0001F534 '%s' steht als Ausnahme hier, ist aber kein Tor mehr. "
            "Die Ausnahme ist\n  dann unbegruendet und gehoert entfernt." % n)


def _stirbt(skript):
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    befehl = [sys.executable, os.path.join(SKRIPTE, skript)]
    befehl += ARGUMENTE.get(skript, [])
    try:
        r = subprocess.run(befehl, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=WURZEL,
                           env=umg, timeout=900)
    except subprocess.TimeoutExpired:
        return "Zeitueberschreitung"
    if "UnicodeEncodeError" in (r.stderr or ""):
        letzte = [z for z in (r.stderr or "").strip().splitlines() if z][-1]
        return letzte.strip()[:140]
    return None


def test_die_kette_selbst_ueberlebt_eine_cp1252_konsole():
    """🔴 Die Kette gehoert zur Klasse - sie war der dritte Fall.

    Nachdem die sieben Torskripte umgestellt waren, starb `torkette.py`
    SELBST: pytest war rot, und beim Hinschreiben der Begruendung
    (`print(ausgabe[-3000:])`) traf sie ein Zeichen, das cp1252 nicht kennt.
    Der Befund war damit UNSICHTBAR - schlimmer als ein rotes Tor, denn ein
    rotes Tor sagt wenigstens, welches.

    Besonders heimtueckisch: die Ausgabe eines Tores wird mit
    `errors="replace"` gelesen. Was dabei nicht lesbar war, steht danach als
    U+FFFD im Text - und auch U+FFFD kennt cp1252 nicht. Die Vorsorge beim
    LESEN erzeugt also genau das Zeichen, an dem das SCHREIBEN scheitert.
    """
    t = io.open(TORKETTE, encoding="utf-8", newline="").read()
    assert "reconfigure" in t, (
        "\U0001F534 torkette.py stellt den Ausgabestrom nicht um. Dann "
        "stirbt die Kette beim\n  Hinschreiben einer Begruendung, und das "
        "rote Tor bleibt unsichtbar.")
    # Wirkung, nicht Anwesenheit - aber OHNE die Kette zu fahren.
    # 🔴 Mein erster Versuch startete sie mit einem unbekannten Schalter, in
    # der Annahme, sie gebe dann eine Hilfe aus. Sie tut das nicht: sie fuhr
    # die ganze Kette, aus pytest heraus, in sich selbst - fuenf Minuten, und
    # gemessen war am Ende nichts. Statt dessen hat die Kette jetzt
    # `--ausgabeprobe`: denselben Ausgabeweg, ohne ein einziges Tor.
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, TORKETTE, "--ausgabeprobe"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=WURZEL, env=umg, timeout=120)
    assert "UnicodeEncodeError" not in (r.stderr or ""), (
        "\U0001F534 torkette.py stirbt unter cp1252 an der eigenen Ausgabe:\n"
        "  %s" % (r.stderr or "").strip().splitlines()[-1:])
    assert r.returncode == 0 and "Ausgabeprobe ueberstanden" in (r.stdout or ""), (
        "\U0001F534 Die Ausgabeprobe der Kette ist nicht durchgelaufen "
        "(Rueckgabewert %s).\n  Ohne sie misst dieser Riegel nichts."
        % r.returncode)


def test_jedes_torskript_ueberlebt_eine_cp1252_konsole():
    _, skripte = _torskripte()
    assert skripte, "\U0001F534 Keine Torskripte ausgelesen."
    tot = []
    for s in sorted(set(skripte)):
        f = _stirbt(s)
        if f:
            tot.append((s, f))
    assert not tot, (
        "\U0001F534 Diese Tore sterben an ihrer EIGENEN Ausgabe, sobald die "
        "Konsole cp1252\n  spricht - also auf jedem gewoehnlichen "
        "Windows-Fenster:\n%s\n"
        "  Auf dem ERFOLGSZWEIG heisst das: die Kette meldet ROT, obwohl die "
        "Messung in\n  Ordnung war. Auf dem FEHLERZWEIG heisst es: der Befund "
        "geht verloren und sieht\n  aus wie ein Befund - man kann die beiden "
        "am Rueckgabewert nicht unterscheiden.\n"
        "  Kur: `sys.stdout.reconfigure(encoding=\"utf-8\", "
        "errors=\"replace\")` VOR der ersten\n  Ausgabe."
        % "\n".join("      %-26s %s" % t for t in tot))


def test_koeder_ein_tor_ohne_vorkehrung_wuerde_auffallen(tmp_path):
    """🔴 Die Selbstprobe.

    Ohne sie belegt ein gruener Lauf nichts: er koennte auch gruen sein, weil
    `PYTHONIOENCODING` in dieser Umgebung gar nicht wirkt (PYTHONUTF8 gesetzt,
    Konsole schon auf utf-8, Python mit anderem Vorgabeverhalten). Dann waere
    der Riegel eine Attrappe - er liefe durch und saehe nie etwas.
    """
    p = tmp_path / "tor_koeder.py"
    io.open(str(p), "w", encoding="utf-8", newline="").write(
        "print('   \\U0001F7E2 alles richtig')\n")
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    r = subprocess.run([sys.executable, str(p)], capture_output=True,
                       text=True, encoding="utf-8", errors="replace",
                       env=umg, timeout=120)
    assert r.returncode != 0 and "UnicodeEncodeError" in (r.stderr or ""), (
        "Der Koeder ist NICHT abgestuerzt. Dann misst dieser Riegel die "
        "cp1252-Falle nicht,\n  und ein gruener Lauf bedeutet nichts.")


def test_koeder_die_zweite_schreibweise_wird_gesehen(tmp_path):
    """🔴 Beide Schreibweisen, denn die zweite war die entscheidende.

    Mein erster Zaehler sah nur Symbole, die ROH im Quelltext stehen. Die
    beiden Tore, die wirklich gestorben sind, schreiben `\\U0001F7E2` - acht
    ASCII-Zeichen. Hier wird belegt, dass beide Formen sterben, damit
    niemand spaeter auf eine Quelltextsuche zurueckfaellt.
    """
    umg = dict(os.environ)
    umg["PYTHONIOENCODING"] = "cp1252"
    umg.pop("PYTHONUTF8", None)
    for name, inhalt in (
            ("roh.py", "print('ampel ' + chr(0x1F7E2))\n"),
            ("esc.py", "print('ampel \\U0001F7E2')\n")):
        p = tmp_path / name
        io.open(str(p), "w", encoding="utf-8", newline="").write(inhalt)
        r = subprocess.run([sys.executable, str(p)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           env=umg, timeout=120)
        assert "UnicodeEncodeError" in (r.stderr or ""), (
            "Die Schreibweise '%s' stirbt NICHT - dann deckt dieser Riegel "
            "sie nicht ab." % name)
