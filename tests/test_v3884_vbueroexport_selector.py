"""v3.8.84 → v3.9.355 (G1/Variante B): VBueroExport globaler Projekt-Selektor ENTFERNT.

Der redundante Dropdown + globale "Bauwochenbericht herunterladen"-Button wurden in
v3.9.355 entfernt — generateAll und die per-Projekt-Excel-Buttons nutzen denselben
Generator generateBWB (nur anderer Scope). Der globale Download ist jetzt "Alle als
Excel" im Bauwochenberichte-Sektionskopf; per-Projekt-Export über die Projektkarten.
Daher prüft dieser Test jetzt den NEUEN Zustand statt des alten Selektor-Min-Widths.
"""
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_global_alle_als_excel_button_present():
    """G1: globaler 'Alle als Excel'-Button (generateAll) im Bauwochenberichte-Kopf."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'Alle als Excel' in text, (
        "G1: globaler 'Alle als Excel'-Button (generateAll) im Bauwochenberichte-Kopf fehlt."
    )


def test_redundant_global_download_button_removed():
    """G1: der redundante globale 'Bauwochenbericht herunterladen'-Button ist entfernt."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'Bauwochenbericht herunterladen' not in text, (
        "G1: redundanter globaler 'Bauwochenbericht herunterladen'-Button sollte entfernt sein "
        "(generateAll jetzt als 'Alle als Excel' im Sektionskopf)."
    )
