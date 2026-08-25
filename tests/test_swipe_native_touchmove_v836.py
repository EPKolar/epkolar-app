"""
Swipe Hochformat (v3.9.836): nativer non-passive touchmove-Riegel im useSwipe.

User: Projekt-Ansicht wischte, aber Haupt-Menü + Zeiterfassung nur im Querformat.
overscroll-behavior-x (v834) reichte im Hochformat nicht — der Browser fing die
horizontale Geste weiter ab. Fix: nativer touchmove-Listener mit preventDefault bei
horizontal-dominanter Bewegung (React onTouchMove ist passive -> nativ via ref nötig).
Vertikal + Tabellen/Inputs bleiben scrollbar. Harnisch-belegt im echten Browser.
"""
import re


def _use_swipe_body(index_html):
    i = index_html.find("function useSwipe(onLeft,onRight){")
    assert i != -1, "useSwipe nicht gefunden"
    j = index_html.find("\nfunction ", i + 10)
    return index_html[i:j]


def test_nativer_touchmove_listener(index_html):
    body = _use_swipe_body(index_html)
    assert "addEventListener('touchmove',mv,{passive:false})" in body, (
        "kein nativer non-passive touchmove-Listener (React onTouchMove wäre passive)"
    )


def test_preventDefault_nur_horizontal(index_html):
    body = _use_swipe_body(index_html)
    # v3.9.871: Die Bedingung steht nicht mehr als ein Ausdruck da. Die Richtung wird
    # jetzt EINMAL pro Geste bei 3px festgelegt (vorher erst ab 12px - da hatte der
    # Browser die Geste nach seinem Slop von etwa 8px laengst uebernommen). Die Absicht
    # dieses Tests bleibt: preventDefault nur bei waagrechter Bewegung, nur auf
    # abbrechbaren Events.
    assert "touch.current.dir=(Math.abs(dx)>Math.abs(dy))?'h':'v';" in body, (
        "Die Richtung wird nicht mehr aus dem Vektor bestimmt"
    )
    assert "if(touch.current.dir!=='h')return;" in body, (
        "preventDefault ist nicht mehr auf waagrechte Gesten beschraenkt"
    )
    assert "if(!e.cancelable)return;" in body, (
        "cancelable-Pruefung fehlt"
    )
    assert "e.preventDefault()" in body


def test_start_skip_respektiert(index_html):
    body = _use_swipe_body(index_html)
    # der touchmove-Riegel greift nur wenn der Start nicht geskippt wurde (Tabelle/Input bleiben scrollbar)
    assert "if(!touch.current.ok)return;" in body


def test_ref_wird_zurueckgegeben(index_html):
    body = _use_swipe_body(index_html)
    assert "ref:_swRef.current" in body, "useSwipe gibt keinen ref zurück (Callsites spreaden {...swipe})"
    # Detektion (onTouchStart/onTouchEnd) bleibt erhalten
    assert "onTouchStart:handlers.onTouchStart" in body and "onTouchEnd:handlers.onTouchEnd" in body
