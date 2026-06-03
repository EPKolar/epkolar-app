"""v3.9.103 — B-A: absences-Writer setzt hours/tage (aktiver Quota-Bug behoben).

Vorher schrieb der Kalender-Schreibpfad (tog) KEINE hours/tage → absences.hours=0 →
Kontingent-/Resturlaub-Abzug rechnete mit 0. Fix: Single-Day-Toggle schreibt 7,7h / 1 Tag
(38,5h-Woche). Kanonisch bleibt from_date/to_date (Sebastian-Entscheidung 2026-06-03).
"""
import re


def test_absences_post_writes_stdvontag_hours(index_html):
    # Der einzige absences-CREATE-Writer ist der Kalender-Toggle (POST /api/absences).
    # v3.9.106: hours = stdVonTag(d) (Mo-Do 8,5 / Fr 4,5 / Sa-So+Feiertag 0), NICHT flat 7,7
    # (Sebastian-Payroll-Bestätigung). tage = 1 nur an Werktagen.
    m = re.search(r'url:"/api/absences",method:"POST",body:\{([^}]*)\}', index_html)
    assert m, "absences POST-Writer (Kalender-Toggle) nicht gefunden"
    body = m.group(1)
    assert "hours:stdVonTag(d)" in body, (
        "absences-Writer muss hours:stdVonTag(d) setzen (kanonische Tageslogik, NICHT flat 7,7)"
    )
    assert "7.7" not in body, "flat 7,7 darf NICHT mehr im absences-Writer stehen"
    assert "tage:(stdVonTag(d)>0?1:0)" in body, "tage nur an Werktagen (Feiertag/WE = 0)"


def test_absences_post_still_canonical_from_to_date(index_html):
    # from_date/to_date bleiben kanonisch (Option 1) — kein Schema-Umbau.
    m = re.search(r'url:"/api/absences",method:"POST",body:\{([^}]*)\}', index_html)
    assert m
    body = m.group(1)
    assert "from_date:dk(d)" in body and "to_date:dk(d)" in body, (
        "from_date/to_date müssen kanonisch erhalten bleiben"
    )
