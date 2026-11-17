# -*- coding: utf-8 -*-
"""v3.9.1033 (Zweig fix/ui-audit) - Nacharbeit aus dem automatischen UI-Audit vom 17.11.

Das Audit hat die ECHTE App lokal (Offline-Sitzung, synthetische Daten, alle
Schreibzugriffe abgefangen) in 390 px hell, 390 px dunkel und 1200 px hell
vermessen. Die Riegel halten je behobener KATEGORIE die Eigenschaft fest, jeweils
mit Umkehrprobe (der Riegel muss den alten Zustand erkennen):

  1. Kontrast   - Statusfarben als SCHRIFT laufen ueber _lesbar() und erreichen
                  in beiden Themen >= 4,5:1 (in Node nachgerechnet, nicht nur
                  "kommt im Text vor"); Wochenende in Abwesenheiten nicht rot.
  2. Aktiv-Text - Markengruen als Schrift aktiver Reiter/Chips ist V.acTx,
                  nicht V.ac (V.ac #009640 als Schrift: 3,0-4,4:1 gemessen).
  3. Emoji      - die behobenen Stellen (Sync-/Server-Leiste, Buero-Portal,
                  Werkzeug-Status, Diagramm-Leerzustand, Flotte, Abwesenheiten)
                  zeigen kein Emoji mehr.
  4. Feldnamen  - Auswahlfelder der Arbeitsschein-Tabelle und die Filter in
                  Arbeitsscheine/Werkzeuge/Monatsabrechnung tragen aria-label.
"""
import json
import re
import subprocess

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")


def _lesbar_quelle(html):
    i = html.index("const _lesbarMerk={};")
    j = html.index("const _okG=", i)
    return html[i:j]


def _kontraste(node_exe, quelle, farben):
    js = r"""
let _dark=false;
%s
const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
const L=h=>{const n=parseInt(h.slice(1),16);return 0.2126*f((n>>16)&255)+0.7152*f((n>>8)&255)+0.0722*f(n&255);};
const K=(a,b)=>{const x=L(a),y=L(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
const out={};
for(const c of %s){
  _dark=false; const h=_lesbar(c); _dark=true; const d=_lesbar(c);
  out[c]={hell:K(h,"#ffffff"),hellChip:K(h,"#f2f4f2"),dunkel:K(d,"#1e2320"),roh:K(c,"#ffffff")};
}
process.stdout.write(JSON.stringify(out));
""" % (quelle, json.dumps(farben))
    p = subprocess.run([node_exe, "-e", js], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr[:800]
    return json.loads(p.stdout)


STATUSFARBEN = ["#eab308", "#84cc16", "#f97316", "#a3a3a3", "#3b82f6", "#22c55e", "#ef4444", "#8b5cf6", "#a855f7", "#009640", "#fb923c"]


def test_lesbar_erreicht_aa_in_beiden_themen(index_html, node_exe):
    k = _kontraste(node_exe, _lesbar_quelle(index_html), STATUSFARBEN)
    for c, w in k.items():
        assert w["hell"] >= 4.5 and w["hellChip"] >= 4.5, (c, w)
        assert w["dunkel"] >= 4.5, (c, w)


def test_umkehrprobe_rohe_statusfarben_waren_unter_aa(index_html, node_exe):
    """Ohne _lesbar faellt der Riegel: die rohen Farben liegen auf Weiss unter 4,5:1."""
    k = _kontraste(node_exe, _lesbar_quelle(index_html), ["#eab308", "#84cc16", "#f97316", "#3b82f6"])
    assert all(w["roh"] < 4.5 for w in k.values()), k
    # und eine "Hilfe", die nichts tut, wird erkannt
    kaputt = _lesbar_quelle(index_html).replace("for(let i=0;i<40&&", "for(let i=0;i<0&&", 1)
    k2 = _kontraste(node_exe, kaputt, ["#eab308"])
    assert k2["#eab308"]["hell"] < 4.5


KONTRAST_STELLEN = [
    'background:st.c+"22",color:_lesbar(st.c),fontWeight:700}}, _asPkt(st.c), st.l)',
    "color:_lesbar((AS_PRIO[a.prioritaet]&&AS_PRIO[a.prioritaet].c)||V.dm),fontWeight:700}}, \"● \"",
    # Touch-UI-Rest (17.11.2026) VERSCHAERFT: Badge-Schrift steht auf ihrem EIGENEN getoenten Chip und nimmt das
    # Chip-Ziel von _lesbar (Werkzeuge 'Ausgegeben' gemessen 4,48:1). Riegel: tests/test_touch_ui_rest_v1037.py.
    'background:bg||color+"18",color:bg?color:_lesbar(color,!0),whiteSpace',
    "return{icon:'→',color:_lesbar('#71717a')};",
    "color:_lesbar(bad?'#ef4444':'#22c55e')};};",
    'color:_lesbar(it.color),padding:"2px 6px",borderRadius:4,background:it.color+"15"',
    'fontWeight:800,color:_lesbar(v.c),fontFamily:mono}}, cnt)',
    'color:i<=val?_lesbar("#eab308"):V.mt}}',
    'color:_lesbar(c.ok?"#22c55e":"#eab308")}}, c.v)',
    'color:h>0?V.tx:V.mt',
]


def test_statusschrift_laeuft_ueber_lesbar(index_html):
    fehlt = [s for s in KONTRAST_STELLEN if s not in index_html]
    assert not fehlt, fehlt
    assert 'color:we?"#ef4444":V.mt' not in index_html, "Wochenende in Abwesenheiten wieder rot (Rot nur fuer Gefahr)"
    assert 'color:diff<=0?"#f97316":"#8b5cf6"' not in index_html, "Violett als Termin-Zierfarbe zurueck"


def test_umkehrprobe_rohe_statusschrift_wird_erkannt(index_html):
    kaputt = index_html.replace('color:_lesbar(st.c),fontWeight:700}}, _asPkt(st.c)', 'color:st.c,fontWeight:700}}, _asPkt(st.c)', 1)
    assert kaputt != index_html
    assert [s for s in KONTRAST_STELLEN if s not in kaputt]


AC_TEXT = re.compile(r"[,{]color:([A-Za-z_!][A-Za-z0-9_.=!\"'()&|]*)\?V\.ac:")


def _ac_als_schrift(html):
    return [m.group(0) for m in AC_TEXT.finditer(html) if m.group(1) != "_n"]


def test_aktiver_text_ist_actx(index_html):
    t = _ac_als_schrift(index_html)
    assert not t, "Markengruen V.ac als Schrift (zu wenig Kontrast): %r" % t[:8]
    assert "color:_n?V.ac:V.tx" in index_html  # bewusst stehen gelassen (Riegel v906)


def test_umkehrprobe_ac_als_schrift_wird_erkannt(index_html):
    kaputt = index_html.replace(",color:tab===t.id?V.acTx:V.dm", ",color:tab===t.id?V.ac:V.dm", 1)
    assert kaputt != index_html
    assert _ac_als_schrift(kaputt)


def _teil(html, a, laenge):
    i = html.index(a)
    return html[i:i + laenge]


EMOJI_STELLEN = [
    # (Anfang, Laenge) - kurze Fenster um die behobenen Stellen
    ("if(online&&!(pendingCount>0)&&!syncing&&failedCount===0)return null;", 2600),
    ("(!syncStatus.connected||!syncStatus.serverOk)&&React.createElement('div', { style: {position:\"absolute\",top:-24", 900),
    ("React.createElement('span', { style: {display:\"inline-flex\"}}, _ik(!syncStatus.connected?", 300),
    ('"Bauwochenberichte")', 400),
    ('"Daten werden geladen..." )', 60),
    ("'Urlaubs-/Abwesenheitsanträge')", 60),
    ("'Fahrtenbuch')", 40),
    ("_ik('standort',24))", 40),
    ("_ik(\"diagramm\",32))", 60),
    ("\"Server-Ordnerstruktur\" )", 40),
    ("\"Dateinamen-Konvention\" )", 40),
    ("_ik(c.ok?\"abnahme\":\"warnung\",16))", 60),
]


# Schliessen-Kreuz ist ein Schriftzeichen (kein Bildzeichen) und ueberall im Bestand
ZEICHEN_OK = {"✕", "✓"}


def _emojis_in(html):
    raus = {}
    for a, n in EMOJI_STELLEN:
        t = _teil(html, a, n)
        t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        t = re.sub(r"__toast\([^)]*\)|_toast\([^)]*\)", "", t)
        e = [z for z in EMOJI.findall(t) if z not in ZEICHEN_OK]
        if e:
            raus[a[:40]] = e
    return raus


def test_behobene_stellen_ohne_emoji(index_html):
    assert not _emojis_in(index_html)
    # Werkzeug-Status: das Abzeichen zeigt nur noch die Bezeichnung
    assert "_sti => _sti.i" not in index_html and "_815 => _815.i" not in index_html and "_797 => _797.i" not in index_html
    # Buero-Portal: keine Ablage-Emojis mehr als Knopfschrift
    esc = chr(92) + "ud83d" + chr(92) + "udce5 "
    assert index_html.count(esc + "Excel") == 0 and index_html.count(esc + "Alle als Excel") == 0
    assert index_html.count('_ikVw("tabelle","Excel")') >= 4


def test_umkehrprobe_emoji_in_sync_leiste_wird_erkannt(index_html):
    kaputt = index_html.replace('minHeight:32}}, _zpIk("drehen","Jetzt sync",14))', 'minHeight:32}}, "\U0001F504 Jetzt sync")', 1)
    assert kaputt != index_html
    assert _emojis_in(kaputt)


# Elementkoepfe bleiben byte-gleich (Riegel v918/v1007/v906 zielen darauf); der Name steht vor dem style-Schluessel.
KOEPFE = [
    "React.createElement('input', { className: \"epk-ruhig\", type: \"date\", value: (_hasTermin(a.terminVorschlag)",
    "React.createElement('input', { type: \"date\", value: (_hasTermin(a.terminBestaetigt)",
    "React.createElement('select', { className: \"epk-ruhig\", value: a.scheinstatus||\"aufgenommen\"",
    "React.createElement('select', { className: \"epk-ruhig\", value: a.prioritaet||\"keine\", onChange:",
    "isAdmin?React.createElement('select', { className: \"epk-ruhig\", value: a.sachbearbeiter||\"\", onChange:",
] + ["React.createElement('select', { value: %s, onChange:" % v for v in
     ("filterStatus", "filterArt", "filterMonteur", "filterSB", "filtSt", "filtKat", "sortCol", "wzServiceSel", "assignTo", "selMA", "selMonat", "selJahr")]


def _namenlose(html):
    raus = []
    for k in KOEPFE:
        pos = 0
        assert k in html, k
        while True:
            i = html.find(k, pos)
            if i < 0:
                break
            j = html.find(", style:", i)
            q = j + len(", style:")
            if html[q:q + 1] == " " and html[q + 1:q + 2] == "{":
                tiefe, q = 0, q + 1
                while True:
                    if html[q] == "{":
                        tiefe += 1
                    elif html[q] == "}":
                        tiefe -= 1
                        if tiefe == 0:
                            break
                    q += 1
            else:
                q = html.find(")", q)
            ende = html.find("}", q + 1)
            elem = html[i:ende + 1]
            if "'aria-label'" not in elem and "title:" not in elem:
                raus.append(k[:80])
            pos = i + len(k)
    return raus


def test_felder_tragen_namen(index_html):
    assert not _namenlose(index_html)


def test_umkehrprobe_namenloses_feld_wird_erkannt(index_html):
    kaputt = index_html.replace(", 'aria-label': \"Nach Kategorie filtern\"", "", 1)
    assert kaputt != index_html
    assert _namenlose(kaputt) == ["React.createElement('select', { value: filtKat, onChange:"]
