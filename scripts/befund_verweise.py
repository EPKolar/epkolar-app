# -*- coding: utf-8 -*-
"""Verweis-Erkennung fuer Messung (3): WER ruft WELCHES Skript wirklich auf?

Drei Fehler der Vorfassungen sind hier ausgebaut:

1. ROHER TEXT.  Eine Suche im rohen Dateitext findet die eigene Begruendung
   im Kommentar. `scripts/torkette.py` nennt in ihrem Docstring
   "npm run verify | tail" und "Kein shell=True" - die erste Fassung meldete
   daraus zwei Befunde, die es nicht gibt.
2. tests/ FEHLTE.  Das vierte Tor der Torkette ist `pytest tests/`. Wer
   tests/ nicht als Startpunkt nimmt, haelt jeden Pruefer fuer verwaist, den
   ein Test als Unterprozess fuehrt.
3. NUR DATEINAMEN.  `tests/test_code_scan_elemente_v959.py` fuehrt
   `scripts/code_scan.py` ueber `import code_scan` - der Dateiname
   "code_scan.py" steht dort nirgends im Code. Wer nur Dateinamen sucht,
   erklaert ein benutztes Modul fuer verwaist.

Ein Verweis gilt hier, wenn er KOMMENTARBLIND in einer der beiden Formen
auftritt:
   FORM S  der Dateiname steht in einer echten Zeichenkette
           (Unterprozess, Path(), open())
   FORM M  das Modul wird importiert (import X / from X import ...)

Aufruf:
    python scripts/befund_verweise.py            Bericht
    python scripts/befund_verweise.py --koeder   Selbstprobe
"""
import ast
import io
import os
import re
import sys
import tempfile
import tokenize

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDUNGEN = (".py", ".js", ".mjs", ".cjs", ".ps1")
AUS = {"node_modules", "__pycache__", "_archiv", "_backups", ".git",
       ".pytest_cache", "screenshots", "preview"}


def lies(p):
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _docstring_ids(baum):
    ids = set()
    for k in ast.walk(baum):
        if isinstance(k, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            if k.body and isinstance(k.body[0], ast.Expr) \
                    and isinstance(k.body[0].value, ast.Constant) \
                    and isinstance(k.body[0].value.value, str):
                ids.add(id(k.body[0].value))
    return ids


def verweise_py(pfad):
    """(Zeichenketten-Namen, importierte Modulnamen) - kommentarblind.

    Kommentare fallen weg, weil der Syntaxbaum sie nicht enthaelt.
    Docstrings werden ausdruecklich uebersprungen.
    """
    quelle = lies(pfad)
    try:
        baum = ast.parse(quelle)
    except SyntaxError:
        return set(), set()
    docs = _docstring_ids(baum)
    namen, module = set(), set()
    for k in ast.walk(baum):
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            if id(k) in docs:
                continue
            for stueck in re.split(r"[\\/\s]+", k.value):
                if stueck.endswith(ENDUNGEN):
                    namen.add(stueck)
        elif isinstance(k, ast.Import):
            for a in k.names:
                module.add(a.name.split(".")[-1])
                module.add(a.name)
        elif isinstance(k, ast.ImportFrom):
            if k.module:
                module.add(k.module.split(".")[-1])
                module.add(k.module)
            for a in k.names:
                module.add(a.name)
    return namen, module


def verweise_text(pfad):
    """Fuer .js/.mjs/.cjs/.ps1: Blockkommentare und Zeilenkommentare weg."""
    q = lies(pfad)
    if pfad.endswith((".js", ".mjs", ".cjs")):
        q = re.sub(r"/\*[\s\S]*?\*/", "", q)
        q = "\n".join(re.sub(r"//.*$", "", z) for z in q.splitlines())
    elif pfad.endswith(".ps1"):
        q = re.sub(r"<#[\s\S]*?#>", "", q)
        q = "\n".join(re.sub(r"#.*$", "", z) for z in q.splitlines())
    namen = set()
    for stueck in re.split(r"[\"'\s,()\[\]{}]+", q):
        stueck = stueck.replace("\\", "/").split("/")[-1]
        if stueck.endswith(ENDUNGEN):
            namen.add(stueck)
    return namen, set()


def verweise(pfad):
    if pfad.endswith(".py"):
        return verweise_py(pfad)
    return verweise_text(pfad)


def kandidaten():
    t = []
    for basis in ("scripts", "sql"):
        wp = os.path.join(WURZEL, basis)
        if not os.path.isdir(wp):
            continue
        for w, verz, dateien in os.walk(wp):
            verz[:] = [d for d in verz if d not in AUS]
            for d in dateien:
                if d.endswith(ENDUNGEN):
                    t.append(os.path.relpath(os.path.join(w, d),
                                             WURZEL).replace("\\", "/"))
    return sorted(t)


def testdateien():
    td = os.path.join(WURZEL, "tests")
    return sorted("tests/" + d for d in os.listdir(td) if d.endswith(".py"))


def trifft(kandidat, namen, module):
    b = os.path.basename(kandidat)
    if b in namen:
        return "S"
    if kandidat.endswith(".py") and b[:-3] in module:
        return "M"
    return None


def abschluss(start, kand):
    """Transitiver Abschluss mit Begruendung je Kante."""
    gesehen, wege = set(), {}
    rand = [(s, None, None) for s in start]
    while rand:
        akt, von, form = rand.pop()
        if akt in gesehen:
            continue
        gesehen.add(akt)
        wege[akt] = (von, form)
        namen, module = verweise(os.path.join(WURZEL, akt.replace("/", os.sep)))
        for k in kand:
            if k in gesehen:
                continue
            f = trifft(k, namen, module)
            if f:
                rand.append((k, akt, f))
    return gesehen, wege


def ist_riegel(k):
    """Kann die Datei mit einem Code != 0 enden - also urteilen?"""
    p = os.path.join(WURZEL, k.replace("/", os.sep))
    q = lies(p)
    if k.endswith(".py"):
        try:
            baum = ast.parse(q)
        except SyntaxError:
            return bool(re.search(r"sys\.exit", q))
        for n in ast.walk(baum):
            if isinstance(n, ast.Call):
                z = ast.unparse(n.func) if n.func else ""
                if z in ("sys.exit", "exit", "SystemExit"):
                    return True
            if isinstance(n, ast.Raise) and n.exc is not None \
                    and "SystemExit" in ast.unparse(n.exc):
                return True
        return False
    q2 = re.sub(r"/\*[\s\S]*?\*/", "", q)
    q2 = "\n".join(re.sub(r"//.*$", "", z) for z in q2.splitlines())
    return bool(re.search(r"process\.exit|exitCode|\bexit\s+1", q2))


def main(argv):
    kand = kandidaten()
    td = testdateien()
    direkt = ["scripts/node_check.py", "scripts/_bracket_check.py",
              "sql/_check_version.js", "scripts/hook_index_riegel.py",
              "scripts/hook_git_add_riegel.py"]
    start = set(direkt) | set(td)
    err, wege = abschluss(start, kand)
    erreicht = [k for k in kand if k in err]
    nie = [k for k in kand if k not in err]

    print("Kandidaten unter scripts//sql/: %d" % len(kand))
    print("Startpunkte: %d direkte Tore + %d Testdateien (pytest-Tor)"
          % (len(direkt), len(td)))
    print("=" * 74)
    print("ERREICHT: %d" % len(erreicht))
    for k in erreicht:
        von, form = wege.get(k, (None, None))
        art = {"S": "Zeichenkette", "M": "import"}.get(form, "direktes Tor")
        print("   %-42s %-13s %s" % (k, art, von or "torkette/hook"))
    print("")
    print("=" * 74)
    riegel_nie = [k for k in nie if ist_riegel(k)]
    print("IN KEINER KETTE: %d   davon urteilsfaehige Riegel: %d"
          % (len(nie), len(riegel_nie)))
    print("")
    print("--- urteilsfaehig, aber in keiner Kette ---")
    for k in riegel_nie:
        print("   %s" % k)
    print("")
    print("--- ohne Urteil (Werkzeug/Bericht/Erzeuger) ---")
    for k in nie:
        if k not in riegel_nie:
            print("   %s" % k)
    return 0


# ── Selbstprobe ───────────────────────────────────────────────────────────
K_IMPORT = ("import sys, os\n"
            "sys.path.insert(0, 'scripts')\n"
            "import _koeder_ziel_modul\n"
            "def test_a():\n    assert _koeder_ziel_modul.x == 1\n")
K_STRING = ("import subprocess, sys\n"
            "def test_b():\n"
            "    subprocess.run([sys.executable, 'scripts/_koeder_ziel_datei.py'])\n")
K_PROSA = ('"""Erwaehnt scripts/_koeder_nur_prosa.py nur im Docstring."""\n'
           "# und hier auch: scripts/_koeder_nur_prosa.py\n"
           "def test_c():\n    assert 1 == 1\n")
K_ZIELE = {"_koeder_ziel_modul.py": "x = 1\nimport sys\n",
           "_koeder_ziel_datei.py": "import sys\nsys.exit(1)\n",
           "_koeder_nur_prosa.py": "import sys\nsys.exit(1)\n"}


def koeder():
    """Selbstprobe in einem WEGWERFBAUM - im Repo wird nichts angelegt.

    tests/ gehoert nicht zu den Orten, an denen diese Messung schreiben darf.
    Der Koeder baut deshalb einen eigenen Miniaturbaum und setzt WURZEL darauf.
    """
    global WURZEL
    echte_wurzel = WURZEL
    with tempfile.TemporaryDirectory() as tmp:
        WURZEL = tmp
        os.makedirs(os.path.join(tmp, "scripts"))
        os.makedirs(os.path.join(tmp, "sql"))
        os.makedirs(os.path.join(tmp, "tests"))
        for n, i in K_ZIELE.items():
            with open(os.path.join(tmp, "scripts", n), "w",
                      encoding="utf-8", newline="") as f:
                f.write(i)
        # ein echtes Tor als Gegenprobe
        with open(os.path.join(tmp, "scripts", "node_check.py"), "w",
                  encoding="utf-8", newline="") as f:
            f.write("import sys\nsys.exit(0)\n")
        for n, i in (("test_koeder_import.py", K_IMPORT),
                     ("test_koeder_string.py", K_STRING),
                     ("test_koeder_prosa.py", K_PROSA)):
            with open(os.path.join(tmp, "tests", n), "w",
                      encoding="utf-8", newline="") as f:
                f.write(i)
        kand = kandidaten()
        td = testdateien()
        direkt = ["scripts/node_check.py"]
        err, wege = abschluss(set(direkt) | set(td), kand)
        proben = [
            ("FORM M (import)", "scripts/_koeder_ziel_modul.py", True),
            ("FORM S (Zeichenkette)", "scripts/_koeder_ziel_datei.py", True),
            ("nur Prosa -> darf NICHT zaehlen", "scripts/_koeder_nur_prosa.py", False),
            ("Gegenprobe echtes Tor", "scripts/node_check.py", True),
        ]
        ok = True
        for beschr, pfad, soll in proben:
            ist = pfad in err
            gut = (ist == soll)
            ok = ok and gut
            print("  %-34s %-34s erreicht=%-5s erwartet=%-5s %s"
                  % (beschr, pfad, ist, soll, "ok" if gut else "ROT"))
        WURZEL = echte_wurzel
        print("SELBSTPROBE %s" % ("GRUEN" if ok else "ROT"))
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(koeder() if "--koeder" in sys.argv[1:] else main(sys.argv[1:]))
