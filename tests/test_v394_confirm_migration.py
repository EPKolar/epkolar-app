"""v3.9.4 Agent LLL: confirm()->_confirmModal Migration + Geo-Inflight-Lock."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_delMonteur_uses_confirmmodal():
    """v3.9.4 Regression: delMonteur muss _confirmModal nutzen, NICHT
    native confirm() (native blockt UI + ignoriert Variant-Styling)."""
    text = INDEX.read_text(encoding='utf-8')
    # Suche delMonteur-Body und prüfe _confirmModal-Proximity
    m = re.search(
        r'(?:const|let|var)\s+delMonteur\s*=\s*(?:async\s*)?[^{]*\{([\s\S]{0,600}?)\}\s*;',
        text,
    )
    assert m, (
        "v3.9.4 Regression: delMonteur-Definition nicht gefunden in index.html."
    )
    body = m.group(1)
    assert 'await _confirmModal' in body or '_confirmModal(' in body, (
        "v3.9.4 Regression: delMonteur ruft _confirmModal NICHT — "
        "native confirm() blockt UI. Body-Snippet: "
        f"{body[:200]}"
    )
    # Doppel-Check: setMonteure-prev-filter muss in selbem Block stehen (zeigt richtige Funktion)
    assert 'setMonteure(prev' in body or 'setMonteure(prev=>prev.filter' in body, (
        "v3.9.4 Regression: delMonteur-Body enthält kein "
        "setMonteure(prev=>prev.filter ...) — Funktions-Match möglicherweise falsch."
    )


def test_geo_inflight_lock_exists():
    """v3.9.4 Regression: Geo-Inflight-Lock via sessionStorage
    'epk_geo_inflight' muss existieren (verhindert Doppel-getCurrentPosition
    bei Re-Mount/Race)."""
    text = INDEX.read_text(encoding='utf-8')
    # SET muss existieren
    pat_set = r'sessionStorage\.setItem\(\s*["\']epk_geo_inflight["\']'
    assert re.search(pat_set, text), (
        "v3.9.4 Regression: sessionStorage.setItem('epk_geo_inflight',...) "
        "fehlt — Geo-Inflight-Lock NICHT installiert."
    )
    # GET muss existieren (für Inflight-Check)
    pat_get = r'sessionStorage\.getItem\(\s*["\']epk_geo_inflight["\']'
    assert re.search(pat_get, text), (
        "v3.9.4 Regression: sessionStorage.getItem('epk_geo_inflight') "
        "fehlt — Inflight-Check (Race-Guard) NICHT installiert."
    )
    # CLEAR (remove) muss in Callbacks existieren (sonst Permanent-Lock)
    pat_clear = r'sessionStorage\.removeItem\(\s*["\']epk_geo_inflight["\']'
    clear_count = len(re.findall(pat_clear, text))
    assert clear_count >= 1, (
        "v3.9.4 Regression: sessionStorage.removeItem('epk_geo_inflight') "
        f"fehlt (count={clear_count}) — Lock wird NIE freigegeben."
    )


def test_confirmmodal_calls_count_increased():
    """v3.9.4 Regression: confirm()->_confirmModal Migration soll
    Gesamt-Count von _confirmModal-Calls >=6 ergeben (Mitarbeiter-Löschen,
    Projekt-Löschen, Tag-Löschen, Reset-Filter, etc.)."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: _confirmModal( (Call-Site)
    pat = r'_confirmModal\('
    count = len(re.findall(pat, text))
    assert count >= 6, (
        f"v3.9.4 Regression: _confirmModal-Call-Count={count}, erwartet >=6 "
        "(confirm()-Migration scheint zurückgerollt oder unvollständig)."
    )
