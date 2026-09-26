# -*- coding: utf-8 -*-
"""v3.9.940 - die Selbstprobe zu vier gelockerten Riegeln.

WARUM ES DIESE DATEI GIBT
─────────────────────────
In v3.9.940 wurden 38 Stellen `window.innerWidth<600` zu
`window.innerWidth<BP_MOB` umbenannt. Vier bestehende Riegel wurden dadurch
rot, weil sie die ZIFFERN 600 im Quelltext verlangten:

    test_hunt_w3_v3986.py::test_fabn_grid_mobile
    test_v3885_settings_responsive.py::test_mein_profil_grid_mobile
    test_v3886_sprint4_perf.py::test_fahrtenbuch_month_padding
    test_projektakte_nav_v937.py::test_die_summenspalte_des_wochenberichts_hat_platz

Sie wurden auf `(?:600|BP_MOB)` gelockert. Das ist genau die Bewegung, die man
NICHT machen darf, wenn man dabei die geschuetzte Eigenschaft verliert - "eine
Pruefung anpassen, damit sie gruen wird" ist der schwerste Fehler in diesem
Lauf. Die Lockerung ist nur dann zulaessig, wenn zwei Dinge belegt sind:

  1. BP_MOB IST 600. Das haelt tests/test_mobil_fundament_v932.py fest
     (`const BP_MOB=600;`, genau einmal). Hier wird es nochmals gepruefft,
     damit diese Datei nicht auf einer Annahme steht.
  2. DIE GELOCKERTEN MUSTER UNTERSCHEIDEN WEITER. Ein Muster, das nach der
     Lockerung auf alles passt, meldet gruen und misst nichts mehr. Also wird
     jedes der vier Muster gegen eine ABSICHTLICH KAPUTTE Fassung des
     Quelltextes gefahren und MUSS dort ins Leere greifen.

Das ist die Regel "ein suchender Riegel braucht einen KOEDER" auf die Riegel
selbst angewandt: ein Muster, das zaehlt, wird beim eigenen Ausfall gruen -
nichts gefunden heisst dann "keine Fehler". Die Mutationsprobe deckt das nicht
ab, weil sie nie fragt, ob der Riegel rot wird, wenn ER SELBST kaputt ist.

WAS DIESE DATEI NICHT TUT
─────────────────────────
Sie misst nicht, ob das Gitter im Browser wirklich stapelt. Das koennen die
vier Riegel auch nicht - sie lesen Quelltext. Diese Datei prueft genau eine
Eigenschaft: dass die Lockerung die Unterscheidungskraft nicht verloren hat.
"""
import io
import re

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def _roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


# Je Eintrag: Name, Muster wie im gelockerten Riegel, und die MUTATION -
# ein Paar (was im Quelltext ersetzt wird, wodurch). Die Mutation zerstoert
# die geschuetzte Eigenschaft, nicht die Schreibweise der Schwelle.
FAELLE = [
    ("fabn_grid_mobile",
     r'gridTemplateColumns:window\.innerWidth<(?:600|BP_MOB)\?"1fr":"1fr 1fr 1fr"',
     ('gridTemplateColumns:window.innerWidth<BP_MOB?"1fr":"1fr 1fr 1fr"',
      'gridTemplateColumns:"1fr 1fr 1fr"')),
    ("mein_profil_grid_mobile",
     r'window\.innerWidth\s*<\s*(?:600|BP_MOB)\s*\?\s*"1fr"\s*:\s*"120px 1fr"',
     ('window.innerWidth<BP_MOB?"1fr":"120px 1fr"',
      '"120px 1fr"')),
    ("fahrtenbuch_month_padding",
     r"padding:window\.innerWidth<(?:600|BP_MOB)\?'10px 10px':'4px 8px'",
     ("padding:window.innerWidth<BP_MOB?'10px 10px':'4px 8px'",
      "padding:'4px 8px'")),
    ("summenspalte_wochenbericht",
     r"width:window\.innerWidth<(?:600|BP_MOB)\?(\d+):",
     ("width:window.innerWidth<BP_MOB?720:",
      "width:")),
]


def test_bp_mob_ist_wirklich_600():
    """Die Lockerung steht und faellt damit. Ohne diese Zeile waere
    `(?:600|BP_MOB)` die Behauptung, zwei Zahlen seien gleich."""
    roh = _roh()
    assert roh.count("const BP_MOB=600;") == 1, (
        "`const BP_MOB=600;` steht %dx im Quelltext. Ist die Zahl eine andere "
        "geworden, sind die vier gelockerten Riegel still falsch: sie "
        "akzeptieren dann eine Schwelle, die nicht mehr 600 ist."
        % roh.count("const BP_MOB=600;"))


def test_jedes_gelockerte_muster_trifft_heute():
    """KOEDER-Haelfte eins: greift ein Muster schon im echten Quelltext ins
    Leere, sagt die Mutationshaelfte darunter nichts aus."""
    roh = _roh()
    leer = [name for name, muster, _ in FAELLE if not re.search(muster, roh)]
    assert not leer, (
        "Diese gelockerten Muster finden im echten Quelltext NICHTS: %s. Dann "
        "ist die Gegenprobe darunter wertlos - ein Muster, das nie trifft, "
        "kann auch nicht unterscheiden." % leer)


def test_jedes_gelockerte_muster_unterscheidet_noch():
    """KOEDER-Haelfte zwei: die eigentliche Frage. Wird das Muster ROT, wenn
    die geschuetzte Eigenschaft entfernt wird? Ein Muster, das auch die
    kaputte Fassung annimmt, ist nach der Lockerung blind."""
    roh = _roh()
    blind = []
    for name, muster, (alt, neu) in FAELLE:
        assert roh.count(alt) >= 1, (
            "Die Mutation fuer %s findet ihren Anker %r nicht - dann ist diese "
            "Selbstprobe selbst kaputt und darf nicht gruen melden."
            % (name, alt))
        kaputt = roh.replace(alt, neu)
        assert kaputt != roh, "Mutation %s aenderte nichts." % name
        if re.search(muster, kaputt):
            blind.append(name)
    assert not blind, (
        "Diese Muster akzeptieren auch die KAPUTTE Fassung: %s. Die Lockerung "
        "auf (?:600|BP_MOB) hat ihnen die Unterscheidungskraft genommen - sie "
        "melden gruen, waehrend die Eigenschaft fehlt." % blind)


def test_keine_nackte_600_mehr_ueber_innerwidth():
    """Der Grund fuer den ganzen Umbau, mit Koeder.

    Gezaehlt wird nur im CODE - ein `600` in einem Kommentar oder einer
    Zeichenkette ist keine Schwelle. Genau daran ist mein Zaehler aus
    v3.9.932/936 schon einmal gescheitert.

    Der KOEDER sind die Schwellen, die es weiter nackt gibt: 768, 700 und 400.
    Findet der Zaehler die nicht, kann er auch die 600 nicht gefunden haben,
    und das Ergebnis 0 heisst dann nicht "keine mehr", sondern "ich sehe
    nichts".
    """
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen

    roh = _roh()
    ok, gefunden, erwartet = eichen(roh)
    assert ok, (
        "Die Eichung von code_scan ist gescheitert (%d von %d). Ohne Eichung "
        "sagt der Zaehler nichts." % (gefunden, erwartet))
    feld = ist_code(roh)

    def zaehl(rx):
        return [m.start() for m in re.finditer(rx, roh) if feld[m.start()]]

    koeder = {
        "768": len(zaehl(r"window\.innerWidth\s*<\s*768\b")),
        "700": len(zaehl(r"window\.innerWidth\s*<\s*700\b")),
        "400": len(zaehl(r"window\.innerWidth\s*<\s*400\b")),
    }
    assert all(v > 0 for v in koeder.values()), (
        "KOEDER STUMM: %r. Der Zaehler findet die nackten Schwellen 768, 700 "
        "und 400 nicht mehr - dann ist seine Null bei der 600 kein Befund, "
        "sondern sein eigener Ausfall. (Sind diese Schwellen absichtlich "
        "entfernt worden, muss der Koeder hier nachgezogen werden.)" % koeder)

    nackt = zaehl(r"window\.innerWidth\s*<\s*600\b")
    assert not nackt, (
        "%d Stellen lesen die Schwelle wieder als nackte 600 (Positionen %s). "
        "Der Name BP_MOB steht genau dafuer da." % (len(nackt), nackt[:6]))

    benannt = zaehl(r"window\.innerWidth\s*<\s*BP_MOB\b")
    assert benannt, (
        "Keine einzige Stelle benutzt window.innerWidth<BP_MOB. Dann hat die "
        "Umbenennung nicht stattgefunden, und die Null oben bedeutet nur, dass "
        "diese Stellen ganz verschwunden sind.")
