# -*- coding: utf-8 -*-
"""v3.9.749 — Register #27 (P1, Screenshot-bewiesen): Ablauf-Einreihung V2 — keine Ueberschneidungen.

Sebastian: fixe MIT termin_zeit sind BELEGTE FENSTER (harte Anker, [start,start+dauer) tabu, nie verschoben);
die Mittagspause 12-13 (+ Fr-Feierabend) ist ein weiteres Fenster derselben Liste (ein Mechanismus).
Einreihung = First-Fit in die LUECKEN ueber den ganzen Tag: ab 07:00 die erste Luecke, die (Fahrzeit+Dauer+
Puffer) aufnimmt, round15; passt es nicht -> naechste Luecke (auch nach der Pause, auch nachmittags), bis
Tagesnorm-Ende. fix-vs-fix-Ueberlappung wird NICHT aufgeloest -> nur gemeldet (Badge/Zaehler).

PURE Kerne (node-eval): _dispoAblauf(items,startMin,pufferMin,taktMin,{anchors,endMin,noLunch}) und
_dispoZeitkonflikte(fixe).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"""
function ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }
function _noOverlap(placed, occ){
  var all=placed.filter(function(p){return p&&p.startMin!=null;}).map(function(p){return {s:p.startMin,e:p.endMin};}).concat(occ);
  for(var i=0;i<all.length;i++)for(var j=i+1;j<all.length;j++){ if(all[i].s<all[j].e&&all[i].e>all[j].s) return false; }
  return true;
}
"""


def _run(node_exe, tmp_path, js):
    f = tmp_path / "ablauf2_749.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_anker_blockt_vormittag_naechste_luecke(index_html, node_exe, tmp_path):
    """3h-Anker 07:00-10:00: naechster Chip startet in der ersten echten Luecke (10:00), nicht im Anker."""
    js = _block(index_html) + _OK + u"""
var anchors=[{startMin:420,endMin:600}]; // 07:00-10:00
var r=_dispoAblauf([{fahrtMin:0,dauerMin:60}],420,10,15,{anchors:anchors,endMin:990});
ok(r[0].startMin>=600,'Chip startet fruehestens 10:00 (nach dem Anker), war '+r[0].startMin);
ok(_noOverlap(r,[{s:420,e:600},{s:720,e:780}]),'kein Overlap mit Anker/Pause');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_kein_overlap_ueber_alle_paare(index_html, node_exe, tmp_path):
    """Mehrere Chips + Anker + Pause: KEIN Chip ueberlappt irgendetwas (alle Paare geprueft)."""
    js = _block(index_html) + _OK + u"""
var anchors=[{startMin:540,endMin:600}]; // 09:00-10:00 Anker
var items=[]; for(var i=0;i<5;i++)items.push({fahrtMin:5,dauerMin:75});
var r=_dispoAblauf(items,420,10,15,{anchors:anchors,endMin:990});
ok(_noOverlap(r,[{s:540,e:600},{s:720,e:780}]),'kein Chip ueberlappt Anker/Pause/andere Chips');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_pause_ganz_umgangen(index_html, node_exe, tmp_path):
    """Ein Stopp, der die Pause kreuzen wuerde, startet GANZ nach der Pause (13:00), nicht mitten drin."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:60}],690,10,15,{endMin:990}); // 11:30 Start, 60 min -> wuerde Pause kreuzen
ok(r[0].startMin===780,'Stopp rutscht ganz auf 13:00 (780), war '+r[0].startMin);
ok(r[0].endMin===840,'Ende 13:00+60=840');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_freitag_norm_ende(index_html, node_exe, tmp_path):
    """Freitag (noLunch, dayEnd 11:30=690): ein Chip der nicht mehr passt -> kein Slot (overflow)."""
    js = _block(index_html) + _OK + u"""
var r=_dispoAblauf([{fahrtMin:0,dauerMin:180},{fahrtMin:5,dauerMin:120}],420,10,15,{noLunch:true,endMin:690});
ok(r[0].startMin===420 && r[0].endMin===600,'Chip1 07:00-10:00');
ok(r[1].startMin===null,'Chip2 passt nicht mehr vor 11:30 -> overflow (null)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_nachmittag_fuellt_sich(index_html, node_exe, tmp_path):
    """6x90 min auf leerem Mo-Do-Tag: die platzierten Chips reichen bis nachmittags (letztes Ende > 16:00=960),
    nicht alles vor 12:00 gestapelt."""
    js = _block(index_html) + _OK + u"""
var items=[]; for(var i=0;i<6;i++)items.push({fahrtMin:5,dauerMin:90});
var r=_dispoAblauf(items,420,10,15,{endMin:990});
var placed=r.filter(function(p){return p&&p.startMin!=null;});
var lastEnd=Math.max.apply(null,placed.map(function(p){return p.endMin;}));
ok(lastEnd>960,'letztes Ende nach 16:00 (960), war '+lastEnd);
var nachmittag=placed.filter(function(p){return p.startMin>=780;}).length; // >=13:00
ok(nachmittag>=1,'mindestens ein Chip am Nachmittag (>=13:00)');
ok(_noOverlap(r,[{s:720,e:780}]),'kein Overlap mit der Pause');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_zeitkonflikte_fix_vs_fix(index_html, node_exe, tmp_path):
    """Zwei vereinbarte Zeiten ueberlappen (07:00/3h vs 07:15/1h) -> Konflikt gemeldet (beide scheinIds)."""
    js = _block(index_html) + _OK + u"""
var fixe=[{scheinId:'A',startMin:420,endMin:600},{scheinId:'B',startMin:435,endMin:495},{scheinId:'C',startMin:660,endMin:720}];
var k=_dispoZeitkonflikte(fixe);
ok(k['A']&&k['A'].indexOf('B')>=0,'A meldet Konflikt mit B');
ok(k['B']&&k['B'].indexOf('A')>=0,'B meldet Konflikt mit A');
ok(!k['C'],'C (keine Ueberlappung) meldet nichts');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)
