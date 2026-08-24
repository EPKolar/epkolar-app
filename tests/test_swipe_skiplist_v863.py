"""
Swipe v3.9.863 — tote Zonen in der useSwipe-Skip-Liste.

BUG (User-Report 24.08.2026): "wir koennen in der App nicht auf allen Seiten
wischen, z.B. Dashboard."

GEMESSEN (eingeloggtes UI, 390px Hochformat, synthetische Touch-Gesten ueber ein
5x9-Raster je Seite; gelesen wurde `defaultPrevented` des touchmove, also die
ECHTE Hook-Entscheidung, nicht eine Nachbildung):

    Einstellungen   24% der Flaeche tot (SELECT 4, INPUT 1)
    Flotte          16% der Flaeche tot (SELECT 5)
    Gefahrenstoffe  11% der Flaeche tot (INPUT 5)

Der Mechanismus selbst war intakt — Haupt-Tabs und Projekt-Ansicht wechselten
sauber. Tot war die Geste immer dann, wenn sie auf einem Element der Skip-Liste
BEGANN: `select` und `table` brachen sie ab.

FIX:
  (1) `select` raus. Ein geschlossenes Select hat keine eigene Horizontal-Geste;
      der Tap oeffnet es weiter, weil der native Riegel erst ab |dx|>12 greift.
  (2) `table` ersetzt durch `_swScrollableX()` — geskippt wird nur noch, was
      WIRKLICH quer scrollen kann (scrollWidth>clientWidth UND overflow-x
      auto/scroll). Das wirkt in beide Richtungen: nicht-scrollende Tabellen
      werden wischbar, und echte Querscroller behalten ihren Scroll — auch die,
      die gar keine Tabelle sind (die alte Tag-Regel schuetzte die nicht; seit
      v836 frass der native Riegel deren Scroll).
  (3) `onTouchCancel` entwertet die Geste (v834-Befund: die Browser-Wisch-
      zurueck-Navigation liefert touchcancel statt touchend).

`input`/`textarea` bleiben bewusst geskippt — dort ist Querziehen Caret,
Textauswahl oder Slider.
"""
import re


def _skip_expr(index_html):
    """Der eine Ausdruck in useSwipe.onTouchStart, der ueber Skip/Nicht-Skip
    entscheidet — von `const skip=` bis zum Zeilenende."""
    m = re.search(r"const skip=el\.closest&&\(.*", index_html)
    assert m, "Skip-Ausdruck in useSwipe.onTouchStart nicht gefunden"
    return m.group(0)


# ── Fix 1: select ist kein Skip-Grund mehr ───────────────────────────────────

def test_select_nicht_mehr_in_skipliste(index_html):
    expr = _skip_expr(index_html)
    assert "select" not in expr, (
        "select steht wieder in der Skip-Liste — jede Geste, die auf einem "
        "Select beginnt, ist damit tot (gemessen: Einstellungen 24%, Flotte "
        "16% der Seitenflaeche).\n" + expr
    )


# ── Fix 2: table -> echte Quer-Scrollbarkeit ─────────────────────────────────

def test_table_nicht_mehr_pauschal_geskippt(index_html):
    expr = _skip_expr(index_html)
    assert "table" not in expr, (
        "Pauschaler table-Skip ist zurueck. Nicht-scrollende Tabellen sind "
        "damit wieder tote Flaeche.\n" + expr
    )


def test_skip_nutzt_scrollbarkeits_pruefung(index_html):
    expr = _skip_expr(index_html)
    assert "_swScrollableX(el,e.currentTarget)" in expr, (
        "Der Skip prueft nicht mehr auf echte Quer-Scrollbarkeit.\n" + expr
    )


def test_swScrollableX_prueft_beide_bedingungen(index_html):
    """Nur scrollWidth>clientWidth reicht nicht (ein overflow:hidden-Container
    meldet das auch) und nur overflow-x:auto reicht nicht (ohne Ueberlaenge
    scrollt da nichts). Beides muss zusammenkommen, sonst wird wieder pauschal
    geskippt bzw. pauschal durchgelassen."""
    m = re.search(r"function _swScrollableX\(el,stop\)\{.*?\n\}", index_html, re.S)
    assert m, "_swScrollableX nicht gefunden"
    body = m.group(0)
    assert "scrollWidth-n.clientWidth>2" in body, "Ueberlaengen-Pruefung fehlt:\n" + body
    assert 'ov==="auto"||ov==="scroll"' in body, "overflow-x-Pruefung fehlt:\n" + body
    assert "n=n.parentElement" in body, "Laeuft nicht die Vorfahren hoch:\n" + body
    assert "n!==stop" in body, (
        "Ohne stop-Grenze laeuft die Suche ueber den Wisch-Container hinaus "
        "und der aeussere Scroller wuerde jede Geste abwuergen:\n" + body
    )


# ── Fix 3: touchcancel ───────────────────────────────────────────────────────

def test_touchcancel_entwertet_die_geste(index_html):
    assert "onTouchCancel:e=>{touch.current.ok=false;}" in index_html, (
        "onTouchCancel-Handler fehlt — eine vom Browser abgebrochene Geste "
        "bliebe als gueltig stehen (v834-Befund: touchcancel statt touchend)."
    )


def test_touchcancel_wird_auch_zurueckgegeben(index_html):
    """Ein Handler, der nicht im Rueckgabeobjekt steht, wird nie gespreadet —
    genau die Falle aus v3.9.200 (Hook definiert, Callsite sieht ihn nie)."""
    m = re.search(r"return \{onTouchStart:handlers\.onTouchStart.*?\};", index_html)
    assert m, "Rueckgabeobjekt von useSwipe nicht gefunden"
    assert "onTouchCancel:handlers.onTouchCancel" in m.group(0), (
        "onTouchCancel fehlt im Rueckgabeobjekt — der Handler existiert dann "
        "zwar, erreicht aber keine Callsite:\n" + m.group(0)
    )


# ── Bewusst behalten ─────────────────────────────────────────────────────────

def test_input_textarea_und_no_swipe_bleiben_geskippt(index_html):
    expr = _skip_expr(index_html)
    for token in ("input", "textarea", "[data-no-swipe]"):
        assert token in expr, (
            f"{token} aus der Skip-Liste verschwunden — dort ist Querziehen "
            f"Caret/Textauswahl/Slider bzw. der Plan-Viewer:\n" + expr
        )


def test_touch_action_none_bleibt_skip_grund(index_html):
    expr = _skip_expr(index_html)
    assert "touchAction: none" in expr and "touch-action:none" in expr, (
        "Die touch-action:none-Ausnahme ist weg (Plan-Viewer pan/zoom):\n" + expr
    )


# ── Umkehrprobe: die Asserts greifen wirklich ────────────────────────────────

def test_selbsttest_asserts_schlagen_bei_rueckbau_an(index_html):
    """Ein gruener Test, der auch bei kaputtem Code gruen bliebe, ist wertlos
    (Repo-Lektion: vier Riegel waren gruen und massen nichts). Hier wird der
    alte Stand rekonstruiert und geprueft, dass die Riegel dann ROT werden."""
    alt = index_html.replace(
        'el.closest("input,textarea,[data-no-swipe]")||_swScrollableX(el,e.currentTarget)',
        'el.closest("input,textarea,select,table,[data-no-swipe]")',
    )
    assert alt != index_html, "Rueckbau griff nicht — Anker veraltet"

    expr_alt = _skip_expr(alt)
    assert "select" in expr_alt, "Umkehrprobe: select-Riegel wuerde nicht anschlagen"
    assert "table" in expr_alt, "Umkehrprobe: table-Riegel wuerde nicht anschlagen"
    assert "_swScrollableX(el,e.currentTarget)" not in expr_alt, (
        "Umkehrprobe: Scrollbarkeits-Riegel wuerde nicht anschlagen"
    )

    ohne_cancel = index_html.replace("onTouchCancel:handlers.onTouchCancel,", "")
    m = re.search(r"return \{onTouchStart:handlers\.onTouchStart.*?\};", ohne_cancel)
    assert m and "onTouchCancel" not in m.group(0), (
        "Umkehrprobe: der Rueckgabe-Riegel wuerde nicht anschlagen"
    )
