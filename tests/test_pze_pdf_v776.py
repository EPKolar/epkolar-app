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
    """Riedmann-Pin (v3.9.783 aktualisiert): 8 Anwesenheitstage >6h, aber 01.07. genehmigt krank
    -> 7 eff. Tage x 11,71 = 81,97 EUR (LA 2740: keine Entfernungszulage auf genehmigter Abwesenheit).

    Alter Pin (bis v3.9.782): 8/93,68 — die Vorbelegung ignorierte Abwesenheiten (Sebastian-Befund aus der
    PDF-Sicht: Krank-Tag faelschlich vorbelegt). Der alte 8/93,68-Pin ist bewusst obsolet (Sebastian freigegeben).
    Node-eval der EINEN EZ-Summenfunktion _ezEffTage (mit ihren Helfern _ezKey/_ezDayEff) — genau die
    Funktion, die Kalender, Zulagen-Ergebnistabelle und PDF-Fuss nutzen. Kein zweiter Rechenpfad.
    """
    parts = []
    for name in ("_ezKey", "_ezDayEff", "_ezEffTage"):
        fn = _extract_fn(index_html, name)
        assert fn, f"{name} nicht gefunden"
        parts.append(fn)
    days = {f"2026-03-{d:02d}": 8.0 for d in range(2, 10)}  # 8 Tage, je 8h (>6h)
    abs_set = {"2026-03-02": True}  # ein Tag genehmigt abwesend (aus _ezAbsSet)
    snippet = (
        "\n".join(parts) + "\n"
        "const dm=" + json.dumps(days) + ";"
        "const aset=" + json.dumps(abs_set) + ";"
        "const r=_ezEffTage(dm,{},'W1',11.71,aset);"
        "const rOhne=_ezEffTage(dm,{},'W1',11.71);"  # ohne absSet-Param = Rueckwaertskompatibilitaet
        "const rOverride=_ezEffTage(dm,{'W1_2026-03-02':{aktiv:true}},'W1',11.71,aset);"  # explizit dazu
        "process.stdout.write(JSON.stringify({mit:r,ohne:rOhne,override:rOverride}));"
    )
    out = json.loads(run_node_snippet(node_exe, snippet))
    assert out["mit"]["tage"] == 7, out
    assert abs(out["mit"]["sum"] - 81.97) < 1e-9, f"7 x 11,71 muss 81,97 EUR ergeben, war {out['mit']}"
    # Rueckwaertskompatibel: ohne absSet unveraendert 8/93,68
    assert out["ohne"]["tage"] == 8 and abs(out["ohne"]["sum"] - 93.68) < 1e-9, out["ohne"]
    # Flag-Override: explizit aktiv=true zaehlt den Abwesenheitstag DOCH -> wieder 8/93,68
    assert out["override"]["tage"] == 8 and abs(out["override"]["sum"] - 93.68) < 1e-9, out["override"]


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
    """Die EZ-Menge im PDF haengt an _ezEffTage (nicht an stempel_log / r.ez / einer >6h-Zaehlung)."""
    pdf = _extract_fn(index_html, "_pzePdf")
    assert "_ezEffTage(" in pdf, "PDF-Fuss muss die EZ-Menge aus _ezEffTage beziehen"
    # Der Fuss beschriftet Menge x Satz; Satz kommt aus KV_RULES (Variable satz), nicht hart im Text.
    assert "Entfernungszulage:" in pdf and "EUR" in pdf, "EZ-Fuss (Tage x Satz = Betrag) fehlt"
    assert "kv.taggeldAb6h" in pdf, "Satz muss aus KV_RULES.taggeldAb6h stammen (nie hart 11,71 im Body)"


def test_rechenkern_unberuehrt(index_html):
    """Saetze + Rechenkern unveraendert: taggeldAb6h 11,71, _kvTaggeldTag/_ezEffTage/_kvZulagenMonat existieren."""
    assert "taggeldAb6h:11.71" in index_html, "EZ-Satz 11,71 (LA 2740) muss unveraendert sein"
    assert re.search(r"function _kvTaggeldTag\(", index_html), "_kvTaggeldTag muss existieren"
    assert re.search(r"function _ezEffTage\(", index_html), "_ezEffTage muss existieren"
    assert re.search(r"function _kvZulagenMonat\(", index_html), "_kvZulagenMonat muss existieren"


def test_csv_button_ersetzt_durch_pze_pdf(index_html):
    """Der CSV-Button ist durch den PZE-PDF-Uebergabezettel ersetzt; _csv-Export ist entfernt (0 Refs)."""
    assert "📄 PZE-PDF (Lohnverrechner)" in index_html, "PZE-PDF-Button fehlt im Zulagen-Tab"
    assert "📥 CSV (Lohnverrechner)" not in index_html, "alter CSV-Button darf nicht mehr existieren"
    # KVZulagenReport._csv wurde entfernt: es gibt keine `const _csv=` mehr (der Audit-_csv ist lokal 'const _csv=' mit anderem Muster).
    assert "const _csv=()=>{" not in index_html, "KVZulagenReport._csv muss entfernt sein (0 Referenzen)"
