"""v3.8.87 (Agent CC): isMob-responsive Input-Widths für Mobile-Tap-Targets."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _read():
    return INDEX.read_text(encoding='utf-8')


def test_arbeitsscheine_search_isMob_minwidth():
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:150', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: Arbeitsscheine-Search-Input fehlt "
        "`minWidth:isMob?0:150` (Mobile-collapse für Tap-Target)"
    )


def test_vmaterial_datanorm_version_isMob_width():
    text = _read()
    hits = re.findall(r'width:isMob\?"100%":130', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: vMaterial DATANORM-Version-Input fehlt "
        "`width:isMob?\"100%\":130` (Mobile full-width)"
    )


def test_vmaterial_datanorm_category_isMob_width():
    text = _read()
    hits = re.findall(r'width:isMob\?"100%":120', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: vMaterial DATANORM-Category-Input fehlt "
        "`width:isMob?\"100%\":120` (Mobile full-width)"
    )


def test_vdoku_folder_input_isMob_width():
    """vDoku Folder + DATANORM Category teilen ggf. dasselbe Pattern — len>=1."""
    text = _read()
    hits = re.findall(r'width:isMob\?"100%":120', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: vDoku Folder-Input fehlt "
        "`width:isMob?\"100%\":120` (Mobile full-width)"
    )


def test_vmaterial_article_search_isMob_minwidth():
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:180', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: vMaterial Article-Search-Input fehlt "
        "`minWidth:isMob?0:180` (Mobile-collapse)"
    )


def test_vmaterial_lager_kommentar_isMob_minwidth():
    """vMaterial Lager-Kommentar teilt ggf. Pattern mit Arbeitsscheine-Search."""
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:150', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: vMaterial Lager-Kommentar-Input fehlt "
        "`minWidth:isMob?0:150` (Mobile-collapse)"
    )


def test_zeiterfassung_monthly_isMob_minwidth():
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:120', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: Zeiterfassung Monthly-Input fehlt "
        "`minWidth:isMob?0:120` (Mobile-collapse)"
    )


def test_fahrtenbuch_worker_isMob_minwidth():
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:200', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: Fahrtenbuch Worker-Filter-Input fehlt "
        "`minWidth:isMob?0:200` (Mobile-collapse)"
    )


def test_werkzeug_bulk_isMob_minwidth():
    """Werkzeug Bulk-Input teilt ggf. Pattern mit Fahrtenbuch-Worker (len>=1)."""
    text = _read()
    hits = re.findall(r'minWidth:isMob\?0:200', text)
    assert len(hits) >= 1, (
        "v3.8.87 IN-N Regression: Werkzeug Bulk-Input fehlt "
        "`minWidth:isMob?0:200` (Mobile-collapse)"
    )
