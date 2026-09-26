# -*- coding: utf-8 -*-
"""v3.9.956 - wie viel von index.html das Klammertor ueberhaupt liest.

WIE DAS GEFUNDEN WURDE
──────────────────────
In v3.9.956 habe ich in einen Blockkommentar in index.html ein Paar Backticks
geschrieben - `ueberschriften: []`, die uebliche Zitierweise dieser Datei.
Danach meldete scripts/_bracket_check.py `() -4` statt der Grundlinie `() -1`,
und tests/test_bracket_drift_guard.py wurde rot.

Die Ursache war NICHT eine Klammer. Der Streicher in _bracket_check.py setzt
das Template-Literal-Muster VOR das Kommentarmuster. Mein Backtick wurde als
ENDE eines viel frueher geoeffneten Template-Literals gelesen: ein einzelner
Treffer lief ueber 375.741 Zeichen echten Code und nahm dessen Klammern mit.
Am Quelltext war nichts falsch; gemessen wurde 375 kB weniger.

Das ist die Fehlerform aus v3.9.936 in neuer Kleidung: dort hielt ein
Sternchen in `accept:"application/pdf,image/*"` den Zaehler fuer einen
Kommentaranfang und liess die letzten 80 kB als Kommentar gelten.

🔴 UND DABEI KAM DAS GROESSERE HERAUS
─────────────────────────────────────
Der Zustand war nicht erst durch mich kaputt. Gemessen am heilen Stand:

    Datei            3.663.123 Zeichen
    gestrichen       2.640.833  = 72,1 %
    beurteilt        1.022.290  = 27,9 %

und davon gehen 1.466.372 Zeichen (40,0 % der Datei) auf 22 Treffer, die mit
einem Backtick beginnen und laenger als 20.000 Zeichen sind. Bei den meisten
folgt dem Backtick deutsche Kommentar-Prosa:

    "` wird BENUTZT, nicht nachgebaut; die Funktion bleibt bytegleich. */..."
    "` war immer truthy -> ALLE FS-Chips hatten blauen Rand */,cursor:..."

Das sind keine Template-Literale. Diese Datei zitiert in Kommentaren mit
Backticks, und jeder einzelne verschiebt die Paarung. Die Folge: die
Grundlinie `() -1` ist die Restsumme dessen, was uebrig bleibt - keine
Aussage ueber die Klammern des Codes. In den blinden Bereichen liegen
Klammer-Ungleichgewichte im Umfang von 52.

WAS DIESE DATEI TUT - UND WAS SIE AUSDRUECKLICH NICHT TUT
─────────────────────────────────────────────────────────
Sie ERSETZT das Tor nicht und aendert es nicht. Ein besserer Streicher wuerde
eine andere Grundlinie ergeben, und ob eine neue Zahl echt oder ein Artefakt
ist, ist eine Entscheidung fuer Sebastian - nicht etwas, das ich im
Vorbeigehen umschreibe. Ein Tor anzupassen, weil man es besser zu wissen
glaubt, ist dieselbe Bewegung wie es gruen zu machen.

Sie NAGELT die Blindheit FEST, damit sie nicht weiter waechst:
  * der Anteil der gestrichenen Zeichen darf nicht ueber 73 % steigen
  * kein Treffer, der mit einem BACKTICK beginnt, darf laenger als 250.000
    Zeichen sein (der laengste echte ist 196.656 - ein HTML-Bericht als
    Template-Literal; mein Unfall war 375.741). Nicht der laengste Treffer
    ueberhaupt: das ist der Changelog-Kommentar hinter APP_VERSION mit
    256.069 Zeichen, ein echter Kommentar, der mit jeder Version waechst.

Eine Obergrenze und kein Festwert, weil diese Datei in Kommentaren mit
Backticks zitiert: jeder normale Kommentar bewegt die Zahl ein wenig. Was
NICHT passieren darf, ist der Sprung.
"""
import io
import os
import re

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

# Genau die Muster aus scripts/_bracket_check.py, in genau dieser Reihenfolge.
# Eine Abweichung hier waere eine Aussage ueber ein anderes Werkzeug.
PATTERNS = [
    r'"(?:[^"\\]|\\.)*"',
    r"'(?:[^'\\]|\\.)*'",
    r"`(?:[^`\\]|\\.)*`",
    r"/\*[\s\S]*?\*/",
    r"//[^\n]*",
]
STREICHER = re.compile("|".join(PATTERNS))

ANTEIL_MAX = 0.73        # gemessen 0.721 am 26.09.2026
TREFFER_MAX = 250_000    # laengster echter 196.656; der Unfall war 375.741


def _lies():
    roh = io.open(PFAD, encoding="utf-8", newline="").read()
    if len(roh) < 3_000_000:
        raise AssertionError(
            "index.html hat nur %d Bytes - Datenverlust. Eine leere Datei hat "
            "uebrigens eine SAUBERE Klammerbilanz; das ist genau der Grund, "
            "warum hier zuerst die Groesse geprueft wird." % len(roh))
    return roh


def _messen(text):
    """(gestrichene Zeichen, laengster BACKTICK-Treffer).

    🔴 Ausdruecklich nur Backtick-Treffer beim Laengsten. Die erste Fassung
    nahm den laengsten Treffer ueberhaupt - und das ist der
    Changelog-Kommentar hinter APP_VERSION mit 256.069 Zeichen. Der ist ein
    echter Blockkommentar, korrekt erkannt, und er WAECHST mit jeder Version.
    Eine Grenze darauf haette bei der naechsten Versionszeile rot gemeldet und
    nichts gemessen als das Wachsen der eigenen Geschichte.

    Was den Unfall ausmacht, ist ein Treffer, der mit einem BACKTICK beginnt:
    dort ist der Backtick das Ende eines viel frueher geoeffneten Literals,
    und der Code dazwischen faellt aus der Bilanz.
    """
    gesamt = 0
    laengster = (0, -1)
    for m in STREICHER.finditer(text):
        ln = m.end() - m.start()
        gesamt += ln
        if m.group(0).startswith("`") and ln > laengster[0]:
            laengster = (ln, m.start())
    return gesamt, laengster


def test_das_klammertor_liest_nicht_noch_weniger():
    """Der gestrichene Anteil darf nicht ueber 73 % steigen.

    27,9 % beurteilt ist schon wenig. Steigt der Anteil, ist entweder ein
    weiterer Backtick in einen Kommentar geraten oder ein Literal ist
    unbeendet - und dann meldet das Tor eine Bilanz ueber immer weniger Code,
    ohne dass irgendwo etwas rot wird.
    """
    roh = _lies()
    gesamt, _ = _messen(roh)
    anteil = gesamt / len(roh)
    assert anteil <= ANTEIL_MAX, (
        "Das Klammertor streicht %.1f %% der Datei weg (Grenze %.0f %%), "
        "beurteilt also nur %.1f %%.\n"
        "Wahrscheinlichste Ursache: ein neuer Backtick in einem Kommentar. "
        "Diese Datei zitiert in Kommentaren mit Backticks, und jeder einzelne "
        "verschiebt die Paarung der Template-Literale - der naechste Treffer "
        "frisst dann zehntausende Zeichen echten Code, und seine Klammern "
        "fehlen in der Bilanz.\n"
        "Suchen: den laengsten Streichtreffer und nachsehen, ob sein Inhalt "
        "Prosa ist." % (100 * anteil, 100 * ANTEIL_MAX, 100 * (1 - anteil)))


def test_kein_einzelner_treffer_frisst_die_halbe_datei():
    """Ein BACKTICK-Treffer ueber 250.000 Zeichen ist kein Literal mehr.

    Der laengste echte ist 196.656 Zeichen - ein HTML-Bericht, der als
    Template-Literal gebaut wird. Mein Unfall in v3.9.956 war 375.741.
    """
    roh = _lies()
    _, (laenge, pos) = _messen(roh)
    assert laenge <= TREFFER_MAX, (
        "Ein Streichtreffer ist %d Zeichen lang (Grenze %d), beginnend in "
        "Zeile %d mit:\n  %r\n"
        "Faengt er mit einem Backtick an und folgt Prosa: dann ist es kein "
        "Template-Literal, sondern ein Backtick in einem Kommentar, der das "
        "naechste offene Literal abschliesst. Der Code dazwischen wird nicht "
        "mehr gezaehlt."
        % (laenge, TREFFER_MAX, roh.count("\n", 0, pos) + 1,
           roh[pos:pos + 90]))


def test_der_riegel_wird_bei_einem_backtick_im_kommentar_rot():
    """KOEDER - und zwar der echte Unfall, nachgestellt.

    Beide Pruefungen oben MESSEN und vergleichen mit einer Grenze. Eine
    Messung, die ins Leere greift, liefert eine kleine Zahl - und eine kleine
    Zahl ist hier gruen. Also wird genau der Fall nachgestellt, der den Fund
    ausgeloest hat: ein Paar Backticks in einen Blockkommentar.
    """
    roh = _lies()
    anker = "/* v3.9.956 D9: war ein div"
    assert anker in roh, (
        "Der Kommentar, an dem der Koeder haengt, ist nicht mehr da. Dann "
        "muss der Koeder an einen anderen Blockkommentar - nicht weggelassen "
        "werden.")
    p = roh.index(anker) + len(anker)
    kaputt = roh[:p] + " `ueberschriften: []` " + roh[p:]

    gesamt_heil, (lang_heil, _) = _messen(roh)
    gesamt_kaputt, (lang_kaputt, _) = _messen(kaputt)

    assert gesamt_kaputt > gesamt_heil, (
        "KOEDER NICHT GEFUNDEN: ein Paar Backticks in einem Kommentar "
        "veraendert den gestrichenen Anteil nicht (%d vs %d Zeichen). Dann "
        "misst dieser Riegel nicht, was er behauptet."
        % (gesamt_kaputt, gesamt_heil))
    assert lang_kaputt > lang_heil, (
        "KOEDER NICHT GEFUNDEN: der laengste Treffer waechst nicht (%d vs "
        "%d). Genau dieses Wachstum war der Unfall - 196.656 wurde 375.741."
        % (lang_kaputt, lang_heil))
    # Und die Grenze muss dabei wirklich gerissen werden, nicht nur gestreift.
    assert lang_kaputt > TREFFER_MAX, (
        "Der Koeder waechst (%d), reisst aber die Grenze %d nicht. Dann ist "
        "die Grenze zu weit gesetzt und der Riegel wuerde den echten Unfall "
        "durchlassen." % (lang_kaputt, TREFFER_MAX))


def test_die_muster_sind_die_des_werkzeugs():
    """Diese Datei misst _bracket_check.py, nicht sich selbst.

    Weichen die Muster ab, ist jede Zahl hier eine Aussage ueber ein anderes
    Werkzeug - und die Grenzen oben waeren aus der Luft gegriffen.
    """
    quelle = io.open(os.path.join(os.path.dirname(__file__), "..", "scripts",
                                  "_bracket_check.py"), encoding="utf-8").read()
    for mus in PATTERNS:
        assert mus in quelle, (
            "Das Muster %r steht nicht mehr in scripts/_bracket_check.py. "
            "Wurde der Streicher geaendert, gelten die Grenzen dieser Datei "
            "nicht mehr - dann neu messen und die Zahlen mit Datum "
            "begruenden, nicht anpassen bis es gruen ist." % mus)
    assert "patterns = [" in quelle, (
        "Die Musterliste in _bracket_check.py ist nicht mehr zu finden. "
        "Diese Datei kann dann nicht belegen, dass sie dasselbe misst.")
