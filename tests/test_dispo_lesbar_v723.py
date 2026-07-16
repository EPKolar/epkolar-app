# -*- coding: utf-8 -*-
"""v3.9.723 — Dispo P1-e "lesbar" (Sebastian): Namen+Titel ueberall + Blockade-Gruende statt "—".

Befund (DB-verifiziert, Rechenkern KORREKT): reine Darstellung.
1. Scheine mit Nr + Kunde + Arbeit/Titel + Ort (Chip + Warteliste), klickbar (P1-b).
2. Jede Monteur×Tag-Zelle ohne Kapazitaet zeigt WARUM als grauer read-only-Chip:
   🏖️ Urlaub / 🤒 Krankenstand / ⏰ Zeitausgleich (aus N8-Abzug), 🏗 <BVH> (aus weekplan_rows).
   Mehrere -> erster + "+1". (🎌 Feiertag geskippt: keine Feiertags-Datenquelle im Kern, nicht raten.)
4. Kopfzeile: "X offen · Y ohne Monteur · Z spaeter (KW+2/+3) · W nicht unterbringbar".
NICHTS am Kapazitaets-/Abwesenheitskern geaendert — nur zusaetzlich der GRUND exponiert.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"
_ISOW = u"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%7);return d.getFullYear();};
"""


def _run(node_exe, tmp_path, js):
    f = tmp_path / "dispo723.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_abwlabel(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoAbwLabel('urlaub').icon==='🏖️','urlaub -> Strand');
ok(_dispoAbwLabel('krankenstand').icon==='🤒','krankenstand -> krank');
ok(_dispoAbwLabel('krank').icon==='🤒','krank-Alias');
ok(_dispoAbwLabel('zeitausgleich').icon==='⏰','zeitausgleich -> Uhr');
ok(_dispoAbwLabel('za').icon==='⏰','za-Alias');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_blockgrund_urlaub_und_belegung(index_html, node_exe, tmp_path):
    js = _ISOW + _block(index_html) + _OK + u"""
var mon=[{id:'m1',n:'Anton',r:'Monteur'}];
var now=new Date('2026-07-16T00:00:00');
var base=_dispoBuildInput([],mon,{},{},now,3);
// v3.9.739: Woche 0 ist die laufende Woche (Mo kann vergangen sein) -> Belegung/Urlaub auf der Folgewoche pruefen.
var monIso=base.wochen[1].tage[0].iso;
// Urlaub am Montag der Folgewoche
var am={}; am['Anton_'+monIso]={type:'urlaub',status:'genehmigt',hours:0};
var oU=_dispoBuildInput([],mon,{},am,now,3);
ok(oU.blockGrund['m1'][monIso] && oU.blockGrund['m1'][monIso][0].icon==='🏖️','Urlaub -> 🏖️-Grund');
// Belegung (weekplan_rows dieser KW) mit BVH-Name
var wp={}; wp[base.wochen[1].yr+'-'+base.wochen[1].kw]=[{z:{Mo:{ma:['m1']}},bvh:'BVH Leth'}];
var oB=_dispoBuildInput([],mon,wp,{},now,3);
ok(oB.blockGrund['m1'][monIso] && oB.blockGrund['m1'][monIso][0].icon==='🏗','Belegung -> 🏗-Grund');
ok(oB.blockGrund['m1'][monIso][0].label.indexOf('BVH Leth')>=0,'BVH-Name aus der Planungszeile (v3.9.724: + Vorab-Hinweis)');
// freier Tag ohne Abzug -> kein Grund
var oF=_dispoBuildInput([],mon,{},{},now,3);
ok(!oF.blockGrund['m1'][monIso],'freier Tag -> kein Block-Grund (zeigt spaeter --)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_chip_und_warteliste_titel(index_html):
    body = _panel(index_html)
    # Chip zeigt Arbeit/Titel (arbeitsanweisungen)
    assert "arbeitsanweisungen" in body, "Chip/Warteliste zeigt keinen Arbeits-Titel"
    # Warteliste baut eine reiche Zeile (Kunde + Ort)
    assert "kundName" in body and "arbeitsort" in body, "Warteliste ohne Kunde/Ort"


def test_zelle_zeigt_blockgrund(index_html):
    body = _panel(index_html)
    assert "_built.blockGrund" in body, "Zelle liest den Block-Grund nicht"


def test_kopf_spaeter_kw23(index_html):
    body = _panel(index_html)
    assert "spaeter (KW+2/+3)" in body or "später (KW+2/+3)" in body, "Kopfzeile ohne 'spaeter'-Zaehler"
