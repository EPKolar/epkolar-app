# -*- coding: utf-8 -*-
"""Gemeinsamer Rumpf fuer Messwerkzeuge - gegen den Fehlalarm aus dem Nichts.

WOZU
────
Am 24./25.09.2026 haben meine EIGENEN Messwerkzeuge sieben Fehlalarme
geliefert. Die schlimmste Form war nicht die falsche Zahl, sondern die
LEERE GRUNDGESAMTHEIT:

    scripts/wisch_flaechen_messen.py meldete "alle Flaechen wechseln" -
    gemessen worden war NICHTS. Null Funde sahen aus wie null Fehler.

Dieselbe Form in drei weiteren Faellen: ein Riegel, der ZAEHLT, wird beim
eigenen Ausfall gruen; `nmea-masse` mass fuenf Tage lang nichts; D3 machte
alle echten Funde zu "wegrollbar", weil die Liste leer blieb.

Der Fehler ist nicht Nachlaessigkeit, sondern die Bauform: wer am Ende
`if not fehler: print("gruen")` schreibt, hat den Ausfall des Messens und das
Ausbleiben von Fehlern in DENSELBEN Zweig gelegt. Die beiden muessen
auseinander.

WIE
───
    from messen import urteil, koeder

    koeder("Der Reiter wechselt ueberhaupt", lambda: tab_wechselt(0, 1))
    funde = [pruefe(f) for f in flaechen]
    urteil("Wisch-Flaechen", funde, schlecht=lambda f: not f["wechselt"])

`urteil` verweigert ein gruenes Ergebnis, solange die Grundgesamtheit leer
ist. `koeder` verweigert den ganzen Lauf, wenn ein Fall, der ROT sein MUSS,
nicht rot wird - dann sieht das Werkzeug ueberhaupt nichts.
"""
import sys


class MessungOhneGrundgesamtheit(SystemExit):
    """Nichts gemessen ist kein Ergebnis."""


def koeder(was, probe):
    """Fuehrt eine Probe, die ANSCHLAGEN MUSS, bevor gemessen wird.

    Ein Werkzeug, das nichts sehen kann, findet auch nichts - und das sieht
    aus wie "keine Fehler". Der Koeder trennt die beiden Faelle, BEVOR die
    eigentliche Messung laeuft.

    `probe` gibt etwas Wahrheitswertiges zurueck. Faellt sie negativ aus oder
    wirft sie, bricht der Lauf ab - ohne Ergebnis, nicht mit einem gruenen.
    """
    try:
        ergebnis = probe()
    except Exception as e:                                    # noqa: BLE001
        raise SystemExit(
            "KOEDER GESCHEITERT (%s): die Probe warf %r.\n"
            "  Das Werkzeug kann nicht messen. Ein Ergebnis waere erfunden."
            % (was, e))
    if not ergebnis:
        raise SystemExit(
            "KOEDER GESCHEITERT (%s): ein Fall, der ANSCHLAGEN MUSS, blieb "
            "stumm.\n"
            "  Das Werkzeug sieht nichts. Was es jetzt meldete - auch ein "
            "gruenes Ergebnis - waere erfunden." % was)
    return ergebnis


def urteil(was, funde, schlecht=None, mindestens=1, still=False):
    """Faellt das Urteil - und verweigert es bei leerer Grundgesamtheit.

    was         Name der Messung, erscheint in jeder Meldung
    funde       die gemessenen Faelle (Liste). LEER heisst NICHT "in Ordnung".
    schlecht    Pruefung je Fall; ohne sie gilt ein falsy Fall als schlecht
    mindestens  so viele Faelle muessen gemessen worden sein
    still       True gibt nichts aus, sondern nur zurueck

    Rueckgabe: die Liste der schlechten Faelle (leer heisst gruen).
    """
    funde = list(funde)
    if len(funde) < mindestens:
        raise MessungOhneGrundgesamtheit(
            "%s: nur %d Fall/Faelle gemessen, erwartet mindestens %d.\n"
            "  Das ist KEIN gruenes Ergebnis, sondern eine ausgefallene "
            "Messung.\n"
            "  Ein leerer Fundhaufen sieht genauso aus wie 'nichts gefunden' - "
            "und\n"
            "  genau daran sind am 24.09.2026 vier Messungen gescheitert."
            % (was, len(funde), mindestens))

    pruef = schlecht if schlecht is not None else (lambda f: not f)
    schlimm = [f for f in funde if pruef(f)]
    if not still:
        if schlimm:
            print("%s: ROT - %d von %d Faellen" % (was, len(schlimm), len(funde)))
            for f in schlimm[:20]:
                print("   %r" % (f,))
        else:
            print("%s: gruen - %d Faelle gemessen" % (was, len(funde)))
        sys.stdout.flush()
    return schlimm
