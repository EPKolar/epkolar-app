# -*- coding: utf-8 -*-
"""v3.9.759 — Register #28d: Vollbilanz im Dispo-Panel-Kopf, test-gepinnte Invariante.

Sebastian: der Panel-Kopf zeigt "N offen: X fix · Y Vorschlaege · Warteliste · nicht-unterbringbar".
INVARIANTE: die Summe deckt ALLE dispo-relevanten offenen Scheine (AS_GRP_OFFEN ohne 'aufgeschoben') —
nie ein Loch. Ein Schein, der in keinen Eimer faellt (Zukunfts-Termin ohne Monteur / ausserhalb Horizont),
landet SICHTBAR im rest-Eimer, wird nie verschluckt.

PURER Kern (node-eval): _dispoBilanz(openIds,fixIds,vorschlagIds,warteMitIds,warteOhneIds) partitioniert
disjunkt (ein Schein zaehlt genau einmal, erster Eimer gewinnt) und zaehlt NUR openIds -> Invariante per
Konstruktion. Die Panel-Kopf-Anzeige ist struktur-gepinnt.
"""
import re
import subprocess


# ---------------------------------------------------------------- static wiring

def test_bilanz_fn_und_export(index_html):
    assert "function _dispoBilanz(openIds,fixIds,vorschlagIds,warteMitIds,warteOhneIds){" in index_html, \
        "_dispoBilanz fehlt/Signatur veraendert"
    assert "window._dispoBilanz=_dispoBilanz;" in index_html, "_dispoBilanz nicht als window-Export"


def test_bilanz_memo_vor_early_return(index_html):
    """Der _bilanz-useMemo MUSS vor dem Early-Return im DispoPanel stehen (React-Hook-Reihenfolge)."""
    start = index_html.index("function DispoPanel({")
    memo = index_html.index("var _bilanz=_react.useMemo", start)
    early = index_html.index('return h(\'div\',{style:{padding:20,color:V.dm}},"Vorschlagsplanung konnte nicht berechnet werden.")', start)
    assert memo < early, "_bilanz-Hook steht NACH dem Early-Return -> Hook-Reihenfolge-Bug (P0-Risiko)"
    seg = index_html[memo:memo + 1300]
    assert "_dispoBilanz(" in seg, "_bilanz-Memo ruft _dispoBilanz nicht"
    assert "!=='aufgeschoben'" in seg, "openIds schliesst 'aufgeschoben' (Parkplatz) nicht aus"
    assert "AS_GRP_OFFEN" in seg, "openIds nicht aus AS_GRP_OFFEN"


def test_kopf_zeigt_vollbilanz(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    for token in ("_bilanz.total", "_bilanz.fix", "_bilanz.vorschlaege", "_bilanz.warteliste",
                  "_bilanz.nichtUnterbringbar", "_bilanz.rest"):
        assert token in body, "Panel-Kopf zeigt %s nicht" % token
    assert "fix" in body and "Vorschl" in body and "Warteliste" in body, "Vollbilanz-Labels fehlen im Kopf"


# ---------------------------------------------------------------- node-eval invariant

_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _extract(index_html):
    start = index_html.index("function _dispoBilanz(")
    end = index_html.index("\n}", start) + 2
    return index_html[start:end]


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_invariante_summe_gleich_total(index_html, node_exe, tmp_path):
    js = _extract(index_html) + _OK + u"""
function summe(b){ return b.fix+b.vorschlaege+b.warteliste+b.nichtUnterbringbar+b.rest; }

// (1) saubere Partition, kein Loch:
var b=_dispoBilanz(['a','b','c','d','e'],['a'],['b','c'],['d'],['e']);
ok(b.total===5,'total 5'); ok(summe(b)===5,'Summe==total (kein Loch)');
ok(b.fix===1&&b.vorschlaege===2&&b.warteliste===1&&b.nichtUnterbringbar===1&&b.rest===0,'Eimer korrekt');

// (2) Loch: 2 offene Scheine in keinem Eimer -> rest, Summe deckt weiter total:
var h=_dispoBilanz(['a','b','c'],['a'],[],[],[]);
ok(h.total===3&&h.rest===2&&summe(h)===3,'Loch sichtbar im rest, Summe==total');
ok(h.restIds.indexOf('b')>=0&&h.restIds.indexOf('c')>=0,'restIds nennt die unklassifizierten Scheine');

// (3) Eimer-ID nicht in open -> ignoriert (nie ueber-zaehlen):
var x=_dispoBilanz(['a'],['a','ZZZ'],[],[],[]);
ok(x.total===1&&x.fix===1&&summe(x)===1,'ID ausserhalb open wird nicht gezaehlt');

// (4) Ueberlappung -> disjunkt (erster Eimer gewinnt, genau 1x):
var o=_dispoBilanz(['a'],['a'],['a'],['a'],['a']);
ok(o.fix===1&&o.vorschlaege===0&&o.warteliste===0&&o.nichtUnterbringbar===0&&o.rest===0,'disjunkt: fix gewinnt');
ok(summe(o)===1,'Ueberlappung nie doppelt gezaehlt');

// (5) Duplikate in open werden dedupliziert:
var d=_dispoBilanz(['a','a','b'],['a'],[],[],[]);
ok(d.total===2&&summe(d)===2,'open dedupliziert');

// (6) leer:
var e=_dispoBilanz([],[],[],[],[]);
ok(e.total===0&&summe(e)===0,'leer -> alles 0');

// (7) Invariante ueber viele gemischte Faelle (Summe IMMER == total):
var buckets=[['a','b'],['c'],['d','e','x'],['f']];  // x nicht in open -> muss ignoriert werden
var open=['a','b','c','d','e','f','g','h'];          // g,h -> Loch
var m=_dispoBilanz(open,buckets[0],buckets[1],buckets[2],buckets[3]);
ok(m.total===8,'total 8'); ok(summe(m)===8,'Summe==total trotz Loch+Fremd-ID'); ok(m.rest===2,'g,h im rest');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "bilanz_759.js")
