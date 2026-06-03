"""Sprint 77 - Extended coverage tests for Sprints 17/32/38/43/46/48/49 + helpers.

Regression-guards + helper-definition coverage for spans previously untested by
test_sprint_helpers.py (Sprint 73). Static-only assertions; no browser/runtime.
"""
import os
import re

import pytest


# ----------------------------- 77.1 Helpers -----------------------------------


def test_log_helper_defined(index_html):
    assert re.search(r"function\s+_log\s*\(\s*level\s*,\s*component\s*\)", index_html), \
        "_log(level,component) helper missing"


def test_log_levels_constant(index_html):
    assert re.search(
        r"const\s+_LOG_LEVELS\s*=\s*\{\s*debug\s*:\s*0\s*,\s*info\s*:\s*1\s*,\s*warn\s*:\s*2\s*,\s*error\s*:\s*3\s*\}",
        index_html,
    ), "_LOG_LEVELS constant must define debug/info/warn/error -> 0..3"


def test_log_exposed_on_window(index_html):
    assert "window._log=_log" in index_html, "_log must be exposed on window"


def test_log_set_log_level_helper(index_html):
    assert "window._setLogLevel=function" in index_html, \
        "window._setLogLevel must be defined"


def test_log_threshold_default_is_info(index_html):
    m = re.search(r"let\s+_LOG_THRESHOLD\s*=.*?info.*", index_html)
    assert m, "_LOG_THRESHOLD default must be 'info'"


def test_log_uses_correct_console_fn(index_html):
    body_m = re.search(r"function\s+_log\s*\([^)]*\)\s*\{(.*?)\n\}", index_html, re.S)
    assert body_m, "_log body not extractable"
    body = body_m.group(1)
    assert "console.error" in body, "_log must route 'error' to console.error"
    assert "console.warn" in body, "_log must route 'warn' to console.warn"
    assert "console.log" in body, "_log must route default to console.log"


def test_safesessionset_defined(index_html):
    assert re.search(r"function\s+_safeSessionSet\s*\(\s*key\s*,\s*val\s*\)", index_html), \
        "_safeSessionSet(key,val) helper missing"


def _ss_line(index_html):
    return next(
        (ln for ln in index_html.splitlines() if "function _safeSessionSet(key,val)" in ln),
        "",
    )


def test_safesessionset_uses_try_catch(index_html):
    line = _ss_line(index_html)
    assert line, "_safeSessionSet line not found"
    assert "try" in line and "catch" in line, \
        "_safeSessionSet must wrap sessionStorage in try/catch"
    assert "sessionStorage.setItem" in line, \
        "_safeSessionSet must call sessionStorage.setItem"


def test_safesessionset_returns_bool(index_html):
    line = _ss_line(index_html)
    assert line, "_safeSessionSet line not found"
    assert "return true" in line, "_safeSessionSet must return true on success"
    assert "return false" in line, "_safeSessionSet must return false on quota/exception"


def test_canHover_defined_as_iife(index_html):
    assert re.search(r"const\s+_canHover\s*=", index_html), "_canHover constant missing"
    line = next((ln for ln in index_html.splitlines() if "const _canHover=" in ln), "")
    assert line, "_canHover definition line not found"
    assert "matchMedia" in line, "_canHover must use window.matchMedia"
    assert "hover: hover" in line or "hover:hover" in line, \
        "_canHover must query (hover: hover) media feature"
    assert "try" in line and "catch" in line, "_canHover must be safe (try/catch)"


def test_canHover_fallback_uses_mobile_check(index_html):
    line = next((ln for ln in index_html.splitlines() if "const _canHover=" in ln), "")
    assert "_isMobileDevice" in line, \
        "_canHover catch-branch must fall back to !_isMobileDevice"


def test_visibleAS_useMemo_present(index_html):
    assert "const _visibleAS=" in index_html, "_visibleAS useMemo missing"
    line = next((ln for ln in index_html.splitlines() if "const _visibleAS=" in ln), "")
    assert "useMemo" in line, "_visibleAS must use useMemo"
    assert "_hvIsField" in line, "_visibleAS must check _hvIsField (monteur role)"
    assert "_hvMid" in line, "_visibleAS must filter by monteurId (_hvMid)"
    assert "arbeitsscheine.filter" in line, "_visibleAS must filter arbeitsscheine"


def test_visibleAS_monteur_filter_exact(index_html):
    line = next((ln for ln in index_html.splitlines() if "const _visibleAS=" in ln), "")
    assert "a.monteur===_hvMid" in line, \
        "_visibleAS filter must match monteur===_hvMid exactly"


def test_vmIsField_defined(index_html):
    assert "const _vmIsField=" in index_html, "_vmIsField missing"
    line = next((ln for ln in index_html.splitlines() if "const _vmIsField=" in ln), "")
    assert "isAdmin" in line, "_vmIsField must consider isAdmin"
    assert "monteur" in line, "_vmIsField must check 'monteur' role"


def test_vpMid_defined(index_html):
    assert "const _vpMid=" in index_html, "_vpMid missing"
    line = next((ln for ln in index_html.splitlines() if "const _vpMid=" in ln), "")
    assert "monteurId" in line, "_vpMid must read curUser.monteurId"


def test_vzMid_defined(index_html):
    assert "const _vzMid=" in index_html, "_vzMid missing"
    line = next((ln for ln in index_html.splitlines() if "const _vzMid=" in ln), "")
    assert "monteurId" in line, "_vzMid must read curUser.monteurId"


def test_pickerlstatus_warn_threshold_parameter(index_html):
    line = next((ln for ln in index_html.splitlines() if "window._pickerlStatus=" in ln), "")
    assert line, "_pickerlStatus line not found"
    assert "warnDays" in line, "_pickerlStatus must accept warnDays parameter"


def test_pickerlstatus_handles_invalid_date(index_html):
    line = next((ln for ln in index_html.splitlines() if "window._pickerlStatus=" in ln), "")
    assert "isNaN" in line or "return null" in line, \
        "_pickerlStatus must guard invalid dates -> return null"


# -------------------- 77.2 Regression-Tests critical bugs --------------------


# Sprint-82 v3.9.101 Sebastian-Variante-B: Mein-Tag-Kachel KOMPLETT entfernt für alle Rollen.
# Die 4 vorherigen Sprint-17 H-1 + Sprint-32 H-9 Regressions-Tests assertierten Subjekte des
# Timer-/Material-Buttons in der Mein-Tag-Kachel. Diese Kachel existiert nicht mehr; die Tests
# werden nun zu Removal-Guards umgedreht. Funktionen bleiben in Zeiterfassung/Material-Tabs.


def test_sprint82_mein_tag_kachel_removed(index_html):
    """Sprint-82: Mein-Tag-Kachel KOMPLETT entfernt (Sebastian-Variante-B v3.9.101)."""
    # Genaue JS-Identifier-Pattern (Kommentar-Erwähnungen im Marker erlaubt).
    assert "const _isMonteurView=" not in index_html, \
        "Sprint-82: _isMonteurView const-Deklaration muss entfernt sein"
    assert "const _myAgg=" not in index_html, \
        "Sprint-82: _myAgg useMemo-Deklaration muss entfernt sein"
    assert "Sprint-82 Sebastian-Variante-B" in index_html, \
        "Sprint-82: Marker-Kommentar muss bleiben (Regression-Anker)"


def test_sprint82_mein_tag_timer_button_removed(index_html):
    """Sprint-82: Timer-Button + _myProjIdsLocal nur in Mein-Tag-Kachel — beides raus."""
    assert "_myProjIdsLocal" not in index_html, \
        "Sprint-82: _myProjIdsLocal (war im Timer-onClick) muss entfernt sein"
    assert "Timer läuft bereits. Trotzdem ersetzen?" not in index_html, \
        "Sprint-82: Timer-Start-Confirm-Prompt muss entfernt sein"


def test_sprint82_mein_tag_material_button_removed(index_html):
    """Sprint-82: Material-Button + _mtMyProj nur in Mein-Tag-Kachel — beides raus."""
    assert "_mtMyProj" not in index_html, \
        "Sprint-82: _mtMyProj (war im Material-Button-onClick) muss entfernt sein"
    assert "Material anfordern" not in index_html, \
        "Sprint-82: Material-anfordern-Button-Label muss entfernt sein"

def test_sprint32_initView_consumed_in_VProj(index_html):
    assert "p._initView" in index_html, \
        "VProj must read p._initView as initial view state"
    assert re.search(r"p\._initView\s*\|\|\s*\"dashboard\"", index_html), \
        "p._initView must fallback to 'dashboard'"



def test_sprint38_sync_button_drain_refresh(index_html):
    assert "if(_dr&&_dr.drained>0)" in index_html, \
        "Sprint-38: post-drain fresh-pull guard missing"
    m = re.search(
        r"if\(_dr&&_dr\.drained>0\)\s*\{[^}]*?_sbGet\(\"arbeitsscheine\"\)",
        index_html, re.S,
    )
    assert m, "Sprint-38: post-drain block must call _sbGet('arbeitsscheine')"


def test_sprint38_sync_button_setArbeitsscheine_after_pull(index_html):
    m = re.search(
        r"if\(_dr&&_dr\.drained>0\)\s*\{(.{0,600}?)\}",
        index_html, re.S,
    )
    assert m, "Sprint-38: post-drain block not extractable"
    block = m.group(1)
    assert "setArbeitsscheine" in block, \
        "Sprint-38: post-drain block must call setArbeitsscheine"
    assert "_mapArbeitsschein" in block, \
        "Sprint-38: post-drain must map rows via _mapArbeitsschein"


def test_bug1_urlaub_carry_over_subtracts_pending(index_html):
    # resturlaub is a single-line arrow with nested object literal; grab the full
    # line containing "const resturlaub=" instead of regex-extracting.
    line = next(
        (ln for ln in index_html.splitlines() if "const resturlaub=" in ln),
        "",
    )
    assert line, "resturlaub helper missing"
    assert "urlaubStdGen" in line, "resturlaub must subtract urlaubStdGen (genehmigt)"
    assert "urlaubStdAusstehend" in line, \
        "Bug-1: resturlaub must subtract urlaubStdAusstehend (pending)"
    # Verify subtraction operators (not added)
    assert "-ys.urlaubStdGen" in line, "resturlaub must SUBTRACT urlaubStdGen"
    assert "-(ys.urlaubStdAusstehend" in line or "-ys.urlaubStdAusstehend" in line, \
        "Bug-1: resturlaub must SUBTRACT urlaubStdAusstehend"


def test_bug1_urlaub_yearSt_tracks_pending_separately(index_html):
    assert "urlaubAusstehend" in index_html, "urlaubAusstehend counter missing"
    assert "urlaubStdAusstehend" in index_html, "urlaubStdAusstehend counter missing"
    assert "urlaubGenehmigt" in index_html, "urlaubGenehmigt counter missing"
    assert "urlaubStdGen" in index_html, "urlaubStdGen counter missing"


def test_bug1_urlaub_marker_comment_present(index_html):
    assert "Bug-1" in index_html, "Bug-1 marker comment missing"
    assert "Rest-Berechnung" in index_html, "Bug-1 Rest-Berechnung-comment missing"


def test_sprint49_riedmann_moreTabs_guard_for_mehr_button(index_html):
    assert "moreTabs.length>0" in index_html, \
        "Sprint-49: moreTabs.length>0 guard missing"
    assert "Riedmann-Sidebar-Fix" in index_html or "S49" in index_html, \
        "Sprint-49: regression-marker (Riedmann-Sidebar / S49) must remain"


def test_sprint49_mehr_button_render_uses_guard(index_html):
    m = re.search(
        r"ww<1200&&moreTabs\.length>0&&React\.createElement",
        index_html,
    )
    assert m, "Sprint-49: ww<1200&&moreTabs.length>0 render-guard missing for Mehr-Button"


def test_sprint49_mehr_popup_uses_guard(index_html):
    m = re.search(
        r"moreOpen&&isMob&&moreTabs\.length>0&&React\.createElement",
        index_html,
    )
    assert m, "Sprint-49: moreOpen&&isMob&&moreTabs.length>0 guard missing for Mehr-Popup"


def test_sprint48_gewerk_filter_auto_detect_present(index_html):
    assert "_gpAdminLike" in index_html, "Sprint-48: _gpAdminLike must exist"
    assert "_gpFromUser" in index_html, \
        "Sprint-48: _gpFromUser (curUser.gewerk DB-column) must exist"


def test_sprint48_gewerk_priority_chain(index_html):
    assert "epk_user_gewerk" in index_html, \
        "Sprint-48: epk_user_gewerk LS key must remain"
    m = re.search(r'_gp\s*=\s*"elektro"', index_html)
    assert m, "Sprint-48: monteur default Gewerk = 'elektro' missing"


def test_sprint48_gewerk_admin_sees_beide(index_html):
    line = None
    for ln in index_html.splitlines():
        if "_gpAdminLike" in ln and "===" in ln and "admin" in ln:
            line = ln
            break
    assert line is not None, "_gpAdminLike definition (with admin check) not found"
    assert "projektleiter" in line and "buero" in line, \
        "Sprint-48: _gpAdminLike must include admin/projektleiter/buero"


def test_sprint48_kataAllowed_handles_allgemein(index_html):
    m = re.search(r"const\s+_kataAllowed\s*=\s*\(\s*g\s*\)\s*=>\s*\{[^}]+\}", index_html)
    assert m, "_kataAllowed helper not extractable"
    body = m.group(0)
    assert "allgemein" in body, "_kataAllowed must explicitly handle 'allgemein'"


# ------------------------- 77.3 Schema-tests --------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQL_DIR = os.path.join(REPO_ROOT, "sql")


SQL_MIGRATIONS = [
    "migrate_notifications_rls_v3953.sql",
    "migrate_supplier_articles_safe_v3954.sql",
    "migrate_user_gewerk_v3968.sql",
    "migrate_user_kiener_v3959.sql",
    "migrate_whatsapp_v3919.sql",
]


@pytest.mark.parametrize("filename", SQL_MIGRATIONS)
def test_sql_migration_file_exists(filename):
    p = os.path.join(SQL_DIR, filename)
    assert os.path.isfile(p), f"SQL migration {filename} missing in sql/"


@pytest.mark.parametrize("filename", SQL_MIGRATIONS)
def test_sql_migration_documents_intent(filename):
    """Every migration must start with SQL comment-block describing intent."""
    p = os.path.join(SQL_DIR, filename)
    with open(p, "r", encoding="utf-8") as f:
        first_lines = "".join([next(f) for _ in range(3)])
    assert first_lines.lstrip().startswith("--"), \
        f"{filename} must start with SQL doc-comments"


@pytest.mark.parametrize("filename", SQL_MIGRATIONS)
def test_sql_migration_has_idempotent_guards(filename):
    """Migrations should use IF EXISTS / IF NOT EXISTS / ON CONFLICT / OR REPLACE."""
    p = os.path.join(SQL_DIR, filename)
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    has_guard = (
        re.search(r"\bIF\s+(NOT\s+)?EXISTS\b", content, re.I)
        or re.search(r"\bON\s+CONFLICT\b", content, re.I)
        or re.search(r"\bOR\s+REPLACE\b", content, re.I)
    )
    assert has_guard, \
        f"{filename} should use IF [NOT] EXISTS / ON CONFLICT / OR REPLACE for idempotency"


@pytest.mark.parametrize("filename", SQL_MIGRATIONS)
def test_sql_migration_no_trailing_destructive_grant_all(filename):
    """Migrations should not GRANT ALL on tables to PUBLIC (security smell)."""
    p = os.path.join(SQL_DIR, filename)
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    forbidden = re.compile(r"GRANT\s+ALL\s+.*\s+TO\s+PUBLIC", re.I)
    assert not forbidden.search(content), \
        f"{filename}: GRANT ALL ... TO PUBLIC is a security smell"


def test_sql_readme_present():
    p = os.path.join(SQL_DIR, "README.md")
    assert os.path.isfile(p), "sql/README.md missing"
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Deploy-Reihenfolge" in content or "Deploy" in content, \
        "sql/README.md should document deploy order"


def test_sql_migrations_no_unguarded_drop_table():
    forbidden = re.compile(r"DROP\s+TABLE\s+(?!IF\s+EXISTS)", re.I)
    for fn in SQL_MIGRATIONS:
        p = os.path.join(SQL_DIR, fn)
        if not os.path.isfile(p):
            continue
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        assert not forbidden.search(content), \
            f"{fn} contains unguarded DROP TABLE - destructive without IF EXISTS"


def test_b034_tickets_page_column_present():
    p = os.path.join(SQL_DIR, "B034_tickets_page_column.sql")
    assert os.path.isfile(p), "B034_tickets_page_column.sql missing"



