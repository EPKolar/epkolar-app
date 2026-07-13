"""v3.9.675 — Wochenplanung: EINE Leer-Definition (_isPaddingRow) fuer Save UND Render.

Bug (Live KW29, 13.07.2026): Der Save nutzte _isPaddingRow (bvh+projId+bem+z), der Render
aber `!(r.bvh||"").trim()` — nur bvh. Eine Zeile mit NUR einer Bemerkung
(bem="09:30 Uhr - Sicherungen", bvh leer, z leer) wurde also persistiert, aber als Padding
gerendert: keine Aktions-Icons (kein Loeschen/Verschieben), kein editierbares BVH-Feld.
Ergebnis: unloeschbare Zombie-Zeile, nur noch per REST-DELETE entfernbar.

Dieser Guard sichert beides ab:
  1. _isPaddingRow selbst klassifiziert eine Nur-Bemerkung-Zeile als NICHT leer.
  2. Render (Desktop-isEmpty + Mobile-Kartenfilter) benutzt genau diesen Helper — nicht
     wieder eine eigene bvh-only-Definition.
"""
import json

from conftest import run_node_snippet, _extract_fn


def _padding_harness(index_html):
    # _isPaddingRow ist eine Arrow-Const (const _isPaddingRow=(r)=>{...}), kein
    # `function`-Statement — daher der explizite signature_regex.
    fn = _extract_fn(index_html, "_isPaddingRow", r"const\s+_isPaddingRow\s*=")
    assert fn, "_isPaddingRow nicht gefunden"
    # Der Extraktor endet auf der schliessenden } der Arrow-Funktion — ohne Semikolon
    # waere das folgende `const rows=...` ein Syntaxfehler (`}const`).
    return fn + ";\n"


def _row(**kw):
    """Zeile im weekplan_rows-Format; leere z-Tage wie emptyWpRow()."""
    z = {d: {"ma": [], "fz": []} for d in ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]}
    row = {"id": "r1", "bvh": "", "projId": "", "bem": "", "z": z}
    row.update(kw)
    return row


def test_is_padding_row_klassifikation(node_exe, index_html):
    """Nur eine rundum leere Zeile ist Padding — Bemerkung/BVH/projId/Zuordnung machen sie echt."""
    leer = _row()
    nur_bem = _row(bem="09:30 Uhr - Sicherungen")   # der Live-Zombie
    nur_bvh = _row(bvh="Baustelle X")
    nur_proj = _row(projId="p-123")
    nur_ma = _row(z={**{d: {"ma": [], "fz": []} for d in ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]},
                     "Mi": {"ma": ["w4"], "fz": []}})
    nur_fz = _row(z={**{d: {"ma": [], "fz": []} for d in ["Mo", "Di", "Mi", "Do", "Fr", "Sa"]},
                     "Fr": {"ma": [], "fz": ["f1"]}})

    snippet = _padding_harness(index_html) + (
        "const rows=" + json.dumps(
            [leer, nur_bem, nur_bvh, nur_proj, nur_ma, nur_fz], ensure_ascii=False
        ) + ";"
        "process.stdout.write(JSON.stringify(rows.map(_isPaddingRow)));"
    )
    got = json.loads(run_node_snippet(node_exe, snippet))

    assert got[0] is True, "rundum leere Zeile muss Padding sein"
    assert got[1] is False, "Zeile mit NUR Bemerkung darf KEIN Padding sein (Zombie-Bug v3.9.675)"
    assert got[2] is False, "Zeile mit BVH ist keine Padding-Zeile"
    assert got[3] is False, "Zeile mit projId ist keine Padding-Zeile"
    assert got[4] is False, "Zeile mit MA-Zuordnung ist keine Padding-Zeile"
    assert got[5] is False, "Zeile mit FZ-Zuordnung ist keine Padding-Zeile"


def test_render_nutzt_denselben_helper(index_html):
    """Render darf keine eigene bvh-only-Leer-Definition mehr haben."""
    assert "const isEmpty=_isPaddingRow(r);" in index_html, (
        "Desktop-Render muss _isPaddingRow nutzen — sonst kehrt der Zombie zurueck "
        "(Icons/BVH-Input haengen an isEmpty)"
    )
    assert 'const isEmpty=!(r.bvh||"").trim();' not in index_html, (
        "alte bvh-only-Definition von isEmpty ist wieder da"
    )
    assert "rows.filter(r=>!_isPaddingRow(r)).map((r,idx)=>" in index_html, (
        "Mobile-Kartenliste muss _isPaddingRow nutzen — sonst ist die Nur-Bemerkung-Zeile "
        "mobil unsichtbar und damit wieder unloeschbar"
    )
