"""v3.9.114 — FINKZEIT STANDBY (Sebastian-Entscheidung 04.06.2026).

Alles FinkZeit-bezogene im Frontend hinter EINEM zentralen Flag geparkt (Code NICHT gelöscht).
Reaktivierung: FINKZEIT_ENABLED = true. DB/Schema unberührt. hasPerm('stunden') unverändert.
"""
import re


def test_flag_exists_and_disabled(index_html):
    assert "const FINKZEIT_ENABLED=false;" in index_html, (
        "Zentrales Flag FINKZEIT_ENABLED muss existieren und false sein (Standby)"
    )


def test_flag_gates_all_surfaces(index_html):
    # Jede FinkZeit-Frontend-Fläche muss das Flag referenzieren:
    gates = [
        # Tab Monatsabrechnung (Tab-Definition spread-conditional)
        '...(FINKZEIT_ENABLED?[{l:"Monatsabrechnung"',
        # mobile _navIds
        '...(FINKZEIT_ENABLED?["stunden"]:[])',
        # Dashboard finkStats-Fetch
        "if(!FINKZEIT_ENABLED)return;",
        # Dashboard-Alerts
        "if(FINKZEIT_ENABLED&&finkStats.offen>0",
        "if(FINKZEIT_ENABLED&&finkStats.diffWarn>0",
        # Dashboard-Card
        'FINKZEIT_ENABLED&&hasPerm(curUser,"stunden")&&',
        # Audit-Filter-Option
        'FINKZEIT_ENABLED&&React.createElement(\'option\', { value: "approve_finkzeit"}',
        # Rechteverwaltung: stunden-Toggle ausgeblendet
        'filter(([_pdm])=>FINKZEIT_ENABLED||_pdm!=="stunden")',
        # Chef-Hinweis
        "if(!FINKZEIT_ENABLED){if(alive)setFinkOpen([]);return;}",
    ]
    for g in gates:
        assert g in index_html, f"FinkZeit-Gate fehlt: {g}"


def test_code_parked_not_deleted(index_html):
    # Die Handler/Logik bleiben im Code erhalten (parken, nicht löschen):
    for kept in ['"/api/finkzeit"', "pdf_data", "function StundenzettelView(",
                 'stunden:"Monatsabrechnung einsehen & freigeben"']:
        assert kept in index_html, f"Geparkter FinkZeit-Code darf NICHT gelöscht sein: {kept}"
    # Standby-Markierungen vorhanden
    assert index_html.count("FINKZEIT STANDBY") >= 6, "Standby-Kommentare müssen die geparkten Stellen markieren"


def test_hasperm_stunden_still_clean(index_html):
    # 'stunden' bleibt in den ROLES-Modulen (hasPerm liefert weiter sauber true/false)
    m = re.search(r'admin:\{l:"Administrator"[^\n]*?modules:\[([^\]]*)\]', index_html)
    assert m and '"stunden"' in m.group(1), "ROLES.admin.modules muss 'stunden' behalten (hasPerm unverändert)"
