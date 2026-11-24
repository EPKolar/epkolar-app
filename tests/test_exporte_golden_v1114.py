"""Export-Ausgabe byte-gleich zu 3.9.1114 (GF-Entscheidung 24.11.2026 abends).

Bis Sebastian im Buero geklaert hat, ob die Excel-Dateien irgendwo eingelesen werden, darf KEIN Export eine andere
Datei liefern als 3.9.1114 (dfc369b). Dieser Test laesst die echten Erzeuger aus index.html in node laufen
(mit festen Beispieldaten, fester Uhrzeit, abgefangenem Download _dl) und vergleicht den Dateiinhalt mit dem
Golden-Abzug tests/exporte_golden_v1114.json, der mit DEMSELBEN Geruest aus dfc369b erzeugt wurde.

Gepruefte Exporte (13):
  Z9 (Zeiterfassung):  exportWochenStz, exportTagesStz, exportBauwochenbericht, exportXls (ZE-KW), exportAllXls (ZE-Uebersicht)
  weitere Excel:       exportMonatXls (ZE-Monatsliste), _absExcel (Abwesenheiten), _krankExcel (Krankenstand),
                       exportAbsCsv (Abwesenheit-Liste), Kontingent-Knopf (Urlaubskontingent), genCsv (Projekt-Zeiterfassung)
Der gemeinsame Erzeuger genXls und _n laufen ECHT mit (aus index.html geschnitten) - eine Aenderung dort faellt auf.

Warum ein Ausgabe-Test: Z9 (test_zeit_handy_z4_z9.py) prueft nur eine Quelltext-Eigenschaft ("_n(" ja, "_hK(" nein);
Paket 13 (b24317e) hat drei Z9-Exporte geaendert, ohne dass Z9 rot wurde.

Golden neu erzeugen (nur mit GF-Freigabe einer Export-Aenderung):
  python tests/test_exporte_golden_v1114.py <pfad-zu-index.html-von-dfc369b> [ziel.json]
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

NODE = shutil.which("node")
GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exporte_golden_v1114.json")

NAMEN = ["exportWochenStz", "exportTagesStz", "exportBauwochenbericht", "exportXls", "exportAllXls", "exportMonatXls",
         "_absExcel", "_krankExcel", "exportAbsCsv", "kontingentXls", "genCsv"]


def _zeile(src, kopf):
    i = src.index(kopf)
    return src[i:src.index("\n", i)]


def _block(src, name, nach=None):
    z = src.index(nach) if nach else 0
    i = src.index("\n  const " + name + "=", z) + 1
    j = src.index("\n  const ", i + 5)
    return src[i:j]


def _pfeil(src, kopf):
    i = src.index(kopf)
    k = src.index("=>{", i) + 2
    d = 0
    for p in range(k, len(src)):
        c = src[p]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return src[i:p + 1]
    raise ValueError(kopf)


def _genxls(src):
    a = src.index("const _XNUM=")
    b = src.index("const genXls=(title,subtitle,headers,rows,filename,opts={})=>{")
    e = src.index("\n};", b) + 3
    return src[a:e]


VORSPANN = r"""
"use strict";
const _FIX=Date.UTC(2026,10,24,9,30,0);const _D=Date;
class FixDate extends _D{constructor(...a){if(a.length)super(...a);else super(_FIX);}static now(){return _FIX;}}
globalThis.Date=FixDate;
function _nullishCoalesce(l,f){return l!=null?l:f();}
function _optionalChain(ops){let last;let v=ops[0];let i=1;while(i<ops.length){const op=ops[i],fn=ops[i+1];i+=2;
  if((op==='optionalAccess'||op==='optionalCall')&&v==null)return undefined;
  if(op==='access'||op==='optionalAccess'){last=v;v=fn(v);}else if(op==='call'||op==='optionalCall'){const vv=v,ll=last;v=fn((...a)=>vv.call(ll,...a));last=undefined;}}return v;}
const COMPANY_FOOTER={name:"Firma",fn:"FN 1x",uid:"ATU1",web:"www.example.at"};
const CF_HTML_LINE1="Zeile1",CF_HTML_LINE2="Zeile2",CF_HTML_AGB="AGB";
const window={__toast:function(){}};
const OUT={};let _AKT="";
function _dl(blob,fn){OUT[_AKT]={datei:fn,blob:blob};}
"""

# Feste Beispieldaten: Viertel-/Drittelstunden (8.25, 8.1666) und ein Tausender-Wert (1234.5) machen jede
# Aenderung an Nachkommastellen, Gruppierung oder Zahlenformat sichtbar. Namen nur Vornamen.
DATEN_ZE = r"""
const DAYS=["Mo","Di","Mi","Do","Fr","Sa","So"];const kw=42,yr=2026;
const dayDate=i=>new Date(2026,9,12+i);
const isoDate=i=>{const d=dayDate(i);return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");};
const dateFmt=i=>{const d=dayDate(i);return String(d.getDate()).padStart(2,"0")+"."+String(d.getMonth()+1).padStart(2,"0")+".";};
const monteure=[{id:"w1",n:"Anna",r:"monteur"},{id:"w2",n:"Ben",r:"monteur"}];const selWorker="w1";
const dayEntries={};
dayEntries[isoDate(0)]=[{label:"Projekt A",taetigkeit:"Montage",type:"projekt",hours:8.25,von:"07:00",bis:"16:00",pause:0.75,bemerkung:"x"}];
dayEntries[isoDate(1)]=[{label:"Projekt A",taetigkeit:"Montage",type:"projekt",hours:7.5,von:"07:00",bis:"15:00",pause:0.5},{label:"Projekt B",taetigkeit:"Service",type:"regie",hours:1.25,von:"15:00",bis:"16:15"}];
dayEntries[isoDate(2)]=[{label:"Projekt A",taetigkeit:"Montage",type:"projekt",hours:8.1666,von:"07:00",bis:"16:10",pause:1}];
dayEntries[isoDate(4)]=[{label:"Projekt B",taetigkeit:"",type:"projekt",hours:4.75,von:"07:00",bis:"11:45",pause:0}];
const dayTotal=i=>(dayEntries[isoDate(i)]||[]).reduce((s,e)=>s+e.hours,0);
const weekTotal=DAYS.reduce((s,_,i)=>s+dayTotal(i),0);
function _kvTagesnorm(dow,ft){if(ft)return 0;return (dow>=1&&dow<=4)?8.5:dow===5?4.5:0;}
function _isATFeiertag(){return false;}
const projects=[{id:"p1",name:"Projekt A",nr:"PA-1"}];
const entries=[{w:"w1",datum:isoDate(0),p:"p1",hours:8.25,taetigkeit:"Montage"},{w:"w2",datum:isoDate(1),p:"p1",hours:7.5,taetigkeit:"Leitungen"},{w:"w1",datum:isoDate(2),p:"p1",hours:8.1666}];
const fieldMAWo=monteure;
const allData=[{n:"Anna",total:25.1666,dayTotals:{Mo:8.25,Di:8.75,Mi:8.1666}},{n:"Ben",total:0,dayTotals:{}},{n:"Carl",total:1234.5,dayTotals:{Mo:1234.5}}];
let zeMonLaedt=false;const setZeMonLaedt=()=>{};
const _zeMonatHolen=async()=>({zeilen:[{datum:"2026-10-12",ziel:"Projekt A",typ:"Projekt",taetigkeit:"Montage",von:"07:00",bis:"15:45",pause:0.75,stunden:8,bemerkung:""},{datum:"2026-10-13",ziel:"Projekt B",typ:"Regie",taetigkeit:"Service",von:"07:00",bis:"14:30",pause:0.25,stunden:7.25,bemerkung:"b"}]});
const _zeDatDE=iso=>{const p=String(iso).split("-");return p[2]+"."+p[1]+"."+p[0];};
const _zeTagKurz=()=>"Mo";const workerName="Anna";const _zeMonatName=()=>"Oktober 2026";const zeMon="2026-10";
const _nWort=(n,a,b)=>n+" "+(n===1?a:b);const _ezHeuteISO=()=>"2026-11-24";const _zeMonDatei=()=>"Zeiterfassung_Anna_2026-10";
"""

DATEN_ABW = r"""
const _abYr=2026;
const _absRows=()=>[{name:"Anna",gesamt:1234.5,urlaub:40.25,krank:8.5,za:4,sonder:0,rest:152.1666}];
const _krankRows=()=>[{name:"Anna",date:"2026-03-02",hours:8.25,status:"genehmigt",hasAtt:true},{name:"Ben",date:"2026-03-03",hours:4.5,status:"ausstehend",hasAtt:false}];
const names=["Anna"];const _absAb=()=>true;const yr=2026;
const yearSt=()=>({urlaubStdGen:16.5,urlaubStdAusstehend:8.25,urlaubStd:24.75,krankenstandStd:8.5,zeitausgleichStd:4.1666});
const kontingent={Anna:{stunden:192.5,vorjahr:12.25,woche:38.5,ueberstunden:3.75}};
const resturlaub=()=>180.1666;
const abs={"Anna_2026-03-02":{type:"urlaub",hours:8.25},"Anna_2026-03-03":{type:"urlaub"}};
const approvals={"Anna_2026-03-02":"genehmigt"};
const AT_T={urlaub:{l:"Urlaub"}};const stdTag=()=>8.5;
const _kontNames=["Anna"];
"""

DATEN_PROJ = r"""
const p={nr:"PA-1",name:"Projekt A",kunde:"Kunde X",matchcode:"KX"};
const pe=[{w:"w1",date:"2026-10-12",gw:"e",taetigkeit:"Montage",hours:8.25},{w:"w2",date:"2026-10-13",gw:"e",task:"Leitungen",stunden:"7.5"},{w:"w1",date:"2026-10-14",gw:"x",hours:1234.5}];
const monteure=[{id:"w1",n:"Anna"},{id:"w2",n:"Ben"}];const MONT=[];
const buildExportFilename=(a,b,c,d,e)=>a+"_"+b+"_"+c+"_"+d+"."+e;const td2=()=>"2026-11-24";
const fdt=iso=>{const q=String(iso).split("-");return q[2]+"."+q[1]+"."+q[0];};
const GW={e:{l:"Elektro"}};
"""


def baue_js(src):
    s = src.replace("\r\n", "\n")
    ze = "\nfunction ZeiterfassungView("
    teile = [VORSPANN, _zeile(s, "function _n(v,d){"), _zeile(s, "function _ktgStd(v){")]
    # Anzeige-Formatierer, falls ein Erzeuger sie ruft (so zeigt die Umkehrprobe gegen b24317e echte Inhaltsunterschiede statt eines Absturzes)
    for kopf in ("function _fzZahl(v){", "function fmtStd(v){", "function fmtStdEingabe(v){"):
        if kopf in s:
            i = s.index(kopf)
            teile.append(s[i:s.index("\n}", i) + 2])
    teile.append(_genxls(s))

    def lauf(name, daten, code, aufruf):
        return ("\n(async function(){\n" + daten + "\n" + code + "\n_AKT=" + json.dumps(name) + ";await " + aufruf
                + ";})" )

    kont = _pfeil(s, 'onClick: ()=>{const hdrs=["Nr","Mitarbeiter","Std/Wo"').replace("onClick: ", "const kontingentXls=", 1)
    laeufe = [
        lauf("exportWochenStz", DATEN_ZE, _block(s, "exportWochenStz", ze), "exportWochenStz()"),
        lauf("exportTagesStz", DATEN_ZE, _block(s, "exportTagesStz", ze), "exportTagesStz(1)"),
        lauf("exportBauwochenbericht", DATEN_ZE, _block(s, "exportBauwochenbericht", ze), 'exportBauwochenbericht("p1")'),
        lauf("exportXls", DATEN_ZE, _block(s, "exportXls", ze), "exportXls()"),
        lauf("exportAllXls", DATEN_ZE, _block(s, "exportAllXls", ze), "exportAllXls()"),
        lauf("exportMonatXls", DATEN_ZE, _block(s, "exportMonatXls", ze), "exportMonatXls()"),
        lauf("_absExcel", DATEN_ABW, _zeile(s, "  const _absExcel="), "_absExcel()"),
        lauf("_krankExcel", DATEN_ABW, _zeile(s, "  const _krankExcel="), "_krankExcel()"),
        lauf("exportAbsCsv", DATEN_ABW, _block(s, "exportAbsCsv"), "exportAbsCsv()"),
        lauf("kontingentXls", DATEN_ABW, kont, "kontingentXls()"),
        lauf("genCsv", DATEN_PROJ, _block(s, "genCsv"), "genCsv()"),
    ]
    kette = "\n(async function(){\n" + "".join("await " + l + "();\n" for l in laeufe) + r"""
const r={};for(const k of Object.keys(OUT).sort()){r[k]={datei:OUT[k].datei,inhalt:await OUT[k].blob.text()};}
process.stdout.write(JSON.stringify(r));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(3);});
"""
    return "\n".join(teile) + kette


def lauf_exporte(src):
    js = baue_js(src)
    r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout)


needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


@pytest.fixture(scope="module")
def ausgabe(index_html):
    return lauf_exporte(index_html)


@pytest.fixture(scope="module")
def golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return json.load(f)


def test_golden_vollstaendig(golden):
    assert sorted(golden) == sorted(NAMEN)
    for k in NAMEN:
        assert len(golden[k]["inhalt"]) > 500, k


@needs_node
@pytest.mark.parametrize("name", NAMEN)
def test_export_byte_gleich_wie_1114(ausgabe, golden, name):
    assert name in ausgabe, name + " hat keine Datei erzeugt"
    assert ausgabe[name]["datei"] == golden[name]["datei"], name
    ist, soll = ausgabe[name]["inhalt"], golden[name]["inhalt"]
    if ist != soll:
        i = next(k for k in range(min(len(ist), len(soll)) + 1) if k >= min(len(ist), len(soll)) or ist[k] != soll[k])
        pytest.fail("%s weicht von 3.9.1114 ab ab Zeichen %d:\n  1114: %r\n  jetzt: %r" % (name, i, soll[max(0, i - 60):i + 60], ist[max(0, i - 60):i + 60]))


@needs_node
def test_mutation_gemeinsamer_helfer_faellt_auf(index_html, golden):
    """Mutationsprobe: ein Zeichen im Zahlenformat des gemeinsamen Erzeugers genXls (General -> Genera1) macht alle genXls-Exporte rot."""
    alt = "td.xn{mso-number-format:General;}"
    assert index_html.count(alt) == 1
    aus = lauf_exporte(index_html.replace(alt, "td.xn{mso-number-format:Genera1;}"))
    rot = sorted(k for k in NAMEN if aus[k]["inhalt"] != golden[k]["inhalt"])
    assert rot == sorted(["_absExcel", "_krankExcel", "exportAbsCsv", "exportAllXls", "exportMonatXls", "exportXls", "genCsv", "kontingentXls"]), rot


@needs_node
def test_mutation_n_faellt_auf(index_html, golden):
    """Mutationsprobe: _n mit einem anderen Dezimalzeichen (toFixed -> Komma) macht die Exporte rot."""
    kopf = _zeile(index_html, "function _n(v,d){")
    neu = kopf.replace("n.toFixed(d):n;}", "n.toFixed(d).replace('.',','):n;}")
    assert neu != kopf
    aus = lauf_exporte(index_html.replace(kopf, neu))
    rot = [k for k in NAMEN if aus[k]["inhalt"] != golden[k]["inhalt"]]
    assert len(rot) >= 10, rot


if __name__ == "__main__":
    NODE = NODE or "node"
    with open(sys.argv[1], encoding="utf-8") as f:
        src = f.read()
    with open(sys.argv[2] if len(sys.argv) > 2 else GOLDEN, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(lauf_exporte(src), ensure_ascii=True, indent=1, sort_keys=True) + "\n")
