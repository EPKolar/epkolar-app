# -*- coding: utf-8 -*-
"""Die Wochenplanung: volle Monteursnamen, keine Schrift unter 12 px.

🔴 DER BEFUND, DEN KEINE MESSUNG FINDEN KONNTE
Der Monteursname in der Tageszelle stand auf `_kurz(nm,6)` bei 9 px, dazu
nowrap und ellipsis. `_kurz` schneidet HART und haengt ein Auslassungszeichen
an: aus "Steinbichler" wird "Steinb…". Bei neun Monteuren sind zwei Nachnamen
mit gleichem Anfang auf sechs Zeichen nicht mehr zu unterscheiden.

Und der Grund, warum das am Schirm unsichtbar war: der fest eingebaute
Vorgabeplan `W0` fuehrt die Kuerzel w1, w2, w3, w5 - ZWEI Zeichen. Daran
kuerzt `_kurz(nm,6)` nichts. Jede Messung, die auf W0 laeuft, ist fuer diesen
Mangel prinzipiell blind. Und die echte Saat erreicht die Wochenplanung nicht:
der Offline-Speicher fuehrt 21 Speicher und KEINEN fuer den Wochenplan; `rows`
kommt aus `_wpGet(kw)||W0`, `_wpGet` liest `wpHistory`, und das fuellt allein
der Server ueber einen Weg, der in diesem Lauf TABU ist.
Deshalb ist dieser Riegel eine QUELLTEXT-Probe, und das ist hier keine
Notloesung, sondern die einzige Stelle, an der der Mangel ueberhaupt sichtbar
ist. Die Ansicht bleibt am Schirm zu Recht als "nicht aussagekraeftig"
gestempelt.

🔴 UND EINE EIGENE FEHLMELDUNG, DIE HIERHIN GEHOERT
Ich habe zuerst nach `slice(0,N)` und `substr(0,N)` gesucht, nichts gefunden
und daraus geschlossen, die sechs Zeichen kaemen von CSS. Der Hausname der
Kuerzung heisst `_kurz`. Ein Muster, das eine Schreibweise nicht kennt, meldet
"kommt nicht vor" - und das ist von einem echten Befund nicht zu
unterscheiden. Deshalb prueft dieser Riegel ALLE drei Formen.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import code_scan  # noqa: E402

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")
GROESSE = re.compile(r"fontSize\s*:\s*(\d+(?:\.\d+)?)(?![\d.])")

# Alle drei Formen der Kuerzung, nicht nur die, an die ich zuerst dachte.
KUERZUNGEN = (
    re.compile(r"_kurz\s*\(\s*\w+\s*,\s*(\d+)\s*\)"),
    re.compile(r"\.slice\(\s*0\s*,\s*(\d+)\s*\)"),
    re.compile(r"\.substr(?:ing)?\(\s*0\s*,\s*(\d+)\s*\)"),
)


def _lies():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _spanne(text):
    feld = code_scan.ist_code(text)
    a = text.index("function WeekPlan(")
    b = min(m.start() for m in re.finditer(r"function\s+[A-Z]\w+\s*\(", text)
            if feld[m.start()] and m.start() > a)
    return a, b


def nur_code(text, a, b):
    """Der Abschnitt OHNE Kommentare und Zeichenkettentexte.

    🔴 WARUM DAS NOETIG IST - es ist mir hier selbst passiert. Der
    Kommentar, mit dem ich die Kur erklaert habe, zitiert `_kurz(nm,6)` zweimal.
    Der Riegel las rohen Dateitext und wurde davon ROT, obwohl der Code stimmt.
    Dieselbe Krankheit wie am 26.09. - nur andersherum: wer rohen Dateitext
    durchsucht, misst seine eigene Begruendung mit. Gruen, sobald jemand sie
    loescht; rot, sobald jemand sie hinschreibt.
    """
    feld = code_scan.ist_code(text)
    return "".join(text[i] if feld[i] else " " for i in range(a, b))


def kleine(abschnitt):
    return [m.group(1) for m in GROESSE.finditer(abschnitt)
            if float(m.group(1)) < 12]


def kurzungen_unter(abschnitt, grenze):
    """Jede Kuerzung auf weniger als `grenze` Zeichen, in JEDER Form."""
    aus = []
    for muster in KUERZUNGEN:
        for m in muster.finditer(abschnitt):
            if int(m.group(1)) < grenze:
                aus.append(m.group(0))
    return aus


def test_keine_schrift_unter_12px():
    text = _lies()
    a, b = _spanne(text)
    seg = nur_code(text, a, b)
    # 🔴 Die Grundgesamtheit wird an ALLEN fontSize-Angaben gemessen, nicht nur
    # an den Zahlen. Nach dem Heben stehen dort Token (UI.fMeta), die Zahl der
    # ZAHLEN sinkt also planmaessig - von 114 auf 63. Eine Klinke auf die
    # Zahlen haette diesen Riegel durch die eigene Kur rot gemacht, und genau
    # das ist beim ersten Lauf passiert.
    alle = len(re.findall(r"fontSize\s*:", seg))
    assert alle > 80, (
        "\U0001F534 Nur %d fontSize-Angaben in WeekPlan - die Spanne stimmt "
        "nicht, und eine\n  leere Grundgesamtheit meldet immer gruen." % alle)
    fund = kleine(seg)
    assert not fund, (
        "\U0001F534 %d feste Schriftgroessen unter 12 px in der "
        "Wochenplanung: %s" % (len(fund), sorted(set(fund))))


def test_der_monteursname_wird_nicht_gekuerzt():
    """Kein Name der Tageszelle darf auf unter 12 Zeichen geschnitten werden.

    Zwolf, nicht sechs: `Steinbichler` hat zwoelf, `Paschinger` zehn. Eine
    Grenze bei sechs waere genau der Fehler, der behoben wurde.
    """
    text = _lies()
    a, b = _spanne(text)
    fund = kurzungen_unter(nur_code(text, a, b), 12)
    # DSHORT-Kuerzel und Wochentage duerfen kurz sein - die sind keine Namen.
    fund = [x for x in fund if "_kurz" in x]
    assert not fund, (
        "\U0001F534 Die Wochenplanung kuerzt wieder hart: %s\n"
        "  `_kurz` haengt ein Auslassungszeichen an und schneidet ab - aus "
        "Steinbichler wird\n"
        "  Steinb…. Bei neun Monteuren sind zwei Nachnamen mit gleichem "
        "Anfang dann nicht\n"
        "  mehr zu unterscheiden. Der Auftrag verlangt: UMBRECHEN statt "
        "kuerzen." % fund)


def test_der_name_bricht_um_statt_zu_kuerzen():
    """Die WIRKUNG, nicht die Abwesenheit: die Zelle muss umbrechen duerfen."""
    text = _lies()
    a, b = _spanne(text)
    seg = text[a:b]
    # Die Namens-Spanne der Tageszelle, an ihrem title=nm erkennbar.
    m = re.search(r"React\.createElement\('span',\{key:id,title:nm,style:\{[^}]*\}\}",
                  seg)
    assert m, (
        "\U0001F534 Die Namens-Spanne der Tageszelle ist nicht mehr "
        "auffindbar - der Riegel\n  misst dann nichts.")
    stil = m.group(0)
    assert "nowrap" not in stil, (
        "\U0001F534 Der Monteursname steht wieder auf nowrap: %s" % stil[:160])
    assert "ellipsis" not in stil, (
        "\U0001F534 Der Monteursname steht wieder auf ellipsis: %s" % stil[:160])
    assert ("overflowWrap" in stil or "wordBreak" in stil), (
        "\U0001F534 Der Monteursname darf nicht umbrechen - dann laeuft er "
        "aus der Spalte,\n  statt in zwei Zeilen zu passen: %s" % stil[:160])


def test_koeder_alle_drei_kuerzungsformen():
    """\U0001F534 Der Koeder gegen meine eigene Fehlmeldung.

    Ich suchte nach slice und substr, fand nichts und schloss auf CSS. Der
    Hausname ist `_kurz`. Alle drei Formen muessen anschlagen.
    """
    for fall in ("_kurz(nm,6)", "nm.slice(0,6)", "nm.substring(0,6)",
                 "nm.substr(0,6)"):
        assert kurzungen_unter(fall, 12), (
            "\U0001F534 Die Form %r wird nicht erkannt - dieselbe "
            "Alphabet-Luecke, die diesen\n  ganzen Lauf traegt." % fall)


def test_koeder_kommazahl():
    """\U0001F534 Die Falle aus v3.9.943, an dieser Ansicht belegt.

    WeekPlan fuehrte ZWEI Werte mit 9.5 und EINEN mit 10.5. Ein Muster ohne
    (?![\\d.]) liest daraus eine 9 und laesst das ".5" stehen; beim Ersetzen
    wurde daraus UI.fMeta.5 und node_check meldete 'Unexpected number'.
    """
    assert kleine('h("div",{style:{fontSize:9.5}})') == ["9.5"]
    assert kleine('h("div",{style:{fontSize:10.5}})') == ["10.5"]
    assert kleine('h("div",{style:{fontSize:12.5}})') == []


def test_gegenprobe_lange_kuerzung_und_zwoelf_schweigen():
    """Wer alles meldet, misst so wenig wie wer schweigt."""
    assert not kurzungen_unter("_kurz(nm,24)", 12)
    assert not kurzungen_unter("kw.slice(0,10)", 10)
    assert not kleine('h("div",{style:{fontSize:12}})')
    assert not kleine('h("div",{style:{fontSize:UI.fMeta}})')


def test_koeder_der_eigene_kommentar_zaehlt_NICHT_mit():
    """🔴 Der Fehler, der an DIESEM Riegel passiert ist.

    Der Kommentar, mit dem die Kur erklaert wird, zitiert `_kurz(nm,6)` zweimal.
    Die erste Fassung dieses Riegels las rohen Dateitext und wurde davon ROT,
    obwohl der Code stimmt. Die Probe belegt beide Richtungen am SELBEN Text:
    im Kommentar zaehlt es nicht, im Code schon.
    """
    # Die Zeilen werden zusammengefuegt statt mit Zeilenumbruechen in eine
    # Zeichenkette geschrieben - ein Heredoc schmilzt Backslashes, und genau
    # daran ist die erste Fassung dieser Probe zerbrochen.
    zeilen = ["function WeekPlan(){",
              "  /* voller Name statt _kurz(nm,6) - siehe v3.9.967 */",
              "  var x = 1;",
              "}",
              "function Danach(){return 0;}"]
    text = "\r\n".join(zeilen) + "\r\n"
    b = text.index("function Danach(")
    assert not kurzungen_unter(nur_code(text, 0, b), 12), (
        "🔴 Der Riegel hat seine eigene Begruendung mitgezaehlt.")
    text2 = text.replace("var x = 1;", "var x = _kurz(nm,6);")
    b2 = text2.index("function Danach(")
    assert kurzungen_unter(nur_code(text2, 0, b2), 12), (
        "🔴 Am selben Text meldet der Riegel die echte Kuerzung nicht - dann "
        "schweigt\n  er immer, und die Probe oben ist wertlos.")
