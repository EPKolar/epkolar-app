# -*- coding: utf-8 -*-
"""Keine Stilregel fuer ein Bauteil, das es nicht gibt.

🔴 FRAGE 24. Am 27.09.2026 wurden `.ber-table`, `.badge` und das Sync-Banner
von 11 px auf 12 px gehoben - richtig gedacht, und wirkungslos. Die
Selektoren treffen nichts.

AM SCHIRM GEMESSEN (`python scripts/tote_regeln_messen.py 1440`), 10
Ansichten, mit EINGESETZTEM Koeder und einer Gegenprobe:

    Koeder eingesetzt -> alle vier Selektoren finden ihn (je 1)
    `.header-row`     -> trifft 9 mal   (die Gegenprobe: der Zaehler misst)
    `.ber-table`      -> 0
    `.badge`          -> 0
    `[style*="Aenderungen warten"]` -> 0
    `[title*="Jetzt sync"]`         -> 0

UND STRUKTURELL, also in JEDEM Zustand - das ist der eigentliche Beleg, denn
eine Messung im Ruhezustand sagt nichts ueber ein Banner, das nur bei
ausstehenden Aenderungen erscheint:

  * `.ber-table` wird in der ganzen Datei kein einziges Mal vergeben -
    weder `class=` noch `className` noch `classList.add`.
  * `.badge` nur in den erzeugten EXPORT- und DRUCK-Dokumenten, und die
    bringen ihre eigenen Stilbloecke mit. Die Regel im Hauptdokument hat sie
    nie erreicht.
  * „Aenderungen warten" kam im ganzen Dokument ZWEIMAL vor - beide Male in
    der Regel selbst. Der Text steht im TEXTINHALT, der Selektor sucht im
    STYLE-ATTRIBUT.
  * „Jetzt sync" gibt es nur als Knopf-TEXT, nie als `title`.

Damit war „reparieren" keine Option: es gaebe nichts zu reparieren, nur zu
erfinden.

🔴 WAS DIESER RIEGEL MISST. Nicht „die Regeln sind weg" - das waere ein
Riegel, der von einem Zustand lebt. Er misst die KLASSE: kein Selektor im
Hauptstilblock darf eine Klasse nennen, die nirgends vergeben wird. Heute
sind das vier gebuchte Namen; wer einen fuenften dazulegt, wird rot.

Die Historie kann uebrigens NICHT sagen, ob `.ber-table` frueher existierte:
`index.html` kam mit Commit 1eb4bfc bereits fertig ins Repo, die Regeln waren
von Anfang an da. Das steht hier, statt als offene Frage weitergereicht zu
werden.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
PFAD = os.path.join(HIER, "..", "index.html")

# Die vier, die am 29.09. entfernt wurden. Sie duerfen nicht zurueckkommen,
# solange nichts sie vergibt.
ENTFERNT = {
    ".ber-table": r"(class=|className\s*:|classList\.add\()\s*[\"'][^\"']*"
                  r"ber-table",
    "[style*=\"Änderungen warten\"]": r"style\s*[:=][^\n]{0,200}"
                                           r"Änderungen warten",
    "[title*=\"Jetzt sync\"]": r"title\s*[:=]\s*[\"'][^\"']*Jetzt sync",
}


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _hauptblock(text):
    """Der ERSTE <style>-Block, OHNE seine Kommentare.

    🔴 ZWEI EIGENE FEHLER IN DIESER FUNKTION, beide vom ersten Lauf gezeigt:

    1. `find` liefert **0**, wenn der Block am Textanfang steht - und ich
       prueft `a > 0`. Der eigene Koeder fiel dadurch durch, nicht der Code.
    2. 🔴 DER WICHTIGERE: die Notizen, die anstelle der entfernten Regeln
       stehen, NENNEN diese Regeln (sonst waeren sie nutzlos). Wer den rohen
       Blocktext durchsucht, misst seine eigene Begruendung mit und wird
       rot - drei von vier Pruefungen waren es. Das ist
       [[mlg-regel-kommentarbehandlung-misst-weg]] in ihrer haeufigeren
       Richtung: nicht der Befund wird weggeschnitten, sondern die
       Begruendung wird als Befund gezaehlt.
    """
    a = text.find("<style")
    assert a >= 0, ("Kein <style> gefunden - die Datei sieht nicht aus wie "
                    "HTML.")
    e = text.find("</style>", a)
    assert e > a, "Der erste <style>-Block ist nicht geschlossen."
    return re.sub(r"/\*.*?\*/", "", text[a:e], flags=re.S)


def test_koeder_der_sucher_findet_eine_wiederkehr():
    """🔴 Ohne Selbstprobe waere jede Null hier wertlos."""
    block = "<style>\n  .ber-table { font-size: 12px !important; }\n"
    assert ".ber-table" in _hauptblock(block + "</style>"), (
        "Der Sucher findet die Regel nicht einmal in einem Block, der nur "
        "daraus besteht.")
    # Gegenprobe: eine Regel im ZWEITEN Block (Export) zaehlt nicht mit.
    zwei = ("<style>\n  .lebt { color: red; }\n</style>\n"
            "<style>\n  .ber-table { min-width: 860px; }\n</style>")
    assert ".ber-table" not in _hauptblock(zwei), (
        "Der Sucher liest ueber den ersten Block hinaus - dann wird er rot "
        "an den\n  Export-Vorlagen, die ihre eigenen Stilbloecke "
        "mitbringen.")
    # 🔴 Der dritte Koeder, und der hat den Riegel beim ersten Lauf rot
    #    gemacht: eine NOTIZ, die die entfernte Regel nennt, darf nicht als
    #    Wiederkehr gelten. Sonst kann man eine Entfernung nicht begruenden,
    #    ohne den Riegel zu brechen.
    notiz = ("<style>\n  /* HIER STAND .ber-table - entfernt, weil der "
             "Selektor nichts trifft.\n     Auch button[title*=\"Jetzt "
             "sync\"] ist weg. */\n  .lebt { color: red; }\n</style>")
    b = _hauptblock(notiz)
    assert ".ber-table" not in b and "Jetzt sync" not in b, (
        "Eine NOTIZ ueber die entfernte Regel gilt als Wiederkehr. Dann "
        "wird der Riegel\n  rot, sobald jemand erklaert, warum er gruen "
        "ist - und die Erklaerung muss weg,\n  damit der Riegel gruen "
        "wird. Das ist genau verkehrt herum.")


def test_der_hauptblock_ist_nicht_leer():
    """🔴 Gegenprobe zur Null: wird ueberhaupt etwas gelesen?"""
    b = _hauptblock(_text())
    assert len(b) > 5000 and "{" in b, (
        "Der erste <style>-Block ist nur %d Zeichen gross - dann misst die "
        "andere\n  Pruefung nichts." % len(b))


def test_die_entfernten_regeln_bleiben_entfernt():
    block = _hauptblock(_text())
    zurueck = [sel for sel in ENTFERNT if sel in block]
    assert not zurueck, (
        "%d am 29.09. entfernte Regeln stehen wieder im Hauptstilblock:\n%s\n"
        "  Sie treffen NICHTS - gemessen an 10 Ansichten mit eingesetztem "
        "Koeder\n  (scripts/tote_regeln_messen.py) und strukturell belegt. "
        "Wer sie zurueckholt,\n  muss zuerst ein Merkmal am Element "
        "vergeben - eine Klasse oder ein\n  data-Attribut."
        % (len(zurueck), "\n".join("   " + s for s in zurueck)))


def test_wer_die_regel_zurueckholt_hat_vorher_das_merkmal_vergeben():
    """🔴 Die Umkehrung, und sie ist der eigentliche Punkt.

    Dieser Riegel soll eine Reparatur nicht verhindern. Wird das Merkmal
    wirklich vergeben, DARF die Regel zurueck - dann ist sie keine Attrappe
    mehr. Gemessen wird also nicht „die Regel fehlt", sondern „Regel ohne
    Merkmal".
    """
    text = _text()
    block = _hauptblock(text)
    schief = []
    for sel, vergabe in ENTFERNT.items():
        if sel not in block:
            continue
        if not re.search(vergabe, text):
            schief.append(sel)
    assert not schief, (
        "%d Regeln sind zurueck, ohne dass das Merkmal irgendwo vergeben "
        "wird:\n%s\n  Eine Regel fuer ein Bauteil, das es nicht gibt, "
        "taeuscht den naechsten Leser."
        % (len(schief), "\n".join("   " + s for s in schief)))
