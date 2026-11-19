# -*- coding: utf-8 -*-
"""v3.9.1052 Lieferanten-Zugangsdaten: raus aus supplier_configs (Klartext fuer jeden Angemeldeten), rein in
supplier_credentials (nur Admin, password per REST nie lesbar).

Node fuehrt die ECHTEN Funktionen aus index.html aus (_supplierLaden, _supplierZugangSpeichern, _supplierZugangNeu,
_suppTabFehlt, _supplierCredStand, _supplierSaveBody und den Rumpf von saveSupplier) gegen einen falschen Server:
  * supplier_credentials: Modus "ok" (Tabelle da), "404" (SQL nicht eingespielt), "403" (Rechte fehlen)
  * supplier_configs: liefert ABSICHTLICH immer auch username/password (wie ein Server, der zu viel schickt) -
    die App muss sie trotzdem nie in den Zustand nehmen, ausser im Rueckfall fuer den Admin.
Dazu statische Pruefung des SQL-Entwurfs und Umkehrproben (Riegel entfernt -> Test schlaegt an).
"""
import json
import os
import re
import subprocess

from conftest import EPK_TEST_TIMEOUT

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)
SQL = os.path.join(WURZEL, "sql", "LIEFERANTEN_ZUGANG_v1052_ENTWURF.sql")


def _funktion(src, name):
    i = src.find("\nfunction " + name + "(")
    if i < 0:
        i = src.index("\nasync function " + name + "(")
    a = i + 1
    e = src.index("\n}\n", a) + 2
    return src[a:e]


def _save_rumpf(src):
    a = src.index("  const saveSupplier=async(data)=>{")
    e = src.index("\n  const deleteSupplier=", a)
    return src[a:e]


def _quelle(src):
    m = re.search(r'const SUPP_CFG_SPALTEN="[^"]*";', src)
    assert m
    teile = [m.group(0), "var _suppCredTabDa=null;"]
    teile += [_funktion(src, n) for n in ("_suppTabFehlt", "_supplierLaden", "_supplierZugangNeu",
                                           "_supplierZugangSpeichern", "_supplierCredStand", "_supplierSaveBody")]
    teile.append("async function saveSupplierTest(data){\n" + _save_rumpf(src) + "\n  return await saveSupplier(data);\n}")
    return "\n".join(teile)


GEHEIM = "Geheim-4711!"

PRELUDE = r"""
var toasts=[];var logs=[];var window={__toast:function(m){toasts.push(String(m));},__doSync:function(){}};
var console={log:function(){logs.push([].slice.call(arguments).join(" "));},warn:function(){logs.push([].slice.call(arguments).join(" "));},error:function(){logs.push([].slice.call(arguments).join(" "));}};
var SB_REST="https://x/rest/v1";
var credModus="ok";var cfgModus="ok";var gets=[];var sends=[];var pushes=[];var postStatus=201;
var CFG=[{id:"u1",name:"Holter",skonto_prozent:3,config:"{}",username:"holter-user",password:"__GEHEIM__"},
         {id:"u2",name:"Impex",skonto_prozent:2,config:"{}",username:"",password:""}];
var CRED=[{supplier_id:"u1",username:"holter-user",has_password:true}];
async function _sbGet(tab,q){
  gets.push(tab+"?"+q);
  if(tab==="supplier_credentials"){
    if(credModus==="404")throw new Error('HTTP404 {"code":"PGRST205","message":"Could not find the table public.supplier_credentials"}');
    if(credModus==="403"){const a=[];a.__rlsFehler=403;return a;}
    return JSON.parse(JSON.stringify(CRED));
  }
  if(tab==="supplier_configs"){
    if(cfgModus==="400"&&q.indexOf("select=")>=0)throw new Error('HTTP400 {"code":"42703","message":"column does not exist"}');
    return JSON.parse(JSON.stringify(CFG));
  }
  return [];
}
function _sbWH(p){return {"Content-Type":"application/json","Prefer":p||"return=representation"};}
function _fT(init){return init;}
async function _authRetry(fn){return await fn();}
async function fetch(url,init){sends.push({url:url,method:init.method,prefer:init.headers.Prefer,body:init.body});
  if(init.method==="POST")return {ok:postStatus<300,status:postStatus};return {ok:true,status:204};}
var _n=0;function _uuid(){_n++;return "neu-"+_n;}
var SQ={push:async function(x){pushes.push(JSON.parse(JSON.stringify(x)));}};
function setSuppEdit(){}function setSuppNew(){}function fetchSuppliers(){}function setTimeout(){}
function _optionalChain(ops){let l;let v=ops[0];let i=1;while(i<ops.length){const op=ops[i];const fn=ops[i+1];i+=2;
  if((op==="optionalAccess"||op==="optionalCall")&&v==null)return undefined;
  if(op==="access"||op==="optionalAccess"){l=v;v=fn(v);}else{const f=v;v=fn((...a)=>f.call(l,...a));l=undefined;}}return v;}
var curUser={role:"admin"};
function neu(){gets=[];sends=[];pushes=[];toasts=[];logs=[];_suppCredTabDa=null;credModus="ok";cfgModus="ok";postStatus=201;curUser={role:"admin"};}
"""

KOERPER = r"""
(async()=>{
 const R={};
 /* Monteur/PL/Lager: nie supplier_credentials, feste Spaltenliste, kein Kennwort im Zustand */
 for(const rolle of ["monteur","projektleiter","buero"]){
   neu();curUser={role:rolle};
   const rows=await _supplierLaden(false);
   R["nicht_"+rolle]={gets:gets,keys:rows.map(r=>Object.keys(r)),stand:rows.map(_supplierCredStand)};
 }
 /* Admin, Tabelle da */
 neu();const ra=await _supplierLaden(true);
 R.admin={gets:gets,tab:_suppCredTabDa,keys:ra.map(r=>Object.keys(r)),stand:ra.map(_supplierCredStand),vorh:ra.map(r=>r._zugVorhanden),user:ra.map(r=>r.username)};
 /* Admin, SQL nicht eingespielt (404) -> bisheriger Weg, zweiter Aufruf fragt nicht mehr */
 neu();credModus="404";const r4=await _supplierLaden(true);const g1=gets.slice();gets=[];await _supplierLaden(true);
 R.r404={gets1:g1,gets2:gets,tab:_suppCredTabDa,keys:r4.map(r=>Object.keys(r)),stand:r4.map(_supplierCredStand)};
 /* Admin, 403 -> unlesbar, Tabelle bleibt unbekannt, kein Rueckfall auf Klartext */
 neu();credModus="403";const r3=await _supplierLaden(true);
 R.r403={gets:gets,tab:_suppCredTabDa,keys:r3.map(r=>Object.keys(r)),stand:r3.map(_supplierCredStand)};
 /* Spaltenliste passt nicht (400) -> alles laden, Kennwort sofort weg */
 neu();curUser={role:"monteur"};cfgModus="400";const r400=await _supplierLaden(false);
 R.r400={gets:gets,keys:r400.map(r=>Object.keys(r))};

 /* Speichern: Admin, Tabelle da, bestehender Haendler mit neuem Kennwort */
 neu();await _supplierLaden(true);gets=[];
 await saveSupplierTest({id:"u1",name:"Holter",_zugVorhanden:true,_passwortNeu:"__GEHEIM__",_usernameGeaendert:false});
 R.sAdmin={push:pushes,sends:sends,toasts:toasts};
 /* Admin, neuer Haendler mit Zugangsdaten -> POST mit derselben id wie die Warteschlange */
 neu();await _supplierLaden(true);
 await saveSupplierTest({name:"Neu",_usernameGeaendert:true,_usernameNeu:" neu-user ",_passwortNeu:"__GEHEIM__"});
 R.sNeu={push:pushes,sends:sends};
 /* POST 409 (Zeile gibt es schon) -> PATCH */
 neu();await _supplierLaden(true);postStatus=409;
 await saveSupplierTest({id:"u2",name:"Impex",_zugVorhanden:false,_passwortNeu:"__GEHEIM__"});
 R.s409={sends:sends.map(s=>s.method)};
 /* Speichern scheitert -> Meldung ohne Wert */
 neu();await _supplierLaden(true);postStatus=500;
 await saveSupplierTest({id:"u2",name:"Impex",_zugVorhanden:false,_passwortNeu:"__GEHEIM__"});
 R.sFehl={toasts:toasts};
 /* Nur Skonto geaendert -> kein Zugangsdaten-Aufruf */
 neu();await _supplierLaden(true);
 await saveSupplierTest({id:"u1",name:"Holter",skonto_prozent:"4",_zugVorhanden:true});
 R.sSkonto={sends:sends,push:pushes};
 /* Projektleiter speichert -> nie Zugangsdaten, nie supplier_credentials */
 neu();curUser={role:"projektleiter"};await _supplierLaden(false);
 await saveSupplierTest({id:"u1",name:"Holter",_passwortNeu:"__GEHEIM__",_usernameGeaendert:true,_usernameNeu:"x"});
 R.sPL={push:pushes,sends:sends,gets:gets};
 /* Admin im Rueckfall (404) -> bisheriger Weg: Kennwort in supplier_configs, kein supplier_credentials-Schreiben */
 neu();credModus="404";await _supplierLaden(true);
 await saveSupplierTest({id:"u1",name:"Holter",_passwortNeu:"__GEHEIM__"});
 R.s404={push:pushes,sends:sends};
 R.logs=logs;R.alleToasts=toasts;
 process.stdout.write(JSON.stringify(R));
})().catch(e=>{process.stderr.write(String(e&&e.stack||e));process.exit(1);});
"""


def _lauf(node_exe, tmp_path, quelle):
    code = (PRELUDE + quelle + KOERPER).replace("__GEHEIM__", GEHEIM)
    p = tmp_path / "lauf.js"
    p.write_text(code, encoding="utf-8")
    r = subprocess.run([node_exe, str(p)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")[:3000]
    return json.loads(r.stdout.decode("utf-8"))


def _cfg_select(g):
    return [x for x in g if x.startswith("supplier_configs?")]


# ── Verhalten ───────────────────────────────────────────────────────────────
def test_supplier_nicht_admin_fragt_nie_zugangsdaten(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    for rolle in ("monteur", "projektleiter", "buero"):
        x = r["nicht_" + rolle]
        assert not any(g.startswith("supplier_credentials") for g in x["gets"]), x
        sel = _cfg_select(x["gets"])
        assert len(sel) == 1 and "select=id,name," in sel[0], sel
        assert "password" not in sel[0] and "username" not in sel[0] and "select=*" not in sel[0], sel
        for k in x["keys"]:
            assert "password" not in k and "username" not in k, k
        assert x["stand"] == ["unlesbar", "unlesbar"]


def test_supplier_admin_liest_supplier_credentials_ohne_kennwort(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    a = r["admin"]
    assert a["gets"][0] == "supplier_credentials?select=supplier_id,username,has_password", a["gets"]
    sel = _cfg_select(a["gets"])
    assert len(sel) == 1 and "password" not in sel[0] and "username" not in sel[0] and "select=*" not in sel[0]
    assert a["tab"] is True
    for k in a["keys"]:
        assert "password" not in k
    assert a["stand"] == ["hinterlegt", "fehlt"]
    assert a["vorh"] == [True, False]
    assert a["user"] == ["holter-user", ""]


def test_supplier_404_rueckfall_wie_bisher(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    x = r["r404"]
    assert x["tab"] is False
    sel = _cfg_select(x["gets1"])
    assert len(sel) == 1 and ",username,password&" in sel[0], sel
    assert not any(g.startswith("supplier_credentials") for g in x["gets2"]), "404 muss gemerkt werden"
    for k in x["keys"]:
        assert "password" not in k, "auch im Rueckfall kommt das Kennwort nicht in den Zustand"
    assert x["stand"] == ["hinterlegt", "fehlt"]
    # Speichern im Rueckfall: bisheriger Weg ueber supplier_configs, keine supplier_credentials-Sendung
    s = r["s404"]
    assert s["push"][0]["body"].get("password") == GEHEIM
    assert s["sends"] == []


def test_supplier_403_und_400(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    x = r["r403"]
    assert x["tab"] is None and x["stand"] == ["unlesbar", "unlesbar"]
    assert not any(",username,password" in g for g in x["gets"]), "403 ist KEIN Freibrief fuer den Klartext-Weg"
    y = r["r400"]
    assert y["gets"][-1] == "supplier_configs?order=name.asc"
    for k in y["keys"]:
        assert "password" not in k and "username" not in k


def test_supplier_speichern_admin(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    s = r["sAdmin"]
    assert len(s["push"]) == 1
    assert "password" not in s["push"][0]["body"] and "username" not in s["push"][0]["body"]
    assert len(s["sends"]) == 1
    z = s["sends"][0]
    assert z["method"] == "PATCH" and z["url"].endswith("/supplier_credentials?supplier_id=eq.u1")
    assert z["prefer"] == "return=minimal"
    assert json.loads(z["body"]) == {"password": GEHEIM}
    n = r["sNeu"]
    pid = n["push"][0]["body"]["id"]
    assert n["push"][0]["method"] == "POST" and "password" not in n["push"][0]["body"] and "username" not in n["push"][0]["body"]
    assert n["sends"][0]["method"] == "POST" and n["sends"][0]["prefer"] == "return=minimal"
    assert json.loads(n["sends"][0]["body"]) == {"supplier_id": pid, "username": "neu-user", "password": GEHEIM}
    assert r["s409"]["sends"] == ["POST", "PATCH"]
    assert r["sSkonto"]["sends"] == []
    assert any("NICHT gespeichert" in t for t in r["sFehl"]["toasts"])


def test_supplier_projektleiter_speichert_nie_zugangsdaten(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    s = r["sPL"]
    assert s["sends"] == [] and not any(g.startswith("supplier_credentials") for g in s["gets"])
    assert "password" not in s["push"][0]["body"] and "username" not in s["push"][0]["body"]


def test_supplier_kennwort_nie_in_log_oder_meldung(index_html, node_exe, tmp_path):
    r = _lauf(node_exe, tmp_path, _quelle(index_html))
    blob = json.dumps(r["logs"]) + json.dumps(r["alleToasts"]) + json.dumps(r["sFehl"])
    assert GEHEIM not in blob
    for n in ("_supplierLaden", "_supplierZugangSpeichern", "_supplierZugangNeu", "_suppTabFehlt"):
        assert "console." not in _funktion(index_html, n), n


# ── Umkehrproben: Riegel entfernt -> die Tests oben schlagen an ─────────────
def test_supplier_umkehrprobe_nicht_admin_ohne_riegel(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("if(istAdmin&&_suppCredTabDa!==false){", "if(_suppCredTabDa!==false){", 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    assert any(g.startswith("supplier_credentials") for g in r["nicht_monteur"]["gets"])


def test_supplier_umkehrprobe_select_stern(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace('"select="+SUPP_CFG_SPALTEN+(alt?",username,password":"")+"&order=name.asc"', '"order=name.asc"', 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    sel = _cfg_select(r["nicht_monteur"]["gets"])
    assert "select=id,name," not in sel[0]


def test_supplier_umkehrprobe_ohne_404_erkennung(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("if(_suppTabFehlt(e))_suppCredTabDa=false;", "", 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    assert r["r404"]["tab"] is None
    assert r["r404"]["stand"] == ["unlesbar", "unlesbar"], "ohne Erkennung bricht der bisherige Weg - genau das verhindert der Rueckfall"


def test_supplier_umkehrprobe_kennwort_bleibt_im_rumpf(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("if(_zugTab||!_istAdm){delete body.username;delete body.password;}", "", 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    assert r["sAdmin"]["push"][0]["body"].get("password") == GEHEIM


# ── statisch: App ───────────────────────────────────────────────────────────
def test_supplier_app_statisch(index_html):
    assert "supplier_configs_safe" not in index_html, "die Sicht existiert in Prod nicht"
    a = index_html.index("  const fetchSuppliers=async()=>{")
    e = index_html.index("  const saveSupplier=async(data)=>{", a)
    fs = index_html[a:e]
    assert '_sbGet("supplier_configs"' not in fs
    assert '_supplierLaden(!!(curUser&&curUser.role==="admin"))' in fs
    m = re.search(r'const SUPP_CFG_SPALTEN="([^"]*)";', index_html)
    spalten = m.group(1).split(",")
    assert "password" not in spalten and "username" not in spalten
    # alles, was _supplierSaveBody zurueckschreibt, muss geladen sein (sonst ueberschreibt Speichern mit Leerwerten)
    body = _funktion(index_html, "_supplierSaveBody")
    for f in re.findall(r"(\w+):(?:parseFloat\(|parseInt\()?data\.(\w+)", body):
        assert f[1] in spalten, f
    # Kartenzustand der Zugangsdaten nur fuer Admin
    assert 'credStand!=="hinterlegt"&&curUser&&curUser.role==="admin"&&' in index_html
    # alle anderen supplier_configs-Leser waehlen Spalten selbst
    for m in re.finditer(r'_sbGet\("supplier_configs","([^"]*)"', index_html):
        assert m.group(1).startswith("select=") or m.group(1) == "order=name.asc", m.group(0)
    assert index_html.count('_sbGet("supplier_configs","order=name.asc")') == 1  # nur der 400-Rueckfall


# ── statisch: SQL-Entwurf ───────────────────────────────────────────────────
def _sql_roh():
    with open(SQL, encoding="utf-8") as f:
        return f.read()


def _sql_code():
    return "\n".join(z for z in _sql_roh().splitlines() if not z.lstrip().startswith("--"))


def test_supplier_sql_kopf_und_rotation():
    roh = _sql_roh()
    assert roh.splitlines()[0].strip() == "-- IDEMPOTENT"
    assert "ROTIERT" in roh and "5 Kennwoerter" in roh
    assert "can_see_supplier_creds()" in roh and "service_role" in roh


def test_supplier_sql_rls_nur_admin_und_anon_gesperrt():
    c = _sql_code()
    assert "ALTER TABLE public.supplier_credentials ENABLE ROW LEVEL SECURITY;" in c
    pol = re.search(r"CREATE POLICY supplier_credentials_nur_admin ON public\.supplier_credentials\s+FOR ALL TO authenticated\s+"
                    r"USING \(public\.auth_role\(\) = 'admin'\)\s+WITH CHECK \(public\.auth_role\(\) = 'admin'\);", c)
    assert pol
    assert len(re.findall(r"CREATE POLICY", c)) == 1
    assert "REVOKE ALL ON TABLE public.supplier_credentials FROM anon;" in c
    assert "REVOKE ALL ON TABLE public.supplier_credentials FROM authenticated;" in c
    grant_sel = re.search(r"GRANT SELECT \(([^)]*)\) ON public\.supplier_credentials TO authenticated;", c)
    assert grant_sel and "password" not in grant_sel.group(1).replace("has_password", "")
    assert not re.search(r"GRANT\s+(SELECT|ALL)\s+ON\s+(TABLE\s+)?public\.supplier_credentials\s+TO\s+(anon|authenticated)", c)
    assert "supplier_id  uuid PRIMARY KEY" in c and "REFERENCES" not in c


KOPIE = "INSERT INTO public.supplier_credentials (supplier_id, username, password)"
LEEREN = "UPDATE public.supplier_configs SET username = NULL, password = NULL"


def _reihenfolge_ok(c):
    try:
        i_vor = c.index("Vorpruefung: supplier_configs.id ist")
        i_kopie = c.index(KOPIE)
        i_konf = c.index("ON CONFLICT (supplier_id) DO NOTHING;", i_kopie)
        i_abgl = c.index("Abgleich:")
        i_leer = c.index(LEEREN)
        i_riegel = c.index("supplier_configs_kein_klartext CHECK (username IS NULL AND password IS NULL)")
    except ValueError:
        return False
    return i_vor < i_kopie < i_konf < i_abgl < i_leer < i_riegel


def test_supplier_sql_reihenfolge_kopie_abgleich_leeren():
    c = _sql_code()
    assert _reihenfolge_ok(c)
    assert not re.search(r"DROP\s+COLUMN", c, re.I), "Spalten bleiben (alte Apps/Function schreiben sie noch)"
    assert len(re.findall(r"RAISE EXCEPTION 'Vorpruefung", c)) >= 4
    assert c.count("BEGIN;") == 1 and c.count("COMMIT;") == 1
    assert "Nachpruefung" in c


def test_supplier_sql_umkehrprobe_reihenfolge():
    """Leeren VOR der Kopie (oder ohne Abgleich) muss die Pruefung erkennen."""
    c = _sql_code()
    vertauscht = c.replace(KOPIE, "@@K@@", 1).replace(LEEREN, KOPIE, 1).replace("@@K@@", LEEREN, 1)
    assert vertauscht != c and not _reihenfolge_ok(vertauscht)
    assert not _reihenfolge_ok(c.replace("Abgleich:", "", 1))


def test_supplier_sql_umleitung_und_probe():
    c = _sql_code()
    assert "CREATE TRIGGER trg_supplier_zugang_umleiten BEFORE INSERT OR UPDATE ON public.supplier_configs" in c
    assert "NEW.username := NULL;" in c and "NEW.password := NULL;" in c
    assert "public.auth_role() = 'admin'" in c.split("_supplier_zugang_umleiten()")[1]
    roh = _sql_roh()
    probe = roh[roh.index("-- PROBE"):]
    assert "-- BEGIN;" in probe and probe.rstrip().endswith("-- ROLLBACK;")
    for rolle in ("'monteur'", "'buero'", "'admin'"):
        assert rolle in probe
    assert "SET LOCAL ROLE anon" in probe and "count(password)" in probe
