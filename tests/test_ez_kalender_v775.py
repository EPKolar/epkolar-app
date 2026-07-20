# -*- coding: utf-8 -*-
"""v3.9.775 — Entfernungszulage-Vergabe als Outlook-Kalender (Monat/Woche).

ETAPPE 2: Kalender flaggt Tage per Klick -> entfernungszulage_tage (42P01-tolerant).
ETAPPE 3 (Sebastian freigegeben, LOHNRELEVANT): "VORBELEGUNG gilt, Flag korrigiert nur".
  - Vorbelegt sind alle Tage mit Tages-Anwesenheit >6h (dieselbe Quelle wie die Ergebnistabelle).
  - Das Flag speichert nur die ABWEICHUNG: aktiv=true = dazu/bestaetigt, aktiv=false = weggeklickte Vorbelegung.
    Darum laedt _ezFetch BEIDE (aktiv=true UND false) als flags[key]={aktiv:bool}.
  - eff je Tag = Flag (falls vorhanden) sonst >6h. Abgerechnete EZ-Menge = eff-Tage x 11,71 (LA 2740),
    in Ergebnistabelle UND CSV — Fallback ohne Flags = reine Vorbelegung (kein stiller Sprung auf 0).

BEWUSSTE AENDERUNG ggue. v3.9.774: die abgerechnete EZ-MENGE wechselt von automatischer >6h-Zaehlung
(via _kvZulagenMonat) auf die eff-basierte Kalender-Vergabe (_ezEffTage). Der SATZ 11,71 und der
Tages-Kern _kvTaggeldTag bleiben unveraendert (test_rechnung_unberuehrt pinnt das).

Pure Helfer (_ezWtag/_ezMonthGrid/_ezWeekDays/_ezKW/_ezKey/_ezDayEff/_ezEffTage) werden per node-eval geprueft.
"""
import re
import subprocess


def _block(index_html):
    """Der zusammenhaengende Modul-Block der pure Helfer (bis vor _ezFetch)."""
    start = index_html.index("function _ezWtag(iso){")
    end = index_html.index("async function _ezFetch(ym){", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "ez775.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_ezwtag(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_ezWtag('2026-07-01')==='Mi','1.7.2026 = Mittwoch');
ok(_ezWtag('2026-06-29')==='Mo','29.6.2026 = Montag');
ok(_ezWtag('2026-07-05')==='So','5.7.2026 = Sonntag');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezmonthgrid_juli2026(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var g=_ezMonthGrid(2026,6); // Juli 2026 (month0=6)
ok(g[0][0].iso==='2026-06-29','erste Zelle = Mo 29.6.');
ok(g[0][0].inMonth===false,'29.6. nicht im Monat');
ok(g[0][2].iso==='2026-07-01','grid[0][2] = 1.7.');
ok(g[0][2].inMonth===true,'1.7. im Monat');
for(var i=0;i<g.length;i++){ok(g[i].length===7,'Woche '+i+' hat 7 Tage');}
var found=false;g.forEach(function(w){w.forEach(function(o){if(o.iso==='2026-07-31'){found=o.inMonth;}});});
ok(found===true,'31.7. vorhanden + inMonth');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezmonthgrid_year_boundary(index_html, node_exe, tmp_path):
    """Dezember 2025 -> Januar-Ueberhang, alle Wochen 7 Tage, 31.12. inMonth."""
    js = _block(index_html) + _OK + u"""
var g=_ezMonthGrid(2025,11); // Dezember 2025
for(var i=0;i<g.length;i++){ok(g[i].length===7,'Dez-Woche '+i+' hat 7 Tage');}
ok(_ezWtag(g[0][0].iso)==='Mo','erste Zelle ist ein Montag');
var last=false;g.forEach(function(w){w.forEach(function(o){if(o.iso==='2025-12-31')last=o.inMonth;});});
ok(last===true,'31.12. inMonth');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezweekdays(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
var w=_ezWeekDays('2026-07-01'); // Mittwoch -> Woche Mo 29.6. .. So 5.7.
ok(w.length===7,'7 Tage');
ok(w[0].iso==='2026-06-29','Mo = 29.6.');
ok(w[6].iso==='2026-07-05','So = 5.7.');
ok(_ezWtag(w[0].iso)==='Mo','erster Tag Montag');
ok(_ezWtag(w[6].iso)==='So','letzter Tag Sonntag');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezkw(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_ezKW('2026-07-01')===27,'1.7.2026 = KW27');
ok(_ezKW('2026-01-01')===1,'1.1.2026 = KW1');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezdayeff(index_html, node_exe, tmp_path):
    """eff je Tag: Flag ueberschreibt Vorbelegung (>6h)."""
    js = _block(index_html) + _OK + u"""
ok(_ezDayEff(8,undefined)===true,'8h ohne Flag -> eff (Vorbelegung)');
ok(_ezDayEff(4,undefined)===false,'4h ohne Flag -> nicht eff');
ok(_ezDayEff(8,{aktiv:false})===false,'Flag aktiv=false zieht 8h-Tag ab');
ok(_ezDayEff(3,{aktiv:true})===true,'Flag aktiv=true zaehlt 3h-Tag dazu');
ok(_ezDayEff(0,{aktiv:true})===true,'Flag aktiv=true auf 0h-Tag zaehlt dazu');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezefftage(index_html, node_exe, tmp_path):
    """_ezEffTage(daysMap,flags,wid[,satz]) -> {tage,sum}. Die 5 von Sebastian benannten Faelle (a)-(e)."""
    js = _block(index_html) + _OK + u"""
var W='w1';
// (a) Vorbelegung >6h ohne Flag zaehlt
var a=_ezEffTage({'2026-07-01':8},{},W);
ok(a.tage===1,'(a) 8h ohne Flag = 1 Tag');
// (b) Flag aktiv=false auf vorbelegtem Tag zieht ab
var b=_ezEffTage({'2026-07-01':8,'2026-07-02':8},{'w1_2026-07-01':{aktiv:false}},W);
ok(b.tage===1,'(b) 2 vorbelegt, 1 weggeklickt = 1 Tag');
// (c) Flag aktiv=true auf <6h-Tag zaehlt dazu (auch 0h-Tag ohne Anwesenheit)
var c=_ezEffTage({'2026-07-01':3},{'w1_2026-07-01':{aktiv:true}},W);
ok(c.tage===1,'(c) 3h-Tag dazugeflaggt = 1 Tag');
var c2=_ezEffTage({},{'w1_2026-07-03':{aktiv:true}},W);
ok(c2.tage===1,'(c2) 0h-Tag nur per Flag = 1 Tag');
// (d) Menge = tage x 11,71
var d=_ezEffTage({'2026-07-01':8,'2026-07-02':9},{},W);
ok(d.tage===2 && Math.abs(d.sum-23.42)<1e-9,'(d) 2 Tage x 11,71 = 23,42');
// (e) leere flags -> Menge = alle >6h-Tage (Vorbelegungs-Fallback)
var e=_ezEffTage({'2026-07-01':8,'2026-07-02':7,'2026-07-03':4},{},W);
ok(e.tage===2 && Math.abs(e.sum-23.42)<1e-9,'(e) Fallback = alle >6h-Tage');
// Satz-Override moeglich (Aufrufer reicht kv.taggeldAb6h)
var s=_ezEffTage({'2026-07-01':8},{},W,11.71);
ok(Math.abs(s.sum-11.71)<1e-9,'Satz-Param wirkt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_riedmann_juli_beispiel(index_html, node_exe, tmp_path):
    """€-Beispiel: 8 Tage vorbelegt, unkorrigiert = 93,68 €; 2 weggeklickt -> 6 Tage = 70,26 €."""
    js = _block(index_html) + _OK + u"""
var W='R', days={};
['2026-07-01','2026-07-02','2026-07-03','2026-07-06','2026-07-07','2026-07-08','2026-07-09','2026-07-10'].forEach(function(d){days[d]=8;});
var unkorr=_ezEffTage(days,{},W);
ok(unkorr.tage===8 && Math.abs(unkorr.sum-93.68)<1e-9,'8 Tage vorbelegt = 93,68');
var korr=_ezEffTage(days,{'R_2026-07-09':{aktiv:false},'R_2026-07-10':{aktiv:false}},W);
ok(korr.tage===6 && Math.abs(korr.sum-70.26)<1e-9,'2 weggeklickt -> 6 Tage = 70,26');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezkey(index_html):
    """_ezKey spiegelt den PK (worker_id,datum), Datum auf 10 Zeichen gekappt."""
    assert "function _ezKey(wid,datum){" in index_html
    m = re.search(r"function _ezKey\(wid,datum\)\{[^}]*return ([^;]+);", index_html)
    assert m, "_ezKey-Rumpf nicht gefunden"
    body = m.group(1)
    assert "'_'" in body and ".slice(0,10)" in body


def test_datenzugriff_existiert(index_html):
    """Flag-Schreibweg: _ezFetch/_ezSet auf entfernungszulage_tage, feature-detect-tolerant (42P01/404).

    Etappe 3: _ezFetch muss aktiv=true UND aktiv=false laden (als {aktiv:bool}), nicht nur die true-Zeilen.
    """
    assert "async function _ezFetch(ym){" in index_html
    assert "async function _ezSet(wid,datum,aktiv,von){" in index_html
    fetch_start = index_html.index("async function _ezFetch(ym){")
    fetch_end = index_html.index("async function _ezSet(", fetch_start)
    fetch_body = index_html[fetch_start:fetch_end]
    assert "/entfernungszulage_tage?select=worker_id,datum,aktiv" in fetch_body
    assert "42P01" in fetch_body and "404" in fetch_body, "Fetch muss fehlende Tabelle tolerieren"
    assert "missing:true" in fetch_body
    assert "{aktiv:!!x.aktiv}" in fetch_body, "Etappe 3: aktiv=true UND false laden"
    assert "if(x&&x.aktiv)f[" not in fetch_body, "true-Zeilen duerfen nicht mehr weggefiltert werden"
    set_start = index_html.index("async function _ezSet(")
    set_end = index_html.index("function EZKalender(", set_start)
    set_body = index_html[set_start:set_end]
    assert "on_conflict=worker_id,datum" in set_body
    assert "resolution=merge-duplicates,return=minimal" in set_body


def test_window_export_pure_helfer(index_html):
    for name in ("_ezWtag", "_ezMonthGrid", "_ezWeekDays", "_ezKey", "_ezDayEff", "_ezEffTage"):
        assert "window." + name + "=" + name in index_html, "fehlender window-Export: " + name


def test_kalender_komponente(index_html):
    """Outlook-Grid als eigene Komponente, von KVZulagenReport gerendert; MA-Auswahl, Missing-Hinweis, 3 Zustaende."""
    assert "function EZKalender(props){" in index_html
    assert "h(EZKalender,{" in index_html
    assert "days:_ezDaysFor(ezWid)" in index_html, "EZKalender braucht die Vorbelegungs-Tage (days)"
    assert "Bitte Mitarbeiter wählen" in index_html
    assert "Tabelle entfernungszulage_tage fehlt" in index_html
    # 3 sichtbar unterscheidbare Zustaende: u.a. durchgestrichener (weggeklickter) Tag
    assert "textDecoration:strike?'line-through':'none'" in index_html
    # Klick schreibt aktiv=!eff
    assert "var eff=_ezDayEff(dm[iso]||0,prevEntry);var want=!eff;" in index_html


def test_menge_eff_basiert(index_html):
    """Die abgerechnete EZ-Summe (Ergebnistabelle + CSV) haengt an _ezEffTage, nicht mehr an der Auto-Zaehlung."""
    assert "_ezEffTage(byW[wid].days,ezFlags,wid" in index_html
    assert "taggeldSum:ez.sum" in index_html
    # Spaltenkoepfe bleiben byte-stabil (Tage>6h/Tage>11h = Info); nur der EUR-Wert ist eff-basiert.
    assert "['Monat','Monteur','Tage>6h','Tage>11h','Entfernungszulage EUR']" in index_html
    assert "r.tage6,r.tage11,_eur(r.taggeldSum)" in index_html


def test_rechnung_unberuehrt(index_html):
    """LOHNRELEVANTE GRENZE: der SATZ 11,71 und der Tages-Kern _kvTaggeldTag bleiben EXAKT.

    Bewusst NICHT gepinnt: die abgerechnete EZ-MENGE — die wechselt in v3.9.775 (Sebastian, Etappe 3, freigegeben)
    von automatischer >6h-Zaehlung auf die eff-basierte Kalender-Vergabe (siehe test_menge_eff_basiert). Der Satz
    und die Rechenfunktionen selbst bleiben unveraendert; KEIN 4-Tage-Deckel.
    """
    assert "taggeldAb6h:11.71," in index_html
    for fn in ("function _kvTaggeldTag(", "function _kvZulagenMonat(", "function _pzeTagRow("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
    # KEIN 4-Tage-Deckel: _ezEffTage summiert ungedeckelt (nur *satz).
    ez_start = index_html.index("function _ezEffTage(")
    ez_body = index_html[ez_start:index_html.index("\n}", ez_start)]
    assert "Math.min" not in ez_body, "kein Deckel in _ezEffTage"
