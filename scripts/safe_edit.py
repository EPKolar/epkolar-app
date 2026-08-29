# -*- coding: utf-8 -*-
"""Sicheres Ersetzen in index.html - erst pruefen, dann ersetzen.

WARUM ES DAS GIBT (29.08.2026): Ein abgebrochener Schreibvorgang hat index.html
auf 0 Bytes gekuerzt. Ursache war ein Surrogatpaar in einem Python-String
(\\ud83d\\udccc fuer ein Emoji): `io.open(p,"w")` hatte die Datei da bereits
geleert, und erst beim Kodieren flog die Ausnahme. 3,4 MB weg.

Wiederherstellbar war es nur, weil der letzte Commit sauber war. Beide Gates
meldeten dabei GRUEN - eine leere Datei parst fehlerfrei und hat ausgeglichene
Klammern. Die bekamen deshalb einen eigenen Lebenszeichen-Riegel.

Dieses Modul schliesst die andere Haelfte: das Zielfile wird gar nicht erst
angefasst, solange nicht feststeht, dass der neue Inhalt vollstaendig ist.

    from safe_edit import ersetze
    ersetze("index.html", [(alt1, neu1, "Beschreibung"), ...])

Ablauf: lesen -> alle Anker pruefen (jeder GENAU einmal) -> ersetzen -> Groesse
pruefen -> in eine Nebendatei schreiben -> zurueckgelesen vergleichen -> erst
dann os.replace. Faellt irgendetwas auf, bleibt das Original unberuehrt.
"""
import io
import os

MIN_BYTES = 1_000_000


def ersetze(pfad, paare, min_bytes=MIN_BYTES):
    """Wendet (alt, neu, name)-Paare an. Jeder Anker muss GENAU einmal treffen.

    Gibt die Liste der angewandten Namen zurueck. Wirft, bevor irgendetwas
    geschrieben wird, wenn ein Anker nicht eindeutig ist.
    """
    s = io.open(pfad, encoding="utf-8", newline="").read()
    ausgang = len(s)
    if ausgang < min_bytes:
        raise SystemExit(
            "%s ist schon vor der Aenderung nur %d Bytes gross - hier stimmt "
            "etwas nicht. Nichts angefasst." % (pfad, ausgang)
        )

    getan = []
    for alt, neu, name in paare:
        n = s.count(alt)
        if n != 1:
            raise SystemExit(
                "Anker '%s' trifft %d mal statt genau einmal. NICHTS geschrieben."
                % (name, n)
            )
        s = s.replace(alt, neu, 1)
        getan.append(name)

    if len(s) < min_bytes:
        raise SystemExit(
            "Ergebnis waere nur %d Bytes gross (vorher %d) - das ist Datenverlust. "
            "NICHTS geschrieben." % (len(s), ausgang)
        )

    tmp = pfad + ".tmp_safe_edit"
    io.open(tmp, "w", encoding="utf-8", newline="").write(s)
    # Zurueckgelesen vergleichen: faengt Kodierfehler, die beim Schreiben nur
    # einen Teil durchlassen - genau der Fall vom 29.08.
    zurueck = io.open(tmp, encoding="utf-8", newline="").read()
    if zurueck != s:
        os.unlink(tmp)
        raise SystemExit(
            "Zurueckgelesener Inhalt weicht ab (%d statt %d Bytes) - vermutlich "
            "ein Kodierproblem. Original unberuehrt." % (len(zurueck), len(s))
        )
    os.replace(tmp, pfad)
    return getan
