# -*- coding: utf-8 -*-
"""v3.9.893 - Drei Alltagswerkzeuge, die seit 15.07.2026 offenstanden, und eine Zahl,
die ihren Namen nicht verdient hat.

Quelle der ersten drei: `docs/handoffs/HANDOFF_2026-07-15.md` - "Was die Damen
brauchen". Alle drei wurden nachgeprueft und fehlten tatsaechlich.

────────────────────────────────────────────────────────────────────────────
(a) Die Kundennummer stand nirgends in der Dispo
────────────────────────────────────────────────────────────────────────────
Die Nummer liegt seit jeher im Schein (`telefon` bzw. `kundTel`), und die
MonteurTafel zeigt sie sogar - dort aber als toten Text. In der Dispo gab es sie
nicht: wer anrufen wollte, musste den Schein oeffnen.

Der Link nutzt WOERTLICH dieselbe Definition wie die MonteurTafel - eine Antwort
auf "die Nummer des Kunden", nicht zwei.

**Die Falle dabei:** die Kachel haengt an `onPointerDown` (Ziehen) UND `onClick`
(Schein oeffnen). Ein Link, der nicht BEIDES stoppt, verschiebt beim Antippen den
Termin, statt zu waehlen.

────────────────────────────────────────────────────────────────────────────
(d) Die Warteliste hatte kein Suchfeld
────────────────────────────────────────────────────────────────────────────
Ein nacktes `_res.warteliste.map` - kein Eingabefeld, kein Zustand. Bei zwanzig
nicht eingeplanten Scheinen sucht man von Hand.

Gesucht wird ueber genau die Felder, die in der ZEILE stehen - plus den **Grund**,
denn danach wird im Alltag genauso gesucht ("wer hat keinen Monteur"). Umlaute
werden gefaltet, damit "Muehlbach" auch "Mühlbach" findet.

Die Ueberschrift nennt gefiltert UND gesamt. Ohne das waere die Zahl in der
Ueberschrift der naechste Widerspruch zur Liste darunter - genau die Krankheit,
die v888 und v891 aufgeraeumt haben.

────────────────────────────────────────────────────────────────────────────
(e) Niemand fragte, was morgen frueh ansteht
────────────────────────────────────────────────────────────────────────────
Gezaehlt werden fixe Termine OHNE vereinbarte Uhrzeit - genau die kosten am
Morgen Telefonate, weil der Kunde nicht weiss, wann jemand kommt.

**"Morgen" ist am Freitag der Samstag, im Raster steht aber Montag.** Der Tag wird
deshalb im Raster GESUCHT, nicht gerechnet - und die Zeile NENNT ihn, sonst waere
es die naechste Zahl ohne Bezug.

────────────────────────────────────────────────────────────────────────────
(C2) `wocheKm` hiess km, enthielt Minuten, und niemand las es
────────────────────────────────────────────────────────────────────────────
`_dispoPlan` summiert die 2-opt-Rundfahrten. Seit v3.9.764 liefert `cfg.dist`
aber **Fahrminuten**, nicht km - und summiert wird ueber den ganzen Horizont, nicht
eine Woche. Leser in der App: **null**.

Anzeigen waere falsch: die Route enthaelt nur die Vorschlags-Scheine, die **fixen
Termine fahren nicht mit**. Eine "Fahrzeit der Woche" ohne die bestaetigten
Kundentermine waere die naechste Zahl, die einer anderen widerspricht.

Loeschen waere aber auch falsch - und das ist erst beim Nachmessen aufgefallen:
`wocheKm` hat doch einen Leser, nur nicht in der App. `test_dispo_horizont_v722`
ist der **einzige** Riegel, der belegt, dass die Tagesroute an der Firma anfaengt
*und* aufhoert.

Deshalb: umbenannt auf `fahrtMinHorizont`, der alte Name bleibt uebergangsweise
als Zwilling stehen. Dann heisst die Zahl, was sie ist, kein Bestandstest geht
still kaputt, und niemand baut ein km-Feld in die Oberflaeche, das keine km
enthaelt.
"""
import re


# ══ (a) Telefon am Chip ═════════════════════════════════════════════════════

def test_es_gibt_genau_eine_definition_der_kundennummer(index_html):
    assert 'var _telOf=function(x){return String((x&&x.telefon)||"").trim()||String((x&&x.kundTel)||"").trim();};' in index_html, (
        "_telOf fehlt oder weicht ab - zwei Definitionen von 'die Nummer des "
        "Kunden' waeren zwei Wahrheiten."
    )


def test_beide_kacheln_reichen_die_nummer_durch(index_html):
    assert "tel:_telOf(_fs)," in index_html, "Die Fix-Kachel reicht die Nummer nicht durch"
    assert "tel:_telOf(_cs)," in index_html, "Die Vorschlags-Kachel reicht die Nummer nicht durch"


def test_der_anruf_verschiebt_keinen_termin(index_html):
    """Die Falle: die Kachel haengt an onPointerDown UND onClick. Stoppt der Link
    nicht BEIDES, verschiebt ein Anruf-Tipp den Termin."""
    i = index_html.find('href:"tel:"')
    assert i != -1, "Der Telefon-Link fehlt"
    block = index_html[i:i + 420]
    assert "onPointerDown:function(e){if(e&&e.stopPropagation)e.stopPropagation();}" in block, (
        "Der Link stoppt onPointerDown nicht - ein Anruf-Tipp startet dann die "
        "Zieh-Geste:\n" + block[:250]
    )
    assert "onClick:function(e){if(e&&e.stopPropagation)e.stopPropagation();}" in block, (
        "Der Link stoppt onClick nicht - ein Anruf-Tipp oeffnet dann den Schein."
    )


def test_die_nummer_wird_fuer_den_waehlvorgang_gesaeubert(index_html):
    assert 'String(o.tel).replace(/[^0-9+]/g,"")' in index_html, (
        "Die Nummer wird nicht gesaeubert - Leerzeichen und Schraegstriche aus "
        "der Stammdatenpflege brechen den tel:-Link."
    )


# ══ (d) Wartelisten-Suche ═══════════════════════════════════════════════════

def test_der_suchzustand_liegt_vor_dem_early_return(index_html):
    """Hook-Reihenfolge: in dieser Datei ist daran schon einmal etwas zerbrochen."""
    i_hook = index_html.find("var _wq=_react.useState.call(void 0,\"\");")
    i_ret = index_html.find("if(!_built||!_res)")
    assert i_hook != -1, "Der Suchzustand fehlt"
    if i_ret != -1:
        assert i_hook < i_ret, (
            "Der Such-Hook steht NACH dem Early-Return - React wirft dann bei "
            "wechselnder Hook-Zahl."
        )


def test_gesucht_wird_auch_im_grund(index_html):
    i = index_html.find("var _wlFilter=function(w){")
    assert i != -1, "_wlFilter fehlt"
    block = index_html[i:i + 420]
    assert "w.grund" in block, (
        "Der Wartelisten-Grund ist nicht durchsuchbar - dabei wird im Alltag "
        "genau danach gesucht ('wer hat keinen Monteur'):\n" + block[:250]
    )
    assert "_dispoBvhNorm" in block, (
        "Keine Umlaut-Faltung - dann findet 'Muehlbach' das 'Mühlbach' nicht."
    )


def test_die_ueberschrift_widerspricht_der_liste_nicht(index_html):
    assert '_wlSicht.length!==_res.warteliste.length?(" von "+_res.warteliste.length)' in index_html, (
        "Die Ueberschrift nennt nicht gefiltert UND gesamt - dann steht dort eine "
        "Zahl, die der Liste darunter widerspricht."
    )


def test_die_liste_selbst_ist_gefiltert(index_html):
    assert ",_wlSicht.map(function(w){" in index_html, (
        "Die Liste zeigt weiter alle Eintraege - die Suche waere wirkungslos."
    )


def test_der_block_haengt_an_der_gesamtzahl(index_html):
    """Sonst verschwaende die Suche samt Liste, sobald sie nichts findet - und
    man kaeme nicht mehr an das Eingabefeld heran."""
    assert "_res.warteliste.length?h('div',{style:{marginTop:14}}" in index_html, (
        "Der Wartelisten-Block haengt nicht mehr an der GESAMTzahl."
    )


# ══ (e) Morgen-Pruefung ═════════════════════════════════════════════════════

def test_morgen_wird_im_raster_gesucht_nicht_gerechnet(index_html):
    assert 'if(_built.tage[_mi].key>_built.heute){_morgenIso=_built.tage[_mi].key;break;}' in index_html, (
        "Der naechste Tag wird gerechnet statt im Raster gesucht - am Freitag "
        "waere 'morgen' dann der Samstag, im Raster steht aber Montag."
    )


def test_gezaehlt_werden_termine_ohne_uhrzeit(index_html):
    i = index_html.find("var _morgenOhneZeit=0;")
    assert i != -1, "Die Morgen-Pruefung fehlt"
    block = index_html[i:i + 320]
    assert 'if(!z2||z2==="00:00")_morgenOhneZeit++;' in block, (
        "Es werden nicht die Termine OHNE vereinbarte Uhrzeit gezaehlt - genau "
        "die kosten am Morgen Telefonate."
    )


def test_die_zeile_nennt_den_tag(index_html):
    assert 'var _morgenLabel=' in index_html and '" am "+_morgenLabel+" ohne Zeit"' in index_html, (
        "Die Anzeige nennt den Tag nicht - dann ist es die naechste Zahl ohne "
        "Bezug."
    )


def test_der_konfliktzaehler_nennt_seinen_zeitraum(index_html):
    assert '+" (Horizont)"' in index_html, (
        "Der Konfliktzaehler laeuft ueber ALLE Wochen, angezeigt wird EINE KW - "
        "ohne den Hinweis sucht man in der offenen Woche vergeblich."
    )


# ══ (C2) Umbenennung ════════════════════════════════════════════════════════

def test_die_zahl_heisst_wie_sie_rechnet(index_html):
    assert "var plan={}, fahrtMinHorizont=0;" in index_html, (
        "fahrtMinHorizont heisst wieder wocheKm - der Name behauptet km und "
        "Woche, die Zahl sind Minuten ueber den ganzen Horizont."
    )
    assert "fahrtMinHorizont:Math.round(fahrtMinHorizont)" in index_html, (
        "Die Rueckgabe fuehrt den neuen Namen nicht."
    )


def test_der_alte_name_bleibt_uebergangsweise(index_html):
    """Bewusste Grenze: test_dispo_horizont_v722 ist der EINZIGE Riegel, der
    belegt, dass die Tagesroute an der Firma beginnt UND endet. Ihn still
    kaputtzumachen waere schlimmer als ein doppelter Name."""
    assert "wocheKm:Math.round(fahrtMinHorizont)" in index_html, (
        "Der Zwilling wocheKm ist weg - dann faellt der einzige Riegel fuer die "
        "Rundfahrt-Eigenschaft still aus."
    )


# ══ Umkehrprobe ═════════════════════════════════════════════════════════════

def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    z1 = index_html.replace(",_wlSicht.map(function(w){", ",_res.warteliste.map(function(w){", 1)
    assert z1 != index_html, "Rueckbau 1 griff nicht"
    assert ",_wlSicht.map(function(w){" not in z1, (
        "Umkehrprobe: der Filter-Riegel wuerde nicht anschlagen"
    )

    z2 = index_html.replace("onPointerDown:function(e){if(e&&e.stopPropagation)e.stopPropagation();},"
                            "onClick:function(e){if(e&&e.stopPropagation)e.stopPropagation();},", "", 1)
    assert z2 != index_html, "Rueckbau 2 griff nicht"
    # Gesucht wird der CODE, nicht das Wort: der erklaerende Kommentar direkt
    # daneben nennt "onPointerDown" ebenfalls und wuerde die Probe entwerten -
    # dieselbe Falle, die in diesem Repo heute achtmal zugeschnappt ist.
    i = z2.find('href:"tel:"')
    assert i != -1, "Telefon-Link im Rueckbau nicht mehr auffindbar"
    assert "onPointerDown:function(e)" not in z2[i:i + 420], (
        "Umkehrprobe: der Gesten-Riegel wuerde nicht anschlagen"
    )

    z3 = index_html.replace("var plan={}, fahrtMinHorizont=0;", "var plan={}, wocheKm=0;", 1)
    assert z3 != index_html, "Rueckbau 3 griff nicht"
    assert "var plan={}, fahrtMinHorizont=0;" not in z3, (
        "Umkehrprobe: der Namens-Riegel wuerde nicht anschlagen"
    )
