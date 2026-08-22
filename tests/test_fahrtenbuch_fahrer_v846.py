"""
Nachtlauf-Hunt v3.9.846 — GPS-Fahrtenbuch zeigte den falschen Fahrer (LEGAL).

`_fahrerVon` (:25965) leitete den Fahrer je Fahrt IMMER aus dem aktuellen
Fahrzeugfahrer (`fahrzeuge.fahrer`) ab und ignorierte den je Fahrt aufgezeichneten
Snapshot `x.fahrer_id` (persistiert beim Write-on-Read :25710). Nach einem
Fahrerwechsel zeigten damit ALLE historischen Fahrten (Anzeige :26037 + CSV-Export
:25867) den neuen Fahrer — ein Fahrtenbuch muss festhalten, wer zum Fahrtzeitpunkt
gefahren ist. Fix: Snapshot bevorzugen, Fallback nur für Alt-Zeilen ohne Snapshot.
"""
import re


def test_fahrervon_bevorzugt_snapshot(index_html):
    # v3.9.855-Nachzieher: _fahrerVon zeigt NUR den Fahrt-Snapshot x.fahrer_id.
    # Der v846-Fallback auf den aktuellen Fahrzeugfahrer ist ENTFERNT (er erzeugte
    # genau die falsche Zuordnung, die v846 verhindern wollte).
    assert "var _fid=(x&&x.fahrer_id)||null;" in index_html
    m = re.search(r"const _fahrerVon=function\(x\)\{.*?\n  \};", index_html, re.S)
    assert m, "_fahrerVon-Funktion nicht gefunden"
    # kein Rueckgriff mehr auf fahrzeuge.fahrer innerhalb von _fahrerVon
    assert "fahrzeuge.find" not in m.group(0)
    assert "const f=fahrzeuge.find" not in m.group(0)
    assert "if(!f||!f.fahrer)" not in m.group(0)


def test_snapshot_nur_bei_belegbarer_quelle(index_html):
    # v3.9.855: der Write-on-Read schreibt KEINEN erfundenen Fahrer mehr
    # (kein _fz.fahrer zum Ansehzeitpunkt) — mangels zeitlich belegbarer Quelle null.
    assert 'fahrer_id:(_fz&&_fz.fahrer)?_fz.fahrer:null' not in index_html
    assert "fahrer_id:null/* v3.9.855" in index_html


def test_fallback_auf_monteur_name(index_html):
    # Anzeigename kommt weiterhin aus props.monteure via aufgeloester id
    m = re.search(r"const _fahrerVon=function\(x\)\{.*?return m\?\(m\.n\|\|''\):'';\s*\};", index_html, re.S)
    assert m, "_fahrerVon-Funktion nicht gefunden / Struktur geaendert"
    body = m.group(0)
    assert "(props.monteure||[]).find(function(y){return y.id===_fid;})" in body
