# -*- coding: utf-8 -*-
"""v3.9.898 - Zwei Listen "Auslastung diese Woche" untereinander, zwei Rechnungen.

Im Chef-Portal, Tab "Personal", sind `_card('zeit',...)` und `_card('kap',...)`
Geschwister im selben Array - sie sind IMMER gleichzeitig sichtbar. Beide sagten
dasselbe und rechneten es verschieden:

    oben  "Auslastung diese Woche (Basis 38,5h)"   loadByWorker
          - keine obere Datumsgrenze (`>=_weekStart`, offen nach vorn)
          - feste 38,5 h als Nenner
          - eigene Abgrenzung: nur Backoffice/Verkauf raus, Lagerleitung,
            Geschaeftsfuehrung und AUSGETRETENE zaehlten mit

    unten "Je Monteur (Ist / Ziel %)"               kapList
          - Mo-So begrenzt
          - Nenner = _sollRange/_stdVonTagK (Fr 4,5 h, Feiertage 0)
          - _kapNonField + Ausgetretene raus

Nachgemessen an der Woche mit dem Nationalfeiertag (Mo 26.10.2026):

    _sollRange('2026-10-26','2026-11-01') = 30,0 h   (statt 38,5)
    ein Monteur mit 30,0 h:  oben 30/38,5 = 78 % gelb
                             unten 30/30  = 100 % "am Anschlag"
    Zeilenzahl:              oben 6 ("Monteure heute x/6")
                             unten 4 ("4 aktive Monteure")

Dass es EINE Aussage war und nicht zwei Absichten, steht im Code selbst: der
Kommentar zu v3.9.425 verweist auf einen Chef-Entscheid ("beide auf 70/90/100")
und hat die Ampelschwellen der beiden Widgets byte-identisch gemacht. Die
Angleichung war begonnen und bei den Schwellen stehengeblieben - Basis, Zeitraum
und Personenkreis blieben verschieden. Beide Karten haben denselben Drill-Down
('zeiterfassung') und dieselbe Akzentfarbe.

Die schwaechere Rechnung ist ersatzlos entfernt; die Kapazitaets-Karte ist die
einzige Quelle.
"""
from _hilfen import nur_code, fundstellen


# == 1 - die zweite, schwaechere Rechnung ist weg ============================

def test_keine_zweite_auslastungsrechnung(index_html):
    """KOMMENTARBLIND. Der Erklaerkommentar zum Ausbau nennt den Namen selbst -
    ein rohes `not in index_html` haette an meinem eigenen Kommentar angeschlagen."""
    code = nur_code(index_html)
    assert "loadByWorker" not in code, (
        "loadByWorker ist zurueck: die Karte 'Zeit & Personal' rechnet die "
        "Auslastung wieder gegen feste 38,5 h und ohne obere Datumsgrenze - "
        "direkt UEBER der Karte 'Auslastung / Kapazitaet', die dieselbe Aussage "
        "Mo-So begrenzt und feiertagskorrekt macht. Fundstellen: "
        + fundstellen(code, "loadByWorker"))


def test_keine_zweite_auslastungs_ueberschrift(index_html):
    code = nur_code(index_html)
    assert "Auslastung diese Woche (Basis 38,5h)" not in code, (
        "Die zweite 'Auslastung diese Woche'-Liste steht wieder ueber der "
        "Kapazitaets-Karte. Zwei Listen derselben Groesse auf einem Schirm.")


# == 2 - die verbliebene Rechnung haengt am feiertagskorrekten Soll ==========

def test_wochensoll_kommt_aus_sollrange(index_html):
    assert "const _sollPerWeek=_sollRange(_weekStart,_weekEnd);" in index_html, (
        "Das Wochen-Soll kommt nicht mehr aus _sollRange - eine feste 38,5 ist "
        "in jeder Feiertagswoche falsch.")


def test_prozent_je_monteur_haengt_am_zeitraum_soll(index_html):
    assert "const pct=_kapSel.sollPer>0?Math.round(h/_kapSel.sollPer*100):0;" in index_html, (
        "Die Prozentzahl je Monteur haengt nicht mehr am Zeitraum-Soll "
        "(_kapSel.sollPer).")


def test_die_woche_hat_eine_obere_grenze(index_html):
    assert ("const _weekEnd=(function(){const d=new Date(_weekStart+'T00:00:00');"
            "d.setDate(d.getDate()+6);return _ymd(d);})();") in index_html, (
        "_weekEnd ist weg - ohne obere Grenze zaehlen kuenftige Erfassungen in "
        "die laufende Woche.")


# == 3 - der Untertitel nennt das Soll, mit dem wirklich gerechnet wird ======

def test_untertitel_behauptet_keine_festen_38_5(index_html):
    code = nur_code(index_html)
    assert "aktive Monteure × 38,5 h/Woche" not in code, (
        "Der Kapazitaets-Untertitel behauptet wieder feste 38,5 h. In der "
        "Feiertagswoche rechnet die Zeile dann 4x38,5=154 h, waehrend direkt "
        "darueber 'Ziel 120 h' steht - und im Monats-Modus sagt sie 'Woche'.")


def test_untertitel_zeigt_das_echte_sollper(index_html):
    assert "String(_n(_kapSel.sollPer,1)).replace('.',',')" in index_html, (
        "Der Untertitel zeigt nicht mehr _kapSel.sollPer - genau den Wert, mit "
        "dem kapSoll multipliziert.")


# == 4 - "Monteure heute" zaehlt dieselbe Menge wie die Kapazitaet ===========

def test_nenner_ist_die_kapazitaets_menge(index_html):
    assert "const totalWorkers=_kapMont.length;" in index_html, (
        "Der Nenner von 'Monteure heute' ist wieder eine eigene Abgrenzung - "
        "dann steht 'Monteure heute 3/6' ueber 'N aktive Monteure'.")


def test_zaehler_ist_auf_dieselbe_menge_gefiltert(index_html):
    assert "_kapIds.has(e.worker||e.w||e.worker_id)" in index_html, (
        "Der Zaehler von 'Monteure heute' ist wieder ungefiltert - ein "
        "buchender Backoffice-Mitarbeiter ergibt dann '7/6'.")


def test_definition_steht_hinter_kapids(index_html):
    """TDZ: `const` - stuende totalWorkers wieder oben, waere _kapMont dort noch
    nicht initialisiert und das Chef-Portal wuerfe beim Rendern."""
    i_ids = index_html.find("const _kapIds=new Set(_kapMont.map(m=>m.id));")
    i_tot = index_html.find("const totalWorkers=_kapMont.length;")
    assert i_ids != -1 and i_tot != -1, "Anker nicht gefunden"
    assert i_tot > i_ids, (
        "totalWorkers steht wieder VOR _kapIds - Temporal Dead Zone, das "
        "Chef-Portal wirft beim Rendern.")


# == 5 - Gegenprobe: die staerkere Seite wurde nicht angefasst ===============

def test_die_kapazitaets_abgrenzung_bleibt_wie_sie_war(index_html):
    assert ("const _kapMont=monteure.filter(m=>!String(m.austritt||'').trim()"
            "&&!_kapNonField(m));") in index_html, (
        "Die Kapazitaets-Abgrenzung hat sich veraendert. Ziel war, die "
        "schwaechere Seite nachzuziehen - nicht die staerkere anzufassen.")


def test_die_ampelschwellen_bleiben_70_90_100(index_html):
    assert ("const _ampBar=pct=>pct<70?'#22c55e':pct<90?'#eab308'"
            ":pct<=100?'#f97316':'#ef4444';") in index_html, (
        "Die 70/90/100-Schwellen (Chef-Entscheid v3.9.425) sind veraendert.")


# == Umkehrprobe ============================================================

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace(
        "  const totalWorkers=_kapMont.length;",
        "  const totalWorkers=monteure.filter(m=>m.r!=='Backoffice'"
        "&&m.r!=='Verkauf/Buchhaltung').length;", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert "const totalWorkers=_kapMont.length;" not in z1, (
        "Umkehrprobe: der Nenner-Riegel wuerde nicht anschlagen")

    z2 = index_html.replace(
        "&&_kapIds.has(e.worker||e.w||e.worker_id))", ")", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "_kapIds.has(e.worker||e.w||e.worker_id)" not in z2, (
        "Umkehrprobe: der Zaehler-Riegel wuerde nicht anschlagen")

    z3 = index_html.replace(
        "× '+String(_n(_kapSel.sollPer,1)).replace('.',',')+' h '"
        "+(kapZeit==='woche'?'in dieser Woche':'in diesem Monat')+'",
        "× 38,5 h/Woche", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "String(_n(_kapSel.sollPer,1)).replace('.',',')" not in z3, (
        "Umkehrprobe: der Untertitel-Riegel wuerde nicht anschlagen")
    assert "aktive Monteure × 38,5 h/Woche" in nur_code(z3), (
        "Umkehrprobe: der 38,5-Riegel wuerde den Rueckbau nicht sehen")

    z4 = index_html.replace(
        "      /* v3.9.898: hier stand eine ZWEITE",
        "      loadByWorker.length>0&&React.createElement('div',{key:'l'}),"
        "      /* v3.9.898: hier stand eine ZWEITE", 1)
    assert z4 != index_html, "Rueckbau 4 griff nicht"
    assert "loadByWorker" in nur_code(z4), (
        "Umkehrprobe: der loadByWorker-Riegel wuerde nicht anschlagen")
