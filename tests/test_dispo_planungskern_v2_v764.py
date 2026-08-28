# -*- coding: utf-8 -*-
"""v3.9.764 — Register #28 Planungskern V2: 28a MINUTEN statt km + 28b Nachbarschafts-Bonus.

28a: Score/2opt optimieren auf FAHR-MINUTEN (cfg.dist -> _dispoStrecke.min: plz_distanz-Matrix-Minute,
sonst Haversine-km/DISPO_KMH->min). Leer-tolerant: ohne Matrix proportional zu km = identischer Plan;
mit Matrix echte Fahrzeit. 28b: ein Stopp <DISPO_NAH_MIN (15) Fahrminuten zum Schein gibt einen
Score-Bonus (DISPO_NAH_BONUS=30000) — buendelt NAHE (nicht exakt gleiche) Adressen auf denselben Tag.
Magnitude ZWISCHEN exakter Buendelung (100000) und Wochen-Malus (10000): schlaegt bis zu 3 Wochen Malus,
NIE die exakte Buendelung. Topf (Prio-Reihung, Greedy) laeuft davor -> schlaegt den Bonus.
"""
import re
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


# ---------------------------------------------------------------- static

def test_28a_dist_nutzt_minuten(index_html):
    # die cfg.dist-Funktion (Score/2opt) gibt st.min zurueck, nicht st.km.
    #
    # v3.9.888 NACHGEZOGEN - nicht abgeschwaecht: der Rueckfallwert bei UNBEKANNTER
    # Distanz ist nicht mehr DISPO_INNERORTS_MIN (5), sondern DISPO_UNBEKANNT_MIN (45),
    # und das known-Flag wird beachtet. Grund: 5 Minuten liessen einen Stopp ohne
    # bekannte PLZ so billig aussehen wie einen um die Ecke - 80 km weg wie nebenan.
    # v3.9.856 hat genau das fuer near() geheilt, dist() blieb uebrig. Die EIGENSCHAFT,
    # die dieser Riegel seit v764 sichert - Optimierung auf MINUTEN statt km - gilt
    # unveraendert und wird weiter geprueft.
    assert "return (st&&st.known&&st.min!=null)?st.min:DISPO_UNBEKANNT_MIN;}" in index_html, \
        "28a/888: cfg.dist optimiert nicht auf Minuten oder beachtet das known-Flag nicht"
    assert "return st.km!=null?st.km:DISPO_INNERORTS_KM;}" not in index_html, \
        "28a: alte km-basierte dist noch vorhanden"


def test_28b_score_und_konstanten(index_html):
    assert "var DISPO_NAH_MIN=15;" in index_html, "DISPO_NAH_MIN fehlt"
    assert re.search(r"var DISPO_NAH_BONUS=30000;", index_html), "DISPO_NAH_BONUS fehlt/veraendert"
    # v3.9.856: Nachbarschafts-Check ist jetzt known-gated (near()) statt distanz-blind
    # (dist()<NAH sah die INNERORTS-Attrappe bei unbekannter Geo als echte Naehe).
    assert "if(near(stops[qn],s)){nah=true;break;}" in index_html, "28b: Nachbarschafts-Check (known-gated near()) fehlt"
    assert "return !!(st.known&&st.min!=null&&st.min<DISPO_NAH_MIN);}" in index_html, "28b: near() nicht known-gated"
    assert "(nah?-DISPO_NAH_BONUS:0)" in index_html, "28b: Nachbarschafts-Bonus nicht im Score"
    # Magnitude-Ordnung: Buendel (100000) > Nachbar (30000) > Wochen-Malus (10000).
    assert 100000 > 30000 > 10000, "Magnitude-Ordnung Buendel>Nachbar>Wochen verletzt (Konstanten anpassen)"


# ---------------------------------------------------------------- node-eval

_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_28a_strecke_liefert_minuten(index_html, node_exe, tmp_path):
    """_dispoStrecke.min = Matrix-Minute wenn vorhanden, sonst Haversine-km/DISPO_KMH->min (28a-Quelle)."""
    js = _block(index_html) + _OK + u"""
// Matrix-Treffer -> Matrix-Minute:
var m=_dispoStrecke('3001','3002',{},{'3001|3002':{km:10,min:8}});
ok(m.min===8,'Matrix-min genutzt (8), war '+m.min);
// gleiche PLZ -> Innerorts (5 min):
var g=_dispoStrecke('3001','3001',{},{});
ok(g.min===5,'gleiche PLZ -> 5 min, war '+g.min);
// nur Geo (keine Matrix) -> Haversine-min > 0, aus km/DISPO_KMH:
var h=_dispoStrecke('3001','3002',{'3001':{lat:48.4,lon:15.7},'3002':{lat:48.6,lon:16.0}},{});
ok(h.min>=5&&h.known===true,'Haversine-min gesetzt+known, war '+JSON.stringify(h));
// unbekannt -> min immer gesetzt (Innerorts-Fallback), nie null:
var u=_dispoStrecke('9998','9999',{},{});
ok(u.min===5&&u.known===false,'unbekannt -> min=5, known=false');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "strecke764.js")


def test_28b_nachbarschaft_und_buendel(index_html, node_exe, tmp_path):
    """Nahe (diff Adresse, gleiche PLZ) UND exakt gebuendelte Scheine landen auf dem Tag des ersten Stopps;
    bei genug Kapazitaet zieht der Nachbarschafts-Bonus S2/S3 zu S1."""
    js = _block(index_html) + _OK + u"""
function tagKeyOf(plan,mid,sid){for(var tk in plan[mid]){if((plan[mid][tk]||[]).some(function(c){return c.scheinId===sid;}))return tk;}return null;}
var cfg={
  monteure:[{id:'M1',name:'A'}],
  tage:[{key:'mo',woche:0,normMin:480},{key:'di',woche:0,normMin:480}],
  firma:{plz:'F'},
  // dist auf MINUTEN: gleiche PLZ -> 5 (nah), sonst 30 (fern):
  dist:function(x,y){var px=(x&&x.plz)||'F',py=(y&&y.plz)||'F';return px===py?5:30;},
  kapAbzug:{}, hatFz:function(){return true;}, horizont:1,
  scheine:[
    {id:'S1',adrKey:'a1',plz:'P1',dauerMin:60,monteurId:'M1',alterMs:1},
    {id:'S2',adrKey:'a2',plz:'P1',dauerMin:60,monteurId:'M1',alterMs:2}, // gleiche PLZ, andere Adresse -> NAH
    {id:'S3',adrKey:'a1',plz:'P1',dauerMin:60,monteurId:'M1',alterMs:3}  // gleiche Adresse -> BUENDEL
  ]
};
var r=_dispoPlan(cfg);
var t1=tagKeyOf(r.plan,'M1','S1');
ok(t1!=null,'S1 eingeplant');
ok(tagKeyOf(r.plan,'M1','S2')===t1,'S2 (nah) landet auf S1s Tag (Nachbarschafts-Bonus)');
ok(tagKeyOf(r.plan,'M1','S3')===t1,'S3 (exakt gebuendelt) landet auf S1s Tag');
ok((r.warteliste||[]).length===0,'nichts auf der Warteliste (Kapazitaet reicht)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "nachbar764.js")
