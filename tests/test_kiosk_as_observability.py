"""
Kiosk-AS-Lader: stiller Ladefehler wird diagnostizierbar (Punkt-4-Familie).

Inventur 21.08.2026: `_kioskWeekArbeitsscheine` gab bei jedem Nicht-ok-RPC still
`null` zurueck -> der Boot-Consumer (`if(asch?.length)`) uebersprang das Update ->
das lager_display-Wandpanel zeigte STILL die alte Woche weiter, ohne jede Diagnose.
Exakter Zwilling von `_loadKioskFahrzeuge`, das laengst `window.__kioskFzErr` setzt.

Fix (v3.9.827): der Lader setzt `window.__kioskAsErr` (Fehler-Art bei Nicht-ok /
Parse-Fehler, `null` bei Erfolg). Render-Logik unveraendert; der Marker macht den
stillen Ausfall per Foto vom Wandpanel diagnostizierbar statt nur per SQL-Editor.
"""
import re


def _fn_body(index_html, name):
    m = re.search(r"async function " + re.escape(name) + r"\(", index_html)
    assert m, f"{name} nicht gefunden"
    start = m.start()
    # bis zum naechsten `\nasync function ` oder `\nfunction ` (Top-Level)
    nxt = re.search(r"\n(async function |function )", index_html[start + 10 :])
    end = start + 10 + nxt.start() if nxt else len(index_html)
    return index_html[start:end]


def test_kiosk_as_lader_setzt_fehlermarker(index_html):
    body = _fn_body(index_html, "_kioskWeekArbeitsscheine")
    assert "window.__kioskAsErr" in body, (
        "_kioskWeekArbeitsscheine muss window.__kioskAsErr setzen (Diagnose des "
        "stillen Ladefehlers, Muster __kioskFzErr)"
    )


def test_kiosk_as_marker_wird_bei_erfolg_genullt(index_html):
    """Der Marker muss bei Erfolg auf null gesetzt werden — sonst bleibt ein
    alter Fehlerzustand haengen und meldet dauerhaft einen Ausfall."""
    body = _fn_body(index_html, "_kioskWeekArbeitsscheine")
    assert re.search(r"__kioskAsErr\s*=\s*.*null", body), (
        "kein Erfolgs-Reset window.__kioskAsErr=...null im Lader"
    )


def test_kiosk_fz_lader_bleibt_gehaertet(index_html):
    """Regressionsschutz: der Zwilling __kioskFzErr darf nicht verloren gehen."""
    assert "window.__kioskFzErr" in index_html
