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
            raise SystemExit(_warum(s, alt, name, n))
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


def _warum(s, alt, name, n):
    """Sagt, WARUM ein Anker nicht genau einmal trifft.

    Das ist die haeufigste Fehlerquelle dieses Werkzeugs, und die alte Meldung
    ("trifft 0 mal") nannte nur das Ergebnis. Geprueft werden der Reihe nach
    die vier Ursachen, die im Bestand tatsaechlich vorgekommen sind.
    """
    kopf = "Anker '%s' trifft %d mal statt genau einmal. NICHTS geschrieben." % (name, n)

    if n > 1:
        stellen = []
        i = 0
        while len(stellen) < 3:
            i = s.find(alt, i)
            if i < 0:
                break
            zeile = s.count(chr(10), 0, i) + 1
            stellen.append("Zeile %d" % zeile)
            i += 1
        return (kopf + chr(10) +
                "  Er kommt an mehreren Stellen vor (%s ...). Nimm die Zeile DAVOR"
                % ", ".join(stellen) + chr(10) +
                "  mit in den Anker - meist unterscheidet der Kommentar die Faelle.")

    # --- Ursache 1: Zeilenenden ------------------------------------------
    crlf, lf = chr(13) + chr(10), chr(10)
    if s.replace(crlf, lf).count(alt.replace(crlf, lf)) == 1:
        hat = "CRLF" if crlf in s else "LF"
        will = "CRLF" if crlf in alt else "LF"
        return (kopf + chr(10) +
                "  URSACHE: ZEILENENDEN. Die Datei ist %s, dein Anker %s." % (hat, will) + chr(10) +
                "  Schneide den Anker aus der Datei (safe_edit.schneide), statt ihn" + chr(10) +
                "  zu tippen - dann kann das nicht passieren.")

    # --- Ursache 2: Leerraum ----------------------------------------------
    def eng(t):
        return " ".join(t.split())
    if eng(alt) and eng(s).count(eng(alt)) == 1:
        return (kopf + chr(10) +
                "  URSACHE: LEERRAUM. Ohne Ruecksicht auf Leerzeichen/Umbrueche" + chr(10) +
                "  traefe er genau einmal - die Einrueckung oder ein Umbruch weicht ab.")

    # --- Ursache 3: ein Zeichen daneben ----------------------------------
    # Den laengsten Anfang suchen, der noch in der Datei steht. Was danach
    # kommt, ist die Stelle, an der Anker und Datei auseinandergehen.
    lo, hi = 0, len(alt)
    while lo < hi:
        mitte = (lo + hi + 1) // 2
        if alt[:mitte] in s:
            lo = mitte
        else:
            hi = mitte - 1
    if lo >= 12:
        i = s.find(alt[:lo])
        echt = s[i + lo:i + lo + 24].replace(crlf, "\\r\\n").replace(lf, "\\n")
        meins = alt[lo:lo + 24].replace(crlf, "\\r\\n").replace(lf, "\\n")
        return (kopf + chr(10) +
                "  URSACHE: AB ZEICHEN %d GEHT ES AUSEINANDER." % lo + chr(10) +
                "    in der Datei: ...%r" % echt + chr(10) +
                "    in deinem Anker: ...%r" % meins + chr(10) +
                "  (Zeile %d)" % (s.count(lf, 0, i) + 1))

    return (kopf + chr(10) +
            "  Auch der Anfang des Ankers steht nirgends in der Datei - er gehoert" + chr(10) +
            "  vermutlich zu einer anderen Fassung. Schneide ihn aus der Datei.")


def schneide(pfad, von, bis, einschliesslich=True):
    """Gibt den woertlichen Text zwischen zwei Marken zurueck - als ANKER.

    Nachgebaute Anker sind die haeufigste Fehlerquelle dieses Werkzeugs
    (Zeilenenden, Escape-Folgen, ein Zeichen daneben). Was geschnitten wird,
    kann nicht anders geschrieben sein als das Original.

        from safe_edit import schneide, ersetze
        alt = schneide("index.html", "function _tuWas(", "}")
        ersetze("index.html", [(alt, alt + "/* Notiz */", "Notiz")])
    """
    s = io.open(pfad, encoding="utf-8", newline="").read()
    i = s.find(von)
    if i < 0:
        raise SystemExit("schneide: Anfang %r steht nicht in %s" % (von[:40], pfad))
    if s.count(von) > 1:
        raise SystemExit(
            "schneide: Anfang %r kommt %d mal vor - nimm mehr Umfeld mit."
            % (von[:40], s.count(von)))
    j = s.find(bis, i + len(von))
    if j < 0:
        raise SystemExit("schneide: Ende %r steht nicht nach dem Anfang" % (bis[:40],))
    return s[i:j + len(bis)] if einschliesslich else s[i:j]

