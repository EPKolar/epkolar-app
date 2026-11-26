# -*- coding: utf-8 -*-
"""Verhaltenstests fuer Luecken aus den Mutationslaeufen B und K (26.11.2026, Stand 3.9.1122).

Die bisherigen Tests zu diesen Stellen waren Textpins (oder rechneten einen Fall, in dem die Mutation
nichts aendert). Die dokumentierte Mutation liess die ganze Suite gruen. Diese Datei fuehrt den
ECHTEN Code aus index.html in node aus und prueft das Verhalten:

- B #30  _sbPatch: HTTP 200 mit leerem Array auf einer Waechter-Tabelle = stille RLS-Abweisung -> Toast + Zaehler.
- B #31  AbsView: Urlaub-Verwaltung (isAdmin/absTabIds) nur admin/PL/buero oder perms 'urlaub_edit', nie Monteur.
- K #6   saveAs: Feldrolle (Monteur/Techniker/Helfer) setzt keine Uhrzeit, auch wenn die Original-Uhrzeit leer ist.
- K #20  _vrNachMonteur: verrechnete Stunden je Monteur ueber mehrere Auftraege SUMMIERT.
- K #21  _vrBezug: ein "erledigt"er Schein gilt NICHT als von OFFA abgerechnet (nur "abgerechnet").
- K #27  Dispo: Feiertag am richtigen Tag (8.12.2026 Di, Fronleichnam 4.6.2026 Do), nicht um einen Tag verschoben.
- K #36  _kioskReloadGuard: die Sperre wird geschrieben -> zweiter Aufruf blockt (keine Reload-Schleife).

Nur Tests; index.html wird nicht veraendert. Die Mutationsprobe je Test steht in
epk-tiefenpruefung-2026-11-26/K_mutation2.md ("Nachschaerfung 26.11.").
"""
import json
import os
import shutil
import subprocess
import tempfile

import pytest

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(not NODE, reason="node fehlt")


def _block(src, kopf, ende):
    assert src.count(kopf) == 1, "Anker nicht eindeutig: " + kopf[:80]
    i = src.index(kopf)
    return src[i:src.index(ende, i + len(kopf)) + len(ende)]


def _node(js):
    """Skript ueber eine Temp-Datei (der Dispo-Block sprengt die Windows-Kommandozeile)."""
    fd, pfad = tempfile.mkstemp(suffix=".js", prefix="zaehne_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(js)
        r = subprocess.run([NODE, pfad], capture_output=True, text=True, encoding="utf-8", timeout=120)
    finally:
        os.remove(pfad)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def _fn(src, name):
    """Top-level-Funktion bis vor die naechste Top-level-Funktion."""
    kopf = "function " + name + "("
    assert src.count("\n" + kopf) == 1, name
    i = src.index("\n" + kopf) + 1
    return src[i:src.index("\nfunction ", i + 10)]


# ── B #30  _sbPatch: stille RLS-Abweisung ───────────────────────────────────
def _sbpatch_lauf(src, faelle):
    code = (_block(src, "const _RLS_SILENT_DENIAL_LABELS=Object.freeze({", "\n});")
            + "\n" + _block(src, "async function _sbPatch(table,id,data){", "\n}"))
    js = r"""
var window={};var toasts=[];window.__toast=function(m,t){toasts.push([m,t]);};
var SB_REST="https://x/rest/v1";var _antwort=null;
async function _dbOhneDateien(t,i,d){return d;}
async function _authRetry(f){return f();}
function _fT(o){return o;} function _sbWH(){return {};} function _sbSelFuer(){return "select=*";}
function _onAuthFail(){}
function fetch(url,o){return Promise.resolve(_antwort);}
%s
(async()=>{
  const F=%s;const out=[];
  for(const f of F){
    toasts=[];delete window.__sbStilleAbweisung;
    _antwort={ok:true,status:200,json:async()=>{if(f.body==="kaputt")throw new Error("no json");return f.body;},text:async()=>""};
    const res=await _sbPatch(f.table,"id1",{a:1});
    out.push({table:f.table,res:res,toasts:toasts.length,typ:toasts[0]?toasts[0][1]:null,
              text:toasts[0]?toasts[0][0]:"",zaehler:window.__sbStilleAbweisung||0});
  }
  console.log(JSON.stringify(out));
})().catch(e=>{console.error(e&&e.stack||e);process.exit(1);});
""" % (code, json.dumps(faelle))
    return _node(js)


@needs_node
def test_b30_sbpatch_meldet_stille_rls_abweisung(index_html):
    faelle = [
        {"table": "fahrzeuge", "body": []},            # 200 + [] auf Waechter-Tabelle -> stille Abweisung
        {"table": "absences", "body": []},
        {"table": "fahrzeuge", "body": [{"id": "id1"}]},  # Zeile zurueck -> echter Erfolg
        {"table": "defects", "body": []},              # bewusst NICHT in der Tafel -> kein Fehlalarm
        {"table": "fahrzeuge", "body": "kaputt"},      # kein JSON -> {ok:1}, kein Alarm
    ]
    r = _sbpatch_lauf(index_html, faelle)
    ab, ab2, ok, frei, kaputt = r
    assert ab["toasts"] == 1 and ab["typ"] == "error" and ab["zaehler"] == 1, ab
    assert "Fahrzeug" in ab["text"] and "NICHT gespeichert" in ab["text"], ab
    assert ab["res"] == [], ab
    assert ab2["toasts"] == 1 and ab2["zaehler"] == 1 and "Urlaub" in ab2["text"], ab2
    assert ok["toasts"] == 0 and ok["zaehler"] == 0 and ok["res"] == [{"id": "id1"}], ok
    assert frei["toasts"] == 0 and frei["zaehler"] == 0, frei
    assert kaputt["toasts"] == 0 and kaputt["res"] == {"ok": 1}, kaputt


# ── B #31  AbsView: Urlaub-Verwaltung je Rolle ─────────────────────────────
ROLLEN = ["admin", "projektleiter", "buero", "obermonteur", "techniker", "monteur", "helfer", "lager_display"]
URLAUB_VERWALTUNG = {"admin", "projektleiter", "buero"}


def _absview_lauf(src, users):
    gate = _block(src, "const isAdmin=(_optionalChain([curUser, 'optionalAccess', _532 => _532.role])===\"admin\"",
                  "hasPerm(curUser,'urlaub_edit');")
    tabs = _block(src, "const absTabIds=isAdmin?[", "];")
    js = r"""
var COLORS=new Proxy({},{get:function(){return "#000";}});
%s
%s
%s
%s
const U=%s;
const out=U.map(function(curUser){%s
%s
return {role:curUser.role,isAdmin:!!isAdmin,tabs:absTabIds};});
console.log(JSON.stringify(out));
""" % (_block(src, "function _optionalChain(ops) {", "return value; }"), _block(src, "const ROLES={", "\n};"), _fn(src, "hasPerm"), "",
       json.dumps(users), gate, tabs)
    return _node(js)


@needs_node
def test_b31_absview_urlaub_verwaltung_je_rolle(index_html):
    users = [{"role": r, "name": "U " + r} for r in ROLLEN]
    users += [{"role": "monteur", "name": "Mit Recht", "permsOverride": {"urlaub_edit": True}},
              {"role": "monteur", "name": "Gesperrt", "locked": True, "permsOverride": {"urlaub_edit": True}},
              {"role": "buero", "name": "Buero ohne", "permsOverride": {"urlaub_edit": False}}]
    r = _absview_lauf(index_html, users)
    for x in r[:len(ROLLEN)]:
        soll = x["role"] in URLAUB_VERWALTUNG
        assert x["isAdmin"] is soll, x
        assert x["tabs"] == (["kalender", "antraege", "uebersicht", "timeline"] if soll else ["kalender"]), x
    mit, gesperrt, buero_ohne = r[len(ROLLEN):]
    assert mit["isAdmin"] is True, "per-User-Recht urlaub_edit muss die Verwaltung oeffnen"
    assert gesperrt["isAdmin"] is False, "gesperrter Benutzer darf trotz Recht nichts verwalten"
    assert buero_ohne["isAdmin"] is True, "buero bleibt per Rolle Verwalter (Rolle vor Override)"


# ── K #6  saveAs: Uhrzeit fuer Feldrollen gesperrt, auch bei leerem Original ─
def _saveas_lauf(src, faelle):
    kopf = "    if(editId){\n      const _origLock=arbeitsscheine.find(a=>a.id===editId)||{};"
    assert src.count(kopf) == 1, "Sperrblock in saveAs nicht eindeutig"
    i = src.index(kopf)
    j = src.index("\n    }\n", src.index("_lockedKeys.forEach(", i))
    seg = src[i:j + 6]
    assert "_FELD_TERMIN" in seg and "_origLock" in seg
    mon = _block(src, "const isMonteurRole=curUser.role===\"monteur\"", ";")
    adm = "const isAdmin=curUser.role===\"admin\"||curUser.role===\"projektleiter\"||curUser.role===\"buero\";"
    assert adm in src, "isAdmin-Definition der Arbeitsschein-Ansicht geaendert"
    js = r"""
function lauf(curUser,arbeitsscheine,editId,form,_asMtLocked){
  %s
  %s
  let _finalForm={...form};
%s
  return _finalForm;
}
const F=%s;
console.log(JSON.stringify(F.map(function(f){return lauf(f.user,f.liste,f.editId,f.form,!!f.locked);})));
""" % (mon, adm, seg, json.dumps(faelle))
    return _node(js)


@needs_node
def test_k6_saveas_feldrolle_setzt_keine_uhrzeit(index_html):
    leer = {"id": "a1", "nummer": "AS-1", "kundName": "Huber", "monteur": "M1",
            "terminBestaetigt": "", "terminZeit": "", "notizen": ""}
    mit = dict(leer, id="a2", terminBestaetigt="2026-12-01", terminZeit="08:00")
    liste = [leer, mit]
    faelle = []
    rollen = ["monteur", "techniker", "helfer", "obermonteur", "admin", "buero", "projektleiter"]
    for r in rollen:
        u = {"role": r, "monteurId": "M1", "name": "X " + r}
        faelle.append({"user": u, "liste": liste, "editId": "a1",
                       "form": dict(leer, terminBestaetigt="2026-12-03", terminZeit="10:30", notizen="neu")})
        faelle.append({"user": u, "liste": liste, "editId": "a2",
                       "form": dict(mit, terminBestaetigt="2026-12-04", terminZeit="11:15", notizen="neu")})
    r = _saveas_lauf(index_html, faelle)
    for k, rolle in enumerate(rollen):
        a_leer, a_mit = r[2 * k], r[2 * k + 1]
        staff = rolle in ("admin", "buero", "projektleiter")
        # freie Felder kommen immer durch
        assert a_leer["notizen"] == "neu" and a_mit["notizen"] == "neu", rolle
        if staff:
            assert (a_leer["terminBestaetigt"], a_leer["terminZeit"]) == ("2026-12-03", "10:30"), (rolle, a_leer)
            assert (a_mit["terminBestaetigt"], a_mit["terminZeit"]) == ("2026-12-04", "11:15"), (rolle, a_mit)
        else:
            # leeres Original bleibt leer - sonst lehnt trg_as_feldrollen_guard den ganzen PUT ab
            assert (a_leer["terminBestaetigt"], a_leer["terminZeit"]) == ("", ""), (rolle, a_leer)
            assert (a_mit["terminBestaetigt"], a_mit["terminZeit"]) == ("2026-12-01", "08:00"), (rolle, a_mit)
    # Monteur darf die Zuweisung nicht aendern, OFFA-Kunde ist fuer alle gesperrt
    z = _saveas_lauf(index_html, [{"user": {"role": "monteur", "monteurId": "M1"}, "liste": liste, "editId": "a1",
                                   "form": dict(leer, monteur="M2", kundName="Anders")},
                                  {"user": {"role": "admin"}, "liste": liste, "editId": "a1",
                                   "form": dict(leer, monteur="M2", kundName="Anders")}])
    assert z[0]["monteur"] == "M1" and z[0]["kundName"] == "Huber", z[0]
    assert z[1]["monteur"] == "M2" and z[1]["kundName"] == "Huber", z[1]


# ── K #20 / #21  Verrechnung ───────────────────────────────────────────────
VR_FUNKTIONEN = ("_vrNorm", "_vrBezug", "_vrSatzWirksam", "_vrIstVerrechnet", "_vrKW", "_vrR",
                 "_vrAuswerten", "_vrNachMonteur", "_vrKennzahlen")


def _vr(src, ausdruck):
    code = "const TIME_DAY=24*60*60*1000;\n" + "\n".join(_fn(src, n) for n in VR_FUNKTIONEN)
    return _node(code + "\nconsole.log(JSON.stringify(" + ausdruck + "));")


@needs_node
def test_k20_vr_nach_monteur_summiert_ueber_auftraege(index_html):
    # m1 arbeitet an zwei Projekten, beide teilweise verrechnet; m2 nur an p2
    e = [{"date": "2026-11-02", "project_id": "p1", "hours": 8, "worker_id": "m1"},
         {"date": "2026-11-16", "project_id": "p1", "hours": 4, "worker_id": "m1"},
         {"date": "2026-11-03", "project_id": "p2", "hours": 6, "worker_id": "m1"},
         {"date": "2026-11-17", "project_id": "p2", "hours": 2, "worker_id": "m1"},
         {"date": "2026-11-04", "project_id": "p2", "hours": 5, "worker_id": "m2"}]
    p = [{"id": "p1", "nr": "PA1", "name": "Halle"}, {"id": "p2", "nr": "PA2", "name": "Schule"}]
    saetze = [{"bezug_typ": "projekt", "bezug_ref": "p1", "verrechnet_bis": "2026-11-10", "voll": False},
              {"bezug_typ": "projekt", "bezug_ref": "p2", "verrechnet_bis": "2026-11-10", "voll": False}]
    a = _vr(index_html, "_vrAuswerten(%s,%s,[],%s)" % (json.dumps(e), json.dumps(p), json.dumps(saetze)))
    m = {x["id"]: x for x in _vr(index_html, "_vrNachMonteur(%s)" % json.dumps(a))}
    # m1: summe 8+4+6+2=20, verrechnet 8 (p1) + 6 (p2) = 14, offen 4+2=6
    assert (m["m1"]["summe"], m["m1"]["verrechnet"], m["m1"]["offen"]) == (20, 14, 6), m["m1"]
    assert (m["m2"]["summe"], m["m2"]["verrechnet"], m["m2"]["offen"]) == (5, 5, 0), m["m2"]
    assert len(m["m1"]["auftraege"]) == 2
    assert sum(x["verrechnet"] for x in m["m1"]["auftraege"]) == m["m1"]["verrechnet"]
    k = _vr(index_html, "_vrKennzahlen(%s)" % json.dumps(a))
    assert k["verrechnet"] == m["m1"]["verrechnet"] + m["m2"]["verrechnet"] == 19


@needs_node
def test_k21_erledigt_ist_nicht_offa_abgerechnet(index_html):
    scheine = [{"id": "s1", "nummer": "AS-1", "kundName": "Huber", "scheinart": "service", "scheinstatus": "erledigt"},
               {"id": "s2", "nummer": "AS-2", "kundName": "Maier", "scheinart": "service", "scheinstatus": "abgerechnet"},
               {"id": "s3", "nummer": "ST-3", "kundName": "Gruber", "scheinart": "stoerung", "scheinstatus": "erledigt"}]
    b = _vr(index_html, "[%s].map(function(e){return _vrBezug(e,[],%s);})" % (
        ",".join(json.dumps({"arbeitsschein_id": s["id"]}) for s in scheine), json.dumps(scheine)))
    assert [x["offa"] for x in b] == [False, True, False], b
    assert [x["typ"] for x in b] == ["as", "as", "stoerung"], b
    e = [{"date": "2026-11-10", "arbeitsschein_id": s["id"], "hours": 3, "worker_id": "m1"} for s in scheine]
    a = {x["ref"]: x for x in _vr(index_html, "_vrAuswerten(%s,[],%s,[])" % (json.dumps(e), json.dumps(scheine)))}
    # erledigt = in der App fertig, aber noch NICHT verrechnet -> bleibt offen
    assert (a["s1"]["offen"], a["s1"]["verrechnet"], a["s1"]["w"]["vorbelegt"]) == (3, 0, False), a["s1"]
    assert (a["s3"]["offen"], a["s3"]["verrechnet"], a["s3"]["w"]["vorbelegt"]) == (3, 0, False), a["s3"]
    assert (a["s2"]["offen"], a["s2"]["verrechnet"], a["s2"]["w"]["vorbelegt"]) == (0, 3, True), a["s2"]


# ── K #27  Dispo: Feiertag am richtigen Tag ────────────────────────────────
def _dispo_tage(src, jetzt_iso, wochen):
    start = src.index("var DISPO_RESERVE_MIN=60;")
    ende = src.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    js = r"""
var AS_GRP_OFFEN=["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"];
const isoWof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%%7);const w=new Date(d.getFullYear(),0,4);return 1+Math.round(((d-w)/864e5-3+(w.getDay()+6)%%7)/7);};
const isoWYof=(dd)=>{const d=new Date(dd);d.setHours(0,0,0,0);d.setDate(d.getDate()+3-(d.getDay()+6)%%7);return d.getFullYear();};
%s
%s
%s
%s
var out=_dispoBuildInput([],[{id:'M1',n:'A',r:'Monteur'}],{},{},new Date(%s),%d);
console.log(JSON.stringify(out.cfg.tage.map(function(t){return {key:t.key,wtag:t.wtag,normMin:t.normMin,feiertag:!!t.feiertag};})));
""" % (_fn(src, "_easterSunday"), _fn(src, "_isATFeiertag"), _fn(src, "_maIstEhemalig"), src[start:ende],
       json.dumps(jetzt_iso), wochen)
    return _node(js)


@needs_node
def test_k27_dispo_feiertag_am_richtigen_tag(index_html):
    # Mo 07.12.2026 -> Woche mit Mariae Empfaengnis (Di 08.12.)
    t = {x["key"]: x for x in _dispo_tage(index_html, "2026-12-07T08:00:00", 1)}
    assert sorted(t) == ["2026-12-07", "2026-12-08", "2026-12-09", "2026-12-10", "2026-12-11"], sorted(t)
    assert t["2026-12-07"] == {"key": "2026-12-07", "wtag": "Mo", "normMin": 510, "feiertag": False}
    assert t["2026-12-08"] == {"key": "2026-12-08", "wtag": "Di", "normMin": 0, "feiertag": True}
    assert t["2026-12-09"] == {"key": "2026-12-09", "wtag": "Mi", "normMin": 510, "feiertag": False}
    assert t["2026-12-11"]["wtag"] == "Fr" and t["2026-12-11"]["normMin"] == 270
    # Fronleichnam Do 04.06.2026 (beweglich, Ostern+60); Fr 05.06. ist normaler halber Tag
    f = {x["key"]: x for x in _dispo_tage(index_html, "2026-06-01T08:00:00", 1)}
    assert f["2026-06-04"] == {"key": "2026-06-04", "wtag": "Do", "normMin": 0, "feiertag": True}
    assert f["2026-06-03"]["normMin"] == 510 and f["2026-06-03"]["feiertag"] is False
    assert f["2026-06-05"]["normMin"] == 270 and f["2026-06-05"]["feiertag"] is False
    assert [k for k, v in f.items() if v["feiertag"]] == ["2026-06-04"]


# ── K #36  Kiosk-Reload-Sperre ─────────────────────────────────────────────
@needs_node
def test_k36_kiosk_reload_sperre_wird_geschrieben(index_html):
    guard = _block(index_html, "window._kioskReloadGuard=function(zielVer){", "\n};")
    silent = _block(index_html, "window._kioskSilentReload=function(zielVer){", "\n};")
    js = r"""
var window={};var _t=1000000;Date.now=function(){return _t;};
var _ls={};var localStorage={getItem:function(k){return k in _ls?_ls[k]:null;},setItem:function(k,v){_ls[k]=String(v);}};
console.error=function(){};console.warn=function(){};
var clears=0;window._forceCacheClear=function(){clears++;};
%s
%s
var r={};
r.erst=window._kioskReloadGuard("3.9.2000");
r.marke=_ls['epk_kiosk_reload_guard']?JSON.parse(_ls['epk_kiosk_reload_guard']):null;
r.sofort=window._kioskReloadGuard("3.9.2000");
_t+=30000; r.gleich30s=window._kioskReloadGuard("3.9.2000");
_t+=1000;  r.andere31s=window._kioskReloadGuard("3.9.2001");
_t+=5000;  r.andere5sSpaeter=window._kioskReloadGuard("3.9.2002");
_t+=11*60000; r.gleich11min=window._kioskReloadGuard("3.9.2001");
_ls={};_t=5000000;
window._kioskSilentReload("3.9.3000");window._kioskSilentReload("3.9.3000");
_t+=60000;window._kioskSilentReload("3.9.3000");
r.clears=clears;
console.log(JSON.stringify(r));
""" % (guard, silent)
    r = _node(js)
    assert r["erst"] is True
    assert r["marke"] == {"ver": "3.9.2000", "ts": 1000000}, r["marke"]
    assert r["sofort"] is False, "Doppelfire binnen 20 s muss blocken"
    assert r["gleich30s"] is False, "derselbe Zielwert binnen 10 min muss blocken (haengende Version)"
    assert r["andere31s"] is True, "neue Zielversion nach 20 s darf laden"
    assert r["andere5sSpaeter"] is False, "Rapid-Sperre gilt auch fuer eine andere Version"
    assert r["gleich11min"] is True, "nach 10 min darf derselbe Zielwert erneut laden"
    assert r["clears"] == 1, "stiller Reload darf in kurzer Folge nur EINMAL Caches leeren/neu laden"
