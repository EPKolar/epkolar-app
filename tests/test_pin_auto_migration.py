"""v3.8.57: Pin Auto-Migration on Edit (Pixel → %)."""
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'

def test_onPinClick_has_migration_logic():
    text = INDEX.read_text(encoding='utf-8')
    # Migration: when xPct null and x not null, push xPct to server
    assert '_sbPatch' in text  # patch-call existiert
    # Pattern: t.xPct == null
    assert 'xPct == null' in text or 'xPct == undefined' in text

def test_migration_uses_pageDims():
    text = INDEX.read_text(encoding='utf-8')
    assert 'pageDims.baseWidth' in text, 'Migration braucht pageDims für Pixel-zu-%-Konversion'

def test_migration_pushes_to_tickets_table():
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbPatch('tickets'" in text or '_sbPatch("tickets"' in text, 'Migration muss tickets-Tabelle patchen'
