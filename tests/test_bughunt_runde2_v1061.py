# -*- coding: utf-8 -*-
"""v1061 Bughunt Runde 2 - vier Code-Fehler, jeweils mit ECHTEM Code aus
index.html in node und Umkehrprobe (alte Logik -> Erwartung verletzt).

1. UrlaubsantragPanel.beantragen: undefined aus leerem RETURNING landete in
   der Liste, antraege.map(a=>a.id) stuerzte ab -> _uaNachAntrag.
2. FRegie.saveE: nr = saved.length+1 -> nach Loeschen doppelte Nummer
   -> _regieNaechsteNr (hoechste Nummer + 1).
3. FahrtenbuchPanel.load: ueberholte Antwort (alter Monat) ueberschrieb die
   neue -> _ladeWache.
4. UrlaubsantragPanel.entscheiden: 0 Zeilen (RLS) galten als "Genehmigt"
   -> _api.patchPruefen (nur dort; _api.patch bleibt unveraendert).
"""
import json

from conftest import _extract_fn, run_node_snippet


def _balanced(src, start):
    i = src.index("{", start)
    depth = 0
    while True:
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[start:i + 1]
        i += 1


def _segment(index_html, head, marker, laenge=40000):
    st = index_html.index(head)
    i = index_html.index(marker, st)
    assert i - st < laenge, (head, marker)
    return _balanced(index_html, i)


# ---------- 1 Urlaubsantrag: leeres RETURNING ----------

def _ua_js(index_html, updater):
    fn = _extract_fn(index_html, "_uaNachAntrag")
    assert fn
    return fn + "\n" + (
        "const prev=[{id:'a',worker_id:'w',status:'beantragt'}];\n"
        "const item={id:'n',worker_id:'w',status:'beantragt'};\n"
        "const U=" + updater + ";\n"
        "const out={};\n"
        "for(const [k,created] of [['leer',undefined],['ok',{id:'n',worker_id:'w',status:'beantragt',created_at:'x'}]]){\n"
        "  try{const l=U(prev,created,item);out[k]={ids:l.map(a=>a.id),offen:l.filter(a=>a&&a.status==='beantragt').length};}\n"
        "  catch(e){out[k]='crash';}\n"
        "}\n"
        "console.log(JSON.stringify(out));"
    )


def test_ua_leeres_returning_faellt_auf_gesendete_zeile(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _ua_js(index_html, "_uaNachAntrag")))
    assert out == {"leer": {"ids": ["n", "a"], "offen": 2},
                   "ok": {"ids": ["n", "a"], "offen": 2}}, out


def test_ua_umkehrprobe_alter_updater(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _ua_js(index_html, "(p,c)=>[c,...p]")))
    assert out["leer"] == "crash", out


def test_ua_panel_nutzt_helfer(index_html):
    seg = _segment(index_html, "function UrlaubsantragPanel(", "const beantragen=async()=>{")
    assert "setAntraege(prev=>_uaNachAntrag(prev,created,item));" in seg
    assert "[created,...prev]" not in seg


# ---------- 2 Regie-Nummer ----------

def test_regie_nr_nach_loeschen_eindeutig(node_exe, index_html):
    fn = _extract_fn(index_html, "_regieNaechsteNr")
    assert fn
    js = fn + "\n" + (
        "const nach=[{nr:'001'},{nr:'003'}];\n"  # 002 geloescht
        "const neu=_regieNaechsteNr(nach);\n"
        "const alt=String(nach.length+1).padStart(3,'0');\n"
        "console.log(JSON.stringify({neu,alt,kollNeu:nach.some(f=>f.nr===neu),kollAlt:nach.some(f=>f.nr===alt),"
        "leer:_regieNaechsteNr([]),undef:_regieNaechsteNr(undefined),"
        "gemischt:_regieNaechsteNr([{nr:'A1'},{},{nr:' 012 '},{nr:7}])}));"
    )
    out = json.loads(run_node_snippet(node_exe, js))
    assert out == {"neu": "004", "alt": "003", "kollNeu": False, "kollAlt": True,
                   "leer": "001", "undef": "001", "gemischt": "013"}, out


def test_regie_saveE_nutzt_helfer(index_html):
    seg = _segment(index_html, "function FRegie(", "const saveE=()=>{")
    assert "nr:_existingNr||d.nr||_regieNaechsteNr(saved)}" in seg
    assert "saved.length+1" not in seg


# ---------- 3 Fahrtenbuch: ueberholte Antwort ----------

def _fb_js(index_html, alt=False):
    seg = _segment(index_html, "function FahrtenbuchPanel(", "const load=async()=>{")
    if alt:
        seg = seg.replace("const _aktuell=_ladeWache(_ldSeq);", "").replace("&&_aktuell()", "")
        assert "_aktuell" not in seg
    wache = _extract_fn(index_html, "_ladeWache")
    assert wache
    ymd = ("const _ymd=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,\"0\")}"
           "-${String(d.getDate()).padStart(2,\"0\")}`;\n")
    return wache + "\n" + ymd + (
        "const window={_showToast(){}};const workerId='w1';let month='2026-10';\n"
        "const _mnt={current:true};const _ldSeq={current:0};const offen=[];\n"
        "const _api={get:(t,q)=>new Promise(r=>offen.push({q,r}))};\n"
        "let entries=null,loading=null;const setEntries=v=>{entries=v;};const setLoading=v=>{loading=v;};\n"
        + "const load=" + seg[len("const load="):] + ";\n"
        "(async()=>{\n"
        "  const p1=load();month='2026-11';const p2=load();\n"
        "  offen[1].r([{id:'nov'}]);await p2;\n"
        "  offen[0].r([{id:'okt'}]);await p1;\n"
        "  console.log(JSON.stringify({ids:entries.map(e=>e.id),loading,q0:offen[0].q.indexOf('2026-10-01')>0,q1:offen[1].q.indexOf('2026-11-01')>0}));\n"
        "})();"
    )


def test_fb_alte_antwort_ueberschreibt_nicht(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _fb_js(index_html)))
    assert out == {"ids": ["nov"], "loading": False, "q0": True, "q1": True}, out


def test_fb_umkehrprobe_ohne_wache(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _fb_js(index_html, alt=True)))
    assert out["ids"] == ["okt"], out


# ---------- 4 Urlaubsantrag entscheiden: 0 Zeilen ----------

def _api_js(index_html, zeilen):
    api = _balanced(index_html, index_html.index("const _api={"))
    return (
        "const window={_ensureAuth:async()=>{},_haptic:{success(){}},_showToast:(m,t)=>toasts.push(t+':'+m)};\n"
        "const toasts=[];const SUPABASE_URL='https://x';const _authRetry=f=>f();const _fT=o=>o;\n"
        "const _sbWH=()=>({});const _sbH=()=>({});const _netzLesen=f=>f();const _netzLeseMs=()=>1;\n"
        "const fetch=async()=>({ok:true,status:200,json:async()=>" + zeilen + ",text:async()=>''});\n"
        + api + ";\n"
    )


def _entscheiden_js(index_html, zeilen, alt=False):
    seg = _segment(index_html, "function UrlaubsantragPanel(", "const entscheiden=async(id,status)=>{")
    if alt:
        seg = seg.replace("_api.patchPruefen(", "_api.patch(")
    return _api_js(index_html, zeilen) + (
        "const curUser={name:'Chef'};const users=[];const antraege=[];let gesetzt=0;\n"
        "const setAntraege=()=>{gesetzt++;};const prompt=()=>'';const _uuid=()=>'u';const _nWort=n=>String(n);\n"
        "const _materialisiereAbsence=async()=>({fehl:0});\n"
        "const entscheiden=" + seg[len("const entscheiden="):] + ";\n"
        "(async()=>{await entscheiden('a1','genehmigt');console.log(JSON.stringify({toasts,gesetzt}));})();"
    )


def test_entscheiden_null_zeilen_ist_fehler(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _entscheiden_js(index_html, "[]")))
    assert out["gesetzt"] == 0, out
    assert len(out["toasts"]) == 1 and out["toasts"][0].startswith("error:Fehler: PATCH urlaubsantraege"), out


def test_entscheiden_mit_zeile_ok(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _entscheiden_js(index_html, "[{id:'a1',status:'genehmigt'}]")))
    assert out["gesetzt"] == 1 and out["toasts"] == ["success:✅ Genehmigt"], out


def test_entscheiden_umkehrprobe_alter_patch(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _entscheiden_js(index_html, "[]", alt=True)))
    # alte Logik: 0 Zeilen geaendert und trotzdem "Genehmigt"
    assert out["gesetzt"] == 1 and out["toasts"] == ["success:✅ Genehmigt"], out


def test_api_patch_semantik_unveraendert(node_exe, index_html):
    js = _api_js(index_html, "[]") + (
        "(async()=>{const p=await _api.patch('t','1',{a:1});const d=await _api.delete('t','1');"
        "let pp='ok';try{await _api.patchPruefen('t','1',{a:1});}catch(e){pp='throw';}"
        "console.log(JSON.stringify({p:p===undefined,d,pp}));})();"
    )
    out = json.loads(run_node_snippet(node_exe, js))
    assert out == {"p": True, "d": True, "pp": "throw"}, out
