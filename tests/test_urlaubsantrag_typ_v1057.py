# -*- coding: utf-8 -*-
"""v1057 Bughunt: Urlaubsantrag -> absences.

1. Die Antrags-Arten 'pflege'/'sonder' gibt es in AT_T nicht. Beim Genehmigen
   wurde die Art 1:1 als absences.type geschrieben -> Kalender (AT_T[ab.type])
   zeigte den Tag leer, Zaehler (AT_T[t].kat) ignorierten ihn.
2. _materialisiereAbsence schluckte jeden Fehlschlag; der Genehmiger sah nur
   "Genehmigt", auch wenn kein einziger Tag in absences ankam.

Beide Tests fuehren den ECHTEN Code aus index.html in node aus und haben eine
Umkehrprobe (alte Logik -> Erwartung verletzt).
"""
import json
import re

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


def _at_t(index_html):
    st = index_html.index("const AT_T={")
    return "const COLORS={ERROR:'#dc2626'};\n" + _balanced(index_html, st) + ";\n"


def _antrag_optionen(index_html):
    st = index_html.index("function UrlaubsantragPanel(")
    seg = index_html[st:st + 40000]
    m = re.search(r"\[\['urlaub','Urlaub'\](?:,\['[a-z_]+','[^']+'\])+\]", seg)
    assert m, "Antrags-Arten-Liste im UrlaubsantragPanel nicht gefunden"
    return re.findall(r"\['([a-z_]+)','", m.group(0))


def _helper(index_html):
    m = re.search(r"var _ANTRAG_ABS_TYP=\{[^}]*\};", index_html)
    assert m, "_ANTRAG_ABS_TYP fehlt"
    fn = _extract_fn(index_html, "_antragAbsTyp")
    assert fn, "_antragAbsTyp fehlt"
    return m.group(0) + "\n" + fn + "\n"


def test_jede_antragsart_landet_auf_gueltigem_at_t_typ(node_exe, index_html):
    arten = _antrag_optionen(index_html)
    assert "pflege" in arten and "urlaub" in arten
    js = _at_t(index_html) + _helper(index_html) + (
        "const arten=%s;const out={};arten.forEach(a=>{const t=_antragAbsTyp(a);"
        "out[a]={t:t,ok:!!AT_T[t]};});console.log(JSON.stringify(out));" % json.dumps(arten)
    )
    out = json.loads(run_node_snippet(node_exe, js))
    for art, r in out.items():
        assert r["ok"], "Antrags-Art %r -> %r ist kein AT_T-Typ (Tag waere im Kalender unsichtbar)" % (art, r["t"])
    assert out["pflege"]["t"] == "pflegefrei"
    assert out["urlaub"]["t"] == "urlaub"
    assert out["krankenstand"]["t"] == "krankenstand"
    assert out["zeitausgleich"]["t"] == "zeitausgleich"

    # Umkehrprobe: alte Logik (type = ant.art) -> mindestens eine Art ist kein AT_T-Typ
    js_alt = _at_t(index_html) + (
        "const arten=%s;console.log(JSON.stringify(arten.filter(a=>!AT_T[a])));" % json.dumps(arten)
    )
    fehlend = json.loads(run_node_snippet(node_exe, js_alt))
    assert "pflege" in fehlend, "Umkehrprobe: alte Identitaets-Abbildung muesste 'pflege' verlieren"


def _materialisiere_src(index_html):
    st = index_html.index("const _materialisiereAbsence=async(ant)=>{")
    body = _balanced(index_html, st)
    return body + ";\n"


def _harness(index_html, mat_src):
    ymd = re.search(r"const _ymd=d=>`[^`]*`;", index_html).group(0)
    return (
        _at_t(index_html) + _helper(index_html) + ymd + "\nconst dk=_ymd;\n"
        "const _stdVonTagBrk=(d)=>{const w=d.getDay();if(w===0||w===6)return 0;return w<=4?8.5:4.5;};\n"
        "const monteure=[{id:'m1',n:'Huber'}];const curUser={name:'Chef'};\n"
        "const posts=[];\n"
        "const _api={get:async()=>[],post:async(t,b)=>{posts.push(b);"
        "if(b.from_date==='2026-11-17')throw new Error('POST absences 409: duplicate key 23505');"
        "if(b.from_date==='2026-11-18')throw new Error('Failed to fetch');return b;}};\n"
        + mat_src +
        "(async()=>{const r=await _materialisiereAbsence({worker_id:'m1',von:'2026-11-16',bis:'2026-11-20',art:'pflege',kommentar:''});"
        "console.log(JSON.stringify({r:r,types:posts.map(p=>p.type)}));})();"
    )


def test_materialisierung_meldet_fehlschlag_und_schreibt_gueltigen_typ(node_exe, index_html):
    out = json.loads(run_node_snippet(node_exe, _harness(index_html, _materialisiere_src(index_html))))
    # Mo 16. bis Fr 20.11.2026 = 5 Werktage; 17. existiert schon (409), 18. scheitert
    assert out["r"] == {"neu": 3, "vorhanden": 1, "fehl": 1}, out
    assert set(out["types"]) == {"pflegefrei"}, out


def test_umkehrprobe_alte_schluckende_fassung(node_exe, index_html):
    src = _materialisiere_src(index_html)
    alt = src.replace("_erg.fehl++;console.warn('[urlaub-brk-insert]'", "console.warn('[urlaub-brk-insert]'")
    alt = alt.replace("type:_typ,", "type:ant.art,")
    assert alt != src
    out = json.loads(run_node_snippet(node_exe, _harness(index_html, alt)))
    assert out["r"]["fehl"] == 0 and "pflege" in out["types"], "Umkehrprobe muss den alten Fehler zeigen"


def test_entscheiden_meldet_fehlschlag(index_html):
    st = index_html.index("const entscheiden=async(id,status)=>{")
    seg = index_html[st:st + 3000]
    assert "const _me=await _materialisiereAbsence(ant);if(_me&&_me.fehl>0)" in seg
