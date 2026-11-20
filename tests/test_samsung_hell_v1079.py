# -*- coding: utf-8 -*-
"""v3.9.1079 Samsung-Hell 3 + Versionsanzeige (A55-Runde 19.11.).

P1: App-Wahl "Hell" (epk_theme=light, data-epk-thema=hell, Hintergrund 242,244,242), Handy im
Nachtmodus, App als Samsung-Internet-Web-App -> die Seite erscheint DUNKEL (Samsungs Zwangs-Dunkel).
Bisher: v1006-v1023 Meta statisch "light dark" + per Skript auf only light/only dark; v1024-v1078 Meta
statisch "light dark", nur die Wurzel only light/only dark. Beides am A55 ohne Wirkung.

Jetzt: das Meta steht schon im HTML auf "only light" (Grundwahl Hell, gilt ab dem ersten Zeichnen,
vor jedem Skript - Chromium: das Meta "only light" schaltet das Auto-Dunkel ganz ab). Das Kopfskript
und applyTheme ziehen Meta und Wurzel auf die App-Wahl:
  Hell   -> Meta "only light", Wurzel "only light", data-epk-thema="hell"
  Dunkel -> Meta "dark",       Wurzel "only dark",  data-epk-thema="dunkel"
Die Geraete-Einstellung wird nie gelesen. Eingabefelder tragen "only light"/"only dark" (sonst darf
Chromiums Zwangs-Dunkel sie trotz heller Wurzel umfaerben: Blink ComputedStyleBuilder::SetUsedColorScheme).
Die Wirkung am A55 ist hier NICHT belegt - nur am Geraet pruefbar.

P3: Die Home-Fusszeile zeigte "v3.9.1076-supabase". Angezeigt wird jetzt _verAnzeige(APP_VERSION)
(ohne "-supabase"); APP_VERSION selbst bleibt unveraendert (SW_VER/CACHE_NAME/Update-Erkennung).
"""
import json
import re
import subprocess

import pytest

from _hilfen import nur_code

META_HELL = '<meta name="color-scheme" content="only light">'


def _kopf_skript(src):
    i = src.find('<meta name="color-scheme"')
    j = src.find("<script>", i) + len("<script>")
    return src[j:src.find("</script>", j)]


def _node(node_exe, tmp_path, js, name="probe.js"):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    out = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


# Falsches document: Meta-Objekt, Wurzel mit style + Attributen, localStorage nach Wunsch,
# matchMedia meldet IMMER Geraete-Dunkel (die App darf es nicht lesen).
_FAKE = r"""
function lauf(code, gespeichert, opts){
  opts=opts||{};
  var meta={c:"only light",setAttribute:function(k,v){if(k==="content")this.c=v;}};
  var at={};
  var document={
    querySelector:function(q){ if(opts.qsWirft) throw new Error("qs"); return q==="meta[name=color-scheme]"?meta:null; },
    documentElement:{style:{},setAttribute:function(k,v){at[k]=v;}}
  };
  var localStorage={getItem:function(k){ if(opts.lsWirft) throw new Error("ls"); return k==="epk_theme"?gespeichert:null; }};
  var window={matchMedia:function(){return {matches:true};}};
  var matchMedia=window.matchMedia;
  (new Function("document","localStorage","window","matchMedia",code))(document,localStorage,window,matchMedia);
  return [meta.c, document.documentElement.style.colorScheme||"", at["data-epk-thema"]||""];
}
"""

HELL = ["only light", "only light", "hell"]
DUNKEL = ["dark", "only dark", "dunkel"]


# ── 1. statisches Meta = Grundwahl Hell, vor jedem Skript ────────────────────

def test_meta_statisch_only_light_vor_jedem_skript(index_html):
    assert index_html.count(META_HELL) == 1
    assert index_html.index(META_HELL) < index_html.index("<script")
    assert '<meta name="color-scheme" content="light dark">' not in index_html
    assert index_html.count('<meta name="color-scheme"') == 1


def test_root_grundwert_only_light(index_html):
    css = index_html[:index_html.index("</style>")]
    assert re.search(r":root \{[^}]*color-scheme: only light;", css)
    assert not re.search(r":root \{[^}]*color-scheme: light dark;", css)


# ── 2. Kopfskript in Node: Hell / Dunkel / ohne Wahl ────────────────────────

@pytest.mark.parametrize("gespeichert,erwartet", [
    (None, HELL),          # ohne Wahl -> hell, obwohl matchMedia "dunkel" meldet
    ("light", HELL),       # der A55-Fall
    ("system", HELL),      # altes "Auto" -> hell
    ("quatsch", HELL),
    ("dark", DUNKEL),
])
def test_kopfskript_setzt_meta_und_wurzel(index_html, node_exe, tmp_path, gespeichert, erwartet):
    code = _kopf_skript(index_html)
    js = _FAKE + "console.log(JSON.stringify(lauf(%s,%s)));" % (json.dumps(code), json.dumps(gespeichert))
    assert _node(node_exe, tmp_path, js) == erwartet


def test_kopfskript_robust(index_html, node_exe, tmp_path):
    code = _kopf_skript(index_html)
    js = _FAKE + (
        "console.log(JSON.stringify([lauf(%s,'dark',{qsWirft:true}),lauf(%s,'dark',{lsWirft:true})]));"
        % (json.dumps(code), json.dumps(code)))
    qs_wirft, ls_wirft = _node(node_exe, tmp_path, js)
    # Meta-Fehler darf die Wurzel nicht verhindern
    assert qs_wirft == ["only light", "only dark", "dunkel"]
    # ohne lesbaren Speicher -> Grundwahl hell
    assert ls_wirft == HELL


def test_kopfskript_umkehrproben(index_html, node_exe, tmp_path):
    code = _kopf_skript(index_html)
    assert "prefers-color-scheme" not in code and "matchMedia" not in code
    assert "setItem" not in code
    # Umkehrprobe 1: ohne Meta-Schreiber (Stand v1024) bleibt das Meta bei Dunkel auf "only light"
    ohne = code.replace('m.setAttribute("content",mcs)', "0")
    assert ohne != code
    # Umkehrprobe 2: wuerde das Skript das Geraet lesen, kaeme bei "ohne Wahl" dunkel heraus
    geraet = code.replace('var d=(v==="dark");', 'var d=(v==="dark")||(v==null&&window.matchMedia("x").matches);')
    assert geraet != code
    js = _FAKE + "console.log(JSON.stringify([lauf(%s,'dark'),lauf(%s,null)]));" % (json.dumps(ohne), json.dumps(geraet))
    a, b = _node(node_exe, tmp_path, js)
    assert a == ["only light", "only dark", "dunkel"]   # Meta passt nicht zur Wahl -> erkannt
    assert b == DUNKEL                                   # Geraet gelesen -> erkannt


# ── 3. applyTheme zieht das Meta live mit ────────────────────────────────────

_THEMA_ANFANG = 'document.documentElement.style.colorScheme=dark?"only dark":"only light";'
_META_LIVE = 'try{var _csm=document.querySelector("meta[name=color-scheme]");if(_csm)_csm.setAttribute("content",dark?"dark":"only light");}catch(_e){}'


def _thema_stueck(src):
    i = src.index("function applyTheme(dark)")
    a = src.index(_THEMA_ANFANG, i)
    e = src.index(_META_LIVE, a) + len(_META_LIVE)
    assert e - a < 400
    return src[a:e]


def test_applytheme_meta_live(index_html, node_exe, tmp_path):
    stueck = _thema_stueck(index_html)
    js = _FAKE + r"""
function wechsel(code, dark, start){
  var meta={c:start,setAttribute:function(k,v){if(k==="content")this.c=v;}};var at={};
  var document={querySelector:function(){return meta;},documentElement:{style:{},setAttribute:function(k,v){at[k]=v;}}};
  (new Function("document","dark",code))(document,dark);
  return [meta.c,document.documentElement.style.colorScheme,at["data-epk-thema"]];
}
var c=%s, alt=c.replace(%s,"");
console.log(JSON.stringify([wechsel(c,true,"only light"),wechsel(c,false,"dark"),wechsel(alt,true,"only light")]));
""" % (json.dumps(stueck), json.dumps(_META_LIVE))
    zu_dunkel, zu_hell, alt = _node(node_exe, tmp_path, js)
    assert zu_dunkel == DUNKEL
    assert zu_hell == HELL
    # Umkehrprobe: ohne die Zeile (Stand v1024) bleibt das Meta beim Wechsel auf Dunkel "only light"
    assert alt == ["only light", "only dark", "dunkel"]


# ── 4. Eingabefelder mit only ────────────────────────────────────────────────

def test_eingabefelder_mit_only(index_html):
    code = nur_code(index_html)
    # Ausnahme mit Absicht: die Admin-Zuordnungsauswahl der Juprowa-Strecke bleibt unberuehrt
    # (Dauerregel: keine Aenderungen an OFFA/Juprowa) - genau eine Stelle ohne only.
    ohne_only = [m.start() for m in re.finditer(re.escape('colorScheme:_dark?"dark":"light"'), code)]
    assert len(ohne_only) == 1
    assert "_juprowaSetWorkerMap(" in code[ohne_only[0]:ohne_only[0] + 200]
    assert code.count('colorScheme:_dark?"only dark":"only light"') == 11
    assert "color-scheme:'+(typeof _dark!=='undefined'&&_dark?'only dark':'only light')" in code
    # kein color-scheme ohne only mehr im Code (ausser der Messhilfe, die genau das braucht)
    rest = code.replace("color-scheme:light;background-color:Canvas", "")
    assert not re.search(r"""colorScheme:\s*["']?(light|dark)["']""", rest)


# ── 5. Messhilfe fuer das Geraet ─────────────────────────────────────────────

def test_messhilfe_liest_nur(index_html):
    i = index_html.index("window.epkDunkelProbe=function(){")
    rumpf = index_html[i:index_html.index("\nconst APP_VERSION=", i)]
    assert "background-color:Canvas" in rumpf and "color-scheme:light" in rumpf
    assert "prefers-color-scheme" not in rumpf and "matchMedia" not in rumpf
    assert "localStorage" not in rumpf and "setAttribute" not in rumpf
    assert "e.remove()" in rumpf


# ── 6. P3 Versionsanzeige ohne -supabase ─────────────────────────────────────

def test_app_version_intern_unveraendert(app_version):
    assert re.fullmatch(r"\d+\.\d+\.\d+-supabase", app_version)


def test_verAnzeige_in_node(index_html, node_exe, tmp_path):
    m = re.search(r'function _verAnzeige\(v\)\{[^}]*\}', index_html)
    assert m
    js = m.group(0) + ';console.log(JSON.stringify([_verAnzeige("3.9.1076-supabase"),_verAnzeige("3.9.1076"),_verAnzeige(null),_verAnzeige("x-supabase-y")]));'
    assert _node(node_exe, tmp_path, js) == ["3.9.1076", "3.9.1076", "", "x-supabase-y"]


def test_anzeigen_nutzen_verAnzeige(index_html):
    code = nur_code(index_html)
    i = code.index('COMPANY_FOOTER.name+" · v"')
    assert "_verAnzeige(APP_VERSION)" in code[i:i + 120]
    for anker in ['"Version ", _verAnzeige(APP_VERSION)', '"Version: " , _verAnzeige(APP_VERSION)',
                  "'Version '+_verAnzeige(APP_VERSION)+' · '", "EP Kolar v'+_verAnzeige(APP_VERSION)+'",
                  '"v", _verAnzeige(APP_VERSION))']:
        assert anker in code, anker
    # Umkehrprobe: keine sichtbare Stelle zeigt APP_VERSION roh
    roh = re.findall(r'''(?:"v"|"Version "|"Version: "|" · v")\s*,\s*APP_VERSION\b(?!\.split)''', code)
    assert roh == []
    assert "'Version '+APP_VERSION" not in code and "v'+APP_VERSION+'" not in code
    alt = code.replace("_verAnzeige(APP_VERSION), \" · \"", "APP_VERSION, \" · \"")
    assert re.findall(r'''" · v"\s*,\s*APP_VERSION\b''', alt)
