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
    ersetze("docs/handoffs/HANDOFF.md", paare, min_bytes=5_000)

FUER JEDE DATEI, NICHT NUR index.html. Am 29.08.2026 wurde dieses Modul fuer
index.html benutzt und fuer einen Handoff nicht - und derselbe Surrogat-Fehler
hat die Handoff-Datei auf 0 Bytes geleert. Der Schutz ist nichts wert, solange
er nur an einer Stelle angewandt wird; das ist im Kleinen dieselbe Krankheit
wie "eine Reparatur an einer von vier Stellen ist keine".

Ablauf: lesen -> alle Anker pruefen (jeder GENAU einmal) -> ersetzen -> Groesse
pruefen -> in eine Nebendatei schreiben -> zurueckgelesen vergleichen -> erst
dann os.replace. Faellt irgendetwas auf, bleibt das Original unberuehrt.
"""
import io
import os

MIN_BYTES = 1_000_000

# Fuer kleinere Dateien (Handoffs, Skripte) beim Aufruf mitgeben, z.B.
# ersetze(pfad, paare, min_bytes=5_000). Das Modul ist NICHT auf index.html
# beschraenkt - genau diese Annahme hat am 29.08. einen Handoff gekostet.


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

    # SURROGAT-RIEGEL. Am 29.08.2026 hat dieselbe Ursache ZWEIMAL eine Datei
    # geleert: ein Emoji, das als Surrogatpaar (\ud83d\udccc) im Python-String
    # landet. `str` haelt das aus, UTF-8 kann es nicht kodieren - und die
    # Ausnahme fliegt ERST beim Schreiben, also nachdem `io.open(p,"w")` die
    # Datei bereits geleert hat. Beim zweiten Mal traf es einen Handoff, weil
    # dieses Modul nur fuer index.html benutzt wurde.
    #
    # Der Nebendatei-Umweg unten faengt das ohnehin ab. Diese Pruefung steht
    # trotzdem davor, weil sie den GRUND nennt statt eines Kodierfehlers -
    # und weil sie greift, bevor auch nur eine Nebendatei entsteht.
    for _i, _z in enumerate(s):
        if 0xD800 <= ord(_z) <= 0xDFFF:
            raise SystemExit(
                "Ein einzelnes Surrogat (U+%04X) an Position %d - das laesst "
                "sich nicht als UTF-8 schreiben. Ursache ist fast immer ein "
                "Emoji, das als \\ud83d\\udxxx im Quelltext steht. Schreib das "
                "Zeichen direkt hin oder lass es weg. NICHTS geschrieben."
                % (ord(_z), _i)
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
