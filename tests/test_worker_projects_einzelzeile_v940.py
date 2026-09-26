# -*- coding: utf-8 -*-
"""v3.9.940 Vorarbeit - Projektzuweisungen muessen ZEILENWEISE geschrieben werden.

WAS HIER GEMESSEN WIRD (und warum es heute rot ist)
───────────────────────────────────────────────────
Heute schreibt EIN Auftrag die ganze Liste: `PUT /api/worker-projects/<mid>`
mit `{projects:[...]}`. Der Uebersetzer macht daraus zwei getrennte HTTP-
Anfragen: erst `DELETE /worker_projects?worker_id=eq.<mid>` (ALLE Zeilen des
Mitarbeiters), dann ein Upsert der Liste, die das eigene Geraet fuer richtig
haelt. Daraus entstehen zwei Schaeden, und diese Datei misst beide:

  1. DER DATENVERLUST. Kennt der lokale Stand Projekt A nicht (weil ein anderer
     Admin es gesetzt hat, nachdem dieses Geraet geladen hat), dann nimmt das
     Alles-Loeschen A mit und das Neu-Einfuegen bringt es nicht zurueck.
  2. DAS LEERE FENSTER. Zwischen den beiden Anfragen hat der Mitarbeiter
     serverseitig KEINE Zuweisung. Reisst die Verbindung dort ab, ist der
     Zustand leer.

WIE GEMESSEN WIRD - AUSGEFUEHRT, NICHT GELESEN
──────────────────────────────────────────────
`toggleProj` (die Benutzerhandlung), `_translateAndExec` (der Uebersetzer) und
ALLE `_sb*`-Helfer werden WOERTLICH aus index.html geschnitten - Klammerbilanz
ueber `scripts/code_scan.py`, damit eine `}` in einem Changelog-Kommentar nicht
mitzaehlt - und unter Node gegen einen NACHGEBAUTEN PostgREST gefahren, der
eine echte Tabelle mit echten Zeilen fuehrt.

Der Schnitt liegt bewusst bei `fetch` und NICHT bei `_sbUpsert`/`_sbDeleteWhere`:
welchen Helfer der Umbau benutzt, ist dann gleichgueltig - jede Anfrage laeuft
durch dieselbe Attrappe und steht im Protokoll. Ein Riegel, der nur nach
`project_id=eq.` im Quelltext sucht, koennte nicht sagen, ob die Zeile auch
ERREICHT wird.

WAS DIE ATTRAPPE UNSICHTBAR MACHT (fetch ist gefaelscht - das hat einen Preis)
─────────────────────────────────────────────────────────────────────────────
Sichtbar ist nur, WELCHE Anfragen der Code stellt und was eine mitspielende
Gegenseite daraus macht. Unsichtbar bleibt:

  * die echten RLS-Policies auf `public.worker_projects`. Ob ein Einzel-DELETE
    live durchgeht, kann diese Datei NICHT sagen (gemessen wurde es nicht -
    siehe docs/befunde/B2_WORKER_PROJECTS.md).
  * der echte eindeutige Schluessel. Die Attrappe loest `merge-duplicates`
    ueber die Spalte `id` auf, weil der heutige Code `id` mitschickt und
    funktioniert. Welche Spalten der PK live wirklich umfasst, ist UNGEMESSEN.
  * NOT-NULL/Vorgabewerte auf `assigned_at` und `role` (beide Spalten existieren
    live, gemessen) - die Attrappe verlangt sie nicht.
  * Trigger auf der Tabelle.
  * ob die laufende Instanz `Prefer: count=exact` auch auf DELETE mit einem
    `Content-Range` beantwortet. Gemessen wurde das nur auf GET und HEAD
    (`preference-applied: count=exact`). Die Attrappe TUT es - das ist eine
    Annahme, keine Messung.
  * Netzabbruch, Zeitueberschreitung, AbortSignal.
  * die 1500 ms Sammelverzoegerung, die Reihenfolge in `doSync`, die
    Wiederholungs-/Verwerfen-Logik und IndexedDB. Die Warteschlange ist hier
    ein Array, das sofort und vollstaendig abgefahren wird.
  * React: kein Rendern, kein Neuladen, kein `visibilitychange`.

KOEDER
──────
Zaehlende Pruefungen werden beim eigenen Ausfall gruen ("nichts gefunden = kein
Fehler"). Deshalb hat jede zaehlende Pruefung hier einen Fall, der anschlagen
MUSS: `test_koeder_*` weist nach, dass der Pruefstand ueberhaupt Anfragen sieht,
dass der Lueckensucher eine Luecke findet und dass die Attrappe eine fremde
Zeile wirklich verlieren KANN. Schlaegt ein Koeder nicht an, ist diese Datei
kaputt und ihre gruenen Faelle bedeuten nichts.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "scripts"))

from code_scan import ist_code, nur_code_stellen  # noqa: E402

NODE_TIMEOUT = int(os.environ.get("EPK_TEST_TIMEOUT", "120"))


# ── Schneiden ─────────────────────────────────────────────────────────────

def _block(roh, feld, anker):
    """Woertlicher Schnitt von `anker` bis zur passenden schliessenden Klammer.

    Die Bilanz laeuft NUR ueber Zeichen, die code_scan als CODE fuehrt. Ohne
    das schneidet man in dieser Datei mitten in eine Funktion: in den
    Changelog-Kommentaren stehen geschweifte Klammern zu Hunderten.
    """
    stellen = nur_code_stellen(roh, anker)
    if len(stellen) != 1:
        raise AssertionError(
            "Anker %r kommt %d mal im CODE vor - erwartet genau 1. Der Schnitt "
            "ist damit nicht eindeutig; die Datei muss angepasst werden, NICHT "
            "der Code." % (anker, len(stellen)))
    i = stellen[0]
    j = i + anker.index("{") if "{" in anker else roh.index("{", i)
    tiefe, k = 0, j
    while k < len(roh):
        if feld[k]:
            if roh[k] == "{":
                tiefe += 1
            elif roh[k] == "}":
                tiefe -= 1
                if tiefe == 0:
                    return roh[i:k + 1]
        k += 1
    raise AssertionError("Keine passende schliessende Klammer fuer %r" % anker)


HELFER_ANKER = [
    "async function _authRetry(fn){",
    "function _sbH(extra){",
    "function _sbRH(){",
    "function _sbWH(prefer){",
    "function _fT(init,ms){",
    "async function _sbGet(table,filter){",
    "async function _sbPost(table,data,minimal){",
    "async function _sbUpsert(table,data,minimal){",
    "async function _sbInsertIfAbsent(table,data){",
    "async function _sbPatch(table,id,data){",
    "async function _sbDelete(table,id){",
    "async function _sbDeleteWhere(table,filter){",
]

UEBERSETZER_ANKER = "async function _translateAndExec(url,method,body){"
TOGGLE_ANKER = "const toggleProj=(mid,pid)=>{"
VERSCHMELZ_ANFANG = "if(wpMap&&Array.isArray(wpMap)&&wpMap.length){"
VERSCHMELZ_ENDE = "// Plans + Tickets + Checklists"


@pytest.fixture(scope="module")
def roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


@pytest.fixture(scope="module")
def schnitte(roh):
    feld = ist_code(roh)
    helfer = "\n".join(_block(roh, feld, a) for a in HELFER_ANKER)
    uebersetzer = _block(roh, feld, UEBERSETZER_ANKER)
    toggle = _block(roh, feld, TOGGLE_ANKER)

    i = nur_code_stellen(roh, VERSCHMELZ_ANFANG)
    assert len(i) == 1, ("Der Verschmelz-Anker kommt %d mal im CODE vor."
                         % len(i))
    j = roh.index(VERSCHMELZ_ENDE, i[0])
    verschmelzen = roh[i[0]:j].rstrip()

    # Wegriegel: ein leerer oder absurd kurzer Schnitt wuerde jede Messung
    # gruen machen, weil dann einfach nichts passiert.
    assert len(uebersetzer) > 5000, len(uebersetzer)
    assert len(toggle) > 120, len(toggle)
    assert len(helfer) > 3000, len(helfer)
    assert 200 < len(verschmelzen) < 4000, len(verschmelzen)
    assert "worker_projects" in uebersetzer, (
        "Der geschnittene Uebersetzer nennt worker_projects nicht - der "
        "Schnitt hat den Zweig verfehlt.")
    assert "SQ.push" in toggle, (
        "Der geschnittene toggleProj legt keinen Auftrag ab.")
    return {"helfer": helfer, "uebersetzer": uebersetzer, "toggle": toggle,
            "verschmelzen": verschmelzen}


# ── Der nachgebaute PostgREST + Treiber ───────────────────────────────────

PRUEFSTAND = r"""
"use strict";
const SB_REST = "http://srv/rest/v1";
const SUPABASE_KEY = "anon-attrappe";
let _authToken = null;
let _authRefreshToken = null;
let _sbHLastRefreshAt = 0;
function dlog(){ }
function _isJwtShape(){ return false; }
function _sbAuthRefresh(){ return Promise.resolve(); }
function _isAuthErr(s){ return s === 401 || s === 403; }
function _onAuthFail(){ }
function _merkeRlsFehler(){ }
function _mapBody(o){ return o; }
const _gemeldet = [];
global.window = { __toast: (t)=>_gemeldet.push(["toast", String(t)]) };
// Node 24 fuehrt `navigator` als Nur-Lese-Eigenschaft - eine einfache
// Zuweisung wirft dort ("has only a getter").
Object.defineProperty(global, "navigator", {value: {onLine: true},
                                            configurable: true, writable: true});
global.console = {
  error: (...a)=>_gemeldet.push(["error", a.map(String).join(" ")]),
  warn:  (...a)=>_gemeldet.push(["warn",  a.map(String).join(" ")]),
  log:   ()=>{}
};

// ── Attrappe: ein sehr kleiner PostgREST auf EINER Tabelle ───────────────
// Sie fuehrt echte Zeilen. Was sie NICHT hat: RLS, Trigger, NOT NULL, den
// echten eindeutigen Schluessel. Siehe Dateikopf.
function macheServer(anfangsZeilen){
  const S = {
    zeilen: anfangsZeilen.map(r=>({...r})),
    protokoll: [],
    momente: []
  };
  const kopie = ()=>S.zeilen.map(r=>({...r}));
  S.moment = (was)=>S.momente.push({was: was, zeilen: kopie()});
  S.moment("Anfangszustand");

  function filterAus(qs){
    const f = {};
    let onConflict = null;
    for (const teil of (qs||"").split("&")){
      if (!teil) continue;
      const k = teil.slice(0, teil.indexOf("="));
      const v = teil.slice(teil.indexOf("=")+1);
      if (k === "select" || k === "limit" || k === "offset" || k === "order") continue;
      if (k === "on_conflict"){ onConflict = decodeURIComponent(v).split(","); continue; }
      if (v.startsWith("eq.")) f[k] = decodeURIComponent(v.slice(3));
      else f["__unbekannt_"+k] = v;
    }
    return {f: f, onConflict: onConflict};
  }
  const passt = (r, f)=>Object.keys(f).every(k=>String(r[k]) === String(f[k]));

  S.fetch = async function(url, init){
    init = init || {};
    const methode = String(init.method || "GET").toUpperCase();
    const kopf = {};
    for (const k of Object.keys(init.headers||{})) kopf[k.toLowerCase()] = init.headers[k];
    const prefer = String(kopf["prefer"] || "");
    const pfad = String(url).replace(SB_REST, "");
    const q = pfad.indexOf("?");
    const tabelle = (q < 0 ? pfad : pfad.slice(0, q)).replace(/^\//, "");
    const {f, onConflict} = filterAus(q < 0 ? "" : pfad.slice(q+1));
    let rumpf = null;
    if (init.body){ try { rumpf = JSON.parse(init.body); } catch(_){ rumpf = init.body; } }

    const eintrag = {methode: methode, tabelle: tabelle, pfad: pfad,
                     filter: f, prefer: prefer, rumpf: rumpf,
                     hatPreferKopf: ("prefer" in kopf)};
    let status = 200, koerper = null, zahl = null;

    if (tabelle !== "worker_projects"){
      // Alles andere interessiert hier nicht, darf aber nicht platzen.
      eintrag.status = 200; S.protokoll.push(eintrag); S.moment(methode+" "+tabelle);
      return antwort(200, [], {});
    }

    if (methode === "GET" || methode === "HEAD"){
      koerper = S.zeilen.filter(r=>passt(r,f)).map(r=>({...r}));
      zahl = koerper.length;
    } else if (methode === "DELETE"){
      const treffer = S.zeilen.filter(r=>passt(r,f));
      S.zeilen = S.zeilen.filter(r=>!passt(r,f));
      zahl = treffer.length;
      koerper = /return=representation/.test(prefer) ? treffer.map(r=>({...r})) : null;
      status = koerper ? 200 : 204;
    } else if (methode === "POST"){
      const neu = Array.isArray(rumpf) ? rumpf : [rumpf];
      const ziel = onConflict || ["id"];
      const merge = /resolution=merge-duplicates/.test(prefer);
      const ignorieren = /resolution=ignore-duplicates/.test(prefer);
      const raus = [];
      for (const r of neu){
        const gl = {}; ziel.forEach(c=>gl[c] = r[c]);
        const i = S.zeilen.findIndex(x=>passt(x, gl));
        if (i >= 0){
          if (merge){ S.zeilen[i] = {...S.zeilen[i], ...r}; raus.push({...S.zeilen[i]}); }
          else if (ignorieren){ /* DO NOTHING */ }
          else {
            eintrag.status = 409; S.protokoll.push(eintrag); S.moment("POST 409");
            return antwort(409, {code:"23505", message:"duplicate key value"}, {});
          }
        } else { S.zeilen.push({...r}); raus.push({...r}); }
      }
      zahl = raus.length;
      koerper = /return=minimal/.test(prefer) ? null : raus;
      status = koerper ? 201 : 204;
    } else if (methode === "PATCH"){
      const treffer = S.zeilen.filter(r=>passt(r,f));
      treffer.forEach(r=>Object.assign(r, rumpf));
      zahl = treffer.length;
      koerper = /return=representation/.test(prefer) ? treffer.map(r=>({...r})) : null;
      status = koerper ? 200 : 204;
    }

    eintrag.status = status;
    eintrag.betroffen = zahl;
    S.protokoll.push(eintrag);
    S.moment(methode + " " + (Object.keys(f).join(",") || "ohne Filter"));
    const zusatz = {};
    if (/count=/.test(prefer)) zusatz["Content-Range"] = "*/" + zahl;
    return antwort(status, koerper, zusatz);
  };

  function antwort(status, koerper, zusatz){
    const h = {...(zusatz||{})};
    const hget = (n)=>{
      const k = Object.keys(h).find(x=>x.toLowerCase() === String(n).toLowerCase());
      return k === undefined ? null : h[k];
    };
    const txt = koerper === null ? "" : JSON.stringify(koerper);
    return {
      ok: status >= 200 && status < 300,
      status: status,
      headers: {get: hget},
      text: async()=>txt,
      json: async()=>{ if (txt === "") throw new Error("Unexpected end of JSON input");
                       return JSON.parse(txt); }
    };
  }
  return S;
}

__HELFER__
__UEBERSETZER__

// ── Treiber ─────────────────────────────────────────────────────────────
async function lauf(opt){
  const srv = macheServer(opt.server);
  global.fetch = srv.fetch;
  _gemeldet.length = 0;

  const SQ = {liste: [], push(a){ SQ.liste.push(a); return Promise.resolve(); }};
  let monteurProjekte = JSON.parse(JSON.stringify(opt.lokal));
  const isWAdm = opt.isWAdm === undefined ? true : opt.isWAdm;
  const setMonteurProjekte = (f)=>{
    monteurProjekte = (typeof f === "function") ? f(monteurProjekte) : f;
  };
  __TOGGLE__

  toggleProj(opt.mid, opt.pid);
  await new Promise(r=>setTimeout(r, 0));
  const auftraege = SQ.liste.map(a=>({url: a.url, method: a.method || "POST",
                                      body: a.body}));
  srv.moment("Warteschlange gefuellt, noch nichts abgeflossen");
  let fehler = null;
  try {
    for (const a of SQ.liste){
      await _translateAndExec(a.url, a.method || "POST", a.body);
    }
  } catch(e){ fehler = String((e && e.message) || e); }

  return {
    auftraege: auftraege,
    protokoll: srv.protokoll,
    momente: srv.momente,
    endzustand: srv.zeilen,
    lokal: monteurProjekte,
    fehler: fehler,
    gemeldet: _gemeldet.slice()
  };
}

// ── Verschmelzung beim Laden (das Ueberspringen leerer Antworten) ────────
function verschmelzen(wpMap, ausstehend, vorher){
  let stand = vorher;
  const _v938PendingWpWorkers = new Set(ausstehend || []);
  const setMonteurProjekte = (f)=>{
    stand = (typeof f === "function") ? f(stand) : f;
  };
  __VERSCHMELZEN__
  return stand;
}

(async()=>{
  const aus = {};

  // 1. DER KERNFALL. Server kennt A (ein anderer Admin hat es gesetzt),
  //    der lokale Stand kennt es NICHT. Jetzt wird B gesetzt.
  aus.kernfall = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"}],
    lokal: {w1: []}, mid: "w1", pid: "B"
  });

  // 2. Gegenprobe: derselbe Griff, aber der lokale Stand KENNT A.
  //    Danach muessen A und B beide stehen - sonst misst Fall 1 nichts.
  aus.lokalKenntA = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"}],
    lokal: {w1: ["A"]}, mid: "w1", pid: "B"
  });

  // 3. Abwaehlen: B war gesetzt (lokal UND server), A nur am Server.
  //    B muss weg, A muss bleiben.
  aus.abwaehlen = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"},
             {id:"w1_B", worker_id:"w1", project_id:"B"}],
    lokal: {w1: ["B"]}, mid: "w1", pid: "B"
  });

  // 4. Der letzte Haken geht weg: danach darf NUR die eine Zeile fehlen.
  aus.letzterHaken = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"},
             {id:"w1_B", worker_id:"w1", project_id:"B"}],
    lokal: {w1: ["A", "B"]}, mid: "w1", pid: "B"
  });

  // 5. Fremder Mitarbeiter darf nie betroffen sein.
  aus.fremderMa = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"},
             {id:"w9_A", worker_id:"w9", project_id:"A"}],
    lokal: {w1: [], w9: ["A"]}, mid: "w1", pid: "B"
  });

  // 6. Die Zeile war schon weg (ein anderer Admin hat B entfernt), der lokale
  //    Stand glaubt noch daran. Das Abwaehlen trifft damit 0 Zeilen - nichts
  //    ist gelogen, das ist der echte Wettlauf in der anderen Richtung.
  //    Wird das GEMELDET oder verschluckt?
  aus.schonWeg = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"}],
    lokal: {w1: ["A", "B"]}, mid: "w1", pid: "B"
  });

  // 7. Kein Admin: es darf gar nichts passieren (Koeder fuer "der Schnitt
  //    tut ueberhaupt etwas" in die andere Richtung).
  aus.keinAdmin = await lauf({
    server: [{id:"w1_A", worker_id:"w1", project_id:"A"}],
    lokal: {w1: []}, mid: "w1", pid: "B", isWAdm: false
  });

  // 8. Die Verschmelzung beim Laden.
  const leerRls = []; leerRls.__rlsFehler = 403;
  aus.verschmelzen = {
    echteZeilen: verschmelzen([{worker_id:"w1", project_id:"A"}], [], {w1:["X"], w2:["Y"]}),
    leeresArray: verschmelzen([], [], {w1:["X"], w2:["Y"]}),
    rlsLeer:     verschmelzen(leerRls, [], {w1:["X"], w2:["Y"]}),
    nullAntwort: verschmelzen(null, [], {w1:["X"], w2:["Y"]}),
    ausstehend:  verschmelzen([{worker_id:"w1", project_id:"A"}], ["w1"], {w1:["X"]}),
    objektZweig: verschmelzen({w1:["A"]}, [], {w1:["X"], w2:["Y"]}),
    objektLeer:  verschmelzen({}, [], {w1:["X"], w2:["Y"]})
  };

  // 9. KOEDER fuer die Attrappe selbst: ein handgeschriebenes Alles-Loeschen
  //    MUSS die fremde Zeile verlieren. Kann die Attrappe das nicht, sagt
  //    Fall 1 nichts aus.
  {
    const srv = macheServer([{id:"w1_A", worker_id:"w1", project_id:"A"}]);
    global.fetch = srv.fetch;
    await fetch(SB_REST + "/worker_projects?worker_id=eq.w1",
                {method:"DELETE", headers:{}});
    aus.koederAttrappe = {nachher: srv.zeilen, protokoll: srv.protokoll.length};
  }

  process.stdout.write(JSON.stringify(aus));
})().catch(e=>{
  process.stderr.write("PRUEFSTAND GEPLATZT: " + ((e && e.stack) || e));
  process.exit(3);
});
"""


@pytest.fixture(scope="module")
def ergebnis(schnitte):
    prog = (PRUEFSTAND
            .replace("__HELFER__", schnitte["helfer"])
            .replace("__UEBERSETZER__", schnitte["uebersetzer"])
            .replace("__TOGGLE__", schnitte["toggle"])
            .replace("__VERSCHMELZEN__", schnitte["verschmelzen"]))
    tmp = tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w",
                                      encoding="utf-8", newline="")
    try:
        tmp.write(prog)
        tmp.close()
        r = subprocess.run(["node", tmp.name], capture_output=True, text=True,
                           timeout=NODE_TIMEOUT)
        assert r.returncode == 0, (
            "Der Pruefstand ist nicht durchgelaufen - dann ist KEIN Urteil "
            "moeglich (auch kein gruenes).\nstderr:\n%s" % r.stderr[-2500:])
        assert r.stdout.strip(), "Der Pruefstand hat nichts ausgegeben."
        return json.loads(r.stdout)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


# ── Hilfen fuers Urteilen ─────────────────────────────────────────────────

def _pids(zeilen, wid):
    return sorted(r["project_id"] for r in zeilen
                  if str(r.get("worker_id")) == wid)


def _wp(protokoll):
    return [e for e in protokoll if e["tabelle"] == "worker_projects"]


LAEUFE = ("kernfall", "lokalKenntA", "abwaehlen", "letzterHaken", "fremderMa",
          "schonWeg")


def _alle_loescher(ergebnis):
    """Alle DELETE gegen worker_projects aus ALLEN Laeufen.

    Bewusst ueber alle Laeufe und nicht ueber einen: nach dem Umbau loescht
    das Setzen eines Hakens gar nichts mehr, und eine Pruefung, die nur den
    Setz-Fall ansieht, waere dann leer wahr - also gruen, ohne zu messen.
    """
    aus = []
    for name in LAEUFE:
        for x in _wp(ergebnis[name]["protokoll"]):
            if x["methode"] == "DELETE":
                aus.append((name, x))
    return aus


def _luecken(momente, wid):
    """Momente, in denen `wid` keine Zuweisung hat, obwohl vorher und nachher
    eine da ist. Genau das ist das leere Fenster."""
    reihe = [(m["was"], _pids(m["zeilen"], wid)) for m in momente]
    if not reihe or not reihe[0][1] or not reihe[-1][1]:
        return None          # kein Vorher/Nachher -> nicht entscheidbar
    return [was for was, p in reihe[1:-1] if not p]


# ── KOEDER: ohne die sagt keine gruene Zeile hier etwas ───────────────────

def test_koeder_der_pruefstand_stellt_ueberhaupt_anfragen(ergebnis):
    """Wuerde der Uebersetzer-Zweig nicht erreicht, waeren alle zaehlenden
    Pruefungen unten leer und damit gruen. Das ist die haeufigste Form eines
    Riegels, der nichts misst."""
    n = len(_wp(ergebnis["kernfall"]["protokoll"]))
    assert n >= 1, (
        "Der Lauf hat KEINE Anfrage gegen worker_projects gestellt (%d). "
        "Entweder greift der Schnitt nicht oder toggleProj legt keinen "
        "Auftrag ab - in beiden Faellen misst diese Datei nichts." % n)
    assert len(ergebnis["kernfall"]["auftraege"]) >= 1, (
        "toggleProj hat keinen Auftrag in die Warteschlange gelegt.")
    assert ergebnis["kernfall"]["fehler"] is None, (
        "Der Uebersetzer hat geworfen: %r" % ergebnis["kernfall"]["fehler"])


def test_koeder_die_attrappe_kann_eine_fremde_zeile_verlieren(ergebnis):
    """Wenn der nachgebaute Server ein `worker_id=eq.`-DELETE gar nicht
    umsetzt, kann der Kernfall nicht rot werden - er waere gruen, weil die
    Attrappe nichts tut."""
    k = ergebnis["koederAttrappe"]
    assert k["protokoll"] == 1, "Die Attrappe hat die Anfrage nicht protokolliert."
    assert k["nachher"] == [], (
        "Ein DELETE auf worker_id=eq.w1 hat %r stehen gelassen - die Attrappe "
        "kann den Verlust nicht abbilden, also misst der Kernfall nichts."
        % (k["nachher"],))


def test_koeder_der_lueckensucher_findet_eine_luecke():
    """Der Lueckensucher zaehlt. Ein Zaehler, der nie anschlaegt, meldet
    gruen. Also einmal gegen eine gebaute Luecke fahren."""
    gebaut = [
        {"was": "vorher", "zeilen": [{"worker_id": "w1", "project_id": "A"}]},
        {"was": "LUECKE", "zeilen": []},
        {"was": "nachher", "zeilen": [{"worker_id": "w1", "project_id": "A"}]},
    ]
    assert _luecken(gebaut, "w1") == ["LUECKE"], (
        "Der Lueckensucher findet eine gebaute Luecke nicht - dann ist sein "
        "gruenes Urteil am echten Lauf wertlos.")
    heil = [
        {"was": "vorher", "zeilen": [{"worker_id": "w1", "project_id": "A"}]},
        {"was": "ok", "zeilen": [{"worker_id": "w1", "project_id": "A"},
                                  {"worker_id": "w1", "project_id": "B"}]},
        {"was": "nachher", "zeilen": [{"worker_id": "w1", "project_id": "B"}]},
    ]
    assert _luecken(heil, "w1") == [], "Der Lueckensucher meldet Falschalarm."


def test_koeder_ohne_adminrecht_passiert_nichts(ergebnis):
    """Gegenprobe in die andere Richtung: der Schnitt fuehrt den echten
    Rechte-Riegel mit, er ist nicht wegattrappiert."""
    k = ergebnis["keinAdmin"]
    assert k["auftraege"] == [], (
        "Ohne Adminrecht wurde trotzdem ein Auftrag abgelegt: %r"
        % (k["auftraege"],))
    assert _wp(k["protokoll"]) == [], "Ohne Adminrecht ging eine Anfrage raus."


# ── DER BEFUND: der Parallelfall ──────────────────────────────────────────

def test_paralleler_stand_bleibt_erhalten(ergebnis):
    """DER KERN DES DATENVERLUSTS.

    Projekt A steht am Server (ein anderer Admin hat es gesetzt), der lokale
    Stand kennt es nicht. Jetzt wird B gesetzt. HEUTE: das Alles-Loeschen
    nimmt A mit, das Neu-Einfuegen bringt nur B - A ist weg, unangekuendigt.
    NACH DEM UMBAU: nur die Zeile fuer B wird geschrieben, A bleibt stehen.
    """
    e = ergebnis["kernfall"]
    da = _pids(e["endzustand"], "w1")
    assert "A" in da, (
        "DATENVERLUST: Projekt A stand am Server, war lokal unbekannt, und ist "
        "nach dem Setzen von B verschwunden. Endzustand fuer w1: %r.\n"
        "Auftraege: %r\nAnfragen: %s"
        % (da, e["auftraege"],
           [(x["methode"], x["filter"]) for x in _wp(e["protokoll"])]))
    assert "B" in da, "Das neu gesetzte Projekt B ist nicht angekommen: %r" % (da,)


def test_der_gutfall_schreibt_ueberhaupt(ergebnis):
    """KOEDER zum Kernfall. Kaeme hier nichts an, wuerde der Kernfall aus
    einer Menge schliessen, die den Fall nicht enthaelt."""
    da = _pids(ergebnis["lokalKenntA"]["endzustand"], "w1")
    assert da == ["A", "B"], (
        "Auch mit vollstaendigem lokalem Stand steht am Ende %r statt "
        "['A','B'] - dann schreibt der Pfad gar nicht richtig und der "
        "Kernfall misst nichts." % (da,))


def test_kein_leeres_fenster(ergebnis):
    """Zwischen Loeschen und Einfuegen darf es keinen Zeitpunkt geben, an dem
    der Mitarbeiter keine Zuweisung hat. Heute gibt es ihn: das DELETE raeumt
    alles ab, der Upsert kommt erst in einer ZWEITEN HTTP-Anfrage."""
    e = ergebnis["lokalKenntA"]
    luecken = _luecken(e["momente"], "w1")
    assert luecken is not None, (
        "Vorher oder nachher war schon leer - dann ist das leere Fenster hier "
        "nicht entscheidbar. Momente: %r"
        % ([(m["was"], _pids(m["zeilen"], "w1")) for m in e["momente"]],))
    assert luecken == [], (
        "LEERES FENSTER: nach %r hatte w1 keine einzige Zuweisung. Reisst die "
        "Verbindung dort ab, ist der Server leer.\nVerlauf: %r"
        % (luecken,
           [(m["was"], _pids(m["zeilen"], "w1")) for m in e["momente"]]))


def test_abwaehlen_nimmt_nur_die_eine_zeile(ergebnis):
    """B abwaehlen, waehrend A nur am Server steht: B muss weg, A bleiben."""
    da = _pids(ergebnis["abwaehlen"]["endzustand"], "w1")
    assert "A" in da, (
        "Beim Abwaehlen von B ist auch das fremde A verschwunden: %r" % (da,))
    assert "B" not in da, "B wurde nicht abgewaehlt: %r" % (da,)


def test_der_letzte_haken_loescht_nur_seine_zeile(ergebnis):
    """Heute ist genau dieser Fall ein reines Alles-Loeschen: die neue Liste
    ist nicht leer, aber der Weg bleibt derselbe. Gemessen wird die WIRKUNG:
    danach muss A stehen und B fehlen - und zwar OHNE dass A zwischendurch
    weg war."""
    e = ergebnis["letzterHaken"]
    da = _pids(e["endzustand"], "w1")
    assert da == ["A"], "Endzustand %r statt ['A']" % (da,)
    luecken = _luecken(e["momente"], "w1")
    assert luecken == [], (
        "Auch hier klafft ein leeres Fenster: %r\nVerlauf: %r"
        % (luecken, [(m["was"], _pids(m["zeilen"], "w1")) for m in e["momente"]]))


def test_ein_fremder_mitarbeiter_wird_nie_angefasst(ergebnis):
    e = ergebnis["fremderMa"]
    assert _pids(e["endzustand"], "w9") == ["A"], (
        "Die Zuweisung eines ANDEREN Mitarbeiters wurde mitveraendert: %r"
        % (_pids(e["endzustand"], "w9"),))


def test_kein_befehl_trifft_eine_ganze_mitarbeiter_menge(ergebnis):
    """Der Umbau heisst: kein Befehl darf mehr eine ganze Mitarbeiter-Menge
    treffen. Also muss JEDES DELETE die Zeile benennen - ueber `project_id`
    oder ueber `id`. `worker_id=eq.<w>` allein ist der Befund."""
    loescher = _alle_loescher(ergebnis)
    assert loescher, (
        "KOEDER: in KEINEM der %d Laeufe wurde geloescht - dann ist 'kein "
        "breites DELETE' eine leere Aussage. Ein Abwaehlen muss irgendwo eine "
        "Zeile entfernen." % len(LAEUFE))
    breit = [(n, x["filter"]) for n, x in loescher
             if "project_id" not in x["filter"] and "id" not in x["filter"]]
    assert breit == [], (
        "%d von %d DELETE benennen die Zeile nicht, sondern treffen alle "
        "Zeilen des Mitarbeiters: %r. Genau das ist der Datenverlust."
        % (len(breit), len(loescher), breit))


# ── Prefer: count ─────────────────────────────────────────────────────────

def test_das_loeschen_fragt_nach_der_zeilenzahl(ergebnis):
    """Heute fragt das DELETE nicht, wie viele Zeilen es entfernt hat (die
    Kopfzeilen sind `_sbH()` ohne `Prefer`). Der Code koennte hinterher also
    nicht sagen, ob er eine fremde Zuweisung mitgenommen hat."""
    loescher = _alle_loescher(ergebnis)
    assert loescher, (
        "KOEDER: kein einziges DELETE in allen Laeufen - 'alle DELETE tragen "
        "Prefer: count' waere sonst leer wahr.")
    ohne = [(n, x["prefer"]) for n, x in loescher
            if "count" not in (x["prefer"] or "")]
    assert ohne == [], (
        "%d von %d DELETE senden kein `Prefer: count` (%r). Die Zahl der "
        "geloeschten Zeilen kommt damit nicht zurueck."
        % (len(ohne), len(loescher), ohne))


def test_eine_unerwartete_loeschzahl_wird_gemeldet(ergebnis):
    """Die Zeile war schon weg (ein anderer Admin hat sie entfernt): das
    Einzel-DELETE trifft 0 statt 1 Zeile. Das muss SICHTBAR werden - durch
    einen Fehler, eine Meldung oder einen Merker. Stillschweigen ist der
    Ausgangszustand dieses Befunds.

    HEUTE scheitert der Fall schon eine Stufe davor: es gibt ueberhaupt kein
    auf eine Zeile eingeengtes DELETE, dessen Zahl man pruefen koennte.
    """
    e = ergebnis["schonWeg"]
    eng = [x for x in _wp(e["protokoll"])
           if x["methode"] == "DELETE"
           and ("project_id" in x["filter"] or "id" in x["filter"])]
    assert eng, (
        "Es gibt kein auf EINE Zeile eingeengtes DELETE - solange die ganze "
        "Mitarbeiter-Menge geloescht wird, ist die Loeschzahl nicht "
        "auswertbar. Anfragen: %r"
        % ([(x["methode"], x["filter"]) for x in _wp(e["protokoll"])],))
    gemeldet = bool(e["fehler"]) or any(
        art == "error" or "zuweisung" in txt.lower() or "count" in txt.lower()
        for art, txt in e["gemeldet"])
    assert gemeldet, (
        "Das DELETE traf 0 statt der erwarteten Zeile und es wurde NICHTS "
        "gemeldet (fehler=%r, meldungen=%r)." % (e["fehler"], e["gemeldet"]))


def test_keine_doppelten_paare(ergebnis):
    """Ein zeilenweises Einfuegen darf kein zweites (worker_id, project_id)
    anlegen. Welcher eindeutige Schluessel live wirklich greift, ist
    UNGEMESSEN - deshalb messen wir die Wirkung am Endzustand, nicht die
    Kopfzeile."""
    for name in LAEUFE:
        z = ergebnis[name]["endzustand"]
        paare = [(r.get("worker_id"), r.get("project_id")) for r in z]
        assert len(paare) == len(set(paare)), (
            "Fall %s hinterlaesst doppelte Paare: %r" % (name, paare))


# ── Das Ueberspringen leerer Serverantworten ──────────────────────────────
# Diese Faelle sind HEUTE GRUEN. Sie halten fest, was das Ueberspringen
# abfaengt, damit der Umbau es nicht versehentlich mit ausbaut.

def test_leere_serverantwort_laesst_den_lokalen_stand_stehen(ergebnis):
    """`if(wpMap&&Array.isArray(wpMap)&&wpMap.length)` ueberspringt die
    Verschmelzung bei einer LEEREN Antwort. Das ist kein Schoenheitsfehler:
    `_sbGet` gibt bei 401/403 ein leeres Array im ERFOLGSPFAD zurueck
    (v3.9.910, Merker `__rlsFehler`). Ohne das Ueberspringen wuerde ein
    RLS-Ausfall die Zuweisungen aller Mitarbeiter lokal loeschen."""
    v = ergebnis["verschmelzen"]
    assert v["leeresArray"] == {"w1": ["X"], "w2": ["Y"]}, (
        "Eine leere Serverantwort hat den lokalen Stand veraendert: %r"
        % (v["leeresArray"],))
    assert v["rlsLeer"] == {"w1": ["X"], "w2": ["Y"]}, (
        "Ein 401/403 (leeres Array mit __rlsFehler) hat den lokalen Stand "
        "veraendert: %r" % (v["rlsLeer"],))
    assert v["nullAntwort"] == {"w1": ["X"], "w2": ["Y"]}, (
        "Eine null-Antwort (der `.catch(()=>null)` im Ladeeffekt) hat den "
        "lokalen Stand veraendert: %r" % (v["nullAntwort"],))
    assert v["objektLeer"] == {"w1": ["X"], "w2": ["Y"]}, (
        "Ein leeres Objekt hat den lokalen Stand veraendert: %r"
        % (v["objektLeer"],))


def test_echte_zeilen_ersetzen_je_mitarbeiter(ergebnis):
    """KOEDER zum vorigen Fall: kaeme auch mit echten Zeilen nichts an, waere
    'leere Antwort aendert nichts' eine Aussage ueber eine Funktion, die
    ueberhaupt nichts tut."""
    v = ergebnis["verschmelzen"]
    assert v["echteZeilen"] == {"w1": ["A"], "w2": ["Y"]}, (
        "Echte Serverzeilen wirken nicht wie erwartet: %r" % (v["echteZeilen"],))
    assert v["objektZweig"] == {"w1": ["A"], "w2": ["Y"]}, (
        "Der Objektzweig wirkt nicht wie erwartet: %r" % (v["objektZweig"],))


def test_ausstehender_auftrag_wird_uebersprungen(ergebnis):
    """Der Ausstehend-Schutz aus v3.9.938 (`_v938PendingWpWorkers`) - er
    behebt den Datenverlust NICHT, aber er darf beim Umbau nicht verloren
    gehen."""
    v = ergebnis["verschmelzen"]
    assert v["ausstehend"] == {"w1": ["X"]}, (
        "Ein Mitarbeiter mit noch nicht abgeflossenem Auftrag wurde doch "
        "ueberschrieben: %r" % (v["ausstehend"],))


# ── Quelltext-Randbedingungen (keine Wirkungsmessung, nur Rahmen) ─────────

def test_der_auftrag_geht_weiter_ueber_die_warteschlange(ergebnis):
    """Der Umbau darf die Offline-Faehigkeit nicht aufgeben: die Aenderung
    muss weiterhin in die Warteschlange, nicht direkt aufs Netz."""
    a = ergebnis["kernfall"]["auftraege"]
    assert a, "Es wurde kein Auftrag in die Warteschlange gelegt."
    for x in a:
        assert x["url"].startswith("/api/worker-projects"), (
            "Ein Auftrag geht an %r - der Ausstehend-Schutz aus v3.9.938 "
            "erkennt Zuweisungs-Auftraege am Pfadanfang "
            "'/api/worker-projects/'." % (x["url"],))


def test_der_ausstehend_schutz_erkennt_die_neuen_auftraege(roh, ergebnis):
    """Wegriegel. `_v938PendingWpWorkers` fuellt sich aus der Warteschlange
    ueber `_u.indexOf("/api/worker-projects/")===0 && _m==="PUT"`. Legt der
    Umbau seine Auftraege mit einem anderen Verb oder einem laengeren Pfad ab,
    sieht der Schutz sie nicht mehr - und das Neuladen dreht die eigene
    Aenderung wieder zurueck. Der Riegel daneben wuerde davon nichts merken.
    """
    stellen = nur_code_stellen(roh, '_u.indexOf("/api/worker-projects/")===0')
    assert len(stellen) == 1, (
        "Der Ausstehend-Schutz wurde nicht (oder mehrfach) gefunden: %d "
        "Stellen." % len(stellen))
    fenster = roh[stellen[0]:stellen[0] + 260]
    verben = set(re.findall(r'_m==="([A-Z]+)"', fenster))
    assert verben, ("KOEDER: im Fenster des Ausstehend-Schutzes steht kein "
                    "Verb - dann prueft dieser Riegel nichts.")
    gebraucht = {x["method"] for x in ergebnis["kernfall"]["auftraege"]}
    fehlt = gebraucht - verben
    assert not fehlt, (
        "Die Warteschlange traegt Zuweisungs-Auftraege mit %r, der "
        "Ausstehend-Schutz erkennt aber nur %r. Ein Neuladen wuerde die eigene "
        "Aenderung zurueckdrehen." % (sorted(fehlt), sorted(verben)))
    # Der Schutz holt die Mitarbeiter-Id mit `_u.split("/").pop()` - also aus
    # dem LETZTEN Pfadstueck. Haengt der Umbau das Projekt an den Pfad
    # (/api/worker-projects/<mid>/<pid>), merkt sich der Schutz die
    # PROJEKT-Id und schuetzt damit einen Schluessel, den niemand nachfragt.
    # Der Schutz bleibt gruen, das Neuladen dreht die Aenderung zurueck.
    assert '_u.split("/").pop()' in fenster, (
        "Der Schutz liest die Mitarbeiter-Id nicht mehr ueber "
        "`_u.split(\"/\").pop()` - dann gilt die Pfadprobe unten nicht mehr "
        "und muss neu gefasst werden.")
    for x in ergebnis["kernfall"]["auftraege"]:
        letztes = x["url"].rstrip("/").split("/")[-1]
        assert letztes == "w1", (
            "Der Auftrag %r hat als letztes Pfadstueck %r - der "
            "Ausstehend-Schutz merkt sich damit %r statt der Mitarbeiter-Id "
            "'w1'. Die Zuweisung gehoert in den Rumpf, nicht in den Pfad."
            % (x["url"], letztes, letztes))
