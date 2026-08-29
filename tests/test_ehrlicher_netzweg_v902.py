# -*- coding: utf-8 -*-
"""v3.9.902 - "WLAN verbunden" war keine Aussage ueber den Uebertragungsweg.

    const isWifi = conn ? conn.type==="wifi" || conn.effectiveType==="4g"
                          && !conn.saveData : true;

Zwei Wege, auf denen das luegt, und beide sind der Normalfall:

  * FEHLT die Network-Information-API - also auf JEDEM iPhone und in Firefox -,
    ist der ganze Ausdruck konstant `true`. Der Monteur liest "WLAN verbunden"
    mit gruenem Punkt, waehrend er im Mobilfunk steht.
  * Ist sie da, aber ohne `type` (Desktop-Chrome liefert meist nur
    `effectiveType`), entscheidet `effectiveType==="4g"` - eine
    GESCHWINDIGKEITSKLASSE, kein Uebertragungsweg. Gutes LTE meldet exakt "4g".

Der Startwert war ebenfalls `true`: schon vor der ersten Messung behauptete die
App WLAN.

Das ist kein Schoenheitsfehler. Es ist die Grundlage einer Entscheidung: wer den
Foto-Stapel eines Tages hochlaedt, sieht vorher nach, ob er im WLAN ist.

WAS SICH AENDERT - UND WAS AUSDRUECKLICH NICHT
──────────────────────────────────────────────
Neu ist `netWeg`: der GEMESSENE Weg, ausschliesslich aus `conn.type`. Ist er
nicht messbar, bleibt er LEER - und die Anzeige sagt dann "Online" statt einer
Behauptung ueber den Weg. Nichtwissen wird als Nichtwissen gezeigt.

`isWifi` bleibt Zeichen fuer Zeichen unveraendert. Das ist Absicht: an ihm haengt
der Sync-Zweig, und der ist eine offene CHEF-ENTSCHEIDUNG (Handoff 7g #22). Diese
Auslieferung macht nur die ANZEIGE ehrlich und aendert kein Verhalten - sonst
haette sie nicht ohne Ruecksprache gehen duerfen.

WAS DAMIT NOCH NICHT ERLEDIGT IST
─────────────────────────────────
`WifiStatusIcon` zeichnet weiterhin einen WLAN-Bogen, gesteuert allein von
`online` - ein WLAN-Symbol im Mobilfunk, unabhaengig von `netWeg`. Und der
Schalter "Manuell" steuert nach wie vor nichts. Beides steht im Handoff.
"""
from _hilfen import nur_code


def test_der_weg_wird_gemessen_nicht_geraten(index_html):
    assert 'const netWeg=(_wegRoh&&_wegRoh!=="unknown")?_wegRoh:"";' in index_html, (
        "netWeg wird nicht mehr aus dem gemessenen Verbindungstyp gebildet - "
        "dann behauptet die Anzeige wieder einen Weg, den sie nicht kennt."
    )


def test_unbekannt_zaehlt_als_unbekannt(index_html):
    """Der Kern. `conn.type` liefert auf manchen Geraeten die Zeichenkette
    "unknown" - die als Weg durchzureichen waere dieselbe Luege in neu."""
    i = index_html.find("const netWeg=")
    assert i != -1
    zeile = index_html[i:i + 120]
    assert '!=="unknown"' in zeile, (
        "Der Wert 'unknown' wird nicht mehr als unbekannt behandelt:" + chr(10) + zeile
    )


def test_der_startwert_behauptet_nichts(index_html):
    """Vor der ersten Messung darf kein Weg behauptet werden. `isWifi` startete
    auf true und sagte damit WLAN, bevor irgendetwas gemessen war."""
    i = index_html.find("const [syncStatus,setSyncStatus]=")
    assert i != -1, "syncStatus-Zustand nicht gefunden"
    zeile = index_html[i:i + 320]
    assert 'netWeg:""' in zeile, (
        "Der Startwert von netWeg ist nicht leer - dann behauptet die App "
        "einen Weg, bevor sie gemessen hat:" + chr(10) + zeile[:220]
    )


def test_keine_anzeige_haengt_mehr_an_isWifi(index_html):
    """KOMMENTARBLIND: der erklaerende Kommentar zur Umstellung nennt isWifi
    naturgemaess. Ohne nur_code schluege dieser Riegel an meinem eigenen
    Erklaertext an - in diesem Repo an zwei Tagen elfmal passiert."""
    code = nur_code(index_html)
    assert 'syncStatus.isWifi?"' not in code, (
        "Ein Anzeigetext haengt wieder direkt an isWifi. isWifi ist auf jedem "
        "iPhone und in Firefox konstant true - der Text behauptet dann WLAN, "
        "ohne etwas zu wissen."
    )


def test_isWifi_selbst_ist_unveraendert(index_html):
    """GEGENPROBE, und die wichtigste: an isWifi haengt der Sync-Zweig. Diese
    Auslieferung durfte nur die ANZEIGE anfassen. Waere isWifi mitgeaendert
    worden, haette sich das VERHALTEN geaendert - und das ist eine offene
    Chef-Entscheidung, keine stille Reparatur."""
    assert ('const isWifi=conn?conn.type==="wifi"||conn.effectiveType==="4g"'
            '&&!conn.saveData:true;') in index_html, (
        "isWifi wurde mitgeaendert. Diese Version sollte ausschliesslich die "
        "Anzeige ehrlich machen und das Sendeverhalten unangetastet lassen."
    )


def test_die_anzeige_kennt_drei_zustaende(index_html):
    """WLAN / Mobilfunk / nicht messbar. Zwei Zustaende waeren zu wenig:
    "kein WLAN" und "weiss nicht" sind verschiedene Aussagen, und genau ihre
    Vermischung war der Fehler."""
    code = nur_code(index_html)
    treffer = code.count('netWeg==="wifi"')
    assert treffer >= 2, (
        "Die Weg-Unterscheidung steht nur %d mal im Code - erwartet werden "
        "mindestens zwei Anzeigestellen, Kopfzeile und Sync-Panel." % treffer
    )
    assert "nicht messbar" in index_html, (
        "Der dritte Zustand fehlt - dann faellt 'unbekannt' wieder mit "
        "'kein WLAN' zusammen, und das war die Luege."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace('const netWeg=(_wegRoh&&_wegRoh!=="unknown")?_wegRoh:"";',
                            'const netWeg="wifi";', 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert 'const netWeg=(_wegRoh&&_wegRoh!=="unknown")?_wegRoh:"";' not in z1, (
        "Umkehrprobe: der Mess-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace('netWeg:""', 'netWeg:"wifi"', 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    i = z2.find("const [syncStatus,setSyncStatus]=")
    assert 'netWeg:""' not in z2[i:i + 320], (
        "Umkehrprobe: der Startwert-Riegel wuerde nicht anschlagen"
    )
