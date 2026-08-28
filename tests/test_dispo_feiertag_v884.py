# -*- coding: utf-8 -*-
"""v3.9.884 - Die Dispo plante an Feiertagen einen vollen Arbeitstag.

BEFUND: `_dispoBuildInput` baute die Tagesnorm aus genau einer Frage - Freitag
oder nicht:

    normMin: i===4 ? 270 : 510

`_isATFeiertag` existiert seit langem und wird an ACHT anderen Stellen benutzt
(Urlaubsberechnung, Zeiterfassung, Zuschlaege, Wochen- und Tages-Stundenbestaetigung)
- nur hier nicht. Ergebnis: am 26.10., 1.5., an Fronleichnam und am 8.12. verteilte
die Dispo 8,5 Stunden Arbeit auf einen Tag, an dem niemand arbeitet, und das Buero
raeumte die Woche hinterher von Hand auf.

DAZU KOMMT: bis v3.9.875 kannte `_isATFeiertag` den oesterreichischen
NATIONALFEIERTAG (26.10.) ueberhaupt nicht - die Fixliste sprang von 15.8. auf 1.11.
Selbst ein Aufruf haette dort also nichts genuetzt. Beide Haelften des Fehlers sind
jetzt behoben; dieser Riegel prueft die zweite und laesst sich von der ersten nicht
taeuschen (er prueft den 26.10. ausdruecklich mit).

STILLE NEBENWIRKUNG, die erwuenscht ist: der Wochen-Auslastungswert war strukturell
zu niedrig, weil die Feiertagsnorm im Nenner mitlief. Eine Woche mit Feiertag sah
dadurch leerer aus, als sie war.

FIX: ein Feiertag verhaelt sich wie ein voll abwesender Tag - normMin 0, also keine
Kapazitaet, also wird dort nichts eingeplant. Kein neuer Rechenweg, keine zweite
Feiertagsliste: derselbe Helfer wie ueberall.
"""
import json
import re

from conftest import run_node_snippet, _extract_fn


def _tagesnorm_zeile(index_html):
    m = re.search(r"var wtage=TAGE\.map\(function\(k,i\)\{.*?\}\);", index_html, re.S)
    assert m, "Die Tagesraster-Zeile der Dispo ist nicht mehr auffindbar."
    return m.group(0)


# -- Der Aufruf existiert ueberhaupt ----------------------------------------

def test_dispo_fragt_die_feiertage(index_html):
    zeile = _tagesnorm_zeile(index_html)
    assert "_isATFeiertag(x)" in zeile, (
        "Die Dispo-Tagesnorm ruft _isATFeiertag nicht - dann plant sie an "
        "Feiertagen wieder einen vollen Arbeitstag:\n" + zeile[:400]
    )


def test_feiertag_ergibt_keine_kapazitaet(index_html):
    zeile = _tagesnorm_zeile(index_html)
    assert "normMin:_fei?0:(i===4?270:510)" in zeile, (
        "Ein Feiertag fuehrt nicht mehr zu normMin 0 - damit bliebe Kapazitaet "
        "uebrig und die Dispo verplant sie:\n" + zeile[:400]
    )


def test_der_freitag_bleibt_ein_halber_tag(index_html):
    """Gegenprobe: der Feiertags-Fix darf die bestehende Freitagsregel nicht
    verschlucken. Mo-Do 510 min, Fr 270 min - das war vorher richtig."""
    zeile = _tagesnorm_zeile(index_html)
    assert "i===4?270:510" in zeile, (
        "Die Freitagsregel (270 statt 510 Minuten) ist verlorengegangen."
    )


def test_der_tag_traegt_seinen_grund(index_html):
    """Ein Tag mit 0 Kapazitaet muss erkennen lassen, WARUM - sonst sieht das
    Buero eine leere Zeile und haelt sie fuer einen Fehler."""
    zeile = _tagesnorm_zeile(index_html)
    assert "feiertag:_fei" in zeile, (
        "Der Tag traegt kein Feiertags-Kennzeichen - dann ist eine 0-Kapazitaet "
        "nicht von einer Stoerung zu unterscheiden."
    )


def test_kein_absturz_wenn_der_helfer_fehlt(index_html):
    """Der Aufruf ist eingepackt: die Dispo ist eine Rechenkette, ein Wurf hier
    wuerde die GANZE Planung leer lassen - schlimmer als ein falscher Feiertag."""
    zeile = _tagesnorm_zeile(index_html)
    assert "try{_fei=_isATFeiertag(x);}catch" in zeile, (
        "Der Feiertags-Aufruf ist nicht abgesichert. Wirft er, faellt die "
        "komplette Dispo-Berechnung aus."
    )


# -- Und die Feiertage selbst stimmen (Verbindung zu v3.9.875) --------------

def test_die_feiertagsliste_kennt_den_nationalfeiertag(node_exe, index_html):
    """Ohne diesen Riegel koennte der Aufruf oben korrekt sein und trotzdem am
    26.10. nichts bewirken - genau der Zustand vor v3.9.875."""
    easter = _extract_fn(index_html, "_easterSunday")
    feiertag = _extract_fn(index_html, "_isATFeiertag")
    assert easter and feiertag, "Feiertags-Helfer nicht gefunden"
    snippet = easter + "\n" + feiertag + "\n" + (
        "const out=[[2026,9,26],[2026,4,1],[2026,11,8],[2026,9,27]]"
        ".map(a=>_isATFeiertag(new Date(a[0],a[1],a[2])));"
        "process.stdout.write(JSON.stringify(out));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res[:3] == [True, True, True], (
        "26.10. (Nationalfeiertag), 1.5. oder 8.12. werden nicht erkannt: %s" % res
    )
    assert res[3] is False, "Der 27.10. ist ein Arbeitstag: %s" % res


# -- Umkehrprobe -------------------------------------------------------------

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    zurueck = index_html.replace(
        "normMin:_fei?0:(i===4?270:510),feiertag:_fei,",
        "normMin:i===4?270:510,", 1)
    assert zurueck != index_html, "Rueckbau griff nicht - Anker veraltet"
    zeile = _tagesnorm_zeile(zurueck)
    assert "normMin:_fei?0:" not in zeile, (
        "Umkehrprobe: der Kapazitaets-Riegel wuerde nicht anschlagen"
    )
    assert "feiertag:_fei" not in zeile, (
        "Umkehrprobe: der Grund-Riegel wuerde nicht anschlagen"
    )
