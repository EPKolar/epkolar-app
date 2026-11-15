# -*- coding: utf-8 -*-
"""v3.9.1014 - drei Entscheidungen des Geschaeftsfuehrers.

1. Planung: KEINE Markierung "doppelt eingeplant" fuer Mitarbeiter mehr (ein Monteur auf mehreren
   Baustellen am Tag ist fachlich normal). Fahrzeug-Konflikte (fzConflicts) bleiben.
2. KW-Anzeige (nur Anzeige): Wochenbericht/Projektkopf nennen die KW der Woche, die die Tabelle
   tatsaechlich zeigt (_kwZiel), die Dispo-KW-Tabs tragen das Jahr.
3. Haekchen app-weit sichtbar (GCSS), Maengel-Review: lokaler Zustand == geschriebener Zustand.

Jede verneinende Zusicherung hat eine Umkehrprobe: derselbe Pruefer muss die alte Form (v3.9.1013)
melden - sonst waere die Abwesenheit trivial wahr.
"""
import json
import re

from conftest import run_node_snippet
from _hilfen import nur_code


# ── Hilfen ────────────────────────────────────────────────────────────────────

def _weekplan(code):
    a = code.find("function WeekPlan(")
    assert a != -1, "WeekPlan nicht gefunden - der Riegel misst sonst nichts."
    e = code.find("\nfunction ", a + 10)
    assert e > a
    return code[a:e]


# Alte Formen aus v3.9.1013 (woertlich), fuer die Umkehrproben.
ALT_MA_BERECHNUNG = "const maConflicts=_react.useMemo.call(void 0, ()=>{const cells={},perDay={},byMa={};});"
ALT_MA_HINWEIS = ", maConflicts.list.length>0&&_wpDoppelHinweis()"
ALT_MA_ZELLE = "title: m.dop?(m.n+\" – doppelt eingeplant, auch bei: \"+m.dop.join(\", \")):m.n"
ALT_MA_TAG = "_zpWarn(),maConflicts.perDay[d]+\" doppelt\")"


def _ma_markierung(seg):
    """Fundstellen der MA-Doppelmarkierung im Planungs-Code (leer = keine)."""
    funde = []
    for begriff in ("maConflicts", "_wpDoppelHinweis", "doppelt eingeplant",
                    "Doppelt eingeplant", "underline wavy", "+\" doppelt\"", "+' doppelt'"):
        if begriff in seg:
            funde.append(begriff)
    return funde


# ── 1. MA-Doppelmarkierung weg, Fahrzeug-Konflikte bleiben ───────────────────

def test_ma_doppelmarkierung_ist_weg(index_html):
    seg = _weekplan(nur_code(index_html))
    assert _ma_markierung(seg) == [], (
        "\U0001F534 Die Planung markiert wieder Mitarbeiter als doppelt eingeplant: %s\n"
        "  Entscheidung GF v3.9.1014: ein MA auf mehreren Baustellen am Tag ist normal."
        % _ma_markierung(seg))


def test_ma_doppelmarkierung_umkehrprobe(index_html):
    """Der Pruefer schlaegt auf jede alte Form an - sonst waere 'weg' trivial wahr."""
    seg = _weekplan(nur_code(index_html))
    for alt in (ALT_MA_BERECHNUNG, ALT_MA_HINWEIS, ALT_MA_ZELLE, ALT_MA_TAG):
        assert _ma_markierung(seg + "\n" + alt), "Pruefer erkennt die alte Form nicht: " + alt


def test_fahrzeug_konflikte_bleiben(index_html):
    seg = _weekplan(nur_code(index_html))
    assert "const fzConflicts=_react.useMemo" in seg, "fzConflicts-Berechnung fehlt"
    # Zelle Schreibtisch, Telefon-Karte, Tageskopf, Wochenliste: Fahrzeug-Warnung sichtbar
    n = seg.count("Fahrzeug doppelt gebucht")
    assert n >= 4, "Fahrzeug-Konflikt-Anzeige geschrumpft (%d Stellen)" % n
    assert "Object.keys(fzConflicts).length>0?React.createElement" in seg, (
        "Der Konflikt-Zaehler in der Kopfzeile meldet Fahrzeug-Konflikte nicht mehr.")


def test_fahrzeug_konflikte_umkehrprobe(index_html):
    seg = _weekplan(nur_code(index_html)).replace("Fahrzeug doppelt gebucht", "x")
    assert seg.count("Fahrzeug doppelt gebucht") < 4


# ── 2. KW-Anzeige ────────────────────────────────────────────────────────────

def _zeile(html, kopf):
    m = re.search(r"(?m)^" + re.escape(kopf) + r".*$", html)
    assert m, "Zeile nicht gefunden: " + kopf
    return m.group(0)


def test_wochenbericht_ueberschrift_folgt_der_gezeigten_woche(node_exe, index_html):
    """WIRKUNG: fuer jedes Jahr 2020-2035 und jede kw 1..53 nennt die Ueberschrift
    (_kwZiel(yr,kw)) genau die ISO-Woche, deren Tage VBer zeigt (getISO(yr,kw))."""
    code = nur_code(index_html)
    helfer = "\n".join(_zeile(index_html, k) for k in (
        "const _getMaxKW=", "const _kwZiel=", "const isoWof=", "const isoWYof="))
    m = re.search(r"const getISO=\(y,w\)=>\{[^\n]*?return d;\};", code)
    assert m, "getISO in VBer nicht gefunden"
    js = helfer + "\n" + m.group(0) + r"""
const out={neu:[],alt:[]};
for(let y=2020;y<=2035;y++)for(let k=1;k<=53;k++){
  const mo=getISO(y,k);const th=new Date(mo);th.setDate(mo.getDate()+3);
  const w=isoWof(th),wy=isoWYof(th);const z=_kwZiel(y,k);
  if(z[1]!==w||z[0]!==wy)out.neu.push([y,k,z,w,wy]);
  if(k!==w||y!==wy)out.alt.push([y,k,w,wy]);
}
console.log(JSON.stringify(out));"""
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["neu"] == [], "Ueberschrift != gezeigte Woche: %s" % r["neu"][:5]
    # Umkehrprobe: die rohe Anzeige (kw, yr) weicht in 52-Wochen-Jahren bei kw=53 ab.
    assert r["alt"], "Umkehrprobe greift nicht - der Test koennte nichts unterscheiden."
    assert [2027, 53, 1, 2028] in r["alt"]


def test_wochenbericht_und_kopf_nutzen_kwziel(index_html):
    code = nur_code(index_html)
    a = code.find("function VBer(")
    vber = code[a:code.find("\nfunction ", a + 5)]
    assert "\"KW \", _kwZiel(yr,kw)[1], \"/\", _kwZiel(yr,kw)[0]" in vber
    assert "\"KW\", kw, \"/\", yr" not in vber, "alte rohe Anzeige steht wieder im Wochenbericht"
    a = code.find("function ProjectShell(")
    shell = code[a:code.find("\nfunction ", a + 5)]
    assert "\"KW \" , _kwZiel(yr,kw)[1], \"/\", _kwZiel(yr,kw)[0]" in shell
    # NUR ANZEIGE: der Zustand bleibt wie in v3.9.993 (yr je Render, kw als State)
    assert "const yr=isoWY();" in shell
    assert "const [kw,setKw]=_react.useState.call(void 0, isoW());" in shell


def test_dispo_kw_tab_mit_jahr(index_html):
    code = nur_code(index_html)
    assert "\"KW \"+W.kw+\"/\"+W.yr+\" (\"+st.geplant+\" geplant)\"" in code
    assert "\"KW \"+W.kw+\" (\"+st.geplant" not in code, "Dispo-Tab wieder ohne Jahr"


# ── 3a. Haekchen ─────────────────────────────────────────────────────────────

GRUND = "input,select,textarea{font-size:16px !important;-webkit-appearance:none;border-radius:8px}"
KUR = "input[type=checkbox],input[type=radio]{-webkit-appearance:auto;appearance:auto;accent-color:#009640}"


def _gcss(code):
    a = code.find("const GCSS=()=>`")
    assert a != -1
    e = code.find("`;", a + 16)
    return code[a:e]


def _haekchen_sichtbar(gcss):
    """Kaestchen/Optionsfeld erhalten ihr Erscheinungsbild zurueck, NACH der Grundregel."""
    g = gcss.find(GRUND)
    k = gcss.find(KUR)
    return g != -1 and k != -1 and k > g


def test_haekchen_regel_ueberschreibt_grundregel(index_html):
    assert _haekchen_sichtbar(_gcss(nur_code(index_html))), (
        "\U0001F534 Kaestchen erben wieder -webkit-appearance:none und zeichnen nichts.")


def test_haekchen_umkehrprobe(index_html):
    g = _gcss(nur_code(index_html))
    assert not _haekchen_sichtbar(g.replace(KUR, ""))
    # vor der Grundregel waere sie bei gleicher Quelle wirkungslos-anfaellig: Reihenfolge zaehlt
    assert not _haekchen_sichtbar(g.replace(KUR, "").replace(GRUND, KUR + GRUND))


def test_keine_kaestchen_mit_eigenem_appearance_none(index_html):
    """Kein bewusst gestaltetes Eigen-Kaestchen wird von der Kur ueberfahren."""
    code = nur_code(index_html)
    for m in re.finditer(r"type: ?['\"](?:checkbox|radio)['\"][^)]{0,400}", code):
        s = m.group(0)
        assert "appearance:'none'" not in s and 'appearance:"none"' not in s, s[:200]


# ── 3b. Maengel-Review: lokal == geschrieben ─────────────────────────────────

ALT_ACCEPT_PUT = 'body:{status:"offen",assignee:reviewWorker,zugewiesen:reviewWorker,kunde_status:"angenommen",review_note:reviewNote||"Wird bearbeitet"}'
ALT_REJECT_LOKAL = '{...m,kundeStatus:"abgelehnt",reviewNote:reviewNote}'

STUBS = r"""
function _optionalChain(ops){let v=ops[0],last;for(let i=1;i<ops.length;i+=2){const op=ops[i],fn=ops[i+1];
 if((op==='optionalAccess'||op==='optionalCall')&&v==null)return undefined;
 if(op==='access'||op==='optionalAccess'){last=v;v=fn(v);}else{const f=v,o=last;v=fn((...a)=>f.apply(o,a));}}return v;}
const window={__toast:()=>{},_allUsers:[],__pushNotif:null};
const isAdmin=true,reviewWorker='w7',reviewNote='Begruendung',curUser={id:'u1'},p={name:'P'};
let state={maengel:[{id:'m1',status:'offen',prio:'normal',kundeStatus:'gemeldet',melder:'Kunde',name:'M'}]};
const forms=state;const puts=[];
const setForms=(f)=>{state=f(state);};const SQ={push:(x)=>puts.push(x)};
const setReviewId=()=>{},setReviewNote=()=>{};const _syncTicketStatus=()=>{};
"""

# DB-Spalte -> lokales Feld (aus _mapDefect)
SPIEGEL = {"status": "status", "prio": "prio", "kunde_status": "kundeStatus",
           "review_note": "reviewNote", "zugewiesen": "zugewiesen"}


def _fn(code, name):
    a = code.find("const " + name + "=(id)=>{")
    assert a != -1, name + " nicht gefunden"
    e = code.find('setReviewId(null);setReviewNote("");};', a)
    assert e > a
    return code[a:e + len('setReviewId(null);setReviewNote("");};')]


def _verlauf_helfer(code):
    """v3.9.1018: reviewAccept/-Reject rufen die echten Statusverlauf-Helfer (_mgVerlaufFeld/_mgVerlaufPut)."""
    a = code.index("function _mgVerlaufListe(m){")
    e = code.index("function _mgStText(", a)
    jp = "const _jp=(v)=>{if(typeof v==='string'){try{return JSON.parse(v);}catch(_e){return v;}}return v;};\n"
    return jp + code[a:e]


def _lauf(node_exe, fn_src, name, helfer=""):
    js = STUBS + helfer + fn_src + "\n" + name + "('m1');console.log(JSON.stringify({m:state.maengel[0],puts}));"
    return json.loads(run_node_snippet(node_exe, js))


def _abweichungen(r):
    """Felder, die geschrieben UND lokal gefuehrt werden, aber nicht uebereinstimmen,
    plus lokal veraenderte Felder mit DB-Spiegel, die NICHT geschrieben wurden."""
    body = r["puts"][-1]["body"]
    m = r["m"]
    aus = []
    for db, lok in SPIEGEL.items():
        if db in body and m.get(lok) != body[db]:
            aus.append((db, body[db], m.get(lok)))
    start = {"status": "offen", "prio": "normal", "kundeStatus": "gemeldet"}
    for db, lok in SPIEGEL.items():
        if lok in start and m.get(lok) != start[lok] and db not in body:
            aus.append(("nur lokal", lok, m.get(lok)))
    return aus


def test_review_accept_lokal_gleich_geschrieben(node_exe, index_html):
    r = _lauf(node_exe, _fn(nur_code(index_html), "reviewAccept"), "reviewAccept", _verlauf_helfer(nur_code(index_html)))
    assert _abweichungen(r) == [], _abweichungen(r)
    assert r["puts"][-1]["body"]["prio"] == "hoch" and r["m"]["prio"] == "hoch"


def test_review_reject_lokal_gleich_geschrieben(node_exe, index_html):
    r = _lauf(node_exe, _fn(nur_code(index_html), "reviewReject"), "reviewReject", _verlauf_helfer(nur_code(index_html)))
    assert _abweichungen(r) == [], _abweichungen(r)
    assert r["m"]["status"] == "abgelehnt"


def test_review_umkehrprobe_alte_formen(node_exe, index_html):
    code = nur_code(index_html)
    acc = _fn(code, "reviewAccept")
    neu_put = re.search(r'body:\{status:"offen",prio:"hoch",[^}]*\}', acc).group(0)
    alt_acc = acc.replace(neu_put, ALT_ACCEPT_PUT)
    assert ("nur lokal", "prio", "hoch") in _abweichungen(_lauf(node_exe, alt_acc, "reviewAccept", _verlauf_helfer(code)))
    rej = _fn(code, "reviewReject")
    alt_rej = rej.replace('{...m,status:"abgelehnt",kundeStatus:"abgelehnt",reviewNote:reviewNote,..._vhR}', ALT_REJECT_LOKAL)
    assert alt_rej != rej
    assert ("status", "abgelehnt", "offen") in [tuple(x) for x in _abweichungen(_lauf(node_exe, alt_rej, "reviewReject", _verlauf_helfer(code)))]
