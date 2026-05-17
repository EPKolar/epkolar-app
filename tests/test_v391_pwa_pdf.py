"""v3.9.1 Agent III: PWA-Install-Banner-Persistence + PDF-Fallback-Escaping."""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def test_pwa_install_banner_persistence():
    """v3.9.1 Regression: showInstallBanner useState-Initializer muss
    localStorage 'epk_install_dismissed' prüfen (sonst Banner wieder
    sichtbar nach Dismiss + Reload)."""
    text = INDEX.read_text(encoding='utf-8')
    # Pattern: useState-Initializer mit localStorage.getItem("epk_install_dismissed")==="1"
    # In Minifier-Form: ()=>{try{if(localStorage.getItem("epk_install_dismissed")==="1")return false;}catch...}
    pat = r'localStorage\.getItem\(\s*["\']epk_install_dismissed["\']\s*\)\s*===\s*["\']1["\']'
    matches = re.findall(pat, text)
    assert len(matches) >= 1, (
        "v3.9.1 Regression: PWA-Banner-Persistence broken — "
        "useState-Initializer muss localStorage.getItem('epk_install_dismissed')==='1' "
        "prüfen, sonst Banner-Re-Show nach Reload."
    )


def test_pdf_fallback_no_unescaped_html():
    """v3.9.1 Regression: PDF/HTML-Fallback für arbeitsanweisungen/
    durchgefuehrte muss esc()-ternary (?esc(...):"<span ...>") nutzen,
    NICHT ||"<span ...>" — sonst XSS via unescaped user-input."""
    text = INDEX.read_text(encoding='utf-8')
    # Positive: must contain esc(...) ternary fallback to <span
    pat_good = r'\?\s*esc\([^)]+\)\s*:\s*["\']<span'
    good_matches = re.findall(pat_good, text)
    assert len(good_matches) >= 2, (
        "v3.9.1 Regression: PDF-Fallback nutzt nicht esc()-ternary — "
        "erwartet >=2 Treffer für `?esc(...):\"<span ...>` "
        f"(gefunden: {len(good_matches)})."
    )
    # Negative: ||"<span fallback ohne esc() darf NICHT für Arbeitsanweisungen/Durchgef. existieren
    pat_bad = r'a\.(arbeitsanweisungen|durchgefuehrte)\s*\|\|\s*["\']<span'
    bad_matches = re.findall(pat_bad, text)
    assert len(bad_matches) == 0, (
        "v3.9.1 Regression: Unescaped ||\"<span\"-Fallback gefunden für "
        f"a.arbeitsanweisungen/durchgefuehrte (Treffer: {bad_matches}). "
        "Muss esc()-ternary nutzen."
    )
