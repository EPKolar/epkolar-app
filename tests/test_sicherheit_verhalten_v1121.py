"""Verhaltenstests fuer drei Sicherheitsfunktionen (Stand 3.9.1121, Mutationslauf 26.11.2026).

Bisher hatten _OFFPW, _maskSVNR und die Reisepass-/SV-Nr.-Anzeige im Mitarbeiter-Detail nur Textpins.
Die K-Mutationen #34 (_OFFPW.verify immer wahr), #37 (_maskSVNR zeigt die ersten 4 Ziffern) und
#38 (Reisepass-Nr. im Klartext fuer Nicht-Staff) liessen die ganze Suite gruen.
Diese Datei fuehrt den echten Code aus index.html in node aus:

1. _OFFPW: create + verify (richtig / falsch / anderer Benutzer / leeres Kennwort / kaputter Speicher).
2. _maskSVNR: ohne Admin-Recht keine einzige Ziffer sichtbar (Politik laut Code: feste Maske
   '•••• •••••', leer -> '—'), Admin sieht den Wert; wirft nie.
3. Mitarbeiter-Detail (SV-Nr.- und Reisepass-Zeile, React.createElement durch einen Rekorder ersetzt):
   Klartext nur fuer admin und buero (_maPersDatenRolle, GF v3.9.1104), alle anderen Rollen sehen
   keine Ziffer der SV-Nr. und kein Zeichen der Passnummer.
"""
import json
import shutil
import subprocess

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")

ROLLEN = ["admin", "buero", "projektleiter", "techniker", "obermonteur", "monteur", "helfer", "lager_display"]
STAFF_PERS = {"admin", "buero"}


def _block(src, kopf, ende):
    i = src.index(kopf)
    return src[i:src.index(ende, i + len(kopf)) + len(ende)]


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


def _offpw(src):
    return _block(src, "const _OFFPW={", "\n};")


def _mask(src):
    return _block(src, "window._maskSVNR=(svnr,isAdmin)=>{", "};")


def _persrolle(src):
    return _block(src, "function _maPersDatenRolle(u){", "\n}")


def _detail_zeilen(src):
    """SV-Nr.- und Reisepass-Zeile aus dem Mitarbeiter-Detail (bis vor die Geburtsdatum-Zeile)."""
    kopf = ", React.createElement('span', { style: {color:V.dm}}, \"SV-Nr.\"), _maPersDatenRolle(curUser)?"
    ende = ", React.createElement('span', { style: {color:V.dm}}, \"Geburtsdatum\")"
    i = src.index(kopf)
    assert src.count(kopf) == 1, "SV-Nr.-Zeile im Mitarbeiter-Detail nicht eindeutig"
    j = src.index(ende, i)
    frag = src[i:j].rstrip()
    assert "Reisepass-Nr." in frag, "Reisepass-Zeile liegt nicht mehr zwischen SV-Nr. und Geburtsdatum"
    return frag


# ── 1. _OFFPW ───────────────────────────────────────────────────────────────
@needs_node
def test_offpw_verify_verhalten(index_html):
    js = r"""
%s;
(async()=>{
  const st=await _OFFPW.create("Max.Muster","Geheim-123");
  const r={};
  r.form={v:st.v,algo:st.algo,iter:st.iter,saltLen:st.salt.length,hashLen:st.hash.length,
          pwImKlartext:JSON.stringify(st).includes("Geheim-123")};
  r.richtig=await _OFFPW.verify("Max.Muster","Geheim-123",st);
  r.richtigGrossKlein=await _OFFPW.verify("  max.muster ","Geheim-123",st);
  r.falsch=await _OFFPW.verify("Max.Muster","Geheim-124",st);
  r.pwGrossKlein=await _OFFPW.verify("Max.Muster","geheim-123",st);
  r.andererUser=await _OFFPW.verify("Eva.Muster","Geheim-123",st);
  r.leer=await _OFFPW.verify("Max.Muster","",st);
  r.undef=await _OFFPW.verify("Max.Muster",undefined,st);
  r.ohneSpeicher=await _OFFPW.verify("Max.Muster","Geheim-123",null);
  r.fremderHash=await _OFFPW.verify("Max.Muster","Geheim-123",{...st,hash:"00".repeat(32)});
  r.fremdesSalt=await _OFFPW.verify("Max.Muster","Geheim-123",{...st,salt:"ab".repeat(16)});
  r.ohneHash=await _OFFPW.verify("Max.Muster","Geheim-123",{...st,hash:""});
  r.falscheVersion=await _OFFPW.verify("Max.Muster","Geheim-123",{...st,v:2});
  r.objektLeer=await _OFFPW.verify("Max.Muster","Geheim-123",{});
  const st2=await _OFFPW.create("Max.Muster","Geheim-123");
  r.saltZufall=st2.salt!==st.salt&&st2.hash!==st.hash;
  // leeres Kennwort gespeichert: nur leer passt, anderes nicht
  const stL=await _OFFPW.create("Max.Muster","");
  r.leerGespeichertLeer=await _OFFPW.verify("Max.Muster","",stL);
  r.leerGespeichertAnderes=await _OFFPW.verify("Max.Muster","x",stL);
  // Altformat (base64) - Grace-Migration
  const alt=btoa("max.muster:Geheim-123");
  r.altRichtig=await _OFFPW.verify("Max.Muster","Geheim-123",alt);
  r.altFalsch=await _OFFPW.verify("Max.Muster","Geheim-12",alt);
  r.altAndererUser=await _OFFPW.verify("Eva.Muster","Geheim-123",alt);
  process.stdout.write(JSON.stringify(r));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1);});
""" % _offpw(index_html)
    r = _node(js)
    assert r["form"] == {"v": 1, "algo": "PBKDF2-SHA256", "iter": 100000, "saltLen": 32, "hashLen": 64,
                         "pwImKlartext": False}, r["form"]
    assert r["richtig"] is True
    assert r["richtigGrossKlein"] is True, "Benutzername wird normalisiert (lower+trim)"
    assert r["saltZufall"] is True
    assert r["leerGespeichertLeer"] is True
    assert r["altRichtig"] is True
    for k in ("falsch", "pwGrossKlein", "andererUser", "leer", "undef", "ohneSpeicher", "fremderHash",
              "fremdesSalt", "ohneHash", "falscheVersion", "objektLeer", "leerGespeichertAnderes",
              "altFalsch", "altAndererUser"):
        assert r[k] is False, (k, r)


# ── 2. _maskSVNR ────────────────────────────────────────────────────────────
EINGABEN = ["1234010185", "1234 010185", "1234/010185", "1234-01.01.85", " 1234 010185 ", "12", "1",
            "1234", "12340101851234", "abc", "", None, 1234010185, 0, "0000000000"]


@needs_node
def test_masksvnr_zeigt_ohne_recht_keine_ziffer(index_html):
    js = r"""
const window={};
%s;
const ein=%s;
const out=[];
for(const v of ein){
  for(const adm of [false,undefined,null,0,"",true]){
    let res,err=null;
    try{res=window._maskSVNR(v,adm);}catch(e){err=String(e);}
    out.push({v,adm,res:res===undefined?"<undef>":String(res),err});
  }
}
process.stdout.write(JSON.stringify(out));
""" % (_mask(index_html), json.dumps(EINGABEN))
    out = _node(js)
    assert len(out) == len(EINGABEN) * 6
    for o in out:
        assert o["err"] is None, o
        v, adm, res = o.get("v"), o.get("adm"), o["res"]  # undefined faellt in JSON weg
        leer = not v
        if adm is True:
            assert res == ("—" if leer else str(v)), o
            continue
        # Nicht-Admin: niemals eine Ziffer, nie der Eingabewert, nie undefined
        assert not any(c.isdigit() for c in res), o
        assert res != "<undef>", o
        if leer:
            assert res == "—", o
        else:
            assert res == "•••• •••••", o
            assert str(v).strip() not in res, o


# ── 3. Mitarbeiter-Detail: SV-Nr. und Reisepass je Rolle ───────────────────
def _render_js(src, mit_maske=True):
    return r"""
const window={};
%s;
%s;
%s
const V={dm:"#888"},mono="monospace";const II=()=>({});const updMonteur=()=>{};
const React={createElement:(t,p,...k)=>({t,p:p||{},k})};
function texte(n,acc){
  if(n==null||n===false||n===true)return acc;
  if(Array.isArray(n)){n.forEach(x=>texte(x,acc));return acc;}
  if(typeof n==="object"){
    if(n.p&&n.p.value!=null)acc.push({art:"input",s:String(n.p.value)});
    if(n.p&&n.p.placeholder!=null)acc.push({art:"placeholder",s:String(n.p.placeholder)});
    texte(n.k,acc);return acc;
  }
  acc.push({art:"text",s:String(n)});return acc;
}
const rollen=%s;
const faelle=[{svnr:"9876 150372",reisepass:"P 4455667"},{svnr:"",reisepass:""}];
const out=[];
for(const role of rollen){
  for(const selM of faelle){
    const curUser={role,id:"u1"};
    const arr=[0 %s];
    out.push({role,svnr:selM.svnr,reisepass:selM.reisepass,teile:texte(arr.slice(1),[]),pers:_maPersDatenRolle(curUser)});
  }
}
process.stdout.write(JSON.stringify(out));
""" % (_persrolle(src), _mask(src) if mit_maske else "", "" if mit_maske else "/* ohne _maskSVNR: Rueckfallzweig */",
       json.dumps(ROLLEN), _detail_zeilen(src))


def _pruefe_detail(out):
    assert len(out) == len(ROLLEN) * 2
    for o in out:
        role, sv, rp = o["role"], o["svnr"], o["reisepass"]
        sichtbar = [t["s"] for t in o["teile"] if t["art"] in ("text", "input")]
        alles = " ".join(sichtbar)
        assert o["pers"] is (role in STAFF_PERS), o
        if role in STAFF_PERS:
            inputs = [t["s"] for t in o["teile"] if t["art"] == "input"]
            assert inputs == [sv, rp], o  # Klartext editierbar
            continue
        assert not any(t["art"] == "input" for t in o["teile"]), ("Nicht-Staff bekommt Eingabefeld", o)
        # keine Ziffer der SV-Nr. / Passnummer, kein Teil der Passnummer
        assert not any(c.isdigit() for c in alles), ("Ziffer sichtbar fuer " + role, o)
        if rp:
            assert rp not in alles and "P 4" not in alles, o
            assert "•••••••" in sichtbar, o
            assert "•••• •••••" in sichtbar or "—" in sichtbar, o
        else:
            assert sichtbar.count("—") >= 1, o


@needs_node
def test_mitarbeiter_detail_svnr_reisepass_je_rolle(index_html):
    out = _node(_render_js(index_html, mit_maske=True))
    _pruefe_detail(out)
    # mit Maske: Nicht-Staff sieht fuer die SV-Nr. genau die feste Maske
    for o in out:
        if o["role"] not in STAFF_PERS and o["svnr"]:
            assert "•••• •••••" in [t["s"] for t in o["teile"]], o


@needs_node
def test_mitarbeiter_detail_ohne_maskenfunktion_kein_klartext(index_html):
    """Rueckfallzweig, falls window._maskSVNR fehlt: Nicht-Staff sieht '—', nie die SV-Nr."""
    out = _node(_render_js(index_html, mit_maske=False))
    _pruefe_detail(out)
