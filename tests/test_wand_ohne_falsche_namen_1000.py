# -*- coding: utf-8 -*-
"""B3 — bei Ausfall zeigte die Wand eine Belegschaft von 2018.

**Am Schirm gemessen, in sechs von sechs Aufnahmen:** scheitert der Abruf der
Mitarbeiter, standen auf der Kiosk-Tafel „Barger · Cracana · Paschinger ·
Schmid" — die fest eingebaute Saatliste aus dem Jahr 2018.

Der Grund: `monteure` startet mit dieser Liste, und ersetzt wird sie nur,
**wenn** etwas ankommt (`if(wk?.length)`). Kommt nichts, bleibt die Saat
stehen — und sieht aus wie die heutige Belegschaft. Auf einer Wand, an der
niemand nachfragt, ist das die schlimmste Form: es sieht richtig aus.

Es gab seit v3.9.822 schon einen Auffangzweig, aber er sagt „Cache bleibt
aktiv" und meldet per Toast. **Beides trifft auf einer Wand nicht zu:** dort
ist der „Cache" die Demoliste, und einen Toast liest niemand — nach sieben
Sekunden ist die Tafel wieder ohne Hinweis.

## Die Kur ist bewusst eng

* **Nur im Kiosk-Anzeigebetrieb**, und nur solange wir noch die **Saat**
  halten. Sind einmal echte Daten geladen worden, bleiben sie stehen: ein
  veralteter echter Stand ist etwas anderes als eine Demoliste, und die
  Offline-Fähigkeit bleibt unberührt.
* **Statt falscher Namen: gar keine Namen**, und ein stehendes Schild. Eine
  leere Tafel mit Begründung ist wahr; vier Namen von 2018 sind es nicht.
* **Kein Toast auf der Wand.** Dort steht niemand, der ihn wegklickt.

Die Machart des Schildes ist vom Alters-Schild aus v3.9.939 **abgeschrieben**:
groß, mit Text und nicht nur Farbe — man liest die Tafel aus einigen Metern,
und Rot-Grün ist die häufigste Farbsehschwäche.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ohne_kommentare(s):
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def test_koeder_die_kommentarbehandlung_traegt():
    mit = "/* HIER STAND window.__toast(...) ohne _isLD */ x=1;"
    assert "window.__toast(" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_die_saatliste_wird_auf_der_wand_geleert():
    code = _ohne_kommentare(_text())
    assert "setMonteure(function(_prev){return (_prev===MONT)?[]:_prev;});" \
        in code, (
        "\U0001F534 Die Saatliste wird nicht mehr geleert. Dann stehen bei "
        "einem Ausfall\n  wieder vier Namen von 2018 auf der Wand - und sie "
        "sehen aus wie die heutige\n  Belegschaft.")
    assert "window.__kioskMaErr=window.__epkWorkerLoadErr" in code, (
        "\U0001F534 Der Fehlermerker wird nicht gesetzt - dann bleibt die "
        "Tafel leer, ohne zu\n  sagen warum, und leer sieht aus wie "
        "'niemand da'.")


def test_nur_die_saat_wird_geleert_nicht_echte_daten():
    """🔴 Gegenprobe zur Kur: sie darf NICHT zu viel wegräumen.

    Ein veralteter echter Stand ist etwas anderes als eine Demoliste. Wer
    hier unbedingt leert, nimmt der Wand die Offline-Fähigkeit — dann steht
    sie bei jedem Netzausfall leer da, obwohl sie gültige Daten hätte.
    """
    code = _ohne_kommentare(_text())
    assert "(_prev===MONT)?[]:_prev" in code, (
        "\U0001F534 Es wird nicht mehr unterschieden, ob wir die SAAT oder "
        "echte Daten halten.\n  Unbedingtes Leeren nimmt der Wand die "
        "Offline-Faehigkeit.")
    assert "setMonteure(function(_prev){return [];})" not in code, (
        "\U0001F534 Es wird unbedingt geleert.")


def test_auf_der_wand_kommt_kein_toast():
    """🔴 Ein Toast auf einer unbedienten Wand ist keine Meldung.

    Er verschwindet nach sieben Sekunden, und danach steht die Tafel wieder
    ohne Hinweis da. Das Schild bleibt, solange der Fehler besteht.
    """
    code = _ohne_kommentare(_text())
    assert "if(window.__toast&&!_isLD)window.__toast" in code, (
        "\U0001F534 Der Toast zur Mitarbeiterliste feuert wieder auch im "
        "Kiosk-Betrieb.")


def test_das_schild_steht_auf_der_tafel():
    t = _text()
    assert t.count("__kioskMaErr") >= 3, (
        "\U0001F534 Der Merker wird nicht mehr gesetzt UND angezeigt "
        "(%d Vorkommen)." % t.count("__kioskMaErr"))
    i = t.find("Mitarbeiterliste nicht geladen")
    assert i > 0, (
        "\U0001F534 Das Schild ist weg. Dann ist die Tafel bei einem Ausfall "
        "leer und sagt\n  nicht warum - und leer sieht aus wie 'niemand "
        "da'.")
    umfeld = t[max(0, i - 400):i + 80]
    assert "fontSize:20" in umfeld, (
        "\U0001F534 Das Schild ist nicht mehr gross genug fuer eine Wand.")
    assert "fontWeight:800" in umfeld, (
        "\U0001F534 Das Schild ist nicht mehr fett.")


def test_das_schild_traegt_text_und_nicht_nur_farbe():
    """🔴 Nie Farbe allein — Rot-Grün ist die häufigste Farbsehschwäche,
    und die Tafel wird aus einigen Metern gelesen."""
    t = _text()
    i = t.find("Mitarbeiterliste nicht geladen")
    assert i > 0, "Das Schild ist weg."
    assert "color:'#B4530A'" in t[max(0, i - 400):i], (
        "\U0001F534 Die Warnfarbe des Hauses fehlt.")
    # Der Text selbst ist die Hauptaussage - er steht im Knoten, nicht im
    # Titel-Attribut allein.
    #
    # 🔴 ZWEI SCHREIBWEISEN, und mein erster Versuch kannte nur eine: das
    # Warnzeichen steht im Quelltext als ESCAPE (Backslash-u-26a0), nicht als
    # Zeichen. Zur Laufzeit ist beides dasselbe; eine Suche nach dem Zeichen
    # findet die Escape-Form nicht und meldet einen Befund, den es nicht gibt.
    # Geprueft werden darum beide Formen.
    zeichen = "'⚠️ Mitarbeiterliste nicht geladen'"
    escape = "'" + chr(92) + "u26a0" + chr(92) + "ufe0f Mitarbeiterliste " \
        "nicht geladen'"
    assert (zeichen in t) or (escape in t), (
        "\U0001F534 Der Text steht nicht mehr sichtbar im Schild - weder als "
        "Zeichen noch als\n  Escape. Ein Titel-Attribut allein sieht auf "
        "einer Wand niemand: dort wird\n  nichts angetippt.")
