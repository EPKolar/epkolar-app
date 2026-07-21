"""v3.9.776 — PZE-Monatsblatt (FinkZeit) als PDF-Uebergabe an den Lohnverrechner.

Der PDF-Export (modul-global _pzePdf, von PZEView UND KVZulagenReport gerufen) spiegelt den
On-Screen-FinkZeit-Report: EINE Zeilen-Quelle (_pzeBuildRows), FinkZeit-Spaltenfolge, KW-Teilsummen
+ Monatssumme. Die Entfernungszulage-MENGE kommt aus der EINEN lohnnahen Quelle _ezEffTage
(Vorbelegung >6h aus time_entries + Korrektur-Flags), NICHT aus stempel_log. Die Tagesiteration ist
kalendarisch (v3.9.700-DST-Lektion). Saetze/Rechenkern bleiben unberuehrt.
"""
import json
import re
from conftest import run_node_snippet, _extract_fn


def test_ez_menge_riedmann_7_tage(node_exe, index_html):
    """Riedmann-Pin (v3.9.785, 3-Stufen): 7 Anwesenheitstage klein x 11,94 = 83,58 EUR (KV ab 01.01.2026).

    Alte Pins 81,97 (Satz 11,71) bzw. 93,68 sind mit dem korrekten KV-Satz 11,94 obsolet (Sebastian freigegeben).
    Node-eval der EINEN EZ-Summenfunktion _ezEffTage (mit _ezKey/_ezDayEff) — dieselbe Funktion, die Kalender,
    Zulagen-Ergebnistabelle und PDF-Fuss nutzen. Rueckgabe je Stufe {tageKlein,tageMittel,tageGross,sum}.
    """
    parts = []
    for name in ("_ezKey", "_ezDayEff", "_ezEffTage"):
        fn = _extract_fn(index_html, name)
        assert fn, f"{name} nicht gefunden"
        parts.append(fn)
    days = {f"2026-03-{d:02d}": 8.0 for d in range(2, 9)}  # 7 Tage, je 8h (>6h) -> klein
    snippet = (
        "\n".join(parts) + "\n"
        "const SA={klein:11.94,mittel:30.00,gross:62.04};"
        "const dm=" + json.dumps(days) + ";"
        "const r=_ezEffTage(dm,{},'W1',SA);"  # 7 klein
        "const rGross=_ezEffTage(dm,{'W1_2026-03-07':{stufe:'gross'},'W1_2026-03-08':{stufe:'gross'}},'W1',SA);"  # 5 klein + 2 gross
        "const rAbs=_ezEffTage(dm,{},'W1',SA,{'2026-03-02':true});"  # 1 Tag genehmigt abwesend
        "process.stdout.write(JSON.stringify({klein:r,gross:rGross,abs:rAbs}));"
    )
    out = json.loads(run_node_snippet(node_exe, snippet))
    assert out["klein"]["tageKlein"] == 7 and abs(out["klein"]["sum"] - 83.58) < 1e-9, f"7 klein x 11,94 = 83,58, war {out['klein']}"
    assert out["gross"]["tageKlein"] == 5 and out["gross"]["tageGross"] == 2 and abs(out["gross"]["sum"] - 183.78) < 1e-9, out["gross"]
    # v783-Abwesenheits-Ausschluss bleibt: 1 Tag genehmigt krank -> 6 klein
    assert out["abs"]["tageKlein"] == 6 and abs(out["abs"]["sum"] - 71.64) < 1e-9, out["abs"]


def test_pdf_finkzeit_spaltenfolge(index_html):
    """Spalten-Pin: der PDF-Generator traegt die FinkZeit-Spaltenfolge in genau dieser Reihenfolge."""
    body = _extract_fn(index_html, "_pzePdf")
    assert body, "_pzePdf nicht gefunden"
    labels = ["Datum", "Tag", "Von/Bis", "Fehlgrund", "Gesamt",
              "Soll", "Pause", "+/-", "Notiz", "Projektzeit"]
    positions = {lab: body.find("['" + lab + "',") for lab in labels}
    fehlend = [lab for lab, p in positions.items() if p < 0]
    assert not fehlend, f"Spalten-Labels fehlen im PDF-Kopf: {fehlend}"
    seq = [positions[lab] for lab in labels]
    assert seq == sorted(seq), f"Spaltenfolge nicht in FinkZeit-Reihenfolge: {positions}"


def test_pdf_dst_iteration_kalendarisch(index_html):
    """DST-Pin (v3.9.700): die Tagesiteration ist kalendarisch (setDate), NICHT ms-Addition.

    Der PDF reicht die On-Screen-Zeilen-Quelle _pzeBuildRows durch (bevorzugt), erbt damit die
    DST-immune Iteration (Maerz = 31 Zeilen). Die Row-Iteration selbst darf kein +TIME_DAY nutzen.
    """
    build = _extract_fn(index_html, "_pzeBuildRows")
    assert build, "_pzeBuildRows nicht gefunden"
    assert "d.setDate(d.getDate()+1)" in build, "Tagesiteration muss kalendarisch sein (setDate)"
    assert "_iso(d)<=endK" in build, "Abbruch muss ueber ISO-String-Vergleich laufen (nicht ms)"
    # Kommentare strippen, dann sicherstellen: die Row-Iteration nutzt KEINE ms-Addition (+TIME_DAY).
    code_only = re.sub(r"/\*.*?\*/", "", build, flags=re.DOTALL)
    code_only = re.sub(r"//[^\n]*", "", code_only)
    assert "TIME_DAY" not in code_only, "Row-Iteration darf keine ms-Addition (+TIME_DAY) nutzen"
    pdf = _extract_fn(index_html, "_pzePdf")
    assert "_pzeBuildRows(" in pdf, "PDF muss dieselbe Zeilen-Quelle _pzeBuildRows verwenden"
    # def + Aufruf im PDF + Aufruf im PZEView-Onscreen -> mind. 3 Vorkommen (eine Quelle, geteilt)
    assert index_html.count("_pzeBuildRows(") >= 3, (
        "PZEView-Onscreen und PDF muessen dieselbe _pzeBuildRows-Quelle teilen"
    )


def test_ez_menge_eine_quelle_ezefftage(index_html):
    """Die EZ-Menge im PDF haengt an _ezEffTage (nicht an stempel_log / r.ez). v3.9.785: je Stufe, Saetze via _ezSaetze."""
    pdf = _extract_fn(index_html, "_pzePdf")
    assert "_ezEffTage(" in pdf, "PDF-Fuss muss die EZ-Menge aus _ezEffTage beziehen"
    # Der Fuss beschriftet Menge je Stufe x Satz; Saetze aus KV_RULES (_ezSaetze), nicht hart im Text.
    assert "Entfernungszulage — klein:" in pdf and "EUR" in pdf, "EZ-Fuss je Stufe (klein/mittel/groß) fehlt"
    assert "_ezSaetze(kv)" in pdf, "Saetze muessen aus KV_RULES (_ezSaetze) stammen (nie hart 11,94 im Body)"
    assert "Summe Entfernungszulage:" in pdf, "Stufen-Summe im PDF-Fuss fehlt"


def test_rechenkern_unberuehrt(index_html):
    """v3.9.785 Saetze + Rechenkern: klein 11,94 (KV ab 01.01.2026, Alt 11,71 war falsch), mittel/gross gesetzt;
    _kvTaggeldTag/_ezEffTage/_kvZulagenMonat existieren."""
    assert "taggeldAb6h:11.94" in index_html, "EZ-Satz klein 11,94 (KV 2026)"
    assert "ezMittel:30.00" in index_html and "ezGross:62.04" in index_html, "Saetze mittel/gross"
    assert re.search(r"function _kvTaggeldTag\(", index_html), "_kvTaggeldTag muss existieren"
    assert re.search(r"function _ezEffTage\(", index_html), "_ezEffTage muss existieren"
    assert re.search(r"function _kvZulagenMonat\(", index_html), "_kvZulagenMonat muss existieren"


def test_csv_button_ersetzt_durch_pze_pdf(index_html):
    """Der CSV-Button ist durch den PZE-PDF-Uebergabezettel ersetzt; _csv-Export ist entfernt (0 Refs)."""
    assert "📄 PZE-PDF (Lohnverrechner)" in index_html, "PZE-PDF-Button fehlt im Zulagen-Tab"
    assert "📥 CSV (Lohnverrechner)" not in index_html, "alter CSV-Button darf nicht mehr existieren"
    # KVZulagenReport._csv wurde entfernt: es gibt keine `const _csv=` mehr (der Audit-_csv ist lokal 'const _csv=' mit anderem Muster).
    assert "const _csv=()=>{" not in index_html, "KVZulagenReport._csv muss entfernt sein (0 Referenzen)"
