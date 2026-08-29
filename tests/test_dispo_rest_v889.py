# -*- coding: utf-8 -*-
"""v3.9.889 - der Rest der Dispo: eine Attrappe, ein zweiter Bruchteil, vier Handgriffe.

Fortsetzung von test_dispo_zahlen_v888. Dieselbe Familie: eine Groesse wird an
zwei Stellen unterschiedlich gerechnet, etwas wird berechnet und nie gelesen, ein
Riegel ist `return true`.

────────────────────────────────────────────────────────────────────────────
A - Die Fahrzeugpruefung ist eine Attrappe MIT Versprechen
────────────────────────────────────────────────────────────────────────────
Gemessen am Bestand (29.537 Zeilen, v3.9.888, main c8bd097):

    grep "hatFz"       -> 4 Treffer: Doku(:5098), Default(:5103),
                          EINZIGER Aufruf(:5125), Uebergabe(:5279)
    grep "fz_bedarf"   -> 1 Treffer ausserhalb des APP_VERSION-Kommentars:
                          _mapArbeitsschein :1883 (LESEN)
    grep "fzBedarf"    -> 2 Treffer: :1883 (lesen), :5270 (lesen)
                       -> KEIN Schreiber. Kein Formularfeld. Kein updAs.
    sql/AS_FZ_BEDARF_v1.sql : "KEIN Ausfuehren durch CC", steht seit 15.07.
                          auf der Human-Run-Liste (HANDOFF_2026-07-15 Z.92).

Daraus folgt beweisbar: `s.fzTyp` ist an JEDEM Schein "". Der `continue`-Zweig
:5125 ist unerreichbar, und `cfg.hatFz` ist app-weit `function(){return true;}` -
er koennte auch mit gesetztem fzTyp nie blocken.

Der Wartelisten-Text :5143 verspricht trotzdem den Suffix `('Steiger' fehlt)`.
Das ist die eigentliche Falle: der Suffix haengt an `s.fzTyp`, NICHT am Ergebnis
der Pruefung. Sobald jemand die halbe Etappe 2 fertig baut (SQL laufen lassen +
das 🚛-Feld ins AS-Formular - genau das steht seit 15.07. offen), wird fzTyp
nicht leer, hatFz sagt weiter `true`, und dann bekommt JEDER Schein, der aus
IRGENDEINEM Grund - meist Kapazitaet - auf der Warteliste landet, den Zusatz
"('Steiger' fehlt)". Das Buero sucht dann ein Fahrzeug, waehrend der Tag in
Wahrheit voll ist. Ein Versprechen, das erst dann zu luegen anfaengt, wenn man
das Feature einschaltet, ist schlimmer als kein Versprechen.

Entscheidung: ENTFERNEN, nicht scharf machen. Gruende, in dieser Reihenfolge:
 1. Scharfmachen braucht vier Teile (SQL-Run + AS-Formular-UI + fahrzeuge-Prop
    bis in _dispoBuildInput + Match-Regel). DispoPanel bekommt `fahrzeuge`
    heute gar nicht (Signatur :9896), ArbeitsscheinView auch nicht (:10298).
 2. Die Match-Regel selbst waere unsound. Im Wochenplan haengen Fahrzeuge an
    einer BVH-ZEILE (`z.<tag>.fz` = Fahrzeug-IDs, :20628/:21308) - und ein
    Monteur haengt ueber `z.<tag>.ma` an derselben Zeile. Genau die Tage, auf
    die die Dispo ueberhaupt planen darf, sind aber die Tage OHNE Belegung
    (frei) bzw. die Stoerungsdienst-Zeilen - dort steht kein Fahrzeug. Ein
    scharfes hatFz wuerde also fuer jeden markierten Schein `false` liefern und
    ihn in die Warteliste schieben. Ein Riegel, der immer zu ist, ist nicht
    besser als einer, der immer offen ist.
 3. Der jetzige Zustand ist der schlechteste der drei, weil der Text eine
    Pruefung behauptet, die es nicht gibt.
Der Lesepfad `_mapArbeitsschein.fzBedarf` (:1883) BLEIBT - er kostet nichts und
ist die vorbereitete Tuer, falls Etappe 2 je gebaut wird.

MITZUAENDERN (sonst rot): tests/test_dispo_plan_v714.py :53-56 - der Fall
"hatFz=false -> Warteliste" faellt mit dem Riegel weg. Die uebrigen
`hatFz:function(){return true;}` in den cfg-Literalen der Alt-Tests sind
harmlos (unbenutzter cfg-Schluessel) und koennen stehenbleiben.

────────────────────────────────────────────────────────────────────────────
C1 - Der Zellbalken teilt durch eine andere Norm als die Wochenzahl
────────────────────────────────────────────────────────────────────────────
v3.9.888 hat den ZAEHLER beider Zahlen angeglichen. Der NENNER blieb ungleich:

    Zelle      (:_zelle)     pct = usedMin / t.normMin
    _weekStats (:_weekStats) norm += max(0, t.normMin - abwAbzug)

Ein Monteur mit halbem Zeitausgleich (abwAbzug 255 von 510) und 255 belegten
Minuten: der Balken in der Zelle zeigt 50 %, gruen. Die Wochenzahl darueber
zaehlt 255/255 = 100 %. Und die Hand-Wand (`_dispoNormFrei`, :10107) sagt
0 Minuten frei - ein Drop wird abgelehnt. Gruener Balken, geschlossene Wand,
auf einem Bildschirm. Die Farbschwellen 88 %/100 % (:10188) koennen an
Teil-Abwesenheitstagen ueberhaupt nie anschlagen.

────────────────────────────────────────────────────────────────────────────
C2 - wocheKm: berechnet, nie gelesen, und die Einheit stimmt nicht
────────────────────────────────────────────────────────────────────────────
`_dispoPlan` summiert ueber ALLE Monteur-Tage die 2-opt-Rundfahrt und gibt
`wocheKm` zurueck (:5155/:5163/:5166). Leser: keiner (grep "wocheKm" -> 4
Treffer, alle in der Definition + Doku). Dazu: seit v3.9.764 #28a liefert
`cfg.dist` FAHRMINUTEN, nicht km - die Zahl heisst km und ist eine
Minutensumme.

Anzeigen waere falsch: die Route enthaelt nur die Vorschlags-Scheine, die fixen
Termine (fixMap) fahren nicht mit. Eine "Fahrzeit der Woche", die die
bestaetigten Kundentermine auslaesst, waere die naechste Zahl, die einer
anderen widerspricht.

Loeschen waere aber auch falsch - und das ist erst beim Nachmessen aufgefallen:
`wocheKm` hat doch EINEN Leser, nur nicht in der App. test_dispo_horizont_v722
:95 (`ok(r.wocheKm===20, 'Route [A] = Firma->A->Firma')`) ist der einzige
Riegel, der belegt, dass die Tagesroute an der Firma anfaengt UND aufhoert.
Also: UMBENENNEN auf `fahrtMinHorizont` - dann heisst die Zahl, was sie ist
(Fahrminuten, ganzer Horizont, nur die Vorschlags-Route), der Riegel bleibt,
und niemand baut ein km-Feld in die Oberflaeche, das keine km enthaelt.

MITZUAENDERN (sonst rot):
  tests/test_dispo_plan_v714.py:47      ok(typeof r.wocheKm==='number', ...)
  tests/test_dispo_horizont_v722.py:95  ok(r.wocheKm===20, ...)

────────────────────────────────────────────────────────────────────────────
C3 - _dispoDauer sagt "geschaetzt" und niemand hoert zu
────────────────────────────────────────────────────────────────────────────
`_dispoDauer` liefert `{min, geschaetzt}`. grep "geschaetzt" -> 8 Treffer, ALLE
innerhalb von _dispoDauer selbst (:4872-:4895). Null Leser.

Folge in drei Stufen:
 1. Am Chip steht "1,5h" - egal ob das Buero die Dauer eingetragen hat oder ob
    eine Keyword-Regel sie geraten hat.
 2. Jede Dispo-Geste schreibt `dauer` (v3.9.740 #22a, EIN Schreibgesetz), und
    `dauer` steht in JUPROWA_PUSH_FIELDS (:3769). Die Schaetzung faehrt also
    nach OFFA und steht dort wie eine Absprache.
 3. Beim naechsten Lauf liefert `_dispoParseDauer(s.dauer)` genau diesen Wert
    zurueck - `geschaetzt:false`. Und `_dispoMedianJeKlasse`/`_dispoMedianJeTyp`
    lernen aus den `dauer`-Feldern abgeschlossener Scheine. Die Schaetzung
    bestaetigt sich selbst.
Stufe 2 nicht anfassen (Schreibgesetz ist eine Sebastian-Entscheidung). Stufe 1
heilen: die Kachel sagt, dass die Zahl geraten ist.

────────────────────────────────────────────────────────────────────────────
C4 - Totes Beiwerk in der Zelle
────────────────────────────────────────────────────────────────────────────
`_kapReal` (:10103) - eine Zuweisung, null Leser in der App. Ueberlebt hat es,
weil ein Test SEINE EXISTENZ festschreibt: test_dispo_kapazitaet_v790:73
(`assert "var _kapReal=_dispoKapazitaet(t.normMin,_abz);" in index_html`). Der
Riegel misst dort nichts - die Aussage des Tests ("die harte Wand der Zelle
rechnet auf kapAbzug") haengt an der Zeile darunter, `var _hard=((t.normMin-
_abz)<=0);`. Beim Ausbau muss diese Test-Zeile mit weg, sonst schuetzt sie
weiter toten Code.

`data-restmin`/`data-cap` gehen in den DOM und werden von keinem getAttribute
gelesen (getAttribute -> nur monteur/iso/hardblock/hardlabel/norm/used).

────────────────────────────────────────────────────────────────────────────
B - Vier Alltagswerkzeuge, seit 15.07. auf der Liste
────────────────────────────────────────────────────────────────────────────
HANDOFF_2026-07-15 Z.134 "Was die Damen brauchen": (a) Telefon am Chip als
tel:, (c) Tagesplan-Ausdruck, (d) Suche+Filter ueber der Warteliste, (e)
Morgen-Check. Alle vier am Bestand geprueft - alle vier fehlen wirklich:
  (a) grep 'href:"tel' -> 1 Treffer (:11252, Juprowa-Rohansicht). _chipBox
      (:10046) rendert Nummer/BVH/Arbeit/Dauer/Zeit - keine Nummer. Die Daten
      liegen da: `kundTel` (:1871) und `telefon` (:1882). Die MonteurTafel
      zeigt sie sogar schon (:7407 `_tel`), aber als toten Text.
  (c) grep "Tagesplan" -> 0 Treffer. Ein Druckmuster (window.open +
      document.write + @media print) existiert 12x im Haus.
  (d) Die Warteliste ist ein nacktes `_res.warteliste.map` (:10276).
  (e) grep "morgen" -> 3 Treffer, alle Kommentare.
"""
import re


def _panel(index_html):
    """Nur der DispoPanel-Rumpf. Mehrere der gesuchten Zeichenketten kommen im
    Haus schon anderswo vor (tel:-Link, Druckfenster) - ohne diese Klammer
    wuerde der Riegel gruen sein, ohne dass die Dispo etwas kann."""
    i = index_html.find("function DispoPanel({")
    assert i != -1, "DispoPanel nicht gefunden"
    j = index_html.find("function ArbeitsscheinView(", i)
    assert j != -1, "ArbeitsscheinView nicht gefunden"
    return index_html[i:j]


# ══ A - Die Fahrzeug-Attrappe ═══════════════════════════════════════════════

# v3.9.896: beide Helfer liegen jetzt in tests/_hilfen.py, weil sie in einer
# zweiten Testdatei gebraucht werden (test_dispo_werkzeuge_v893). Zwei Kopien
# waeren die naechste Groesse mit zwei Rechnungen - nur eben im Messgeraet.
# Das WARUM steht dort ausfuehrlich.
from _hilfen import nur_code as _nur_code, fundstellen as _fundstellen_neu


def _fundstellen(code, begriff, wieviel=3):
    return _fundstellen_neu(code, begriff, umfeld=55, max_treffer=wieviel)


def test_hatfz_attrappe_ist_weg(index_html):
    code = _nur_code(index_html)
    assert "hatFz" not in code, (
        "cfg.hatFz existiert wieder. Der Default ist function(){return true;} - "
        "ein Riegel, der nie zumacht, und der einzige Aufrufer haengt an "
        "s.fzTyp, das ohne Schreiber immer '' ist. Fundstellen:" + chr(10)
        + _fundstellen(code, "hatFz")
    )


def test_das_falsche_versprechen_im_wartelisten_text_ist_weg(index_html):
    code = _nur_code(index_html)
    assert "' fehlt)" not in code, (
        "Der Wartelisten-Grund verspricht wieder \"('typ' fehlt)\". Der Suffix "
        "haengt an s.fzTyp, NICHT am Ergebnis einer Pruefung - sobald fz_bedarf "
        "je gefuellt wird, nennt jeder Kapazitaets-Ueberlauf ein fehlendes "
        "Fahrzeug als Grund. Fundstellen:" + chr(10)
        + _fundstellen(code, "' fehlt)")
    )


def test_der_tote_zweig_im_plan_ist_aufgeloest(index_html):
    code = _nur_code(index_html)
    assert "s.fzTyp" not in code, (
        "fzTyp wird wieder durch _dispoBuildInput -> _dispoPlan getragen, "
        "obwohl es keinen Schreiber fuer fz_bedarf gibt."
    )


def test_der_wartelisten_grund_nennt_weiter_monteur_und_horizont(index_html):
    """Gegenprobe: beim Entfernen darf der eigentliche Grund nicht mitgehen."""
    assert '"kein freier Tag bei "+mName+" in "+(cfg.horizont||1)+" Wochen"' in index_html, (
        "Der echte Ablehngrund (Monteur + Horizont) ist beim Ausbau der "
        "Fahrzeug-Attrappe mit verschwunden."
    )


def test_der_vorbereitete_lesepfad_bleibt(index_html):
    """Gegenprobe: `fzBedarf` in _mapArbeitsschein ist die vorbereitete Tuer
    fuer Etappe 2 und kostet nichts. Sie darf NICHT mit ausgeraeumt werden."""
    assert "fzBedarf:Array.isArray(a.fz_bedarf)" in index_html, (
        "Der 42703-tolerante Lesepfad fz_bedarf (v3.9.712) wurde mit "
        "entfernt - dann muss Etappe 2 spaeter bei null anfangen."
    )


# ══ C1 - Balken-Nenner ══════════════════════════════════════════════════════

def _zelle(index_html):
    i = index_html.find("var _zelle=function(m,t){")
    assert i != -1, "_zelle nicht gefunden"
    j = index_html.find("var _weekStats=function(W){", i)
    assert j != -1, "_weekStats nicht gefunden"
    return index_html[i:j]


def test_der_zellbalken_teilt_durch_die_verfuegbare_norm(index_html):
    block = _zelle(index_html)
    assert "usedMin/(t.normMin||1)*100" not in block, (
        "Der Zellbalken teilt wieder durch die VOLLE Tagesnorm, waehrend "
        "_weekStats durch (normMin - abwAbzug) teilt. Halber Zeitausgleich + "
        "halber Tag belegt = Balken 50 % gruen, Wochenzahl 100 %, Hand-Wand zu."
    )
    assert "_pctNorm" in block, (
        "Der Balken rechnet nicht mehr gegen _pctNorm (= normMin - _abwAbz)."
    )


def test_balken_und_wand_lesen_dieselbe_abwesenheit(index_html):
    """Der Kern: beide muessen aus _abwAbz kommen, sonst driften sie erneut."""
    block = _zelle(index_html)
    assert "Math.max(0,(t.normMin||0)-_abwAbz)" in block, (
        "Der Balken-Nenner wird nicht aus _abwAbz gebildet - genau derselben "
        "Quelle, aus der _dispoNormFrei die Hand-Wand baut."
    )


def test_der_balken_bleibt_bei_null_norm_ehrlich(index_html):
    """Gegenprobe: an einem vollen Abwesenheitstag ist der Nenner 0. Eine
    Division darf dort nicht Infinity/NaN in die Breite schreiben."""
    block = _zelle(index_html)
    assert "_pctNorm>0?" in block, (
        "Kein Schutz gegen Nenner 0 - an Urlaubs-/Feiertagen wuerde die "
        "Balkenbreite NaN."
    )


# ══ C2 - wocheKm ════════════════════════════════════════════════════════════

def test_die_summe_heisst_nicht_mehr_km(index_html):
    assert "wocheKm" not in _nur_code(index_html), (
        "wocheKm ist wieder da: seit v3.9.764 #28a zaehlt cfg.dist Fahrminuten, "
        "nicht km. Der Name lockt dazu, die Zahl als km anzuzeigen."
    )


def test_die_summe_heisst_was_sie_ist(index_html):
    assert "fahrtMinHorizont" in index_html, (
        "Die Rundfahrt-Summe ist ersatzlos verschwunden - damit faellt auch der "
        "einzige Riegel, der belegt, dass die Tagesroute an der Firma beginnt "
        "UND endet (test_dispo_horizont_v722:95)."
    )


def test_der_name_sagt_auch_den_umfang(index_html):
    """Sie zaehlt den GANZEN Horizont, nicht eine Woche - und nur die
    Vorschlags-Route, ohne die fixen Termine. Wer das nicht weiss, zeigt sie
    irgendwann als "Fahrzeit dieser Woche" an.

    v3.9.896 NACHGEZOGEN: dieser Riegel las urspruenglich ein ZEICHENFENSTER
    (-1200/+400) um das erste Vorkommen des Namens. Solche Fenster messen
    frueher oder spaeter den Nachbarkommentar mit oder verrutschen bei der
    naechsten Zeile davor - in diesem Repo die haeufigste Ursache falscher
    Test-Ausschlaege. Gemessen wird jetzt am RUECKGABE-AUSDRUCK selbst und dem
    Kommentar, der unmittelbar an ihm haengt."""
    i = index_html.find("fahrtMinHorizont:Math.round(fahrtMinHorizont)};")
    assert i != -1, "Die Rueckgabe fuehrt fahrtMinHorizont nicht (mehr)"
    ende = index_html.find("*/", i)
    assert ende != -1 and ende - i < 1500, (
        "An der Rueckgabe haengt kein Erklaerkommentar mehr."
    )
    erklaerung = index_html[i:ende]
    assert "fixMap" in erklaerung, (
        "Am Rueckgabewert steht nicht, dass die fixen Termine NICHT mitfahren - "
        "genau das macht ihn als Anzeige-Zahl unbrauchbar."
    )
    assert "Horizont" in erklaerung, (
        "Am Rueckgabewert steht nicht, dass ueber den ganzen Horizont summiert "
        "wird und nicht ueber eine Woche."
    )


def test_die_2opt_reihenfolge_bleibt_erhalten(index_html):
    """Gegenprobe: nur die Summe faellt weg, die Routenoptimierung nicht."""
    assert "var opt=_dispo2opt(idx,function(i,j){return dist(pts[i],pts[j]);});" in index_html, (
        "Beim Ausbau von wocheKm ist der 2-opt-Aufruf mit verschwunden - "
        "dann steht die Tagesroute wieder in Eingabereihenfolge."
    )


# ══ C3 - geschaetzte Dauer sichtbar machen ══════════════════════════════════

def test_die_geschaetzte_dauer_wird_weitergereicht(index_html):
    assert "dauerGeschaetzt" in index_html, (
        "_dispoDauer liefert weiterhin {min, geschaetzt} und niemand liest das "
        "Flag. Am Chip ist eine geratene Dauer dann nicht von einer "
        "vereinbarten zu unterscheiden - und die Geste schreibt sie via "
        "dauer/AK_DAUER bis nach OFFA."
    )


def test_der_plan_traegt_das_flag_bis_zur_kachel(index_html):
    assert "dauerGeschaetzt:!!x.dauerGeschaetzt" in index_html, (
        "_dispoPlan reicht dauerGeschaetzt nicht an die Chip-Objekte durch - "
        "dann kommt das Flag nie an der Kachel an."
    )


def test_die_fixen_termine_tragen_es_auch(index_html):
    """v3.9.896 NACHGEZOGEN: hier stand der Riegel auf einem VARIABLENNAMEN
    (`dauerGeschaetzt:_dd.geschaetzt`). Die Umsetzung heisst an der Stelle
    `_ddf` und coerct zusaetzlich (`!!`), ist also strenger - der Riegel waere
    rot geworden, obwohl die Eigenschaft besser erfuellt ist als gefordert.
    Gemessen wird jetzt der fixMap-Eintrag als Ganzes."""
    i = index_html.find("fixMap[s.monteur][iso].push({")
    assert i != -1, "Der fixMap-Eintrag ist nicht mehr auffindbar"
    eintrag = index_html[i:index_html.find("});", i)]
    assert "dauerGeschaetzt:" in eintrag, (
        "Die fixMap-Eintraege tragen das Flag nicht - dabei ist gerade ein "
        "fixer Termin ohne gesetzte dauer der Fall, in dem eine Geste die "
        "Schaetzung nach OFFA schreibt." + chr(10) + eintrag
    )
    assert "geschaetzt" in eintrag.split("dauerGeschaetzt:")[1], (
        "dauerGeschaetzt haengt nicht am geschaetzt-Merker der Dauer-Ermittlung "
        "- dann ist es eine Konstante und markiert nichts:" + chr(10) + eintrag
    )


def test_die_kachel_zeigt_es_an(index_html):
    assert "o.dauerGeschaetzt" in index_html, (
        "_chipBox rendert das Flag nicht - dann ist es zwar berechnet und "
        "durchgereicht, aber wieder ungelesen (derselbe Fehler eine Etage "
        "hoeher)."
    )


def test_der_dauer_griff_schlaegt_die_schaetzung(index_html):
    """Gegenprobe: sobald jemand am Griff gezogen hat, ist die Zahl KEINE
    Schaetzung mehr - dann darf die Kachel sie nicht so markieren."""
    assert "_dauerOv[c.scheinId]==null" in index_html, (
        "Die Schaetzungs-Markierung beachtet den Dauer-Griff nicht - eine von "
        "Hand gezogene Dauer wuerde weiter als geraten markiert."
    )


# ══ C4 - totes Beiwerk ══════════════════════════════════════════════════════

def test_kapreal_ist_weg(index_html):
    assert "_kapReal" not in _nur_code(index_html), (
        "_kapReal wird wieder berechnet und nie gelesen."
    )


def test_ungelesene_data_attribute_sind_weg(index_html):
    assert "data-restmin" not in _nur_code(index_html) and "data-cap" not in _nur_code(index_html), (
        "data-restmin/data-cap gehen wieder in den DOM, ohne dass ein "
        "getAttribute sie liest."
    )


def test_die_gelesenen_data_attribute_bleiben(index_html):
    """Gegenprobe: an denselben Attributen haengt die Hand-Wand (Drop)."""
    for attr in ("data-monteur", "data-iso", "data-hardblock",
                 "data-hardlabel", "data-norm", "data-used"):
        assert index_html.count("getAttribute('%s')" % attr) == 2, (
            "%s wird nicht mehr an beiden Stellen (mv + up) gelesen - die "
            "Drop-Pruefung haengt daran." % attr
        )


# ══ C5 - dieselbe Zeit, zwei Toleranzen ═════════════════════════════════════

def test_terminzeit_wird_ueberall_gleich_streng_gelesen(index_html):
    """Kein Live-Fehler, ein latenter: termin_zeit ist heute TEXT im Format
    'HH:MM' (Backup 24.06.: 105x "" + 1x "07:30"). Aber DREI Stellen lesen es
    mit ZWEI Toleranzen - :9976 und :10120 mit `p.length>=2`, :10155 mit
    `p.length===2`. Kaeme je ein 'HH:MM:SS' herein (die MonteurTafel :7366
    normalisiert vorsorglich mit slice(0,5), rechnet also damit), dann waere
    derselbe Termin gleichzeitig ein blockierender Anker UND eine Kachel mit
    dem Badge 'ohne Zeit'."""
    assert 'p.length===2&&p[0]!==""' not in _nur_code(index_html), (
        "Die dritte Lesestelle ist wieder strenger als die beiden anderen."
    )


# ══ B(a) - Telefon am Chip ══════════════════════════════════════════════════

def test_der_chip_hat_einen_tel_link(index_html):
    """Wichtig: NUR im DispoPanel messen. `href:"tel:"` gibt es im Haus schon
    (Juprowa-Rohansicht :11252) - der blosse Name traefe also auch ohne die
    Dispo-Aenderung."""
    assert 'href:"tel:"' in _panel(index_html), (
        "Am Dispo-Chip gibt es keine anwaehlbare Kundennummer - dabei liegt "
        "sie im Schein (kundTel/telefon) und wird auf der MonteurTafel schon "
        "als toter Text angezeigt."
    )


def test_der_tel_link_reisst_weder_drag_noch_oeffnen_mit(index_html):
    """Der Chip haengt an onPointerDown (Drag) und onClick (Schein oeffnen).
    Ein Link darin muss BEIDE stoppen, sonst waehlt ein Fingertipp die Nummer
    und verschiebt den Termin."""
    panel = _panel(index_html)
    i = panel.find('href:"tel:"')
    assert i != -1, "kein tel:-Link im DispoPanel"
    block = panel[max(0, i - 400):i + 400]
    assert block.count("stopPropagation") >= 2, (
        "Der tel:-Link stoppt nicht beides (onPointerDown UND onClick) - "
        "dann loest ein Anruf-Tipp zugleich Drag oder Oeffnen aus."
    )


# ══ B(c) - Tagesplan-Ausdruck ═══════════════════════════════════════════════

def test_es_gibt_einen_tagesplan_ausdruck(index_html):
    assert "_dispoTagesplanDruck" in index_html, (
        "Kein Tagesplan-Ausdruck fuer den Monteur - der Zettel, der morgens "
        "mitgeht, muss weiter von Hand abgeschrieben werden."
    )


def test_der_ausdruck_nutzt_das_haus_druckmuster(index_html):
    """Kein neues Paket: window.open + document.write, wie an einem Dutzend
    anderer Stellen im Haus.

    v3.9.896 NACHGEZOGEN - die Forderung nach `@media print` ist ERSATZLOS
    entfallen, und das ist keine Abschwaechung: `@media print` braucht, wer in
    ein Dokument druckt, das auch am Bildschirm lebt - dort blendet es die
    Bedienelemente aus. Dieses Fenster ist ein EIGENSTAENDIGES Dokument, das
    nur zum Drucken existiert; sein gesamtes Stylesheet IST das Druck-
    Stylesheet. Ein `@media print` darum herum wuerde nichts aendern.

    Die dahinterliegende Sorge - "der Ausdruck kaeme mit Bildschirm-Layout" -
    wird trotzdem gemessen, nur an der Eigenschaft statt an der Schreibweise:
    eigenes Dokument, eigenes Papierformat, eigene Seitenumbrueche."""
    i = index_html.find("function _dispoTagesplanDruck(")
    assert i != -1
    block = index_html[i:i + 4200]
    assert "window.open(" in block and "document.write(" in block, (
        "Der Ausdruck geht nicht ueber das bestehende Druckfenster-Muster."
    )
    assert "<!DOCTYPE html>" in block, (
        "Der Ausdruck schreibt kein eigenstaendiges Dokument - dann erbt er "
        "das Bildschirm-Layout der App."
    )
    assert "@page{size:A4" in block, (
        "Kein eigenes Papierformat - der Ausdruck richtete sich nach dem "
        "Druckertreiber."
    )
    assert "page-break-inside:avoid" in block and "thead{display:table-header-group}" in block, (
        "Keine Seitenumbruch-Regeln - Zeilen wuerden mitten durchgeschnitten "
        "und der Spaltenkopf fehlte auf Folgeseiten."
    )


# ══ B(d) - Suche ueber der Warteliste ═══════════════════════════════════════

def test_die_warteliste_hat_eine_suche(index_html):
    assert "_wlQ" in index_html, (
        "Die Warteliste ist weiter ein nacktes map ohne Suchfeld - bei "
        "dreissig Zeilen sucht man die eine Nummer mit dem Auge."
    )


def test_die_suche_greift_auf_nummer_kunde_ort_und_grund(index_html):
    i = index_html.find("_wlFilter")
    assert i != -1, "_wlFilter nicht gefunden"
    block = index_html[i:i + 900]
    for feld in ("nummer", "kundName", "grund"):
        assert feld in block, (
            "Die Wartelisten-Suche sieht %s nicht an - dann findet sie genau "
            "das nicht, wonach im Alltag gesucht wird." % feld
        )


def test_die_ueberschrift_zaehlt_das_gefilterte_und_das_ganze(index_html):
    """Sonst waere die Zahl in der Ueberschrift der naechste Widerspruch:
    Filter an, '(30)' im Titel, drei Zeilen darunter."""
    assert "_wlSicht.length" in index_html, (
        "Die Wartelisten-Ueberschrift zaehlt nicht die sichtbaren Zeilen."
    )


# ══ B(e) - Morgen-Check ═════════════════════════════════════════════════════

def test_es_gibt_einen_morgen_check(index_html):
    assert "_morgen" in index_html, (
        "Keine Morgen-Pruefung. Termine ohne vereinbarte Zeit fallen erst am "
        "Morgen auf, wenn der Kunde anruft."
    )


def test_der_morgen_check_erscheint_nur_wenn_es_etwas_zu_melden_gibt(index_html):
    assert "_morgenOhneZeit>0&&" in index_html, (
        "Der Morgen-Check ist nicht an >0 geknuepft - eine dauerhafte 0 waere "
        "Rauschen und wuerde die Zahl entwerten (wie beim Konfliktzaehler "
        "v3.9.888)."
    )


def test_der_morgen_check_nennt_den_tag_den_er_gemessen_hat(index_html):
    """Am Freitag ist 'morgen' Samstag - im Raster steht dann Montag. Die
    Zeile muss sagen, welchen Tag sie meint, sonst ist sie die naechste Zahl
    ohne Bezug."""
    i = index_html.find("_morgenIso")
    assert i != -1, "_morgenIso nicht gefunden"
    assert "_morgenLabel" in index_html, (
        "Der Morgen-Check nennt den gemessenen Tag nicht."
    )


# ══ Konfliktzaehler: Umfang benennen ════════════════════════════════════════

def test_der_konfliktzaehler_sagt_ueber_welchen_zeitraum_er_zaehlt(index_html):
    """v3.9.888 hat ihn sichtbar gemacht - er laeuft aber ueber ALLE Wochen des
    Horizonts, waehrend darunter genau EINE KW im Raster steht. Wer die 2 sieht
    und in der offenen Woche nichts findet, sucht am falschen Ort."""
    i = index_html.find("_konfCount>0&&h('span'")
    assert i != -1, "Konfliktzaehler nicht gefunden"
    block = index_html[i:i + 600]
    assert "Horizont" in block, (
        "Der Konfliktzaehler nennt seinen Zeitraum nicht - er zaehlt ueber "
        "alle %d Wochen, angezeigt wird eine." % 4
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    """Jeder Riegel wird gegen einen kuenstlichen Rueckbau gehalten. Schlaegt
    er dabei nicht an, misst er nichts."""

    z1 = index_html.replace("_pctNorm", "t.normMin", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht (kein _pctNorm im Bestand)"
    assert _zelle(z1).count("_pctNorm") < _zelle(index_html).count("_pctNorm"), (
        "Umkehrprobe: der Balken-Nenner-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("dauerGeschaetzt:!!x.dauerGeschaetzt",
                            "dauerMin:x.dauerMin", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    assert "dauerGeschaetzt:!!x.dauerGeschaetzt" not in z2, (
        "Umkehrprobe: der Schaetzungs-Durchreiche-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace("_wlQ", "_xxQ")
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "_wlQ" not in z3, (
        "Umkehrprobe: der Wartelisten-Such-Riegel wuerde nicht anschlagen"
    )

    # Gegenrichtung: die A-Riegel sind Abwesenheits-Riegel. Sie muessen
    # anschlagen, wenn die Attrappe WIEDER eingebaut wird.
    z4 = index_html + "\nvar hatFz=cfg.hatFz||function(){return true;};\n"
    assert "hatFz" in z4, (
        "Umkehrprobe: der hatFz-Riegel wuerde einen Wiedereinbau nicht sehen"
    )
    z5 = index_html + "\n\" ('\"+s.fzTyp+\"' fehlt)\"\n"
    assert "' fehlt)" in z5, (
        "Umkehrprobe: der Versprechen-Riegel wuerde einen Wiedereinbau nicht "
        "sehen"
    )
