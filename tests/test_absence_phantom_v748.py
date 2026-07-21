# -*- coding: utf-8 -*-
"""v3.9.748 — Register #5 (P1, DB-bewiesen): Phantom-Krankmeldung im Poll-Diff.

Sebastian/Handoff: Der Absence-Poll ersetzte den Snapshot KOMPLETT (absenceKeys = newAbsKeys). Ein
partieller/fehlgeschlagener Absence-Load (weniger Keys) schrumpfte den Snapshot -> beim naechsten vollen
Poll galten alte Krankmeldungen als "neu" -> Phantom-Notif. Fix (client-only):
  (a) Union-Merge: absenceKeys nur additiv (new Set([...snap, ...fresh])) — nie schrumpfen.
  (b) Plausi-Guard: fresh-Set < 50% des bekannten -> partieller Load -> keine Notif + kein Merge + warn.
  (c) absence_sick nur wenn from_date >= heute-3 (Wiener Datum, td2) — alte Krankmeldungen feuern nie;
      Vergleich gegen from_date (absences hat KEINE date-Spalte -> 42703).

PURER Kern (node-eval): _absNotifOk(fromD, heuteISO) — Alters-Guard.
"""
import subprocess

from conftest import _extract_fn


def test_absnotifok_neu_und_alt(index_html, node_exe, tmp_path):
    src = _extract_fn(index_html, "_absNotifOk")
    js = src + u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
ok(_absNotifOk('2026-07-16','2026-07-16')===true,'from_date heute -> Notif ok');
ok(_absNotifOk('2026-07-14','2026-07-16')===true,'from_date heute-2 -> ok (innerhalb 3 Tage)');
ok(_absNotifOk('2026-07-13','2026-07-16')===true,'from_date heute-3 -> ok (Grenze)');
ok(_absNotifOk('2026-07-10','2026-07-16')===false,'from_date heute-6 -> ALT, keine Notif');
ok(_absNotifOk('','2026-07-16')===false,'leeres from_date -> keine Notif');
console.log('OK');
"""
    f = tmp_path / "absguard748.js"; f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_poll_union_merge(index_html):
    # Der Absence-Snapshot wird additiv gemerged, nicht komplett ersetzt.
    i = index_html.index("freshAbs.forEach(a=>{newAbsKeys.add")
    seg = index_html[i - 200:i + 400]
    assert "new Set([...snap.absenceKeys" in index_html or "new Set([...lastSnapshot.current.absenceKeys" in index_html, \
        "Absence-Snapshot wird nicht additiv gemerged (Union) -> Phantom-Risiko"


def test_poll_plausi_guard(index_html):
    # Ein verdaechtig kleines fresh-Set (< 50% des bekannten) darf keine Notif ausloesen / den Snapshot nicht schrumpfen.
    i = index_html.index("Fetch fresh absences")
    seg = index_html[i:i + 1400]
    assert "0.5" in seg, "kein Plausi-Guard (fresh < 50% des bekannten) im Absence-Poll"


def test_poll_nutzt_altersguard(index_html):
    i = index_html.index("Fetch fresh absences")
    seg = index_html[i:i + 2400]
    assert "_absNotifOk(fromD,td2())" in seg, "Absence-Notif nutzt den from_date-Alters-Guard (td2) nicht"
