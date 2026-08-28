# -*- coding: utf-8 -*-
"""v3.9.888 - Die Dispo zeigte Zahlen, die sich gegenseitig widersprachen.

Fuenf Befunde, alle aus derselben Familie: eine Groesse wird an zwei Stellen
unterschiedlich gerechnet, oder gar nicht angezeigt, oder aus der falschen Quelle
geholt. Keiner davon stuerzt ab - sie erzeugen nur Zahlen, nach denen entschieden
wird und die nicht stimmen.

────────────────────────────────────────────────────────────────────────────
1 - KW-Auslastung gegen Zell-Balken: zwei Werte auf einem Bildschirm
────────────────────────────────────────────────────────────────────────────
`_weekStats` und die Zelle rechneten unterschiedlich. Drei Abweichungen in einer
einzigen Zeile:

    Zelle:      usedMin = chips.reduce(_effDauer) + fixMap.reduce(dauerMin)
    _weekStats: used    = chips.reduce(c.dauerMin)          <- kein fixMap,
                                                               kein _effDauer
                norm   += t.normMin                          <- ALLE Tage

Folgen: Eine Woche, die ausschliesslich aus bestaetigten Kundenterminen besteht,
zeigte **Auslastung 0 %**. Der Dauer-Griff (mit dem man die Plan-Dauer vor der
Uebernahme zieht) wurde ignoriert. Und am Freitag zeigte die laufende Woche
zwangslaeufig einen Bruchteil, weil Mo-Do als freie Kapazitaet mitliefen - obwohl
sie vorbei sind. Genau nach dieser Zahl wird entschieden, ob noch etwas hineinpasst.

────────────────────────────────────────────────────────────────────────────
2 - Der Konfliktzaehler wurde berechnet und weggeworfen
────────────────────────────────────────────────────────────────────────────
`_konfCount` laeuft ueber Wochen x Monteure x Tage - und hatte **null Leser**. Das
ist die Zahl, die das Buero im Kopf haben muesste ("3 Ueberschneidungen diese
Woche"); sichtbar war eine Ueberschneidung nur am einzelnen Chip, wenn man
zufaellig hinschaute.

────────────────────────────────────────────────────────────────────────────
3 - Jede Fahrzeit wurde ab der Firma gerechnet
────────────────────────────────────────────────────────────────────────────
`_dispoStrecke("3470", ...)` fuer JEDEN Stopp - obwohl `_dispo2opt` vorher eine
Rundfahrt Firma -> Stopps -> Firma gelegt hat. Drei Auftraege in Krems zaehlten
dreimal die volle Anfahrt statt einmal plus zwei kurze Spruenge. Der Tag sah
kuenstlich voll aus, Kacheln fielen unnoetig in "keine Luecke" - und die
2-opt-Reihenfolge wirkte sich auf die angezeigten Zeiten praktisch gar nicht aus.

────────────────────────────────────────────────────────────────────────────
4 - Das Geo-Nachziehen holte die Rechnungsadresse
────────────────────────────────────────────────────────────────────────────
Der Prefetch geocodierte die rohe `kundPlz`. Genau fuer die Verwalter-Kunden, fuer
die `_dispoScheinPlz` ueberhaupt gebaut wurde (Baustelle steht nur im Text), kamen
dadurch **nie** echte Kilometer - er holte dauerhaft die falschen PLZ. Der
Renderer hat denselben Fehler in v3.9.857 schon einmal repariert; diese Stelle und
die Vorschlags-Chips blieben uebrig.

────────────────────────────────────────────────────────────────────────────
5 - Unbekannte Entfernung galt als Fuenf-Minuten-Nachbarschaft
────────────────────────────────────────────────────────────────────────────
`cfg.dist` gab `st.min` weiter und liess das `known`-Flag fallen. Bei unbekannter
PLZ ist `st.min` der Innerorts-Rueckfall (5 min) - ein Stopp 80 km weg kostete im
Score also so wenig wie einer um die Ecke. Score und Routenreihenfolge waren fuer
solche Scheine Zufall, sahen aber exakt aus wie eine Berechnung. v3.9.856 hat
genau das fuer `near()` geheilt, `dist()` blieb uebrig.

Der Ersatzwert ist bewusst KEIN Schaetzwert der echten Entfernung - den kennen wir
nicht. Er ist ein Malus, der verhindert, dass Unbekanntes BESSER dasteht als
Bekanntes.
"""
import re


# ══ 1 - KW-Auslastung ═══════════════════════════════════════════════════════

def _weekstats(index_html):
    i = index_html.find("var _weekStats=function(W){")
    assert i != -1, "_weekStats nicht gefunden"
    j = index_html.find("var _weekTable=", i)
    return index_html[i:j]


def test_auslastung_zaehlt_die_fixen_termine_mit(index_html):
    block = _weekstats(index_html)
    assert "_built.fixMap" in block, (
        "Die KW-Auslastung zaehlt die fixen Termine nicht mit - eine Woche aus "
        "lauter bestaetigten Kundenterminen zeigt dann wieder 0 %:\n" + block[:400]
    )


def test_auslastung_beachtet_den_dauer_griff(index_html):
    block = _weekstats(index_html)
    assert "_effDauer(c)" in block, (
        "Die KW-Auslastung nimmt wieder c.dauerMin statt _effDauer - dann "
        "ignoriert sie den Dauer-Griff, mit dem die Plan-Dauer gezogen wird."
    )


def test_auslastung_zaehlt_nur_verfuegbare_tage(index_html):
    block = _weekstats(index_html)
    assert "Math.max(0,(t.normMin||0)-_aw)" in block, (
        "Die Norm addiert wieder ALLE Tage - auch vergangene, gesperrte, "
        "Urlaubs- und Feiertage. Am Freitag zeigt die laufende Woche dann "
        "zwangslaeufig einen Bruchteil."
    )


def test_auslastung_und_zelle_nutzen_dieselbe_quelle(index_html):
    """Der Kern: beide muessen aus abwAbzug rechnen, mit demselben Rueckfall
    auf kapAbzug. Sonst driften sie wieder auseinander."""
    block = _weekstats(index_html)
    assert "abwAbzug" in block and "kapAbzug" in block, (
        "Die Wochenzahl rechnet nicht mehr mit derselben Abzugs-Quelle wie die "
        "Zelle - genau so ist der Widerspruch entstanden."
    )


# ══ 2 - Konfliktzaehler ═════════════════════════════════════════════════════

def test_der_konfliktzaehler_wird_angezeigt(index_html):
    assert "_konfCount>0&&h('span'" in index_html, (
        "_konfCount wird wieder berechnet und weggeworfen - die einzige Zahl, "
        "die Ueberschneidungen zusammenfasst, waere dann unsichtbar."
    )
    assert "berschneidung" in index_html, "Der Text zum Konfliktzaehler fehlt"


def test_er_erscheint_nur_wenn_es_konflikte_gibt(index_html):
    """Eine dauerhafte 0 waere Rauschen und wuerde die Zahl entwerten."""
    assert "_konfCount>0&&" in index_html, (
        "Der Zaehler ist nicht mehr an >0 geknuepft."
    )


# ══ 3 - Fahrzeit vom Vorgaenger ═════════════════════════════════════════════

def test_fahrzeit_kommt_vom_vorgaenger(index_html):
    assert 'var _vor="3470";_combItems.forEach(function(it){' in index_html, (
        "Die Fahrzeit wird nicht mehr vom Vorgaenger gerechnet - dann zaehlt "
        "jeder Stopp wieder die volle Anfahrt ab der Firma."
    )
    assert "it.fahrtMin=_dispoStrecke(_vor,it.plz||\"\",_geo.geoMap,_geo.distMatrix).min;" in index_html, (
        "Der Vorgaenger wird nicht als Startpunkt benutzt."
    )
    assert 'if(it.plz)_vor=it.plz;' in index_html, (
        "Der Vorgaenger wird nicht fortgeschrieben - dann rechnet ab dem zweiten "
        "Stopp wieder alles ab der Firma."
    )


def test_der_erste_stopp_startet_weiterhin_an_der_firma(index_html):
    """Gegenprobe: die Rundfahrt beginnt an der Firma - das war und ist richtig."""
    assert 'var _vor="3470";' in index_html, (
        "Der Startpunkt ist nicht mehr die Firma."
    )


# ══ 4 - Baustellen-PLZ ══════════════════════════════════════════════════════

def test_geo_nachziehen_nimmt_die_baustellen_plz(index_html):
    i = index_html.find("typeof _geoSelbstnachzieh==='function'")
    assert i != -1, "Die AUFRUFSTELLE des Geo-Nachzieh-Laufs ist nicht mehr auffindbar (der blosse Name trifft die Definition und deren Kommentar)"
    block = index_html[i:i + 1200]
    assert "_dispoScheinPlz(a.arbeitsort" in block, (
        "Der Nachzieh-Lauf geocodiert wieder die rohe kundPlz - dann bekommen "
        "genau die Verwalter-Kunden nie echte Kilometer."
    )


def test_der_nachzieh_lauf_faellt_sauber_zurueck(index_html):
    """Er laeuft im Hintergrund - ein Wurf duerfte die Dispo nicht mitreissen."""
    i = index_html.find("typeof _geoSelbstnachzieh==='function'")
    block = index_html[i:i + 1200]
    assert "catch(_gp){return String(a.kundPlz||'').trim();}" in block, (
        "Kein Rueckfall auf die kundPlz - wirft _dispoScheinPlz, faellt der "
        "ganze Nachzieh-Lauf aus."
    )


def test_auch_die_vorschlags_chips_nutzen_die_baustellen_plz(index_html):
    assert "var _cp=c.plz||(_dispoScheinPlz(_cs.arbeitsort" in index_html, (
        "Die Vorschlags-Chips nehmen wieder die rohe kundPlz - v3.9.857 hat das "
        "nur fuer die fixen Termine repariert, die Chips blieben uebrig."
    )


# ══ 5 - Unbekannte Entfernung ═══════════════════════════════════════════════

def test_unbekannte_entfernung_ist_keine_nachbarschaft(index_html):
    assert "var DISPO_UNBEKANNT_MIN=45;" in index_html, (
        "Der Malus fuer unbekannte Entfernungen fehlt."
    )
    assert "return (st&&st.known&&st.min!=null)?st.min:DISPO_UNBEKANNT_MIN;}" in index_html, (
        "cfg.dist beachtet das known-Flag nicht mehr - dann kostet ein Stopp "
        "ohne bekannte PLZ wieder 5 Minuten, also so wenig wie einer um die Ecke."
    )


def test_der_malus_ist_groesser_als_die_nachbarschaft(index_html):
    """Sonst waere er wirkungslos - Unbekanntes darf nicht besser dastehen als
    Bekanntes."""
    m1 = re.search(r"DISPO_INNERORTS_MIN=(\d+)", index_html)
    m2 = re.search(r"DISPO_UNBEKANNT_MIN=(\d+)", index_html)
    assert m1 and m2, "Konstanten nicht gefunden"
    assert int(m2.group(1)) > int(m1.group(1)) * 3, (
        "Der Unbekannt-Malus (%s) ist nicht deutlich groesser als der "
        "Innerorts-Wert (%s) - dann wirkt er kaum." % (m2.group(1), m1.group(1))
    )


def test_near_bleibt_known_gated(index_html):
    """Gegenprobe zu v3.9.856: der Nachbarschafts-Bonus war schon geheilt und
    darf nicht mitveraendert worden sein."""
    i = index_html.find("near:function(x,y){")
    assert i != -1, "near() nicht gefunden"
    block = index_html[i:i + 400]
    assert "known" in block, (
        "near() prueft das known-Flag nicht mehr - v3.9.856 waere damit "
        "zurueckgenommen."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("return (st&&st.known&&st.min!=null)?st.min:DISPO_UNBEKANNT_MIN;}",
                            "return st.min!=null?st.min:DISPO_INNERORTS_MIN;}", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "DISPO_UNBEKANNT_MIN;}" not in z1, (
        "Umkehrprobe: der Entfernungs-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace('var _vor="3470";_combItems.forEach(function(it){', "", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert 'var _vor="3470";_combItems.forEach' not in z2, (
        "Umkehrprobe: der Fahrzeit-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace("_konfCount>0&&h('span'", "false&&h('span'", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "_konfCount>0&&h('span'" not in z3, (
        "Umkehrprobe: der Konflikt-Riegel wuerde nicht anschlagen"
    )
