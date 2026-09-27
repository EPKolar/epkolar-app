# -*- coding: utf-8 -*-
"""Messung zu `docs/befunde/DIE_31_VERDACHTE.md`, Teil 2: die MUTATIONSPROBE.

Fuer die Verdachte, deren Datei KEINE eigene Selbstprobe traegt, wird hier
gemessen, ob der Fall ueberhaupt rot werden KANN: ein Koeder wird in eine
KOPIE von index.html eingebaut und genau dieser eine Fall gefahren.

  Koeder    -> der Fall MUSS rot werden
  Gegenprobe-> der Fall MUSS gruen bleiben

🔴 `index.html` im Repo wird NIE angefasst. Gearbeitet wird in einem
Wegwerfbaum (`git archive HEAD`), den `--baum` benennt; dort liegt eine
eigene `index.html`, eine eigene `tests/` und eine eigene `scripts/`.
Die Vorrichtung `index_html` in `tests/conftest.py` liest `repo_root`,
und `repo_root` ist das Elternverzeichnis von `tests/` - deshalb greift
die Mutation, ohne dass eine Testdatei geaendert wird.

Der Rueckgabewert wird aus der LOGDATEI gelesen, nie hinter einer Pipe.

Aufruf:
    python scripts/befund_31_mutation.py --baum <wegwerfbaum> [--nur D21]
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ═══ Die Proben ════════════════════════════════════════════════════════════
# (schluessel, nodeid, [(name, art, einbau)], ...)
#   art: "rot"  -> der Fall muss nach dem Einbau ROT sein
#        "gruen"-> der Fall muss GRUEN bleiben (Gegenprobe)
#   einbau: Funktion(text) -> neuer Text  oder  None, wenn nicht baubar


def _am_ende(zeile):
    def f(t):
        return t + "\n" + zeile + "\n"
    return f


def _vor_head_ende(stueck):
    def f(t):
        i = t.lower().find("</head>")
        return t[:i] + stueck + t[i:]
    return f


_BAUM = [None]


def _modul(pfad, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, pfad)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _hook_in_app(t):
    """Baut einen React-Hook ZWISCHEN den ersten und den letzten return des
    App-Rumpfes - genau die Verletzung, die der Riegel behauptet auszuschliessen.

    🔴 Die Stellen werden mit den MUSTERN DES RIEGELS SELBST gesucht
    (`HOOK_RE`, `RETURN_RE`, `APP_OPEN_RE`, `_function_span`), nicht mit
    eigenen. Ein erster Versuch baute `  const [x,setX]=React.useState(0);`
    ein und blieb gruen - der Riegel sucht aber `^  _react\\.useState`.
    Eine Probe mit einer ANDEREN Definition von "Hook" misst nicht den
    Riegel, sondern den eigenen Irrtum, und haette ihn faelschlich fuer
    blind erklaert.
    """
    m = _modul(os.path.join(_BAUM[0], "tests", "test_hook_order_static.py"),
               "_koeder_hook_order")
    zeilen = t.split("\n")
    start = None
    for i, z in enumerate(zeilen):
        if m.APP_OPEN_RE.match(z):
            start = i
            break
    if start is None:
        return None
    ende = m._function_span(zeilen, start)
    rets = [i for i in range(start + 1, ende) if m.RETURN_RE.match(zeilen[i])]
    if len(rets) < 2:
        return None
    koeder = "  _react.useState(0);"
    if not m.HOOK_RE.match(koeder):
        return None          # Selbstprobe: der Koeder MUSS das Muster treffen
    zeilen.insert(rets[0] + 1, koeder)
    return "\n".join(zeilen)


PROBEN = [
    ("D21", "tests/test_projekt_cache_v927.py::"
            "test_die_projektbezogenen_listen_gehen_ueber_saveProj_und_loadProj",
     [("ODB.save(\"docs_...\") - doppelte Anfuehrung", "rot",
       _am_ende('<script>ODB.save("docs_koeder31",1);</script>')),
      ("ODB.save('docs_...') - EINFACHE Anfuehrung", "rot",
       _am_ende("<script>ODB.save('docs_koeder31',1);</script>")),
      ("GEGENPROBE ODB.save(\"andere_...\")", "gruen",
       _am_ende('<script>ODB.save("andere_koeder31",1);</script>'))]),

    ("D22", "tests/test_schrift_und_tokens_v933.py::"
            "test_die_schrift_kommt_aus_dem_repo_und_nicht_von_google",
     [("url('https://fonts.gstatic.com/..') im Kopf", "rot",
       _vor_head_ende("<style>@font-face{src:url("
                      "'https://fonts.gstatic.com/koeder31.woff2')}</style>")),
      ('<link href="https://fonts.googleapis.com/..">', "rot",
       _vor_head_ende('<link rel="stylesheet" '
                      'href="https://fonts.googleapis.com/css2?family=Roboto">')),
      ("GEGENPROBE url('./fonts/koeder31.woff2')", "gruen",
       _vor_head_ende("<style>@font-face{src:url('./fonts/koeder31.woff2')}"
                      "</style>"))]),

    ("D28", "tests/test_zulagen_saetze_v768.py::test_keine_taggeld_anzeige_mehr",
     [("'Taggeld alt' - einfache Anfuehrung", "rot",
       _am_ende("<script>var _k31='Taggeld alt';</script>")),
      ('"Taggeld alt" - doppelte Anfuehrung', "rot",
       _am_ende('<script>var _k31="Taggeld alt";</script>')),
      ("`Taggeld alt` - Vorlagenliteral", "rot",
       _am_ende("<script>var _k31=`Taggeld alt`;</script>")),
      ("GEGENPROBE // Taggeld als Prosa im Kommentar", "gruen",
       _am_ende("// Taggeld als Prosa im Kommentar"))]),

    ("D10", "tests/test_hook_order_static.py::test_no_hook_after_early_return_in_App",
     [("React-Hook zwischen erstem und letztem return im App-Rumpf", "rot",
       _hook_in_app)]),

    # 🔴 Der Koeder fuer D25 stand zuerst auf ✏️ - das Zeichen steht NICHT in
    # der Liste SYMBOLE des Riegels, und beide Proben blieben gruen. Ein Koeder,
    # der die Definition des Riegels nicht kennt, misst den eigenen Irrtum.
    # Jetzt ✕ (U+2715), aus SYMBOLE.
    # Vertreter der haeufigsten Form: die leere Menge ist eine EINZELNE Runde
    # einer Schleife, deren Stelle in anderen Runden gefuellt war. Hier muss
    # belegt werden, dass der Fall trotzdem rot werden kann.
    ("D03", "tests/test_b3_stufen_4_7_v942.py::"
            "test_keine_header_regel_geht_unter_44_px",
     [("min-height:20px in einer .header-row .mob-stack button-Regel", "rot",
       _am_ende("<style>.header-row .mob-stack button {min-height:20px}"
                "</style>")),
      ("GEGENPROBE min-height:20px in einer ANDEREN Regel", "gruen",
       _am_ende("<style>.irgendwas button {min-height:20px}</style>"))]),

    ("D25", "tests/test_symbolknoepfe_haben_namen_v957.py::"
            "test_kein_symbolknopf_ohne_namen",
     [("namenloser Symbolknopf als createElement('button'", "rot",
       _am_ende("<script>React.createElement('button',{onClick:x},"
                '"✕");</script>')),
      ("derselbe Knopf als h('button'  (Kuerzel)", "rot",
       _am_ende("<script>h('button',{onClick:x},"
                '"✕");</script>')),
      ("GEGENPROBE derselbe Knopf MIT title", "gruen",
       _am_ende("<script>React.createElement('button',"
                '{onClick:x,title:"Bearbeiten"},"✕");</script>'))]),

    ("D29", "tests/test_zusammengesetzte_knopfnamen_v960.py::"
            "test_wer_seinen_text_verlieren_kann_hat_einen_namen",
     [("namenloser Knopf als React.createElement('button'", "rot",
       _am_ende("<script>React.createElement('button',{onClick:x},"
                '"✖",h("span",{className:"nurgross"},"Loeschen"));'
                ".nurgross{display:none}</script>")),
      ("derselbe Knopf als h('button'  (Kuerzel)", "rot",
       _am_ende("<script>h('button',{onClick:x},"
                '"✖",h("span",{className:"nurgross"},"Loeschen"));'
                ".nurgross{display:none}</script>"))]),
]


def _lauf(baum, nodeid, log):
    with io.open(log, "w", encoding="utf-8", newline="") as f:
        r = subprocess.run([sys.executable, "-m", "pytest", nodeid, "-q",
                            "--no-header", "-p", "no:cacheprovider"],
                           cwd=baum, stdout=f, stderr=subprocess.STDOUT)
    with io.open(log, "a", encoding="utf-8", newline="") as f:
        f.write("\nPYTEST_RC=%d\n" % r.returncode)
    # Urteil AUS DER DATEI, nicht aus dem Rueckgabewert der Pipe
    with io.open(log, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()
    m = re.search(r"PYTEST_RC=(\d+)", txt)
    return int(m.group(1)), txt


def main(argv):
    if "--baum" not in argv:
        print("Aufruf: befund_31_mutation.py --baum <wegwerfbaum> [--nur D21]")
        return 2
    baum = argv[argv.index("--baum") + 1]
    _BAUM[0] = baum
    nur = argv[argv.index("--nur") + 1].split(",") if "--nur" in argv else None
    index = os.path.join(baum, "index.html")
    if not os.path.isfile(index):
        print("Kein index.html in %s" % baum)
        return 2
    sicherung = index + ".urfassung"
    if not os.path.isfile(sicherung):
        shutil.copy2(index, sicherung)
    logs = tempfile.mkdtemp(prefix="mut31_")
    with io.open(sicherung, "r", encoding="utf-8") as f:
        original = f.read()

    print("Wegwerfbaum: %s" % baum)
    print("index.html dort: %d Zeichen" % len(original))
    print("=" * 78)

    # Grundstand: JEDER gepruefte Fall muss OHNE Mutation gruen sein.
    # Ohne das belegt ein spaeteres Rot gar nichts.
    print("GRUNDSTAND (ohne Mutation) - jeder Fall muss gruen sein:")
    for schluessel, nodeid, _ in PROBEN:
        if nur and schluessel not in nur:
            continue
        rc, _t = _lauf(baum, nodeid, os.path.join(logs, schluessel + "_basis.log"))
        print("   %-5s %-70s rc=%d %s"
              % (schluessel, nodeid.split("::")[1][:70], rc,
                 "GRUEN" if rc == 0 else "ROT - Grundstand kaputt!"))
    print("=" * 78)

    richtig = falsch = 0
    for schluessel, nodeid, proben in PROBEN:
        if nur and schluessel not in nur:
            continue
        print("")
        print("%s  %s" % (schluessel, nodeid))
        for i, (name, art, einbau) in enumerate(proben):
            if einbau is None:
                print("   %-58s NICHT BAUBAR" % name)
                continue
            neu = einbau(original)
            if neu is None or neu == original:
                print("   %-58s EINBAU MISSLUNGEN - keine Aussage" % name)
                falsch += 1
                continue
            with io.open(index, "w", encoding="utf-8", newline="") as f:
                f.write(neu)
            try:
                rc, _t = _lauf(baum, nodeid,
                               os.path.join(logs, "%s_%d.log" % (schluessel, i)))
            finally:
                with io.open(index, "w", encoding="utf-8", newline="") as f:
                    f.write(original)
            erwartet_rot = (art == "rot")
            ist_rot = (rc != 0)
            ok = ist_rot == erwartet_rot
            richtig += ok
            falsch += (not ok)
            print("   %-58s %s  rc=%d (%s, erwartet %s)"
                  % (name, "OK    " if ok else "LUECKE",
                     rc, "ROT" if ist_rot else "GRUEN",
                     "ROT" if erwartet_rot else "GRUEN"))
    print("")
    print("=" * 78)
    print("Proben: %d richtig, %d Luecken. Logdateien: %s"
          % (richtig, falsch, logs))
    # index.html im Wegwerfbaum ist wiederhergestellt:
    with io.open(index, "r", encoding="utf-8") as f:
        assert f.read() == original, "Wegwerfbaum nicht zurueckgesetzt!"
    print("Wegwerfbaum zurueckgesetzt: index.html wieder in der Urfassung.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
