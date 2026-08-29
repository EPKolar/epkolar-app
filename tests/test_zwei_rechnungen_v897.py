# -*- coding: utf-8 -*-
"""v3.9.897 - Vier Groessen, die an zwei Stellen verschieden gerechnet wurden.

Alle vier stammen aus einem eigenen Durchgang genau nach dieser Fehlerklasse
ueber die zwoelf Ansichten, die in dieser Sitzung noch nicht abgesucht waren.
Das Erkennungsmerkmal ist immer dasselbe: **zwei Zahlen auf einem Bildschirm,
die sich widersprechen - und jemand entscheidet nach einer davon.**

────────────────────────────────────────────────────────────────────────────
1 - Das Fahrtenbuch-Fenster war 32 TAGE lang, nicht ein Monat  (lohnrelevant)
────────────────────────────────────────────────────────────────────────────
    const from = month+'-01';
    const to   = _ymd(new Date(new Date(from).getTime() + 32*TIME_DAY));

Fuer Februar 2026 heisst das: geladen wird bis zum **4. Maerz**. Die Fahrten
vom 1. bis 4. Maerz standen damit unter Februar UND unter Maerz - in der
Bildschirmsumme (`totalKm`, `totalKraftstoff`) wie im Excel-Export.

Kilometergeld und Sachbezug wurden fuer dieselben Fahrten zweimal ausgewiesen.
Kein Monat war verschont, nachgemessen:

    Jaenner  bis 02.02. statt 01.02.      April     bis 03.05. statt 01.05.
    Februar  bis 05.03. statt 01.03.      Dezember  bis 02.01. statt 01.01.
    Februar 2028 (Schaltjahr) bis 04.03.

Jetzt der erste des Folgemonats. `new Date(y, m, 1)` zaehlt Monate ab null, `m`
ist also bereits der Folgemonat, und der Jahreswechsel rollt von selbst.

────────────────────────────────────────────────────────────────────────────
2 - Der Urlaubsantrag zeigte Kalendertage, gebucht werden Werktage
────────────────────────────────────────────────────────────────────────────
Die Antragskarte rechnete `(bis - von)/TAG + 1`. Das Genehmigen materialisiert
die Abwesenheit dagegen ueber `_stdVonTagBrk` - Sa/So und AT-Feiertage zaehlen
nicht. Gemessen am echten Kalender:

    Mo 21.12. - So 27.12.     Karte "7 Tag(e)"   gebucht 4
    Sa 24.10. - So 25.10.     Karte "2 Tag(e)"   gebucht 0
    Mo 26.10. (Nationalf.)    Karte "1 Tag(e)"   gebucht 0

Der Genehmiger sah eine andere Zahl, als sein eigener Klick vom Urlaubskonto
abzog - und beide standen auf demselben Schirm. Gezaehlt wird jetzt mit
derselben Funktion, die auch bucht.

────────────────────────────────────────────────────────────────────────────
3 - Die Tankkosten-Summe zaehlte stillgelegte Fahrzeuge, die Zahl daneben nicht
────────────────────────────────────────────────────────────────────────────
In EINER Kachel: `value` = aktive Fahrzeuge (der Titel sagt es sogar),
`sub` = Tankkosten ueber ALLE. Ein ausgemusterter Sprinter mit 4.200 EUR
Tank-Log stand in der Summe, aber nicht im Nenner - Kosten je Fahrzeug 3.680
statt 2.840 EUR, und das Diagramm daneben zeigte fuer ihn keinen Balken.

Das war die einzige Fahrzeug-Summe der Datei ohne diesen Filter; neun andere
Stellen haben ihn. Grundlage fuer Leasing- und Ersatzentscheidungen.

────────────────────────────────────────────────────────────────────────────
4 - Die Krankenstandsliste liess den Alt-Typ "krank" fallen, die Kopfzeile nicht
────────────────────────────────────────────────────────────────────────────
Kopfzeile ueber `_yearStK` (normalisiert `krank` auf `krankenstand`), Liste im
selben `<details>` ueber `_krankByMA` (nur `krankenstand`). Ein Altdatensatz
ergab Kopf "4 Tage" und drei Zeilen.

Das Buero-Portal hat genau diese Reparatur schon in v3.9.668 bekommen
(`_krankRows`, mit Kommentar). AbsView wurde damals nicht mitgezogen - eine
Reparatur an einer von zwei Stellen ist keine.
"""
from _hilfen import nur_code


# ══ 1 - Fahrtenbuch-Monatsfenster ═══════════════════════════════════════════

def test_das_fenster_endet_am_ersten_des_folgemonats(index_html):
    assert "const to=_ymd(new Date(_fbJ,_fbM,1));" in index_html, (
        "Das Fahrtenbuch-Fenster endet nicht mehr am Monatsersten - dann "
        "stehen Grenztage in ZWEI Monaten und das Kilometergeld wird doppelt "
        "ausgewiesen."
    )


def test_die_32_tage_sind_weg(index_html):
    """KOMMENTARBLIND gemessen. Beim ersten Versuch schlug dieser Riegel an -
    und zwar an MEINEM EIGENEN Erklaerkommentar, der den ausgebauten Ausdruck
    natuerlich nennt. Elfte Wiederholung dieser Falle in diesem Repo; genau
    dafuer ist `tests/_hilfen.py` heute Vormittag entstanden."""
    assert "32*TIME_DAY" not in nur_code(index_html), (
        "Das 32-Tage-Fenster ist zurueck. Februar laedt damit bis zum 4. Maerz."
    )


def test_die_grenze_bleibt_halboffen(index_html):
    """Der Erste des Folgemonats darf NICHT mehr dazugehoeren - sonst waere
    genau ein Tag doppelt, statt bisher bis zu vier."""
    i = index_html.find("const to=_ymd(new Date(_fbJ,_fbM,1));")
    assert i != -1
    block = index_html[i:i + 400]
    assert "&datum=lt.'+to" in block, (
        "Die obere Grenze ist nicht mehr halboffen (`lt.`) - mit `lte.` waere "
        "der Monatserste in beiden Monaten:" + chr(10) + block[:260]
    )


def test_das_jahr_wird_aus_dem_monat_gelesen(index_html):
    """Gegenprobe gegen den naheliegenden Fehler: `new Date(from)` waere
    UTC-basiert, `_ymd` liest lokal - in Wien haette das den Monatsersten um
    einen Tag verschoben."""
    assert ("const _fbJ=parseInt(month.slice(0,4),10), "
            "_fbM=parseInt(month.slice(5,7),10);") in index_html, (
        "Jahr und Monat werden nicht mehr direkt aus der Monatsangabe gelesen."
    )


# ══ 2 - Werktage im Urlaubsantrag ═══════════════════════════════════════════

def test_es_gibt_eine_werktage_zaehlung(index_html):
    assert "const _antragWerktage=(von,bis)=>{" in index_html, (
        "Die Werktage-Zaehlung fehlt - dann zeigt die Antragskarte wieder "
        "Kalendertage, waehrend das Genehmigen Werktage bucht."
    )


def test_sie_benutzt_dieselbe_funktion_wie_das_buchen(index_html):
    """DER KERN: eine Groesse, EINE Rechnung. Eine eigene Wochenend-/
    Feiertagslogik neben der buchenden waere genau der Fehler noch einmal."""
    i = index_html.find("const _antragWerktage=(von,bis)=>{")
    assert i != -1
    fn = index_html[i:index_html.find("};", i)]
    assert "_stdVonTagBrk(d)>0" in fn, (
        "Die Zaehlung prueft nicht ueber _stdVonTagBrk - dann gibt es zwei "
        "Vorstellungen davon, welcher Tag ein Werktag ist:" + chr(10) + fn[:260]
    )
    for eigen in ("getDay()", "_isATFeiertag"):
        assert eigen not in fn, (
            "Die Zaehlung baut die Werktagsregel mit '%s' selbst nach, statt "
            "die buchende Funktion zu fragen." % eigen
        )


def test_die_karte_zeigt_werktage(index_html):
    assert "+_antragWerktage(a.von,a.bis)+' Werktag(e)')" in index_html, (
        "Die Antragskarte zeigt die Werktage nicht - der Genehmiger sieht "
        "wieder eine andere Zahl, als sein Klick abbucht."
    )


def test_die_alte_kalendertag_rechnung_ist_weg(index_html):
    assert "(new Date(a.bis)-new Date(a.von))/TIME_DAY" not in index_html, (
        "Die Kalendertag-Rechnung steht wieder in der Antragskarte."
    )


# ══ 3 - Tankkosten ══════════════════════════════════════════════════════════

def test_die_tankkosten_lassen_stillgelegte_aus(index_html):
    i = index_html.find("const totalTankKosten=")
    assert i != -1, "totalTankKosten nicht gefunden"
    block = index_html[i:i + 260]
    assert 'filter(f=>f.status!=="stillgelegt")' in block, (
        "Die Tankkosten-Summe zaehlt wieder stillgelegte Fahrzeuge mit, "
        "waehrend die Fahrzeugzahl in derselben Kachel sie auslaesst:"
        + chr(10) + block[:200]
    )


def test_die_kachel_bleibt_auf_aktiven_fahrzeugen(index_html):
    """Gegenprobe: der Nenner war schon richtig und darf sich NICHT aendern -
    sonst waere die Kachel wieder in sich widerspruechlich, nur andersherum."""
    assert ('value: (fahrzeuge||[]).filter(f=>f.status!=="stillgelegt").length, '
            'sub: "€"+Math.round(totalTankKosten)') in index_html, (
        "Zaehler und Summe der Fahrzeug-Kachel stehen nicht mehr beisammen "
        "oder rechnen wieder verschieden."
    )


def test_das_diagramm_daneben_bleibt_unveraendert(index_html):
    """Das Balkendiagramm filterte von Anfang an richtig. Wenn die Summe jetzt
    dieselbe Menge nimmt, muessen beide dieselbe Grundmenge haben."""
    assert ('(fahrzeuge||[]).filter(f=>f.status!=="stillgelegt")'
            '.map(f=>({') in index_html, (
        "Das Tank-Diagramm hat seinen Filter verloren."
    )


# ══ 4 - Alt-Typ "krank" ═════════════════════════════════════════════════════

def test_die_liste_kennt_den_alten_typ(index_html):
    assert ('if(v&&(v.type==="krankenstand"||v.type==="krank")'
            '&&key.indexOf(m+"_")===0)') in index_html, (
        "Die Krankenstandsliste laesst den Alt-Typ 'krank' wieder fallen - "
        "Kopfzeile und Liste stehen dann mit verschiedenen Zahlen auf einem "
        "Schirm."
    )


def test_das_buero_portal_bleibt_wie_es_war(index_html):
    """Gegenprobe: dort war es SCHON richtig (v3.9.668). Ziel war, die zweite
    Stelle nachzuziehen - nicht, die erste anzufassen."""
    assert ('if((v.type!=="krankenstand"&&v.type!=="krank")'
            '||!key.startsWith(m.n+"_"))return;') in index_html, (
        "Der Krankenstands-Pfad des Buero-Portals hat sich veraendert."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace("const to=_ymd(new Date(_fbJ,_fbM,1));",
                            "const to=_ymd(new Date(new Date(from).getTime()+32*TIME_DAY));", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "const to=_ymd(new Date(_fbJ,_fbM,1));" not in z1, (
        "Umkehrprobe: der Fahrtenbuch-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("+_antragWerktage(a.von,a.bis)+' Werktag(e)')",
                            "+'7 Tag(e)')", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "+_antragWerktage(a.von,a.bis)+' Werktag(e)')" not in z2, (
        "Umkehrprobe: der Werktage-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace(
        'const totalTankKosten=_react.useMemo.call(void 0, ()=>(fahrzeuge||[])'
        '.filter(f=>f.status!=="stillgelegt")',
        'const totalTankKosten=_react.useMemo.call(void 0, ()=>(fahrzeuge||[])', 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    i = z3.find("const totalTankKosten=")
    assert 'filter(f=>f.status!=="stillgelegt")' not in z3[i:i + 260], (
        "Umkehrprobe: der Tankkosten-Riegel wuerde nicht anschlagen"
    )

    z4 = index_html.replace(
        'if(v&&(v.type==="krankenstand"||v.type==="krank")&&key.indexOf(m+"_")===0)',
        'if(v&&v.type==="krankenstand"&&key.indexOf(m+"_")===0)', 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    assert ('if(v&&(v.type==="krankenstand"||v.type==="krank")'
            '&&key.indexOf(m+"_")===0)') not in z4, (
        "Umkehrprobe: der Krankenstands-Riegel wuerde nicht anschlagen"
    )
