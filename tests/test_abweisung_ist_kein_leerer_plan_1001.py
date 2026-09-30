# -*- coding: utf-8 -*-
"""B1-Kiosk — eine Abweisung sah aus wie „heute nichts geplant".

**Am Schirm gemessen:** die Wochenplantafel zeigte bei einer Abweisung des
Zeilenschutzes denselben Text wie bei einem wirklich leeren Plan — „Keine
Wochenplan-Zeilen für KW 40". Die Textlängen unterschieden sich um **drei
Zeichen**, und die steckten in einer Fahrzeug-Diagnose daneben.

Auf einer Wand ist das der teuerste Fall: *„heute nichts geplant"* ist eine
Aussage, nach der jemand handelt — und niemand steht daneben, der nachfragt.

## Die Kenntnis lag die ganze Zeit im Browser

Bei derselben Messung standen **elf Einträge** in `window.__EP_RLS` — der
Merkliste, die seit v3.9.910 jeden Rechtefehler mitschreibt. Keine der drei
Tafeln sah sie an.

## Warum nicht das Array gefragt wird

Das leere Array trägt seit v3.9.910 seinen Grund als `__rlsFehler` mit, und
`_rlsLeer()` fragt genau das. Das ist der **genauere** Weg und bleibt der
erste. Er hilft aber nur, solange man das Array noch in der Hand hat: die
Tafel baut ihre Zeilen aus einer **Karte** und kopiert sie mit `.slice()` —
dabei fällt das Feld weg. Beide Enden richtig, die Mitte blind.

## 🔴 Die Meldehäufigkeit ist gemessen, nicht geschätzt

Die Merkliste füllt sich **ausschließlich** bei 401/403. In der Messung:
leere Antwort → 0 Einträge, Abweisung → 11. Dieser Hinweis erscheint also
**0×/Tag**, solange nichts abgewiesen wird.

Das ist der Unterschied zu dem Melder, den ich am selben Tag zu breit gebaut
habe (B2, `limit=1`, Hinweis bei jedem Einzelabruf). Deshalb ist er hier eng
gefasst: nur `weekplan_rows`, nur die letzten fünf Minuten, und nur wenn die
Tafel wirklich keine Zeilen hat.
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
    mit = '/* HIER STAND "Keine Wochenplan-Zeilen für KW " */ x=1;'
    assert "Keine Wochenplan-Zeilen" not in _ohne_kommentare(mit), (
        "Ein Kommentar, der die alte Form zitiert, wird mitgezaehlt.")


def test_die_tafel_unterscheidet_abweisung_von_leer():
    code = _ohne_kommentare(_text())
    assert '_rlsKuerzlich("weekplan_rows")' in code, (
        "\U0001F534 Die Tafel fragt die Merkliste nicht mehr. Dann zeigt sie "
        "bei einer\n  Abweisung wieder denselben Satz wie bei einem leeren "
        "Plan - und auf einer Wand\n  ist \"heute nichts geplant\" eine "
        "Aussage, nach der jemand handelt.")
    assert "keine Leseberechtigung" in code, (
        "\U0001F534 Der Text fuer den Abweisungsfall fehlt.")
    assert "Das ist KEIN leerer Plan" in code, (
        "\U0001F534 Der Satz, der die beiden Faelle auseinanderhaelt, fehlt. "
        "Ohne ihn liest\n  man die Meldung wieder als \"nichts zu tun\".")


def test_der_leere_plan_sagt_weiterhin_leer():
    """🔴 Gegenprobe: der Normalfall darf NICHT zur Warnung werden.

    Ein wirklich leerer Plan ist kein Fehler. Wer hier unbedingt warnt,
    macht die Meldung wertlos, bevor sie je gebraucht wird.
    """
    code = _ohne_kommentare(_text())
    assert '"Keine Wochenplan-Zeilen für KW "+kw' in code, (
        "\U0001F534 Der Text fuer den WIRKLICH leeren Plan ist verschwunden. "
        "Dann meldet die\n  Tafel auch dann eine Abweisung, wenn schlicht "
        "nichts geplant ist.")


def test_der_helfer_ist_eng_gefasst():
    """🔴 Er darf nicht bei fremden Fehlern anschlagen.

    `window.__EP_RLS` sammelt Rechtefehler ALLER Tabellen. Ohne Filter auf
    Tabelle und Zeitfenster würde ein Fehler irgendwo im Haus die Tafel eine
    Abweisung melden lassen, die es dort nie gab.
    """
    t = _text()
    i = t.find("function _rlsKuerzlich(")
    assert i > 0, "\U0001F534 Der Helfer ist weg."
    rumpf = t[i:i + 900]
    assert ".tab===tab" in rumpf, (
        "\U0001F534 Der Helfer filtert nicht mehr nach der TABELLE - dann "
        "meldet die Tafel\n  einen Fehler, den es dort nie gab.")
    assert "Date.now()-(ms||" in rumpf, (
        "\U0001F534 Das Zeitfenster fehlt - dann bleibt ein alter Fehler "
        "fuer immer stehen.")


def test_der_genauere_weg_bleibt_bestehen():
    """`_rlsLeer` fragt das Array selbst und ist genauer. Die Merkliste ist
    der Rückfall für die Stellen, an denen das Array unterwegs verloren
    geht — sie ersetzt ihn nicht."""
    code = _ohne_kommentare(_text())
    assert "function _rlsLeer(liste){" in code, (
        "\U0001F534 `_rlsLeer` ist weg. Die Merkliste ist der GROEBERE Weg - "
        "sie darf den\n  genaueren nicht verdraengen.")


def test_warnung_traegt_text_und_farbe():
    """🔴 Nie Farbe allein — die Tafel wird aus einigen Metern gelesen."""
    code = _ohne_kommentare(_text())
    i = code.find('_rlsKuerzlich("weekplan_rows")?\'#B4530A\'')
    assert i > 0, (
        "\U0001F534 Die Warnfarbe des Hauses fehlt am Leerzustand.")
    umfeld = code[i:i + 400]
    assert "fontWeight:_rlsKuerzlich" in umfeld, (
        "\U0001F534 Die Warnung ist nicht mehr fett - auf einer Wand ist das "
        "der Unterschied\n  zwischen gelesen und uebersehen.")
