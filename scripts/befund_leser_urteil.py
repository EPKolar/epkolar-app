# -*- coding: utf-8 -*-
"""Kann dieser Pruefer UEBERHAUPT rot werden?

WOZU - EIN BEFUND AN DEN VORMESSUNGEN
─────────────────────────────────────
`scripts/befund_kette.py` und `scripts/befund_verweise.py` nennen einen
Pruefer "urteilsfaehig", wenn in seinem Code das Wort `exit` vorkommt. Das
ist Anwesenheit, nicht Wirkung. `scripts/b3_12_15_quelltext.py` endet mit

    sys.exit(main(sys.argv[1:]))

und in `main` steht genau EIN `return`, naemlich `return 0`. Der Pruefer
meldete am 27.09.2026 113 Stellen mit einer Schriftgroesse unter 12 px - und
gab 0 zurueck. Er ist ein BERICHT, kein Riegel, und beide Vormessungen zaehlen
ihn als Riegel.

WAS HIER GEMESSEN WIRD
──────────────────────
Ueber den Syntaxbaum (Python) bzw. einen Abtaster (JS):
gibt es einen Ausstieg mit einem Wert, der nicht 0 ist?

  Python   sys.exit(<nicht 0>) / SystemExit(...) / return <nicht 0> in main
  JS       process.exit(<nicht 0>) / process.exitCode = <nicht 0>

UNBEKANNT heisst: der Wert steht nicht als Zahl da (z. B. `sys.exit(main(...))`
oder `process.exit(miss?1:0)`). Dann wird die aufgerufene Funktion
nachgesehen; geht auch das nicht, steht UNBEKANNT, und UNBEKANNT ist kein
Beleg fuer "kann rot werden".

AUFRUF
──────
    python scripts/befund_leser_urteil.py
    python scripts/befund_leser_urteil.py --koeder
"""
import ast
import os
import re
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIE_FUENFZEHN = [
    "scripts/a2_dryrun.mjs",
    "scripts/anker_schneiden.py",
    "scripts/ansicht_inventar.py",
    "scripts/b3_12_15_quelltext.py",
    "scripts/b3_bestand_quelltext.py",
    "scripts/bestand.py",
    "scripts/bughunt-state-update.ps1",
    "scripts/freivar/mutation.js",
    "scripts/freivar/selbsttest.js",
    "scripts/icons_erzeugen.py",
    "scripts/md5_geschuetzt.py",
    "scripts/paare_v931_ausgetretene.py",
    "scripts/torkette.py",
    "scripts/verify_sync_behavior.cjs",
    "sql/_check_brackets.js",
]


def _wert_nicht_null(knoten):
    """True, wenn dieser Ausdruck sicher ein Wert != 0 ist."""
    if isinstance(knoten, ast.Constant):
        if knoten.value is None or knoten.value == 0:
            return False
        return True
    return None  # unbekannt


def py_urteil(pfad):
    quelle = open(pfad, encoding="utf-8", errors="replace").read()
    try:
        baum = ast.parse(quelle)
    except SyntaxError as e:
        return "UNLESBAR", str(e)
    # 1 direkte sys.exit(<zahl != 0>) / SystemExit("text")
    gruende = []
    unbekannt = []
    for k in ast.walk(baum):
        if isinstance(k, ast.Call):
            ziel = ast.unparse(k.func)
            if ziel in ("sys.exit", "exit", "SystemExit"):
                arg = k.args[0] if k.args else None
                if arg is None:
                    continue
                u = _wert_nicht_null(arg)
                if u is True:
                    gruende.append("%s(%s)" % (ziel, ast.unparse(arg)[:40]))
                elif u is None:
                    unbekannt.append(ast.unparse(arg)[:40])
        if isinstance(k, ast.Raise) and k.exc is not None:
            if "SystemExit" in ast.unparse(k.exc):
                gruende.append("raise " + ast.unparse(k.exc)[:40])
    # 2 return <zahl != 0> in irgendeiner Funktion
    for k in ast.walk(baum):
        if isinstance(k, ast.Return) and k.value is not None:
            if _wert_nicht_null(k.value) is True:
                gruende.append("return " + ast.unparse(k.value)[:30])
    if gruende:
        return "KANN ROT", "; ".join(sorted(set(gruende))[:3])
    if unbekannt:
        # `sys.exit(main(...))` ist der Regelfall in diesem Repo. Wenn der
        # einzige unbekannte Ausstieg ein Aufruf einer Funktion IN DIESER
        # DATEI ist und deren returns oben schon alle geprueft wurden (keiner
        # war != 0), dann ist der Ausstieg NIE rot - und nicht "unbekannt".
        # Ohne diesen Schritt meldet die Messung fuer jede Datei mit
        # `sys.exit(main())` UNBEKANNT und sagt damit nichts.
        eigene = {k.name for k in ast.walk(baum)
                  if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef))}
        if all(re.match(r"^([\w.]+)\(", x) and x.split("(")[0] in eigene
               for x in unbekannt):
            return "NIE ROT", ("Ausstieg nur ueber %s, und dort steht kein "
                               "return != 0" % ", ".join(sorted(set(unbekannt))[:2]))
        return "UNBEKANNT", "Ausstieg ueber " + ", ".join(sorted(set(unbekannt))[:2])
    return "NIE ROT", "kein Ausstieg mit einem Wert != 0"


def js_urteil(pfad):
    quelle = open(pfad, encoding="utf-8", errors="replace").read()
    gruende = []
    for m in re.finditer(r"process\.exit(?:Code)?\s*(?:=\s*|\()\s*([^);\n]*)",
                         quelle):
        arg = m.group(1).strip()
        if arg in ("0", ""):
            continue
        if re.fullmatch(r"[1-9]\d*", arg):
            gruende.append("process.exit(%s)" % arg)
        else:
            gruende.append("process.exit(%s) [Ausdruck]" % arg[:30])
    if any("[Ausdruck]" not in g for g in gruende):
        return "KANN ROT", "; ".join(sorted(set(gruende))[:3])
    if gruende:
        return "WAHRSCHEINLICH", "; ".join(sorted(set(gruende))[:3])
    if "throw" in quelle:
        return "KANN ROT", "throw (unbehandelt -> Code 1)"
    return "NIE ROT", "kein process.exit != 0"


def ps_urteil(pfad):
    quelle = open(pfad, encoding="utf-8", errors="replace").read()
    t = [m.group(1) for m in re.finditer(r"exit\s+(\d+)", quelle)]
    nn = [x for x in t if x != "0"]
    if nn:
        return "KANN ROT", "exit " + ", ".join(sorted(set(nn)))
    return "NIE ROT", "kein exit != 0"


def urteil(rel):
    p = os.path.join(WURZEL, rel.replace("/", os.sep))
    if rel.endswith(".py"):
        return py_urteil(p)
    if rel.endswith((".js", ".mjs", ".cjs")):
        return js_urteil(p)
    if rel.endswith(".ps1"):
        return ps_urteil(p)
    return "UNBEKANNT", "unbekannte Endung"


KOEDER = {
    "_k_nie.py": "import sys\n\n\ndef main():\n    print('x')\n    return 0\n\n\nsys.exit(main())\n",
    "_k_kann.py": "import sys\n\n\ndef main():\n    if 1:\n        return 1\n    return 0\n\n\nsys.exit(main())\n",
    "_k_direkt.py": "import sys\nsys.exit(2)\n",
    "_k_nie.js": "console.log('x');\nprocess.exit(0);\n",
    "_k_kann.js": "console.log('x');\nprocess.exit(1);\n",
}
ERWARTET = {
    "_k_nie.py": "NIE ROT",
    "_k_kann.py": "KANN ROT",
    "_k_direkt.py": "KANN ROT",
    "_k_nie.js": "NIE ROT",
    "_k_kann.js": "KANN ROT",
}


def koeder():
    ordner = os.path.join(WURZEL, "scripts", "_k_urteil_tmp")
    os.makedirs(ordner, exist_ok=True)
    rot = 0
    try:
        for name, inhalt in KOEDER.items():
            with open(os.path.join(ordner, name), "w", encoding="utf-8",
                      newline="") as f:
                f.write(inhalt)
        print("KOEDER-SELBSTPROBE")
        print("=" * 66)
        for name, soll in ERWARTET.items():
            rel = "scripts/_k_urteil_tmp/" + name
            ist, warum = urteil(rel)
            ok = ist == soll
            if not ok:
                rot += 1
            print("%-14s %-14s (soll %-14s) %s   %s"
                  % (name, ist, soll, "ok" if ok else "FALSCH", warum[:30]))
        # Gegenprobe an echtem Code, in BEIDE Richtungen.
        #
        # EIGENER IRRTUM, hier festgehalten: ich hatte fuer
        # b3_12_15_quelltext.py "NIE ROT" erwartet, weil sein main() nur
        # `return 0` kennt. Die Messung meldete KANN ROT und hatte RECHT: in
        # Zeile 115 steht `raise SystemExit("ABBRUCH (K-Q1) ...")`, wenn die
        # UI-Tabelle nicht aufloesbar ist. Mein grep hatte nur nach
        # "sys.exit" gesucht, und "sys.exit" ist kein Teil von "SystemExit".
        # Der Pruefer kann also rot werden - aber nur, wenn seine EIGENE
        # Eichung scheitert, nie wegen der 113 Fundstellen, die er meldet.
        # Das ist ein Unterschied, den erst die Mutationsprobe zeigt.
        # ZWEITER eigener Irrtum, gleiche Form: ich erwartete fuer
        # icons_erzeugen.py "NIE ROT", weil es ein Erzeuger ist. Es hat
        # `raise SystemExit(2)` (Zeile 67) und `return 1` (Zeile 225). Auch
        # hier hatte die Messung recht und meine Erwartung unrecht. Beide
        # Male war der Grund derselbe: ich habe mit grep nach "sys.exit"
        # gesucht und "raise SystemExit" damit nicht gesehen.
        #
        # Die Richtung "NIE ROT" ist deshalb NUR an _k_nie.py/_k_nie.js
        # belegt - an Dateien, deren einzigen Ausstieg ich Zeile fuer Zeile
        # gelesen habe. KEINE der fuenfzehn echten Dateien ist NIE ROT; die
        # Probe an echtem Code kann diese Richtung also nicht zeigen, und
        # eine Probe, die ihre Richtung nicht zeigen kann, wird hier nicht
        # behauptet.
        for rel, soll in (("scripts/bestand.py", "KANN ROT"),
                          ("scripts/b3_12_15_quelltext.py", "KANN ROT"),
                          ("scripts/icons_erzeugen.py", "KANN ROT")):
            ist, _ = urteil(rel)
            ok = ist == soll
            if not ok:
                rot += 1
            print("%-14s %-14s (soll %-14s) %s   Gegenprobe echter Code"
                  % (os.path.basename(rel)[:14], ist, soll,
                     "ok" if ok else "FALSCH"))
        print("=" * 66)
        print("%d von %d Proben falsch." % (rot, len(ERWARTET) + 3))
        return 1 if rot else 0
    finally:
        for name in KOEDER:
            p = os.path.join(ordner, name)
            if os.path.exists(p):
                os.remove(p)
        if os.path.isdir(ordner) and not os.listdir(ordner):
            os.rmdir(ordner)


def main(argv):
    if "--koeder" in argv:
        return koeder()
    print("%-38s %-15s %s" % ("Pruefer", "Urteilsfaehig?", "Beleg"))
    print("-" * 100)
    for rel in DIE_FUENFZEHN:
        u, warum = urteil(rel)
        print("%-38s %-15s %s" % (rel, u, warum))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
