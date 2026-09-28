# -*- coding: utf-8 -*-
"""Ausgetretene Mitarbeiter verschwinden in der Wochenplanung TAGESGENAU.

Regel: bis **einschliesslich** Austrittstag sichtbar, danach nicht mehr.

🔴 WARUM NICHT PAUSCHAL. Ein Filter „ausgetretener MA wird nie angezeigt"
waere eine rueckwirkende Verfaelschung der Wochenhistorie samt Excel- und
PDF-Ausgabe. Wer am Mittwoch austritt, hat Montag und Dienstag gearbeitet, und
das steht so in den Ausgaben.

ANLASSFALL, gepinnt: zwei Mitarbeiter mit `austritt = 2026-07-22`. In KW30
(Mo 20.07. bis Sa 25.07.) bleiben Mo/Di/Mi stehen, Do/Fr verschwinden.

🔴 VIER FUNDSTELLEN, und die vierte war in die ANDERE Richtung falsch: die
Mobil-Wochenkarten loesten ueber `fieldMA` auf, worin Ausgetretene gar nicht
mehr vorkommen - dort verschwanden Mo bis Mi FAELSCHLICH mit. Telefon und
Schreibtisch zeigten unterschiedliche Belegung. Nach der Kur loesen beide
ueber `monteure` auf und filtern ueber denselben Helfer.

DER `!isoTag`-ZWEIG IST ABSICHT und wird hier gepinnt: laesst sich das Datum
nicht ableiten, wird der Chip GEZEIGT. Lieber einer zu viel als eine still
verschwundene Planung.
"""
import io
import json
import os
import re
import subprocess

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD = os.path.join(WURZEL, "index.html")


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _funktion(name):
    """Der Quelltext einer Funktion, aus der DATEI geschnitten.

    Nicht abgeschrieben: eine Abschrift entfernt sich beim naechsten Umbau
    still von der Datei und meldet trotzdem gruen.
    """
    t = _lies()
    i = t.index("function %s(" % name)
    tiefe, j = 0, t.index("{", i)
    k = j
    while k < len(t):
        if t[k] == "{":
            tiefe += 1
        elif t[k] == "}":
            tiefe -= 1
            if tiefe == 0:
                return t[i:k + 1]
        k += 1
    raise AssertionError("\U0001F534 %s laesst sich nicht abgrenzen." % name)


def _helfer_quelle():
    return _funktion("_wpMaSichtbarAmTag")


def _ohne_kommentare(js):
    """Entfernt Block- und Zeilenkommentare.

    🔴 Wer rohen Text durchsucht, misst seine eigene Begruendung mit. Genau
    das ist beim ersten Anlauf dieser Datei passiert: der Kommentar im Helfer
    nennt das Wort `.austritt`, und die Probe darunter wurde davon rot. Der
    Koeder unten belegt beide Richtungen.
    """
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    return re.sub(r"//[^\n]*", " ", js)


def test_koeder_kommentare_werden_entfernt():
    """Beide Richtungen am selben Text."""
    mit = "function f(){ /* liest .austritt nicht */ return 1; }"
    ohne = "function f(){ return w.austritt; }"
    assert ".austritt" not in _ohne_kommentare(mit), (
        "\U0001F534 Ein Kommentar wird mitgemessen.")
    assert ".austritt" in _ohne_kommentare(ohne), (
        "\U0001F534 Echter Code wird mitentfernt - dann findet die Probe nie "
        "etwas.")


def _node(faelle):
    """Fuehrt den Helfer in node aus - am ECHTEN Quelltext.

    🔴 Seit der Umstellung ruft der Helfer `_maIstEhemalig`, und das ruft
    `_ezHeuteISO`. Beide muessen MITGESCHNITTEN werden - sonst laeuft der
    node-Lauf auf einen ReferenceError, und ein Riegel, der am eigenen
    Aufbau scheitert, misst nichts.
    """
    prog = (_funktion("_ezHeuteISO") + "\n"
            + _funktion("_maIstEhemalig") + "\n"
            + _helfer_quelle() + "\n"
            + "const F=" + json.dumps(faelle, ensure_ascii=False) + ";\n"
            + "console.log(JSON.stringify(F.map("
            + "f=>_wpMaSichtbarAmTag(f[0], f[1]))));\n")
    r = subprocess.run(["node", "-e", prog], capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, "\U0001F534 node-Lauf gescheitert:\n%s" % r.stderr
    return json.loads(r.stdout.strip())


def test_die_regel_selbst():
    """Sechs Faelle, in node am echten Quelltext gefahren."""
    faelle = [
        [{"id": "a"}, "2026-07-23"],                       # kein austritt
        [{"id": "a", "austritt": ""}, "2026-07-23"],       # leerer austritt
        [{"id": "a", "austritt": "2026-07-22"}, "2026-07-21"],   # davor
        [{"id": "a", "austritt": "2026-07-22"}, "2026-07-22"],   # AM Tag
        [{"id": "a", "austritt": "2026-07-22"}, "2026-07-23"],   # danach
        [None, "2026-07-23"],                              # kein worker
        [{"id": "a", "austritt": "2026-07-22"}, ""],       # kein Datum
    ]
    soll = [True, True, True, True, False, False, True]
    ist = _node(faelle)
    fehler = [(f, s, i) for f, s, i in zip(faelle, soll, ist) if s != i]
    assert not fehler, (
        "\U0001F534 Die Regel stimmt nicht:\n    %s\n"
        "  Erinnerung: der Austrittstag SELBST zaehlt noch als sichtbar, und "
        "ein fehlendes\n  Datum wird NICHT still verschluckt." % fehler)


def test_der_anlassfall_kw30():
    """Austritt am 22.07.2026: Mo/Di/Mi sichtbar, Do/Fr nicht."""
    w = {"id": "w3", "n": "Cracana", "austritt": "2026-07-22"}
    tage = ["2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23",
            "2026-07-24"]
    ist = _node([[w, t] for t in tage])
    assert ist == [True, True, True, False, False], (
        "\U0001F534 KW30 stimmt nicht: %s\n"
        "  Mo 20.07. bis Mi 22.07. sind gearbeitete Historie und muessen "
        "stehen bleiben." % dict(zip(tage, ist)))


def test_der_austrittstag_selbst_ist_sichtbar():
    """\U0001F534 Die Stelle, an der ein `<` statt `<=` alles kaputt macht.

    Ein Mitarbeiter, der am Mittwoch austritt, hat am Mittwoch gearbeitet. Ein
    `<` statt `<=` loescht diesen Tag aus der Wochenplanung UND aus dem Excel.
    """
    assert _node([[{"austritt": "2026-07-22"}, "2026-07-22"]]) == [True], (
        "\U0001F534 Der Austrittstag selbst wird ausgeblendet. Das ist ein "
        "Tag zu viel:\n  gearbeitete Zeit verschwindet aus dem Raster und aus "
        "den Ausgaben.")


def test_alle_vier_fundstellen_rufen_den_helfer():
    t = _lies()
    stellen = [
        ("Excel-Export", "const xlsCellText=(cell,_dIdx)=>"),
        ("Review-Modell", "const buildDay=(cell,_dIdx)=>"),
        ("Desktop-Tabelle", "const _isoD=dk(dayDate(dIdx));"),
        ("Mobil-Karten", "const _isoM=dk(dayDate(i));"),
    ]
    fehlt = [n for n, a in stellen if a not in t]
    assert not fehlt, (
        "\U0001F534 Diese Fundstellen tragen den Tagbezug nicht mehr: %s"
        % fehlt)
    assert t.count("_wpMaSichtbarAmTag") >= 6, (
        "\U0001F534 Der Helfer wird nur %d mal genannt. Erwartet: die "
        "Deklaration, der\n  window-Export und mindestens vier Fundstellen."
        % t.count("_wpMaSichtbarAmTag"))


def test_die_mobilkarte_loest_NICHT_mehr_ueber_fieldMA_auf():
    """\U0001F534 Der Fehler in die andere Richtung.

    `fieldMA` fuehrt Ausgetretene gar nicht mehr. Solange die Mobil-Karte
    darueber aufloeste, verschwanden Mo bis Mi FAELSCHLICH mit, und Telefon
    und Schreibtisch zeigten unterschiedliche Belegung.
    """
    t = _lies()
    assert "const shown=maIds.slice(0,3).map(id=>{const m=fieldMA.find(" \
        not in t, (
        "\U0001F534 Die Mobil-Karte loest wieder ueber fieldMA auf - dann "
        "verschwinden die\n  Tage VOR dem Austritt faelschlich mit.")
    assert "const maSichtbar=maIds.filter(id=>_wpMaSichtbarAmTag(" in t, (
        "\U0001F534 Die Mobil-Karte filtert nicht mehr vor dem Abschneiden auf "
        "drei.\n  Dann zeigt sie weniger als drei, obwohl mehr sichtbar "
        "waeren.")
    assert "const extra=maSichtbar.length>3?" in t, (
        "\U0001F534 Der +N-Zaehler zaehlt wieder ALLE statt der sichtbaren - "
        "er stuende auf\n  +6, waehrend sechs davon gar nicht erscheinen.")


def test_die_auswahllisten_bleiben_unberuehrt():
    """Die v820/v821-Filter sind richtig und gehoeren NICHT angefasst.

    Ausgetretene bleiben nicht waehlbar - das verhindert das NEUE Eintragen
    und ist eine andere Frage als die Anzeige bereits gespeicherter Tage.
    """
    t = _lies()
    for anker, was in (("fieldMA", "die Auswahlliste der Wochenplanung"),
                       ("fieldM", "die Auswahlliste"),
                       ("_maIstEhemalig", "der Austritts-Helfer")):
        assert anker in t, (
            "\U0001F534 %s (%s) ist verschwunden - dieser Auftrag durfte sie "
            "nicht anfassen." % (anker, was))


def test_kein_optional_chaining_im_neuen_helfer():
    q = _helfer_quelle()
    assert "?." not in q, (
        "\U0001F534 Optional chaining im Helfer. Diese Datei wird ohne "
        "Uebersetzer ausgeliefert."
    )
    assert "new Date" not in q, (
        "\U0001F534 `new Date` im Helfer - das bringt die "
        "UTC-Tagesrand-Kipper zurueck.\n"
        "  Der Vergleich laeuft ueber ISO-Zeichenketten.")


def test_der_helfer_leitet_die_austrittsregel_NICHT_selbst_ab():
    """\U0001F534 Der Bestandsriegel, der meinen ersten Entwurf rot gemacht hat.

    `test_austritt_eine_regel_v952` verlangt: eine Stelle, die ableitet OB
    jemand ausgetreten ist, gehoert NICHT in seine Ausnahmeliste, sondern auf
    `_maIstEhemalig` umgestellt. Mein erster Entwurf hatte den Vergleich selbst
    hingeschrieben - genau die Form, die der Riegel sucht.

    Die Algebra geht auf: *sichtbar am Tag X* ist genau *am Tag X noch nicht
    ehemalig*. Der Vertrag nach aussen ist unveraendert; alle sechs Faelle
    oben pinnen ihn.
    """
    # 🔴 OHNE KOMMENTARE. Der erste Anlauf dieser Probe war rot, weil der
    # Kommentar IM Helfer das Wort `.austritt` nennt ("Kein eigener Vergleich
    # auf .austritt"). Wer rohen Text durchsucht, misst seine eigene
    # Begruendung mit - fuenftes Mal am 28.09.2026, diesmal in die Richtung
    # falscher Alarm.
    q = _ohne_kommentare(_helfer_quelle())
    assert ".austritt" not in q, (
        "\U0001F534 Der Helfer liest `.austritt` wieder selbst. Damit gibt es "
        "die Austrittsregel\n  an zwei Stellen, und die zweite wird bei der "
        "naechsten Aenderung vergessen.")
    assert "!_maIstEhemalig(worker, String(isoTag).slice(0,10))" in q, (
        "\U0001F534 Der Helfer ruft `_maIstEhemalig` nicht mehr so. Wenn das "
        "Absicht ist,\n  gehoert es hier UND in test_austritt_eine_regel_v952 "
        "begruendet.")
    # Und die zwei Sonderzweige muessen AUSSERHALB bleiben - `_maIstEhemalig`
    # beantwortet sie anders (ohne worker: sichtbar; ohne Stichtag: heute).
    assert "if(!worker) return false;" in q and "if(!isoTag) return true;" in q, (
        "\U0001F534 Ein Sonderzweig fehlt. Ohne `worker` gaebe `_maIstEhemalig` "
        "false (= sichtbar),\n  und ohne Stichtag naehme es HEUTE als "
        "Vergleichsdatum - beides ist hier falsch.")
