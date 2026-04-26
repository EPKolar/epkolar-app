"""v3.8.64 Mega-Run-Tests (5 Bugs + Performance + Schema + Multi-Page)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'
ROOT = Path(__file__).parent.parent


# ═══ Bug-1: Urlaub Status-Filter ═══

def test_urlaub_status_filter_includes_ausstehend():
    """yearSt muss urlaubStdAusstehend tracken (nicht nur urlaubStdGen)."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'urlaubStdAusstehend' in text, 'urlaubStdAusstehend-Counter muss existieren'
    # resturlaub muss beide abziehen
    m = re.search(r'const resturlaub\s*=\s*m\s*=>[\s\S]{0,400}?urlaubStdGen[\s\S]{0,200}?urlaubStdAusstehend', text)
    assert m, 'resturlaub muss urlaubStdGen UND urlaubStdAusstehend abziehen'


def test_urlaub_filter_excludes_only_abgelehnt():
    """Filter-Logik: !=='abgelehnt' (nicht nur ==='genehmigt')."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche im yearSt-Body
    m = re.search(r'const yearSt\s*=\s*m\s*=>[\s\S]{0,1500}?abgelehnt', text)
    assert m, 'yearSt muss abgelehnt-Filter haben (!== abgelehnt)'


# ═══ Bug-2: AKTUELLE PLÄNE entfernt ═══

def test_no_aktuelle_plaene_section():
    """Dashboard-Sektion 'Aktuelle Pläne' muss entfernt sein."""
    text = INDEX.read_text(encoding='utf-8')
    assert '🗺️ Aktuelle Pläne' not in text, "AKTUELLE PLÄNE-Header darf nicht mehr im Code stehen"


# ═══ Bug-3: ODB urlaubskontingent ═══

def test_urlaubskontingent_in_stores():
    """STORES muss urlaubskontingent enthalten."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const STORES\s*=\s*\[([^\]]+)\]', text)
    assert m, 'STORES nicht gefunden'
    assert 'urlaubskontingent' in m.group(1), 'urlaubskontingent muss in STORES sein'


def test_db_ver_bumped_to_8():
    """DB_VER muss auf 8 sein (war 7) damit onupgradeneeded für existierende User triggert."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'const DB_NAME="epkolar_offline";const DB_VER=(\d+)', text)
    assert m, 'DB_VER nicht gefunden'
    assert int(m.group(1)) >= 8, f'DB_VER muss >= 8 sein für urlaubskontingent-Migration, ist: {m.group(1)}'


# ═══ Bug-4: Notifications PATCH ohne updated_at ═══

def test_notifications_patch_excludes_updated_at():
    """_translateAndExec PATCH-Body muss updated_at für notifications NICHT setzen."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche Pattern: if(table!=="notifications")patchData.updated_at
    m = re.search(r'table\s*!==?\s*[\'"]notifications[\'"][^;]*patchData\.updated_at', text)
    assert m, 'PATCH-Body muss updated_at für notifications excluden (PGRST204-Fix)'


# ═══ Bug-5: PlanViewer renderTask cancel ═══

def test_planRenderPage_cancels_previous():
    """_planRenderPage muss vorherigen render-task cancel'en (canvas._epkRenderTask)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'async function _planRenderPage[\s\S]{0,1500}?\n\}', text)
    assert m, '_planRenderPage nicht gefunden'
    body = m.group(0)
    assert '_epkRenderTask' in body, 'renderTask-Tracking muss existieren'
    assert '.cancel()' in body, 'Cancel des vorherigen Tasks muss existieren'


# ═══ Phase 2: Performance ═══

def test_useMemo_count_grew():
    """useMemo-Calls müssen >= 18 sein nach Phase 2 (war ~12 vorher)."""
    text = INDEX.read_text(encoding='utf-8')
    n = len(re.findall(r'_react\.useMemo\.call', text))
    assert n >= 18, f'Min. 18 useMemo erwartet nach Performance-Audit, gefunden: {n}'


def test_useCallback_count_intact():
    """useCallback-Calls müssen >= 12 sein."""
    text = INDEX.read_text(encoding='utf-8')
    n = len(re.findall(r'_react\.useCallback\.call', text))
    assert n >= 12, f'Min. 12 useCallback erwartet, gefunden: {n}'


# ═══ Phase 3: Schema-Doku ═══

def test_schema_doku_committed():
    """SCHEMA_LIVE_26_04_2026.md muss im Repo-Root liegen + Schlüssel-Tabellen enthalten."""
    p = ROOT / 'SCHEMA_LIVE_26_04_2026.md'
    assert p.exists(), 'SCHEMA_LIVE_26_04_2026.md muss existieren'
    txt = p.read_text(encoding='utf-8')
    for tbl in ['notifications', 'urlaubskontingent', 'finkzeit', 'arbeitsscheine', 'tickets']:
        assert tbl in txt, f'Schema-Doku muss {tbl}-Eintrag haben'


# ═══ Phase 4: Multi-Page ═══

def test_b034_sql_file_exists():
    """sql/B034_tickets_page_column.sql muss existieren."""
    p = ROOT / 'sql' / 'B034_tickets_page_column.sql'
    assert p.exists(), 'sql/B034_tickets_page_column.sql muss vorbereitet sein'
    txt = p.read_text(encoding='utf-8')
    assert 'ALTER TABLE tickets' in txt
    assert 'page integer' in txt


def test_planviewer_has_prev_next_buttons():
    """PlanViewerCanvas Toolbar muss Prev/Next-Buttons für Multi-Page haben."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche nach setPageNum-Pattern in Toolbar (◀ / ▶)
    assert 'setPageNum(p => Math.max(1, p-1))' in text, 'Prev-Page-Button (◀) muss existieren'
    assert 'setPageNum(p => Math.min(pageCount, p+1))' in text, 'Next-Page-Button (▶) muss existieren'


def test_pageNum_state_exists():
    """pageNum-State muss in PlanViewerCanvas existieren."""
    text = INDEX.read_text(encoding='utf-8')
    assert '[pageNum, setPageNum]' in text, 'pageNum-State muss existieren'
