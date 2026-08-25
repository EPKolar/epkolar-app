# -*- coding: utf-8 -*-
"""
v3.9.870 - Ruecknahme der einzigen Verschaerfung, die ich eingebaut hatte.

MELDUNG: "bei mir geht es auch nicht mehr" - also eine Regression, und die kann
nur von mir sein. Von v863/865/867/869 hat genau EINE Aenderung die Erkennung
strenger gemacht: v863 liess eine Geste verfallen, die auf einem Quer-Scroller
BEGANN. Alles andere wurde grosszuegiger (select/table raus, dt 800->2500,
Toleranz 0.6->1.0, Flaeche groesser, Bottom-Nav dazu).

WARUM KEINE MEINER MESSUNGEN DAS FAND: ohne echte Daten laeuft kein Container
ueber. Erst mit vollen Listen entsteht der Ueberlauf - und im schmalen
Hochformat mehr als im breiten Querformat. Damit konnte die ganze Inhaltsflaeche
tot sein, waehrend mein Harnisch gruen meldete.

REPRODUZIERT, indem die Bedingung kuenstlich hergestellt wurde (breiter Wrapper
mit 1026px Ueberlauf in die Inhaltsflaeche gehaengt):

    v3.9.869   Wisch auf dem Wrapper          -> TOT
               Wrapper am Anschlag, nochmal   -> TOT   (dauerhaft tot)
    v3.9.870   Wisch auf dem Wrapper          -> TOT   (Container scrollt - richtig)
               Wrapper am Anschlag, nochmal   -> wechselt

FIX: Der Scroller wird beim Beruehren nur GEMERKT. Am Ende entscheidet die
Tatsache statt der Vermutung - hat sich sein scrollLeft veraendert, hat er die
Geste verbraucht; sonst zaehlt der Wisch. Der native Riegel haelt die Geste nur
fest, wenn der Scroller in diese Richtung nicht mehr kann.
"""
import re


def test_scroller_entwertet_die_geste_nicht_mehr_vorab(index_html):
    m = re.search(r"const skip=el\.closest&&\(.*", index_html)
    assert m, "Skip-Ausdruck nicht gefunden"
    assert "_swScrollableX" not in m.group(0), (
        "Der Quer-Scroller steht wieder in der Vorab-Absage. Genau das machte "
        "mit echten Daten die halbe Inhaltsflaeche tot."
    )


def test_scroller_wird_beim_beruehren_gemerkt(index_html):
    assert "const sc=el.closest?_swScrollableX(el,e.currentTarget):null;" in index_html, (
        "Der Scroller unter dem Finger wird nicht mehr ermittelt."
    )
    assert "sc:sc,scL:sc?sc.scrollLeft:0" in index_html, (
        "Scroller und sein Ausgangs-scrollLeft werden nicht gemerkt - dann kann "
        "am Ende niemand entscheiden, ob er die Geste verbraucht hat."
    )


def test_am_ende_entscheidet_die_tatsaechliche_bewegung(index_html):
    assert "if(Math.abs(_jetzt-touch.current.scL)>1)return;" in index_html, (
        "Es wird nicht geprueft, ob der Scroller sich wirklich bewegt hat."
    )
    # ... und zwar NACH den Schwellen, sonst haette man die Reihenfolge verdreht
    i_schwelle = index_html.find("if(dt>2500||Math.abs(dx)<70")
    i_scroll = index_html.find("if(Math.abs(_jetzt-touch.current.scL)>1)return;")
    assert i_schwelle != -1 and i_scroll != -1, "Anker nicht gefunden"
    assert i_schwelle < i_scroll, "Scroller-Pruefung steht vor den Schwellen"


def test_riegel_laesst_den_scroller_zuerst_scrollen(index_html):
    """Wuerde der native Riegel immer preventDefault machen, koennte die
    Stunden-Tabelle gar nicht mehr quer geschoben werden."""
    assert "if(dx<0?(l<max-1):(l>1))return;" in index_html, (
        "Der Riegel beruecksichtigt nicht, ob der Scroller in DIESE Richtung "
        "noch kann - dann friert er dessen Quer-Scroll ein."
    )
    assert "var max=sc.scrollWidth-sc.clientWidth, l=sc.scrollLeft;" in index_html, (
        "Der Riegel liest den Scroll-Zustand nicht."
    )


def test_helfer_unveraendert(index_html):
    """_swScrollableX selbst bleibt, wie es war - nur sein Einsatzort aendert sich."""
    m = re.search(r"function _swScrollableX\(el,stop\)\{.*?\n\}", index_html, re.S)
    assert m, "_swScrollableX fehlt"
    body = m.group(0)
    assert "scrollWidth-n.clientWidth>2" in body and 'ov==="auto"||ov==="scroll"' in body, (
        "Die Erkennung eines echten Quer-Scrollers wurde veraendert:\n" + body
    )


def test_uebrige_schwellen_unangetastet(index_html):
    """Die Ruecknahme darf die v865-Werte nicht mitnehmen."""
    m = re.search(r"if\(dt>(\d+)\|\|Math\.abs\(dx\)<(\d+)\|\|"
                  r"Math\.abs\(dy\)>Math\.abs\(dx\)\*([\d.]+)\)return;", index_html)
    assert m, "Schwellen nicht gefunden"
    assert int(m.group(1)) >= 2000, "dt-Schranke wieder zu eng"
    assert int(m.group(2)) == 70, "Mindestweg veraendert"
    assert float(m.group(3)) >= 1.0, "Richtungs-Toleranz wieder zu eng"


def test_selbsttest_riegel_schlagen_beim_rueckbau_an(index_html):
    kaputt = index_html.replace(
        'el.closest("input,textarea,[data-no-swipe]")',
        'el.closest("input,textarea,[data-no-swipe]")||_swScrollableX(el,e.currentTarget)', 1)
    assert kaputt != index_html, "Rueckbau griff nicht"
    m = re.search(r"const skip=el\.closest&&\(.*", kaputt)
    assert m and "_swScrollableX" in m.group(0), (
        "Umkehrprobe: der Vorab-Absage-Riegel wuerde nicht anschlagen"
    )
