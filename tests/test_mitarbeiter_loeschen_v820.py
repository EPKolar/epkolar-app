# -*- coding: utf-8 -*-
"""v3.9.820 — Mitarbeiter-Löschen ehrlich + Austritt wirkt überall + P028 stillgelegt.

BUG (live): ein in der App gelöschter Mitarbeiter (worker mqyxfca35x6i, Ismail Aliti) blieb still in
der DB (active=1). URSACHE: delMonteur entfernte SOFORT lokal und feuerte SQ.push(DELETE)
fire-and-forget; PostgREST liefert bei einer per RLS herausgefilterten Zeile 204/[] = "ok" mit 0
gelöschten Zeilen -> _sbDelete wirft nicht -> SQ hakt ab -> UI/DB divergieren still.

FIX: awaited DELETE direkt mit Prefer return=representation; lokal NUR bei genau 1 Zeile entfernen.
"""
import json
from conftest import run_node_snippet, _extract_fn


# ── TEIL 1: 0-Rows -> kein stilles Entfernen ──────────────────────────────────
def _del_block(index_html):
    a = index_html.index("const delMonteur=async id=>{")
    b = index_html.index("\n  };", a)
    return index_html[a:b]


def test_awaited_delete_mit_representation(index_html):
    blk = _del_block(index_html)
    assert '_sbWH("return=representation")' in blk, "DELETE ohne Prefer return=representation -> 0-Rows nicht erkennbar"
    assert 'method:"DELETE"' in blk and 'SB_REST+"/workers?id=eq."' in blk, "kein direkter awaited workers-DELETE"
    assert "SQ.push" not in blk, "Löschen darf NICHT über die Offline-Queue (Fehlschlag würde still geschluckt)"


def test_null_rows_kein_stilles_entfernen(index_html):
    blk = _del_block(index_html)
    # Guard MUSS vor dem lokalen Entfernen stehen und bei !=1 abbrechen.
    assert "_rows.length!==1" in blk, "1-Zeilen-Check fehlt"
    i_guard = blk.index("_rows.length!==1")
    i_local = blk.index("setMonteure(prev=>prev.filter")
    assert i_guard < i_local, "lokales Entfernen passiert VOR dem 1-Zeilen-Check (stiller Verlust)"
    # Abbruchpfade melden ehrlich.
    assert "Löschen abgelehnt" in blk, "RLS-Silent-Denial meldet nicht"
    assert "Löschen fehlgeschlagen" in blk, "Netzfehler meldet nicht"


def test_workers_in_rls_silent_denial_labels(index_html):
    a = index_html.index("const _RLS_SILENT_DENIAL_LABELS=Object.freeze({")
    b = index_html.index("});", a)
    assert "workers:" in index_html[a:b], "workers fehlt in _RLS_SILENT_DENIAL_LABELS (deckt PATCH mit ab)"


# ── TEIL 2: Austritt wirkt in WeekPlan + Dispo ────────────────────────────────
_PRED = ('(function(m,heute){return !["Backoffice","Verkauf/Buchhaltung","Geschäftsführer"].includes(m.r)'
         '&&(!m.austritt||String(m.austritt).slice(0,10)>=heute);})')


def _pred(node_exe, m_js, heute):
    snip = "process.stdout.write(String(" + _PRED + "(" + m_js + ",'" + heute + "')))"
    return run_node_snippet(node_exe, snip).strip()


def test_austritt_praedikat_logik(node_exe):
    # Ausgetreten (Vergangenheit) -> raus.
    assert _pred(node_exe, "{r:'Monteur',austritt:'2020-01-01'}", "2026-07-22") == "false"
    # Kein Austritt -> drin.
    assert _pred(node_exe, "{r:'Monteur'}", "2026-07-22") == "true"
    # Austritt in der Zukunft -> noch drin (letzter Tag zählt).
    assert _pred(node_exe, "{r:'Monteur',austritt:'2026-12-31'}", "2026-07-22") == "true"
    # Austritt exakt heute -> noch drin.
    assert _pred(node_exe, "{r:'Monteur',austritt:'2026-07-22'}", "2026-07-22") == "true"
    # Rollen-Filter bleibt.
    assert _pred(node_exe, "{r:'Backoffice'}", "2026-07-22") == "false"


def test_austritt_in_beiden_filtern_verdrahtet(index_html):
    # WeekPlan-MA-Picker
    assert ('const fieldMA=monteure.filter(m=>!["Backoffice","Verkauf/Buchhaltung","Geschäftsführer"].includes(m.r)'
            '&&(!m.austritt||String(m.austritt).slice(0,10)>=_hkMA));' in index_html), "fieldMA ohne Austritts-Filter"
    assert "const _hkMA=_ezHeuteISO();" in index_html, "WeekPlan nutzt nicht den Wiener-Datum-Helper"
    # Dispo-Rasterzeilen
    assert ('var feld=(monteure||[]).filter(function(m){return !["Backoffice","Verkauf/Buchhaltung","Geschäftsführer"].includes(m.r)'
            '&&(!m.austritt||String(m.austritt).slice(0,10)>=_heute);});' in index_html), "Dispo-feld ohne Austritts-Filter"
    # _heute muss VOR feld stehen (now-treu, kein zweiter Zeit-Begriff).
    assert index_html.index("var _heute;try{_heute=new Intl.DateTimeFormat") < index_html.index("var feld=(monteure||[]).filter"), \
        "_heute steht nicht vor feld -> Austritts-Filter waere undefined"


# ── TEIL 3: P028 stillgelegt ──────────────────────────────────────────────────
def test_p028_aus_worker_map(index_html):
    a = index_html.index("const JUPROWA_WORKER_MAP={")
    b = index_html.index("};", a)
    assert "'P028'" not in index_html[a:b], "P028 steht noch in JUPROWA_WORKER_MAP (Zombie-Worker-ID)"
    assert "'P026':'mpxpwdhrht1b'" in index_html[a:b], "P026 (Kiener) darf NICHT angetastet sein"


def test_p028_resolve_leer(node_exe, index_html):
    fn = _extract_fn(index_html, "_juprowaResolveWorker")
    assert fn, "_juprowaResolveWorker nicht gefunden"
    a = index_html.index("const JUPROWA_WORKER_MAP={")
    wmap = index_html[a:index_html.index("\n", a)]
    a2 = index_html.index("const JUPROWA_RETIRED=")
    retired = index_html[a2:index_html.index("\n", a2)]
    snip = wmap + "\n" + retired + "\n" + fn + "\nprocess.stdout.write(JSON.stringify({p028:_juprowaResolveWorker('P028','',[]),p026:_juprowaResolveWorker('P026','',[])}))"
    out = json.loads(run_node_snippet(node_exe, snip))
    assert out["p028"] == "", "P028 liefert noch eine Worker-ID statt ''"
    assert out["p026"] == "mpxpwdhrht1b", "P026 (Kiener) wurde versehentlich mit stillgelegt"
