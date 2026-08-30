# -*- coding: utf-8 -*-
"""v3.9.892 - Die Dispo sagte seit jeher, ob eine Dauer geraten ist. Niemand hat zugehoert.

BEFUND: `_dispoDauer` liefert `{min, geschaetzt}`. Das Flag steht dort seit der
Einfuehrung der Quellenkette:

    1. gesetzte dauer            -> geschaetzt:false
    2. gelernter Klassen-Median  -> geschaetzt:true
    3. Typ-Median / Typ-Fallback -> geschaetzt:true
    4. Text-Stichwort            -> geschaetzt:true
    5. Default 90 min            -> geschaetzt:true

Gemessen: `geschaetzt` kam **zehnmal** in der Datei vor - **alle zehn innerhalb von
`_dispoDauer` selbst**. Null Leser.

WARUM DAS MEHR IST ALS KOSMETIK - die Schaetzung bestaetigt sich selbst:

  1. Am Chip stand "1,5h" - egal ob das Buero die Dauer eingetragen oder eine
     Keyword-Regel sie geraten hat. Nicht unterscheidbar.
  2. Jede Dispo-Geste schreibt `dauer` (v3.9.740, EIN Schreibgesetz), und `dauer`
     steht in `JUPROWA_PUSH_FIELDS` -> die Schaetzung faehrt nach OFFA und steht
     dort wie eine Absprache.
  3. Beim naechsten Lauf liest `_dispoParseDauer(s.dauer)` genau diesen Wert
     zurueck - jetzt als GESETZTE Dauer, `geschaetzt:false`. Und
     `_dispoMedianJeKlasse`/`_dispoMedianJeTyp` lernen aus den `dauer`-Feldern
     abgeschlossener Scheine.

Aus einer Vermutung wird so in drei Schritten eine Tatsache, ohne dass irgendwo
ein Mensch zugestimmt haette.

FIX, bewusst begrenzt: **Stufe 2 wird NICHT angefasst.** Dass jede Geste die Dauer
schreibt, ist eine Entscheidung (v3.9.740) und kein Fehler - die melde ich, aendere
sie aber nicht. Geheilt wird Stufe 1: die Kachel sagt mit `≈`, dass die Zahl geraten
ist. Sobald jemand die Dauer selbst zieht (`_dauerOv`), verschwindet die Markierung -
dann ist sie eine Entscheidung, keine Schaetzung mehr.
"""
import re


def test_das_flag_wird_ueberhaupt_gelesen(index_html):
    """Der Kern: vorher hatte `geschaetzt` null Leser ausserhalb von _dispoDauer."""
    ohne_komm = re.sub(r"/\*.*?\*/", "", index_html, flags=re.S)
    ohne_komm = "\n".join(l for l in ohne_komm.splitlines()
                          if not l.startswith("const APP_VERSION="))
    assert "dauerGeschaetzt" in ohne_komm, (
        "Das geschaetzt-Flag wird wieder nirgends weitergereicht - dann ist eine "
        "geratene Dauer am Chip nicht von einer vereinbarten zu unterscheiden."
    )


def test_ein_aufruf_fuer_min_und_geschaetzt(index_html):
    """Zwei Aufrufe waeren zwei Rechnungen - genau die Krankheit, die v886 und
    v888 in dieser Datei aufgeraeumt haben."""
    assert "var _dd=_dispoDauer(s,null,_gelernt,_typMed);" in index_html, (
        "Der Vorschlags-Pfad holt min und geschaetzt nicht mehr aus EINEM Aufruf."
    )
    assert "var _ddf=_dispoDauer(s,null,_gelernt,_typMed);var d=_ddf.min;" in index_html, (
        "Der Fixtermin-Pfad holt min und geschaetzt nicht mehr aus EINEM Aufruf."
    )


def test_das_flag_kommt_bis_an_die_kachel(index_html):
    """Vier Stationen: Schein -> plan/fixMap -> Kachel-Objekt -> Anzeige.
    Faellt eine weg, ist die Markierung still verschwunden."""
    for stelle, was in (
        ("dauerMin:_dd.min, dauerGeschaetzt:!!_dd.geschaetzt,", "Schein-Aufbereitung"),
        ("dauerGeschaetzt:!!_ddf.geschaetzt,", "fixMap"),
        ("dauerGeschaetzt:!!x.dauerGeschaetzt,", "plan-Uebergabe"),
        ("dauerGeschaetzt:!!f.dauerGeschaetzt,", "Fix-Kachel"),
    ):
        assert stelle in index_html, (
            "Station '%s' reicht dauerGeschaetzt nicht weiter - die Markierung "
            "verschwindet dann still." % was
        )


def test_die_kachel_zeigt_es(index_html):
    assert 'o.dauerGeschaetzt?"\\u2248"' in index_html or 'o.dauerGeschaetzt?"≈"' in index_html, (
        "Die Kachel zeigt kein Zeichen fuer eine geratene Dauer."
    )
    assert "Dauer geschaetzt" in index_html, (
        "Es fehlt der erklaerende Hinweistext - ein Sonderzeichen ohne Erklaerung "
        "ist Rauschen."
    )


def test_der_dauer_griff_hebt_die_markierung_auf(index_html):
    """Wer die Dauer selbst zieht, hat entschieden - dann ist sie keine
    Schaetzung mehr. Ohne das bliebe das Zeichen stehen und waere falsch."""
    assert "dauerGeschaetzt:(!!c.dauerGeschaetzt&&_dauerOv[c.scheinId]==null)" in index_html, (
        "Der Dauer-Griff hebt die Schaetz-Markierung nicht mehr auf - dann zeigt "
        "die Kachel eine selbst gezogene Dauer weiterhin als geraten an."
    )


def test_die_quellenkette_selbst_ist_unveraendert(index_html):
    """Gegenprobe: nur die Anzeige wurde geheilt, nicht die Rechnung.

    v3.9.913 - ZWEI Umbauten hier:

    1. Das Fenster war 2000 Zeichen ab dem Funktionskopf. _dispoDauer ist aber
       nur ~800 Zeichen lang; die restlichen 1200 gehoerten _dispoHaversine und
       _dispoStrecke. Ein Fenster, dessen Groesse man frei waehlt, misst die
       Fensterbreite mit. Jetzt endet der Block an der schliessenden Klammer.

    2. Die ZAHL ist weg. Vorher: `block.count("geschaetzt:true") >= 4`. Die
       Aussage war "die Schaetz-Stufen sind vollstaendig" - aber jede Stufe hat
       einen Namen, und eine Summe sagt nicht, WELCHE fehlt. Vier Vorkommen
       haetten auch gestimmt, wenn der Typ-Median doppelt und der Text-Keyword-
       Zweig gar nicht dastuende. Und ein Kommentar mit "geschaetzt:true" haette
       eine geloeschte Stufe ersetzt. Jetzt: fuenf benannte Stufen, einzeln.
    """
    i = index_html.find("function _dispoDauer(schein,regeln,gelernt,typMedian){")
    assert i != -1, "_dispoDauer nicht gefunden"
    ende = index_html.find("\n}", i)
    assert ende != -1, "_dispoDauer hat kein Funktionsende auf Spalte 0"
    block = index_html[i:ende]
    assert "if(mn!=null)return {min:mn,geschaetzt:false};" in block, (
        "Stufe 1 (gesetzte Dauer schlaegt alles) hat sich veraendert."
    )
    for stufe, zeile in (
        ("2 Klassen-Median (n>=8)",
         "if(g&&g.n>=8)return {min:g.median,geschaetzt:true};"),
        ("3 Typ-Median (n>=8)",
         "if(t&&t.n>=8)return {min:t.median,geschaetzt:true};"),
        ("4 Typ-Fallback",
         "if(DISPO_TYP_DAUER_FALLBACK[_ta])return {min:DISPO_TYP_DAUER_FALLBACK[_ta],geschaetzt:true};"),
        ("5 Text-Keyword",
         "if(_regelMin!=null)return {min:_regelMin,geschaetzt:true};"),
        ("6 Default",
         "return {min:DISPO_DAUER_DEFAULT,geschaetzt:true};"),
    ):
        assert zeile in block, (
            "Schaetz-Stufe %s fehlt in der Quellenkette - dann liefert _dispoDauer "
            "an dieser Stelle etwas anderes als gemessen." % stufe
        )


def test_das_schreibgesetz_bleibt_unberuehrt(index_html):
    """BEWUSSTE GRENZE: dass jede Geste die Dauer schreibt (v3.9.740), ist eine
    Entscheidung und kein Fehler. Sie wird gemeldet, nicht geaendert - sonst
    haette ich einen Chef-Entscheid stillschweigend zurueckgenommen."""
    i = index_html.find("JUPROWA_PUSH_FIELDS")
    assert i != -1, "JUPROWA_PUSH_FIELDS nicht gefunden"
    assert "dauer" in index_html[i:i + 2000], (
        "dauer steht nicht mehr in der Push-Liste. Falls das Absicht ist: die "
        "Begruendung dieses Fixes (die Schaetzung faehrt nach OFFA) gilt dann nur "
        "noch fuer die eigene Datenbank - der Docstring gehoert angepasst."
    )


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace('(o.dauerGeschaetzt?"\\u2248":"")', "", 1)
    if z1 == index_html:
        z1 = index_html.replace('(o.dauerGeschaetzt?"≈":"")', "", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht - Anker veraltet"

    z2 = index_html.replace("dauerGeschaetzt:(!!c.dauerGeschaetzt&&_dauerOv[c.scheinId]==null)",
                            "dauerGeschaetzt:!!c.dauerGeschaetzt", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht - Anker veraltet"
    assert "_dauerOv[c.scheinId]==null)" not in z2.split("dauerGeschaetzt:")[1][:60], (
        "Umkehrprobe: der Dauer-Griff-Riegel wuerde nicht anschlagen"
    )
