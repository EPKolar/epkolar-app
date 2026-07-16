# -*- coding: utf-8 -*-
"""v3.9.741 Gate-Lektion (Sebastian, P0-Hotfix): jeder in DispoPanel referenzierte Prop-Callback (on*) MUSS
in der Signatur stehen — sonst ReferenceError beim RENDERN (der Boot-Smoke sieht das DispoPanel nie).

Konkret gefangen: v740 liess `onReschedule?` im Style der fixen Kachel stehen, obwohl der Prop in onDrop
umbenannt war -> ReferenceError in _zelle -> ganzer Arbeitsscheine-Tab crasht. Dieser statische Test difft
alle on*-Referenzen (ausser DOM-Handler onClick/onPointer*) gegen die DispoPanel-Parameterliste.
"""
import re


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


_DOM_HANDLERS = {
    "onClick", "onPointerDown", "onPointerUp", "onPointerMove", "onPointerEnter",
    "onPointerLeave", "onPointerCancel", "onChange", "onInput", "onSubmit",
    "onFocus", "onBlur", "onKeyDown", "onKeyUp", "onMouseDown", "onMouseUp",
    "onMouseEnter", "onMouseLeave", "onWheel", "onScroll", "onTouchStart", "onTouchEnd",
}


def test_alle_prop_callbacks_in_signatur(index_html):
    body = _panel(index_html)
    sig = re.search(r"function DispoPanel\(\{([^}]*)\}\)", body).group(1)
    params = set(p.strip() for p in sig.split(","))
    # Alle on*-Bezeichner im Body, ausser echte DOM-Event-Handler.
    referenced = set(re.findall(r"\bon[A-Z][a-zA-Z]+", body)) - _DOM_HANDLERS
    missing = sorted(r for r in referenced if r not in params)
    assert not missing, (
        "Diese Prop-Callbacks werden in DispoPanel referenziert, stehen aber NICHT in der Signatur "
        "(ReferenceError beim Rendern): %s. Signatur: %s" % (missing, sorted(params))
    )


def test_onreschedule_ist_raus(index_html):
    # v3.9.740/741: onReschedule wurde durch onDrop ersetzt — im Panel-Code darf es nicht mehr vorkommen.
    body = _panel(index_html)
    assert "onReschedule" not in body, "onReschedule noch im DispoPanel-Code (P0-Klasse)"
