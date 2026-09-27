"""v3.8.59: tickets-Schema bleibt x/y (Pixel) — Component konvertiert beim Render.

v3.9.961: `test_no_xPct_yPct_write_to_tickets` war der ZWEITE Fall mit dem
Befund "Schleife ueber leerer Menge, NULL Zusicherungen, gruen"
(docs/befunde/WAS_LAEUFT_WIRKLICH.md §2 B2) — woertlich dieselben vier Zeilen
wie in tests/test_db_schema_assumptions.py, mit demselben bruechigen
`[^)]+`-Muster.

Der Auszieher liegt jetzt EINMAL in test_db_schema_assumptions.py und wird von
hier importiert. Zwei Kopien waeren zwei Rechnungen — und die eine, die man
beim Reparieren vergisst, ist genau die, die weiter nichts misst. Die
ZUSICHERUNGEN bleiben in dieser Datei, damit dieser Fall sein eigenes Urteil
faellt und eigene Koeder traegt.
"""
import os
import sys
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_db_schema_assumptions import (  # noqa: E402
    KOEDER_GRUEN,
    KOEDER_ROT,
    _MIND_AUFRUFE,
    sbpatch_aufrufe,
    spaltenschreiber,
)

_SPALTEN = ("xPct", "yPct")


def test_no_xPct_yPct_write_to_tickets():
    """tickets-DB hat keine xPct/yPct-Spalten; PostgREST verwirft still.

    Erst die Grundgesamtheit belegen, dann die Abwesenheit behaupten.
    """
    text = INDEX.read_text(encoding='utf-8')
    rufe = sbpatch_aufrufe(text)
    assert len(rufe) >= _MIND_AUFRUFE, (
        'Nur %d _sbPatch-Aufrufe im Code (erwartet >=%d) — dieser Riegel '
        'urteilt sonst ueber eine leere Menge und meldet gruen, ohne zu '
        'messen.' % (len(rufe), _MIND_AUFRUFE))
    assert 'fahrzeuge' in {t for _, t, _ in rufe}, (
        'Der Auszieher liest keine Tabellennamen mehr — dann koennte er auch '
        '"tickets" nicht erkennen.')
    verstoesse = spaltenschreiber(text, 'tickets', _SPALTEN)
    assert not verstoesse, (
        '_sbPatch schreibt xPct/yPct auf tickets. Fundstellen: %r'
        % (verstoesse,))


def test_koeder_dieser_riegel_findet_jede_schreibweise():
    """Eigener Koeder-Nachweis fuer DIESEN Fall — nicht geliehen."""
    assert len(KOEDER_ROT) >= 11, 'Koederliste ausgeduennt'
    for name, probe in KOEDER_ROT:
        assert spaltenschreiber(probe, 'tickets', _SPALTEN), (
            'KOEDER NICHT GEFUNDEN (%s): %r' % (name, probe))


def test_gegenprobe_dieser_riegel_meldet_nichts_falsches():
    assert len(KOEDER_GRUEN) >= 10, 'Gegenprobenliste ausgeduennt'
    for name, probe in KOEDER_GRUEN:
        assert not spaltenschreiber(probe, 'tickets', _SPALTEN), (
            'FEHLALARM (%s): %r' % (name, probe))

def test_pin_render_uses_x_y():
    text = INDEX.read_text(encoding='utf-8')
    assert 't.x != null' in text or 't.x !== null' in text
