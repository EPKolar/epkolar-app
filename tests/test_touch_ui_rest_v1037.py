# -*- coding: utf-8 -*-
"""Touch-UI-Rest (17.11.2026, Zweig fix/touch-ui) - die offenen Punkte aus dem UI-Audit.

Jeder Riegel hat eine Umkehrprobe: er muss den alten Zustand erkennen.

  1. Tippziele  - Das Lenovo-Tablet ist ein TOUCH-Geraet mit 1200 px. Gemessen mit
                  emuliertem Touch (hasTouch, pointer:coarse): die Hausregel
                  `@media (pointer: coarse), (max-width: 768px)` deckt Knoepfe,
                  [role=button] und Haken bereits; offen waren 341 Tippziele, KEIN
                  Knopf darunter: 171 Auswahlfelder, 84 Datumsfelder, 84 tabIndex-
                  Zellen, 1 Suchfeld. Neu: ein Block NUR nach Zeigerart (pointer:
                  coarse, ohne Breite), damit der Desktop mit Maus dicht bleibt.
  2. Emoji      - Projektakte Maengel, Fotos, Bautagebuch, Dokumente zeigen keine
                  Bildzeichen mehr (Toasts, Excel-Titel und eine tote Variable sind
                  benannt ausgenommen).
  3. Namen      - Projekt- und Kundennamen in Listen/Karten brechen auf zwei Zeilen
                  um (_zweiZeilen) und tragen den vollen Namen im title.
  4. Kontrast   - Werkzeuge "Ausgegeben" (Badge auf eigenem Chip), Chef-Kennzahlen,
                  Planung rotes Kreuz, Admin "Kein Login", Fahrzeuge leerer Stern:
                  in Node nachgerechnet >= 4,5:1.
"""
import json
import re
import subprocess

# ── 1 Tippziele ────────────────────────────────────────────────────────────

HAUSREGEL = "@media (pointer: coarse), (max-width: 768px) {"
TOUCH = "@media (pointer: coarse) {"


def _block(html, kopf):
    i = html.find(kopf)
    if i < 0:
        return None
    tiefe, j = 0, i + len(kopf) - 1
    while j < len(html):
        if html[j] == "{":
            tiefe += 1
        elif html[j] == "}":
            tiefe -= 1
            if tiefe == 0:
                return html[i:j + 1]
        j += 1
    return None


def _regeln(block):
    """[(selektoren, deklarationen)] eines @media-Blocks, ohne Kommentare."""
    innen = re.sub(r"/\*.*?\*/", "", block[block.index("{") + 1:-1], flags=re.S)
    return [(m.group(1), m.group(2)) for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", innen)]


def _deckt(block, selektor, eigenschaft):
    for sel, dekl in _regeln(block):
        teile = [t.strip() for t in sel.split(",")]
        if selektor in teile and re.search(eigenschaft + r"\s*:\s*44px\s*!important", dekl):
            return True
    return False


SOLL_TOUCH = [
    ("select", "min-height"), ("select", "min-width"),
    ('input:not([type="checkbox"]):not([type="radio"]):not([type="hidden"]):not([type="file"])', "min-height"),
    ('[role="tab"]', "min-height"), ('[role="menuitem"]', "min-height"),
    ('[tabindex="0"]:not(textarea)', "min-height"),
]
SOLL_HAUS = [("button", "min-height"), ("button", "min-width"), ('[role="button"]', "min-height"),
             ('input[type="checkbox"]', "min-height"), ('input[type="radio"]', "min-height")]


def _touch_fehlt(html):
    raus = []
    haus, touch = _block(html, HAUSREGEL), _block(html, TOUCH)
    if not haus:
        return ["Hausregel fehlt"]
    if not touch:
        return ["Touch-Block fehlt"]
    raus += ["Haus: %s %s" % x for x in SOLL_HAUS if not _deckt(haus, *x)]
    raus += ["Touch: %s %s" % x for x in SOLL_TOUCH if not _deckt(touch, *x)]
    if "max-width" in touch or "min-width: 769" in touch:
        raus.append("Touch-Block haengt an der Breite")
    return raus


def test_touch_tippziele_44px_nach_zeigerart(index_html):
    assert not _touch_fehlt(index_html), _touch_fehlt(index_html)


def test_desktop_mit_maus_bleibt_dicht(index_html):
    """Die neuen Selektoren duerfen nirgends OHNE pointer:coarse auf 44 px gehen."""
    touch = _block(index_html, TOUCH)
    rest = index_html.replace(touch, "")
    assert "(pointer: fine)" not in rest or not re.search(r"@media \(pointer: fine\)[^{]*\{[^}]*select[^}]*min-height:\s*44px", rest)
    assert not re.search(r"\n\s*select\s*,\s*input:not\(\[type=\"checkbox\"\]\)", rest)


def test_umkehrprobe_tippziele(index_html):
    touch = _block(index_html, TOUCH)
    ohne_select = index_html.replace(touch, touch.replace("select, ", "", 2))
    assert any("select" in f for f in _touch_fehlt(ohne_select))
    nach_breite = index_html.replace(TOUCH, "@media (max-width: 1300px) {", 1)
    assert _touch_fehlt(nach_breite)
    haus = _block(index_html, HAUSREGEL)
    ohne_knopf = index_html.replace(haus, haus.replace("  button,\r\n", "", 1).replace("  button,\n", "", 1))
    assert ohne_knopf != index_html and _touch_fehlt(ohne_knopf)


# ── 2 Emoji in der Projektakte ─────────────────────────────────────────────

EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2300-\u23FF\u25B6\u25C0\u25BC\uFE0F]")
ZEICHEN_OK = {"✕", "✓"}
FENSTER = ["function VMang(", "function VFotos(", "function VDoku(", "function VBautag(", "const HKLSE_CHIPS=["]
# benannte Ausnahmen (Anweisung, in der das Literal steht):
#  - Toasts (__toast) und Push-Texte (__pushNotif): Hausregel, Toasts duerfen Emoji tragen
#  - genXls(: Titelzeile der Excel-Datei, keine Bildschirmanzeige
#  - const icon=: tote Variable in VMang (wird nie gelesen, siehe test_..._tote_variable)
AUSNAHME = ("__toast", "__pushNotif", "genXls(", "const icon=")


def _fenster(html, kopf):
    i = html.index(kopf)
    m = re.compile(r"\r?\n(function |const |let |var |/\*)").search(html, i + len(kopf))
    return html[i:m.start() if m else len(html)]


def _ohne_kommentare(t):
    """Blockkommentare durch Leerzeichen ersetzen - Zeichenketten werden uebersprungen.

    Ein reines re.sub(/\\*.*?\\*/) haelt `accept: "image/*"` fuer einen Kommentaranfang und
    blendet alles bis zum naechsten `*/` aus - genau so war die erste Fassung dieses Riegels
    an der Umkehrprobe in VFotos blind (gemessen, 17.11.)."""
    out, i, n = [], 0, len(t)
    while i < n:
        c = t[i]
        if c in "\"'`":
            j = i + 1
            while j < n and t[j] != c and t[j] != "\n":
                j += 2 if t[j] == "\\" else 1
            out.append(t[i:j + 1])
            i = j + 1
        elif t.startswith("/*", i):
            j = t.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", t[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _emoji_rest(html):
    raus = []
    for kopf in FENSTER:
        t = _ohne_kommentare(_fenster(html, kopf))
        for m in EMOJI.finditer(t):
            if m.group(0) in ZEICHEN_OK or m.group(0) == "\uFE0F":
                continue
            vor = t[:m.start()]
            anw = vor[max(vor.rfind(";"), vor.rfind("\n")) + 1:]
            if any(a in anw for a in AUSNAHME):
                continue
            raus.append((kopf, m.group(0), t[max(0, m.start() - 50):m.start() + 20]))
    return raus


def test_projektakte_ohne_sichtbare_emoji(index_html):
    rest = _emoji_rest(index_html)
    assert not rest, "\n".join("%s %r ... %s" % r for r in rest[:20])


def test_umkehrprobe_emoji(index_html):
    alt = '_ikVw("plus","Neuer Eintrag"))'
    assert alt in index_html
    assert _emoji_rest(index_html.replace(alt, '"\u2795 Neuer Eintrag")', 1))
    alt2 = '_ik("kamera",48)), filter==="alle"?'
    assert alt2 in index_html
    assert _emoji_rest(index_html.replace(alt2, '"\U0001F4F7"), filter==="alle"?', 1))


def test_ausnahmen_sind_echt(index_html):
    vm = _fenster(index_html, "function VMang(")
    assert len(re.findall(r"\bicon\b", re.sub(r"/\*.*?\*/", "", vm, flags=re.S))) == 1, "icon wird jetzt gelesen - dann ist es sichtbar"
    # DOC_CATS behaelt das Bildzeichen im Datensatz; JEDE Anzeige schneidet das erste Wort ab
    assert "c.l.split(\" \").slice(1).join(\" \")" in index_html
    assert "catInfo.l.split(\" \").slice(1).join(\" \")" in index_html
    assert not re.search(r"[,(]\s*c\.i\s*,", _fenster(index_html, "function VFotos("))


def test_neue_ikonen_haben_zeichnungen(index_html):
    for n in ("schloss", "monitor"):
        assert re.search(r"Object\.assign\(IKON,\{[^;]*\b%s:\[" % n, index_html), n
    namen = set(re.findall(r'_ik(?:Vw)?\("([a-z_]+)"', "".join(_fenster(index_html, k) for k in FENSTER)))
    alle = set(re.findall(r"[{,]([a-z_]+):\[\"M", index_html))
    assert namen and not (namen - alle), namen - alle


# ── 3 Namen auf zwei Zeilen ────────────────────────────────────────────────

NAMEN_STELLEN = [
    'title: pr.name, style: {fontSize:14,fontWeight:700,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen,flex:1}}, pr.name)',
    'title: pr.name, style: {fontSize:12,fontWeight:700,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}, pr.name)',
    'title: a.kundName||a.nummer, style: {fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}, a.kundName||a.nummer)',
    'title: p.name, style: {fontWeight:600,fontSize:UI.fTitel,color:UI.tinte,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}, p.name)',
    'title: (p.kunde||"—")+" · "+(p.ort||""), style: {fontSize:12,color:V.dm,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}',
    'title: p.name, style: {fontWeight:600,fontSize:UI.fTitelGross,color:UI.tinte,lineHeight:1.3,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}, p.name)',
    'title: [p.nr,p.kunde,p.ort].filter(Boolean).join(" \\u00b7 "), style: {color:UI.grau,fontSize:UI.fMeta,minWidth:0,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}',
    "title:(p.name||'')+(p.kunde?(' · '+p.kunde):''),style:{fontSize:UI.fMeta,color:V.dm,maxWidth:isMob?150:280,overflow:'hidden',textOverflow:'ellipsis',..._zweiZeilen}}",
    "title:(p.nr?p.nr+' · ':'')+(p.name||'—'),style:{fontSize:13,fontWeight:700,marginBottom:8,overflow:'hidden',textOverflow:'ellipsis',..._zweiZeilen}}",
    'title: it.text, style: {fontSize:12,fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",..._zweiZeilen}}, it.text)',
]


def _namen_fehlen(html):
    raus = [s[:60] for s in NAMEN_STELLEN if s not in html]
    m = re.search(r"const _zweiZeilen=\{([^}]*)\}", html)
    if not m or "WebkitLineClamp:2" not in m.group(1) or 'whiteSpace:"normal"' not in m.group(1):
        raus.append("_zweiZeilen")
    return raus


def test_namen_brechen_zweizeilig_mit_title(index_html):
    assert not _namen_fehlen(index_html), _namen_fehlen(index_html)


def test_umkehrprobe_namen(index_html):
    kaputt = index_html.replace("WebkitLineClamp:2", "WebkitLineClamp:1", 1)
    assert _namen_fehlen(kaputt)
    kaputt2 = index_html.replace('textOverflow:"ellipsis",..._zweiZeilen,flex:1}}, pr.name)', 'textOverflow:"ellipsis",whiteSpace:"nowrap",flex:1}}, pr.name)', 1)
    assert kaputt2 != index_html and _namen_fehlen(kaputt2)


# ── 4 Kontrast ─────────────────────────────────────────────────────────────

KONTRAST_STELLEN = [
    'color:bg?color:_lesbar(color,!0),whiteSpace:"nowrap"}}, text)',            # Badge (Werkzeuge "Ausgegeben")
    "color:col?_lesbar(col):V.tx,fontFamily:mono}},(val===null||val===undefined)?'…':val)",  # Chef-Kennzahlen
    'color:_lesbar(COLORS.ERROR),padding:"0 2px"}}, "✕")',                     # Planung: Zeile verwerfen
    'width:24,height:24,color:_lesbar(COLORS.ERROR)}, title: "Zeile löschen"}, "✕")',
    'style:{..._mbS(_lesbar(COLORS.ERROR)),marginLeft:14},title:"Zeile löschen"}',   # Planung am Handy
    'style: {color:_lesbar("#b45309"),fontWeight:600}}, "Kein Login")',
    'color:_lesbar("#b45309"),display:"flex",alignItems:"center",gap:6}}, "Mitarbeiter ohne Login ("',
    'color:isFav(f.id)?"#eab308":_lesbar("#555555"),',
    'color:isFav(sel)?"#eab308":_lesbar("#555555")}',
]


def _lesbar_quelle(html):
    i = html.index("const _lesbarMerk={};")
    return html[i:html.index("const _okG=", i)]


def _rechne(node_exe, quelle, faelle):
    js = r"""
let _dark=false;
%s
const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);};
const rgb=h=>{const n=parseInt(h.slice(1),16);return[(n>>16)&255,(n>>8)&255,n&255];};
const L=c=>0.2126*f(c[0])+0.7152*f(c[1])+0.0722*f(c[2]);
const K=(a,b)=>{const x=L(a),y=L(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05);};
const auf=(fg,a,bg)=>fg.map((v,k)=>v*a+bg[k]*(1-a));
const out=[];
for(const [farbe,dunkel,chip,grund,alpha] of %s){
  _dark=dunkel; const t=_lesbar(farbe,chip);
  const g=alpha?auf(rgb(farbe),alpha,rgb(grund)):rgb(grund);
  out.push(K(rgb(t),g));
}
process.stdout.write(JSON.stringify(out));
""" % (quelle, json.dumps(faelle))
    p = subprocess.run([node_exe, "-e", js], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr[:800]
    return json.loads(p.stdout)


A18 = 0x18 / 255.0
# (Farbe, dunkel, chip, Grund, Alpha der Chipflaeche) - Gruende wie im Audit gemessen
FAELLE = [
    ("#f97316", False, True, "#f2f4f2", A18), ("#f97316", False, True, "#ffffff", A18),   # Badge hell (gemessen #f3e8dd)
    ("#f97316", True, True, "#1e2320", A18), ("#f97316", True, True, "#121513", A18),     # Badge dunkel
    ("#22c55e", False, True, "#f2f4f2", A18), ("#eab308", False, True, "#f2f4f2", A18),
    ("#ef4444", False, True, "#f2f4f2", A18), ("#3b82f6", False, True, "#f2f4f2", A18),
    ("#f97316", False, False, "#ffffff", 0), ("#ef4444", False, False, "#ffffff", 0),     # Chef-Kennzahlen hell
    ("#3b82f6", False, False, "#ffffff", 0), ("#ef4444", True, False, "#1e2320", 0),
    ("#ef4444", False, False, "#fbfbfb", 0),                                                # Planung Kreuz
    ("#b45309", True, False, "#1e2320", 0), ("#b45309", True, False, "#121513", 0),       # Admin dunkel
    ("#b45309", False, False, "#ffffff", 0),
    ("#555555", True, False, "#1e2320", 0), ("#555555", False, False, "#ffffff", 0),      # Stern
]


def test_kontrast_stellen_laufen_ueber_lesbar(index_html):
    fehlt = [s for s in KONTRAST_STELLEN if s not in index_html]
    assert not fehlt, fehlt


def test_kontrast_nachgerechnet(index_html, node_exe):
    k = _rechne(node_exe, _lesbar_quelle(index_html), FAELLE)
    zu = [(f[0], "dunkel" if f[1] else "hell", f[3], round(v, 2)) for f, v in zip(FAELLE, k) if v < 4.5]
    assert not zu, zu


def test_umkehrprobe_kontrast(index_html, node_exe):
    # ohne Chip-Ziel lag "Ausgegeben" bei 4,48:1 - der Riegel muss das sehen
    q = _lesbar_quelle(index_html)
    ohne_chip = q.replace("(chip?0.125:0.145)", "0.145").replace("(chip?0.36:0.33)", "0.33")
    assert ohne_chip != q
    k = _rechne(node_exe, ohne_chip, [FAELLE[0]])
    assert k[0] < 4.5, k
    # rohe Farben (vorher) lagen darunter
    roh = _rechne(node_exe, "function _lesbar(h){return h;}", [("#555555", True, False, "#1e2320", 0), ("#b45309", True, False, "#1e2320", 0), ("#f97316", False, False, "#ffffff", 0)])
    assert all(v < 4.5 for v in roh), roh
    kaputt = index_html.replace('style: {color:_lesbar("#b45309"),fontWeight:600}}, "Kein Login")', 'style: {color:"#b45309",fontWeight:600}}, "Kein Login")', 1)
    assert [s for s in KONTRAST_STELLEN if s not in kaputt]
