# -*- coding: utf-8 -*-
"""
v3.9.872 - Zwei Funde aus dem Flaechen-Audit, beide selbst am Code nachgeprueft.

(1) PROJEKT-BOTTOM-NAV WAR TOT - derselbe Fall wie v869, eine Ebene tiefer.
    `.mob-shell-nav` (:15189) ist `position:fixed; bottom:0; z-index:80` und
    GESCHWISTER des shellSwipe-Containers (:15173), nicht dessen Kind. Mit
    `flex-wrap` und 13 Icons wird sie auf dem Handy zweireihig - also ein noch
    breiterer toter Streifen als die Haupt-Bottom-Nav, und wieder genau dort, wo
    der Daumen liegt. In JEDER Projektansicht.

(2) DOPPELTER AUSLOESER BEI DEN ABWESENHEITEN.
    `absSwipe` ist die einzige Wischflaeche, die INNERHALB einer anderen liegt
    (in `.main-pad`). React-Touch-Events blubbern, `useSwipe` stoppte nichts:
    ein Wisch dort wechselte den Unter-Tab UND sprang gleichzeitig auf den
    naechsten Haupt-Tab. Fuer Monteure faellt das nicht auf (nur ein Unter-Tab),
    fuer Admin/PL/Buero mit vier Unter-Tabs sehr wohl - wieder ein Fehler, den
    eine Messung mit Admin-Daten haette finden muessen und nicht fand.

FIX (1): eigene Wischflaeche `shellNavSwipe` mit denselben Callbacks; die
Callbacks liegen dafuer in `_shellVor`/`_shellZurueck`, damit beide Flaechen EIN
Verhalten haben.

FIX (2): die inneren Callbacks melden per `true`, dass sie wirklich gewechselt
haben; `useSwipe` stoppt dann die Weitergabe nach aussen. Hat die innere Flaeche
nichts zu tun, bleibt die aeussere zustaendig. Callbacks ohne Rueckgabewert
verhalten sich unveraendert - mainSwipe, shellSwipe und navSwipe sind nicht
betroffen.
"""
import re

from _hilfen import nur_code


# -- (1) Projekt-Bottom-Nav --------------------------------------------------

def test_projekt_bottom_nav_ist_eine_wischflaeche(index_html):
    assert 'className: "mob-shell-nav", style: {touchAction:"pan-y"}, ...shellNavSwipe}' in index_html, (
        "Die Projekt-Bottom-Nav traegt keine Wisch-Handler. Sie ist position:fixed "
        "und Geschwister des Wisch-Containers - unten waere in jeder Projektansicht "
        "wieder die Daumenzone tot."
    )


def test_beide_projekt_flaechen_teilen_die_callbacks(index_html):
    assert "const shellSwipe=useSwipe(_shellVor,_shellZurueck);" in index_html, (
        "shellSwipe nutzt nicht die ausgelagerten Callbacks"
    )
    assert "const shellNavSwipe=useSwipe(_shellVor,_shellZurueck);" in index_html, (
        "shellNavSwipe fehlt oder nutzt andere Callbacks - die beiden Flaechen "
        "koennten auseinanderlaufen."
    )


def test_projekt_callbacks_inhaltlich_unveraendert(index_html):
    assert "const _shellVor=()=>{const i=navIds.indexOf(view);if(i<navIds.length-1)setView(navIds[i+1]);};" in index_html, (
        "Vorwaerts-Callback der Projektansicht veraendert"
    )
    assert "const _shellZurueck=()=>{const i=navIds.indexOf(view);if(i>0)setView(navIds[i-1]);};" in index_html, (
        "Rueckwaerts-Callback der Projektansicht veraendert"
    )


def test_projekt_nav_bleibt_nur_auf_dem_handy_sichtbar(index_html):
    """Gegenprobe zur Diagnose: auf breiten Schirmen gibt es die Leiste nicht,
    dort stellt sich die Frage nicht."""
    assert ".mob-shell-nav{display:none}" in index_html, (
        "Die Standard-Regel display:none ist weg"
    )
    assert "@media(max-width:600px){.mob-shell-nav{display:flex" in index_html, (
        "Die Leiste wird nicht mehr nur unter 600px eingeblendet"
    )


# -- (2) Kein doppelter Ausloeser --------------------------------------------

def test_innere_flaeche_stoppt_die_aeussere_wenn_sie_feuert(index_html):
    assert "if(_gefeuert&&e.stopPropagation)e.stopPropagation();" in index_html, (
        "Eine innere Wischflaeche gibt die Geste weiter nach aussen - dann "
        "wechselt ein Wisch Unter- UND Haupt-Tab gleichzeitig."
    )
    assert "var _gefeuert=false;" in index_html, "Kein Merker, ob wirklich gefeuert wurde"


def test_stop_nur_bei_echtem_wechsel(index_html):
    """Nur `true` stoppt. Sonst wuerde eine innere Flaeche ohne Ziel die aeussere
    dauerhaft blockieren - z.B. bei Monteuren, die nur einen Unter-Tab haben."""
    assert "_gefeuert=(onLeft()===true);" in index_html and "_gefeuert=(onRight()===true);" in index_html, (
        "Der Merker haengt nicht an einem echten true - dann stoppt schon ein "
        "wirkungsloser Callback die aeussere Flaeche."
    )


def test_abs_callbacks_melden_den_wechsel(index_html):
    """v3.9.913 - DIE ZAHLEN SIND WEG. Vorher: `body.count("return true;") == 2`
    und `body.count("return false;") == 2` im absSwipe-Block.

    Die Aussage sind ZWEI benannte Callbacks (vor / zurueck), und beide muessen
    BEIDES melden - `true` beim echten Wechsel, `false` am Rand. Die zwei Summen
    konnten das nicht auseinanderhalten: ein Callback mit zwei `return true;`
    und einer ganz ohne haette sie erfuellt. Und beide zaehlten roh - ein
    Kommentar mit `return true;` haette eine fehlende Meldung gedeckt.

    Jetzt steht jede Kette ganz da: Index suchen, Grenze pruefen, umschalten,
    `true`; sonst `false`. Damit haengt auch die Bedingung mit im Riegel - ein
    `>=` statt `<` an der oberen Grenze faellt jetzt auf, vorher nicht.
    """
    code = nur_code(index_html)
    m = re.search(r"const absSwipe=useSwipe\(.*?\n  \);", code, re.S)
    assert m, "absSwipe nicht gefunden"
    body = m.group(0)
    for richtung, kette in (
        ("vor (naechster Unter-Tab)",
         "()=>{const i=absTabIds.indexOf(subView);"
         "if(i<absTabIds.length-1){setSubView(absTabIds[i+1]);return true;}return false;}"),
        ("zurueck (voriger Unter-Tab)",
         "()=>{const i=absTabIds.indexOf(subView);"
         "if(i>0){setSubView(absTabIds[i-1]);return true;}return false;}"),
    ):
        assert kette in body, (
            "Der Abwesenheits-Callback '%s' meldet den Wechsel nicht mehr genau so "
            "(true beim echten Wechsel, false am Rand) - je nach Richtung wechselt "
            "ein Wisch dann Unter- UND Haupt-Tab zugleich, oder die aeussere "
            "Flaeche bleibt faelschlich blockiert:\n%s" % (richtung, body)
        )


def test_aeussere_flaechen_bleiben_unveraendert(index_html):
    """mainSwipe/shellSwipe/navSwipe geben nichts zurueck und duerfen sich
    deshalb genau wie bisher verhalten."""
    assert "const _swipeVor=()=>setKat(k=>Math.min(k+1,Math.max(0,_tabsCountRef.current-1)));" in index_html, (
        "Haupt-Callback veraendert - er darf weiterhin nichts zurueckgeben."
    )
    assert "return true" not in index_html.split("const _swipeVor=")[1][:200], (
        "Der Haupt-Callback meldet ploetzlich einen Wechsel - dann wuerde er "
        "eine (nicht vorhandene) aeussere Flaeche stoppen wollen."
    )


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    ohne_nav = index_html.replace(
        'className: "mob-shell-nav", style: {touchAction:"pan-y"}, ...shellNavSwipe}',
        'className: "mob-shell-nav"}', 1)
    assert ohne_nav != index_html, "Rueckbau der Projekt-Nav griff nicht"
    assert '...shellNavSwipe' not in ohne_nav.split('className: "mob-shell-nav"')[1][:120], (
        "Umkehrprobe: der Projekt-Nav-Riegel wuerde nicht anschlagen"
    )

    ohne_stop = index_html.replace("if(_gefeuert&&e.stopPropagation)e.stopPropagation();", "", 1)
    assert ohne_stop != index_html, "Rueckbau des Stopps griff nicht"
    assert "if(_gefeuert&&e.stopPropagation)e.stopPropagation();" not in ohne_stop, (
        "Umkehrprobe: der Doppelauslöser-Riegel wuerde nicht anschlagen"
    )
