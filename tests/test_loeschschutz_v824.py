# -*- coding: utf-8 -*-
"""v3.9.824 — Löschschutz Mitarbeiter (Punkt 2 aus HANDOFF_2026-07-23.md).

VORFALL (23.07.2026): zwei Mitarbeiter wurden HART aus `workers` gelöscht, obwohl Lohn-/Projekt-
historie an ihnen hing (8 time_entries / 53 h, 9 absences, 1 Arbeitsschein, 1 fahrzeuge.fahrer).
Es gibt KEINE Foreign Keys auf `workers` -> das DELETE lief klaglos durch, die Daten verwaisten,
stundensatz/SVNR/eintritt waren unwiederbringlich weg.

FIX: delMonteur zählt vorher server-seitig die Referenzen und blockt HART (kein "trotzdem löschen").
Der Bestätigen-Knopf führt zum Austrittsdatum, nicht zum Löschen. Kann die Prüfung nicht durch-
geführt werden, wird NICHT gelöscht (fail-closed) — "leer" darf nie als "keine Referenzen" gelten.
"""
import re

from conftest import run_node_snippet


# ── Helfer ────────────────────────────────────────────────────────────────────
def _del_block(index_html):
    a = index_html.index("const delMonteur=async id=>{")
    return index_html[a:index_html.index("\n  };", a)]


def _pure_src(index_html):
    """Die beiden PUREN Funktionen + ihre Def-Tabelle, node-lauffähig."""
    a = index_html.index("const _WORKER_REF_DEFS=Object.freeze([")
    b = index_html.index("if(typeof window!=='undefined'){window._workerRefSumme=", a)
    return index_html[a:b]


def _run(node_exe, index_html, expr):
    return run_node_snippet(
        node_exe, _pure_src(index_html) + "\nprocess.stdout.write(String(" + expr + "))"
    ).strip()


# ── TEIL 1: die PUREN Funktionen ──────────────────────────────────────────────
def test_summe_zaehlt_alle_kategorien(node_exe, index_html):
    # Cracana-Fall aus dem Vorfall: 8 TE + 9 Abwesenheiten + 1 AS = 18.
    assert _run(node_exe, index_html,
                "_workerRefSumme({entries:8,abs:9,as:1,fz:0,login:0})") == "18"
    # Aliti-Fall: NUR ein Fahrzeug — muss trotzdem > 0 ergeben, sonst hätte der Block nicht gegriffen.
    assert _run(node_exe, index_html, "_workerRefSumme({fz:1})") == "1"


def test_summe_ist_robust_gegen_muell(node_exe, index_html):
    # Kein Objekt / fehlende Keys / Unsinn -> 0, aber NIE NaN (NaN>0 ist false => stiller Durchlass).
    for arg in ["undefined", "null", "{}", "{entries:'x',abs:null,as:undefined}", "{entries:-3}"]:
        assert _run(node_exe, index_html, "_workerRefSumme(" + arg + ")") == "0", arg
    # entriesH darf NICHT mitzählen (ist eine Stundensumme, keine Zeilenzahl).
    assert _run(node_exe, index_html, "_workerRefSumme({entriesH:53})") == "0"


def test_text_listet_nur_belegte_kategorien(node_exe, index_html):
    out = _run(node_exe, index_html, "JSON.stringify(_workerRefText({entries:8,entriesH:53,abs:9,as:1}))")
    assert "8 Zeiteinträge (53 h)" in out, out
    assert "9 Abwesenheiten" in out, out
    assert "1 Arbeitsschein" in out and "1 Arbeitsscheine" not in out, "Singular/Plural falsch: " + out
    # Leere Kategorien tauchen NICHT auf (sonst "0 Fahrzeuge" als Blocker-Begründung).
    assert "Fahrzeug" not in out and "Login" not in out, out
    assert out.count("\\n") == 2, "erwartet 3 Zeilen: " + out


def test_text_singular_plural_und_stunden(node_exe, index_html):
    assert "1 Zeiteintrag (7.5 h)" in _run(
        node_exe, index_html, "_workerRefText({entries:1,entriesH:7.5})")
    # Stundensumme 0 -> kein leerer Klammerzusatz "(0 h)".
    assert _run(node_exe, index_html, "_workerRefText({entries:2,entriesH:0})") == "• 2 Zeiteinträge"
    # Keine Referenzen -> leerer Text (der Aufrufer blockt dann ohnehin nicht).
    assert _run(node_exe, index_html, "JSON.stringify(_workerRefText({}))") == '""'


def test_alle_fuenf_referenzquellen_gedeckt(index_html):
    """Die Tabelle muss genau die Spalten treffen, die real auf workers.id zeigen."""
    a = index_html.index("const _WORKER_REF_DEFS=Object.freeze([")
    defs = index_html[a:index_html.index("]);", a)]
    for tab, col in [("time_entries", "worker_id"), ("absences", "worker_id"),
                     ("arbeitsscheine", "monteur"), ("fahrzeuge", "fahrer"),
                     ("users", "monteur_id")]:
        assert '"' + tab + '"' in defs, "Referenzquelle " + tab + " fehlt"
        assert '"' + col + '"' in defs, "Spalte " + col + " fehlt"


# ── TEIL 2: strikter Leser (fail-closed) ──────────────────────────────────────
def test_selectstrict_wirft_auch_bei_401_403(index_html):
    a = index_html.index("async function _sbSelectStrict(")
    blk = index_html[a:index_html.index("\n}", a)]
    assert "if(!r.ok){" in blk and "throw new Error" in blk, "Nicht-2xx wirft nicht"
    # Genau das darf NICHT passieren: Auth-Fehler in [] verwandeln (v820-Silent-Denial).
    assert "_isAuthErr" not in blk and "return[]" not in blk, (
        "_sbSelectStrict schluckt Auth-Fehler -> 'leer' würde als 'keine Referenzen' gelten"
    )
    assert "Array.isArray(j)" in blk, "nicht-Array-Antwort wird nicht als Fehler behandelt"


def test_workerrefs_nutzt_strikten_leser_nicht_sbget(index_html):
    a = index_html.index("async function _workerRefs(id){")
    blk = index_html[a:index_html.index("\n}", a)]
    assert "_sbSelectStrict" in blk, "_workerRefs liest nicht strikt"
    assert "_sbGet(" not in blk and "_sbGetUsersSafe" not in blk, (
        "_workerRefs nutzt einen Leser, der bei Auth-Fehlern [] liefert"
    )
    # Promise.all -> EIN Fehlschlag reisst den ganzen Check mit (kein Teilergebnis).
    assert "Promise.all" in blk, "Teil-Ergebnisse möglich — ein Fehlschlag muss den Check kippen"


# ── TEIL 3: delMonteur — harter Block, richtige Reihenfolge ───────────────────
def test_refcheck_laeuft_vor_dem_delete(index_html):
    blk = _del_block(index_html)
    i_refs = blk.index("await _workerRefs(id)")
    i_del = blk.index('method:"DELETE"')
    assert i_refs < i_del, "DELETE wird abgesetzt bevor die Referenzen geprüft sind"


def test_referenzen_blocken_hart_ohne_ausweg(index_html):
    blk = _del_block(index_html)
    i_guard = blk.index("_workerRefSumme(_refs)>0")
    i_del = blk.index('method:"DELETE"')
    assert i_guard < i_del, "Blocker steht nicht vor dem DELETE"
    # Zwischen Blocker und DELETE muss ein `return;` liegen -> kein Durchfallen.
    assert "return;" in blk[i_guard:i_del], "Blocker-Zweig kehrt nicht zurück (löscht trotzdem)"
    # Der Bestaetigen-Knopf fuehrt zum Austritt, NICHT zum Loeschen.
    assert "Austrittsdatum setzen" in blk, "kein Weg zum Austrittsdatum angeboten"
    assert "setSel(id)" in blk, "Bestätigen öffnet den Mitarbeiter nicht zum Austritt-Eintragen"


def test_block_dialog_nennt_zahlen(index_html):
    blk = _del_block(index_html)
    i_guard = blk.index("_workerRefSumme(_refs)>0")
    i_del = blk.index('method:"DELETE"')
    zweig = blk[i_guard:i_del]
    assert "_workerRefText(_refs)" in zweig, (
        "Blocker zeigt keine Zahlen — Handoff verlangt '8 Zeiteinträge, 9 Abwesenheiten hängen dran'"
    )


def test_pruef_fehler_loescht_nicht(index_html):
    """fail-closed: eine nicht beantwortbare Frage darf nicht als 'keine Referenzen' durchgehen."""
    blk = _del_block(index_html)
    i_catch = blk.index("catch(_re)")
    i_del = blk.index('method:"DELETE"')
    zweig = blk[i_catch:i_del]
    assert "return;" in zweig, "Prüf-Fehler fällt zum DELETE durch"
    assert "konnten nicht geprüft werden" in zweig, "Prüf-Fehler meldet nicht ehrlich"


def test_loesch_confirm_nur_bei_null_referenzen(index_html):
    """Der eigentliche 'wirklich löschen?'-Confirm darf erst NACH dem Blocker kommen."""
    blk = _del_block(index_html)
    i_guard = blk.index("_workerRefSumme(_refs)>0")
    i_confirm = blk.index('_confirmModal("Mitarbeiter wirklich löschen?')
    assert i_guard < i_confirm, "Lösch-Confirm erscheint vor dem Blocker"


def test_kein_sq_push_und_kein_natives_confirm(index_html):
    """v820-Erbe: Löschen läuft nie über die Offline-Queue; UI-Dialoge nie nativ."""
    blk = _del_block(index_html)
    assert "SQ.push" not in blk, "Löschpfad nutzt die Offline-Queue (Fehlschlag würde still geschluckt)"
    assert not re.search(r"[^_\w]confirm\s*\(", blk), "natives confirm() in delMonteur"
