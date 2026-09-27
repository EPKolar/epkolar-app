# -*- coding: utf-8 -*-
"""v3.9.961 - die sieben geschuetzten Funktionen, jetzt IM LAUF geprueft.

🔴 DER FUND: DIE EINZIGE ZUSICHERUNG FUER SIEBEN LOHNNAHE FUNKTIONEN LIEF NIRGENDS
──────────────────────────────────────────────────────────────────────────────────
`scripts/md5_geschuetzt.py` haelt die Byte-Identitaet von

    _ezEffTage        Entfernungszulage, effektive Tage (lohnnah)
    _asEskalierbar    Arbeitsschein-Eskalation
    _dispoPlan        Dispo-Planung
    _maIstEhemalig    wer ist ausgeschieden
    _maWaehlbar       wer ist waehlbar
    _juprowaPush      Push nach JUPROWA
    _juprowaSanitize  Saeuberung davor

Sein eigener Dateikopf beginnt mit den Worten **"Gate 5"**. Es ist nie eines
geworden: kein Skript ruft es auf, keine Kette fuehrt es, und **keine einzige
der sieben Pruefsummen steht in irgendeiner Testdatei** (vollstaendig gesucht
am 27.09.2026).

Dabei verweisen ZWEI Tests ausdruecklich darauf:
    tests/test_austritt_eine_regel_v950.py:181  "haelt scripts/md5_geschuetzt.py fest"
    tests/test_b3_stufen_12_15_v946.py:83       "(das haelt scripts/md5_geschuetzt.py fest)"

Die Zusicherung wurde also an etwas delegiert, das nie gefahren wird. Gefahren
habe ich es waehrend des ganzen Laufs von Hand nach jeder Stufe - aber Disziplin
ist kein Riegel, und der naechste Mensch weiss davon nichts.

Seit v3.9.961 laeuft es an ZWEI Stellen: als eigenes Tor in
`scripts/torkette.py` (0,06 s) und hier, damit es auch in den 3210 Faellen
steckt. Zwei Eingaenge, eine Wahrheit: beide benutzen dieselbe Tabelle aus
`md5_geschuetzt.py`.

WARUM DIE TABELLE HIER NICHT ABGESCHRIEBEN STEHT
────────────────────────────────────────────────
Eine zweite Kopie der sieben Summen waere eine zweite Stelle, die beim
naechsten bewussten Umbau nachgezogen werden muss - und wer eine vergisst,
bekommt einen Riegel, der auf einen alten Stand zeigt. Deshalb wird
`md5_geschuetzt.SOLL` und `md5_geschuetzt.summen` IMPORTIERT. Faellt das
Skript weg, faellt diese Datei mit auf - das ist gewollt.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob die Funktionen RICHTIG sind. Gemessen wird nur, dass sie sich nicht
geaendert haben. Eine falsche Funktion, die sich nicht aendert, bleibt gruen -
dafuer sind die ausfuehrenden Riegel daneben da.
"""
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "scripts"))
import md5_geschuetzt  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust, keine md5-Frage. "
            "Eine leere Datei enthaelt die Funktionen uebrigens auch nicht, "
            "und 'nicht gefunden' darf nie wie 'nichts zu beanstanden' "
            "aussehen." % len(roh))
    return roh


def test_die_tabelle_ist_die_des_werkzeugs():
    """Sieben Eintraege, importiert statt abgeschrieben.

    Waere die Tabelle hier kopiert, gaebe es zwei Staende, die auseinander
    laufen koennen - und der Riegel zeigte dann auf einen alten.
    """
    assert len(md5_geschuetzt.SOLL) == 7, (
        "Die Tabelle fuehrt %d Funktionen, erwartet 7. Sinkt die Zahl, ist "
        "eine geschuetzte Funktion aus der Aufsicht gefallen - das ist ein "
        "Fehler und kein Aufraeumen." % len(md5_geschuetzt.SOLL))
    for name, soll in md5_geschuetzt.SOLL.items():
        assert len(soll) == 32, "%s: %r ist keine md5-Summe." % (name, soll)


def test_die_sieben_sind_bytegleich():
    """Die eigentliche Aussage - und sie ist FAIL-CLOSED.

    Eine nicht gefundene Funktion ist ROT, nicht gruen. Eine verschwundene
    Funktion ist der schlimmste denkbare Fall, und er darf nie wie
    "nichts zu beanstanden" aussehen.
    """
    ist = md5_geschuetzt.summen(_lies())
    fehlend = [n for n in md5_geschuetzt.SOLL if ist[n] is None]
    assert not fehlend, (
        "%d geschuetzte Funktion(en) sind NICHT GEFUNDEN: %s.\n"
        "Das ist der schlimmste Fall: die Funktion ist weg oder umbenannt. "
        "Fail-closed - hier wird rot gemeldet, nicht gruen."
        % (len(fehlend), ", ".join(fehlend)))
    abweichend = {n: (md5_geschuetzt.SOLL[n], ist[n])
                  for n in md5_geschuetzt.SOLL
                  if ist[n] != md5_geschuetzt.SOLL[n]}
    assert not abweichend, (
        "%d geschuetzte Funktion(en) VERAENDERT:\n%s\n\n"
        "Diese sieben tragen Lohn- und Eskalationslogik und sind ausdruecklich "
        "TABU. Ist die Aenderung gewollt, gehoert die neue Summe in "
        "scripts/md5_geschuetzt.py - mit einem Satz dazu, WER sie entschieden "
        "hat. Ist sie nicht gewollt: zurueck."
        % (len(abweichend),
           "\n".join("  %-18s soll %s\n  %-18s ist  %s"
                     % (n, s, "", i) for n, (s, i) in sorted(abweichend.items()))))


def test_der_riegel_wird_bei_einer_veraenderung_rot():
    """KOEDER. Ohne ihn ist "sieben unveraendert" die Aussage eines Riegels,
    von dem niemand weiss, ob er rot werden KANN - und genau das war er vier
    Wochen lang, weil er nirgends lief.
    """
    roh = _lies()
    anker = "function _maIstEhemalig"
    assert anker in roh, (
        "Der Anker fuer den Koeder fehlt - dann ist _maIstEhemalig weg, und "
        "die Pruefung darueber haette das schon gemeldet.")
    # Ein einziges Zeichen im Rumpf: aus < wird <=. Genau die Aenderung, die
    # den Austrittstag selbst zum Ausscheidetag machen wuerde.
    i = roh.index(anker)
    rumpf = roh[i:i + md5_geschuetzt.LAENGE]
    assert "<" in rumpf, "Im Rumpf steht kein Vergleich - Koeder nicht anwendbar."
    kaputt = roh[:i] + rumpf.replace("<", "<=", 1) + roh[i + md5_geschuetzt.LAENGE:]
    assert kaputt != roh, "Die Mutation hat nichts geaendert."
    ist = md5_geschuetzt.summen(kaputt)
    assert ist["_maIstEhemalig"] != md5_geschuetzt.SOLL["_maIstEhemalig"], (
        "KOEDER NICHT GEFUNDEN: eine geaenderte _maIstEhemalig ergibt dieselbe "
        "Summe. Dann misst der Riegel den Rumpf nicht.")


def test_eine_verschwundene_funktion_ist_rot_und_nicht_gruen():
    """KOEDER auf die Fail-closed-Eigenschaft.

    Das ist die wichtigere der beiden Richtungen: ein Riegel, der bei einer
    VERSCHWUNDENEN Funktion gruen meldet, ist schlimmer als keiner.
    """
    roh = _lies()
    kaputt = roh.replace("function _maWaehlbar", "function _maWaehlbarX", 1)
    assert kaputt != roh, "Die Mutation hat nichts geaendert."
    ist = md5_geschuetzt.summen(kaputt)
    assert ist["_maWaehlbar"] is None, (
        "KOEDER NICHT GEFUNDEN: eine umbenannte Funktion wird nicht als "
        "'nicht gefunden' gemeldet. Dann koennte ein Wegfall unbemerkt "
        "durchgehen.")


def test_die_zwei_tests_die_hierher_verweisen_gibt_es_noch():
    """Zwei Tests delegieren ihre Zusicherung an das Skript.

    Verschwindet einer, ist das kein Fehler - aber der Verweis war der Grund,
    warum die Luecke so lange unsichtbar blieb: es SAH aus, als sei die
    Eigenschaft abgedeckt. Diese Pruefung haelt den Zusammenhang fest, damit
    er beim naechsten Umbau nicht wieder verlorengeht.
    """
    hier = os.path.dirname(os.path.abspath(__file__))
    verweise = []
    for name in os.listdir(hier):
        if not name.startswith("test_") or not name.endswith(".py"):
            continue
        t = io.open(os.path.join(hier, name), encoding="utf-8",
                    errors="replace").read()
        if "md5_geschuetzt.py" in t and name != os.path.basename(__file__):
            verweise.append(name)
    assert verweise, (
        "Keine Testdatei verweist mehr auf scripts/md5_geschuetzt.py. Das ist "
        "kein Fehler - aber dann ist auch der Hinweis weg, dass die "
        "Zusicherung dort liegt. Wenn das so bleiben soll, diese Pruefung mit "
        "einem Satz dazu entfernen.")
