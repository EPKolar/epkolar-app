# -*- coding: utf-8 -*-
"""Wer einen Monteur-NAMEN aus einer Wochenplanzelle holt, fragt nach dem Tag.

🔴 FRAGE 27, gemessen am 28.09.2026, gebaut am 29.09. `WeekPlan` prueft den
Austritt an vier Stellen ueber `_wpMaSichtbarAmTag(m, isoTag)`.
`WochenplanTafel` - die Tafel am Wandbildschirm - prueft ihn an KEINER:

    const maName = id => { const m = monteure.find(x=>x.id===id);
                           return m ? (m.n||'') : ''; };

Kein Tag, keine Pruefung. Ein ausgetretener Mitarbeiter stand damit weiter in
**allen sechs Tagesspalten** - auf dem Bildschirm, den die halbe Firma sieht.

AM SCHIRM GEMESSEN, vorher und nachher
(`python scripts/tafel_austritt_wirkung.py`), mit drei erfundenen Leuten:

                                  vorher      nachher
    aktiv, kein Austritt          steht da    steht da
    Austritt in 400 Tagen         steht da    steht da
    Austritt vorige Woche         STEHT DA    weg

Die beiden ersten Zeilen sind die Selbstprobe. Ohne sie waere „der
Ausgetretene ist weg" von „es wurde gar nichts gezeichnet" nicht zu
unterscheiden - und ein Riegel, der nur Ausgetretene zaehlt, waere auch bei
„alle weg" gruen.

🔴 WAS DIESER RIEGEL MISST. Nicht „kommt `_wpMaSichtbarAmTag` im Bauteil
vor" - das waere Anwesenheit, und die Wirkung steht schon oben. Gemessen wird
die ganze KLASSE, damit eine dritte Tafel nicht wieder durchrutscht:

    Jede Stelle, die aus einer Monteur-Kennung den NAMEN (`m.n`) holt,
    muss im selben Block `_wpMaSichtbarAmTag` fragen.

Wer nur die ROLLE holt (`m.r`, fuer den Farbbalken), muss nicht fragen: der
Balken wird nur gezeichnet, wenn der Name schon da ist. Diese eine Ausnahme
ist gebucht und wird MITGEZAEHLT - verschwindet sie oder kommt eine zweite
dazu, wird der Riegel rot statt sie stillschweigend zu erlauben.

🔴 `_maIstEhemalig` wird dabei nur GERUFEN, nie angefasst - es steht unter
Byte-Gleichheit. Und es gibt KEINEN eigenen Vergleich auf `.austritt`: die
Austrittsregel steht an EINER Stelle, siehe test_austritt_eine_regel_v952.
"""
import io
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "scripts"))

import code_scan  # noqa: E402

PFAD = os.path.join(HIER, "..", "index.html")

AUFLOESUNG = "monteure.find(x=>x.id===id)"
PRUEFUNG = "_wpMaSichtbarAmTag"
# So viele Stellen gibt es heute: drei liefern den Namen, eine nur die Rolle.
ERWARTET_GESAMT = 4
ERWARTET_NUR_ROLLE = 1


def _text():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _innerster_block(text, pos, ist):
    """Der innerste `{...}`-Block, der `pos` umschliesst.

    🔴 KEIN `slice` um die Fundstelle. Ein Fenster fester Groesse ist selbst
    die Luecke - es schneidet die Pruefung weg, sobald jemand einen Kommentar
    dazwischenschreibt. Geholt wird per Klammerabgleich, siehe
    [[mlg-regel-beide-enden-gemessen-mitte-blind]].
    """
    bester = None
    i = text.rfind("{", 0, pos)
    # Rueckwaerts, hoechstens 4000 Klammern weit - jede oeffnende Klammer
    # davor kommt in Frage, die innerste passende gewinnt.
    n = 0
    while i >= 0 and n < 4000:
        n += 1
        if i < len(ist) and ist[i]:
            ende = code_scan._klammer_zu(text, i, "{", "}")
            if ende > pos:
                bester = (i, ende)
                break
        i = text.rfind("{", 0, i)
    if not bester:
        return None
    return text[bester[0] + 1:bester[1] - 1]


def _ohne_kommentare(s):
    """🔴 Sonst erfuellt die Begruendung den Riegel - oder bricht ihn.

    Der Kommentar an der kurierten Stelle nennt `_wpMaSichtbarAmTag`
    ausdruecklich. Wer den ROHEN Text misst, findet die Pruefung auch dann,
    wenn nur noch die Erklaerung dasteht und der Aufruf weg ist. Genau so ist
    der SOS-Riegel am 27.09. gruen geblieben.
    """
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"//[^\n]*", "", s)


def _fundstellen(text, ist):
    """Die Stellen von AUFLOESUNG, die im CODE liegen.

    🔴 NICHT `code_scan.nur_code_stellen`. Das eicht sich an den
    `isMob`-Deklarationen der echten Datei und bricht - zu Recht - an einem
    Kunsttext ab. Damit waeren die Koeder nicht zu fahren, und ein Riegel
    ohne Koeder ist keiner. Gesucht wird deshalb direkt, mit derselben
    Code-Maske.
    """
    aus, i = [], text.find(AUFLOESUNG)
    while i >= 0:
        if i < len(ist) and ist[i]:
            aus.append(i)
        i = text.find(AUFLOESUNG, i + 1)
    return aus


def _stellen(text=None):
    """(Zeile, holt_namen, fragt) je Aufloesung einer Monteur-Kennung."""
    if text is None:
        text = _text()
        ist = code_scan.ist_code(text)
    else:
        # Kunsttext aus einem Koeder: er besteht nur aus Code.
        ist = [True] * len(text)
    aus = []
    for pos in _fundstellen(text, ist):
        block = _innerster_block(text, pos, ist)
        if block is None:
            continue
        rein = _ohne_kommentare(block)
        aus.append((text.count("\n", 0, pos) + 1,
                    bool(re.search(r"\bm\.n\b", rein)),
                    PRUEFUNG in rein))
    return aus


def test_koeder_der_sucher_sieht_die_ALTE_form():
    """🔴 Drei Koeder: die kranke Form, die kurierte, und die Ausnahme."""
    krank = ("const maName=id=>{const m=monteure.find(x=>x.id===id);"
             "return m?(m.n||''):'';};")
    s = _stellen(krank)
    assert len(s) == 1 and s[0][1] and not s[0][2], (
        "Der Sucher sieht die ALTE Form nicht als Befund: %r.\n"
        "  Dann ist seine Null an der echten Datei wertlos." % (s,))

    kuriert = ("const maName=(id,t)=>{const m=monteure.find(x=>x.id===id);"
               "return (m&&_wpMaSichtbarAmTag(m,t))?(m.n||''):'';};")
    s = _stellen(kuriert)
    assert len(s) == 1 and s[0][1] and s[0][2], (
        "Der Sucher haelt auch die KURIERTE Form fuer schlecht: %r.\n"
        "  Dann ist er nicht rot wegen des Mangels, sondern immer." % (s,))

    rolle = ("const maRole=id=>{const m=monteure.find(x=>x.id===id);"
             "return m?(m.r||''):'';};")
    s = _stellen(rolle)
    assert len(s) == 1 and not s[0][1], (
        "Eine Stelle, die nur die ROLLE holt, wird als Namensstelle "
        "gezaehlt: %r.\n  Dann wird der Riegel an etwas rot, das kein "
        "Mangel ist." % (s,))


def test_koeder_ein_kommentar_erfuellt_den_riegel_NICHT():
    """🔴 Der Aufruf entfernt, die Erklaerung stehengelassen -> muss ROT sein.

    Genau diese Form hat am 27.09. einen Riegel gruen gehalten, dessen
    Funktion gar nicht mehr gerufen wurde.
    """
    nur_kommentar = ("const maName=id=>{/* fragt _wpMaSichtbarAmTag */"
                     "const m=monteure.find(x=>x.id===id);"
                     "return m?(m.n||''):'';};")
    s = _stellen(nur_kommentar)
    assert len(s) == 1 and s[0][1] and not s[0][2], (
        "Ein KOMMENTAR, der `%s` nennt, erfuellt den Riegel: %r.\n"
        "  Dann bleibt er gruen, sobald jemand den Aufruf entfernt und die "
        "Begruendung\n  stehenlaesst." % (PRUEFUNG, s))


def test_die_grundgesamtheit_stimmt():
    """🔴 Gegenprobe zur Null - und eine Buchung fuer jede neue Stelle."""
    s = _stellen()
    assert len(s) == ERWARTET_GESAMT, (
        "%d Stellen loesen eine Monteur-Kennung auf, gebucht sind %d "
        "(Zeilen %s).\n"
        "  MEHR heisst: eine neue Stelle ist dazugekommen und niemand hat "
        "sie angesehen.\n  WENIGER heisst: der Sucher greift daneben und die "
        "andere Pruefung misst nichts.\n  Beides gehoert angesehen, nicht "
        "weggezaehlt."
        % (len(s), ERWARTET_GESAMT, [z for z, _, _ in s]))
    nur_rolle = [z for z, name, _ in s if not name]
    assert len(nur_rolle) == ERWARTET_NUR_ROLLE, (
        "%d Stellen holen NUR die Rolle, gebucht ist %d (Zeilen %s).\n"
        "  Die eine gebuchte ist `maRole` in der Wandtafel - sie darf ohne "
        "Pruefung\n  auskommen, weil der Farbbalken nur gezeichnet wird, "
        "wenn der Name schon da\n  ist. Eine ZWEITE solche Stelle waere eine "
        "neue Entscheidung."
        % (len(nur_rolle), ERWARTET_NUR_ROLLE, nur_rolle))


def test_jede_namensstelle_fragt_nach_dem_tag():
    s = _stellen()
    ohne = [z for z, name, fragt in s if name and not fragt]
    assert not ohne, (
        "%d Stellen holen den NAMEN eines Monteurs, ohne `%s` zu fragen "
        "(Zeile %s).\n"
        "  Ein ausgetretener Mitarbeiter steht dann weiter im Plan - auf der "
        "Wandtafel\n  in allen sechs Tagesspalten. Nicht mit einem eigenen "
        "Vergleich auf\n  `.austritt` reparieren: die Austrittsregel steht "
        "an EINER Stelle.\n  Beleg am Schirm: python "
        "scripts/tafel_austritt_wirkung.py"
        % (len(ohne), PRUEFUNG, ohne))
