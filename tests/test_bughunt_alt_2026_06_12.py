"""Regression-Tests fuer Bug-Hunt-Befunde 2026-06-12 (v3.9.325-328).

Verhindert dass die Modal-Migration-Luecken erneut entstehen — gerade die
destruktiven Handler haben sich offenbar seit v3.9.11 (Round-3) durch Refactors
unbemerkt zurueck-mutiert.
"""
import re


# v3.9.325 — Wochenplanung clearRow + delRow ---------------------------------

def test_wochenplanung_clearRow_uses_confirmModal(index_html):
    """clearRow muss async sein + _confirmModal-Aufruf enthalten."""
    m = re.search(
        r"const\s+clearRow\s*=\s*async\s*\(id\)\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "clearRow ohne async/_confirmModal — Bug-Regression v3.9.325"


def test_wochenplanung_delRow_uses_confirmModal_danger(index_html):
    """delRow muss async + _confirmModal mit danger-Variant."""
    m = re.search(
        r"const\s+delRow\s*=\s*async\s*\(id\)\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "delRow ohne async/_confirmModal — Bug-Regression v3.9.325"
    # Block fuer die n-Zeichen nach delRow grep
    blob = index_html[m.start():m.start()+400]
    assert 'variant:"danger"' in blob, "delRow _confirmModal sollte danger-Variant haben"


# v3.9.326 — Urlaubsplanung approve + reject ---------------------------------

def test_urlaub_approve_has_admin_guard_and_modal(index_html):
    """approve(m,d) muss async sein + isAdmin-Handler-Guard + _confirmModal."""
    m = re.search(
        r"const\s+approve\s*=\s*async\s*\(m,\s*d\)\s*=>\s*\{[\s\S]{0,400}?_confirmModal\(",
        index_html,
    )
    assert m, "approve ohne async/_confirmModal — Bug-Regression v3.9.326"
    blob = index_html[m.start():m.start()+400]
    assert "if(!isAdmin)return" in blob, "approve braucht Handler-Eingangs-Guard if(!isAdmin)return"


def test_urlaub_reject_has_admin_guard_and_modal_danger(index_html):
    """reject(m,d) muss async + isAdmin-Guard + _confirmModal mit danger."""
    m = re.search(
        r"const\s+reject\s*=\s*async\s*\(m,\s*d\)\s*=>\s*\{[\s\S]{0,400}?_confirmModal\(",
        index_html,
    )
    assert m, "reject ohne async/_confirmModal — Bug-Regression v3.9.326"
    blob = index_html[m.start():m.start()+500]
    assert "if(!isAdmin)return" in blob, "reject braucht Handler-Eingangs-Guard"
    assert 'variant:"danger"' in blob, "reject _confirmModal sollte danger-Variant haben"


# v3.9.327 — Notifs deleteNotif + Alle-loeschen ------------------------------

def test_deleteNotif_uses_confirmModal(index_html):
    """deleteNotif muss async sein + _confirmModal mit danger."""
    m = re.search(
        r"const\s+deleteNotif\s*=\s*async\s+id\s*=>\s*\{[\s\S]{0,200}?_confirmModal\(",
        index_html,
    )
    assert m, "deleteNotif ohne async/_confirmModal — Bug-Regression v3.9.327"
    blob = index_html[m.start():m.start()+400]
    assert 'variant:"danger"' in blob, "deleteNotif sollte danger-Variant haben"


def test_notifs_clear_all_button_uses_confirmModal(index_html):
    """Inline-onClick fuer 'Alle Benachrichtigungen löschen' muss _confirmModal nutzen.

    Pattern: title:'Alle Benachrichtigungen löschen' → onClick: async ()=>{... _confirmModal ...}
    """
    # Suche das Inline-onClick mit "notifications/clear" — dort muss _confirmModal davor stehen
    m = re.search(
        r"onClick:\s*async\s*\(\)\s*=>\s*\{\s*if\(!await\s+_confirmModal\([\s\S]{0,700}?notifications/clear",
        index_html,
    )
    assert m, "Alle-loeschen-Notifs-Button ohne _confirmModal — Bug-Regression v3.9.327"


# v3.9.328 — Material deleteSuppOrd + deleteCatalog --------------------------

def test_deleteSuppOrd_render_has_canDo_guard(index_html):
    """deleteSuppOrd-Render-Button muss canDo('material_delete')-gated sein."""
    # Pattern: canDo("material_delete",curUser)&&React.createElement('button', { onClick: ()=>deleteSuppOrd
    m = re.search(
        r'canDo\("material_delete",curUser\)\s*&&React\.createElement\(\'button\',\s*\{\s*onClick:\s*\(\)=>deleteSuppOrd',
        index_html,
    )
    assert m, "deleteSuppOrd-Render ohne canDo-Guard — Bug-Regression v3.9.328"


def test_deleteCatalog_handler_has_canDo_guard(index_html):
    """deleteCatalog-Handler muss als ERSTES canDo('material_delete') pruefen."""
    m = re.search(
        r'const\s+deleteCatalog\s*=\s*async\s*\(catId\)\s*=>\s*\{[\s\S]{0,300}?if\(!canDo\("material_delete",curUser\)\)',
        index_html,
    )
    assert m, "deleteCatalog-Handler ohne canDo-Eingangs-Guard — Bug-Regression v3.9.328"


def test_deleteCatalog_render_has_canDo_guard(index_html):
    """deleteCatalog-Render-Button muss canDo-gated sein."""
    m = re.search(
        r'canDo\("material_delete",curUser\)\s*&&React\.createElement\(\'button\',\s*\{\s*onClick:\s*\(\)=>deleteCatalog',
        index_html,
    )
    assert m, "deleteCatalog-Render ohne canDo-Guard — Bug-Regression v3.9.328"


# Hygiene: Logout-Warning + AS-Duplikat sind dokumentierte legacy native-confirm-Stellen.
# Werden bewusst NICHT durch Heuristik geguarded (BUGHUNT_ALT_2026-06-12.md fuer Detail).
