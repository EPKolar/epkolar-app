# -*- coding: utf-8 -*-
"""v1087 Kameras live in die App (Auftrag Inhaber 21.11.2026 "bring die Kameras endlich live in die App").

KAMERAS_PROD=true. Wirkung (alles in Node gegen den echten Block //@KAMERAS-START..END ausgefuehrt):
  * Admin sieht den Bereich wie bisher (KAMERAS_ADMIN).
  * Projektleitung/Buero/Lagerleitung sehen den Reiter NUR bei system_config kameras_aktiv=true.
  * Monteur und alle anderen Rollen: nie - auch nicht mit kameras_aktiv/Testschalter.
  * Admin-Schalter in Kameras > Einrichtung schreibt kameras_aktiv direkt (_sbUpsert, nicht SyncQueue),
    EIN erst, wenn _kamEinrichtung(...).fertig, mit Bestaetigung; danach wird neu gelesen.
  * Kopf-Chip fuer den Admin: "Für Team freigeschaltet" / "Nur Admin" (ersetzt "Testbetrieb").
Umkehrproben: KAMERAS_PROD=false -> nur Admin; ohne Rollenpruefung -> Monteur waere drin; ohne Fertig-Riegel
-> der EIN-Schalter waere offen.
"""
import itertools
import json

import pytest

from test_kameras_phase1_v1055 import _block, _index, _render_lauf

ROLLEN = ["admin", " Admin ", "projektleiter", "buero", "lagerleitung", "monteur", "helfer", "techniker", "lager_display", None]
AKTIV = [True, "true", '"true"', 1, False, "false", "", None, "__fehlt__"]
TEAM = ("projektleiter", "buero", "lagerleitung")

MATRIX = r"""
const ROLLEN = %(rollen)s, AKTIV = %(aktiv)s;
function cfg(a) { return a === '__fehlt__' ? {} : {kameras_aktiv: a}; }
function nutzer(r) { return r === null ? null : {id: 'x', role: r}; }
function lauf() {
  const o = [];
  ROLLEN.forEach(function (r) { AKTIV.forEach(function (a) {
    o.push({r: r, a: a, s: _kamSchalter(nutzer(r), cfg(a), false), abruf: _kamSchalterAbruf(nutzer(r), false),
            test: _kamSchalter(nutzer(r), Object.assign({kameras_testumgebung: true}, cfg(a)), true)});
  }); });
  return o;
}
OUT.prod = lauf();
KAMERAS_ADMIN = false; OUT.prod_ohne_admin = lauf(); KAMERAS_ADMIN = true;
KAMERAS_PROD = false; OUT.aus = lauf(); KAMERAS_PROD = true;
OUT.anz = [_kamFreigabeAnzeige({stand: 'ok', an: true}, true), _kamFreigabeAnzeige({stand: 'ok', an: false}, true),
           _kamFreigabeAnzeige({stand: 'ok', an: false}, false), _kamFreigabeAnzeige({stand: 'ok', an: true}, false),
           _kamFreigabeAnzeige({stand: 'laedt'}, true), _kamFreigabeAnzeige({stand: 'fehler'}, true),
           _kamFreigabeAnzeige({stand: 'ok', an: false, busy: true}, true)];
KAMERAS_PROD = false; OUT.anz_aus = _kamFreigabeAnzeige({stand: 'ok', an: true}, true); KAMERAS_PROD = true;
OUT.fehler = [_kamFreigabeFehler(new Error('Auth:401')), _kamFreigabeFehler(new Error('HTTP403 x')),
              _kamFreigabeFehler(new Error('HTTP400 {"code":"P0001","message":"Nur Admin darf system_config aendern"}')),
              _kamFreigabeFehler(new Error('Failed to fetch'))];
"""


def _matrix_js():
    return MATRIX % {"rollen": json.dumps(ROLLEN), "aktiv": json.dumps(AKTIV)}


def _erwartet_schalter(r, a, prod=True, admin=True):
    rolle = (r or "").strip().lower()
    wahr = a in (True, "true", '"true"', 1)
    if rolle not in ("admin",) + TEAM:
        return False
    if prod and wahr:
        return True
    return rolle == "admin" and admin


def _erwartet_abruf(r, prod=True, admin=True):
    rolle = (r or "").strip().lower()
    if rolle not in ("admin",) + TEAM:
        return False
    return prod or (rolle == "admin" and admin)


@pytest.fixture(scope="module")
def M(node_exe):
    return _render_lauf(node_exe, _block(), _matrix_js())


def test_produktionsschalter_steht_auf_an():
    b = _block()
    assert b.count("var KAMERAS_PROD=true;") == 1 and "var KAMERAS_PROD=false;" not in b
    assert b.count("var KAMERAS_ADMIN=true;") == 1


def test_rollenmatrix_produktion(M):
    assert len(M["prod"]) == len(ROLLEN) * len(AKTIV)
    for z in M["prod"]:
        assert z["s"] is _erwartet_schalter(z["r"], z["a"]), z
        assert z["abruf"] is _erwartet_abruf(z["r"]), z


def test_team_nur_mit_kameras_aktiv_monteur_nie(M):
    for z in M["prod"]:
        rolle = (z["r"] or "").strip().lower()
        if rolle in TEAM and z["a"] not in (True, "true", '"true"', 1):
            assert z["s"] is False, ("ohne kameras_aktiv nie", z)
        if rolle in TEAM and z["a"] in (True, "true", '"true"', 1):
            assert z["s"] is True, z
        if rolle not in ("admin",) + TEAM:
            assert z["s"] is False and z["abruf"] is False and z["test"] is False, ("nie", z)
        if rolle == "admin":
            assert z["s"] is True, z


def test_admin_ohne_admin_freigabe_folgt_kameras_aktiv(M):
    for z in M["prod_ohne_admin"]:
        assert z["s"] is _erwartet_schalter(z["r"], z["a"], admin=False), z


def test_umkehrprobe_prod_aus_nur_admin(M):
    for z in M["aus"]:
        rolle = (z["r"] or "").strip().lower()
        assert z["s"] is (rolle == "admin"), z
        assert z["abruf"] is (rolle == "admin"), z
    # der Umkehrschluss muss die Produktionsmatrix tatsaechlich unterscheiden, sonst waere der Test blind
    assert [z["s"] for z in M["aus"]] != [z["s"] for z in M["prod"]]


def test_anzeige_und_fehlertexte(M):
    a = M["anz"]
    assert a[0]["chip"] == "Für Team freigeschaltet" and a[0]["an"] is True and a[0]["aktiv"] is True
    assert a[1]["chip"] == "Nur Admin" and a[1]["an"] is False and a[1]["aktiv"] is True
    assert a[2]["aktiv"] is False and a[2]["hinweis"] == "Erst wenn alle Voraussetzungen erfüllt sind."
    assert a[3]["an"] is True and a[3]["aktiv"] is True, "Ausschalten geht immer, auch wenn etwas fehlt"
    assert a[4]["chip"] == "" and a[4]["aktiv"] is False and a[5]["aktiv"] is False and "nicht lesbar" in a[5]["hinweis"]
    assert a[6]["aktiv"] is False, "waehrend des Speicherns gesperrt"
    assert M["anz_aus"] == {"chip": "Nur Admin", "knopf": False, "an": False, "aktiv": False, "hinweis": ""}
    f = M["fehler"]
    assert "Anmeldung abgelaufen" in f[0] and "nur ein Admin" in f[1] and "nur ein Admin" in f[2] and "Netzfehler" in f[3]


# ── Ansicht: Admin-Schalter in Kameras > Einrichtung ──────────────────────────
SZENEN = r"""
function reset(s) { SZENE = s; store.clear(); _kamBackend.fehlt = false; ['get','post','upsert','del','fetch','pruef'].forEach(function (k) { ZAEHL[k].length = 0; }); BEST.length = 0; }
const KAMS = [{id: 'cam1', name: 'Kamera 1', standort: 'Hof', aktiv: true, aufbewahrung_tage: 3}];
const FEHLT = new Error('HTTP404 {"code":"PGRST205"}');
const FN_OK = {status: 200, json: {einrichtung: true, secret: true, basis: 'https://video.example.test/'}};
const BEST = []; let JA = true;
window.confirm = function (t) { BEST.push(t); return JA; };
_sbUpsert = async function (tab, row) {
  ZAEHL.upsert.push({tab: tab, row: row});
  if (SZENE.upsertFehler) throw SZENE.upsertFehler;
  if (tab === 'system_config') SZENE.db.system_config = [{key: row.key, value: row.value}];
  return [row];
};
function wurzel(rolle, ww) { return React.createElement(KameraView, {curUser: {id: 'x', role: rolle, name: 'Anna Admin'}, ww: ww || 1440, users: []}); }
function knoepfe() { return alle(baum, function (n) { return n.tag === 'button'; }); }
function schalter() { return alle(baum, function (n) { return n.tag === 'button' && n.props.role === 'switch'; })[0] || null; }
// v3.9.1099: cfg zaehlt die Abrufe des FREIGABE-Stands (kameras_aktiv/kameras_testumgebung). Die Anordnung
// (system_config.kameras_reihenfolge) lesen bewusst ALLE Kamerarollen beim Laden der Kameras - sie wird
// getrennt als ord gezaehlt und in test_anordnung_wird_gelesen geprueft. Erwartete Zahlen unveraendert.
function cfgGets() { return ZAEHL.get.filter(function (g) { return g.indexOf('system_config') === 0 && g.indexOf('kameras_reihenfolge') < 0; }).length; }
function ordGets() { return ZAEHL.get.filter(function (g) { return g.indexOf('system_config') === 0 && g.indexOf('kameras_reihenfolge') >= 0; }).length; }
function bild() { const s = schalter(); return {text: text(baum), cfg: cfgGets(), ord: ordGets(), upsert: ZAEHL.upsert.slice(), best: BEST.slice(),
  schalter: s ? {text: text(s).trim(), an: s.props['aria-checked'], aus: !!s.props.disabled} : null,
  chip: (alle(baum, function (n) { return n.props && n.props['data-kam-freigabe']; })[0] || null) ? text(alle(baum, function (n) { return n.props && n.props['data-kam-freigabe']; })[0]).trim() : ''}; }
async function drueck(w) { schalter().props.onClick({}); await ruhe(w); }
let w;

// 1) alles fertig, kameras_aktiv fehlt -> Nur Admin; Abbrechen schreibt nichts; Ja schreibt true und liest neu
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK});
w = wurzel('admin'); await ruhe(w); OUT.start = bild();
await klick(w, 'Einrichtung'); OUT.einr = bild();
JA = false; await drueck(w); OUT.abbruch = bild();
JA = true; await drueck(w); OUT.an = bild();
await drueck(w); OUT.aus = bild();
// 1b) am Tablet (kein PC) erreichbar
reset({db: {kameras: KAMS, system_config: [{key: 'kameras_aktiv', value: 'true'}]}, fein: false, einrichtung: FN_OK});
w = wurzel('admin', 800); await ruhe(w); await klick(w, 'Einrichtung'); OUT.tablet = bild();
// 2) Voraussetzungen fehlen -> EIN gesperrt, auch ein erzwungener Klick schreibt nichts
reset({db: {kameras: FEHLT}, fein: true, einrichtung: {status: 404, json: {}}});
w = wurzel('admin'); await ruhe(w); OUT.offen = bild();
await drueck(w); OUT.offen_klick = bild();
// 3) Fehler beim Schreiben
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK, upsertFehler: new Error('HTTP403 {"code":"42501"}')});
w = wurzel('admin'); await ruhe(w); await klick(w, 'Einrichtung'); await drueck(w); OUT.f403 = bild();
reset({db: {kameras: KAMS}, fein: true, einrichtung: FN_OK, upsertFehler: new Error('Failed to fetch')});
w = wurzel('admin'); await ruhe(w); await klick(w, 'Einrichtung'); await drueck(w); OUT.fnetz = bild();
// 4) Stand nicht lesbar
reset({db: {kameras: KAMS, system_config: new Error('HTTP500 x')}, fein: true, einrichtung: FN_OK});
w = wurzel('admin'); await ruhe(w); await klick(w, 'Einrichtung'); OUT.unlesbar = bild();
// 5) Projektleitung mit kameras_aktiv: kein Chip, kein Schalter, kein system_config-Abruf in der Ansicht
reset({db: {kameras: KAMS, system_config: [{key: 'kameras_aktiv', value: 'true'}]}, fein: true});
w = wurzel('projektleiter'); await ruhe(w); OUT.pl = bild();
// 6) Notbremse KAMERAS_PROD=false: kein Schalter, kein Abruf, Chip Nur Admin
KAMERAS_PROD = false;
reset({db: {kameras: KAMS, system_config: [{key: 'kameras_aktiv', value: 'true'}]}, fein: true, einrichtung: FN_OK});
w = wurzel('admin'); await ruhe(w); await klick(w, 'Einrichtung'); OUT.prod_aus = bild();
KAMERAS_PROD = true;
"""


@pytest.fixture(scope="module")
def V(node_exe):
    return _render_lauf(node_exe, _block(), SZENEN)


def test_admin_chip_statt_testbetrieb(V):
    s = V["start"]
    assert s["chip"] == "Nur Admin" and "Testbetrieb" not in s["text"] and s["cfg"] == 1


def test_einschalten_mit_bestaetigung_und_neu_lesen(V):
    e = V["einr"]
    assert "Kameras für Büro/Projektleitung/Lager freigeben" in e["text"]
    assert e["schalter"] == {"text": "Freigabe: Aus – einschalten", "an": "false", "aus": False}
    ab = V["abbruch"]
    assert ab["upsert"] == [] and len(ab["best"]) == 1
    assert ab["best"][0] == ("Ab jetzt sehen Büro, Projektleitung und Lagerleitung die freigegebenen Kameras "
                             "in ihren Zeitfenstern. Fortfahren?")
    an = V["an"]
    assert len(an["upsert"]) == 1
    u = an["upsert"][0]
    assert u["tab"] == "system_config" and u["row"]["key"] == "kameras_aktiv" and u["row"]["value"] == "true"
    assert u["row"]["updated_by"] == "Anna Admin" and u["row"]["updated_at"]
    assert set(u["row"]) == {"key", "value", "updated_at", "updated_by"}, "gleiche Spalten wie kv_rules/stempel_pause_rules"
    assert an["cfg"] > ab["cfg"], "nach dem Speichern neu gelesen"
    assert an["chip"] == "Für Team freigeschaltet" and an["schalter"]["an"] == "true"
    aus = V["aus"]
    assert aus["upsert"][-1]["row"]["value"] == "false" and len(aus["best"]) == 2, "Ausschalten ohne Rueckfrage"
    assert aus["chip"] == "Nur Admin" and aus["schalter"]["an"] == "false"


def test_tablet_erreicht_den_schalter(V):
    t = V["tablet"]
    assert t["schalter"] and t["schalter"]["an"] == "true" and t["chip"] == "Für Team freigeschaltet"


def test_ein_erst_wenn_alles_fertig(V):
    o = V["offen"]
    assert o["schalter"]["aus"] is True and "Erst wenn alle Voraussetzungen erfüllt sind." in o["text"]
    k = V["offen_klick"]
    assert k["upsert"] == [] and k["best"] == []


def test_fehler_deutsch(V):
    assert "nur ein Admin darf die Freigabe umschalten" in V["f403"]["text"] and V["f403"]["chip"] == "Nur Admin"
    assert "Netzfehler" in V["fnetz"]["text"]
    assert V["f403"]["schalter"]["aus"] is False, "nach dem Fehler wieder bedienbar"
    u = V["unlesbar"]
    assert "Freigabe-Stand nicht lesbar" in u["text"] and u["schalter"] is None and "Erneut laden" in u["text"]
    assert u["chip"] == ""


def test_andere_rollen_ohne_schalter_und_ohne_abruf(V):
    p = V["pl"]
    assert p["schalter"] is None and p["chip"] == "" and p["cfg"] == 0 and "freigeben" not in p["text"]


def test_anordnung_wird_gelesen(V):
    # v3.9.1099: jede Kamerarolle liest beim Laden die Anordnung genau einmal (PL wie Admin)
    assert V["pl"]["ord"] == 1 and V["start"]["ord"] >= 1


def test_notbremse_prod_aus(V):
    p = V["prod_aus"]
    assert p["schalter"] is None and p["cfg"] == 0 and p["chip"] == "Nur Admin"


def test_schreibweg_direkt_nicht_syncqueue():
    b = _block()
    i = b.index("async function _kamFreigabeSchreiben(")
    t = b[i:b.index("\n}", i)]
    assert "_sbUpsert('system_config'" in t and "SyncQueue" not in t and "_sqEnqueue" not in t


def test_app_reiter_haengt_weiter_am_schalter():
    s = _index()
    assert s.count('if(t.perm==="kameras")return _kamFlag&&!!_kamRolle(curUser);') == 1
    i = s.index("const [_kamFlag,_setKamFlag]=_react.useState.call(void 0, false);")
    teil = s[i:s.index("const _bauproNowYr=", i)]
    assert teil.index("_kamSchalterAbruf(curUser,_lokal)") < teil.index("_kamLadeSchalter()")


def _mut(alt, neu):
    b = _block()
    assert b.count(alt) == 1, alt
    return b.replace(alt, neu, 1)


def test_umkehrprobe_ohne_rollenliste_waere_monteur_drin(node_exe):
    R2 = _render_lauf(node_exe, _mut("return KAMERA_ROLLEN.indexOf(r)>=0?r:'';", "return r;"), _matrix_js())
    assert any(z["r"] == "monteur" and z["s"] is True for z in R2["prod"]), "Umkehrprobe: 'Monteur nie' waere blind"


def test_umkehrprobe_ohne_fertig_riegel_waere_ein_offen(node_exe):
    kaputt = _mut("aktiv:fertig===true&&frei.busy!==true", "aktiv:frei.busy!==true")
    alt = "if(an&&!(einr&&einr.fertig)){"
    assert kaputt.count(alt) == 1
    kaputt = kaputt.replace(alt, "if(false){", 1)
    R2 = _render_lauf(node_exe, kaputt, SZENEN)
    assert R2["offen"]["schalter"]["aus"] is False and len(R2["offen_klick"]["upsert"]) == 1
