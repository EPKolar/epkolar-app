"""
Swipe-Navigation im Browser (nicht nur standalone) — touch-action-Guard.

BUG (User-Report 21.08.2026): In der PWA im BROWSER geht kein Wischen mehr;
als installierte (standalone) App geht es. Ursache: der useSwipe-Hook faengt
horizontale Wische ueber onTouchStart/onTouchEnd, tut aber KEIN preventDefault.
Ohne `touch-action: pan-y` auf dem Wisch-Container behandelt der Browser die
horizontale Geste selbst (Page-Scroll / History-Navigation) und der Hook sieht
nie eine saubere Geste. Standalone gibt es diese konkurrierenden Browser-Gesten
nicht -> dort funktioniert derselbe Code.

`.main-pad` bekam den Fix schon in v3.9.313 (CSS: touch-action:pan-y, mit genau
dieser Begruendung im Kommentar). Die beiden anderen useSwipe-Flaechen
(shellSwipe = Projekt-interne Navigation, absSwipe = Urlaubs-Tabs) blieben ohne
-> genau die brechen im Browser.

Invariante: JEDE Flaeche, die ein useSwipe-Handlerset spreadet, muss die
horizontale Browser-Geste per touch-action:pan-y freigeben (inline touchAction
oder via .main-pad-Klasse, die die Regel in CSS traegt).
"""
import re

# Alle useSwipe-Callsites liefern Variablen, die per {...var} auf den
# Wisch-Container gespreadet werden. Diese Namen sind die horizontalen Wische.
SWIPE_SPREADS = ["mainSwipe", "shellSwipe", "absSwipe", "navSwipe", "shellNavSwipe"]
# v3.9.869: navSwipe kam dazu — die fixe .bottom-nav liegt im Hochformat ueber den
# untersten ~58px und ist KEIN Kind von .main-pad. Ein Wisch dort erreichte den Hook
# nie ("quer geht wischen, hoch nicht"). Sie ist damit eine vollwertige Wisch-Flaeche
# und faellt unter dieselbe touch-action-Invariante.


def _props_object_for_spread(index_html, spread_name):
    """Liefert das createElement-Props-Objekt (der {...}-Block), in dem
    `...spread_name` steht — von der oeffnenden `{` vor dem Spread bis zur
    passenden schliessenden `}`."""
    marker = "..." + spread_name
    idx = index_html.find(marker)
    assert idx != -1, f"Spread ...{spread_name} nicht gefunden"
    # Ruecklaufen zur oeffnenden Klammer des Props-Objekts
    open_brace = index_html.rfind("{", 0, idx)
    assert open_brace != -1, f"Keine oeffnende Klammer vor ...{spread_name}"
    # Vorwaerts die passende schliessende Klammer suchen
    depth = 0
    i = open_brace
    while i < len(index_html):
        c = index_html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return index_html[open_brace : i + 1]
        i += 1
    raise AssertionError(f"Keine schliessende Klammer fuer ...{spread_name}")


def test_alle_useSwipe_callsites_erfasst(index_html):
    """Regressionsschutz: es gibt genau 3 useSwipe-Callsites (+1 Definition).
    Kommt eine neue Wisch-Flaeche dazu, muss sie hier aufgenommen und mit
    touch-action versehen werden."""
    callsites = len(re.findall(r"useSwipe\(", index_html))
    # v3.9.872: shellNavSwipe kam dazu - die Projekt-Bottom-Nav (.mob-shell-nav) ist
    # wie die Haupt-Bottom-Nav position:fixed und Geschwister des Wisch-Containers,
    # auf dem Handy sogar zweireihig. Ohne eigene Flaeche waere dort die Daumenzone tot.
    assert callsites == 6, (
        f"Erwartet: 1 Definition + 5 Callsites = 6 'useSwipe('; gefunden {callsites}. "
        f"Neue Wisch-Flaeche? SWIPE_SPREADS + touch-action-Guard pruefen."
    )


def test_horizontale_swipe_flaechen_geben_geste_frei(index_html):
    """Jede useSwipe-Flaeche muss die horizontale Browser-Geste per
    touch-action:pan-y freigeben — sonst faengt der Browser sie ab und
    Wischen geht nur standalone, nicht im Browser (der gemeldete Bug)."""
    fehlend = []
    for name in SWIPE_SPREADS:
        props = _props_object_for_spread(index_html, name)
        has_inline = re.search(r'touchAction\s*:\s*["\']pan-y["\']', props) is not None
        has_mainpad = re.search(r'className\s*:\s*["\']main-pad["\']', props) is not None
        if not (has_inline or has_mainpad):
            fehlend.append(name)
    assert not fehlend, (
        "Wisch-Flaeche(n) ohne touch-action:pan-y -> Browser frisst die Geste, "
        f"Wischen geht nur standalone: {fehlend}"
    )
