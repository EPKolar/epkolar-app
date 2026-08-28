"""v3.9.106 — AT/NÖ-Feiertage für Urlaub/ZA-Stundenberechnung.

Chat-Claude-Befund: stdVonTag zählte AT-Feiertage (z.B. Pfingstmontag 25.5.2026) als 8,5h
Urlaub mit → Günther 98,5h statt korrekt 90,0h. Fix: _isATFeiertag(d) (Easter-berechnet,
jedes Jahr korrekt) → stdVonTag liefert 0 an Feiertagen.
"""
import re
import json
from conftest import run_node_snippet, _extract_fn

# Der lokale _extract_fn-Klon ist entfernt (13.07.2026): sein Brace-Zaehler nahm die erste
# `{` nach dem Funktionsnamen als Body-Start und griff damit bei destrukturierten Parametern
# (function X({a,b}){...}) die Parameterliste statt des Rumpfs. Hier war das folgenlos, weil
# _easterSunday/_isATFeiertag normale Parameter haben — aber latent kaputt. Master ist der
# gefixte Extraktor in conftest.py (Commit 6f3f12b).


def _holiday_harness(index_html):
    easter = _extract_fn(index_html, "_easterSunday")
    feiertag = _extract_fn(index_html, "_isATFeiertag")
    assert easter, "_easterSunday nicht gefunden"
    assert feiertag, "_isATFeiertag nicht gefunden"
    return easter + "\n" + feiertag + "\n"


def test_easter_helper_present(index_html):
    assert "function _easterSunday(" in index_html
    assert "function _isATFeiertag(" in index_html


def test_at_holidays_2026(node_exe, index_html):
    # Chat-Claude bestätigte 2026-Feiertage (NÖ): fix + beweglich (Oster-basiert).
    # v3.9.875: 2026-10-26 (Nationalfeiertag) FEHLTE hier — genau deshalb war dieser
    # Test gruen, waehrend _isATFeiertag den Tag nicht kannte. Ein Riegel, der die
    # Luecke des Geprueften teilt, misst nichts.
    holidays = ["2026-01-01", "2026-01-06", "2026-04-06", "2026-05-01", "2026-05-14",
                "2026-05-25", "2026-06-04", "2026-08-15", "2026-10-26", "2026-11-01", "2026-12-08",
                "2026-12-25", "2026-12-26"]
    snippet = _holiday_harness(index_html) + (
        "const days=" + json.dumps(holidays) + ";"
        "const out=days.map(s=>{const p=s.split('-');return _isATFeiertag(new Date(+p[0],+p[1]-1,+p[2]));});"
        "process.stdout.write(JSON.stringify(out));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert all(res), f"alle 2026-Feiertage müssen erkannt werden, war {res}"


def test_non_holidays_not_flagged(node_exe, index_html):
    # 26.5.2026 (Di nach Pfingstmontag), 2.1.2026 (Fr), 13.5.2026 (Mi vor Chr.Himmelf.)
    nondays = ["2026-05-26", "2026-01-02", "2026-05-13", "2026-04-07"]
    snippet = _holiday_harness(index_html) + (
        "const days=" + json.dumps(nondays) + ";"
        "const out=days.map(s=>{const p=s.split('-');return _isATFeiertag(new Date(+p[0],+p[1]-1,+p[2]));});"
        "process.stdout.write(JSON.stringify(out));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert not any(res), f"keiner dieser Tage ist Feiertag, war {res}"


def test_pfingstmontag_other_year(node_exe, index_html):
    # Robustheit über Jahre: Pfingstmontag 2025 = 9.6.2025, Ostermontag 2024 = 1.4.2024.
    snippet = _holiday_harness(index_html) + (
        "const a=_isATFeiertag(new Date(2025,5,9));"      # 9.6.2025 Pfingstmontag
        "const b=_isATFeiertag(new Date(2024,3,1));"       # 1.4.2024 Ostermontag
        "const c=_isATFeiertag(new Date(2025,5,10));"      # 10.6.2025 kein Feiertag
        "process.stdout.write(JSON.stringify([a,b,c]));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res == [True, True, False], f"Easter-Logik über Jahre falsch: {res}"


# ---------------------------------------------------------------------------
# v3.9.875 - Nationalfeiertag. Eigener Riegel, weil der Tag LOHN kostet.
# ---------------------------------------------------------------------------

def test_nationalfeiertag_ueber_jahre(node_exe, index_html):
    """26.10. ist ein FIXER Feiertag - er muss in JEDEM Jahr greifen, nicht nur 2026.

    Warum das Geld kostet: _stdVonTagK (Urlaub) und _stdVonTagBrk (Zeiterfassung)
    liefern an Feiertagen 0 Sollstunden. Fehlt der Tag, rechnet die App am 26.10.
    volle 8,5 Stunden - wer ueber den Nationalfeiertag Urlaub nimmt, bekommt einen
    Urlaubstag abgezogen, der ihm zusteht. Zusaetzlich plant die Dispo dort einen
    vollen Arbeitstag.
    """
    snippet = _holiday_harness(index_html) + (
        "const out=[2024,2025,2026,2027,2030].map(y=>_isATFeiertag(new Date(y,9,26)));"
        "process.stdout.write(JSON.stringify(out));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert all(res), "26.10. muss in jedem Jahr Feiertag sein, war %s" % res


def test_nachbartage_bleiben_arbeitstage(node_exe, index_html):
    """Gegenprobe zur Zahl 26: nur der 26.10., nicht der 25./27.10., nicht 26.9./26.11."""
    snippet = _holiday_harness(index_html) + (
        "const out=[[2026,9,25],[2026,9,27],[2026,8,26],[2026,10,26]]"
        ".map(a=>_isATFeiertag(new Date(a[0],a[1],a[2])));"
        "process.stdout.write(JSON.stringify(out));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert not any(res), "25./27.10., 26.9. und 26.11. sind Arbeitstage, war %s" % res


def test_selbsttest_riegel_schlaegt_beim_rueckbau_an(node_exe, index_html):
    """Umkehrprobe: wird [10,26] entfernt, MUSS der Riegel rot werden.

    Ohne diese Probe koennte der Test aus einem anderen Grund gruen sein - genau
    der Zustand, in dem die Feiertagspruefung jahrelang war.
    """
    zurueck = index_html.replace(
        "const fixed=[[1,1],[1,6],[5,1],[8,15],[10,26],[11,1],[12,8],[12,25],[12,26]];",
        "const fixed=[[1,1],[1,6],[5,1],[8,15],[11,1],[12,8],[12,25],[12,26]];", 1)
    assert zurueck != index_html, "Rueckbau griff nicht - Anker veraltet"
    snippet = _holiday_harness(zurueck) + (
        "process.stdout.write(JSON.stringify(_isATFeiertag(new Date(2026,9,26))));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert res is False, (
        "Umkehrprobe gescheitert: ohne [10,26] meldet _isATFeiertag den 26.10. "
        "trotzdem als Feiertag - dann prueft dieser Test etwas anderes als gedacht."
    )
