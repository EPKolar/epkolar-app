# -*- coding: utf-8 -*-
"""v3.9.959 - kein Kommentar darf der Fahne FINKZEIT_ENABLED widersprechen.

WAS VIERZEHN MONATE LANG FALSCH DASTAND
───────────────────────────────────────
`FINKZEIT_ENABLED` schaltet den Reiter „Monatsabrechnung". Am 04.06.2026 hat
Sebastian ihn geparkt (Fahne auf `false`), und in **v3.9.204** ist er
reaktiviert worden - die Fahne steht seither auf `true`.

Die Kommentare sind nie nachgezogen worden. Bis v3.9.958 behaupteten
**sechzehn** Stellen auf dreizehn Zeilen weiter „FINKZEIT STANDBY", „Tab
geparkt", „UI-ausgeblendet" und - am schaedlichsten, direkt ueber
`StundenzettelView` - „komplette View geparkt: diese Komponente wird nicht mehr
gerendert."

Gemessen war zur gleichen Zeit: `const FINKZEIT_ENABLED=true;`, `"stunden"`
steht in `_navIds` und in der Reiterliste, und der Aufruf der Komponente haengt
nur noch an `hasPerm(curUser,"stunden")`. **Der Weg ist offen, der Kommentar
war falsch.**

Aufgefallen ist das schon einmal: ein Kommentar aus v3.9.864 haelt selbst fest
„und FINKZEIT_ENABLED=true, der Tab war fuer alle live". Nachgezogen wurde
damals nichts. Und in der Sitzung vom 26./27.09.2026 ist genau das passiert,
wovor es schuetzen soll: ein Befund wurde wegen dieses Satzes fast falsch
einsortiert - lebender Code galt als stillgelegt.

WAS DIESER RIEGEL MISST - ein VERHAELTNIS, keine Anwesenheit
────────────────────────────────────────────────────────────
Er liest den WERT der Fahne aus der Deklaration und prueft erst dann die
Kommentare:

  * Fahne `true`  -> keine Stelle darf behaupten, der Reiter sei geparkt.
  * Fahne `false` -> dieselben Saetze sind richtig und duerfen dastehen.

Eine Liste verbotener Woerter waere also falsch: sie haengt daran, wie die
Fahne steht. Wer die Fahne wieder auf `false` setzt, wird von diesem Riegel
NICHT behindert.

🔴 UND EIN ZITAT IST KEINE BEHAUPTUNG
─────────────────────────────────────
Die Richtigstellungen nennen die alte Formulierung, damit nachvollziehbar
bleibt, was falsch war: *Bis v3.9.958 stand hier „Tab geparkt" - das war seit
der Reaktivierung falsch.* Ein Riegel, der nur nach dem Wortlaut sucht, waere
dadurch fuer immer rot - und man wuerde ihn dann entweder loeschen oder die
Erklaerung streichen. Beides waere schlechter als der Zustand vorher.

Deshalb ist die Bedingung scharf: die Phrase darf vorkommen, aber nur **in
Anfuehrungszeichen**, also als Zitat. Unzitiert ist sie eine Behauptung, und
die ist bei `true` falsch.

WAS DIESE DATEI NICHT MISST
───────────────────────────
Ob der Reiter im Browser wirklich erscheint - das haengt zusaetzlich an
`hasPerm(curUser,"stunden")` und damit an der Rolle. Gemessen wird der
Quelltext: die Fahne und die Saetze darueber.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Saetze, die NUR bei Fahne=false stimmen. Praesens, ueber den heutigen
# Zustand. Ausdruecklich NICHT dabei: "geparkt, nicht geloescht" - das ist
# eine Angabe zur Geschichte mit Datum und bleibt richtig.
NUR_BEI_FALSE = [
    "FINKZEIT STANDBY",
    "Tab geparkt",
    "komplette View geparkt",
    "wird nicht mehr gerendert",
    "wird aber nicht gerendert/aufgerufen",
    "UI-ausgeblendet",
    "nur der UI-Toggle ist ausgeblendet",
]


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust. Eine leere Datei "
            "enthaelt uebrigens keinen falschen Kommentar." % len(roh))
    return roh


def _fahne(text):
    """Der WERT der Fahne, aus der Deklaration gelesen."""
    m = re.search(r"const\s+FINKZEIT_ENABLED\s*=\s*(true|false)\s*;", text)
    assert m, (
        "Die Deklaration `const FINKZEIT_ENABLED=<true|false>;` ist nicht zu "
        "finden. Ohne den WERT der Fahne kann dieser Riegel nichts sagen - er "
        "verweigert die Auskunft, statt eine zu erfinden.")
    return m.group(1) == "true", m.start()


def _ist_zitiert(text, start, ende):
    """Liegt die Phrase INNERHALB eines Anfuehrungszeichen-Paares?

    🔴 DIE ERSTE FASSUNG HATTE HIER EIN LOCH, und ein fremder Riegel hat es
    gefunden. Sie fragte nur, ob im umgebenden Kommentar irgendwo VOR und
    irgendwo NACH der Phrase ein Anfuehrungszeichen steht. Der
    Changelog-Kommentar hinter APP_VERSION ist 256.000 Zeichen lang und
    enthaelt Tausende davon - dort galt also JEDE Phrase als zitiert. Genau
    darin stand dann eine unzitierte Behauptung, und dieser Riegel schwieg.

    Jetzt werden die Zitatbereiche des Kommentars AUSGERECHNET (paarweise) und
    gefragt, ob die Phrase in einem davon liegt. Ein Loch, das "irgendwo im
    Umfeld" prueft statt "innerhalb", ist dieselbe Fehlerform wie ein Anker,
    der zu weit schneidet.
    """
    links = text.rfind("/*", max(0, start - 300_000), start)
    if links < 0:
        return False
    rechts = text.find("*/", ende)
    if rechts < 0:
        return False
    komm = text[links:rechts]
    a = start - links
    b = ende - links
    # Paarweise Zitatbereiche: 1. mit 2., 3. mit 4. Anfuehrungszeichen usw.
    pos = [m.start() for m in re.finditer('"', komm)]
    for i in range(0, len(pos) - 1, 2):
        if pos[i] < a and b <= pos[i + 1]:
            return True
    return False


def _behauptungen(text):
    """(Zeile, Phrase) je Stelle, die etwas BEHAUPTET statt zu zitieren."""
    aus = []
    for ph in NUR_BEI_FALSE:
        for m in re.finditer(re.escape(ph), text):
            if _ist_zitiert(text, m.start(), m.end()):
                continue
            aus.append((text.count("\n", 0, m.start()) + 1, ph))
    return sorted(aus)


def test_kein_kommentar_widerspricht_der_fahne():
    """Die Aussage: Fahne und Kommentare sagen dasselbe."""
    roh = _lies()
    an, pos = _fahne(roh)
    zeile = roh.count("\n", 0, pos) + 1
    fund = _behauptungen(roh)
    if not an:
        # Fahne false: die Saetze sind richtig, hier ist nichts zu tun.
        return
    assert not fund, (
        "FINKZEIT_ENABLED steht auf true (Z%d), aber %d Stelle(n) behaupten "
        "unzitiert das Gegenteil:\n%s\n\n"
        "Seit v3.9.204 ist der Reiter \"Monatsabrechnung\" LIVE. Ein Kommentar, "
        "der ihn als geparkt beschreibt, laesst lebenden Code als stillgelegt "
        "erscheinen - genau daran ist in der Sitzung vom 26./27.09.2026 ein "
        "Befund fast falsch einsortiert worden.\n"
        "Soll der Satz als GESCHICHTE stehenbleiben: in Anfuehrungszeichen "
        "setzen und dazuschreiben, seit wann er nicht mehr gilt. Soll der "
        "Reiter wirklich wieder weg: die Fahne auf false setzen - dann "
        "schweigt dieser Riegel."
        % (zeile, len(fund),
           "\n".join("  Z%-7d %s" % f for f in fund)))


def test_die_fahne_selbst_ist_noch_da():
    """Ohne die Fahne misst der Riegel oben nichts.

    Verschwindet die Deklaration, wuerde `_fahne` werfen - das steht hier
    eigenstaendig, damit im roten Fall die Ursache in der Meldung steht und
    nicht nur ein Fehler aus einer Hilfsfunktion.
    """
    roh = _lies()
    an, pos = _fahne(roh)
    assert isinstance(an, bool)
    # Und sie ist genau EINMAL deklariert - zwei Deklarationen hiessen, dass
    # der Riegel die falsche liest.
    n = len(re.findall(r"const\s+FINKZEIT_ENABLED\s*=", roh))
    assert n == 1, (
        "FINKZEIT_ENABLED ist %dx deklariert. Dann liest dieser Riegel "
        "moeglicherweise die andere - und seine Aussage gilt fuer die falsche "
        "Fahne." % n)


def test_der_riegel_wird_bei_einer_neuen_behauptung_rot():
    """KOEDER 1: eine unzitierte Behauptung MUSS gefunden werden."""
    roh = _lies()
    an, _ = _fahne(roh)
    assert an, (
        "Dieser Koeder setzt voraus, dass die Fahne true ist. Steht sie auf "
        "false, ist er nicht anwendbar - dann bitte hier begruenden, statt ihn "
        "zu entfernen.")
    anker = "const FINKZEIT_ENABLED=true;"
    assert anker in roh
    kaputt = roh.replace(
        anker, anker + "/* Tab geparkt, wird nicht mehr gerendert */", 1)
    fund = _behauptungen(kaputt)
    assert fund, (
        "KOEDER NICHT GEFUNDEN: ein eingesetzter Kommentar \"Tab geparkt, wird "
        "nicht mehr gerendert\" wird nicht erkannt. Der Riegel ist blind, "
        "nicht die Datei ist in Ordnung.")


def test_ein_zitat_macht_den_riegel_NICHT_rot():
    """KOEDER 2, in der Gegenrichtung - und der wichtigere.

    Ein Riegel, der auch Zitate rot macht, zwingt dazu, entweder ihn oder die
    Erklaerung zu loeschen. Beides waere schlechter als vorher. Hier wird
    belegt, dass er unterscheidet.
    """
    roh = _lies()
    anker = "const FINKZEIT_ENABLED=true;"
    zitat = (anker + "/* Bis v3.9.958 stand hier \"Tab geparkt\" - das war "
             "seit der Reaktivierung falsch. */")
    kaputt = roh.replace(anker, zitat, 1)
    vorher = _behauptungen(roh)
    nachher = _behauptungen(kaputt)
    assert nachher == vorher, (
        "Ein ZITAT der alten Formulierung macht den Riegel rot. Dann kann die "
        "Richtigstellung nicht erklaeren, was falsch war, ohne selbst "
        "anzustossen - und am Ende wird die Erklaerung geloescht statt der "
        "Fehler.\nNeu gemeldet: %s"
        % [f for f in nachher if f not in vorher])


def test_die_richtigstellungen_stehen_noch_da():
    """Die neuen Saetze sollen nicht wieder verschwinden.

    Gemessen wird nicht, dass ein bestimmter Wortlaut vorkommt - das waere
    Anwesenheit. Gemessen wird, dass die drei Stellen, an denen der falsche
    Satz stand, ueberhaupt noch etwas zur Fahne sagen. Ein Kommentar, der
    stillschweigend ganz entfernt wird, laesst die naechste Leserin ohne
    Hinweis darauf, dass die Fahne diesen Zweig steuert.
    """
    roh = _lies()
    an, _ = _fahne(roh)
    if not an:
        return
    n = len(re.findall(r"FINKZEIT-SCHALTER", roh))
    assert n >= 5, (
        "Nur %d Stellen sind als FINKZEIT-SCHALTER gekennzeichnet, erwartet "
        "mindestens 5. In v3.9.959 waren es 9. Sinkt die Zahl, sind Hinweise "
        "auf die Fahne verschwunden - und dann steht an einer Stelle Code, der "
        "an einer Fahne haengt, ohne dass es dort jemand sieht." % n)
