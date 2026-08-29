# -*- coding: utf-8 -*-
"""v3.9.898 - Fuhrpark: Kacheln, Pickerl-Deckel und Leerzustand.

WARUM DIESER RIEGEL DEN CODE AUSFUEHRT statt Zeichenketten zu suchen: die drei
Befunde sind alle vom Typ "eine Groesse, zwei Rechnungen". Ein `assert "visibleFz"
in HTML` misst die FORM und wuerde gruen bleiben, sobald jemand eine fuenfte
Kachel mit `fahrzeuge` daneben stellt. Gemessen wird deshalb die EIGENSCHAFT:
Kachelzahl == das, was auf den Karten darunter tatsaechlich zu sehen ist.

Die vier KPI-Ausdruecke, sortedFz, visibleFz und _fzEmptyGrund werden WOERTLICH
aus index.html geschnitten und in Node ausgefuehrt. Nur `_react.useMemo` und
`_optionalChain` sind gestellt - es gibt keine Attrappe der zu messenden Logik.

UMKEHRPROBE: test_umkehrprobe_* baut jeweils genau den alten Zustand wieder ein
(fahrzeuge statt visibleFz / 365-Tage-Deckel / Rollen-statt-Pruefung) und
verlangt, dass die Messung dann ROT wird. Ein Riegel, der nicht zumachen kann,
ist ein Denkmal.
"""
import json
import pathlib
import re

from conftest import run_node_snippet

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")

_PRE = (
    "const TIME_HOUR=3600000;const TIME_DAY=86400000;const window={};"
    "const _react={useMemo:{call:(t,fn)=>fn()}};"
    "function _optionalChain(ops){let lastAccessLHS=undefined;let value=ops[0];let i=1;"
    "while(i<ops.length){const op=ops[i];const fn=ops[i+1];i+=2;"
    "if((op==='optionalAccess'||op==='optionalCall')&&value==null){return undefined;}"
    "if(op==='access'||op==='optionalAccess'){lastAccessLHS=value;value=fn(value);}"
    "else if(op==='call'||op==='optionalCall'){value=fn((...args)=>value.call(lastAccessLHS,...args));"
    "lastAccessLHS=undefined;}}return value;}\n"
)

# Die Karten-Praedikate sind die WAHRHEIT AUF DEM BILDSCHIRM (Z~28060 ff.):
# pickerlWarn / serviceWarn / offSch. Sie stehen hier bewusst als Zweitmeinung.
_KARTE = (
    "const kartePickerl=f=>{const _p=window._pickerlStatus(f.pickerl);"
    "return _p==='warn'||_p==='overdue';};"
    "const karteService=f=>!!(f.naechstService&&new Date(f.naechstService+'T00:00:00')<=new Date());"
    "const karteSchaeden=f=>(f.schaeden||[]).filter(s=>s.status==='offen').length;"
)


def _d(off):
    return "new Date(Date.now()+%d*TIME_DAY).toISOString().slice(0,10)" % off


_FLOTTE = """
const FLOTTE=[
 {id:'a',kennzeichen:'TU-1',status:'aktiv',fahrer:'m1',pickerl:%s,naechstService:%s,schaeden:[]},
 {id:'b',kennzeichen:'TU-2',status:'aktiv',fahrer:'m2',pickerl:%s,naechstService:%s,schaeden:[{status:'offen'}]},
 {id:'c',kennzeichen:'TU-3',status:'aktiv',fahrer:'m2',pickerl:%s,naechstService:'',schaeden:[{status:'offen'},{status:'offen'}]},
 {id:'d',kennzeichen:'TU-4',status:'stillgelegt',fahrer:'m1',pickerl:%s,naechstService:%s,schaeden:[{status:'offen'}]}
];
""" % (_d(400), _d(30), _d(-20), _d(-5), _d(-596), _d(-800), _d(-700))
# TU-3 traegt bewusst -596 Tage: DER Fall, den der 365-Tage-Deckel verschluckt hat.
# TU-4 ist stillgelegt UND hat einen offenen Schaden und ein faelliges Service.


def _schnitt():
    """Die zu messenden Ausdruecke woertlich aus index.html."""
    def grab(pat, name):
        m = re.search(pat, HTML)
        assert m, "nicht gefunden (Umbau in index.html?): " + name
        return m.group(0)

    vf = HTML.index("  const visibleFz=_react.useMemo")
    i_sv = HTML.index("  const serviceFaellig=", vf)
    i_ak = HTML.rindex("  const aktiv=", 0, i_sv)
    i_os = HTML.rindex("  const offeneSchaeden=", 0, i_sv)
    i_pf = HTML.rindex("  const pickerFaellig=", 0, i_sv)

    def zeile(i):
        # Path.read_text normalisiert Zeilenenden -> im Speicher steht "\n", nicht CRLF.
        return HTML[i:HTML.index("\n", i)]

    teile = [
        grab(r"window\._pickerlStatus=\(datum,warnDays\)=>\{.*?\};", "_pickerlStatus"),
        grab(r"  const myFzId=.*?\|\|null;", "myFzId"),
        grab(r"  const sortedFz=_react\.useMemo[\s\S]*?\},\[fahrzeuge,favFz,myFzId\]\);", "sortedFz"),
        grab(r"  const visibleFz=_react\.useMemo.*?\);", "visibleFz"),
        zeile(i_ak), zeile(i_os), zeile(i_pf), zeile(i_sv),
    ]
    m = re.search(r"  const _fzEmptyGrund=[\s\S]*?\"nicht_zugewiesen\"\);", HTML)
    assert m, "_fzEmptyGrund fehlt - der Leertext haengt wieder an der Rolle"
    teile.append(m.group(0))
    return "\n".join(teile)


def _lauf(node_exe, koerper=None):
    koerper = koerper if koerper is not None else _schnitt()
    runner = """
function lauf(fahrzeuge,curUser,isVAdmin,favFz){
%s
%s
  return {liste:visibleFz.map(f=>f.kennzeichen).join(','),
    KACHEL:[aktiv,offeneSchaeden,pickerFaellig,serviceFaellig].join('/'),
    KARTEN:[visibleFz.length,visibleFz.reduce((s,f)=>s+karteSchaeden(f),0),
            visibleFz.filter(kartePickerl).length,visibleFz.filter(karteService).length].join('/'),
    leerGrund:visibleFz.length===0?_fzEmptyGrund:null};
}
const ADMIN={role:'admin',monteurId:'x',username:'u'};
const M1={role:'monteur',monteurId:'m1',username:'u1'};
const M9={role:'monteur',monteurId:'m9',username:'u9'};
process.stdout.write(JSON.stringify({
 admin: lauf(FLOTTE,ADMIN,true,[]),
 monteur_m1: lauf(FLOTTE,M1,false,[]),
 monteur_ohne: lauf(FLOTTE,M9,false,[]),
 monteur_nur_stillgelegtes: lauf(FLOTTE.filter(f=>f.id==='d'),M1,false,[]),
 admin_gar_keine: lauf([],ADMIN,true,[]),
 admin_alle_stillgelegt: lauf(FLOTTE.filter(f=>f.id==='d'),ADMIN,true,[])
}));
""" % (koerper, _KARTE)
    return json.loads(run_node_snippet(node_exe, _PRE + _FLOTTE + runner))


# ─────────────────────────── BEFUND 1 + 2: Zahl == Farbe ───────────────────────────

def test_kacheln_gleich_karten_in_jeder_rolle(node_exe):
    """Die vier Kacheln sind die Kopfzeile der Liste - sie muessen zaehlen, was
    darunter zu SEHEN ist. Gilt fuer Admin (stillgelegtes TU-4 raus, TU-3 mit
    -596 Tagen rein) genauso wie fuer den Monteur (nur sein Fahrzeug)."""
    out = _lauf(node_exe)
    for fall, r in out.items():
        assert r["KACHEL"] == r["KARTEN"], (
            "Kacheln und Karten widersprechen sich im Fall %s: "
            "Kachel=%s Karten=%s (Liste: %r)" % (fall, r["KACHEL"], r["KARTEN"], r["liste"])
        )


def test_monteur_sieht_seine_eigenen_zahlen(node_exe):
    out = _lauf(node_exe)
    assert out["monteur_m1"]["liste"] == "TU-1"
    assert out["monteur_m1"]["KACHEL"] == "1/0/0/0", \
        "Monteur mit einem sauberen Fahrzeug muss 1/0/0/0 lesen, nicht die Flottenzahlen"


def test_pickerl_596_tage_wird_gezaehlt(node_exe):
    """Befund 2: das am laengsten ueberfaellige Fahrzeug darf nicht aus der Zahl fallen."""
    out = _lauf(node_exe)
    assert out["admin"]["KACHEL"].split("/")[2] == "2", \
        "TU-3 (-596 Tage) fehlt in 'Pickerl faellig' - der 365-Tage-Deckel ist zurueck"


def test_stillgelegtes_erhoeht_keine_kachel(node_exe):
    """TU-4 ist stillgelegt, hat einen offenen Schaden und ein faelliges Service -
    ohne Karte darf es in keiner Kachel auftauchen."""
    out = _lauf(node_exe)
    assert out["admin"]["KACHEL"] == "3/3/2/1"
    assert out["admin_alle_stillgelegt"]["KACHEL"] == "0/0/0/0"


# ─────────────────────────── BEFUND 3: Leertext an der Pruefung ───────────────────────────

def test_leergrund_unterscheidet_vier_faelle(node_exe):
    out = _lauf(node_exe)
    assert out["admin_gar_keine"]["leerGrund"] == "keine_daten"
    assert out["admin_alle_stillgelegt"]["leerGrund"] == "alle_stillgelegt"
    assert out["monteur_nur_stillgelegtes"]["leerGrund"] == "meines_stillgelegt", \
        "Monteur mit stillgelegtem eigenem Fahrzeug liest wieder 'Kein Fahrzeug zugewiesen'"
    assert out["monteur_ohne"]["leerGrund"] == "nicht_zugewiesen"


def test_leertexte_haengen_am_grund_nicht_an_der_rolle():
    """Die beiden gerenderten Zeilen muessen _fzEmptyGrund lesen. Reine Formpruefung,
    absichtlich schmal: die Bedeutung misst test_leergrund_unterscheidet_vier_faelle."""
    i = HTML.index('!sel&&!batchMode&&visibleFz.length===0&&!fzScanMode')
    block = HTML[i:i + 2600]
    assert block.count("_fzEmptyGrund===") >= 6, \
        "Leerzustands-Texte lesen _fzEmptyGrund nicht (Rollen-Ternaer zurueck?)"
    assert "Dein Fahrzeug ist stillgelegt" in block


# ─────────────────────────── UMKEHRPROBEN ───────────────────────────

def test_umkehrprobe_grundmenge(node_exe):
    """Grundmenge zurueck auf `fahrzeuge` -> die Messung MUSS rot werden."""
    alt = _schnitt()
    alt = alt.replace("const aktiv=visibleFz.length;",
                      'const aktiv=fahrzeuge.filter(f=>f.status!=="stillgelegt").length;')
    alt = alt.replace("()=>visibleFz.reduce", "()=>fahrzeuge.reduce")
    alt = alt.replace("const serviceFaellig=visibleFz.filter", "const serviceFaellig=fahrzeuge.filter")
    out = _lauf(node_exe, alt)
    assert any(r["KACHEL"] != r["KARTEN"] for r in out.values()), \
        "UMKEHRPROBE BLIND: der alte Zustand (Grundmenge fahrzeuge) faellt nicht auf"


def test_umkehrprobe_365_tage_deckel(node_exe):
    """Deckel wieder rein -> TU-3 (-596 Tage) faellt aus der Zahl, Messung MUSS rot werden."""
    alt = _schnitt().replace(
        "const pickerFaellig=visibleFz.filter(f=>{const _pkSt=window._pickerlStatus(f.pickerl);"
        "return _pkSt==='warn'||_pkSt==='overdue';}).length;",
        "const pickerFaellig=visibleFz.filter(f=>{const _pkSt=window._pickerlStatus(f.pickerl);"
        "if(!_pkSt||_pkSt==='ok')return false;const d=new Date(f.pickerl+\"T00:00:00\");"
        "return (d-new Date())/TIME_DAY>-365;}).length;")
    assert "TIME_DAY>-365" in alt, "Umkehrprobe hat nicht gegriffen - Zeile umgebaut?"
    out = _lauf(node_exe, alt)
    assert out["admin"]["KACHEL"] != out["admin"]["KARTEN"], \
        "UMKEHRPROBE BLIND: der 365-Tage-Deckel faellt nicht auf"


def test_umkehrprobe_leergrund_an_der_rolle(node_exe):
    """Leergrund zurueck an die Rolle -> die beiden Monteur-Faelle kollabieren."""
    alt = re.sub(r"  const _fzEmptyGrund=[\s\S]*?\"nicht_zugewiesen\"\);",
                 '  const _fzEmptyGrund=isVAdmin?"alle_stillgelegt":"nicht_zugewiesen";',
                 _schnitt())
    out = _lauf(node_exe, alt)
    assert out["monteur_nur_stillgelegtes"]["leerGrund"] == out["monteur_ohne"]["leerGrund"], \
        "UMKEHRPROBE BLIND: der Rollen-Ternaer faellt nicht auf"


# ─────────────────────────── Nachbarzahlen, die NICHT kippen duerfen ───────────────────────────

def test_labels_druck_und_excel_unveraendert():
    """Der Labels-Button bleibt auf visibleFz, der Excel-Export bleibt auf `fahrzeuge`
    (er hat eine Status-Spalte und ist isVAdmin-gegated - stillgelegte gehoeren dort hinein)."""
    assert "printLabels(visibleFz.filter(f=>f.status!==\"stillgelegt\")" in HTML
    assert 'COMPANY_FOOTER.name+" · "+fahrzeuge.length+" Fahrzeuge"' in HTML


def test_dashboard_alerts_unveraendert():
    """Das Dashboard ist ein eigener Ort mit eigener Grundmenge (_alertFz) - dieser
    Fix fasst ihn nicht an. Faellt der Riegel, ist das Dashboard mitgeaendert worden
    und die Nachbarzahlen muessen neu bewertet werden."""
    assert "const _alertFz=_isFleetAdmin?(fahrzeuge||[]):(fahrzeuge||[]).filter(f=>f.fahrer===_myMonteurId);" in HTML
    assert "const aktivFz=(fahrzeuge||[]).filter(f=>f.status!==\"stillgelegt\").length;" in HTML
