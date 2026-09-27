# -*- coding: utf-8 -*-
"""v3.9.961 - jede Testdatei muss auch WIRKLICH eingesammelt werden.

DER FUND, DEN DIESE DATEI KUENFTIG SELBST FINDET
────────────────────────────────────────────────
`tests/test_nichtgemessen_v909.py` lag am 29.08.2026 im Verzeichnis, hiess
`test_*`, war fehlerfrei und meldete von Hand GRUEN 18/18 - und enthielt keine
einzige `def test_`-Funktion. pytest sammelte daraus NULL Faelle. **29 Tage und
75 Commits** lang eine gruene Pruefung, die nichts gemessen hat.

Von innen sieht so eine Datei richtig aus. Gefunden wurde sie erst, als jemand
die Dateien auf der Platte mit dem verglich, was `pytest --collect-only`
tatsaechlich einsammelt - also von aussen.

Diese Datei macht daraus eine Pruefung, die IM Lauf steht: sie fragt pytest
selbst, aus welchen Dateien Faelle gekommen sind, und vergleicht das mit dem
Verzeichnis. Keine Unterprozesse, kein zweiter pytest-Lauf.

🔴 WARUM SIE SICH BEI EINEM TEILLAUF ZURUECKHAELT
Wer `pytest -k etwas` oder eine einzelne Datei fahrt, sammelt absichtlich nur
einen Teil ein. Eine Pruefung, die dann rot wird, ist eine Pruefung, die man
abschaltet - und abgeschaltet ist sie wieder nichts wert. Sie urteilt deshalb
nur, wenn der Lauf gross genug ist, um ein Volllauf zu sein, und sagt sonst
ausdruecklich, dass sie nicht geurteilt hat. Das ist der Unterschied zwischen
"nicht gemessen" und "kein Befund".

WAS SIE NICHT MISST
Ob die eingesammelten Faelle etwas WERT sind - ein Fall ohne Zusicherung oder
mit leerer Grundgesamtheit wird hier mitgezaehlt. Das ist eine andere Frage, und
sie steht in `docs/befunde/WAS_LAEUFT_WIRKLICH.md` (sechs solche Faelle belegt).
Hier geht es nur darum, dass eine Datei ueberhaupt zu Wort kommt.
"""
import os

import pytest

HIER = os.path.dirname(os.path.abspath(__file__))

# Dateien, die absichtlich keine Faelle beitragen - namentlich, mit Grund.
# KEINE Zahl: eine Obergrenze unterscheidet nicht, ob ein bekannter Fall
# wegfaellt und ein neuer dazukommt.
OHNE_FAELLE = {
    "test_dispo_resched_push_v737.py":
        "Zwei-Zeilen-Platzhalter aus v3.9.737, bewusst leer.",
}

# Unter dieser Zahl gilt der Lauf als TEILLAUF und es wird nicht geurteilt.
# Gemessen am 27.09.2026: ein Volllauf sammelt aus ueber 460 Dateien.
VOLLLAUF_AB = 300


def test_jede_testdatei_hat_faelle_beigetragen(request):
    """Vergleicht das Verzeichnis mit dem, was pytest eingesammelt hat."""
    auf_platte = {f for f in os.listdir(HIER)
                  if f.startswith("test_") and f.endswith(".py")}
    assert len(auf_platte) > 100, (
        "Nur %d Testdateien im Verzeichnis gefunden. Das ist kein gruenes "
        "Ergebnis - es sind ueber 460. Entweder ist der Pfad falsch, oder es "
        "ist etwas verlorengegangen." % len(auf_platte))

    mit_faellen = set()
    for item in request.session.items:
        pfad = getattr(item, "fspath", None)
        if pfad is None:
            continue
        name = os.path.basename(str(pfad))
        if os.path.dirname(os.path.abspath(str(pfad))) == HIER:
            mit_faellen.add(name)

    if len(mit_faellen) < VOLLLAUF_AB:
        pytest.skip(
            "TEILLAUF: nur %d von %d Dateien haben Faelle beigetragen "
            "(Schwelle %d). Dieser Lauf hat absichtlich nur einen Teil "
            "eingesammelt, also wird hier NICHT geurteilt - eine Pruefung, die "
            "bei -k rot wird, wird abgeschaltet. Fuer das Urteil den vollen "
            "Lauf fahren: pytest tests/ -q"
            % (len(mit_faellen), len(auf_platte), VOLLLAUF_AB))

    stumm = sorted(auf_platte - mit_faellen - set(OHNE_FAELLE))
    assert not stumm, (
        "%d Testdatei(en) liegen in tests/, tragen aber KEINEN Fall bei:\n%s\n\n"
        "Eine solche Datei ist eine gruene Pruefung, die nichts messen kann - "
        "genau das war test_nichtgemessen_v909.py, 29 Tage und 75 Commits "
        "lang. Von innen sieht sie richtig aus.\n"
        "Moegliche Gruende: keine `def test_`-Funktion (als eigenstaendiges "
        "Programm geschrieben), ein Importfehler, ein Sammelfehler, oder alle "
        "Faelle sind uebersprungen. Ist die Datei absichtlich leer, gehoert sie "
        "mit Grund in OHNE_FAELLE."
        % (len(stumm), "\n".join("  " + s for s in stumm)))


def test_die_namentlichen_ausnahmen_gibt_es_noch():
    """Eine Ausnahme, deren Anlass verschwunden ist, erlaubt beim naechsten
    Mal einen echten Fehler."""
    for name, grund in OHNE_FAELLE.items():
        assert os.path.exists(os.path.join(HIER, name)), (
            "Die Ausnahme %r steht in OHNE_FAELLE, die Datei gibt es aber "
            "nicht mehr. Dann gehoert der Eintrag WEG - samt seiner "
            "Begruendung (%s)." % (name, grund))


def test_der_vergleich_wuerde_eine_stumme_datei_finden(request):
    """KOEDER auf die Mengenrechnung.

    Die Pruefung oben zieht zwei Mengen voneinander ab und ist gruen, wenn die
    Differenz leer ist - eine leere Differenz entsteht aber auch, wenn eine der
    Mengen falsch gefuellt ist. Hier wird ein Name eingesetzt, der auf der
    Platte liegt und keine Faelle beigetragen hat; er MUSS in der Differenz
    auftauchen.
    """
    auf_platte = {f for f in os.listdir(HIER)
                  if f.startswith("test_") and f.endswith(".py")}
    assert auf_platte, "Keine Testdateien gefunden - der Koeder ist wertlos."
    mit_faellen = {os.path.basename(str(i.fspath))
                   for i in request.session.items
                   if getattr(i, "fspath", None) is not None}
    # Eine Datei, die es gibt und die Faelle beigetragen hat, aus der
    # Trefferliste entfernen: sie MUSS dann als stumm gelten.
    eigene = os.path.basename(__file__)
    assert eigene in mit_faellen or len(mit_faellen) < VOLLLAUF_AB, (
        "Diese Datei selbst erscheint nicht in der Trefferliste, obwohl sie "
        "gerade laeuft. Dann ist der Abgleich ueber fspath kaputt - und die "
        "Pruefung oben wuerde jede Datei als stumm melden oder keine.")
    kaputt = mit_faellen - {eigene}
    assert eigene in (auf_platte - kaputt), (
        "KOEDER NICHT GEFUNDEN: eine Datei, die aus der Trefferliste entfernt "
        "wurde, erscheint nicht in der Differenz. Dann misst die Rechnung "
        "nicht, was sie behauptet.")
