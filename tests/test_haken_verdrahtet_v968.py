# -*- coding: utf-8 -*-
"""Die Haken sind verdrahtet, und jeder einzelne MISST auch etwas.

🔴 WARUM ES DIESEN RIEGEL GIBT
Die Haken in `.claude/settings.json` sind seit dem 25.09.2026 konfiguriert und
haben in ueber dreissig Commits kein einziges Mal gefeuert. Die Ursache ist
NICHT die Konfiguration - der git-add-Haken verweigert `git add -A` korrekt,
wenn man ihm die Eingabe direkt gibt. Die Ursache ist der Beobachter: er
ueberwacht nur Verzeichnisse, in denen beim Sitzungsstart schon eine
Einstellungsdatei lag. **Sebastian muss einmal `/hooks` oeffnen**; das kann
kein Lauf selbst tun, weil das Menue den Zug beendet.

Dieser Riegel kann den Beobachter nicht ersetzen. Er stellt sicher, dass
alles, was der Mensch mit einem `/hooks` scharf schalten wuerde, auch
tatsaechlich da ist und wirkt:

  1. Jeder Haken in der Konfiguration zeigt auf eine vorhandene Datei.
  2. Jedes Hakenskript im Ordner ist auch verdrahtet - ein Skript, das in
     keiner Konfiguration steht, ist eine Attrappe. Genau diese Form hatte
     `scripts/md5_geschuetzt.py`: fertig gebaut, in keiner Kette, nie gelaufen.
  3. Jeder Haken meldet bei seinem Koeder-Fall und SCHWEIGT bei der
     Gegenprobe. Ein Haken, der alles verweigert, ist so nutzlos wie einer,
     der nie anschlaegt - und beide sehen von aussen gleich aus.

Die Faelle unter 3. laufen ueber die Selbstproben der Haken selbst
(`scripts/hook_shell_fallen_probe.py`), damit es die Koeder nur EINMAL gibt.
"""
import io
import json
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KONF = os.path.join(WURZEL, ".claude", "settings.json")
SKRIPTE = os.path.join(WURZEL, "scripts")


def _konf():
    return json.loads(io.open(KONF, encoding="utf-8", newline="").read())


def _verdrahtete():
    """Die Dateinamen aller Haken, die in der Konfiguration stehen."""
    aus = []
    for ereignis, gruppen in (_konf().get("hooks") or {}).items():
        for g in gruppen:
            for h in g.get("hooks", []):
                b = h.get("command", "")
                for stueck in b.replace("\\", "/").split("/"):
                    if stueck.startswith("hook_") and stueck.endswith(".py\""):
                        aus.append((ereignis, g.get("matcher"),
                                    stueck.rstrip("\"")))
                    elif stueck.startswith("hook_") and stueck.endswith(".py"):
                        aus.append((ereignis, g.get("matcher"), stueck))
    return aus


def test_die_konfiguration_ist_lesbar_und_nicht_leer():
    """Eine kaputte settings.json schaltet STILL alle Einstellungen ab."""
    k = _konf()
    haken = [h for g in (k.get("hooks") or {}).values()
             for gr in g for h in gr.get("hooks", [])]
    assert len(haken) >= 4, (
        "\U0001F534 Nur %d Haken in .claude/settings.json. Erwartet sind "
        "mindestens vier:\n"
        "  index.html-Tore, CRLF-Riegel, git-add-Riegel, Shell-Fallen."
        % len(haken))
    for h in haken:
        assert h.get("type") == "command" and h.get("command"), \
            "\U0001F534 Ein Haken ohne Befehl: %r" % h


def test_jeder_verdrahtete_haken_existiert():
    fehlt = [(e, m, n) for e, m, n in _verdrahtete()
             if not os.path.exists(os.path.join(SKRIPTE, n))]
    assert not fehlt, (
        "\U0001F534 Diese Haken stehen in der Konfiguration, aber die Datei "
        "fehlt: %r\n"
        "  Ein Haken, der ins Leere zeigt, meldet nichts - und sieht von "
        "aussen aus wie einer,\n  der nichts zu melden hat." % fehlt)


def test_jedes_hakenskript_ist_auch_verdrahtet():
    """\U0001F534 Die Attrappenform: gebaut, aber in keiner Konfiguration.

    Genau so lag `scripts/md5_geschuetzt.py` da - fertig, mit Kopfzeile
    'Gate 5', und in keiner Kette. Es ist nie gelaufen.
    """
    da = {f for f in os.listdir(SKRIPTE)
          if f.startswith("hook_") and f.endswith(".py")
          and not f.endswith("_probe.py")}
    drin = {n for _, _, n in _verdrahtete()}
    waisen = sorted(da - drin)
    assert not waisen, (
        "\U0001F534 Diese Hakenskripte stehen in KEINER Konfiguration: %s\n"
        "  Entweder verdrahten oder loeschen. Ein ungenutztes Hakenskript ist "
        "eine Attrappe:\n"
        "  es sieht nach Absicherung aus und misst nichts." % waisen)


def _probe(name):
    p = os.path.join(SKRIPTE, name)
    assert os.path.exists(p), "\U0001F534 Selbstprobe %s fehlt." % name
    r = subprocess.run([sys.executable, p], capture_output=True, text=True,
                       encoding="utf-8", cwd=WURZEL)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def test_shell_fallen_haken_trifft_und_schweigt():
    """Koeder UND Gegenprobe - die Selbstprobe des Hakens selbst."""
    rc, aus = _probe("hook_shell_fallen_probe.py")
    assert rc == 0, (
        "\U0001F534 Die Selbstprobe des Shell-Fallen-Hakens ist rot:\n%s"
        % aus[-1400:])
    assert "gruen" in aus, "\U0001F534 Die Selbstprobe hat nichts gemeldet."


def test_git_add_haken_verweigert_und_schweigt():
    """Direkt am Haken, beide Richtungen.

    Ohne die zweite Richtung waere ein Haken gruen, der JEDES `git add`
    verweigert - und der waere schlimmer als gar keiner.
    """
    p = os.path.join(SKRIPTE, "hook_git_add_riegel.py")

    def frag(befehl):
        r = subprocess.run(
            [sys.executable, p],
            input=json.dumps({"tool_name": "Bash",
                              "tool_input": {"command": befehl}}),
            capture_output=True, text=True, encoding="utf-8")
        assert r.returncode == 0, "\U0001F534 Haken abgestuerzt: %s" % r.stderr
        return "deny" in (r.stdout or "")

    assert frag("git add -A"), \
        "\U0001F534 `git add -A` wird NICHT verweigert."
    assert frag("git add -u"), \
        "\U0001F534 `git add -u` wird NICHT verweigert."
    assert not frag("git add index.html sw.js"), (
        "\U0001F534 Die benannte Form wird verweigert - dann verweigert der "
        "Haken alles,\n  und er wird bei der ersten Gelegenheit abgeschaltet.")
    assert not frag("python -m pytest tests/ -q"), \
        "\U0001F534 Ein Befehl ohne `git add` wird verweigert."


def test_crlf_haken_meldet_und_schweigt():
    """Der Haken gegen die Falle, die 19 Dateien still auf CRLF gestellt hat."""
    p = os.path.join(SKRIPTE, "hook_python_crlf.py")
    import tempfile

    def frag(inhalt):
        d = tempfile.mkdtemp()
        f = os.path.join(d, "probe.py")
        io.open(f, "w", encoding="utf-8", newline="").write(inhalt)
        r = subprocess.run(
            [sys.executable, p],
            input=json.dumps({"tool_input": {"file_path": f}}),
            capture_output=True, text=True, encoding="utf-8")
        os.remove(f)
        os.rmdir(d)
        assert r.returncode == 0, "\U0001F534 Haken abgestuerzt: %s" % r.stderr
        return bool((r.stdout or "").strip())

    assert frag("io.open(p, 'w').write(s)\n"), \
        "\U0001F534 Ein Schreibaufruf ohne newline='' wird NICHT gemeldet."
    assert not frag("io.open(p, 'w', encoding='utf-8', newline='').write(s)\n"), (
        "\U0001F534 Ein Aufruf MIT newline='' wird gemeldet - dann meldet der "
        "Haken alles.")
    assert not frag("t = io.open(p, encoding='utf-8').read()\n"), \
        "\U0001F534 Ein reines Lesen wird gemeldet."
