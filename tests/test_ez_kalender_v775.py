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
    """v3.9.785: _ezDayEff -> STUFE ('klein'|'mittel'|'gross'|''). Flag-Stufe-Override gewinnt (auch am
    genehmigten Abwesenheitstag, v783); ohne Flag: genehmigt-abwesend -> '' sonst >6h -> Vorschlag 'klein'."""
    js = _block(index_html) + _OK + u"""
ok(_ezDayEff(8,undefined)==='klein','8h ohne Flag -> Vorschlag klein');
ok(_ezDayEff(4,undefined)==='','4h ohne Flag -> keine');
ok(_ezDayEff(8,{stufe:null})==='','Flag null = keine (abgelehnt)');
ok(_ezDayEff(3,{stufe:'klein'})==='klein','Flag klein auf 3h-Tag zaehlt');
ok(_ezDayEff(8,{stufe:'mittel'})==='mittel','Flag mittel gewinnt vor Vorschlag');
ok(_ezDayEff(0,{stufe:'gross'})==='gross','Flag gross auf 0h-Tag zaehlt');
// v3.9.783 (LOHNRELEVANT): genehmigte Abwesenheit (3. Param) -> kein Vorschlag; gesetzte Stufe zaehlt trotzdem.
ok(_ezDayEff(8,undefined,true)==='','8h Krank (genehmigt) ohne Flag -> keine');
ok(_ezDayEff(8,undefined,false)==='klein','absGenehmigt=false -> Vorschlag klein');
ok(_ezDayEff(8,{stufe:'gross'},true)==='gross','8h Krank + Flag gross -> Override zaehlt DOCH');
ok(_ezDayEff(8,{stufe:null},true)==='','8h Krank + Flag keine -> raus');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezefftage(index_html, node_exe, tmp_path):
    """v3.9.785: _ezEffTage(daysMap,flags,wid,saetze,absSet) -> {tageKlein,tageMittel,tageGross,sum}.
    Genau EINE Stufe je Tag; sum je Stufe*Satz (klein 11,94 / mittel 30 / gross 62,04), kein Deckel."""
    js = _block(index_html) + _OK + u"""
var W='w1';var SA={klein:11.94,mittel:30.00,gross:62.04};
// Vorbelegung >6h ohne Flag = klein
var a=_ezEffTage({'2026-07-01':8},{},W,SA);
ok(a.tageKlein===1 && Math.abs(a.sum-11.94)<1e-9,'8h ohne Flag = 1 klein / 11,94');
// Flag null (keine) zieht ab
var b=_ezEffTage({'2026-07-01':8,'2026-07-02':8},{'w1_2026-07-01':{stufe:null}},W,SA);
ok(b.tageKlein===1,'1 vorbelegt, 1 auf keine = 1 klein');
// Flag mittel/gross auf <6h-/0h-Tag zaehlt dazu
var c=_ezEffTage({'2026-07-01':3},{'w1_2026-07-01':{stufe:'mittel'}},W,SA);
ok(c.tageMittel===1 && Math.abs(c.sum-30)<1e-9,'3h-Tag mittel = 1 mittel / 30');
var c2=_ezEffTage({},{'w1_2026-07-03':{stufe:'gross'}},W,SA);
ok(c2.tageGross===1 && Math.abs(c2.sum-62.04)<1e-9,'0h-Tag gross nur per Flag = 62,04');
// gemischt: 1 klein + 1 mittel + 1 gross
var d=_ezEffTage({'2026-07-01':8,'2026-07-02':9,'2026-07-03':8},{'w1_2026-07-02':{stufe:'mittel'},'w1_2026-07-03':{stufe:'gross'}},W,SA);
ok(d.tageKlein===1 && d.tageMittel===1 && d.tageGross===1 && Math.abs(d.sum-(11.94+30+62.04))<1e-9,'1k+1m+1g = 103,98');
// leere flags -> alle >6h-Tage als klein (Vorbelegungs-Fallback)
var e=_ezEffTage({'2026-07-01':8,'2026-07-02':7,'2026-07-03':4},{},W,SA);
ok(e.tageKlein===2 && Math.abs(e.sum-23.88)<1e-9,'Fallback = alle >6h-Tage klein');
// Saetze-Fallback (kein saetze-Arg) -> KV-2026-Default
var s=_ezEffTage({'2026-07-01':8},{},W);
ok(Math.abs(s.sum-11.94)<1e-9,'Saetze-Fallback klein 11,94');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_riedmann_juli_beispiel(index_html, node_exe, tmp_path):
    """€-Freigabe-Beispiele (v3.9.785, Sebastian): Riedmann Juli, 7 Anwesenheitstage.
    - 7 klein = 83,58  (7 × 11,94)
    - 5 klein + 2 gross = 183,78  (5×11,94 + 2×62,04)
    - 3 klein + 1 mittel + 1 gross + 2 keine = 127,86  (3×11,94 + 30 + 62,04)
    Alte Pins 81,97/93,68 (Satz 11,71) sind mit dem KV-Satz 11,94 obsolet (Sebastian freigegeben)."""
    js = _block(index_html) + _OK + u"""
var W='R';var SA={klein:11.94,mittel:30.00,gross:62.04};
function days(n){var d={};for(var i=1;i<=n;i++){d['2026-07-'+String(i).padStart(2,'0')]=8;}return d;}
// 7 klein = 83,58
var r1=_ezEffTage(days(7),{},W,SA);
ok(r1.tageKlein===7 && Math.abs(r1.sum-83.58)<1e-9,'7 klein = 83,58');
// 5 klein + 2 gross = 183,78
var r2=_ezEffTage(days(7),{'R_2026-07-06':{stufe:'gross'},'R_2026-07-07':{stufe:'gross'}},W,SA);
ok(r2.tageKlein===5 && r2.tageGross===2 && Math.abs(r2.sum-183.78)<1e-9,'5 klein + 2 gross = 183,78');
// 3 klein + 1 mittel + 1 gross + 2 keine = 127,86
var r3=_ezEffTage(days(7),{'R_2026-07-04':{stufe:'mittel'},'R_2026-07-05':{stufe:'gross'},'R_2026-07-06':{stufe:null},'R_2026-07-07':{stufe:null}},W,SA);
ok(r3.tageKlein===3 && r3.tageMittel===1 && r3.tageGross===1 && Math.abs(r3.sum-127.86)<1e-9,'3k+1m+1g+2keine = 127,86');
// v783-Abwesenheits-Ausschluss bleibt: 01.07 genehmigt krank -> raus (mit Stufe)
var r4=_ezEffTage(days(7),{},W,SA,{'2026-07-01':true});
ok(r4.tageKlein===6 && Math.abs(r4.sum-71.64)<1e-9,'01.07 krank raus -> 6 klein');
var r5=_ezEffTage(days(7),{'R_2026-07-01':{stufe:'gross'}},W,SA,{'2026-07-01':true});
ok(r5.tageKlein===6 && r5.tageGross===1,'01.07 explizit gross am Krank-Tag zaehlt (Override)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ezabsset(index_html, node_exe, tmp_path):
    """_ezAbsSet(abs,approvals,name) -> {iso:true} nur fuer GENEHMIGTE Abwesenheit (alle Typen).

    Status wie _resolveApprK (approvals gewinnt vor abs.status); beantragt/abgelehnt zaehlen NICHT. Key = name_iso
    (Prefix-Match wie _pzeBuildRows/_krankByMA); fremder MA + leerer/unbekannter Name -> leeres Set.
    """
    js = _block(index_html) + _OK + u"""
var A={
 'Riedmann_2026-07-01':{type:'krankenstand',status:'genehmigt'},
 'Riedmann_2026-07-02':{type:'urlaub',status:'beantragt'},
 'Riedmann_2026-07-03':{type:'urlaub',status:'abgelehnt'},
 'Riedmann_2026-07-04':{type:'za',status:'genehmigt'},
 'Anderer_2026-07-01':{type:'krankenstand',status:'genehmigt'}
};
var apps={'Riedmann_2026-07-02':'genehmigt'}; // approvals gewinnt vor abs.status
var s=_ezAbsSet(A,apps,'Riedmann');
ok(s['2026-07-01']===true,'krank genehmigt -> im Set');
ok(s['2026-07-02']===true,'approvals=genehmigt schlaegt abs.status=beantragt');
ok(s['2026-07-03']===undefined,'abgelehnt -> nicht im Set');
ok(s['2026-07-04']===true,'za genehmigt -> im Set (alle Typen)');
ok(s['Anderer_2026-07-01']===undefined,'fremder MA nicht dabei');
ok(Object.keys(s).length===3,'genau 3 genehmigte Tage fuer Riedmann');
ok(Object.keys(_ezAbsSet(A,apps,'')).length===0,'leerer Name -> leeres Set');
ok(Object.keys(_ezAbsSet(A,apps,'Unbekannt')).length===0,'unbekannter MA -> leeres Set');
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
    assert "async function _ezSet(wid,datum,stufe,von){" in index_html, "v3.9.785: _ezSet schreibt Stufe"
    fetch_start = index_html.index("async function _ezFetch(ym){")
    fetch_end = index_html.index("async function _ezSet(", fetch_start)
    fetch_body = index_html[fetch_start:fetch_end]
    assert "/entfernungszulage_tage?select=worker_id,datum,stufe,aktiv" in fetch_body, "v3.9.785: stufe laden (aktiv nur Migration-Fallback)"
    assert "42P01" in fetch_body and "404" in fetch_body, "Fetch muss fehlende Tabelle tolerieren"
    assert "missing:true" in fetch_body
    assert "{stufe:_ezStufeFromRow(x.stufe,!!x.aktiv)}" in fetch_body, "v3.9.785: Zeile -> {stufe} (Migration-tolerant)"
    set_start = index_html.index("async function _ezSet(")
    set_end = index_html.index("function EZKalender(", set_start)
    set_body = index_html[set_start:set_end]
    assert "on_conflict=worker_id,datum" in set_body
    assert "resolution=merge-duplicates,return=minimal" in set_body
    assert "method:'DELETE'" in set_body, "v3.9.785: stufe===undefined -> Zeile loeschen (zurueck Vorschlag)"


def test_window_export_pure_helfer(index_html):
    for name in ("_ezWtag", "_ezMonthGrid", "_ezWeekDays", "_ezKey", "_ezDayEff", "_ezEffTage", "_ezAbsSet"):
        assert "window." + name + "=" + name in index_html, "fehlender window-Export: " + name


def test_kalender_komponente(index_html):
    """Outlook-Grid als eigene Komponente, von KVZulagenReport gerendert; MA-Auswahl, Missing-Hinweis, 3 Zustaende."""
    assert "function EZKalender(props){" in index_html
    assert "h(EZKalender,{" in index_html
    assert "days:_ezDaysFor(ezWid)" in index_html, "EZKalender braucht die Vorbelegungs-Tage (days)"
    assert "Bitte Mitarbeiter wählen" in index_html
    assert "Tabelle entfernungszulage_tage fehlt" in index_html
    # sichtbar unterscheidbare Zustaende: u.a. durchgestrichener ("keine") Tag
    assert "textDecoration:strike?'line-through':'none'" in index_html
    # v3.9.785 Klick-Zyklus: Klick berechnet die naechste Stufe via _ezCycleNext (Vorschlag->klein->mittel->gross->keine->Vorschlag).
    assert "var next=_ezCycleNext(cur);" in index_html, "Toggle muss den Stufen-Zyklus nutzen"
    assert "if(next===undefined)delete n[key];else n[key]={stufe:next};" in index_html, "optimistischer Flag-Write je Stufe"


def test_menge_eff_basiert(index_html):
    """Die abgerechnete EZ-Summe (Ergebnistabelle) haengt an _ezEffTage, nicht mehr an der Auto-Zaehlung.

    v3.9.776: der CSV-Export ist durch den PZE-PDF-Uebergabezettel ersetzt — die frueheren CSV-Header-Pins
    entfallen; die eff-basierte MENGE (_ezEffTage) bleibt die gepinnte Invariante.
    """
    assert "_ezEffTage(byW[wid].days,ezFlags,wid" in index_html
    assert "taggeldSum:ez.sum" in index_html


def test_rechnung_unberuehrt(index_html):
    """LOHNRELEVANTE GRENZE (v3.9.785): der KV-Satz klein 11,94 (KV ab 01.01.2026) und der Tages-Kern
    _kvTaggeldTag bleiben; der Alt-Satz 11,71 war falsch (Sebastian). Rechenfunktionen unveraendert, KEIN Deckel."""
    assert "taggeldAb6h:11.94," in index_html, "KV-Satz klein 11,94 (Alt 11,71 war falsch)"
    assert "ezMittel:30.00, ezGross:62.04," in index_html, "Saetze mittel 30,00 / gross 62,04"
    for fn in ("function _kvTaggeldTag(", "function _kvZulagenMonat(", "function _pzeTagRow("):
        assert fn in index_html, "Rechenfunktion versehentlich entfernt: " + fn
    # KEIN Deckel: _ezEffTage summiert ungedeckelt (je Stufe n*satz).
    ez_start = index_html.index("function _ezEffTage(")
    ez_body = index_html[ez_start:index_html.index("\n}", ez_start)]
    assert "Math.min" not in ez_body, "kein Deckel in _ezEffTage"


def test_v783_abwesenheit_ausschluss_verdrahtung(index_html):
    """v3.9.783 (LOHNRELEVANT): genehmigte Abwesenheit (_ezAbsSet) faellt aus der EZ-Vorbelegung (LA 2740).

    EINE PURE-Authority _ezAbsSet, an ALLE lohnrelevanten Aufrufer durchgereicht — kein neuer Fetch, kein
    zweiter Rechenpfad. EZ-Kalender kennzeichnet Abwesenheitstage (absDays-Prop).
    """
    # _ezDayEff hat den 3. Param + verrechnet ihn (Vorschlag klein nur wenn NICHT genehmigt-abwesend) — v3.9.785 Stufe
    de = index_html[index_html.index("function _ezDayEff("):index_html.index("function _ezEffTage(")]
    assert "function _ezDayEff(std,flagEntry,absGenehmigt){" in de, "3. Param absGenehmigt fehlt"
    assert "(((parseFloat(std)||0)>6)&&!absGenehmigt)?'klein':''" in de, "Ausschluss/Vorschlag nicht in _ezDayEff verdrahtet"
    # _ezEffTage reicht absSet an _ezDayEff durch
    ef = index_html[index_html.index("function _ezEffTage("):index_html.index("function _ezAbsSet(")]
    assert "var A=absSet||{};" in ef and "f[_ezKey(wid,iso)],!!A[iso]" in ef, "_ezEffTage reicht absSet nicht durch"
    # PURE-Helfer _ezAbsSet existiert + window-exportiert
    assert "function _ezAbsSet(abs,approvals,workerName){" in index_html
    assert "window._ezAbsSet=_ezAbsSet" in index_html
    # Aufrufer reichen absSet durch (abs/approvals schon im Scope, kein neuer Fetch); v3.9.785 Saetze via _ezSaetze
    assert "_ezEffTage(byW[wid].days,ezFlags,wid,_ezSaetze(kv),_ezAbsSet(props.abs||{},props.approvals,_nm))" in index_html, "KVZulagenReport-rows reicht Saetze+absSet nicht durch"
    assert "var absSet=_ezAbsSet(abs||{},approvals,worker.name);" in index_html, "_pzePdf baut absSet nicht"
    assert "_ezEffTage(daysMap,ezF,worker.id,saetze,absSet)" in index_html, "_pzePdf reicht Saetze+absSet nicht an _ezEffTage"
    # EZ-Kalender: Prop + Label-Branch (v3.9.785 effStufe)
    assert "const absDays=props.absDays||{};" in index_html, "EZKalender nimmt absDays-Prop nicht"
    assert "absDays:_ezAbsDaysFor(ezWid)" in index_html, "EZKalender bekommt absDays nicht gerendert"
    assert "var absG=absDays[iso];" in index_html and "var effStufe=_ezDayEff(std,flagEntry,!!absG);" in index_html


def test_v783_konflikt_marker(index_html):
    """v3.9.783: Konflikt-Marker (genehmigter Fehlgrund UND Projektbuchung am selben Tag) in PZE-PDF + On-Screen.

    Macht die widerspruechliche Datenlage (Krank-Tag MIT Projektzeit) sichtbar; Bereinigung ist Buero/Sebastian.
    """
    # PDF-Notiz-Spalte
    assert "if(r.fehlgrund&&r.fehlgrund.genehmigt&&r.projMin>0)notiz=(notiz?notiz+' ':'')+'Konflikt Abw/Proj';" in index_html
    # On-Screen-PZE (Desktop-Notiz-Zelle + Mobile-Card) — mind. 2 weitere Vorkommen des Marker-Guards
    assert index_html.count("r.fehlgrund&&r.fehlgrund.genehmigt&&r.projMin>0") >= 3, "Konflikt-Marker fehlt in PDF/Desktop/Mobile"
    assert "Konflikt: Abwesenheit + Projektbuchung" in index_html, "On-Screen-Konflikt-Text fehlt"
