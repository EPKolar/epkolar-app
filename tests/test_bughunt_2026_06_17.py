"""Bug-Hunt-Marathon 2026-06-17 (v3.9.407) — Welle-1-Fixes.

Static-Source-Regression-Guards:
 - FleetView Service-Fälligkeit: date-only lokal parsen (+"T00:00:00"), kein UTC-Mitternacht-Flip.
 - Material-Order createdById: leerer FK -> null (nicht "").
 - Audit-CSV-Export: Formel-Injektion-Schutz im Zellen-Formatter.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _txt():
    return INDEX.read_text(encoding='utf-8')


def test_fleetview_service_faellig_local_parse():
    """Positiv: FleetView serviceFaellig parst date-only lokal (+T00:00:00)."""
    text = _txt()
    assert 'const d=new Date(f.naechstService+"T00:00:00");return d<=new Date();' in text, \
        'v3.9.407 Regression: FleetView serviceFaellig muss +"T00:00:00" lokal parsen'


def test_fleetview_service_warn_local_parse():
    """Positiv: FleetView serviceWarn (Listen-Karte) parst date-only lokal."""
    text = _txt()
    assert 'f.naechstService&&new Date(f.naechstService+"T00:00:00")<=new Date()' in text, \
        'v3.9.407 Regression: FleetView serviceWarn muss +"T00:00:00" lokal parsen'


def test_fleetview_no_bare_naechstservice_utc_parse():
    """Negativ-Guard: bare new Date(f.naechstService) ohne T00:00:00 darf NICHT zurückkehren."""
    text = _txt()
    bad = re.findall(r'new Date\(f\.naechstService\)(?!\+)', text)
    assert not bad, \
        'v3.9.407 Regression: bare new Date(f.naechstService) (UTC-Flip) zurückgekehrt'


def test_material_order_created_by_id_null_not_empty():
    """Positiv: createdById faellt auf null (nicht "") -> FK/owner-RLS sauber."""
    text = _txt()
    assert '{createdById:(curUser&&curUser.monteurId)||null}' in text, \
        'v3.9.407 Regression: createdById muss ||null sein (FK-Null-Muster), nicht ||""'
    assert '{createdById:(curUser&&curUser.monteurId)||""}' not in text, \
        'v3.9.407 Regression: createdById ||"" (leerer FK) zurückgekehrt'


def test_audit_csv_formula_injection_guard():
    """Positiv: CSV-Zellen-Formatter neutralisiert fuehrende = + - @ \\t \\r."""
    text = _txt()
    # Eindeutiges Fragment des Formel-Injektion-Guards im Audit-CSV _cf-Formatter
    assert r'/^[=+\-@\t\r]/.test(s)' in text, \
        'v3.9.407 Regression: CSV _cf Formel-Injektion-Schutz fehlt'
