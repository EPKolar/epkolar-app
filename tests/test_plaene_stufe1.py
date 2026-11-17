# -*- coding: utf-8 -*-
"""Plaene Stufe 1 - "Plan zuerst". Je Punkt ein Riegel MIT Umkehrprobe.

Jeder Riegel ist eine Pruef-Funktion, die eine Liste von Befunden liefert.
Der echte Code muss leer herauskommen; ein gezielt zurueckgebauter Text muss
mindestens einen Befund liefern - sonst waere der Riegel blind (gruen, auch
wenn die Sache wieder kaputt ist).

  1 Plan zuerst      Kopfzeile statt Leisten, Plan fuellt die gemessene Hoehe
  2 Langer Tipp      setzt ein Ticket; Pinch/Bewegung brechen ab; Knopf bleibt
  3 EIN Blatt        Pin-Tipp oeffnet genau ein Blatt; Schreibwege unveraendert
  4 Statusfarben     CI-konform, unterscheidbar, kein Markengruen, "!" ueberfaellig
  5 Ikonen/Groessen  keine Emoji-Knoepfe, kein Orange, Schrift >= 12 im Plan-Bereich
  6 Erstellt-Datum   ISO-Zeitstempel ergibt kein "Invalid Date"
"""
import hashlib
import json
import re

import pytest

from conftest import run_node_snippet


def _fn(src, name):
    """Rumpf einer Top-Level-Funktion bis zur naechsten Top-Level-Deklaration."""
    a = src.index("function " + name + "(")
    m = re.compile(r"\r?\n(?:function |const |// |/\*)").search(src, a + 10)
    return src[a:m.start() if m else len(src)]


def _vplan(src):
    a = src.index("function VPlan(")
    return src[a:src.index("// ═══════════ OFFA EXPORT", a)]


def _planbereich(src):
    """TicketDetail .. VPlan-Ende: der ganze Plan-Bereich (Detail, Liste, Pin, Viewer, Blatt, VPlan)."""
    a = src.index("function TicketDetail(")
    return src[a:src.index("// ═══════════ OFFA EXPORT", a)]


def _ohne_kommentare(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


# ── 1 Plan zuerst ──────────────────────────────────────────────────────────
def pruef_plan_zuerst(src):
    v = _vplan(src)
    b = []
    if "isMob?t.k:t.l" in v or '{id:"viewer",i:"' in v:
        b.append("Unterreiter-Leiste steht wieder ueber dem Plan")
    if "'aria-label': \"Plan / Geschoss wählen\"" not in v:
        b.append("keine Geschoss-Auswahl in der Kopfzeile")
    if "'aria-label': \"Menü: Ebenen, Planverwaltung, Hochladen, Export, Bericht\"" not in v:
        b.append("kein Menue fuer Ebenen/Planverwaltung/Hochladen/Export/Bericht")
    if 'hoehe: _planH?_planH+"px":"70vh"' not in v:
        b.append("Plan bekommt die gemessene Hoehe nicht")
    if "--epk-bar-h" not in v or "_unten-_oben-_res" not in v:
        b.append("Hoehenmessung zieht die Fussleiste nicht ab")
    if 'height: hoehe || "82vh"' not in _fn(src, "PlanViewerCanvas"):
        b.append("PlanViewerCanvas nimmt die Hoehe nicht an")
    if 'React.createElement(\'div\', { style: {display:"flex",gap:6,marginBottom:10,flexWrap:"wrap",alignItems:"center",padding:"6px 8px"' in v:
        b.append("Geschoss-Pillen + Ebenen-Chips stehen wieder ueber dem Plan")
    return b


def test_plan_zuerst(index_html):
    assert pruef_plan_zuerst(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('hoehe: _planH?_planH+"px":"70vh", ', ""),
    ("'aria-label': \"Plan / Geschoss wählen\"", "'aria-label': \"x\""),
    ("_unten-_oben-_res", "_unten-_oben"),
])
def test_plan_zuerst_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_plan_zuerst(index_html.replace(alt, neu)), "Riegel blind fuer: " + alt


# ── 2 Langer Tipp ──────────────────────────────────────────────────────────
def pruef_langer_tipp(src):
    pv = _fn(src, "PlanViewerCanvas")
    v = _vplan(src)
    b = []
    if "if(onPlanLongPress && !pinMode){" not in pv or "}, 500);" not in pv:
        b.append("kein 500-ms-Zeitgeber beim Aufsetzen")
    if "_lpAbbruch();\r\n      setIsPanning(false);" not in pv and "_lpAbbruch();\n      setIsPanning(false);" not in pv:
        b.append("zweiter Finger (Pinch) bricht den langen Tipp nicht ab")
    if "Math.hypot(e.clientX - lp.x, e.clientY - lp.y) > 8) _lpAbbruch();" not in pv:
        b.append("Bewegung (Pan) bricht den langen Tipp nicht ab")
    if "!_lpFired && _wasSingle" not in pv:
        b.append("Loslassen nach langem Tipp zaehlt als Doppeltipp")
    if "onPlanLongPress: _pinPerLangTipp" not in v or "const _pinPerLangTipp=(pos)=>{if(newTicket||!selPlan||!selPlan.id)return;_neuesTicketAn(pos);};" not in v:
        b.append("VPlan verdrahtet den langen Tipp nicht")
    if '"Lange tippen = neues Ticket hier"' not in v:
        b.append("Hinweis auf den langen Tipp fehlt")
    if 'placing?"Abbrechen":"Ticket platzieren"' not in v or "const handlePlanClick=(pos)=>{if(!placing)return;_neuesTicketAn(pos);};" not in v:
        b.append("der bisherige Knopf-Weg ist weg")
    return b


def test_langer_tipp(index_html):
    assert pruef_langer_tipp(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("Math.hypot(e.clientX - lp.x, e.clientY - lp.y) > 8) _lpAbbruch();", "false) _lpAbbruch();"),
    ("!_lpFired && _wasSingle", "_wasSingle"),
    ("onPlanLongPress: _pinPerLangTipp", "onPlanLongPressX: _pinPerLangTipp"),
])
def test_langer_tipp_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_langer_tipp(index_html.replace(alt, neu)), "Riegel blind fuer: " + alt


def test_langer_tipp_rechnet_auf_den_plan(index_html, node_exe):
    """Die Position kommt aus derselben reinen Rechnung wie der Knopf-Tipp (_planPctAusKlick)."""
    js = _fn(index_html, "_planPctAusKlick") + (
        "\nprocess.stdout.write(JSON.stringify([_planPctAusKlick(150,100,{left:100,top:50,width:200,height:100}),"
        "_planPctAusKlick(10,10,{left:100,top:50,width:0,height:100})]));")
    a, b = json.loads(run_node_snippet(node_exe, js))
    assert a == {"x": 25, "y": 50} and b is None


# ── 3 EIN Blatt ────────────────────────────────────────────────────────────
# Fingerabdruck der Schreibwege (gemessen an v3.9.1020; Plaene Stufe 3 aendert createTicket/updateTicket bewusst:
# Fotos -> Storage, PUT nur geaenderte Felder - neu gemessen an feature/plaene-stufe3)
SCHREIBWEGE_MD5 = {
    "createTicket": "951a7a90b9c5d572ba94821aa1d525a1",
    "updateTicket": "14605d6bb657baab3592a962708e36db",
}


def _schreibweg(src, a, b):
    i = src.index("const " + a + "=")
    return src[i:src.index("const " + b + "=", i)].replace("\r\n", "\n")


def pruef_ein_blatt(src):
    v = _vplan(src)
    q = _fn(src, "QuickEditPin")
    b = []
    if "isMob&&selTicket&&subView===\"viewer\"&&(" in v:
        b.append("am Handy oeffnet selTicket wieder das Detail-Blatt (zweite Ebene)")
    if "isMob&&selTicket&&sideMode===\"detail\"&&!quickTicket&&!quickDefect&&subView===\"viewer\"" not in v:
        b.append("ganzes Ticket nicht nur auf ausdrueckliches 'Ganzes Ticket'")
    if "if(t&&t._isDefectPin){setQuickTicket(null);}else{setQuickDefect(null);}" not in v:
        b.append("Pin-Tipp schliesst das andere Blatt nicht")
    if "React.createElement(TkKlickSchild, null)" not in q:
        b.append("kein Schutz gegen den Geister-Klick nach dem Pin-Tipp")
    if "_react.useEffect.call(void 0, () => { if(_sp) _save(); }, [_sp]);" not in q:
        b.append("Status speichert nicht sofort")
    if "onClick:()=>_setz(setSt, k, st)" not in q:
        b.append("Status-Knoepfe fehlen")
    if '"💾 Speichern"' in q or "React.createElement('select', {value:st" in q:
        b.append("altes Schnellfenster (Status-Liste + Speichern) ist zurueck")
    if "onSave: u=>{updateTicket(u);}" not in v:
        b.append("Blatt speichert nicht ueber updateTicket")
    if 'hideJournal ? "Im Mängel-Reiter bearbeiten" : "Ganzes Ticket"' not in q:
        b.append("'Ganzes Ticket' fehlt")
    for name, (a, z) in {"createTicket": ("createTicket", "updateTicket"), "updateTicket": ("updateTicket", "deleteTicket")}.items():
        if hashlib.md5(_schreibweg(src, a, z).encode("utf-8")).hexdigest() != SCHREIBWEGE_MD5[name]:
            b.append("Schreibweg %s veraendert" % name)
    return b


def test_ein_blatt(index_html):
    assert pruef_ein_blatt(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("isMob&&selTicket&&sideMode===\"detail\"&&!quickTicket&&!quickDefect&&subView===\"viewer\"", "isMob&&selTicket&&subView===\"viewer\"&&("),
    ("React.createElement(TkKlickSchild, null),", ""),
    ("method:\"PUT\",body:_tkNurGeaendert(", "method:\"PATCH\",body:_tkNurGeaendert("),
])
def test_ein_blatt_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_ein_blatt(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 4 Statusfarben ─────────────────────────────────────────────────────────
def _status(src):
    m = re.search(r"const TICKET_STATUS=(\{.*?\}\});", src)
    roh = re.sub(r"([{,])([A-Za-z_]+):", r'\1"\2":', m.group(1))
    return json.loads(roh)


def _lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def pruef_statusfarben(src):
    st = _status(src)
    b = []
    farben = [v["c"].lower() for v in st.values()]
    if any(not re.match(r"^#[0-9a-f]{6}$", f) for f in farben):
        b.append("Statusfarbe ist kein fester Hexwert (PDF liest .c)")
        return b
    if "#009640" in farben:
        b.append("Markengruen #009640 als Statusfarbe")
    if len(set(farben)) != len(farben):
        b.append("zwei Status mit derselben Farbe")
    for k, v in st.items():
        kontrast = 1.05 / (_lum(v["c"]) + 0.05)
        if kontrast < 4.5:
            b.append("weisse Pin-Ziffer auf %s nur %.2f:1" % (k, kontrast))
    p = _fn(src, "PlanCanvasPinMarker")
    if "const _ueb = _tkUeberfaellig(ticket);" not in p or "background:UI.fehler" not in p:
        b.append("Pin zeigt 'ueberfaellig' nicht als rotes Abzeichen")
    if 'background:_open>0?"#009640"' in _fn(src, "PlanViewerCanvas"):
        b.append("Cluster wieder als gruener Kreis")
    if "_tkPunkt(k, 10)" not in _fn(src, "PlanViewerCanvas"):
        b.append("Legende nutzt nicht denselben Punkt wie Liste/Blatt")
    return b


def test_statusfarben(index_html):
    assert pruef_statusfarben(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ('offen:{l:"Offen",c:"#B4530A"', 'offen:{l:"Offen",c:"#009640"'),
    ('erledigt:{l:"Erledigt",c:"#15803D"', 'erledigt:{l:"Erledigt",c:"#B4530A"'),
    ('storniert:{l:"Storniert",c:"#6B7280"', 'storniert:{l:"Storniert",c:"#9CA3AF"'),
])
def test_statusfarben_umkehrprobe(index_html, alt, neu):
    assert alt in index_html
    assert pruef_statusfarben(index_html.replace(alt, neu)), "Riegel blind fuer: " + alt


# ── 5 Ikonen, kein Orange, Schrift ─────────────────────────────────────────
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿]")


def pruef_ikonen(src):
    t = _ohne_kommentare(_planbereich(src))
    b = []
    # Knopf, dessen erstes Kind ein String mit Emoji ist
    for m in re.finditer(r"createElement\('button',\s*\{", t):
        tiefe, i = 0, m.end() - 1
        while i < len(t):
            if t[i] == "{":
                tiefe += 1
            elif t[i] == "}":
                tiefe -= 1
                if tiefe == 0:
                    break
            i += 1
        rest = t[i + 1:i + 200].lstrip(" ,")
        mk = re.match(r'"([^"]*)"', rest)
        if mk and EMOJI.search(mk.group(1)):
            b.append("Emoji-Knopf: " + mk.group(1))
    if "rgba(249,115,22" in t:
        b.append("oranger Schatten/Rahmen im Plan-Bereich")
    for m in re.finditer(r"fontSize\s*:\s*(\d+)\b", t):
        if int(m.group(1)) < 12:
            b.append("Schrift %s px" % m.group(1))
    return b


def test_ikonen_kein_orange_schrift(index_html):
    assert pruef_ikonen(index_html) == []


@pytest.mark.parametrize("alt,neu", [
    ("_ik(\"kreuz\", 20))", "\"✕\")"),
    ('background:"rgba(0,150,64,.12)"', 'background:"rgba(249,115,22,.15)"'),
    ("fontSize:UI.fMeta, fontWeight:900, lineHeight:1", "fontSize:9, fontWeight:900, lineHeight:1"),
])
def test_ikonen_umkehrprobe(index_html, alt, neu):
    assert alt in index_html, alt
    assert pruef_ikonen(index_html.replace(alt, neu, 1)), "Riegel blind fuer: " + alt


# ── 6 Erstellt-Datum ───────────────────────────────────────────────────────
def test_erstellt_datum_iso(index_html, node_exe):
    td = _fn(index_html, "TicketDetail")
    assert 'fdt(String(ticket.createdAt||"").slice(0,10))' in td
    assert "fdt(ticket.createdAt)" not in td, "ungeschnittener Zeitstempel an fdt"
    zeile = re.search(r"const _fdtC=\{\};const fdt=d=>\{.*?\};", index_html).group(0)
    js = zeile + ('\nprocess.stdout.write(JSON.stringify([fdt(String("2026-10-01T09:00:00Z").slice(0,10)),'
                  'fdt("2026-10-02T09:00:00Z")]));')
    geschnitten, roh = json.loads(run_node_snippet(node_exe, js))
    assert geschnitten != "Invalid Date" and "2026" in geschnitten
    # Umkehrprobe: ohne den Schnitt waere es "Invalid Date" - fdt selbst bleibt unangetastet (haengt an Berichten/OFFA)
    assert roh == "Invalid Date"
