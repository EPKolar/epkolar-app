# -*- coding: utf-8 -*-
"""v3.9.901 Befund 3/4/5 - drei Zahlen, die neben einer zweiten Zahl standen und
etwas anderes meinten, als daneben behauptet wurde.

BEFUND 3 - ChefDashboard, Karte "Abwesenheiten", EINE _metricRow (L24425-24429):

    'Abwesend diese Woche'    absThisWeek   L24150  dt>=_weekStart && dt<=_td
    'Abwesend naechste Woche' nextWeekAbs   L24105  dt>=_nextMonStart && dt<_nextMonEnd

    Die linke Zahl endet HEUTE, die rechte umfasst eine (fast) volle Woche.
    Am Montag ist das linke Fenster EIN TAG lang. Gemessen (Mo 24.08.2026,
    Europe/Vienna, ein Monteur mit Urlaub Mi-Fr dieser Woche, einer am Mo der
    naechsten): "Abwesend diese Woche 0" neben "Abwesend naechste Woche 1".
    Der Chef plant den Mittwoch mit voller Mannschaft.

    _weekStart selbst wird NICHT angefasst: daran haengen ueber _weekEnd/_kapSel
    die komplette Auslastungskarte (kapSoll/kapIst/kapPct/kapList, L24208-24219),
    also genau die Rechnung, die v3.9.898 gerade als die starke festgeschrieben
    hat. Der Fix sitzt allein in der oberen Grenze von absThisWeek.

BEFUND 4 - "Mein Profil", Karte "Projektstunden", vier Kacheln in EINEM Grid
    (L9859-9863):

    'Stunden gesamt' totalH        L9837  nur das LAUFENDE Jahr (startsWith(_yrPrefix))
    'Ø Woche'        totalH / 52   L9838  als waere das Jahr vorbei

    Ende August sind das die Stunden aus 35 Wochen, verteilt auf 52.
    Gemessen an Mo-Fr 7,7 h ab 1.1.2026 bis 28.08.: "Ø Woche 25,6 h" direkt
    neben "Diese Woche 38,5 h".

    Nebenbefund derselben Zeile: das Wochenfenster wurde mit
    `_ymd2=d=>d.toISOString().slice(0,10)` gebaut, waehrend die uebrige App
    _ymd (lokal) benutzt. In Wien ist Montag 00:00 lokal in UTC der Sonntag
    davor - das Fenster war Sonntag..Samstag statt Montag..Sonntag. Gemessen
    (Mi 26.08.2026, ein Sonntagseinsatz am 23.08. und einer am 30.08.):
        IST : letzte Woche 0 h,  diese Woche 6 h
        SOLL: letzte Woche 6 h,  diese Woche 9 h

BEFUND 5 - zwei Zahlen mit demselben Wortlaut, eine gefiltert:
    Flotte:   Kopfzeile L27335 zaehlt fleet (ganzer Fuhrpark), die Klappgruppe
              L27347 zaehlt fleetView (suchgefiltert) - beide sagen "ohne Tracker".
    Material: matQuery war EIN State fuer die Artikelsuche im Warenkorb (L19959)
              UND die Bestellsuche im Lager (L20195).
"""
import json
import os
import re
import subprocess

from conftest import EPK_TEST_TIMEOUT
from _hilfen import nur_code, fundstellen


def _zeile_mit(index_html, nadel):
    """KOMMENTARBLIND. Beim ersten Lauf sind ZWEI dieser Riegel an meinen EIGENEN
    Erklaerkommentaren angeschlagen - der Kommentar zum Fix nennt den alten
    Ausdruck, den er erklaert. Im Repo ist das der zwoelfte Fall dieser Art;
    deshalb geht jede Suche hier durch nur_code()."""
    treffer = [z for z in nur_code(index_html).splitlines() if nadel in z]
    assert len(treffer) == 1, (
        "Erwartet genau eine Codezeile mit %r, gefunden %d.%s"
        % (nadel, len(treffer), chr(10) + fundstellen(nur_code(index_html), nadel)))
    return treffer[0]


def _zeile_regex(index_html, muster):
    treffer = [z for z in nur_code(index_html).splitlines() if re.match(muster, z)]
    assert len(treffer) == 1, (
        "Erwartet genau eine Codezeile fuer %r, gefunden %d" % (muster, len(treffer)))
    return treffer[0]


def _node(node_exe, tmp_path, name, js):
    p = tmp_path / name
    p.write_text(js, encoding="utf-8")
    env = dict(os.environ, TZ="Europe/Vienna")
    r = subprocess.run([node_exe, str(p)], capture_output=True, text=True,
                       timeout=EPK_TEST_TIMEOUT, env=env)
    assert r.returncode == 0, "Node brach ab:" + chr(10) + r.stderr
    assert r.stdout.strip(), "Node lieferte NICHTS - ein leerer Lauf ist kein gruener Lauf."
    return json.loads(r.stdout.strip().splitlines()[-1])


def _uhr(iso):
    return ("const R=Date;global.Date=class extends R{constructor(...a)"
            "{if(a.length===0)super(" + json.dumps(iso) + ");else super(...a);}"
            "static now(){return new R(" + json.dumps(iso) + ").getTime();}};")


# == BEFUND 3 ===============================================================

def test_abwesend_beide_fenster_volle_woche(index_html, node_exe, tmp_path):
    """Am Montag muessen beide Zahlen die ganze Woche sehen.

    UMKEHRPROBE: `dt<=_weekSun` zurueck auf `dt<=_td` -> diese=0 neben
    naechste=1, der Test faellt. Am Stand 808e58f ist er ROT (nachgemessen).
    """
    js = chr(10).join([
        _uhr("2026-08-24T08:00:00+02:00"),   # MONTAG - der teuerste Tag
        _zeile_regex(index_html, r"^const _ymd=d=>"),
        _zeile_mit(index_html, "const _td=_ymd(new Date());"),
        _zeile_mit(index_html, "const _weekStart=(function(){"),
        _zeile_mit(index_html, "const _weekSun=(function(){"),
        _zeile_mit(index_html, "const _nextMonStart=(function(){"),
        _zeile_mit(index_html, "const _nextMonEnd=(function(){"),
        "const abs={'Huber_2026-08-26':{type:'urlaub',date:'2026-08-26',status:'genehmigt'},"
        "'Huber_2026-08-27':{type:'urlaub',date:'2026-08-27',status:'genehmigt'},"
        "'Huber_2026-08-28':{type:'urlaub',date:'2026-08-28',status:'genehmigt'},"
        "'Bauer_2026-08-31':{type:'urlaub',date:'2026-08-31',status:'genehmigt'}};",
        _zeile_mit(index_html, "const absThisWeek=(function(){"),
        "const nx=(function(){const h=[];Object.keys(abs).forEach(k=>{const e=abs[k];"
        "const dt=((e.date||'')+'').slice(0,10);"
        + _zeile_mit(index_html, "if(dt>=_nextMonStart&&dt<_nextMonEnd){").strip()
        + "h.push(k);}});return h.length;})();",
        "console.log(JSON.stringify({diese:absThisWeek,naechste:nx,"
        "von:_weekStart,bis:_weekSun}));",
    ])
    m = _node(node_exe, tmp_path, "abwesend.js", js)
    assert m["diese"] == 1, (
        "Am Montag sieht 'Abwesend diese Woche' den Urlaub Mi-Fr nicht: " + repr(m))
    assert m["naechste"] == 1, repr(m)


def test_abwesend_fenster_ist_ganze_woche(index_html, node_exe, tmp_path):
    """Das linke Fenster muss an JEDEM Wochentag Mo..So abdecken.

    UMKEHRPROBE: obere Grenze wieder an _td haengen -> das Fenster ist an
    sechs von sieben Tagen kuerzer als die Woche.
    """
    for tag in ["2026-08-24", "2026-08-26", "2026-08-29", "2026-08-30"]:
        js = chr(10).join([
            _uhr(tag + "T08:00:00+02:00"),
            _zeile_regex(index_html, r"^const _ymd=d=>"),
            _zeile_mit(index_html, "const _weekStart=(function(){"),
            _zeile_mit(index_html, "const _weekSun=(function(){"),
            "console.log(JSON.stringify({von:_weekStart,bis:_weekSun}));",
        ])
        m = _node(node_exe, tmp_path, "fenster.js", js)
        assert (m["von"], m["bis"]) == ("2026-08-24", "2026-08-30"), (
            "Am %s ist das Fenster %s..%s statt Mo 24.08...So 30.08." % (tag, m["von"], m["bis"]))


# == BEFUND 4 ===============================================================

def test_wochenschnitt_teilt_durch_verstrichene_wochen(index_html, node_exe, tmp_path):
    """"Ø Woche" darf nicht durch 52 teilen, solange totalH nur das laufende
    Jahr deckt - sonst steht die Kachel neben "Diese Woche" und widerspricht ihr.

    UMKEHRPROBE: `/_wkVerstrichen` zurueck auf `/52` -> 25,6 statt 39,1, rot.
    """
    js = chr(10).join([
        _uhr("2026-08-28T10:00:00+02:00"),
        "const entries=[];",
        "for(let d=new Date(2026,0,1); d<=new Date(2026,7,28); d.setDate(d.getDate()+1)){"
        "const w=d.getDay(); if(w>=1&&w<=5) entries.push({worker:'M1',"
        "datum:d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'"
        "+String(d.getDate()).padStart(2,'0'),hours:7.7});}",
        "const _myMid='M1';",
        # TIME_* aus index.html, weil _wkVerstrichen mit TIME_DAY rechnet
        _zeile_regex(index_html, r"^const TIME_SECOND="),
        _zeile_regex(index_html, r"^const TIME_MINUTE="),
        _zeile_regex(index_html, r"^const TIME_HOUR="),
        _zeile_regex(index_html, r"^const TIME_DAY="),
        _zeile_mit(index_html, "const _curYr=new Date().getFullYear();"),
        _zeile_mit(index_html, "const _yrPrefix=String(_curYr);"),
        _zeile_mit(index_html, "const _zeitStats=(()=>{"),
        _zeile_mit(index_html, "const _wkVerstrichen=(function(){"),
        _zeile_mit(index_html, "const _wochenSchnitt=Math.round("),
        "console.log(JSON.stringify({schnitt:_wochenSchnitt,wochen:_wkVerstrichen,"
        "diese:Math.round(_zeitStats.thisWeekH*10)/10}));",
    ])
    m = _node(node_exe, tmp_path, "schnitt.js", js)
    assert m["wochen"] == 35, "Verstrichene Wochen am 28.08.2026: " + repr(m)
    assert 36.0 <= m["schnitt"] <= 40.0, (
        "Der Wochenschnitt muss neben 'Diese Woche' (38,5 h) plausibel stehen, "
        "ist aber " + repr(m))


def test_wochenfenster_ist_lokal(index_html, node_exe, tmp_path):
    """Ein Sonntagseinsatz muss in SEINE Woche fallen, nicht in die naechste.

    UMKEHRPROBE: _ymd2 zurueck auf toISOString -> letzte Woche 0 h, diese
    Woche 6 h (der Sonntag der VORwoche), der Test faellt.
    """
    js = chr(10).join([
        _uhr("2026-08-26T12:00:00+02:00"),   # Mittwoch, Woche Mo 24.08 - So 30.08
        "const entries=[{worker:'M1',datum:'2026-08-23',hours:6},"
        "{worker:'M1',datum:'2026-08-30',hours:9}];",
        "const _myMid='M1';const _yrPrefix='2026';",
        _zeile_mit(index_html, "const _zeitStats=(()=>{"),
        "console.log(JSON.stringify(_zeitStats));",
    ])
    m = _node(node_exe, tmp_path, "woche.js", js)
    assert m["lastWeekH"] == 6, "So 23.08. gehoert in die VORwoche: " + repr(m)
    assert m["thisWeekH"] == 9, "So 30.08. gehoert in DIESE Woche: " + repr(m)
    assert "toISOString" not in _zeile_mit(index_html, "const _zeitStats=(()=>{"), \
        "Das Wochenfenster rechnet wieder in UTC."


# == BEFUND 5 ===============================================================

def test_lagersuche_hat_eigenen_state(index_html):
    """Warenkorb-Artikelsuche und Lager-Bestellsuche duerfen sich keinen State
    teilen - sonst faerbt eine Eingabe im einen Tab die Liste im anderen.

    UMKEHRPROBE: das Lager-Suchfeld zurueck auf matQuery -> rot.
    """
    code = nur_code(index_html)
    feld = _zeile_mit(index_html, 'placeholder: "\U0001f50d Bestellungen suchen')
    assert "matQueryLg" in feld and "value: matQuery," not in feld, (
        "Das Lager-Suchfeld haengt weiter am Warenkorb-State:" + chr(10) + feld)
    assert "return matTokensLg.every(" in code, \
        "Der Lager-Filter liest weiter die Warenkorb-Tokens."
    assert "const matTokensLg=" in code, "Der eigene Tokenizer fehlt."


def test_zwei_zahlen_zwei_worte(index_html):
    """Kopfzeile (ganzer Fuhrpark) und Klappgruppe (suchgefiltert) sagten beide
    nur "ohne Tracker". Bei aktiver Suche muss der Unterschied im Text stehen.

    UMKEHRPROBE: die Zusaetze entfernen -> rot.
    """
    kopf = _zeile_mit(index_html, "' aktiv · '+_nInakt+' inaktiv")
    # NICHT ueber "+' ohne Tracker')" suchen: dieselbe Zeichenfolge steckt auch
    # in der Kopfzeile ("...ohne Tracker'):''") - genau die Verwechslung, die
    # dieser Riegel bewachen soll, waere im Riegel selbst passiert.
    grp = _zeile_mit(index_html, "(ohneOpen?'")
    assert "_fq?" in kopf, (
        "Die Kopfzeile sagt bei aktiver Suche nicht, dass sie den ganzen "
        "Fuhrpark zaehlt:" + chr(10) + kopf)
    assert "_fq?(" in grp and "' von '" in grp, (
        "Die Klappgruppe nennt ihre gefilterte Zahl ohne Bezug:" + chr(10) + grp)


def test_lager_leermeldung_nennt_die_suche(index_html):
    """"Keine offenen Anforderungen." neben einem Chip, der "7" traegt, ist eine
    Falschaussage - die 7 sind da, nur ausgeblendet.

    UMKEHRPROBE: den matTokensLg-Zweig aus der Leermeldung nehmen -> rot.
    """
    zeile = _zeile_mit(index_html, '"Keine offenen Anforderungen."')
    assert "matTokensLg.length>0?" in zeile, (
        "Die Leermeldung unterscheidet nicht zwischen leer und weggefiltert:"
        + chr(10) + zeile)
