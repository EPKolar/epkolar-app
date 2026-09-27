# -*- coding: utf-8 -*-
"""Faehrt die REINEN LESER und misst Rueckgabewert und Laufzeit.

WARUM NICHT IN DER MUSCHEL
──────────────────────────
`node scripts/x.mjs | tail` meldet den Rueckgabewert von `tail`. Jedes Skript
laeuft hier als eigener Prozess ohne Pipe, `returncode` wird EINZELN gelesen
und die Ausgabe erst danach in eine Logdatei geschrieben. Das Urteil steht in
der Logdatei, nicht auf dem Schirm.

WAS HIER NICHT LAEUFT
─────────────────────
Jedes Skript, das schreibt oder migriert. Die Liste steht in AUS und ist mit
Grund je Zeile begruendet - ein Messlauf, der nebenbei das Repo aendert, ist
keine Messung.

Laufzeit wird DREIMAL genommen und der Mittelwert der letzten zwei gemeldet:
der erste Lauf traegt den Dateisystem-Zwischenspeicher fuer index.html
(3,6 MB), und das ist nicht die Zahl, die die Torkette kosten wuerde.

AUFRUF
──────
    python scripts/befund_leser_lauf.py
    python scripts/befund_leser_lauf.py --wirkung   Mutationsprobe an KOPIEN
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(WURZEL, "docs", "befunde", "_leser_lauf.log")

PY = sys.executable

# (Name, Befehl, Umgebung-Zusatz)
EIN = [
    ("scripts/a2_dryrun.mjs", ["node", "scripts/a2_dryrun.mjs"], {}),
    ("scripts/anker_schneiden.py", [PY, "scripts/anker_schneiden.py"], {}),
    ("scripts/b3_12_15_quelltext.py", [PY, "scripts/b3_12_15_quelltext.py"], {}),
    ("scripts/bestand.py", [PY, "scripts/bestand.py"], {}),
    ("scripts/freivar/selbsttest.js", ["node", "scripts/freivar/selbsttest.js"], {}),
    ("scripts/md5_geschuetzt.py", [PY, "scripts/md5_geschuetzt.py"], {}),
    ("scripts/paare_v931_ausgetretene.py",
     [PY, "scripts/paare_v931_ausgetretene.py"], {}),
    ("scripts/verify_sync_behavior.cjs",
     ["node", "scripts/verify_sync_behavior.cjs"], {}),
    ("sql/_check_brackets.js", ["node", "sql/_check_brackets.js"], {}),
]

# Nicht gefahren, je mit Grund. Die Begruendung steht hier und nicht im
# Bericht, damit sie neben dem Code liegt, der sie betrifft.
AUS = {
    "scripts/ansicht_inventar.py":
        "schreibt eine Inventardatei und braucht --ansicht",
    "scripts/b3_bestand_quelltext.py":
        "schreibt einen Vergleichsstand nach docs/",
    "scripts/bughunt-state-update.ps1":
        "SCHREIBT per Set-Content in die uebergebene Zustandsdatei",
    "scripts/freivar/mutation.js":
        "legt scripts/freivar/_mut.html im REPO an (3,6 MB, 25 Mutationen)",
    "scripts/icons_erzeugen.py":
        "schreibt PNG-Dateien in die Repo-Wurzel - ein Erzeuger, kein Pruefer",
    "scripts/torkette.py":
        "IST die Kette; ein Kandidat kann nicht in sich selbst haengen",
}


def fahre(befehl, zusatz=None):
    """Ein Lauf, ein eigener Prozess, kein shell, keine Pipe."""
    umg = dict(os.environ)
    if zusatz:
        umg.update(zusatz)
    t0 = time.time()
    try:
        r = subprocess.run(befehl, cwd=WURZEL, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900,
                           env=umg)
    except FileNotFoundError as e:
        return None, time.time() - t0, "liess sich nicht starten: %s" % e
    except subprocess.TimeoutExpired:
        return None, time.time() - t0, "Zeitgrenze 900 s ueberschritten"
    return r.returncode, time.time() - t0, ((r.stdout or "") + (r.stderr or ""))


def main(argv):
    if "--wirkung" in argv:
        return wirkung()
    zeilen = []
    with open(LOG, "w", encoding="utf-8", newline="") as log:
        log.write("LESER-LAUF  %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
        log.write("=" * 74 + "\n\n")
        for name, befehl, zusatz in EIN:
            dauern = []
            rc = None
            ausgabe = ""
            for i in range(3):
                rc, d, ausgabe = fahre(befehl, zusatz)
                dauern.append(d)
            # Erster Lauf verworfen: er traegt den Datei-Zwischenspeicher.
            mittel = sum(dauern[1:]) / len(dauern[1:])
            zeilen.append((name, rc, mittel, dauern[0]))
            log.write("--- %s\n" % name)
            log.write("Befehl:          %s\n" % " ".join(befehl))
            log.write("Rueckgabewert:   %s\n" % rc)
            log.write("Laufzeit (kalt): %.2f s\n" % dauern[0])
            log.write("Laufzeit (warm): %.2f s  (Mittel aus 2)\n" % mittel)
            log.write("Ausgabe:\n")
            log.write(ausgabe.strip()[:4000] + "\n\n")
        log.write("=" * 74 + "\n")
        log.write("NICHT GEFAHREN:\n")
        for name, grund in sorted(AUS.items()):
            log.write("  %-38s %s\n" % (name, grund))
    print("%-38s %-4s %8s %8s" % ("Skript", "rc", "kalt", "warm"))
    print("-" * 62)
    for name, rc, mittel, kalt in zeilen:
        print("%-38s %-4s %7.2fs %7.2fs" % (name, rc, kalt, mittel))
    print("")
    print("Logdatei: %s" % LOG)
    print("Nicht gefahren: %d (Gruende in der Logdatei)" % len(AUS))
    return 0


# ── Mutationsprobe: wird der Pruefer ROT, wenn sein Gegenstand kaputt ist? ────
# Nie an index.html. Jede Probe laeuft auf einer KOPIE in einem Wegwerfbaum,
# und der Pruefer wird ueber EPK_INDEX auf die Kopie gezeigt - oder, wenn er
# EPK_INDEX nicht kennt, im Wegwerfbaum selbst gefahren.
# (Pruefer, Befehl, Mutation, SOLL-Wirkung, Satz)
# SOLL-Wirkung True  = der Pruefer MUSS bei dieser Mutation rot werden
# SOLL-Wirkung False = er darf es NICHT - und das ist dann der Befund, nicht
#                      ein Fehler der Probe. Eine Probe, die nur eine
#                      Richtung kennt, kann nicht zwischen "wirkt nicht" und
#                      "soll nicht wirken" unterscheiden.
MUTATIONEN = [
    ("scripts/md5_geschuetzt.py", [PY, "scripts/md5_geschuetzt.py"],
     "rumpf", True,
     "md5 einer geschuetzten Funktion veraendert -> MUSS rot werden"),
    ("scripts/bestand.py", [PY, "scripts/bestand.py"],
     "begriff", True,
     "ein Bestandsbegriff ueberall aus index.html entfernt -> MUSS rot "
     "werden"),
    ("scripts/b3_12_15_quelltext.py", [PY, "scripts/b3_12_15_quelltext.py"],
     "fontsize", False,
     "fontSize unter 12 eingesetzt -> bleibt gruen. Der Pruefer BERICHTET "
     "seinen Gegenstand und urteilt nur ueber seine eigene Eichung "
     "(raise SystemExit, Zeile 115). Als Tor taugt er so nicht."),
    # Die ATTRAPPEN-PROBE. Beide Skripte tragen eine ABSCHRIFT der Logik aus
    # index.html im eigenen Quelltext ("repliziert ... VERBATIM"). Wenn das
    # Original kaputtgeht, MUESSEN sie es uebersehen - denn sie lesen es gar
    # nicht. Erwartet ist deshalb "wirkt nicht", und genau das ist der
    # Befund: als Tor wuerden sie gruen melden, waehrend der Gegenstand rot
    # ist. Ein Riegel auf einer Kopie schuetzt die Kopie.
    ("scripts/a2_dryrun.mjs", ["node", "scripts/a2_dryrun.mjs"],
     "juprowa", False,
     "JUPROWA_STATUS_MAP in index.html verdreht -> bleibt gruen. Die Tabelle "
     "steht ABGESCHRIEBEN im Skript; index.html wird nicht gelesen."),
    ("scripts/verify_sync_behavior.cjs",
     ["node", "scripts/verify_sync_behavior.cjs"],
     "sync", False,
     "die doSync-Schleife in index.html zerstoert -> bleibt gruen. Die "
     "Schleife steht ABGESCHRIEBEN im Skript."),
    # Diese Probe mutiert NICHT index.html, sondern eine PNG-Kopie. Sie steht
    # trotzdem hier, damit alle sechs Proben mit EINEM Aufruf nachfahrbar
    # sind - eine Probe, die nur in der Erinnerung des Messenden existiert,
    # ist kein Beleg.
    ("scripts/icons_erzeugen.py --pruefen",
     [PY, "scripts/icons_erzeugen.py", "--pruefen"],
     "icon", True,
     "ein Byte in icon-192.png gekippt -> MUSS rot werden"),
]

# Welche Datei die Mutation trifft. Vorgabe ist index.html.
MUT_ZIEL = {"icon": "icon-192.png"}
ICONS = ("icon-192.png", "icon-512.png", "icon-192-maskable.png",
         "icon-512-maskable.png")


def baum():
    """Ein Wegwerfbaum mit KOPIEN. Im Repo wird nichts angefasst."""
    t = tempfile.mkdtemp(prefix="leser_wirkung_")
    for d in ("scripts", "sql", "docs"):
        shutil.copytree(os.path.join(WURZEL, d), os.path.join(t, d),
                        ignore=shutil.ignore_patterns("__pycache__",
                                                      "node_modules"))
    # node_modules von freivar wird gebraucht, aber nicht kopiert (gross):
    shutil.copy2(os.path.join(WURZEL, "index.html"),
                 os.path.join(t, "index.html"))
    for p in ICONS:
        q = os.path.join(WURZEL, p)
        if os.path.exists(q):
            shutil.copy2(q, os.path.join(t, p))
    return t


def wirkung():
    t = baum()
    print("Wegwerfbaum: %s" % t)
    rot = 0
    try:
        for name, befehl, art, soll, was in MUTATIONEN:
            # Jede Probe trifft EINE Datei - meist index.html, bei den Icons
            # eine PNG. Text wird als Text gelesen (newline="" haelt die
            # CRLF-Zeilenenden), Bilder binaer.
            ziel = os.path.join(t, MUT_ZIEL.get(art, "index.html"))
            binaer = ziel.endswith(".png")
            if binaer:
                original = open(ziel, "rb").read()
            else:
                original = open(ziel, encoding="utf-8", newline="").read()
            # 1 unveraendert: der Pruefer MUSS gruen sein, sonst misst die
            #   Probe nur, dass die Kopie kaputt ist.
            schreibe(ziel, original, binaer)
            r0 = subprocess.run(befehl, cwd=t, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                timeout=900)
            # 2 kaputt: der Pruefer MUSS rot werden.
            kaputt = mutiere(original, art)
            if kaputt == original:
                print("%-34s KOEDER GRIFF NICHT - Mutation %r aenderte nichts"
                      % (name, art))
                rot += 1
                continue
            schreibe(ziel, kaputt, binaer)
            r1 = subprocess.run(befehl, cwd=t, capture_output=True, text=True,
                                encoding="utf-8", errors="replace",
                                timeout=900)
            wirkt = (r1.returncode != 0)
            ok = (r0.returncode == 0) and (wirkt == soll)
            if not ok:
                rot += 1
            print("%-34s unveraendert rc=%s  kaputt rc=%s  %-11s %s"
                  % (name, r0.returncode, r1.returncode,
                     "WIRKT" if wirkt else "wirkt nicht",
                     "wie erwartet" if ok else "NICHT WIE ERWARTET"))
            print("      %s" % was)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print("")
    print("%d von %d Proben nicht wie erwartet." % (rot, len(MUTATIONEN)))
    return 1 if rot else 0


def schreibe(ziel, inhalt, binaer):
    if binaer:
        with open(ziel, "wb") as f:
            f.write(inhalt)
        return
    # newline="" - sonst stellt Python auf Windows JEDE Zeile auf CRLF um.
    with open(ziel, "w", encoding="utf-8", newline="") as f:
        f.write(inhalt)


def mutiere(s, art):
    if art == "icon":
        # EIN Byte im Bilddaten-Teil kippen, die Laenge bleibt gleich: ein
        # Pruefer, der nur die Dateigroesse vergleicht, wuerde das uebersehen.
        d = bytearray(s)
        d[-40] ^= 0xFF
        return bytes(d)
    if art == "rumpf":
        # Eine Zeile IM Rumpf einer geschuetzten Funktion aendern.
        i = s.find("function _ezEffTage")
        if i < 0:
            return s
        j = s.find("\n", i + 30)
        return s[:j] + "\n  /*zZmutZz*/" + s[j:]
    if art == "begriff":
        # EIGENER FEHLER, hier ausgebaut: die erste Fassung ersetzte den
        # Begriff nur EINMAL (`replace(b, ..., 1)`). bestand.py prueft aber
        # `if not any(k in quelle ...)` - solange der Begriff irgendwo sonst
        # noch steht, ist er GEFUNDEN. Die Probe meldete darum "WIRKT NICHT"
        # fuer einen Riegel, der einwandfrei wirkt. Ein Koeder, der seinen
        # Gegenstand nicht trifft, ist eine leere Grundgesamtheit und belegt
        # NICHTS - schon gar nicht das Gegenteil.
        # Genommen wird ein Begriff aus bestand.py's EIGENER Liste, und er
        # wird UEBERALL entfernt.
        for b in ("Bautagebuch", "Kabelwerkzeug", "Verloren/Defekt"):
            if b in s:
                return s.replace(b, "zZwegZz")
        return s
    if art == "juprowa":
        # Die Statustabelle im ORIGINAL verdrehen.
        i = s.find("JUPROWA_STATUS_MAP")
        if i < 0:
            return s
        j = s.find("'0':'aufgenommen'", i)
        if j < 0:
            j = s.find('"0":"aufgenommen"', i)
        if j < 0:
            # Keine erkennbare Tabelle -> lieber gar keine Mutation als eine,
            # die nichts trifft. Ein Koeder, der nicht greift, belegt nichts.
            return s
        return s[:j] + s[j:].replace("aufgenommen", "zZkaputtZz", 1)
    if art == "sync":
        i = s.find("syncQueueFailed")
        if i < 0:
            return s
        return s[:i] + "zZkaputtZz" + s[i + len("syncQueueFailed"):]
    if art == "fontsize":
        i = s.find("fontSize:13")
        if i < 0:
            i = s.find("fontSize:12")
        if i < 0:
            return s
        return s[:i] + "fontSize:7" + s[i + len("fontSize:13"):]
    return s


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
