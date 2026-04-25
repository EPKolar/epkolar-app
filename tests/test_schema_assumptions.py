"""v3.8.57: Schema-Annahmen-Tests. Verhindert dass Code-Pattern und DB-Schema auseinanderlaufen.

Lehre 25.04.2026: plans.file_url existiert in DB, Component erwartete plan.dataUrl —
PDF-Plans rendern nicht, Sebastian sah leere Flaeche. Diese Test-Suite codifiziert
die zwei wichtigsten Schema-Annahmen.

Note: Eine ursprueglich geplante 'no-camelcase-DB-column'-Assertion wurde entfernt,
weil der Code intern camelCase (naechstService, terminBestaetigt) als Form-State
verwendet und _toSnake/_mapBody bei Server-Calls konvertiert — 75 legitime
camelCase-Treffer existieren. Statt Verbot pruefen wir positiv die Existenz
des Mappers.
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_camelcase_to_snakecase_mapper_exists():
    """_toSnake + _mapBody muessen existieren — sie konvertieren camelCase-Frontend-Form-State
    zu snake_case-DB-Spalten beim Server-Push (verhindert das urspruengliche file_url-Symptom
    fuer alle anderen camelCase-Felder)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'function _toSnake' in text, '_toSnake-Helper muss existieren'
    assert 'function _mapBody' in text, '_mapBody-Helper muss existieren'


def test_plans_table_uses_correct_name():
    """Verhindert plaene-Tabellen-Aufruf (gibt's nicht — DB-Tabelle heisst 'plans')."""
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbGet('plaene'" not in text, "Tabelle 'plaene' existiert nicht — DB-Tabelle heisst 'plans'"
    assert '_sbGet("plaene"' not in text, "Tabelle 'plaene' existiert nicht — DB-Tabelle heisst 'plans'"


def test_planviewer_handles_file_url_schema():
    """Lehre 25.04: PlanViewerCanvas muss file_url als Fallback haben (nicht nur dataUrl)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m, '_planSrc-Resolver muss existieren'
    assert 'file_url' in m.group(1), '_planSrc muss file_url-Fallback enthalten'


def test_planLoadPdf_handles_storage_url():
    """_planLoadPdf muss https-URLs (Supabase Storage) akzeptieren."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planLoadPdf[\s\S]{0,1500}?pdfjsLib\.getDocument', text)
    assert m, '_planLoadPdf-Body nicht gefunden'
    body = m.group(0)
    assert 'http:' in body or 'https:' in body, '_planLoadPdf muss http(s):-URL akzeptieren'
