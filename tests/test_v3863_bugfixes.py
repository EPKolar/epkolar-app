"""v3.8.63 Bugfix-Tests (Live-Audit Sa 26.04.2026 ~07:00 UTC nach v3.8.62-Push)."""
import re
from pathlib import Path
INDEX = Path(__file__).parent.parent / 'index.html'


# ═══ Bug-A: Banner-Hide echter Fix ═══

def test_swUpdate_useState_initializer_checks_localStorage():
    """useState-Initializer muss localStorage gegen window.SW_VER checken (kein blind false)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'\[swUpdate,setSwUpdate\]\s*=\s*_react\.useState\.call\([^,]+,\s*\(\)=>\s*\{([\s\S]{0,400}?)\}\s*\)', text)
    assert m, 'swUpdate-useState-Initializer (function form) nicht gefunden'
    body = m.group(1)
    assert 'epk_sw_ver' in body, 'Initializer muss localStorage.epk_sw_ver lesen'
    assert 'window.SW_VER' in body, 'Initializer muss window.SW_VER referenzieren'


def test_setSwUpdate_in_statechange_handler_fires_on_update():
    """v3.9.209 FIX: _stateChangeHandler ruft setSwUpdate(true) bei ECHTEM Update (installed+controller).
    Der frühere _stored===window.SW_VER-Guard wurde ENTFERNT — bei stale-SW war stored===geladene Version
    → Banner dauerhaft unterdrückt → Geräte hingen auf alter Version (kritischer Update-Bug)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_stateChangeHandler\s*=\s*\(\s*\)\s*=>\s*\{([\s\S]{0,500}?setSwUpdate\(true\))', text)
    assert m, '_stateChangeHandler-Body mit setSwUpdate(true) nicht gefunden'
    body = m.group(0)
    assert 'nw.state==="installed"' in body and 'navigator.serviceWorker.controller' in body, \
        'muss auf echtes neues SW (state installed + vorhandener controller) prüfen'
    assert '_stored===window.SW_VER' not in body, \
        'fehlerhafter Over-Suppress-Guard muss entfernt sein (v3.9.209)'


def test_setSwUpdate_in_msg_handler_fires_on_update():
    """v3.9.209 FIX: SW_UPDATED-Handler ruft setSwUpdate(true) OHNE den fehlerhaften _stored===SW_VER-Guard."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'SW_UPDATED[\s\S]{0,300}?setSwUpdate\(true\)', text)
    assert m, 'SW_UPDATED-Handler mit setSwUpdate(true) nicht gefunden'
    body = m.group(0)
    assert '_stored===window.SW_VER' not in body, \
        'fehlerhafter Over-Suppress-Guard muss entfernt sein (v3.9.209)'


# ═══ Bug-B: u1 → Name Resolve ═══

def test_pendingDetails_uses_users_lookup():
    """pendingDetails-Builder muss users (nicht nur monteure) für worker_id-Lookup nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r'_pendingByMonth\s*=\s*\{\}[\s\S]{0,800}?pendingDetails\s*=', text)
    assert m, 'pendingDetails-Builder nicht gefunden'
    body = m.group(0)
    assert '(users||[]).find' in body or 'users.find' in body, \
        'pendingDetails-Builder muss users.find als Lookup nutzen (finkzeit.worker_id ist users-PK)'


def test_no_raw_user_id_in_bestellt_von():
    """Material-Bestellung 'von:' muss window._allUsers Lookup nutzen."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche bestellt_von-Render-Pattern
    m = re.search(r'so\.bestellt_von&&React\.createElement[\s\S]{0,300}?von:[\s\S]{0,200}?\)', text)
    assert m, 'bestellt_von-Render nicht gefunden'
    body = m.group(0)
    assert 'window._allUsers' in body or '_allUsers' in body, \
        'bestellt_von-Display muss Lookup statt rohem User-PK haben'


# ═══ Bug-C: Kontrast Mode-Pills + V.fg ═══

def test_no_V_fg_color_usage():
    """V.fg ist UNDEFINED im V-Theme — darf nirgendwo als color verwendet werden."""
    text = INDEX.read_text(encoding='utf-8')
    matches = re.findall(r'color:\s*V\.fg\b', text)
    assert len(matches) == 0, f'V.fg ist undefined, {len(matches)} Stellen müssen auf V.tx umgestellt sein'


def test_urlaub_mode_pills_use_V_tx():
    """Mode-Toggle-Pills (Urlaub/Krankenstand/Zeitausgleich) inactive nutzt V.tx (nicht V.fg/V.dm)."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche nach AT_T-Filter-Block mit "urlaub|krank|za" Filter, dann color-typ-Pattern
    m = re.search(r'AT_T[\s\S]{0,300}?v\.kat==="za"[\s\S]{0,800}?color:typ===k\?v\.c:(V\.\w+)', text)
    assert m, 'Mode-Pills-Pattern (AT_T+urlaub/krank/za + color:typ===k?v.c:V.X) nicht gefunden'
    assert m.group(1) == 'V.tx', f'Mode-Pills inactive muss color:V.tx sein, ist: {m.group(1)}'


# ═══ Bug-D: IndexedDB graceful degradation ═══

def test_odb_has_store_helper_exists():
    """_odbHasStore Helper muss existieren."""
    text = INDEX.read_text(encoding='utf-8')
    assert 'function _odbHasStore' in text, '_odbHasStore-Helper fehlt'


def test_odb_methods_use_existence_check():
    """ODB.get/set/del/getAll/clear muessen _odbHasStore checken."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche ODB-Object und prüfe auf _odbHasStore-Calls
    m = re.search(r'const ODB\s*=\s*\{[\s\S]{0,3000}?\};', text)
    assert m, 'ODB-Object nicht gefunden'
    body = m.group(0)
    # Min. 5 _odbHasStore-Calls (1 pro CRUD-Method)
    matches = re.findall(r'_odbHasStore', body)
    assert len(matches) >= 5, f'Min. 5 _odbHasStore-Checks erwartet, gefunden: {len(matches)}'


def test_odb_getAll_returns_empty_array_on_missing_store():
    """ODB.getAll muss [] (Array) zurückgeben wenn store fehlt — nicht undefined (Caller iteriert)."""
    text = INDEX.read_text(encoding='utf-8')
    m = re.search(r"async getAll\(store\)\{[\s\S]{0,400}?_odbHasStore[\s\S]{0,200}?return\s+(\[\]|undefined)", text)
    assert m, 'ODB.getAll graceful-degradation nicht gefunden'
    assert m.group(1) == '[]', f'ODB.getAll muss [] zurückgeben (für .map/.filter-Caller), nicht {m.group(1)}'
