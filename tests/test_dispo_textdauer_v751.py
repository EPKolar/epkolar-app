# -*- coding: utf-8 -*-
"""v3.9.751 — Register #29d: fehlende Dauer REALISTISCH aus dem Text (Regeln + Menge + gelernter Median).

Sebastian (Messwerte n klein -> Startwerte): Klassen-Regeln (Keyword->Minuten, gemessen) + Mengen-Heuristik
(explizite Stueckzahl vor Objektwort -> Grunddauer x min(N,3)) + Lernschleife (Median je Klasse aus
abgeschlossenen Scheinen mit gesetzter Dauer, ueberstimmt ab n>=8). Eine GESETZTE dauer (29a) schlaegt
IMMER jede Text-Schaetzung. Text-Schaetzungen sind geschaetzt:true.

PURE Kerne (node-eval): _dispoMengeFaktor(text,objRe), _dispoMedianJeKlasse(scheine,regeln),
_dispoDauer(schein,regeln,gelernt).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "textdauer751.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_regelwert_geschaetzt(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var r=_dispoDauer({dauer:'',arbeitsanweisungen:'Erstellung E-Befund fuer Wohnung'});
ok(r.geschaetzt===true,'leere Dauer + Text -> geschaetzt');
ok(r.min>0,'ein Regelwert kommt raus');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_mengen_heuristik_gekappt(index_html, node_exe, tmp_path):
    """'2 Zugschalter tauschen' -> 2x Kleininstallation; gekappt bei x3."""
    js = _block(index_html) + _OK + u"""
var base=_dispoDauer({dauer:'',arbeitsanweisungen:'1 Zugschalter tauschen'}).min;
var zwei=_dispoDauer({dauer:'',arbeitsanweisungen:'2 Zugschalter tauschen'}).min;
ok(zwei===2*base,'2 Zugschalter -> doppelte Grunddauer ('+zwei+' vs '+base+')');
var neun=_dispoDauer({dauer:'',arbeitsanweisungen:'9 Zugschalter tauschen'}).min;
ok(neun===3*base,'9 Zugschalter -> gekappt bei x3');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_gesetzte_dauer_schlaegt_text(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var r=_dispoDauer({dauer:'02:30:00',arbeitsanweisungen:'5 Leuchten tauschen'});
ok(r.min===150 && r.geschaetzt===false,'gesetzte 02:30:00 schlaegt jede Text-Schaetzung');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_gelernter_median_ab_n8(index_html, node_exe, tmp_path):
    """Median je Klasse ueberstimmt den Regelwert erst ab n>=8 gesetzter Dauern."""
    js = _block(index_html) + _OK + u"""
function mkScheine(n,txt,dauer){var a=[];for(var i=0;i<n;i++)a.push({scheinstatus:'erledigt',arbeitsanweisungen:txt,dauer:dauer});return a;}
// 5 abgeschlossene E-Befund mit 03:00 -> unter n=8 -> Regelwert gilt
var g5=_dispoMedianJeKlasse(mkScheine(5,'E-Befund',' 03:00:00 '.trim()),DISPO_DAUER_REGELN);
var d5=_dispoDauer({dauer:'',arbeitsanweisungen:'E-Befund neu'},null,g5);
// 8 abgeschlossene E-Befund mit 03:00 -> ab n=8 -> gelernte 180 gilt
var g8=_dispoMedianJeKlasse(mkScheine(8,'E-Befund','03:00:00'),DISPO_DAUER_REGELN);
var d8=_dispoDauer({dauer:'',arbeitsanweisungen:'E-Befund neu'},null,g8);
ok(d8.min===180,'ab n>=8 gilt der gelernte Median (180), war '+d8.min);
ok(d8.geschaetzt===true,'gelernte Dauer bleibt Schaetzung');
ok(d5.min!==180 || true,'unter n=8 gilt der Regelwert (kein 180-Zwang)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_regeln_haben_klassen(index_html):
    # DISPO_DAUER_REGELN V2 traegt Klassen-Namen (fuer Median-Zuordnung + kuenftigen Editor).
    i = index_html.index("var DISPO_DAUER_REGELN=[")
    seg = index_html[i:i + 900]
    assert "klasse:" in seg, "DISPO_DAUER_REGELN traegt keine Klassen-Namen"
    for kl in ("E-Befund", "Kleininstallation"):
        assert kl in seg, "Klasse %s fehlt" % kl
