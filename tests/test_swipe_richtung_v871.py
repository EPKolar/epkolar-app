# -*- coding: utf-8 -*-
"""
v3.9.871 - Die Richtung wurde zu spaet entschieden.

DER BEFUND, DER ES AUFLOESTE (vom Nutzer):
"geht nur in der Leiste das Wischen, aber nicht am ganzen Bildschirm."

Beide Flaechen nutzen denselben Hook - es lag also nicht am Hook, sondern an der
Flaeche:

  .bottom-nav  ist position:fixed. Dort gibt es NICHTS zu scrollen, der Browser
               laesst die Geste in Ruhe -> Wischen ging dort immer.
  .main-pad    ist die scrollbare Flaeche. Dort entscheidet Chrome nach seinem
               Touch-Slop (etwa 8px) SELBST, ob die Geste ein Scroll ist.

Der bisherige Riegel griff erst ab |dx| > 12px - da hatte der Browser die Geste
laengst uebernommen. Spaetere preventDefault laufen ins Leere (die Events sind
dann nicht mehr cancelable), und am Ende kommt oft touchcancel statt touchend.
Deshalb kam der Wisch auf dem Inhalt nie an.

Das erklaert auch "quer geht, hoch nicht": im Querformat ist die sichtbare
Flaeche kuerzer und der Browser weniger scroll-eifrig.

FIX: EINMAL PRO GESTE entscheiden, sobald der Finger 3px zurueckgelegt hat - also
VOR dem Browser - und die Entscheidung festhalten:
    waagrecht -> jeden weiteren Move festhalten, der Browser bekommt sie nicht
    senkrecht -> Geste ans Scrollen abgeben (ok=false, kein Wisch)

WARUM KEINE MEINER MESSUNGEN DAS FAND: synthetische und CDP-Gesten durchlaufen
die Scroll-Arbitrierung des Browsers nicht wie ein echter Finger auf echter
Hardware. Genau deshalb war jede Messung gruen, waehrend zwei Nutzer dasselbe
Gegenteil berichteten.
"""
import re


def _mv(index_html):
    i = index_html.find("var mv=function(e){if(!touch.current.ok)return;")
    assert i != -1, "Der native touchmove-Riegel ist nicht mehr auffindbar"
    j = index_html.find("e.preventDefault();", i)
    assert j != -1, "preventDefault im Riegel fehlt"
    return re.sub(r"/\*.*?\*/", "", index_html[i:j], flags=re.S)


def test_richtung_wird_vor_dem_browser_entschieden(index_html):
    """Chrome entscheidet nach etwa 8px. Wer erst danach zugreift, kommt zu spaet."""
    mv = _mv(index_html)
    m = re.search(r"if\(weg<(\d+)\)return;", mv)
    assert m, "Keine frueh greifende Schwelle gefunden:\n" + mv
    slop = int(m.group(1))
    assert slop <= 5, (
        "Die Richtung wird erst ab %dpx entschieden. Chrome uebernimmt die Geste "
        "schon bei etwa 8px - danach ist jedes preventDefault wirkungslos." % slop
    )
    assert slop >= 2, (
        "Schwelle %dpx ist zu klein - schon das Zittern beim Antippen wuerde eine "
        "Richtung festlegen." % slop
    )


def test_entscheidung_gilt_fuer_die_ganze_geste(index_html):
    """Ohne Festhalten koennte mitten in der Geste umgeschaltet werden - dann
    haette der Browser doch wieder eine Chance, sie zu uebernehmen."""
    mv = _mv(index_html)
    assert "if(touch.current.dir===null){" in mv, "Es wird keine Richtung gemerkt"
    assert "touch.current.dir=(Math.abs(dx)>Math.abs(dy))?'h':'v';" in mv, (
        "Die Richtung wird nicht aus dem Vektor bestimmt:\n" + mv
    )
    assert "if(touch.current.dir!=='h')return;" in mv, (
        "Die gemerkte Richtung wird nicht angewandt - die Entscheidung waere "
        "wirkungslos."
    )


def test_senkrechte_geste_gibt_das_scrollen_frei(index_html):
    """Wird senkrecht erkannt, muss die Geste komplett losgelassen werden -
    sonst ruckelt das Scrollen oder wird ganz blockiert."""
    mv = _mv(index_html)
    assert "if(touch.current.dir==='v'){touch.current.ok=false;return;}" in mv, (
        "Eine als senkrecht erkannte Geste wird nicht freigegeben:\n" + mv
    )


def test_zustand_traegt_die_richtung(index_html):
    assert "dir:null}" in index_html, (
        "Der Gesten-Zustand traegt kein dir-Feld - dann startet jede Geste ohne "
        "sauberen Ausgangspunkt und die Entscheidung der Vorgaenger-Geste wirkt nach."
    )


def test_querscroller_vorrang_bleibt(index_html):
    """v870 darf durch die Umstellung nicht verloren gehen."""
    mv = _mv(index_html)
    assert "var sc=touch.current.sc;" in mv and "if(dx<0?(l<max-1):(l>1))return;" in mv, (
        "Der Vorrang eines echten Quer-Scrollers ist weg - die Stunden-Tabelle "
        "liesse sich dann nicht mehr schieben."
    )


def test_reihenfolge_richtung_vor_scroller(index_html):
    """Erst Richtung klaeren, dann dem Scroller den Vortritt lassen. Andersherum
    wuerde die Geste beim Scroller haengen, bevor sie ueberhaupt als waagrecht
    erkannt ist."""
    mv = _mv(index_html)
    i_dir = mv.find("touch.current.dir=(")
    i_sc = mv.find("var sc=touch.current.sc;")
    assert i_dir != -1 and i_sc != -1, "Anker nicht gefunden"
    assert i_dir < i_sc, "Scroller-Pruefung steht vor der Richtungsentscheidung"


def test_schwellen_der_auswertung_unangetastet(index_html):
    """Die Richtungsentscheidung ersetzt NICHT die Auswertung am Gestenende."""
    m = re.search(r"if\(dt>(\d+)\|\|Math\.abs\(dx\)<(\d+)\|\|"
                  r"Math\.abs\(dy\)>Math\.abs\(dx\)\*([\d.]+)\)return;", index_html)
    assert m, "Die Auswertung am Gestenende ist weg"
    assert int(m.group(1)) >= 2000 and int(m.group(2)) == 70 and float(m.group(3)) >= 1.0, (
        "Die Schwellen aus v865 wurden mitveraendert: dt=%s, dx=%s, ratio=%s"
        % (m.group(1), m.group(2), m.group(3))
    )


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(index_html):
    kaputt = re.sub(r"if\(weg<\d+\)return;", "if(weg<12)return;", index_html, count=1)
    assert kaputt != index_html, "Rueckbau griff nicht - Anker veraltet"
    m = re.search(r"if\(weg<(\d+)\)return;", _mv(kaputt))
    assert m and int(m.group(1)) > 5, (
        "Umkehrprobe: der Schwellen-Riegel wuerde nicht anschlagen"
    )
