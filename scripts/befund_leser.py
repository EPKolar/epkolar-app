# -*- coding: utf-8 -*-
"""Messung: welche der verwaisten Pruefer sind REINE LESER?

Fortsetzung von scripts/befund_kette.py. Dort wurde gemessen, WER in keiner
Kette haengt. Hier wird gemessen, WAS ein verwaister Pruefer braucht, um zu
laufen - denn nur ein reiner Leser ist ueberhaupt ein Einhaeng-Kandidat.

VIER KLASSEN
────────────
  BROWSER   braucht Playwright/Chromium  -> Einmal-Messgeraet, nicht einhaengen
  DB        greift auf Supabase/Postgres -> nicht einhaengen, schreibt evtl.
  NETZ      laedt aus dem Internet       -> nicht einhaengen
  LESER     liest nur Dateien im Baum    -> KANDIDAT

WARUM KOMMENTARBLIND
────────────────────
Ein Skript, das im Docstring erklaert "dieses Werkzeug braucht KEIN
playwright", wuerde bei einer Rohtextsuche als Browser-Skript gelten. Genau
diese Fehlerform hat in scripts/befund_kette.py zwei Befunde erfunden, die es
nicht gab ("shell=True gefunden" stand in der Begruendung, warum es dort kein
shell=True gibt). Python wird deshalb ueber den Syntaxbaum gelesen
(ast: Kommentare existieren dort nicht, Docstrings werden gestrichen).
JS/PS1 haben keinen Syntaxbaum zur Hand - dort streicht ein Abtaster die
Kommentare, und was er nicht kann, steht unten unter GRENZEN.

GRENZEN DIESER MESSUNG
──────────────────────
* Der JS/PS1-Abtaster kennt keine regulaeren Ausdruecke als Literale. Ein
  `/playwright/` als Regex wuerde als Code gelten (richtig) - aber ein `//`
  innerhalb eines Regex koennte den Rest der Zeile streichen (Unterzaehlung).
  Fuer die 5 betroffenen Dateien ist das von Hand gegengelesen.
* "braucht Argumente" wird aus sys.argv/process.argv geschlossen, nicht aus
  einem Lauf. Der Lauf steht getrennt in der Messung.

AUFRUF
──────
    python scripts/befund_leser.py            Bericht
    python scripts/befund_leser.py --koeder   Selbstprobe

Der Koeder ist Pflicht: diese Messung ZAEHLT, und wer zaehlt, wird beim
eigenen Ausfall gruen. Eine Fassung, die nichts findet, meldet "0 Browser,
alles Leser" - und das sieht wie ein Ergebnis aus.
"""
import ast
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Merkmale je Klasse. Gesucht wird im CODE, nicht im Rohtext.
# EIGENER FEHLER, hier ausgebaut: die erste Fassung hatte "webkit" als
# Browser-Merkmal. Damit galt scripts/schrift_holen.py als Browser-Skript -
# es laedt Schriften und nennt dabei das CSS-Praefix `-webkit-` und das
# Format `woff`. Ein Merkmal, das auch ausserhalb seines Gegenstands
# vorkommt, ordnet falsch zu; die Browser-Merkmale sind deshalb jetzt alle
# an einen AUFRUF gebunden (`.launch`, `new_page`, `sync_playwright`).
BROWSER = (
    "playwright", "sync_playwright", "async_playwright", "chromium.launch",
    "chromium", "webkit.launch", "firefox.launch", "new_page(", "puppeteer",
)
DB = (
    "supabase", "SUPABASE", "psycopg", "postgres", "pg_", "Invoke-RestMethod",
    "Invoke-WebRequest", "service_role", "anon_key", "rest/v1", "sql-runner",
)
NETZ = (
    "urllib", "requests.get", "requests.post", "http.client", "socket.",
    "fonts.googleapis", "curl ", "wget ",
)
# NETZ und DB ueberschneiden sich (beides sind Netzaufrufe). Die Reihenfolge
# der Pruefung entscheidet, und DB kommt zuerst: ein Supabase-Aufruf ist fuer
# das Urteil "nicht einhaengen" der schaerfere Befund.


def lies(p):
    with open(os.path.join(WURZEL, p), "r", encoding="utf-8",
              errors="replace") as f:
        return f.read()


def code_python(quelle):
    """Gibt den Code OHNE Kommentare und OHNE Docstrings zurueck.

    ast kennt keine Kommentare - sie sind nach dem Parsen weg. Docstrings
    sind dagegen echte Ausdruecke und muessen gestrichen werden.
    """
    baum = ast.parse(quelle)
    for knoten in ast.walk(baum):
        if not isinstance(knoten, (ast.Module, ast.FunctionDef,
                                   ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        rumpf = getattr(knoten, "body", None)
        if not rumpf:
            continue
        erst = rumpf[0]
        if (isinstance(erst, ast.Expr)
                and isinstance(erst.value, ast.Constant)
                and isinstance(erst.value.value, str)):
            rumpf.pop(0)
            if not rumpf:
                rumpf.append(ast.Pass())
    ast.fix_missing_locations(baum)
    return ast.unparse(baum)


def code_abtaster(quelle, zeilenmarke, block=("/*", "*/")):
    """Streicht Kommentare eines Nicht-Python-Textes, Zeichenketten bleiben.

    Zeichenketten bleiben stehen, weil ein Pfad wie 'supabase' dort ein
    echter Gebrauch ist, kein Kommentar.
    """
    aus = []
    i = 0
    n = len(quelle)
    auf, zu = block
    while i < n:
        z = quelle[i]
        if quelle.startswith(auf, i):
            ende = quelle.find(zu, i + len(auf))
            i = n if ende < 0 else ende + len(zu)
            continue
        if quelle.startswith(zeilenmarke, i):
            ende = quelle.find("\n", i)
            i = n if ende < 0 else ende
            continue
        if z in "'\"`":
            aus.append(z)
            i += 1
            while i < n and quelle[i] != z:
                if quelle[i] == "\\":
                    aus.append(quelle[i])
                    i += 1
                    if i < n:
                        aus.append(quelle[i])
                        i += 1
                    continue
                aus.append(quelle[i])
                i += 1
            if i < n:
                aus.append(quelle[i])
                i += 1
            continue
        aus.append(z)
        i += 1
    return "".join(aus)


def nur_code(p):
    """Code ohne Kommentare, oder None wenn die Datei nicht lesbar ist."""
    quelle = lies(p)
    if p.endswith(".py"):
        try:
            return code_python(quelle)
        except SyntaxError:
            return None
    if p.endswith((".js", ".mjs", ".cjs")):
        return code_abtaster(quelle, "//", ("/*", "*/"))
    if p.endswith(".ps1"):
        return code_abtaster(quelle, "#", ("<#", "#>"))
    return quelle


def klasse(p):
    txt = nur_code(p)
    if txt is None:
        return "UNLESBAR", []
    tief = txt.lower()
    for name, merkmale in (("BROWSER", BROWSER), ("DB", DB), ("NETZ", NETZ)):
        treffer = [m for m in merkmale if m.lower() in tief]
        if treffer:
            return name, treffer
    return "LESER", []


def braucht_argumente(p):
    """Grobe Anzeige: liest das Skript argv-Positionen ueber 0 hinaus?"""
    txt = nur_code(p) or ""
    if p.endswith(".py"):
        return bool(re.search(r"sys\.argv\[[1-9]", txt)
                    or "argparse" in txt
                    or re.search(r"sys\.argv\[1:\]", txt))
    if p.endswith((".js", ".mjs", ".cjs")):
        return bool(re.search(r"argv\.slice\(2\)", txt)
                    or re.search(r"argv\[[2-9]", txt))
    if p.endswith(".ps1"):
        return "param(" in txt.lower()
    return False


def schreibt(p):
    """Schreibt das Skript Dateien? Ein Schreiber ist kein reiner Leser."""
    txt = nur_code(p) or ""
    if p.endswith(".py"):
        return bool(re.search(r"open\([^)]*['\"][waxb+]", txt)
                    or ".write_text(" in txt
                    or "shutil.copy" in txt
                    or "os.remove" in txt
                    or "os.rename" in txt)
    if p.endswith((".js", ".mjs", ".cjs")):
        return bool("writeFileSync" in txt or "writeFile" in txt
                    or "unlinkSync" in txt or "renameSync" in txt)
    if p.endswith(".ps1"):
        tief = txt.lower()
        return bool("set-content" in tief or "out-file" in tief
                    or "remove-item" in tief or "add-content" in tief)
    return False


# ── Die Grundgesamtheit: die verwaisten urteilsfaehigen Pruefer ──────────────
# Sie kommt aus scripts/befund_verweise.py, NICHT aus scripts/befund_kette.py.
#
# WARUM NICHT befund_kette.py (am 27.09.2026 gemessen, beide Richtungen):
# Es gleicht Verweise ueber den BASISNAMEN ab (`if b in txt`). Damit
#   * FEHLT ihm die Import-Form: `from code_scan import ist_code` nennt
#     "code_scan.py" nirgends, also hielt es code_scan.py fuer verwaist -
#     obwohl 19 Testdateien es importieren. Ebenso safe_edit.py und
#     mob_ansicht_messen.py. DREI falsche Waisen.
#   * und es ERFINDET eine Kette per Teilzeichenkette: "bracket_check.py" ist
#     ein Teil von "_bracket_check.py". Weil
#     tests/test_klammertor_blindheit_v956.py den Streicher
#     `_bracket_check.py` nennt, galt ihm auch scripts/bracket_check.py als
#     gefahren. EINE falsche Kette.
# befund_verweise.py trennt Form S (Zeichenkette) von Form M (Import) und
# trifft beide Faelle richtig: 14 erreicht statt 12.
def verwaiste():
    import subprocess
    r = subprocess.run([sys.executable, os.path.join("scripts",
                                                     "befund_verweise.py")],
                       cwd=WURZEL, capture_output=True, text=True,
                       timeout=600)
    if r.returncode != 0:
        raise SystemExit("befund_verweise.py endete mit %d - Grundgesamtheit "
                         "nicht vertrauenswuerdig" % r.returncode)
    zeilen = r.stdout.splitlines()
    try:
        a = zeilen.index("--- urteilsfaehig, aber in keiner Kette ---")
    except ValueError:
        raise SystemExit("Abschnitt der Verwaisten nicht gefunden - "
                         "befund_verweise.py hat sein Ausgabeformat geaendert")
    aus = []
    for z in zeilen[a + 1:]:
        if not z.startswith("   "):
            break
        aus.append(z.strip())
    if not aus:
        raise SystemExit("LEERE GRUNDGESAMTHEIT - eine leere Menge besteht "
                         "keine Probe")
    return aus


KOEDER = {
    "_koeder_browser.py": (
        "import sys\n"
        "from playwright.sync_api import sync_playwright\n"
        "sys.exit(1)\n"),
    "_koeder_db.py": (
        "import os, sys\n"
        "u = os.environ['SUPABASE_URL']\n"
        "sys.exit(1)\n"),
    "_koeder_netz.py": (
        "import sys, urllib.request\n"
        "urllib.request.urlopen('http://example.org')\n"
        "sys.exit(1)\n"),
    "_koeder_leser.py": (
        "import sys, os\n"
        "n = len(open('index.html', encoding='utf-8').read())\n"
        "sys.exit(0 if n > 0 else 1)\n"),
    "_koeder_nur_kommentar.py": (
        '"""Dieses Werkzeug braucht KEIN playwright und KEINE supabase-URL.\n'
        'Es laedt auch nichts per urllib. Das steht hier absichtlich.\n'
        '"""\n'
        "import sys\n"
        "n = len(open('index.html', encoding='utf-8').read())\n"
        "sys.exit(0 if n > 0 else 1)\n"),
    "_koeder_schreiber.py": (
        "import sys\n"
        "open('wegwerf.txt', 'w', newline='').write('x')\n"
        "sys.exit(1)\n"),
}

ERWARTET = {
    "_koeder_browser.py": ("BROWSER", False),
    "_koeder_db.py": ("DB", False),
    "_koeder_netz.py": ("NETZ", False),
    "_koeder_leser.py": ("LESER", False),
    # Die wichtigste Probe: die drei Merkmale stehen NUR im Docstring.
    # Wer roh sucht, meldet hier BROWSER. Richtig ist LESER.
    "_koeder_nur_kommentar.py": ("LESER", False),
    "_koeder_schreiber.py": ("LESER", True),
}


def koeder():
    """Sieben Proben in einem Wegwerf-Ordner. Im Repo bleibt nichts."""
    ordner = os.path.join(WURZEL, "scripts", "_koeder_leser_tmp")
    os.makedirs(ordner, exist_ok=True)
    angelegt = []
    try:
        for name, inhalt in KOEDER.items():
            p = os.path.join(ordner, name)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(inhalt)
            angelegt.append(p)
        rot = 0
        print("KOEDER-SELBSTPROBE")
        print("=" * 74)
        for name, (k_soll, s_soll) in ERWARTET.items():
            rel = os.path.join("scripts", "_koeder_leser_tmp",
                               name).replace("\\", "/")
            k_ist, _ = klasse(rel)
            s_ist = schreibt(rel)
            ok = (k_ist == k_soll) and (s_ist == s_soll)
            if not ok:
                rot += 1
            print("%-28s Klasse %-8s (soll %-8s)  schreibt %-5s (soll %-5s) %s"
                  % (name, k_ist, k_soll, s_ist, s_soll,
                     "ok" if ok else "FALSCH"))
        # Probe 7: findet die Messung ueberhaupt etwas? Eine Fassung, die
        # nichts findet, meldet "alles Leser" und sieht wie ein Ergebnis aus.
        v = verwaiste()
        gefunden = [p for p in v if klasse(p)[0] == "BROWSER"]
        leer_ok = len(v) > 20 and len(gefunden) > 5
        print("%-28s %d Verwaiste, davon %d BROWSER  %s"
              % ("Grundgesamtheit nicht leer", len(v), len(gefunden),
                 "ok" if leer_ok else "FALSCH"))
        if not leer_ok:
            rot += 1
        print("=" * 74)
        print("%d von %d Proben falsch." % (rot, len(ERWARTET) + 1))
        return 1 if rot else 0
    finally:
        for p in angelegt:
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(ordner) and not os.listdir(ordner):
            os.rmdir(ordner)


def main(argv):
    if "--koeder" in argv:
        return koeder()
    v = verwaiste()
    nach = {"BROWSER": [], "DB": [], "NETZ": [], "LESER": [], "UNLESBAR": []}
    for p in v:
        k, treffer = klasse(p)
        nach[k].append((p, treffer))
    print("Verwaiste urteilsfaehige Pruefer: %d" % len(v))
    print("=" * 74)
    for k in ("BROWSER", "DB", "NETZ", "UNLESBAR"):
        print("%-9s %3d" % (k, len(nach[k])))
    print("%-9s %3d   <- die Einhaeng-Kandidaten" % ("LESER",
                                                     len(nach["LESER"])))
    print("")
    print("--- DIE REINEN LESER ---")
    for p, _ in sorted(nach["LESER"]):
        marken = []
        if braucht_argumente(p):
            marken.append("braucht Argumente")
        if schreibt(p):
            marken.append("SCHREIBT Dateien")
        print("   %-46s %s" % (p, ", ".join(marken) if marken else ""))
    print("")
    for k in ("DB", "NETZ"):
        print("--- %s ---" % k)
        for p, t in sorted(nach[k]):
            print("   %-46s %s" % (p, ",".join(t[:3])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
