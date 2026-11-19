# -*- coding: utf-8 -*-
"""v3.9.1069 - zwei Anzeige-Fixes, mit echtem Code aus index.html in node gerechnet.

1) Administration > Statistiken: jede Zeile "Inaktiv" und "Logins gesamt 0".
   Gemessen 19.11. (read-only, nur Zaehlungen): users 10, active=1 bei 10 (Spalte integer), last_login bei 9,
   login_count > 0 bei 9 (Summe 288); activity_log login in 30 Tagen: 8 Zeilen von 1 Benutzer.
   Ursache: die Tabellenzeilen wurden ohne active/locked gebaut (u.active immer undefined -> "Inaktiv"),
   und "Logins gesamt" zaehlte nur activity_log der letzten 30 Tage statt users.login_count.
   Fix: _stBenutzerZeile liest active/locked/login_count aus einem eigenen users-Lesen, typ-unabhaengig;
   nicht lesbar (401/403/Netz, _rlsLeer) -> null -> "Nicht lesbar" bzw. "—", nie "Inaktiv"/0.
2) Wechselkennzeichen: BMW X5 "TU-266BP (X5)" und Mercedes CL 500 "TU-266BP". Dispo/Wochenplan kuerzten auf das
   erste Wort -> zweimal "TU-266BP". _fzKzAnzeige haengt bei zwei AKTIVEN Fahrzeugen mit gleichem Kurzkennzeichen
   " · Modell" (sonst Marke) an. Exporte behalten das rohe Kennzeichen.
"""
import json
import os
import re
import subprocess
import tempfile

from conftest import EPK_TEST_TIMEOUT


def _zeile(src, anfang):
    assert src.count(anfang) == 1, anfang
    i = src.index(anfang)
    return src[i:src.index("\n", i)].rstrip("\r")


def _block(src, anfang):
    assert src.count(anfang) == 1, anfang
    i = src.index(anfang)
    m = re.compile(r"\r?\n\}\r?\n").search(src, i)
    return src[i:m.end()]


def _node(node_exe, prog):
    fd, p = tempfile.mkstemp(suffix=".js")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(prog)
    try:
        r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8", timeout=EPK_TEST_TIMEOUT)
    finally:
        os.unlink(p)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def _helfer(src):
    return "\n".join([
        _zeile(src, "function _rlsLeer(liste){"),
        _zeile(src, "function _stJaNein(v){"),
        _block(src, "function _stBenutzerZeile(u,roh,lastL,totL,alUnlesbar){"),
        _zeile(src, "function _fzArchiviert(f){"),
        _zeile(src, "function _fzKzKurz(kz){"),
        _zeile(src, "function _fzKzAktiv(f){"),
        _zeile(src, "function _fzKzAnzeige(f,alle,kurz){"),
        _zeile(src, "function _fzKzAnzeigeVon(fid,roh,alle){"),
    ])


# ══ 1. Statistik ═══════════════════════════════════════════════════════════════

STAT = r"""
const U = {id: 'u1', name: 'A', username: 'a', role: 'admin', last_login: '2026-11-17T14:38:29Z'};
const echt = [{id: 'u1', active: 1, locked: 0, login_count: 37, last_login: '2026-11-17T14:38:29Z'}];
const leer403 = []; leer403.__rlsFehler = 403;
const netz = []; netz.__rlsFehler = -1;
const out = {
  ja: [true, 1, '1', 'true', 't', ' T ', 'TRUE'].map(_stJaNein),
  nein: [false, 0, '0', 'false', 'f'].map(_stJaNein),
  unbekannt: [undefined, null, '', 'x', 2].map(_stJaNein),
  echt: _stBenutzerZeile(U, echt, {}, {}, false),
  text_t: _stBenutzerZeile(U, [{id: 'u1', active: 't', locked: 'f', login_count: '5'}], {}, {}, false),
  inaktiv: _stBenutzerZeile(U, [{id: 'u1', active: 0, locked: 0, login_count: 2}], {}, {}, false),
  gesperrt: _stBenutzerZeile(U, [{id: 'u1', active: 1, locked: true, login_count: 2}], {}, {}, false),
  r403: _stBenutzerZeile(U, leer403, {}, {u1: 4}, false),
  netz: _stBenutzerZeile(U, netz, {}, {}, false),
  fehlt: _stBenutzerZeile(U, [{id: 'u9', active: 1, login_count: 3}], {}, {}, false),
  ohne_spalte: _stBenutzerZeile(U, [{id: 'u1'}], {}, {}, false),
  dreissig_mehr: _stBenutzerZeile(U, [{id: 'u1', active: 1, login_count: 1}], {u1: '2026-11-18T08:00:00Z'}, {u1: 3}, false),
  al_unlesbar: _stBenutzerZeile(U, echt, {u1: '2026-11-18T08:00:00Z'}, {u1: 99}, true),
  id_zahl: _stBenutzerZeile({id: 7}, [{id: '7', active: '1', login_count: 1}], {}, {}, false)
};
console.log(JSON.stringify(out));
"""


def _stat(node_exe, src):
    return _node(node_exe, _helfer(src) + STAT)


def test_aktiv_typ_unabhaengig_und_unbekannt_bleibt_unbekannt(node_exe, index_html):
    r = _stat(node_exe, index_html)
    assert r["ja"] == [True] * 7 and r["nein"] == [False] * 5 and r["unbekannt"] == [None] * 5


def test_echte_datenlage_zeigt_aktiv_und_gesamtzahl(node_exe, index_html):
    r = _stat(node_exe, index_html)
    e = r["echt"]
    assert e["active"] is True and e["locked"] is False and e["total_logins"] == 37 and e["lesbar"] is True
    assert e["last_login"] == "2026-11-17T14:38:29Z"
    assert r["text_t"]["active"] is True and r["text_t"]["locked"] is False and r["text_t"]["total_logins"] == 5
    assert r["inaktiv"]["active"] is False and r["gesperrt"]["locked"] is True
    assert r["id_zahl"]["active"] is True


def test_nicht_lesbar_ist_nicht_inaktiv(node_exe, index_html):
    r = _stat(node_exe, index_html)
    for k in ("r403", "netz", "fehlt", "ohne_spalte"):
        assert r[k]["active"] is None, k
        assert r[k]["locked"] is None, k
    for k in ("r403", "netz", "fehlt"):
        assert r[k]["total_logins"] is None and r[k]["lesbar"] is False, k
    assert r["r403"]["last_login"] == "2026-11-17T14:38:29Z", "Rueckfall auf den Benutzerstempel"


def test_gesamtzahl_und_letzter_login(node_exe, index_html):
    r = _stat(node_exe, index_html)
    d = r["dreissig_mehr"]
    assert d["total_logins"] == 3, "30-Tage-Zaehlung groesser als login_count -> die groessere Zahl"
    assert d["last_login"] == "2026-11-18T08:00:00Z", "der spaetere der beiden Zeitpunkte"
    a = r["al_unlesbar"]
    assert a["total_logins"] == 37 and a["last_login"] == "2026-11-17T14:38:29Z", "unlesbares activity_log zaehlt nicht mit"


def test_umkehrprobe_ohne_users_lesen_waere_alles_unbekannt(node_exe, index_html):
    """Bricht man die Zuordnung zur users-Zeile (alter Zustand: Felder fehlen), ist active nicht mehr wahr."""
    alt = "if(roh[i]&&String(roh[i].id)===id){r=roh[i];break;}"
    assert index_html.count(alt) == 1
    r = _stat(node_exe, index_html.replace(alt, "", 1))
    assert r["echt"]["active"] is not True and r["echt"]["total_logins"] is None


def test_verdrahtung_statistik(index_html):
    assert index_html.count('_sbGetUsersSafe("").catch(e=>_eskLeseMarke(e))') == 1
    assert "notifs,logRows,actRows,usrRoh]=await Promise.all([" in index_html
    # Tablet-Runde 1077 (4): hinter der Zeile steht jetzt actions_7d (vorher nie gesetzt, "Aktionen (7T)" immer 0)
    assert "..._stBenutzerZeile(u,usrRoh,_lastL,_totL,_alUnlesbar),actions_7d:_alUnlesbar?null:(_a7[String(u.id)]||0)}));" in index_html
    i = index_html.index("const _alUnlesbar=_rlsLeer(actRows)||_rlsLeer(logRows);")
    assert i < index_html.index("..._stBenutzerZeile(u,usrRoh,_lastL,_totL,_alUnlesbar)"), "erst die Lese-Marke, dann die Zeilen"
    assert 'u.active===false?React.createElement(Badge, { text: "Inaktiv"' in index_html
    assert 'React.createElement(Badge, { text: "Nicht lesbar", color: COLORS.NEUTRAL} )' in index_html
    assert 'u.total_logins==null?"—":u.total_logins' in index_html
    assert "u.total_logins||0" not in index_html, "Umkehrprobe: unbekannt darf nicht als 0 erscheinen"
    assert ':u.active?React.createElement(Badge, { text: "Aktiv"' not in index_html


def test_mapuser_aktiv_typ_unabhaengig(node_exe, index_html):
    fn = _block(index_html, "function _mapUser(u){")
    prog = ("function _jo(x){return x;}function _jp(x){return x;}function _vwTagLokal(x){return x||'';}\n" + fn +
            "\nconsole.log(JSON.stringify([1,'1',true,'true','t',0,'0',false,'f',null,undefined].map(function(v){"
            "var m=_mapUser({id:'u',active:v,locked:v});return [m.active,m.locked];})));")
    r = _node(node_exe, prog)
    assert [x[0] for x in r] == [True, True, True, True, True, False, False, False, False, False, False]
    assert r == [[x[0], x[0]] for x in r]


# ══ 2. Wechselkennzeichen ══════════════════════════════════════════════════════

KZ = r"""
const L = [{id: 'fz1', kennzeichen: 'TU-266BP', marke: 'Mercedes', modell: 'CL 500', status: 'aktiv'},
           {id: 'fz1b', kennzeichen: 'TU-266BP (X5)', marke: 'BMW', modell: 'X5', status: 'aktiv'},
           {id: 'fz2', kennzeichen: 'TU-516CP', marke: 'Ford', modell: 'Transit', status: 'aktiv'}];
const arch = L.map(function (f) { return f.id === 'fz1b' ? Object.assign({}, f, {archiviert_am: '2026-11-19'}) : f; });
const still = L.map(function (f) { return f.id === 'fz1b' ? Object.assign({}, f, {status: 'stillgelegt'}) : f; });
const ohneModell = [Object.assign({}, L[0], {modell: ''}), L[1]];
const alt = function (f) { return (f.kennzeichen || '').split(' ')[0] || f.kennzeichen || ''; };
console.log(JSON.stringify({
  voll: L.map(function (f) { return _fzKzAnzeige(f, L); }),
  kurz: L.map(function (f) { return _fzKzAnzeige(f, L, true); }),
  arch: arch.map(function (f) { return [_fzKzAnzeige(f, arch), _fzKzAnzeige(f, arch, true)]; }),
  still: still.map(function (f) { return _fzKzAnzeige(f, still, true); }),
  marke: _fzKzAnzeige(ohneModell[0], ohneModell),
  ohneListe: [_fzKzAnzeige(L[1]), _fzKzAnzeige(L[1], null, true), _fzKzAnzeige(null, L)],
  von: [_fzKzAnzeigeVon('fz1b', 'TU-266BP (X5)', L), _fzKzAnzeigeVon('weg', 'ROH', L)],
  gross: _fzKzAnzeige({id: 'a', kennzeichen: 'tu-266bp', modell: 'Y'}, [{id: 'a', kennzeichen: 'tu-266bp'}, L[0]]),
  alt: L.map(alt)
}));
"""


def test_wechselkennzeichen_unterscheidbar(node_exe, index_html):
    r = _node(node_exe, _helfer(index_html) + KZ)
    assert r["voll"] == ["TU-266BP · CL 500", "TU-266BP · X5", "TU-516CP"]
    assert r["kurz"] == ["TU-266BP · CL 500", "TU-266BP · X5", "TU-516CP"]
    assert r["marke"] == "TU-266BP · Mercedes"
    assert r["von"] == ["TU-266BP · X5", "ROH"]
    assert r["gross"] == "tu-266bp · Y", "Gross/klein egal, gleiche id zaehlt nicht doppelt"


def test_nur_aktive_zaehlen_sonst_wie_bisher(node_exe, index_html):
    r = _node(node_exe, _helfer(index_html) + KZ)
    assert r["arch"] == [["TU-266BP", "TU-266BP"], ["TU-266BP (X5)", "TU-266BP"], ["TU-516CP", "TU-516CP"]]
    assert r["still"] == ["TU-266BP", "TU-266BP", "TU-516CP"]
    assert r["ohneListe"] == ["TU-266BP (X5)", "TU-266BP", ""]


def test_umkehrprobe_alte_kuerzung_macht_beide_gleich(node_exe, index_html):
    r = _node(node_exe, _helfer(index_html) + KZ)
    assert r["alt"][0] == r["alt"][1] == "TU-266BP", "so sah der Befund aus"
    assert r["kurz"][0] != r["kurz"][1]
    kaputt = index_html.replace("if(!dop)return basis;", "return basis;", 1)
    assert kaputt != index_html
    k = _node(node_exe, _helfer(kaputt) + KZ)
    assert k["kurz"][0] == k["kurz"][1], "ohne die Doppelt-Pruefung waere der Test rot"


def test_anzeige_stellen_verdrahtet_und_exporte_roh(index_html):
    assert "split(' ')[0]||f.kennzeichen" not in index_html and 'split(" ")[0]||f.kennzeichen' not in index_html
    assert 'split(" ")[0]||(f.kennzeichen' not in index_html
    for teil in ("_tfEt('transporter',_fzKzAnzeige(f,fahrzeuge,true))", "return f?_fzKzAnzeige(f,_fzWpAlle,true):null;",
                 "kz:_fzKzAnzeige(f,_fzWpAlle,true),", 'text:"Pickerl "+_fzKzAnzeige(f,fahrzeuge)',
                 'text:"Service "+_fzKzAnzeige(f,fahrzeuge)', "return {label:_fzKzAnzeige(f,fahrzeuge),",
                 'Pickerl "+(_fzKzAnzeige(f,_fahrzeuge)||f.kennzeichen||f.id||"Fzg")',
                 '((f&&f.kennzeichen)?_fzKzAnzeige(f,fahrzeuge):"(ohne KZ)")',
                 "_fzKzAnzeigeVon(x.fid,x.kennzeichen,fahrzeuge)"):
        assert index_html.count(teil) == 1, teil
    # Exporte/Etiketten: rohes Kennzeichen
    assert "var z=sicht.map(function(x){return [x.kennzeichen,modellVon(x.fid)" in index_html
    assert "code:f.kennzeichen,kennzeichen:f.kennzeichen" in index_html
    assert "f.kennzeichen||'',((f.marke||'')+' '+(f.modell||'')).trim(),String(t.anzahl)" in index_html
