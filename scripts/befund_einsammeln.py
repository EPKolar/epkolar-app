# -*- coding: utf-8 -*-
"""Messung (1): Wird JEDE Testdatei auf der Platte von pytest eingesammelt?

Vergleicht die .py-Dateien unter tests/ mit den Dateien, die in einem
`pytest --collect-only -q`-Protokoll als Traeger mindestens eines Falls
auftauchen. Eine Datei, die nicht auftaucht, kann nichts messen.

Aufruf:
    python scripts/befund_einsammeln.py <collect.log>          echte Messung
    python scripts/befund_einsammeln.py --koeder                Selbstprobe

Die Selbstprobe baut einen Miniaturbaum mit VIER bekannt-unsammelbaren
Dateien und laesst pytest wirklich darauf laufen. Findet der Vergleich sie
nicht alle, ist das Messverfahren selbst kaputt und der Ausgang ist 1.
"""
import os
import re
import subprocess
import sys
import tempfile

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dateien_auf_der_platte(testdir):
    """Alle .py-Dateien unter testdir, als POSIX-Pfade relativ zum Repo."""
    treffer = []
    for wurzel, verz, dateien in os.walk(testdir):
        verz[:] = [d for d in verz if d != "__pycache__"]
        for d in dateien:
            if d.endswith(".py"):
                p = os.path.join(wurzel, d)
                treffer.append(os.path.relpath(p, WURZEL).replace("\\", "/"))
    return sorted(treffer)


def dateien_im_protokoll(text):
    """Dateien, die im collect-Protokoll mindestens EINEN Fall tragen."""
    gefunden = set()
    for zeile in text.splitlines():
        zeile = zeile.strip()
        if "::" not in zeile:
            continue
        pfad = zeile.split("::", 1)[0]
        if pfad.endswith(".py"):
            gefunden.add(pfad.replace("\\", "/"))
    return gefunden


def faelle_je_datei(text):
    zaehler = {}
    for zeile in text.splitlines():
        zeile = zeile.strip()
        if "::" not in zeile:
            continue
        pfad = zeile.split("::", 1)[0].replace("\\", "/")
        if pfad.endswith(".py"):
            zaehler[pfad] = zaehler.get(pfad, 0) + 1
    return zaehler


def grund(pfad):
    """Warum traegt diese Datei keinen eingesammelten Fall?"""
    name = os.path.basename(pfad)
    voll = os.path.join(WURZEL, pfad)
    try:
        with open(voll, "r", encoding="utf-8", errors="replace") as f:
            quelle = f.read()
    except OSError as e:
        return "nicht lesbar: %s" % e
    hat_testfn = re.search(r"^\s*(async\s+)?def\s+test", quelle, re.M) is not None
    hat_testklasse = re.search(r"^\s*class\s+Test", quelle, re.M) is not None
    if name == "conftest.py":
        return "conftest.py - Fixtures, kein Traeger von Faellen (erwartet)"
    if not name.startswith("test_") and not name.endswith("_test.py"):
        if hat_testfn or hat_testklasse:
            return ("DATEINAME passt auf kein Sammelmuster (test_*.py), "
                    "enthaelt aber %d def test*/class Test - wird NIE gefahren"
                    % len(re.findall(r"^\s*(?:async\s+)?def\s+test", quelle, re.M)))
        return "Hilfsmodul ohne def test* (erwartet)"
    if not (hat_testfn or hat_testklasse):
        return "Name passt, enthaelt aber KEINE def test*/class Test"
    return ("Name passt UND enthaelt def test*, taucht aber nicht auf - "
            "Import-/Sammelfehler, Datei einzeln pruefen")


def messe(protokolltext, testdir):
    platte = dateien_auf_der_platte(testdir)
    protokoll = dateien_im_protokoll(protokolltext)
    fehlt = [p for p in platte if p not in protokoll]
    return platte, protokoll, fehlt


def bericht(protokolltext, testdir, praefix=""):
    platte, protokoll, fehlt = messe(protokolltext, testdir)
    print("%sDateien auf der Platte (.py, ohne __pycache__): %d" % (praefix, len(platte)))
    print("%sDateien mit mindestens einem eingesammelten Fall: %d" % (praefix, len(protokoll)))
    print("%sOHNE eingesammelten Fall: %d" % (praefix, len(fehlt)))
    for p in fehlt:
        print("%s  - %s" % (praefix, p))
        print("%s      %s" % (praefix, grund(p)))
    verwaist = sorted(protokoll - set(platte))
    if verwaist:
        print("%sim Protokoll, aber nicht auf der Platte: %d" % (praefix, len(verwaist)))
        for p in verwaist:
            print("%s  ! %s" % (praefix, p))
    return fehlt


KOEDER_DATEIEN = {
    # 1: richtiger Name, aber kein Fall drin
    "test_leer.py": "x = 1\n\ndef hilf():\n    return 2\n",
    # 2: falscher Dateiname, Faelle drin -> laeuft NIE
    "pruefe_etwas.py": "def test_das_laeuft_nie():\n    assert False\n",
    # 3: Name passt, Importfehler
    "test_importbruch.py": "import ein_modul_das_es_nicht_gibt\n\ndef test_a():\n    assert True\n",
    # 4: Name passt, nur eine Klasse ohne Test-Praefix
    "test_falsche_klasse.py": "class Pruefungen:\n    def test_drin(self):\n        assert False\n",
    # Gegenprobe: dieser MUSS eingesammelt werden
    "test_echt.py": "def test_der_wird_gesammelt():\n    assert True\n",
}


def koeder():
    """Selbstprobe: vier bekannte Ausfaelle, einer davon muss gefunden werden."""
    global WURZEL
    with tempfile.TemporaryDirectory() as tmp:
        WURZEL = tmp
        td = os.path.join(tmp, "tests")
        os.makedirs(td)
        for name, inhalt in KOEDER_DATEIEN.items():
            with open(os.path.join(td, name), "w", encoding="utf-8", newline="") as f:
                f.write(inhalt)
        logpfad = os.path.join(tmp, "collect.log")
        with open(logpfad, "w", encoding="utf-8", newline="") as f:
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
                cwd=tmp, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=300)
            f.write((r.stdout or "") + (r.stderr or ""))
        with open(logpfad, "r", encoding="utf-8") as f:
            text = f.read()
        print("KOEDER-LAUF, pytest-Rueckgabewert = %d" % r.returncode)
        print("-" * 60)
        fehlt = bericht(text, td, praefix="  ")
        print("-" * 60)
        erwartet = {"tests/test_leer.py", "tests/pruefe_etwas.py",
                    "tests/test_importbruch.py", "tests/test_falsche_klasse.py"}
        gefunden = set(fehlt)
        nicht_gefunden = erwartet - gefunden
        falsch_gemeldet = gefunden - erwartet
        for p in sorted(erwartet):
            print("  %-34s %s" % (p, "GEFUNDEN" if p in gefunden else "NICHT GEFUNDEN"))
        print("  %-34s %s" % ("tests/test_echt.py (Gegenprobe)",
                              "korrekt NICHT gemeldet" if "tests/test_echt.py"
                              not in gefunden else "FALSCH gemeldet"))
        if nicht_gefunden or falsch_gemeldet:
            print("SELBSTPROBE ROT")
            return 1
        print("SELBSTPROBE GRUEN - der Vergleich findet alle vier Ausfallarten.")
        return 0


def main(argv):
    if "--koeder" in argv:
        return koeder()
    if not argv:
        print("Aufruf: befund_einsammeln.py <collect.log> | --koeder")
        return 2
    with open(argv[0], "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r"PYTEST_RC=(\d+)", text)
    print("pytest-Rueckgabewert aus der Logdatei: %s" % (m.group(1) if m else "NICHT PROTOKOLLIERT"))
    fehler = re.findall(r"^(ERROR|ERRORS?\b).*$", text, re.M)
    print("Zeilen mit ERROR im Protokoll: %d" % len(fehler))
    print("-" * 60)
    fehlt = bericht(text, os.path.join(WURZEL, "tests"))
    print("-" * 60)
    zaehler = faelle_je_datei(text)
    print("Summe eingesammelter Faelle: %d" % sum(zaehler.values()))
    duenn = sorted((v, k) for k, v in zaehler.items() if v <= 1)
    print("Dateien mit nur EINEM Fall: %d" % len(duenn))
    for v, k in duenn:
        print("  %s" % k)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
