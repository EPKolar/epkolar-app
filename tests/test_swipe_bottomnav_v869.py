# -*- coding: utf-8 -*-
"""
v3.9.869 - "quer kann er wischen, hoch nicht".

Der Hinweis kam vom Nutzer selbst, nachdem Riedmann die App geloescht und neu
installiert hatte - er lief also nachweislich auf dem aktuellen Stand, und
trotzdem ging es nur gedreht. Das war der entscheidende Satz der ganzen Jagd.

URSACHE: Im Hochformat liegt am unteren Rand die fixe `.bottom-nav`
(position:fixed, ~58px + Safe-Area, z-index 80). Sie ist KEIN Kind von
`.main-pad`, also erreicht ein Wisch dort den Hook nie - und genau dort liegt
der Daumen, wenn man ein Handy einhaendig haelt. Im Querformat (>= 600px) ist
die Leiste `display:none`, die ganze Flaeche gehoert `.main-pad`, deshalb ging
dort immer alles.

GEMESSEN (echte Touch-Eingabe ueber CDP, Rolle monteur, Live-Stand):

    hoch 390x844   Bottom-Nav y 786..844 (display:flex)
                   Mitte Inhalt   y=464  -> wechselt
                   knapp darueber y=761  -> wechselt
                   AUF der Leiste y=806  -> TOT
    quer 844x390   Bottom-Nav display:none
                   alle drei Punkte      -> wechseln

WARUM v3.9.867 DAS NICHT LOESTE: dieser Fix hat `.main-pad` bis zum unteren
Bildschirmrand gezogen - richtig und noetig, aber die Leiste liegt DARUEBER.
`elementFromPoint` trifft dort die Leiste, nicht `.main-pad`. Die Flaeche war
also gross genug und trotzdem an dieser Stelle unerreichbar.

FIX: Die Leiste bekommt ihre eigene Wisch-Flaeche (`navSwipe`) mit denselben
Callbacks. Tippen bleibt unberuehrt: der native Riegel greift erst ab |dx|>12,
ausgeloest wird erst ab |dx|>=70 - ein Tipp hat dx~0 und trifft weiter den Knopf.
"""
import re


def test_bottom_nav_ist_eine_wischflaeche(index_html):
    assert 'className: "bottom-nav", style: {touchAction:"pan-y"}, ...navSwipe}' in index_html, (
        "Die Bottom-Nav traegt keine Wisch-Handler mehr. Im Hochformat sind damit "
        "die untersten ~58px wieder tot - genau dort, wo der Daumen liegt."
    )


def test_navSwipe_existiert_und_nutzt_dieselben_callbacks(index_html):
    """Zwei Flaechen, EIN Verhalten. Getrennte Callbacks waeren zwei Wahrheiten."""
    assert "const navSwipe=useSwipe(_swipeVor,_swipeZurueck);" in index_html, "navSwipe fehlt"
    assert "const mainSwipe=useSwipe(_swipeVor,_swipeZurueck);" in index_html, (
        "mainSwipe nutzt nicht dieselben Callbacks wie navSwipe - die beiden "
        "Flaechen koennten auseinanderlaufen."
    )


def test_callbacks_sind_inhaltlich_unveraendert(index_html):
    """Die Auslagerung in _swipeVor/_swipeZurueck darf das Verhalten nicht
    veraendern - inklusive der v3.9.313-Klammer gegen den Ueberlauf."""
    assert "const _swipeVor=()=>setKat(k=>Math.min(k+1,Math.max(0,_tabsCountRef.current-1)));" in index_html, (
        "Vorwaerts-Callback veraendert - der Clamp gegen den letzten Tab (v3.9.313) "
        "muss erhalten bleiben, sonst haengen Folge-Wische."
    )
    assert "const _swipeZurueck=()=>setKat(k=>Math.max(k-1,0));" in index_html, (
        "Rueckwaerts-Callback veraendert - der Clamp bei 0 muss bleiben."
    )


def test_tippen_auf_der_leiste_bleibt_moeglich(index_html):
    """Der Riegel darf erst bei echter Querbewegung greifen, sonst schluckt die
    Leiste ihre eigenen Knopfdruecke."""
    # v3.9.870: der Riegel steht jetzt als Frueh-Ausstieg da (if(!(...))return;),
    # damit ein Quer-Scroller vorher zum Zug kommt. Die Schwelle selbst ist dieselbe.
    m = re.search(r"Math\.abs\(dx\)>(\d+)&&Math\.abs\(dx\)>Math\.abs\(dy\)&&e\.cancelable", index_html)
    assert m, "Der touchmove-Riegel ist nicht mehr auffindbar"
    schwelle = int(m.group(1))
    assert schwelle >= 10, (
        "Der Riegel greift schon ab %dpx Querbewegung - ein leicht verwackelter "
        "Tipp auf einen Nav-Knopf wuerde dann unterdrueckt." % schwelle
    )
    m2 = re.search(r"if\(dt>\d+\|\|Math\.abs\(dx\)<(\d+)\|\|", index_html)
    assert m2 and int(m2.group(1)) >= 70, (
        "Der Mindestweg fuer einen Wisch ist unter 70px - auf der Nav-Leiste "
        "wuerde dann ein ungenauer Tipp als Wisch zaehlen und die Seite wechseln."
    )


def test_leiste_traegt_touch_action_wie_die_anderen_flaechen(index_html):
    """Dieselbe Invariante wie fuer .main-pad, shellSwipe und absSwipe:
    ohne touch-action:pan-y frisst der Browser die horizontale Geste."""
    assert 'className: "bottom-nav", style: {touchAction:"pan-y"}' in index_html, (
        "Die Leiste hat kein touch-action:pan-y"
    )


def test_querformat_blendet_die_leiste_weiterhin_aus(index_html):
    """Die Gegenprobe zur Diagnose: quer gibt es die Leiste nicht, deshalb ging
    es dort immer. Kippt diese Regel, aendert sich das Fehlerbild komplett."""
    assert "@media(max-width:600px){.bottom-nav{display:flex" in index_html, (
        "Die Bottom-Nav wird nicht mehr nur unter 600px eingeblendet - die "
        "Hoch/Quer-Diagnose dieser Version passt dann nicht mehr."
    )
    assert ".bottom-nav{display:none}" in index_html, (
        "Die Standard-Regel display:none fuer >=600px ist weg."
    )


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    kaputt = index_html.replace(
        'className: "bottom-nav", style: {touchAction:"pan-y"}, ...navSwipe}',
        'className: "bottom-nav"}', 1)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet"
    assert '...navSwipe}' not in kaputt.split('className: "bottom-nav"')[1][:120], (
        "Umkehrprobe: der Bottom-Nav-Riegel wuerde nicht anschlagen"
    )
