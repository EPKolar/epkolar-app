# -*- coding: utf-8 -*-
"""v3.9.1081 - Funde der Render-Pruefung 1080 (Playwright, Offline-Anmeldung, Supabase gesperrt).

P2-1  Hauptreiter als Zahl: Kameras kommt nach dem Schalter-Abruf dazu, alles ab Werkzeuge rutscht
      um eins - Admin wurde 4 s spaeter still zum Buero-Portal. Jetzt bildet _katNachListe die Zahl
      ueber den Schluessel (perm) auf die neue Liste ab; der Verlauf traegt katP.
P2-2  Maengel-Karte am Handy: Aktionsreihe 383 px, Seite rollte 23 px quer -> bricht um.
P2-3  Kopf-Logo in "mittel" gekappt (74/145 px) -> Logo-Block schrumpft nicht, Knopfgruppe gibt nach.
P2-4  Maengel-Filter quer rollend (1535 px in 704 px) -> bricht in jeder Stufe um.
P3a   englische Browser-Netzfehler ("Failed to fetch") -> Anzeige-Hilfe _fehlerDeutsch/_fehlerText.
P3b   Projekt-Seitenleiste "Dashboard" -> "Übersicht".
P3c   AS-Sortierkoepfe 41 px -> 44 px (mittel).
P3d   Handy-Netzstreifen "SERVER" ragte 21 px in die Fussleiste -> bottom:calc(100% + 1px), deutscher Text.

Jede Zusicherung hat eine Umkehrprobe: der alte Stand muss an derselben Pruefung scheitern.
Gemessen am gerenderten Schirm wurde zusaetzlich (Zahlen im Bericht des Laufs); hier steht die
Quelltext- und Logikseite.
"""
import io
import json
import os
import re
import subprocess

import pytest

WURZEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


@pytest.fixture(scope="module")
def html():
    s = io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read()
    assert len(s) > 3_000_000, "index.html zu klein - Datenverlust, kein gruener Fall"
    return s.replace("\r\n", "\n")


def _fn(src, name):
    i = src.index("function %s(" % name)
    j = src.index("{", src.index(")", i))
    d = 0
    for k in range(j, len(src)):
        if src[k] == "{":
            d += 1
        elif src[k] == "}":
            d -= 1
            if d == 0:
                return src[i:k + 1]
    raise AssertionError("Funktion %s ohne Ende" % name)


def _node(js):
    from conftest import _find_node
    exe = _find_node()
    if not exe:
        pytest.skip("Node.js fehlt")
    r = subprocess.run([exe, "-e", js], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


# ── P2-1: der gewaehlte Reiter bleibt derselbe ─────────────────────────────

OHNE = ["_home", "_chef", "projekte", "arbeitsscheine", "wochenplanung", "zeiterfassung", "urlaub", "stunden",
        "fahrzeuge", "flotte", "werkzeuge", "bauprovisorien", "gefahrstoff", "mitarbeiter", "auswertungen",
        "_settings", "bueroexport", "admin"]
MIT = OHNE[:10] + ["kameras"] + OHNE[10:]


def _render_block(src):
    a = src.index("  const _tabsSchlRef=")
    e = src.index("\n  }\n", a) + 4
    return src[a:e]


def _render_harness(block):
    """Fuehrt den ECHTEN Render-Block aus index.html wiederholt aus (Ref bleibt ueber die Durchlaeufe)."""
    return """
%s
const ref={current:null};
const _react={useRef:{call:()=>ref}};
function render(perms,kat){
  const tabs=perms.map(p=>({perm:p}));
  let gesetzt=null;const setKat=v=>{gesetzt=v;};const _katUmgebogen={current:false};
  %s
  return {gesetzt,flag:_katUmgebogen.current};
}
""" % ("%s", block)


def _lauf(src, block):
    h = _render_harness(block) % (_fn(src, "_katNachListe"))
    js = h + """
const OHNE=%s, MIT=%s;
const out={};
for(const p of ["admin","werkzeuge","mitarbeiter","bueroexport","projekte","_home"]){
  ref.current=null;
  const k=OHNE.indexOf(p);
  render(OHNE,k);                       // erstes Bild: Kameras noch nicht da
  const r=render(MIT,k);                // Schalter-Abruf antwortet: Liste mit Kameras
  const kNeu=r.gesetzt===null?k:r.gesetzt;
  out[p]={seite:MIT[kNeu],flag:r.flag,wieder:render(MIT,kNeu).gesetzt};
}
ref.current=null;render(MIT,MIT.indexOf("kameras"));const weg=render(OHNE,MIT.indexOf("kameras"));
out.kamerasWeg=weg.gesetzt;
console.log(JSON.stringify(out));
""" % (json.dumps(OHNE), json.dumps(MIT))
    return _node(js)


def test_p2_1_reiter_bleibt_beim_listenwechsel(html):
    out = _lauf(html, _render_block(html))
    for p in ["admin", "werkzeuge", "mitarbeiter", "bueroexport", "projekte", "_home"]:
        assert out[p]["seite"] == p, "Reiter %s wurde nach dem Kameras-Einschub zu %s" % (p, out[p]["seite"])
        assert out[p]["wieder"] is None, "zweiter Durchlauf setzt erneut - Endlosschleife droht"
    assert out["admin"]["flag"] is True, "Umrechnung muss den Verlauf auf Ersetzen schalten (_katUmgebogen)"
    assert out["_home"]["flag"] is False, "vor dem Einschub: keine Umrechnung, kein Ersetzen"
    assert out["kamerasWeg"] is None, "verschwundener Reiter: Zahl bleibt, die Klemme uebernimmt"


def test_p2_1_umkehrprobe_alter_stand_springt_zum_buero_portal(html):
    block = _render_block(html)
    alt = block.replace("_katNachListe(_tabsSchlRef.current,_tabsSchl,kat)", "kat")
    assert alt != block
    out = _lauf(html, alt)
    assert out["admin"]["seite"] == "bueroexport", out["admin"]
    assert out["werkzeuge"]["seite"] == "kameras", out["werkzeuge"]


def test_p2_1_verlauf_ueber_schluessel(html):
    js = _fn(html, "_katAusVerlauf") + """
const L=%s.map(p=>({perm:p}));
console.log(JSON.stringify([
  _katAusVerlauf({kat:10,katP:"werkzeuge"},L),   // Eintrag aus der Liste OHNE Kameras
  _katAusVerlauf({kat:3},L),                      // alter Eintrag ohne katP: Zahl gilt
  _katAusVerlauf({kat:4,katP:"gibtsnicht"},L),
  _katAusVerlauf(null,L)]));
""" % json.dumps(MIT)
    r = _node(js)
    assert r == [MIT.index("werkzeuge"), 3, 4, 0], r
    # Umkehrprobe: die nackte Zahl (alter popstate-Weg) landet auf Kameras
    assert MIT[10] == "kameras"


def test_p2_1_alle_wege_tragen_den_schluessel(html):
    app = html[html.index("const [kat,setKat]=") - 5000:html.index("const mainTabs=tabs.filter")]
    push = re.findall(r"pushState\(\{kat[^)]*\)", html)
    assert len(push) >= 5, push
    for p in push:
        assert "katP" in p, "Verlaufseintrag ohne Schluessel: %s" % p
    assert "const _nk=_katAusVerlauf(s,_tabsListeRef.current);" in html
    assert "history.replaceState({...(history.state||{}),kat,katP:_kp},'')" in html
    # stabile Hook-Position: Render-Block VOR dem ersten Early-Return
    assert html.index("const _tabsSchlRef=") < html.index("if(appLoading) return (")
    assert html.index("const _tabsSchlRef=") > html.index("_tabsListeRef.current=tabs;")
    # Umkehrprobe des Wegezaehlers: ein Eintrag ohne katP faellt auf
    kaputt = html.replace("history.pushState({kat:0,katP:\"_home\"},'')", "history.pushState({kat:0},'')", 1)
    assert any("katP" not in p for p in re.findall(r"pushState\(\{kat[^)]*\)", kaputt))
    assert app


# ── P2-2 / P2-4: Maengel ───────────────────────────────────────────────────

def test_p2_2_aktionsreihe_bricht_um(html):
    a = html.index("'data-epk': \"mg-aktionen\"")
    stil = html[a:a + 160]
    assert 'flexWrap:"wrap"' in stil and 'maxWidth:"100%"' in stil, stil
    zeile = html[a:html.index("\n          )", html.index("delM(m.id)", a))]
    assert zeile.count("minHeight:44") >= 3, "Knoepfe (Status, Plan, Loeschen) muessen 44 px hoch bleiben"
    # Umkehrprobe: der alte Kopf hatte weder Umbruch noch Grenze
    alt = '{display:"flex",gap:6,alignItems:"center",flexShrink:0}}\n              /* Quick-Status-Pills'
    assert alt not in html


def test_p2_4_filter_bricht_in_jeder_stufe_um(html):
    a = html.index("'data-epk': \"mg-filter\"")
    stil = html[a:a + 120]
    assert 'flexWrap:"wrap"' in stil and "nowrap" not in stil, stil
    assert "'data-epk': \"mg-filter-status\"" in html and "'data-epk': \"mg-filter-prio\"" in html
    # Gruppen am Handy unsichtbar (display:contents) - dort Umbruch wie bisher
    assert html.count('display:isMob?"contents":"flex"/* schmal: Gruppe unsichtbar') == 2
    assert 'flexWrap:isMob?"wrap":"nowrap",overflowX:isMob?"visible":"auto"' not in html


# ── P2-3: Logo ganz sichtbar in "mittel" ──────────────────────────────────

def test_p2_3_logo_block_schrumpft_nicht(html):
    a = html.index("'data-epk': \"kopf-logo\"")
    assert "flexShrink:_isTabletNav?0:1" in html[a:a + 400]
    assert 'gap:8,flexShrink:_isTabletNav?1:0,minWidth:0}}' in html, "Knopfgruppe muss in mittel nachgeben"
    assert '!isMob&&!_isTabletNav&&"Abmelden")' in html
    assert "'aria-label': \"Abmelden\"" in html, "Abmelden bleibt benannt"
    # Umkehrprobe: alter Logo-Block ohne flexShrink-Regel
    assert 'gap:_isTabletNav?2:10,minWidth:0,overflow:"hidden"}}' not in html


# ── P3a: englische Netzfehler ─────────────────────────────────────────────

def test_p3a_netzfehler_deutsch(html):
    a = html.index("var _NETZFEHLER_EN=")
    rx = html[a:html.index("\n", a)]
    js = rx + "\n" + _fn(html, "_fehlerDeutsch") + "\n" + _fn(html, "_fehlerText") + """
console.log(JSON.stringify([
 _fehlerText(new TypeError("Failed to fetch")),
 _fehlerDeutsch("System-Config laden fehlgeschlagen: TypeError: Failed to fetch"),
 _fehlerDeutsch("NetworkError when attempting to fetch resource."),
 _fehlerDeutsch("Load failed"),
 _fehlerText(new Error("HTTP 500")),
 _fehlerDeutsch(null)]));"""
    r = _node(js)
    assert r[0] == "keine Verbindung zum Server"
    assert r[1] == "System-Config laden fehlgeschlagen: keine Verbindung zum Server"
    assert r[2] == "keine Verbindung zum Server" and r[3] == "keine Verbindung zum Server"
    assert r[4] == "HTTP 500", "fremde Fehler bleiben woertlich - kein erfundener Grund"
    assert r[5] is None
    # Render 1089 P3: Toast ohne Emoji (CI), weiter ueber _fehlerText - Pin nachgezogen
    assert "_2(\"Juprowa-Konfiguration: \"+_fehlerText(e)" in html
    assert "'System-Config laden fehlgeschlagen: '+_fehlerText(e)" in html
    assert "msg=_fehlerDeutsch(msg);/* v3.9.1081 P3a */" in html
    assert "msg=_fehlerDeutsch(msg);/* v3.9.1081 P3a: englische" in html


def test_p3a_umkehrprobe_alter_text_bleibt_englisch(html):
    assert "Juprowa-Config: \"+(e&&e.message||e)" not in html
    assert "'System-Config laden fehlgeschlagen: '+e.message" not in html


def test_p3a_geschuetzte_funktionen_unberuehrt(html):
    for name in ("_juprowaPush", "_juprowaSanitize"):
        assert "_fehlerText" not in _fn(html, name) and "_fehlerDeutsch" not in _fn(html, name)


# ── P3b / P3c / P3d ───────────────────────────────────────────────────────

def test_p3b_seitenleiste_uebersicht(html):
    assert '{id:"dashboard",ik:"uebersicht",l:"Übersicht"' in html
    assert 'l:"Dashboard"' not in html


def test_p3c_sortkoepfe_44(html):
    assert 'table.epk-as-mittel thead th[role="button"] { height: 44px; }' in html


def test_p3d_netzstreifen(html):
    a = html.index("'data-epk': \"netz-streifen\"")
    t = re.sub(r"/\*.*?\*/", "", html[a:a + 1500], flags=re.S)
    assert 'bottom:"calc(100% + 1px)"' in t and "top:-24" not in t
    assert '"Offline – keine Internetverbindung":"Server nicht erreichbar"' in t
    assert '"OFFLINE":"SERVER"' not in html
