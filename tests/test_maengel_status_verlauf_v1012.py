# -*- coding: utf-8 -*-
"""v3.9.1012 - Maengel bekommen einen Statusverlauf wie Tickets (defects.status_history jsonb).

Riegel auf die EIGENSCHAFTEN:
1. Jede Schreibstelle, die per PUT /api/defects/<id> einen status schickt, schickt den
   Verlauf aus dem EINEN Helfer _mgVerlaufFeld direkt dahinter als eigenen PUT
   (_mgVerlaufPut, gleiche id) UND traegt ihn im lokalen Zustand. Der Status-Body selbst
   bleibt unveraendert (gepinnt von v849/v895): scheitert der Verlauf, bleibt der Status.
   Die Menge wird vollstaendig aus dem Quelltext gezaehlt (nicht aus einer Abschrift).
2. Der Helfer, per node ausgefuehrt: haengt an, bei gleichem Status kein Eintrag, alter
   Verlauf bleibt, unbekannter Verlauf wird NIE ueberschrieben.
3. Die Load-Map (_mapDefect) reicht status_history durch - sonst ersetzte der naechste
   Wechsel den Server-Verlauf durch ein Ein-Element-Array. Login-Merge haelt den Verlauf
   eines wartenden PUT.
4. Anzeige am Mangel, ohne Emoji, Farben ueber V-Tokens.
Jeweils mit Umkehrprobe: zurueckgebaut muss der Riegel anschlagen.
"""
import io
import json
import re
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn, run_node_snippet  # noqa: E402

PUT_RE = re.compile(r'SQ\.push\(\{url:"/api/defects/"\+([\w.]+),method:"PUT",body:')
# Anzahl der Schreibstellen mit status im PUT-Body (gezaehlt am Stand v3.9.1012):
# updSt (traegt auch den Sammel-Weg), reviewAccept, reviewReject, reviewProgress,
# reviewDone, updateTicket-Spiegel (VPlan), QuickEditPin onSave (VPlan).
ERWARTET_STATUS_PUTS = 7


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _klammer_ende(text, i):
    """i zeigt auf '{'. Liefert Index hinter der passenden '}' (Strings uebersprungen)."""
    tiefe = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            q = c
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    i += 1
                i += 1
        elif c == "/" and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = j + 1
        elif c == "{":
            tiefe += 1
        elif c == "}":
            tiefe -= 1
            if tiefe == 0:
                return i + 1
        i += 1
    raise AssertionError("Klammer nicht geschlossen")


def _status_puts(text):
    """Alle PUT /api/defects/<id>, deren Body (ausserhalb von Kommentaren) ein status-Feld schreibt."""
    out = []
    for m in PUT_RE.finditer(text):
        b0 = m.end()
        if text[b0] != "{":
            # body:_ks?{...}:{...} - beide Zweige einsammeln
            ende = text.find("});", b0)
            body = text[b0:ende]
        else:
            body = text[b0:_klammer_ende(text, b0)]
        ohne_k = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
        if re.search(r"(?<![\w.])status:", ohne_k):
            out.append((m.start(), body, m.group(1), b0 + len(body)))
    return out


def _fehlende_verlaeufe(text):
    """Liefert die Stellen, an denen der Verlauf-PUT oder der lokale Zustand fehlen."""
    fehl = []
    for pos, body, ident, ende in _status_puts(text):
        zeile = text.count("\n", 0, pos) + 1
        if "status_history" in body:
            fehl.append("Z%d Verlauf im Status-Body statt eigenem PUT" % zeile)
        danach = text[ende:ende + 80]
        m = re.match(r"\}?\}\);_mgVerlaufPut\(%s,(_vh\w*)\);" % re.escape(ident), danach)
        if not m:
            fehl.append("Z%d kein _mgVerlaufPut(%s,...) direkt hinter dem Status-PUT: %s" % (zeile, ident, danach[:60]))
            continue
        n = m.group(1)
        fenster = text[max(0, pos - 1500):pos + 1500]
        if not re.search(r"const %s=_mgVerlaufFeld\(" % re.escape(n), fenster):
            fehl.append("Z%d %s kommt nicht aus _mgVerlaufFeld" % (zeile, n))
        if not re.search(r"setForms\([^;]*?maengel[^;]*?\.\.\.%s\}" % re.escape(n), fenster):
            fehl.append("Z%d lokaler Zustand ohne %s" % (zeile, n))
    return fehl


# ── 1. Schreibstellen ────────────────────────────────────────────────────

def test_alle_status_schreibstellen_gefunden(src):
    puts = _status_puts(src)
    assert len(puts) == ERWARTET_STATUS_PUTS, (
        "Status-PUTs auf defects: %d statt %d - eine neue Stelle braucht den Verlauf, "
        "oder eine ist verschwunden." % (len(puts), ERWARTET_STATUS_PUTS))


def test_jede_status_schreibstelle_traegt_den_verlauf(src):
    fehl = _fehlende_verlaeufe(src)
    assert not fehl, "\n".join(fehl)


@pytest.mark.parametrize("weg,ersatz", [
    ("_mgVerlaufPut(u.id,_vhQ);", ""),            # QuickEditPin: Verlauf-PUT weg
    ("_mgVerlaufPut(_u.id,_vhT);", ""),           # updateTicket-Spiegel
    ("_mgVerlaufPut(id,_vhD);", ""),              # reviewDone
    ("_mgVerlaufPut(id,_vh);", ""),               # updSt (und damit Sammel-Weg)
    ("worker:_zug,..._vhQ}:m)", "worker:_zug}:m)"),  # QuickEditPin: lokaler Zustand
])
def test_umkehrprobe_zurueckgebaute_stelle_schlaegt_an(src, weg, ersatz):
    assert weg in src, "Anker der Umkehrprobe fehlt: %s" % weg
    kaputt = src.replace(weg, ersatz, 1)
    assert kaputt != src
    assert _fehlende_verlaeufe(kaputt), "Riegel bleibt gruen, obwohl %s zurueckgebaut ist" % weg


def test_umkehrprobe_neue_stelle_ohne_verlauf_wird_gezaehlt(src):
    neu = src + '\nSQ.push({url:"/api/defects/"+id,method:"PUT",body:{status:"offen"}});\n'
    assert len(_status_puts(neu)) == ERWARTET_STATUS_PUTS + 1
    assert _fehlende_verlaeufe(neu)


def test_status_bodies_bleiben_unveraendert(src):
    """Der Statuswechsel haengt nie an der neuen Spalte: die Status-Bodies sind die alten."""
    for alt in ('body:_ks?{status:st,kunde_status:_ks}:{status:st}});_mgVerlaufPut(id,_vh);',
                'body:{status:_dst,prio:_prio,frist:_frist,zugewiesen:_zug}});_mgVerlaufPut(u.id,_vhQ);',
                'body:{status:"abgelehnt",kunde_status:"abgelehnt",review_note:reviewNote}});_mgVerlaufPut(id,_vhR);'):
        assert alt in src, alt


def test_verlauf_put_schickt_nur_den_verlauf(node_exe, src):
    b = _extract_fn(src, "_mgVerlaufPut")
    assert b
    js = ("var q=[];var SQ={push:function(a){q.push(a);}};" + b +
          "_mgVerlaufPut('a',{});_mgVerlaufPut('',{status_history:[]});"
          "_mgVerlaufPut('b',{status_history:[{status:'behoben'}]});console.log(JSON.stringify(q));")
    q = json.loads(run_node_snippet(node_exe, js))
    assert q == [{"url": "/api/defects/b", "method": "PUT", "body": {"status_history": [{"status": "behoben"}]}}]


def test_bulk_laeuft_ueber_updst(src):
    vm = _extract_fn(src, "VMang")
    assert vm
    bulk = vm[vm.find("const _bulkApply="):vm.find("const delM=")]
    assert "if(_bulkSt)updSt(id,_bulkSt);" in bulk
    assert not re.search(r'body:\{[^}]*\bstatus:', bulk), "Sammel-Weg schreibt status am Helfer vorbei"


def test_post_bodies_ohne_verlauf(src):
    """Anlegen setzt den Verlauf ueber den DB-Default '[]' - im POST-Body steht er nicht."""
    for m in re.finditer(r'SQ\.push\(\{url:"/api/defects",method:"POST",body:', src):
        b0 = m.end()
        body = src[b0:_klammer_ende(src, b0)]
        assert "status_history" not in body


# ── 2. Helfer per node ───────────────────────────────────────────────────

def _helfer_js(src):
    jp = re.search(r"const _jp=s=>\{.*?\};", src)
    assert jp, "_jp nicht gefunden"
    teile = [jp.group(0)]
    for n in ("_mgVerlaufListe", "_mgVerlauf", "_mgVerlaufFeld", "_mapDefect"):
        b = _extract_fn(src, n)
        assert b, "%s nicht gefunden - das ist rot, nicht gruen." % n
        teile.append(b)
    return ("var window={_curUser:function(){return {id:'u1',name:'Pinger'};}};"
            + "\n".join(teile))


def _node(node_exe, src, rumpf, helfer=None):
    js = (helfer or _helfer_js(src)) + "\n" + "console.log(JSON.stringify((function(){" + rumpf + "})()));"
    return json.loads(run_node_snippet(node_exe, js))


def test_helfer_haengt_an(node_exe, src):
    r = _node(node_exe, src, """
      var m={id:'a',status:'offen',status_history:[]};
      return _mgVerlaufFeld(m,'in Behebung','  ');""")
    h = r["status_history"]
    assert len(h) == 1
    e = h[0]
    assert e["status"] == "in Behebung" and e["fromStatus"] == "offen"
    assert e["changed_by_id"] == "u1" and e["changed_by_name"] == "Pinger"
    assert e["comment"] is None and e["changed_at"]
    assert set(e) == {"status", "fromStatus", "changed_by_id", "changed_by_name", "changed_at", "comment"}


def test_helfer_gleicher_status_kein_eintrag(node_exe, src):
    r = _node(node_exe, src, """
      var alt=[{status:'offen',fromStatus:null}];
      var m={id:'a',status:'offen',status_history:alt};
      return {feld:_mgVerlaufFeld(m,'offen'),arr:_mgVerlauf(m,'offen'),leer:_mgVerlaufFeld(m,'')};""")
    assert r["feld"] == {} and r["leer"] == {}
    assert r["arr"] == [{"status": "offen", "fromStatus": None}]


def test_helfer_alter_verlauf_bleibt_und_kommentar(node_exe, src):
    r = _node(node_exe, src, """
      var alt=[{status:'in Behebung',fromStatus:'offen'},{status:'behoben',fromStatus:'in Behebung'}];
      var m={id:'a',status:'behoben',status_history:JSON.stringify(alt)};
      var f=_mgVerlaufFeld(m,'abgelehnt',' Doppelt gemeldet ');
      return {f:f,altLen:alt.length};""")
    h = r["f"]["status_history"]
    assert [x["status"] for x in h] == ["in Behebung", "behoben", "abgelehnt"]
    assert h[2]["fromStatus"] == "behoben" and h[2]["comment"] == "Doppelt gemeldet"
    assert r["altLen"] == 2, "der alte Verlauf darf nicht mutiert werden"


def test_helfer_unbekannter_verlauf_wird_nie_ueberschrieben(node_exe, src):
    r = _node(node_exe, src, """
      return {ohne:_mgVerlaufFeld({id:'a',status:'offen'},'behoben'),
              nul:_mgVerlaufFeld({id:'a',status:'offen',status_history:null},'behoben'),
              kein:_mgVerlaufFeld(undefined,'behoben')};""")
    assert r == {"ohne": {}, "nul": {}, "kein": {}}


def test_umkehrprobe_helfer_ohne_gleich_pruefung(node_exe, src):
    """Faellt die Gleich-Pruefung weg, muss der Riegel 'kein Eintrag' rot werden."""
    h = _helfer_js(src)
    kaputt = h.replace('if(!neuerStatus||neuerStatus===((m&&m.status)||""))return {};', "")
    assert kaputt != h
    r = _node(node_exe, src, "return _mgVerlaufFeld({id:'a',status:'offen',status_history:[]},'offen');", kaputt)
    assert r != {}


# ── 3. Load-Map + Merge ─────────────────────────────────────────────────

LADE = """
  var srv={id:'a',title:'X',status:'behoben',status_history:[{status:'behoben',fromStatus:'offen'}]};
  var txt={id:'b',status:'offen',status_history:'[{"status":"offen","fromStatus":"behoben"}]'};
  var ohne={id:'c',status:'offen'};
  var m=_mapDefect(srv);
  var f=_mgVerlaufFeld(m,'offen');
  return {m:m.status_history,t:_mapDefect(txt).status_history,o:('status_history' in _mapDefect(ohne))?_mapDefect(ohne).status_history===undefined:true,f:f};
"""


def test_loadmap_reicht_verlauf_durch(node_exe, src):
    r = _node(node_exe, src, LADE)
    assert r["m"] == [{"status": "behoben", "fromStatus": "offen"}]
    assert r["t"] == [{"status": "offen", "fromStatus": "behoben"}]
    assert r["o"] is True, "fehlendes Feld muss UNBEKANNT bleiben, nicht [] werden"
    h = r["f"]["status_history"]
    assert len(h) == 2 and h[0]["fromStatus"] == "offen", "Server-Verlauf muss erhalten bleiben"


def test_umkehrprobe_loadmap_ohne_feld(node_exe, src):
    h = _helfer_js(src)
    kaputt = re.sub(r",\s*/\*[^*]*\*/\s*status_history:\(d\.status_history==null\?undefined:_jp\(d\.status_history\)\)", "", h)
    assert kaputt != h, "Anker der Umkehrprobe fehlt"
    r = _node(node_exe, src, LADE, kaputt)
    assert r.get("m") is None and r["f"] == {}, "ohne Durchreichen darf der Riegel nicht gruen bleiben"


def test_merge_pfade_halten_den_verlauf(src):
    # Poll (v3.9.597): wartender PUT -> lokale Fassung bleibt (inkl. status_history)
    assert "(_v597PDefPut.has(d.id)&&_prevById.has(d.id))?_prevById.get(d.id):d" in src
    # Login-Load: Verlauf des letzten wartenden PUT gewinnt
    assert re.search(r'_m==="PUT"\)\{const _id=_u\.split\("/"\)\.pop\(\);if\(_id&&it\.body&&Array\.isArray\(it\.body\.status_history\)\) _v1012PendingDefectVerlauf\.set\(_id,it\.body\.status_history\);\}', src)
    assert ".map(_mapDefect).map(m=>_v1012PendingDefectVerlauf.has(m.id)?{...m,status_history:_v1012PendingDefectVerlauf.get(m.id)}:m)" in src


def test_neuanlagen_kennen_leeren_verlauf(src):
    vm = _extract_fn(src, "VMang")
    add = vm[vm.find("const add=()=>"):vm.find("const _DEF2TICKET_ST=")]
    assert 'status:"offen",status_history:[]' in add
    vp = _extract_fn(src, "VPlan")
    assert vp.count("fromPlan:true,status_history:[]") == 2


# ── 4. Anzeige ───────────────────────────────────────────────────────────

def test_anzeige_am_mangel_im_ci(src):
    vm = _extract_fn(src, "VMang")
    assert ", _mgVerlaufAnzeige(m)" in vm
    an = _extract_fn(src, "_mgVerlaufAnzeige")
    assert an and "React.createElement('details'" in an and "React.createElement('summary'" in an
    assert "Statusverlauf (" in an
    assert "V.dm" in an and "V.bd" in an
    assert not re.search(r"#[0-9A-Fa-f]{3,6}\b", an), "Farben nur ueber Tokens"
    assert not re.search(r"fontSize:\d", an), "Schriftgroessen nur ueber UI-Tokens"
    emoji = [c for c in an if ord(c) >= 0x2190 and c not in "→"]
    assert not emoji, "Emoji/Sonderzeichen in der Anzeige: %r" % emoji
    st = _extract_fn(src, "_mgStText")
    for paar in ('"offen"?"Offen"', '"in Behebung"?"In Arbeit"', '"behoben"?"Erledigt"', '"abgelehnt"?"Abgelehnt"'):
        assert paar in st
