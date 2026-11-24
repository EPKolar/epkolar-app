# -*- coding: utf-8 -*-
"""Stufe 5 Zeiterfassung (GF 19.11.2026, "EINE Oberflaeche, drei Breiten-Stufen").

Vorher: ZeiterfassungView kannte drei eigene Breitenabfragen - isMob=ww<BP_MOB,
ww<1100 (Wochenkarten drei- oder sechsspaltig) und im Buchungsdialog
window.innerWidth<BP_MOB (Bottom-Sheet). Die Monteur-Uebersicht (Admin, "Alle
Monteure") war in jeder Breite eine Tabelle mit fester Mindestbreite 700 -
am Handy nur per Querwischen lesbar, eine schmale Fassung fehlte.

Entscheidung Tabelle in "mittel", Karten nur in "schmal":
- Die Monteur-Uebersicht ist eine Matrix Mitarbeiter x Tag (Summe, Stunden,
  "fehlt", genehmigte Abwesenheit). Gelesen wird quer (wer fehlt an welchem Tag)
  und laengs (wer hat die Woche voll). Direkt-Aendern gibt es in der Zeile nicht -
  der Tipp auf die Zeile oeffnet die Woche des Mitarbeiters (Drill-down), dort wird
  gebucht und bearbeitet. Neun Spalten passen am Tablet hochkant (800 px) ohne
  feste Mindestbreite; die Namensspalte klebt links, nur der Tabellenkasten rollt,
  Koepfe brechen nicht um, Ziffern gleich breit. Owner-Regel (1070, AS-Liste):
  Arbeitslisten bleiben am Tablet hochkant Tabelle - dieselbe Lesart gilt hier.
- Am Handy (schmal) je Mitarbeiter eine Karte: Name, Wochensumme, sieben Tage
  als Raster; die ganze Karte ist ein echter Knopf mit demselben Drill-down.
- Die Buchungsansicht (Wochenkarten je Tag mit Bearbeiten/Loeschen/+ Eintrag)
  ist schon kartenfoermig: schmal eine Spalte, mittel drei, breit sechs - dieselben
  Knoepfe in jeder Stufe. Die Wochensumme bleibt kompakt (schmal: eine Zeile).

Was hier gesichert wird:
1. Stufe NUR ueber _layoutStufe - mit echtem Code fuer 384, 412, 800x1280,
   1280x800, 1920x1080 ausgefuehrt (Stufe, isMob, mittel, Kartenraster,
   Tabellen-Mindestbreite, klebende Spalte, Tabellenklasse, Uebersichtsform).
2. EIN Tabellenzweig fuer mittel und breit; dieselben Handlungen in der Buchungs-
   ansicht in mittel und breit. Die Stufe steuert dort nur Darstellung.
3. Abdeckung: keine eigene Breitenabfrage in ZeiterfassungView.
4. Rechnung/Rundung/Speichern/Freigabe unberuehrt: md5 je Block gegen v3.9.1074.
5. Trefferflaechen >= 44 px, Schrift >= 12, kein Querrollen in den Karten.
6. Handy-Karte zeigt je Tag dasselbe wie die Tabellenzelle (echter Code).
Jeder Riegel hat eine Umkehrprobe.
"""
import hashlib
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")

DEKL = ('const _zeStufe=_layoutStufe(ww,(typeof window!=="undefined"?window.innerHeight:0));'
        'const isMob=_zeStufe==="schmal";const _zeMittel=_zeStufe==="mittel";')
KLEB = 'const _zeKleb=(bg)=>_zeMittel?{position:"sticky",left:0,zIndex:1,background:bg}:{};'
RASTER = 'gridTemplateColumns:isMob?"1fr":(_zeMittel?"repeat(3,minmax(0,1fr))":"repeat(6,minmax(0,1fr))")'
TAB_KLASSE = 'className:"epk-ze-tab"+(_zeMittel?" epk-ze-mittel":"")'
TAB_MIN = "minWidth:_zeMittel?0:700"
KARTEN = "isMob&&React.createElement('div',{'data-ze-uebersicht':\"karten\""
TABELLE = "!isMob&&React.createElement('div',{'data-ze-uebersicht':_zeStufe,style:{overflowX:\"auto\"}},"
DRILL = "onClick:()=>{setSelWorker(m.id);setViewAll(false);}"


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _ze(src):
    a = src.index("function ZeiterfassungView(")
    return src[a:src.index("\nfunction _floorRank(", a)]


def _stufe_code(src):
    i = src.index("const BP_MOB=600;")
    mob = src[i:i + len("const BP_MOB=600;")]
    j = src.index("const BP_BREIT=")
    k = src.index("function _grobZeiger(", j)
    return mob + "\n" + src[j:k]


KLEBT = {"position": "sticky", "left": 0, "zIndex": 1, "background": "x"}
R3 = "repeat(3,minmax(0,1fr))"
R6 = "repeat(6,minmax(0,1fr))"
# (Breite, Hoehe) -> (Stufe, isMob, mittel, Raster, Mindestbreite, klebend, Klasse, Uebersicht)
FAELLE = [
    ([384, 832], ["schmal", True, False, "1fr", 700, {}, "epk-ze-tab", "karten"]),
    ([412, 915], ["schmal", True, False, "1fr", 700, {}, "epk-ze-tab", "karten"]),
    ([800, 1280], ["mittel", False, True, R3, 0, KLEBT, "epk-ze-tab epk-ze-mittel", "tabelle"]),
    ([1280, 800], ["breit", False, False, R6, 700, {}, "epk-ze-tab", "tabelle"]),
    ([1920, 1080], ["breit", False, False, R6, 700, {}, "epk-ze-tab", "tabelle"]),
]


def _entscheidung(node_exe, src, faelle):
    """Fuehrt die ECHTEN Ausdruecke aus ZeiterfassungView aus (nicht abgeschrieben)."""
    v = _ze(src)
    for x in (DEKL, KLEB, RASTER, TAB_KLASSE, TAB_MIN, KARTEN, TABELLE):
        assert v.count(x) == 1, x
    js = ("var window={innerWidth:0,innerHeight:0};\n" + _stufe_code(src) + "\n"
          "function f(ww,hh){window.innerWidth=ww;window.innerHeight=hh;" + DEKL + KLEB
          + "return [_zeStufe,isMob,_zeMittel," + RASTER[len("gridTemplateColumns:"):] + ","
          + TAB_MIN[len("minWidth:"):] + ",_zeKleb(\"x\")," + TAB_KLASSE[len("className:"):] + ","
          + "(isMob?\"karten\":\"tabelle\")];}\n"
          "process.stdout.write(JSON.stringify(" + json.dumps(faelle)
          + ".map(function(x){return f(x[0],x[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_entscheidung_fuer_fuenf_groessen(roh, node_exe):
    r = _entscheidung(node_exe, roh, [f for f, _ in FAELLE])
    assert r == [e for _, e in FAELLE], list(zip([f for f, _ in FAELLE], r))


def test_umkehr_breite_grenze_auf_handy_waere_rot(roh, node_exe):
    """Mit BP_BREIT=600 bekaeme das Tablet hochkant sechs Spalten und Mindestbreite 700."""
    kaputt = roh.replace("const BP_BREIT=1100;", "const BP_BREIT=600;", 1)
    assert kaputt != roh
    assert _entscheidung(node_exe, kaputt, [f for f, _ in FAELLE]) != [e for _, e in FAELLE]


def test_dieselbe_handy_grenze_wie_vorher(roh, node_exe):
    """schmal == alte isMob (ww<BP_MOB) und altes _im (innerWidth<BP_MOB)."""
    r = _entscheidung(node_exe, roh, [[599, 900], [600, 900]])
    assert [x[1] for x in r] == [True, False]
    v = _ze(roh)
    assert "const _im=isMob;" in v
    assert "window.innerWidth<BP_MOB" not in v


# ── Ein Tabellenzweig, dieselben Handlungen in mittel und breit ─────────────
def _uebersicht(v):
    i = v.index("Monteur-Übersicht KW ")
    return v[i:v.index("DAY-CENTRIC WEEK GRID", i)]


def _tabelle(v):
    u = _uebersicht(v)
    return u[u.index(TABELLE):]


def _woche(v):
    i = v.index("DAY-CENTRIC WEEK GRID")
    return v[i:v.index("/* No worker selected */", i)]


# Stufenabhaengig ist in Tabelle und Buchungsansicht NUR Darstellung:
NUR_DARSTELLUNG = [
    re.compile(re.escape(TABELLE)),
    re.compile(re.escape(TAB_KLASSE)),
    re.compile(re.escape(TAB_MIN)),
    re.compile(r"\.\.\._zeKleb\("),
    re.compile(re.escape(RASTER)),
    re.compile(r"gap:isMob\?8:6"),
    re.compile(r"minHeight:isMob\?0:200"),
    re.compile(r'gridTemplateColumns:isMob\?"1fr":"repeat\(6,1fr\) auto",gap:isMob\?0:6'),
    re.compile(r'padding:isMob\?"8px":"6px 6px"'),
    re.compile(r"padding:isMob\?\"10px 14px\":\"5px 12px\",fontSize:isMob\?14:12"),
    re.compile(r"minHeight:isMob\?44:0"),
]


def _stufen_reste(teil):
    for m in NUR_DARSTELLUNG:
        teil = m.sub("", teil)
    # isMob? als Wochensummen-Form (schmal eine Zeile) unterscheidet mittel und breit nicht
    teil = teil.replace("          isMob?\r\n            React.createElement('div',{style:{display:\"flex\",justifyContent:\"space-between\"", "", 1)
    return re.findall(r"_zeMittel|_zeStufe|isMob", teil)


HANDLUNGEN_WOCHE = [
    "_canEditEntry&&React.createElement('span',{onClick:()=>_startEditEntry(iso,entry)",
    "_canDelEntry&&React.createElement('span',{onClick:()=>deleteEntry(iso,eIdx)",
    "React.createElement('button',{onClick:()=>{setAddDay(iso);",
    "React.createElement('button',{onClick:exportWochenStz,",
    "React.createElement('button',{onClick:exportXls,",
    "onClick:()=>exportTagesStz(i)",
    "exportBauwochenbericht(bwbProjId);",
]


def test_ein_tabellenzweig_und_gleiche_handlungen(roh):
    v = _ze(roh)
    tab = _tabelle(v)
    assert DRILL in tab and "React.createElement('tfoot'" in tab
    assert _stufen_reste(tab) == [], "Stufe steuert in der Tabelle mehr als Darstellung"
    w = _woche(v)
    for h in HANDLUNGEN_WOCHE:
        assert h in w, h
    assert _stufen_reste(w) == [], "Stufe steuert in der Buchungsansicht mehr als Darstellung"
    # Karten und Tabelle oeffnen den Mitarbeiter auf demselben Weg
    assert _uebersicht(v).count(DRILL) == 2


def test_umkehr_handlung_nur_breit_waere_rot(roh):
    v = _ze(roh)
    w = _woche(v)
    kaputt = w.replace("_canDelEntry&&React.createElement('span',{onClick:()=>deleteEntry(iso,eIdx)",
                       "!_zeMittel&&_canDelEntry&&React.createElement('span',{onClick:()=>deleteEntry(iso,eIdx)", 1)
    assert kaputt != w and _stufen_reste(kaputt)
    tab = _tabelle(v)
    kaputt2 = tab.replace(DRILL, "onClick:()=>{if(_zeMittel)return;setSelWorker(m.id);setViewAll(false);}", 1)
    assert kaputt2 != tab and _stufen_reste(kaputt2)


def test_mittel_klebt_links_und_rollt_nur_im_kasten(roh):
    v = _ze(roh)
    tab = _tabelle(v)
    assert tab.startswith(TABELLE)  # nur dieser Kasten rollt quer
    assert tab.count("..._zeKleb(") == 3  # Kopf, Zeile, Summe
    assert '..._zeKleb("#009640")' in tab
    css = _css(roh)
    assert "table.epk-ze-mittel th { white-space: nowrap; }" in css
    assert "table.epk-ze-mittel thead th:first-child { z-index: 2 !important; }" in css
    assert "table.epk-ze-tab td { font-variant-numeric: tabular-nums; }" in css


# ── Abdeckung ───────────────────────────────────────────────────────────────
# Gepinnte gemeinsame Ausdruecke ohne Breitenvergleich, die bleiben:
#   matchMedia("(pointer:fine)") - Hinweis "Esc schliesst" nur mit Maus/Tastatur (Zeigerart,
#   keine Breite); gepinnt in test_tablet_thema_v1016 und test_v1016_bedienung.
ERLAUBT = ['window.matchMedia&&window.matchMedia("(pointer:fine)")']
BREITEN_MUSTER = re.compile(r"\bww\s*[<>]=?|innerWidth\s*[<>]=?|matchMedia|userAgent|navigator\.")


def _fremde_breiten(src):
    code = nur_code(_ze(src))
    for e in ERLAUBT:
        code = code.replace(e, "")
    return [code[max(0, m.start() - 50):m.end() + 30] for m in BREITEN_MUSTER.finditer(code)]


def test_abdeckung_keine_eigenen_breitenvergleiche(roh):
    funde = _fremde_breiten(roh)
    assert not funde, "Eigene Breitenvergleiche statt _layoutStufe:\n" + "\n".join(funde)
    assert nur_code(_ze(roh)).count(ERLAUBT[0]) == 1


def test_abdeckung_fragt_die_stufe(roh):
    v = _ze(roh)
    assert DEKL in v and "const isMob=ww<BP_MOB;" not in v
    assert "ww<1100" not in v
    # ww kommt nur noch als Argument an _layoutStufe vor
    assert re.findall(r"\bww\b", nur_code(v)) == ["ww", "ww"]  # Parameterliste + _layoutStufe(ww,


def test_umkehr_abdeckung_findet_neuen_vergleich(roh):
    kaputt = roh.replace(RASTER, RASTER.replace("_zeMittel?", "ww<1100?"), 1)
    assert kaputt != roh and _fremde_breiten(kaputt)
    kaputt2 = roh.replace("const _im=isMob;", 'const _im=(typeof window!=="undefined"&&window.innerWidth<BP_MOB);', 1)
    assert kaputt2 != roh and _fremde_breiten(kaputt2)
    kaputt3 = roh.replace(DEKL, DEKL + "const _ua=/Android/.test(navigator.userAgent);", 1)
    assert _fremde_breiten(kaputt3)


def _bloecke(s):
    aus = []
    for m in re.finditer(r"<script\b[^>]*>", s, re.I):
        e = s.find("</script>", m.end())
        aus.append((m.end(), e if e > 0 else len(s)))
    return aus


def test_stufe_steht_im_block_von_zeiterfassungview(roh):
    bl = _bloecke(roh)
    p1, p2 = roh.index("function _layoutStufe(w,h){"), roh.index("function ZeiterfassungView(")
    n1 = [n for n, (a, b) in enumerate(bl) if a <= p1 < b]
    n2 = [n for n, (a, b) in enumerate(bl) if a <= p2 < b]
    assert n1 and n2 and n1[0] == n2[0]


# ── Rechnung, Rundung, Speichern, Freigabe: unberuehrt ──────────────────────
# md5 je Block (CRLF -> LF), gemessen an v3.9.1074 (origin/main ed65d41) und nach dem Umbau gleich.
# Der erste Block umfasst ALLES vom Wiener Datum bis vor den Buchungsdialog: Laden, Uebersicht
# (Fehltage), Stunden aendern mit verzoegertem PUT (stzSaveTimers), Loeschen, Bearbeiten,
# Buchen (Doppel-Tap-Sperre, Konflikt-Rueckfrage), Wie-letzte-Woche, Tages-/Wochensumme, Exporte.
UNBERUEHRT = [
    ("  const _hkZE=", "  // ── Add Entry Modal ──", "e6031b91feb2453160f0a66492a652e2"),  # v3.9.1110 GF 24.11.: Vorbelegungen leer, Pflicht-/Rasterpruefung - vorher d32b44b2c6f3115f41c88160546b470b
    ("  const loadWeek=", "  _react.useEffect.call(void 0, ()=>{loadWeek();}", "b385eb03b69f774d0fda2c645009df8e"),
    ("  const loadAllOverview=()=>{", "  const updateEntryHours=", "cd30063a0ff0c90357bc549f4fca834d"),
    ("  const updateEntryHours=(iso,entryIdx,newHours)=>{", "  const _isFieldRoleZE=", "6269e5f3f81bbbab81a3fdc3c13afed1"),
    ("  const deleteEntry=async(iso,entryIdx)=>{", "  const _startEditEntry=", "4ab9e2c3c729e01e68f051d6a7f915ba"),
    ("  const _startEditEntry=", "  const _addEntryInFlightRef=", "ce43dcdf5ee5072f23343af4180b23bf"),  # v3.9.1110: Bearbeiten ohne erfundene Zeiten, Original fuer Pruefung - vorher 32eed371fbcd11f70f584e185ac4c977
    ("  const addEntry=async()=>{", "  const _wlwAbs=()=>{", "9413568ee09aace4c3027678aaf1b604"),  # v3.9.1110: Pflicht-/15-min-Pruefung, alte Stunden bleiben - vorher b9a3b2b4c452d71e2b1cdc83373372cb
    ("  const _wlwUebernehmen=async()=>{", "  const wlwModal=()=>{", "cb75e471a823b19d4e6686ccd223e3cc"),
    ("  const dayTotal=(off)=>", "  const _nEintrZE=", "699bc7098a09a1aaa54417c453451d78"),
    # Dialog: Von/Bis/Pause/Stunden mit 5-Min-Rundung (_zeitRundVon/_zeitRundBis) und Pausenabzug
    # v3.9.1093: Stundenfeld text statt number (ZahlEingabe, gelesen ueber _fzZahl) - bewusst neu gehasht.
    # Die Aenderung im Block ist GENAU diese Ersetzung: test_dialog_rueckbau_ergibt_alten_hash belegt es.
    ("React.createElement('label',{style:LL()},\"Von\"),", "\"Mittagspause: 12:00", "692eefd1afb392a77bdc07ce3ae18b49"),  # v3.9.1110: Uhrzeit step 900, Pause waehlen, Vorschau exakt - vorher ed4a6fa584c0ffbb9ad0d529ffb9e98a
    # Stunden-Anzeige auf der Karte (Leer-/Komma-Schutz, test_zeit_lohn_v885)
    ("React.createElement('input',{type:\"text\",readOnly:true,tabIndex:-1,\"aria-label\":\"Stunden, ändern über Bearbeiten\"",
     "React.createElement('span',{style:{fontSize:UI.fMeta,color:V.dm,fontWeight:600}},\"h\"))", "750998533ffe43f76063114a74f80250"),
    ("React.createElement('button',{onClick:addEntry,", "\n", "bca217b61befe7061dcaaa438dd77165"),
]


def _hashes(src):
    v = _ze(src).replace("\r\n", "\n")
    aus = []
    for a, b, _ in UNBERUEHRT:
        assert v.count(a) == 1, a
        i = v.index(a)
        j = v.index(b, i + len(a))
        aus.append(hashlib.md5(v[i:j].encode("utf-8")).hexdigest())
    return aus


def test_rechnung_und_speichern_byte_gleich(roh):
    assert _hashes(roh) == [h for _, _, h in UNBERUEHRT]


def test_dialog_rueckbau_ergibt_alten_hash(roh):
    """v3.9.1093: dreht man NUR die Feld-Umstellung zurueck, ist der Dialog-Block byte-gleich mit v3.9.1074."""
    rev = roh.replace("React.createElement(ZahlEingabe,{inputMode:\"decimal\",value:(_zeitEffektiveStunden(addVon,addBis,addPause)!=null?",
                      "React.createElement('input',{type:\"number\", inputMode:\"decimal\",step:\"0.5\",min:\"0\",max:\"24\",value:(_zeitEffektiveStunden(addVon,addBis,addPause)!=null?")
    rev = rev.replace("setAddHours(_fzZahl(e.target.value)||0)", "setAddHours(parseFloat(e.target.value)||0)")
    assert rev != roh
    assert _hashes(rev)[9] == "a3511b895cdc0d5594c95628de667e9f"  # v3.9.1110 Dialog bewusst geaendert (GF 24.11.) - vorher ceca4e0175d8265f7c94de699b306eac


def _im_ze(src, alt, neu):
    a = src.index("function ZeiterfassungView(")
    e = src.index("\nfunction _floorRank(", a)
    v = src[a:e]
    assert v.count(alt) == 1, alt
    return src[:a] + v.replace(alt, neu) + src[e:]


def test_umkehr_rundung_geaendert_waere_rot(roh):
    kaputt = _im_ze(roh, "const v=_zeitRundVon(e.target.value);", "const v=e.target.value;")
    assert kaputt != roh and _hashes(kaputt) != [h for _, _, h in UNBERUEHRT]
    i = roh.index("  const updateEntryHours=(iso,entryIdx,newHours)=>{")
    j = roh.index("  const _isFieldRoleZE=", i)
    blk = roh[i:j]
    m = re.search(r"\b800\b", blk)
    assert m, "verzoegerter PUT (800 ms) nicht gefunden"
    kaputt2 = roh[:i] + blk[:m.start()] + "1500" + blk[m.end():] + roh[j:]
    assert _hashes(kaputt2) != [h for _, _, h in UNBERUEHRT]


# ── Trefferflaechen, Schrift, kein Querrollen ───────────────────────────────
def _karten(v):
    u = _uebersicht(v)
    return u[u.index(KARTEN):u.index(TABELLE)]


def _karten_ok(v, css):
    k = _karten(v)
    knopf = re.search(r"React\.createElement\('button',\{key:m\.id,type:\"button\",onClick:\(\)=>\{[^}]*\},style:\{([^}]*)\}", k)
    if not knopf or not re.search(r"minHeight:(\d+)", knopf.group(1)):
        return False
    if int(re.search(r"minHeight:(\d+)", knopf.group(1)).group(1)) < 44:
        return False
    if "overflowX" in k or "overflow-x" in k or "minWidth:7" in k:
        return False
    for px in re.findall(r"fontSize:(\d+)", k):
        if int(px) < 12:
            return False
    if 'gridTemplateColumns:"repeat(7,minmax(0,1fr))"' not in k:
        return False
    return "table.epk-ze-mittel tbody td { height: 44px; }" in css


def _css(roh):
    a = roh.index("<style")
    return roh[a:roh.index("</style>", a)]


def test_karten_44_schrift_12_kein_querrollen(roh):
    v = _ze(roh)
    assert _karten_ok(v, _css(roh))
    # Bearbeiten/Loeschen auf den Wochenkarten bleiben 44 px (v3.9.1016)
    assert v.count('minWidth:44,minHeight:44,padding:"2px 4px",borderRadius:6') == 2
    # Alle uebrigen Knoepfe (Heute, KW, Tages-Stundenbestaetigung, Exporte) traegt die Hausregel
    # auf Touch-Geraeten (pointer:coarse) - Tablet hochkant und quer, Handy.
    css = _css(roh)
    i = css.index("@media (pointer: coarse), (max-width: 768px) {")
    regel = css[i:css.index("}", i)]
    assert "button," in regel and '[role="button"],' in regel and "min-height: 44px !important;" in css[i:i + 900]


def test_umkehr_kleine_karte_oder_querrollen_waere_rot(roh):
    v = _ze(roh)
    css = _css(roh)
    k = _karten(v)
    assert not _karten_ok(v.replace(k, k.replace("minHeight:44,", "minHeight:24,", 1)), css)
    assert not _karten_ok(v.replace(k, k.replace("{display:\"flex\",flexDirection:\"column\",gap:8}",
                                                 "{display:\"flex\",flexDirection:\"column\",gap:8,overflowX:\"auto\"}", 1)), css)
    assert not _karten_ok(v.replace(k, k.replace("fontSize:14,", "fontSize:10,", 1)), css)
    assert not _karten_ok(v, css.replace("table.epk-ze-mittel tbody td { height: 44px; }", ""))


def _css_ok(css):
    regeln = re.findall(r"[^\n{}]*epk-ze-[^{]*\{[^}]*\}", css)
    if len(regeln) < 4:
        return False
    for r in regeln:
        if "overflow-x" in r or "display: none" in r:
            return False
        for px in re.findall(r"font-size:\s*(\d+)px", r):
            if int(px) < 12:
                return False
    return any("epk-ze-tab" in r and "tabular-nums" in r for r in regeln)


def test_css_ohne_querrollen_und_mit_ziffern(roh):
    assert _css_ok(_css(roh))


def test_umkehr_css_querrollen_waere_rot(roh):
    alt = "table.epk-ze-mittel th { white-space: nowrap; }"
    assert alt in roh
    assert not _css_ok(_css(roh.replace(alt, alt.replace("{ ", "{ overflow-x: auto; "), 1)))


def test_schmal_ohne_feste_breiten_ueber_handy(roh):
    """Kein Element ausserhalb des Tabellenzweigs (nur mittel/breit) erzwingt mehr als 360 px."""
    v = nur_code(_ze(roh))
    tab = nur_code(_tabelle(_ze(roh)))
    rest = v.replace(tab, "")
    zu_breit = [int(x) for x in re.findall(r"(?:minWidth|width):(\d+)\b", rest) if int(x) > 360]
    assert zu_breit == [], zu_breit
    assert TAB_MIN in tab


# ── Handy-Karte = Tabellenzelle (echter Code) ───────────────────────────────
STUBS = ("var _dark=false;var mono='M';var UI={neutralTxt:'N',fMeta:12};var V={tx:'T',mt:'M',cd:'C',dm:'D'};"
         "function _okG(x){return 'G';}function _lesbar(x){return 'L';}"
         "var _hK=function(v,d){return String(v).replace('.',',');};"
         "var React={createElement:function(t,p){return {p:p,c:Array.prototype.slice.call(arguments,2)};}};")
MA = {"dayTotals": {"Mo": 8, "Di": 0, "Mi": 4.5}, "absTyp": {"Di": {"i": "U", "l": "Urlaub"}},
      "fehlt": {"Do": True}}


def _zelle_js(src):
    v = _ze(src)
    a = v.index("  const _zeTagZelle=")
    hilfe = v[a:v.index("  /* Stufe 5 mittel:", a)]
    tab = _tabelle(v)
    t0 = tab.index("DAYS.map(d=>{const _h=m.dayTotals[d]||0;")
    t1 = tab.index(':"—");})', t0) + len(':"—");})')
    tabzelle = tab[t0:t1]
    return (STUBS + hilfe + "\nvar m=" + json.dumps(MA) + ";var DAYS=['Mo','Di','Mi','Do','Fr','Sa','So'];"
            "var T=" + tabzelle + ";"
            "var K=DAYS.map(function(d){return _zeTagZelle(m,d);});"
            "process.stdout.write(JSON.stringify(DAYS.map(function(d,i){var t=T[i];return "
            "[[String(t.c[0]),t.p.title||null,t.p.style.color],[String(K[i].t),K[i].title||null,K[i].farbe]];})));")


def _gleich(node_exe, src):
    r = json.loads(run_node_snippet(node_exe, _zelle_js(src)))
    return all(a == b for a, b in r), r


def test_handy_karte_zeigt_dasselbe_wie_die_tabelle(roh, node_exe):
    ok, r = _gleich(node_exe, roh)
    assert ok, r
    texte = [a[0] for a, _ in r]
    assert texte[:4] == ["8", "U", "4,5", "fehlt"], texte


def test_umkehr_abweichende_karte_waere_rot(roh, node_exe):
    kaputt = roh.replace('return {t:"fehlt",', 'return {t:"—",', 1)
    assert kaputt != roh
    ok, _ = _gleich(node_exe, kaputt)
    assert not ok
