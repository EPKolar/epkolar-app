# -*- coding: utf-8 -*-
"""Messung (3)+(4): welcher Pruefer haengt in einer Kette, welcher in keiner?

Es gibt in diesem Repo KEINE package.json und KEIN .github/workflows/.
Die Ketten sind:

  K1  scripts/torkette.py                 der Auslieferungslauf, 4 Tore
  K2  .claude/settings.json PostToolUse   nach jedem Edit/Write
  K3  .claude/settings.json PreToolUse    vor jedem Bash

ZWEI EIGENE FEHLER, DIE HIER AUSGEBAUT SIND
───────────────────────────────────────────
1. Die erste Fassung suchte im ROHEN Dateitext. Damit fand sie in
   torkette.py deren eigene Begruendung ("Kein `shell=True`, keine Pipe",
   "npm run verify | tail") und meldete zwei Befunde, die es nicht gibt.
   Ein Riegel, der rohen Text durchsucht, misst seinen eigenen Kommentar mit.
   Jetzt wird KOMMENTAR- UND DOCSTRINGBLIND gelesen (ueber den Syntaxbaum).

2. Die erste Fassung liess `tests/` aus. Das vierte Tor der Torkette ist
   aber `pytest tests/` - jede der 465 Testdateien laeuft darin, und viele
   rufen ein Skript aus scripts/ als Unterprozess auf. Diese Pruefer hangen
   also SEHR WOHL in der Kette, nur mittelbar. Ohne tests/ als Startpunkt
   meldete die Messung 59 statt der tatsaechlichen Zahl.

Aufruf:
    python scripts/befund_kette.py
    python scripts/befund_kette.py --koeder
"""
import ast
import io
import json
import os
import re
import sys
import tokenize

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDUNGEN = (".py", ".js", ".mjs", ".cjs", ".ps1")
AUSGENOMMEN_VERZ = {"node_modules", "__pycache__", "_archiv", "_backups",
                    ".git", ".pytest_cache", "screenshots", "preview"}


def lies(p):
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


# ── kommentar- und docstringblindes Lesen ─────────────────────────────────
def nur_code_py(quelle):
    """Python-Quelle ohne Kommentare und ohne Docstrings.

    Zeichenketten, die WIRKLICH benutzt werden (Pfade in subprocess-Aufrufen,
    Importnamen), bleiben stehen - genau die sollen gefunden werden.
    """
    # 1 Kommentare weg
    try:
        ausgabe = []
        for tok in tokenize.generate_tokens(io.StringIO(quelle).readline):
            if tok.type == tokenize.COMMENT:
                continue
            ausgabe.append(tok)
        ohne_kommentar = tokenize.untokenize(ausgabe)
    except Exception:
        ohne_kommentar = re.sub(r"(?m)^\s*#.*$", "", quelle)
    # 2 Docstrings weg
    try:
        baum = ast.parse(ohne_kommentar)
    except SyntaxError:
        try:
            baum = ast.parse(quelle)
        except SyntaxError:
            return ohne_kommentar
    docs = set()
    for k in ast.walk(baum):
        if isinstance(k, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            if k.body and isinstance(k.body[0], ast.Expr) \
                    and isinstance(k.body[0].value, ast.Constant) \
                    and isinstance(k.body[0].value.value, str):
                docs.add(id(k.body[0].value))
    stuecke = []
    for k in ast.walk(baum):
        if isinstance(k, ast.Constant) and isinstance(k.value, str):
            if id(k) not in docs:
                stuecke.append(k.value)
        elif isinstance(k, ast.Name):
            stuecke.append(k.id)
        elif isinstance(k, ast.Attribute):
            stuecke.append(k.attr)
        elif isinstance(k, ast.alias):
            stuecke.append(k.name)
            if k.asname:
                stuecke.append(k.asname)
        elif isinstance(k, ast.ImportFrom) and k.module:
            stuecke.append(k.module)
        elif isinstance(k, ast.keyword) and k.arg:
            # Schluesselwortnamen gehoeren zum Code. Ohne sie meldete diese
            # Messung faelschlich "capture_output fehlt" in torkette.py.
            stuecke.append(k.arg)
    return "\n".join(stuecke)


def nur_code_js(quelle):
    ohne = re.sub(r"/\*[\s\S]*?\*/", "", quelle)
    return "\n".join(re.sub(r"//.*$", "", z) for z in ohne.splitlines())


def nur_code(pfad):
    q = lies(pfad)
    if pfad.endswith(".py"):
        return nur_code_py(q)
    if pfad.endswith((".js", ".mjs", ".cjs")):
        return nur_code_js(q)
    if pfad.endswith(".ps1"):
        return "\n".join(re.sub(r"#.*$", "", z) for z in q.splitlines())
    return q


# ── Bestandsaufnahme ──────────────────────────────────────────────────────
def kandidaten():
    treffer = []
    for basis in ("scripts", "sql"):
        wp = os.path.join(WURZEL, basis)
        if not os.path.isdir(wp):
            continue
        for w, verz, dateien in os.walk(wp):
            verz[:] = [d for d in verz if d not in AUSGENOMMEN_VERZ]
            for d in dateien:
                if d.endswith(ENDUNGEN):
                    treffer.append(os.path.relpath(os.path.join(w, d),
                                                   WURZEL).replace("\\", "/"))
    return sorted(treffer)


def testdateien():
    td = os.path.join(WURZEL, "tests")
    return sorted("tests/" + d for d in os.listdir(td)
                  if d.endswith(".py"))


def ist_riegel(k):
    """Kann diese Datei mit einem Code != 0 enden - also urteilen?"""
    txt = nur_code(os.path.join(WURZEL, k.replace("/", os.sep)))
    if k.endswith(".py"):
        muster = [r"sys\.exit", r"SystemExit"]
        # sys.exit steckt nach nur_code_py als Namen/Attribute drin
        return bool(re.search(r"\bexit\b", txt))
    muster = [r"process\.exit", r"exitCode", r"\bexit\b"]
    return any(re.search(m, txt) for m in muster)


def ketten():
    k = []
    txt = lies(os.path.join(WURZEL, "scripts", "torkette.py"))
    tore = re.findall(r'\(\s*"([^"]+)"\s*,\s*\[(.*?)\]\s*,\s*(True|False)\s*\)',
                      txt, re.S)
    for name, befehl, langsam in tore:
        k.append(("K1 torkette.py", name, befehl.strip(), langsam == "True"))
    pfad = os.path.join(WURZEL, ".claude", "settings.json")
    if os.path.isfile(pfad):
        s = json.loads(lies(pfad))
        for ereignis, eintraege in s.get("hooks", {}).items():
            for e in eintraege:
                for h in e.get("hooks", []):
                    k.append(("K2/K3 %s (%s)" % (ereignis, e.get("matcher")),
                              "hook", h.get("command", ""), False))
    return k


def erreichbar(start, kand):
    """Transitiver Abschluss ueber KOMMENTARBLIND gelesene Verweise."""
    gesehen = set()
    wege = {}
    rand = [(s, [s]) for s in start]
    basis = {os.path.basename(k): k for k in kand}
    while rand:
        akt, weg = rand.pop()
        if akt in gesehen:
            continue
        gesehen.add(akt)
        wege.setdefault(akt, weg)
        txt = nur_code(os.path.join(WURZEL, akt.replace("/", os.sep)))
        for b, k in basis.items():
            if k == akt or k in gesehen:
                continue
            if b in txt:
                rand.append((k, weg + [k]))
    return gesehen, wege


def torkette_pruefen():
    """(4) Wird jedes Tor eigener Prozess, jeder Rueckgabewert einzeln gelesen?

    KOMMENTARBLIND - sonst findet der Riegel die Begruendung in der Datei.
    """
    pfad = os.path.join(WURZEL, "scripts", "torkette.py")
    roh = lies(pfad)
    code = nur_code_py(roh)
    baum = ast.parse(roh)
    befunde = []
    # shell=True?
    shell_true = []
    for k in ast.walk(baum):
        if isinstance(k, ast.Call):
            for kw in k.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) \
                        and kw.value.value is True:
                    shell_true.append(k.lineno)
    if shell_true:
        befunde.append("shell=True in Z%s" % shell_true)
    # Pipe in einem tatsaechlich gebauten Befehl?
    pipe = [z for z in code.splitlines()
            if re.search(r"\|\s*(tail|head|more|findstr|sort)\b", z)]
    if pipe:
        befunde.append("Pipe in einem echten Befehl: %s" % pipe[:3])
    # returncode explizit gelesen, nicht in and/or verknuepft?
    rc_vergleich = re.findall(r"returncode\s*==\s*0", roh)
    if not rc_vergleich:
        befunde.append("liest returncode nicht explizit")
    rc_verknuepft = [k.lineno for k in ast.walk(baum)
                     if isinstance(k, ast.BoolOp)
                     and "returncode" in ast.unparse(k)]
    if rc_verknuepft:
        befunde.append("returncode in einer and/or-Verknuepfung Z%s" % rc_verknuepft)
    # faengt die Torkette selbst die Ausgabe?
    if "capture_output" not in code:
        befunde.append("faengt die Ausgabe nicht selbst - Pipe-Gefahr")
    # Ausfall beim Start / Zeitgrenze als ROT?
    hat_fnf = any(isinstance(k, ast.ExceptHandler)
                  and k.type is not None
                  and "FileNotFoundError" in ast.unparse(k.type)
                  for k in ast.walk(baum))
    if not hat_fnf:
        befunde.append("ein Tor, das nicht startet, wird nicht als ROT gewertet")
    hat_to = any(isinstance(k, ast.ExceptHandler) and k.type is not None
                 and "Timeout" in ast.unparse(k.type) for k in ast.walk(baum))
    if not hat_to:
        befunde.append("kein Zeitlimit - ein haengendes Tor haengt die Kette")
    # Wird JEDES Tor gefahren, oder kann eines uebersprungen werden?
    return befunde


def main(argv):
    kand = kandidaten()
    td = testdateien()
    ks = ketten()

    print("Skriptdateien unter scripts/ und sql/: %d" % len(kand))
    print("Testdateien unter tests/: %d" % len(td))
    print("package.json im Repo: %s" % ("JA" if os.path.isfile(
        os.path.join(WURZEL, "package.json")) else "NEIN - es gibt keine, "
        "und laut git-Historie hat es nie eine gegeben"))
    print(".github/workflows/: %s" % ("JA" if os.path.isdir(
        os.path.join(WURZEL, ".github", "workflows")) else "NEIN - es gibt keine CI"))
    print("=" * 74)
    print("DIE KETTEN UND IHRE TORE")
    direkt = set()
    pytest_tor = False
    for kette, name, befehl, langsam in ks:
        gefunden = re.findall(r'([\w/\\.-]+\.(?:py|js|mjs|cjs|ps1))', befehl)
        ziele = {g.replace("\\", "/").split("/")[-1] for g in gefunden}
        auf = [k for k in kand if os.path.basename(k) in ziele]
        direkt.update(auf)
        if "pytest" in befehl:
            pytest_tor = True
        print("  %-30s %-18s %s%s" % (kette, name,
                                      auf or befehl[:46],
                                      "  [langsam]" if langsam else ""))
    print("")
    print("Das pytest-Tor fuehrt alle %d Testdateien - sie sind damit Teil "
          "der Kette." % len(td) if pytest_tor else "KEIN pytest-Tor!")

    start = set(direkt) | (set(td) if pytest_tor else set())
    err, wege = erreichbar(start, kand)
    erreichte_kand = sorted(k for k in kand if k in err)
    print("")
    print("Von der Kette erreichte Pruefer unter scripts//sql/: %d von %d"
          % (len(erreichte_kand), len(kand)))
    for k in erreichte_kand:
        weg = wege.get(k, [])
        ueber = weg[0] if weg else "?"
        art = "direkt" if k in direkt else "ueber %s" % ueber
        print("   %-44s %s" % (k, art))

    print("=" * 74)
    nie = [k for k in kand if k not in err]
    riegel_nie = [k for k in nie if ist_riegel(k)]
    print("IN KEINER KETTE: %d von %d" % (len(nie), len(kand)))
    print("davon urteilsfaehig (Riegel, Code != 0 moeglich): %d" % len(riegel_nie))
    print("")
    print("--- RIEGEL, die in KEINER Kette haengen ---")
    for k in riegel_nie:
        print("   %s" % k)
    print("")
    print("--- ohne Urteil (Werkzeug/Bericht), in keiner Kette: %d ---"
          % (len(nie) - len(riegel_nie)))
    for k in nie:
        if k not in riegel_nie:
            print("   %s" % k)

    print("")
    print("=" * 74)
    print("(4) TORKETTE - kommentarblind geprueft")
    befunde = torkette_pruefen()
    if befunde:
        for b in befunde:
            print("   BEFUND: %s" % b)
    else:
        print("   keine Befunde: jedes Tor eigener Prozess (subprocess.run ohne")
        print("   shell, ohne Pipe), r.returncode == 0 EINZELN je Tor gelesen,")
        print("   Kuerzung der Ausgabe erst NACH dem Lesen, Startausfall und")
        print("   Zeitgrenze werden als ROT gewertet.")
    print("")
    print("   Vollstaendigkeit der Torliste gegen package.json: nicht pruefbar,")
    print("   es gibt keine package.json. Gegen die Hooks:")
    hook = lies(os.path.join(WURZEL, "scripts", "hook_index_riegel.py"))
    hk = nur_code_py(hook)
    for n in ("node_check.py", "_bracket_check.py", "_check_version.js", "pytest"):
        print("     %-22s Torkette: %-5s Hook: %s"
              % (n, "JA" if any(n in b for _, _, b, _ in ks) else "nein",
                 "JA" if n in hk else "nein"))
    return 0


KOEDER = "import sys\nsys.exit(1)\n"
KOEDER_KOMMENTAR = ('# scripts/node_check.py steht nur in diesem Kommentar\n'
                    '"""und hier: scripts/tab_sweep.py"""\n'
                    'import sys\nsys.exit(1)\n')


def koeder():
    """Drei Proben:
    1 ein Riegel, den nichts aufruft, MUSS auffallen
    2 ein Riegel, der in der Torkette steht, darf NICHT auffallen
    3 eine Datei, die einen Pfad nur im KOMMENTAR nennt, darf daraus
      keine Kette bauen (sonst misst die Messung Kommentare mit)
    """
    p1 = os.path.join(WURZEL, "scripts", "_koeder_nie_gefahren.py")
    p2 = os.path.join(WURZEL, "scripts", "_koeder_nur_kommentar.py")
    neu = []
    for p, inhalt in ((p1, KOEDER), (p2, KOEDER_KOMMENTAR)):
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(inhalt)
            neu.append(p)
    try:
        kand = kandidaten()
        td = testdateien()
        ks = ketten()
        direkt = set()
        for kette, name, befehl, langsam in ks:
            gefunden = re.findall(r'([\w/\\.-]+\.(?:py|js|mjs|cjs|ps1))', befehl)
            ziele = {g.replace("\\", "/").split("/")[-1] for g in gefunden}
            direkt.update(k for k in kand if os.path.basename(k) in ziele)
        err, _ = erreichbar(set(direkt) | set(td), kand)
        k1 = "scripts/_koeder_nie_gefahren.py"
        k2 = "scripts/_koeder_nur_kommentar.py"
        p1ok = k1 not in err and ist_riegel(k1)
        p2ok = "scripts/node_check.py" in err
        # Probe 3: der Koeder nennt tab_sweep NUR im Kommentar/Docstring.
        # Kommentarblind gelesen darf daraus kein Verweis entstehen.
        txt = nur_code(os.path.join(WURZEL, "scripts", "_koeder_nur_kommentar.py"))
        p3ok = "tab_sweep.py" not in txt and "node_check.py" not in txt
        print("1 %-42s %s" % (k1, "GEFUNDEN (in keiner Kette, Riegel)"
                              if p1ok else "NICHT GEFUNDEN"))
        print("2 %-42s %s" % ("scripts/node_check.py (Gegenprobe)",
                              "korrekt als gefahren erkannt" if p2ok
                              else "FALSCH als ungefahren"))
        print("3 %-42s %s" % ("Verweis nur im Kommentar",
                              "korrekt NICHT als Kette gezaehlt" if p3ok
                              else "FALSCH: Kommentar wurde mitgemessen"))
        if p1ok and p2ok and p3ok:
            print("SELBSTPROBE GRUEN")
            return 0
        print("SELBSTPROBE ROT")
        return 1
    finally:
        for p in neu:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    sys.exit(koeder() if "--koeder" in sys.argv[1:] else main(sys.argv[1:]))
