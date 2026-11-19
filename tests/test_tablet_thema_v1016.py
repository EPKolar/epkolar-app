# -*- coding: utf-8 -*-
"""v3.9.1016 Tablet-Test (Lenovo 1200x1920, Chrome-WebAPK) + GF-Entscheidung Thema.

GF: "app muss die hell dunkel einstellung ignorieren, es zaehlt was in der app
gewaehlt wurde" und "das design muss professionell sein und nicht verspielt".

Riegel je Auftrag, jeweils mit Umkehrprobe (ein eingesetzter Rueckfall wird
erkannt). Gemessen am Schirm: scratchpad/v1016/vor_* und nach_* (1200 und 800 px).
"""
import re
import shutil
import subprocess

SAMSUNG_REGEL = '@media (prefers-color-scheme: dark) { :root[data-epk-thema="hell"] { color-scheme: only light; background-color: #F2F4F2; } :root[data-epk-thema="hell"] body { background-color: #F2F4F2; } }'

import pytest

from _hilfen import nur_code

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.find("\nfunction ", i + 10)
    return src[i:j]


def _kopf_skript(src):
    j = src.find("<script>", src.find('<meta name="color-scheme"')) + len("<script>")
    return src[j:src.find("</script>", j)]


# ── 1. Thema: nur die App-Wahl zaehlt, die Deklaration bleibt ─────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
@pytest.mark.parametrize("gespeichert,os_dunkel,erwartet", [
    (None, True, "only light"),      # ohne Wahl hell - auch wenn das Geraet dunkel ist
    ("system", True, "only light"),  # altes "Auto" = hell
    ("light", True, "only light"),   # Wahl hell schlaegt Geraet dunkel (Samsung-A55-Fall)
    ("dark", False, "only dark"),    # Umkehrprobe: Wahl dunkel -> only dark
    ("dark", True, "only dark"),
])
def test_kopfskript_folgt_nur_der_app_wahl(index_html, gespeichert, os_dunkel, erwartet):
    js = (
        "var meta={c:'light dark',setAttribute:function(k,v){this.c=v;}};"
        "var document={querySelector:function(){return meta;},documentElement:{style:{}}};"
        "var localStorage={getItem:function(){return %s;}};"
        "var window={matchMedia:function(q){return {matches:%s};}};"
        % ("null" if gespeichert is None else "'%s'" % gespeichert, "true" if os_dunkel else "false")
        + _kopf_skript(index_html)
        + ";console.log(meta.c+'|'+document.documentElement.style.colorScheme);"
    )
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "light dark|" + erwartet  # v3.9.1024: Meta bleibt statisch


def test_deklaration_bleibt_gegen_zwangsabdunkelung(index_html):
    """Coordinator/GF: color-scheme-DEKLARATION bleibt (v1006 Samsung-Fix) - nur
    die AUSWAHL liest das Geraet nicht mehr."""
    assert '<meta name="color-scheme"' in index_html
    kopf = _kopf_skript(index_html)
    assert '"only dark":"only light"' in kopf and 'setAttribute("content",cs)' not in kopf  # v3.9.1024
    assert "documentElement.style.colorScheme=cs" in kopf
    i = index_html.index("function applyTheme(dark)")
    rumpf = index_html[i:i + 4000]
    assert 'document.documentElement.style.colorScheme=dark?"only dark":"only light"' in rumpf
    assert '_csm.setAttribute(' not in rumpf  # v3.9.1024: Meta bleibt statisch "light dark"


def test_kein_geraete_lauscher_mehr(index_html):
    # v3.9.1020: genau EINE statische CSS-Regel darf die Medienabfrage nennen - sie bestaetigt bei
    # Geraete-Dunkel nur die App-Wahl Hell (Samsung-Zwangsdunkel). Gelesen wird das Geraet nie.
    code = nur_code(index_html)
    assert code.count(SAMSUNG_REGEL) == 1
    code = code.replace(SAMSUNG_REGEL, "")
    assert "prefers-color-scheme" not in code
    assert "_systemDark" not in code
    assert '["system","Auto"]' not in code
    # Umkehrprobe
    assert "prefers-color-scheme" in nur_code(index_html + '\nvar q=matchMedia("(prefers-color-scheme: dark)");')


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_resolve_und_themode_rechnen_richtig(index_html):
    m = re.search(r"function resolveTheme\(stored\)\{.*?\n\}", index_html, re.S)
    t = re.search(r"function _themeMode\(\)\{[^\n]*\}\}", index_html)
    assert m and t
    js = (m.group(0) + ";" + t.group(0) + ";var _v=null;var localStorage={getItem:function(){return _v;}};"
          "var r=[resolveTheme(null),resolveTheme('system'),resolveTheme('light'),resolveTheme('dark')];"
          "_v='system';r.push(_themeMode());_v='dark';r.push(_themeMode());_v=null;r.push(_themeMode());"
          "console.log(JSON.stringify(r));")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == '[false,false,false,true,"light","dark","light"]'


def test_startwert_vor_dem_ersten_rendern_ist_hell(index_html):
    assert "let _dark=true;" not in nur_code(index_html)
    assert 'let _dark=(function(){try{return localStorage.getItem("epk_theme")==="dark";}' in index_html


def test_zwei_knoepfe_mehrmenue_und_einstellungen(index_html):
    assert index_html.count('[["light","Hell"],["dark","Dunkel"]].map(') == 2


# ── 2. Zeiterfassung: Wochenkarten ────────────────────────────────────────

def test_ze_knoepfe_44px_und_karten_am_tablet_dreispaltig(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    assert ze.count('minWidth:44,minHeight:44,padding:"2px 4px",borderRadius:6') == 2
    assert 'minWidth:24,minHeight:24' not in ze
    # Stufe 5 Zeiterfassung (19.11.2026): die eigene Grenze ww<1100 ist in die gemeinsame Stufe gewandert -
    # drei Spalten in "mittel" (Tablet hochkant), sechs in "breit" (tests/test_stufe_zeiterfassung_v1075.py).
    assert '(_zeMittel?"repeat(3,minmax(0,1fr))":"repeat(6,minmax(0,1fr))")' in ze
    assert 'whiteSpace:"nowrap"}},entry.von,"–",entry.bis)' in ze


def test_ze_loeschen_im_dialog_mit_rueckfrage(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    assert "editEntry&&_canDelEntry&&React.createElement('button'" in ze
    assert "if(await deleteEntry(addDay,_i)){setEditEntry(null);setAddDay(null);}" in ze
    # deleteEntry fragt weiter nach und meldet Erfolg
    i = ze.index("const deleteEntry=async(iso,entryIdx)=>{")
    rumpf = ze[i:i + 1200]
    assert '_confirmModal("Zeiteintrag "+_zeitEintragName(iso,entry.hours,entry.label)+" löschen?",{variant:"danger"})' in rumpf  # v1016: Dialog nennt den Eintrag
    assert "return true;" in rumpf


def test_ze_kopf_einzahl_esc_samstag(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    assert 'dateFmt(0)," – ",dateFmt(6)' in ze
    assert '_nWort(_nEintrZE,"Eintrag","Einträge")' in ze
    assert '_nEintrZE," Einträge · "' not in ze
    assert 'matchMedia("(pointer:fine)")' in ze
    assert "#7f1d1d" not in ze and "#1e293b,#334155" not in ze
    assert '"rgba(239,68,68,.04)"' not in ze


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_nwort_einzahl_mehrzahl(index_html):
    m = re.search(r"function _nWort\(n,ein,mehr\)\{[^\n]*?\}", index_html)
    js = m.group(0) + ";console.log([_nWort(1,'Eintrag','Einträge'),_nWort(4,'Eintrag','Einträge'),_nWort(0,'Eintrag','Einträge')].join('|'));"
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.stdout.strip() == "1 Eintrag|4 Einträge|0 Einträge"


# ── 3. Taetigkeit erfindet keinen Wert ────────────────────────────────────

RUECKFAELLE = [
    'addTaetigkeit.trim()||label',
    "setAddTaetigkeit(entry.taetigkeit||entry.label||'')",
    'taetigkeit:entry.taetigkeit||entry.label,gewerk:',
]


def test_taetigkeit_kein_rueckfall_auf_projektname(index_html):
    ze = nur_code(_fn(index_html, "ZeiterfassungView"))
    for r in RUECKFAELLE:
        assert r not in ze, "Rueckfall zurueck: %s" % r
    assert 'const taet=addType==="frei"?addFrei.trim():addTaetigkeit.trim();' in ze
    # Umkehrprobe
    kaputt = ze.replace('addTaetigkeit.trim();', 'addTaetigkeit.trim()||label;', 1)
    assert any(r in kaputt for r in RUECKFAELLE)


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_taetigkeit_speichern_im_lauf(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    m = re.search(r"const taet=(addType===\"frei\"\?addFrei\.trim\(\):addTaetigkeit\.trim\(\));", ze)
    e = re.search(r"setAddTaetigkeit\((\(entry\.type!=='frei'.*?)\);", ze)
    assert m and e
    js = ("var label='BVH Sparkasse Ravelsbach (PA242467)';var r=[];"
          "var addType='projekt',addFrei='',addTaetigkeit='  ';r.push(" + m.group(1) + ");"
          "addTaetigkeit='Montage';r.push(" + m.group(1) + ");"
          "addType='frei';addFrei='Lager';r.push(" + m.group(1) + ");"
          "var entry={type:'projekt',label:label,taetigkeit:label};r.push(" + e.group(1) + ");"
          "entry={type:'projekt',label:label,taetigkeit:''};r.push(" + e.group(1) + ");"
          "entry={type:'projekt',label:label,taetigkeit:'Montage'};r.push(" + e.group(1) + ");"
          "console.log(JSON.stringify(r));")
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == '["","Montage","Lager","","","Montage"]'


def test_anzeige_sagt_ohne_taetigkeit(index_html):
    assert '"ohne Tätigkeit")' in _fn(index_html, "ZeiterfassungView")
    assert '" · ohne Tätigkeit")' in _fn(index_html, "VDash")


# ── 4. Kopfzeile ──────────────────────────────────────────────────────────

def _kopf(src):
    i = src.index("/* Photo Queue */")
    j = src.index("/* ═══ NOTIFICATION PANEL ═══ */", i)
    return src[i:j]


def test_kopfzeile_linien_ikonen(index_html):
    k = nur_code(_kopf(index_html))
    for e in ("📷", "🔍", "🅰", "🔔", "👑", "🚪", "☀", "🌙"):
        assert e not in k, "Emoji in der Kopfzeile: %s" % e
    for ik in ('_ik("kamera",18)', '_ik("suche",18)', '_ik(isDark?"mond":"sonne",18)', '_ik("glocke",18)', '_ik("abmelden",16)'):
        assert ik in k
    assert "_kioskKnopf('gefahr')" in k
    assert 'if(await _confirmModal("Wirklich abmelden?",{variant:"danger"}))logout();' in k
    # Umkehrprobe
    assert EMOJI.search(k.replace('_ik("glocke",18)', '"\U0001F514"', 1))


def test_neue_ikonen_stehen_in_ikon_und_der_regelabstand_haelt(index_html):
    i = index_html.index("const IKON={")
    j = index_html.index("};function _ik(", i)
    rumpf = index_html[i:j]
    assert 'mond:["' in rumpf and 'glocke:["' in rumpf
    u = index_html.index("const UI={")
    # Kameras Phase 1 (v1055): 12000 -> 13000, IKON um videokamera gewachsen; die Regel steht unveraendert am Objekt.
    assert "NIE Statusampel" in index_html[u - 13000:u]


# ── 5. Home + Projekt-Uebersicht ──────────────────────────────────────────

HOME_WEG = ["🏗", "📋", "📅", "🏖", "📊", "⛽", "📐", "📄", "🔄", "⚙", "🍂", "🌅", "👑", "🟢", "🔴", "🟡", "⚪", "📦", "📝", "👥", "📈", "📉"]


def test_home_ohne_bedien_emoji(index_html):
    hv = nur_code(_fn(index_html, "HomeView"))
    rest = [e for e in HOME_WEG if e in hv]
    assert not rest, "Emoji auf Home: %r" % rest
    # P3-A55 (16.11., Auftrag: Wetter -> Linien-Ikonen): die Wetterleiste zeichnet
    # Linien-Ikonen aus IKON statt der WMO-Emoji; die Leiste selbst bleibt.
    # Vorher stand hier: assert "WMO[wcode]" in hv (Wetter-Emoji bleiben).
    assert "_ik(_wmoIk(wcode)" in hv
    kaputt = hv.replace('{i:"helm",l:"Neues Projekt"', '{i:"\U0001F3D7",l:"Neues Projekt"', 1)
    assert any(e in kaputt for e in HOME_WEG)


def test_projekt_uebersicht_ohne_emoji_und_ein_primaerknopf(index_html):
    vd = nur_code(_fn(index_html, "VDash"))
    assert not EMOJI.search(vd), EMOJI.findall(vd)
    assert vd.count("{...bpS,") == 1, "genau EIN primaerer Knopf"
    assert vd.count("{...bsS(),padding:\"8px 14px\"") == 4
    for alt in ("rgba(59,130,246,.12)", "rgba(239,68,68,.12)", "rgba(249,115,22,.12)"):
        assert alt not in vd, "Pastellknopf zurueck"
    assert "_307.c])||V.ac" not in vd, "Gewerkfarbe (Blau) am Punkt zurueck"
    assert EMOJI.search(vd + '"\U0001F4D0"')


# ── 6. Abwesenheiten ──────────────────────────────────────────────────────

def test_abwesenheit_typknoepfe_ikonen_und_markengruen(index_html):
    i = index_html.index('Object.entries(AT_T).filter(([k,v])=>v.kat==="urlaub"||v.kat==="krank"||v.kat==="za")')
    seg = index_html[i:i + 1400]
    assert '_ik(({urlaub:"sonne",krank:"fieber",za:"uhr"})[v.kat]' in seg
    assert "v.i, \" \" , v.l" not in seg
    assert 'border:typ===k?"2px solid "+UI.marke' in seg
    assert "'aria-pressed': typ===k" in seg
    assert 'rgba(99,102,241,.1)' not in index_html[i:i + 3000]


def test_abwesenheit_hinweis_neutral_und_antraege_ehrlich(index_html):
    assert '"Klicke auf die Tage für: "' not in index_html
    assert '"Tipp auf einen Tag trägt ein: "' in index_html
    assert '" (?)"' not in nur_code(index_html)
    assert '(pendingUnklar?" (mind. "+pendingGesamt+")":" ("+pendingGesamt+")")' in index_html


# ── 7. Arbeitsscheine-Tabelle: nur Darstellung ────────────────────────────

def test_as_tabelle_rollhinweis_ohne_spaltenaenderung(index_html):
    assert '"Tabelle ist breiter als der Bildschirm – seitlich wischen für weitere Spalten"' in index_html
    assert "className: \"epk-as-roll\", style: {overflowX:\"auto\"" in index_html
    # Pin nachgezogen (AS Liste mittel, GF 19.11.2026 nach 1065): die Tabelle traegt
    # am Tablet hochkant die Klasse epk-as-mittel (Koepfe ohne Umbruch, 44-px-Felder);
    # Spalten und Mindestbreite bleiben woertlich gleich.
    assert 'React.createElement(\'table\', { className: _asMittel?"epk-as-mittel":undefined, style: {width:"100%",borderCollapse:"collapse",minWidth:1300,fontSize:12}}' in index_html


# ── 9. Barrierefreiheit ───────────────────────────────────────────────────

def test_monteur_uebersicht_trenner_fuer_vorlesehilfe(index_html):
    ze = _fn(index_html, "ZeiterfassungView")
    i = ze.index("m.n,React.createElement('span',{style:{position:\"absolute\"")
    seg = ze[i:i + 300]
    assert 'clip:"rect(0 0 0 0)"' in seg and '", ")' in seg
    assert "m.n,React.createElement('span',{style:{fontSize:UI.fMeta,color:V.dm,fontWeight:400,marginLeft:6}},m.r)" not in ze
