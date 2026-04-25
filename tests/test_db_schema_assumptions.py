"""v3.8.61 MEGA-C Phase 7.1: DB-Schema-Annahmen.

Verhindert Schema-Drift-Bugs wie v3.8.55→56 (file_url) und v3.8.57→59
(xPct/yPct/page silent fail). Statische Tests gegen index.html-Patterns.
"""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


def test_AS_GRP_OFFEN_includes_underscore_variant():
    """Lehre v3.8.55: scheinstatus="in_bearbeitung" (snake) muss matchen."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'AS_GRP_OFFEN\s*=\s*\[([^\]]+)\]', text)
    assert m, 'AS_GRP_OFFEN nicht gefunden'
    assert 'in_bearbeitung' in m.group(1)


def test_no_plaene_table_call():
    """plaene-Tabelle existiert nicht — DB-Tabelle heisst 'plans'."""
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbGet('plaene'" not in text
    assert '_sbGet("plaene"' not in text


def test_no_projekte_table_call():
    """projekte-Tabelle existiert nicht — DB-Tabelle heisst 'projects'."""
    text = INDEX.read_text(encoding='utf-8')
    assert "_sbGet('projekte'" not in text
    assert '_sbGet("projekte"' not in text


def test_no_xPct_yPct_in_tickets_patch():
    """v3.8.59 Schema-Reality: tickets-DB hat KEINE xPct/yPct-Spalten."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}", text)
    for m in matches:
        assert 'xPct' not in m, f"_sbPatch tickets darf kein xPct schreiben: {m[:100]}"
        assert 'yPct' not in m, f"_sbPatch tickets darf kein yPct schreiben: {m[:100]}"


def test_projects_table_used_via_sbGet():
    """projects-Tabelle existiert (3 Rows DB-verifiziert) — Code muss sie nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_sbGet\(\s*[\'"]projects[\'"]', text)
    assert len(matches) >= 1, f'projects-Tabelle muss via _sbGet aufgerufen werden, gefunden: {len(matches)}'


def test_plans_table_used_via_sbGet():
    """plans-Tabelle existiert (1 Row DB-verifiziert) — Code muss sie nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'_sbGet\(\s*[\'"]plans[\'"]', text)
    assert len(matches) >= 1, 'plans-Tabelle muss via _sbGet aufgerufen werden'


def test_finkzeit_worker_id_has_lookup_not_raw():
    """finkzeit pendingDetails muss Worker-Name-Lookup machen (nicht raw u1/w1 anzeigen).
    Akzeptiert monteure.find ODER users.find ODER window._allUsers — Lookup-Quelle ist
    aktuell monteure (Workers w1-w9), kann später auf users (u1-u9) umgestellt werden
    falls Reminder-Plan-Block-2 noch implementiert wird."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_pendingByMonth\s*=\s*\{\}[\s\S]{0,800}pendingDetails\s*=', text)
    assert m, 'pendingDetails-Builder nicht gefunden'
    body = m.group(0)
    has_lookup = 'monteure.find' in body or 'users.find' in body or 'window._allUsers' in body or 'usersMap' in body
    assert has_lookup, 'Lookup muss aus monteure/users sein, nicht raw worker_id-Display'


def test_camelcase_to_snakecase_mapper_exists():
    """_toSnake + _mapBody muessen existieren (camelCase-Frontend → snake_case-DB)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'function _toSnake' in text
    assert 'function _mapBody' in text


def test_planSrc_resolver_handles_file_url():
    """v3.8.56 Lehre: PlanViewerCanvas muss file_url als Fallback haben."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_planSrc\s*=\s*([^;]+);', text)
    assert m
    assert 'file_url' in m.group(1)


def test_planLoadPdf_handles_storage_url():
    """_planLoadPdf muss https-URLs (Supabase Storage) akzeptieren."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planLoadPdf[\s\S]{0,1500}?pdfjsLib\.getDocument', text)
    assert m
    assert 'http:' in m.group(0) or 'https:' in m.group(0)
