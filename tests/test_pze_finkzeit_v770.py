# -*- coding: utf-8 -*-
"""v3.9.770 — PZE-Ansicht in FinkZeit-Struktur (Quelle stempel_log).

Prüft den Rechenkern, der die On-Screen-Tabelle speist:
  · Soll exakt (Mo-Do 8:30, Fr 4:30, Sa/So/Feiertag 0) — _kvTagesnorm
  · +/- = Ist(netto) − Soll je Tag — _pzeTagRow.saldoMin
  · Pause ROLLENBASIERT (lohnnah!): Monteur = Auto-Abzug (default 60),
    Büro/Backoffice = 0 Auto-Abzug -> die selbst gestempelte Pause (Lücke
    zwischen den Paaren) fällt automatisch raus, es wird NICHT nochmal
    abgezogen. Das war schon so (_stPauseAbzug(role,rules)) — hier gepinnt.
  · Krank additiv in der KW-Teilsumme — _pzeSummen.krankMin
  · leeres stempel_log -> Tag ohne Stempel = Fehltag, kein Throw
"""
import re
import subprocess


def _prelude(index_html):
    """Alle Kern-Funktionen, die _pzeTagRow/_pzeSummen brauchen, als node-Prelude."""
    # _st-Helfer + Konstanten (Block 2071..2093)
    a = index_html.index("const STEMPEL_ROUND_MIN=5;")
    b = index_html.index("function _stFmtHm(")
    stblock = index_html[a:b]
    # _kvTagesnorm
    m = re.search(r"function _kvTagesnorm\(.*?\n\}", index_html, re.S)
    kv = m.group(0)
    # //@PZE-START .. //@PZE-END
    ps = index_html.index("//@PZE-START")
    pe = index_html.index("//@PZE-END")
    pze = index_html[ps:pe]
    # isoWof-Stub (nur _pzeKW braucht es; wir testen _pzeKW nicht)
    stub = "function isoWof(){return 0;}\n"
    return stblock + "\n" + kv + "\n" + stub + pze + "\n"


def _node(index_html, body, tmp_path):
    js = _prelude(index_html) + "\n" + body
    f = tmp_path / "pze.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    return r.stdout.strip().splitlines()[-1]


def test_soll_exakt(index_html, tmp_path):
    got = _node(index_html,
        "console.log(JSON.stringify(["
        "_kvTagesnorm(1,false),_kvTagesnorm(4,false),_kvTagesnorm(5,false),"
        "_kvTagesnorm(0,false),_kvTagesnorm(6,false),_kvTagesnorm(3,true)]));", tmp_path)
    assert got == "[8.5,8.5,4.5,0,0,0]", "Soll falsch (Mo-Do 8,5 / Fr 4,5 / So/Sa/Feiertag 0). Bekommen: " + got


def test_saldo_ist_minus_soll(index_html, tmp_path):
    # Monteur, Mo, 08:00-16:30 = 8,5h brutto, Auto-Pause 60 -> netto 7,5h=450; Soll 510 -> Saldo -60
    body = ("var ev=[{direction:'kommen',ts:'2026-06-15T08:00:00'},{direction:'gehen',ts:'2026-06-15T16:30:00'}];"
            "var r=_pzeTagRow(ev,'Monteur',{default:60},8.5,0,false);"
            "console.log(JSON.stringify([r.nettoMin,r.sollMin,r.saldoMin,r.pauseMin]));")
    got = _node(index_html, body, tmp_path)
    assert got == "[450,510,-60,60]", "Saldo != Ist-Soll oder Pause falsch. Erwartet [450,510,-60,60], bekommen: " + got


def test_pause_rollenbasiert_buero_vs_monteur(index_html, tmp_path):
    # LOHNNAH: derselbe Arbeitstag, Rolle entscheidet.
    # Monteur 07:00-16:00 = 9h brutto, Auto-60 -> 480 netto, Pause 60.
    # Büro (Backoffice, Abzug 0) stempelt Pause SELBST: 08:00-12:00 + 12:30-16:00 = 450 netto,
    #   die 30-min-Lücke ist raus (kein Paar), es wird NICHT nochmal abgezogen -> Pause 0.
    body = ("var mont=[{direction:'kommen',ts:'2026-06-15T07:00:00'},{direction:'gehen',ts:'2026-06-15T16:00:00'}];"
            "var rm=_pzeTagRow(mont,'Monteur',{Backoffice:0,default:60},8.5,0,false);"
            "var buero=[{direction:'kommen',ts:'2026-06-15T08:00:00'},{direction:'gehen',ts:'2026-06-15T12:00:00'},"
            "{direction:'kommen',ts:'2026-06-15T12:30:00'},{direction:'gehen',ts:'2026-06-15T16:00:00'}];"
            "var rb=_pzeTagRow(buero,'Backoffice',{Backoffice:0,default:60},8.5,0,false);"
            "console.log(JSON.stringify([rm.nettoMin,rm.pauseMin,rb.nettoMin,rb.pauseMin]));")
    got = _node(index_html, body, tmp_path)
    assert got == "[480,60,450,0]", (
        "Pause nicht rollenbasiert. Erwartet Monteur netto 480/Pause 60, Büro netto 450/Pause 0 "
        "(gestempelte 30-min-Pause NICHT nochmal abgezogen). Bekommen: " + got)


def test_krank_in_kw_summe(index_html, tmp_path):
    body = ("var rows=[{nettoMin:510,sollMin:510,saldoMin:0,pauseMin:60,projMin:0,krankMin:0},"
            "{nettoMin:510,sollMin:510,saldoMin:0,pauseMin:0,projMin:0,krankMin:510}];"
            "var s=_pzeSummen(rows);console.log(JSON.stringify([s.nettoMin,s.krankMin]));")
    got = _node(index_html, body, tmp_path)
    assert got == "[1020,510]", "KW-Teilsumme summiert Krank nicht additiv. Bekommen: " + got


def test_leeres_stempel_log_kein_throw(index_html, tmp_path):
    # Werktag ohne Stempel, ohne Gutschrift -> Fehltag, netto 0, kein Throw
    body = ("var r=_pzeTagRow([],'Monteur',{default:60},8.5,0,false);"
            "var g=_pzeGroupByDay([]);"
            "console.log(JSON.stringify([r.nettoMin,r.fehltag,r.saldoMin,Object.keys(g).length]));")
    got = _node(index_html, body, tmp_path)
    assert got == "[0,true,-510,0]", "Leeres Log nicht sauber (Fehltag/Saldo). Bekommen: " + got


def test_buero_gutschrift_kein_doppelabzug(index_html, tmp_path):
    # genehmigte Abwesenheit ohne Stempel -> Gutschrift = Soll, Pause 0
    body = ("var r=_pzeTagRow([],'Backoffice',{Backoffice:0,default:60},8.5,0,true);"
            "console.log(JSON.stringify([r.nettoMin,r.pauseMin,r.gutschrift,r.saldoMin]));")
    got = _node(index_html, body, tmp_path)
    assert got == "[510,0,true,0]", "Gutschrift falsch. Erwartet netto=Soll 510, Saldo 0. Bekommen: " + got
