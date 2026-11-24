"""Paket 14 (GF 24.11.2026): "Berichte bearbeiten" zeigt EINE Kalenderwoche statt der letzten 50 Eintraege.

Gemessen: der Buero-Export (Bauwochenbericht, Stunden-KW-Tabelle) ordnet Eintraege ueber
_kwFromDate/_kwYearFromDate (ISO, Mo-So, Jahreswechsel nach ISO-Wochenjahr) und zeigt die Tage ueber
_kwDates(yr,kw). Der Dialog nimmt GENAU diese Funktionen (_beKwEintraege). Die Zeiterfassungs-KW-Excel
(exportXls) rechnet ihren Montag ueber new Date(yr,0,4) ... - der Test belegt, dass beide Grenzen fuer
alle KW 2025-2028 gleich sind und die Wochensumme des Dialogs der Export-Summe entspricht.
"""
import json
import re
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _zeile(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n", i)].rstrip("\r")


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def _kw_js(src):
    teile = [_zeile(src, "const _getMaxKW=(year)=>{"),
             _zeile(src, "const _ymd=d=>`"),
             _zeile(src, "  const _kwDates=(yr,kw)=>{"),
             _zeile(src, "  const _localD=(d)=>"),
             _zeile(src, "  const _kwFromDate=(d)=>{"),
             _zeile(src, "  const _beKwEintraege=(liste,wid,yr,kw)=>"),
             _zeile(src, "  const _kwYearFromDate=(d)=>{")]
    return "\n".join(teile) + "\n"


E = [{"id": "a", "monteur": "w1", "datum": "2026-11-22", "stunden": 1},
     {"id": "b", "monteur": "w1", "datum": "2026-11-29", "stunden": 2.25},
     {"id": "c", "monteur": "w1", "datum": "2026-11-23", "stunden": 8.5},
     {"id": "d", "monteur": "w1", "datum": "2026-11-30", "stunden": 4},
     {"id": "e", "monteur": "w2", "datum": "2026-11-25", "stunden": 7},
     {"id": "f", "monteur": "w1", "datum": "2026-12-28", "stunden": 3},
     {"id": "g", "monteur": "w1", "datum": "2027-01-03", "stunden": 5},
     {"id": "h", "monteur": "w1", "datum": "2027-01-04", "stunden": 6},
     {"id": "i", "monteur": "w1", "datum": "2026-12-31", "stunden": 1.5},
     {"id": "j", "monteur": "w1", "datum": "2026-01-01", "stunden": 2}]


@needs_node
def test_montag_und_sonntag_drin_naechster_montag_nicht(index_html):
    r = _node(_kw_js(index_html) + "const E=" + json.dumps(E) + ";\n"
              "console.log(JSON.stringify(_beKwEintraege(E,'w1',2026,48).map(e=>e.id)));")
    assert r == ["c", "b"], "KW 48/2026 = Mo 23.11. bis So 29.11., aufsteigend; 22.11. und 30.11. nicht"


@needs_node
def test_jahreswechsel_kw53_und_kw1(index_html):
    r = _node(_kw_js(index_html) + "const E=" + json.dumps(E) + ";\n"
              "console.log(JSON.stringify([_beKwEintraege(E,'w1',2026,53).map(e=>e.id),_beKwEintraege(E,'w1',2027,1).map(e=>e.id),"
              "_beKwEintraege(E,'w1',2026,1).map(e=>e.id),_getMaxKW(2026),_getMaxKW(2027),"
              "_kwDates(2026,53).map(_ymd)[0],_kwDates(2026,53).map(_ymd)[6]]));")
    assert r[0] == ["f", "i", "g"], "KW 53/2026 reicht von Mo 28.12.2026 bis So 03.01.2027"
    assert r[1] == ["h"], "KW 1/2027 beginnt Mo 04.01.2027"
    assert r[2] == ["j"], "01.01.2026 (Do) gehoert zu KW 1/2026"
    assert r[3:] == [53, 52, "2026-12-28", "2027-01-03"]


@needs_node
def test_grenzen_wie_zeiterfassungs_export_und_summe_gleich(index_html):
    """Fuer jede KW 2025-2028: _kwDates == Montag-Formel des ZE-Exports; Dialogsumme == Export-Summe."""
    assert "const kwMon=_react.useMemo.call(void 0, ()=>{const d=new Date(yr,0,4);d.setDate(d.getDate()-(d.getDay()||7)+1+(kw-1)*7);return d;},[kw,yr]);" in index_html
    js = _kw_js(index_html) + r"""
const ex=(yr,kw)=>{const d=new Date(yr,0,4);d.setDate(d.getDate()-(d.getDay()||7)+1+(kw-1)*7);const t=[];for(let i=0;i<7;i++){const x=new Date(d);x.setDate(d.getDate()+i);t.push(_ymd(x));}return t;};
const E=[];let s=7;const rnd=()=>{s=(s*1103515245+12345)%2147483648;return s/2147483648;};
for(let i=0;i<1500;i++){const t=new Date(2025,0,1);t.setDate(t.getDate()+Math.floor(rnd()*1460));E.push({id:'x'+i,monteur:rnd()<0.8?'w1':'w2',datum:_ymd(t),stunden:Math.round(rnd()*40)/4});}
const fehl=[];let n=0;
for(let yr=2025;yr<=2028;yr++)for(let kw=1;kw<=_getMaxKW(yr);kw++){n++;
  const a=_kwDates(yr,kw).map(_ymd),b=ex(yr,kw);if(a.join()!==b.join())fehl.push('grenze '+kw+'/'+yr);
  const dlg=_beKwEintraege(E,'w1',yr,kw).reduce((x,e)=>x+e.stunden,0);
  const exp=E.filter(e=>e.monteur==='w1'&&e.datum>=b[0]&&e.datum<=b[6]).reduce((x,e)=>x+e.stunden,0);
  if(Math.abs(dlg-exp)>1e-9)fehl.push('summe '+kw+'/'+yr+' '+dlg+' != '+exp);}
console.log(JSON.stringify({fehl,n}));"""
    r = _node(js)
    assert r["n"] == 209 and r["fehl"] == [], r


def _edit(src):
    a = src.index("  const editMonteurEntries=async(ms)=>{")
    return src[a:src.index("    let cnt=0;", a)]


def test_dialog_zeigt_eine_kw_statt_letzte_50(index_html):
    e = _edit(index_html)
    assert ".slice(0,50)" not in e and "Letzte 50" not in e
    assert "myEntries=_beKwEintraege(allEntries,ms.id,_kwSel.yr,_kwSel.kw);" in e
    assert "let _kwSel={kw:_kwFromDate(_heuteD),yr:_kwYearFromDate(_heuteD)};" in e, "Start: aktuelle KW"
    assert 'const _kwKopf=_kwTxt+" · "' in e and "+_kwKopf,titleIk" in e, "Kopf KW 48/2026 · 23.11.–29.11."
    assert "kwNav:{kw:_kwSel.kw,yr:_kwSel.yr,maxKw:_getMaxKW}" in e
    assert "if(_antwort&&_antwort._nav&&_antwort._nav.kw){" in index_html


@needs_node
def test_kopfzeile_text(index_html):
    js = _kw_js(index_html) + r"""
const _kwTage=_kwDates(2026,48);const _kwTxt="KW 48/2026";""" + "\n" + _zeile(index_html, "    const _kwKopf=_kwTxt+") + "\nconsole.log(JSON.stringify(_kwKopf));"
    assert _node(js) == "KW 48/2026 · 23.11.–29.11."


def test_leere_kw_und_ladefehler_verschieden(index_html):
    e = _edit(index_html)
    m = re.search(r"leerText:loaded\?\((.*?)\):(\"[^\"]*\"),", e)
    assert m, "leerText unterscheidet geladen/nicht geladen"
    assert "Keine Zeiteinträge in" in m.group(1)
    assert "nicht geladen" in m.group(2) and "Keine Zeiteinträge" not in m.group(2)
    assert "if(!myEntries.length){window.__toast" not in e, "leere KW oeffnet den Dialog (Woche wechseln moeglich)"


def test_buchung_hinzufuegen_in_gewaehlter_kw_und_hinweis(index_html):
    e = _edit(index_html)
    assert "datum:(_h>=_kwVon&&_h<=_kwBis)?_h:_kwVon" in e
    assert '"Datum liegt in KW "+_kwFromDate(_d)+"/"+_kwYearFromDate(_d)' in e


def _modal(src):
    a = src.index("window._exportReviewModal=function(opts){")
    return src[a:src.index("\n};", a)]


def test_seitendialog_statt_confirm(index_html):
    m = _modal(index_html)
    ohne_kommentar = re.sub(r"/\*.*?\*/", "", m, flags=re.S)
    assert "confirm(" in m, "Positivkontrolle: das Wort steht im Kommentar"
    assert "confirm(" not in ohne_kommentar and "_confirmModal" not in ohne_kommentar
    assert "_seite.setAttribute('data-kw-seitendialog','1')" in m
    assert "function _wechsel(ziel){if(_geaendert()){_seitendialog(" in m
    assert "function _abbrechen(){if(kwNav&&_geaendert()){_seitendialog(" in m
    assert "btnCancel.onclick=function(){_abbrechen();};" in m


def test_summe_im_dialog_ueber_fmtstd(index_html):
    e = _edit(index_html)
    assert 'summe:(rs)=>"Summe "+_kwTxt+": "+fmtStd(' in e
    assert "_summeEl.setAttribute('data-kw-summe','1')" in _modal(index_html)


def test_andere_aufrufer_unveraendert(index_html):
    """kwNav/leerText/zeilenHinweis/summe sind opt-in: nur editMonteurEntries setzt sie."""
    assert index_html.count("kwNav:{") == 1
    assert index_html.count("zeilenHinweis:(r)=>") == 1
    m = _modal(index_html)
    assert "+(kwNav?'position:relative;overflow:hidden;':'')" in m
    assert "if(_navBar)box.appendChild(_navBar);" in m


def test_stunden_spalte_im_dialog_zwei_stellen(index_html):
    m = _modal(index_html)
    assert "((col.key==='stunden')?fmtStd(v):_tankEinDE(v))" in m
    assert "if(col.type==='number'&&col.key==='stunden')inp.addEventListener('blur'" in m
