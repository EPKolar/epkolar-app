# -*- coding: utf-8 -*-
"""A55 Runde 3 (Handy 384x752, Stufe schmal, gemeldet an 3.9.1082) - nur Darstellung.

Gesichert (jeder Riegel mit Umkehrprobe):
V1  Mitarbeiter: am Handy kein leerer Platzhalter "Mitarbeiter auswaehlen" unter der Liste
    (wie Administration seit 1080).
P2a Statistik "Tagesaktivitaet": Balkenhoehe in Pixel relativ zum hoechsten Tag (vorher Prozent
    einer Spalte ohne Hoehe -> alle 4 px); die Reihe rollt in einem eigenen Kasten statt der Seite.
P2b Aktivitaets-Feed: OFFA-Zeilen als deutsche Zusammenfassung (Schein-Nr., angenommen/Fehler,
    kurzer Grund), Rohdaten nur fuer Admins hinter "Details". _juprowaPush & Co. unberuehrt.
P3  Rollen-Anzeige ohne Rohschluessel, ACT_LABELS ohne Emoji, Login-Verlauf "Anmeldeart"
    deutsch, Matrix-Spalten nach Bereich geordnet + klebende Koepfe + Knoepfe, Monatsabrechnung
    MA-Filter eigene Zeile, Planung Kennzeichen umbrechend + "Mo .. – Sa ..", Buero-Portal
    Reiter am Handy als Raster.
"""
import io
import json
import os
import re

import pytest

from conftest import run_node_snippet

PFAD = os.path.join(os.path.dirname(__file__), "..", "index.html")


@pytest.fixture(scope="module")
def roh():
    return io.open(PFAD, encoding="utf-8", newline="").read()


def _zwischen(src, a, b):
    i = src.index(a)
    return src[i:src.index(b, i)]


def _akt_helfer(src):
    return _zwischen(src, "function _jpAntwortOk(", "/* A55 Runde 3 (1084) P2-a")


def _balken(src):
    return _zwischen(src, "function _stBalkenHoehe(", "\n")


# ── P2b: Zusammenfassung des Aktivitaets-Feeds ──────────────────────────────
FAELLE = [
    ["juprowa_push", {"nummer": "S075486", "juprowa_id": 5534070,
                      "result": json.dumps({"sd_m": "Error", "sd_d": {"ResponseParams": {"msg": "x"}}})}],
    ["juprowa_push", {"nummer": "S075487", "result": json.dumps({"sd_m": "OK", "sd_d": {"ResponseParams": {"data": {"ID": 5}}}})}],
    ["juprowa_push", {"nummer": "S1", "result": json.dumps({"sd_m": "OK"})}],
    # abgeschnittenes JSON (result.substring(0,500)) -> Regex-Rueckfall
    ["juprowa_push", {"nummer": "S2", "result": '{"sd_m": "Error", "sd_d": {"Respo'}],
    ["juprowa_push_fail", {"nummer": "S3", "grund": "HTTP 500 Internal Server Error"}],
    ["juprowa_push_fail", {"nummer": "S4", "grund": "reset_patch_0_rows"}],
    ["juprowa_push_gesperrt", {"nummer": "S5", "grund": "status_gesperrt"}],
    ["juprowa_pull", {"added": 2, "updated": 5, "errors": 0}],
    ["juprowa_pull", {"added": 0, "updated": 1, "errors": 3}],
    ["juprowa_status_unbekannt", {"nummer": "S6", "code": "77"}],
    ["update", {"feld": "status"}],
]
ERWARTET = [
    {"text": "Schein S075486 an OFFA gesendet – Fehler: OFFA hat den Schein nicht angenommen", "ok": False},
    {"text": "Schein S075487 an OFFA gesendet – angenommen", "ok": True},
    {"text": "Schein S1 an OFFA gesendet – nicht bestätigt", "ok": None},
    {"text": "Schein S2 an OFFA gesendet – Fehler: OFFA hat den Schein nicht angenommen", "ok": False},
    {"text": "Schein S3: Senden an OFFA fehlgeschlagen – OFFA-Server nicht erreichbar", "ok": False},
    {"text": "Schein S4: Senden an OFFA fehlgeschlagen – Rückmeldung konnte nicht gespeichert werden", "ok": False},
    {"text": "Schein S5: Senden an OFFA gesperrt", "ok": False},
    {"text": "OFFA-Abruf: 2 neu, 5 aktualisiert", "ok": True},
    {"text": "OFFA-Abruf: 0 neu, 1 aktualisiert, 3 Fehler", "ok": False},
    {"text": "Schein S6: OFFA meldet einen unbekannten Status (77)", "ok": None},
    None,
]


def _zusammen(node_exe, src):
    js = (_akt_helfer(src) + "\nprocess.stdout.write(JSON.stringify("
          + json.dumps(FAELLE) + ".map(function(f){return _actZusammenfassung(f[0],f[1]);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_feed_zusammenfassung_deutsch(roh, node_exe):
    r = _zusammen(node_exe, roh)
    assert r == ERWARTET, r
    for z in r:
        if z:
            assert "Error" not in z["text"] and "sd_m" not in z["text"] and "juprowa_id" not in z["text"]


def test_umkehr_ok_ohne_id_waere_rot(roh, node_exe):
    """Wer "sd_m OK" schon als angenommen zaehlt, widerspricht der Push-Regel (nur mit ID)."""
    alt = 'if(id!=null&&id!=="")return true;'
    assert _akt_helfer(roh).count(alt) == 1
    kaputt = roh.replace(alt, 'if(id!=null&&id!=="")return true;if(o.sd_m==="OK")return true;', 1)
    assert _zusammen(node_exe, kaputt) != ERWARTET


def test_feed_nutzt_zusammenfassung_details_nur_admin(roh):
    i = roh.index("const _zs=_actZusammenfassung(a.action,det);")
    blk = roh[i:i + 1600]
    assert "curUser&&curUser.role===\"admin\"&&_roh" in blk
    assert "React.createElement('details'" in blk and "\"Details\"" in blk
    # Umkehr: ohne Admin-Bedingung waere der Riegel rot
    assert "curUser&&curUser.role===\"admin\"&&_roh" not in blk.replace("curUser&&curUser.role===\"admin\"&&_roh", "_roh")


def test_protokoll_schreibwege_unberuehrt(roh):
    """Nur Anzeige: die Helfer schreiben nichts und rufen keinen Push."""
    h = _akt_helfer(roh)
    for verboten in ("_sbPost", "_sbPatch", "_juprowaPush", "_juprowaSanitize", "fetch(", "localStorage"):
        assert verboten not in h, verboten


# ── P2a: Balkenhoehe ────────────────────────────────────────────────────────
def _hoehen(node_exe, src, werte):
    js = (_balken(src) + "\nvar w=" + json.dumps(werte) + ";var m=Math.max.apply(null,w);"
          "process.stdout.write(JSON.stringify(w.map(function(x){return _stBalkenHoehe(x,m,80);})));")
    return json.loads(run_node_snippet(node_exe, js))


def test_balken_proportional(roh, node_exe):
    h = _hoehen(node_exe, roh, [18, 32, 31, 11, 8, 0])
    assert h == [45, 80, 78, 28, 20, 2], h
    assert len(set(h[:5])) == 5


def test_umkehr_gleiche_hoehe_waere_rot(roh, node_exe):
    alt = "return Math.max(4,Math.round(Math.min(1,c/m)*px));"
    assert alt in roh
    assert len(set(_hoehen(node_exe, roh.replace(alt, "return 4;", 1), [18, 32, 31]))) == 1


def test_tagesreihe_eigener_rollkasten_und_pixelhoehe(roh):
    blk = _zwischen(roh, "'data-st-tage': \"1\"", "Aktionen/Tag")
    assert 'overflowX:"auto"' in blk
    assert "minWidth:isMob?stats.daily.length*16:0" in blk
    assert "height:h," in blk and 'height:h+"%"' not in blk
    assert "_stBalkenHoehe(d.cnt,maxD,80)" in blk


# ── V1 Mitarbeiter ──────────────────────────────────────────────────────────
def test_mitarbeiter_platzhalter_nicht_am_handy(roh):
    i = roh.index('"Mitarbeiter auswählen" )))')
    vor = roh[max(0, i - 900):i]
    assert ")) : isMob ? null" in vor
    assert roh.count('"Mitarbeiter auswählen" )))') == 1


# ── P3 ──────────────────────────────────────────────────────────────────────
def test_rollen_anzeige(roh, node_exe):
    z = _zwischen(roh, "function _rolleAnzeige(", "\n")
    js = ("var ROLES={admin:{l:'Administrator'}};" + z
          + "\nprocess.stdout.write(JSON.stringify(['admin','lager_display','stempel_terminal','x',''].map(_rolleAnzeige)));")
    assert json.loads(run_node_snippet(node_exe, js)) == ["Administrator", "Lager-Bildschirm", "Stempel-Terminal", "x", "—"]
    assert "text: _rolleAnzeige(u.role)" in roh
    assert "_optionalChain([ROLES, 'access', _229 => _229[u.role]" not in roh
    # ROLES selbst bleibt ohne Kiosk-Eintrag (Module/Rechte unveraendert)
    roles = _zwischen(roh, "const ROLES={", "\n};")
    assert "lager_display" not in roles


def test_act_labels_ohne_emoji(roh):
    z = _zwischen(roh, "const ACT_LABELS={", "};")
    werte = re.findall(r':"([^"]*)"', z)
    assert len(werte) >= 25
    for w in werte:
        assert not re.search("[\U0001F000-\U0001FFFF☀-➿⬀-⯿]", w), w
    assert 'juprowa_push_fail:"OFFA-Senden fehlgeschlagen"' in z
    # Umkehr
    assert re.search("[\U0001F000-\U0001FFFF]", z.replace('login:"Anmeldung"', 'login:"\U0001F7E2 Login"'))


def test_logins_gesamt_null_mit_login_widerspruchsfrei(roh):
    assert '(u.total_logins===0&&u.last_login)?' in roh and '"nicht gezählt"' in roh


def test_module_leerzustand(roh):
    for k in ("module", "benutzer", "aktionen"):
        assert "'data-st-leer': \"%s\"" % k in roh


def test_login_verlauf_anmeldeart(roh):
    assert "'data-l': \"Anmeldeart\"" in roh and "'data-l': \"Auth\"" not in roh
    assert 'm==="gotrue"?"Passwort":"Passwort (alt)"' in roh
    assert "m.toUpperCase()" not in _zwischen(roh, "'data-l': \"Anmeldeart\"", "'data-l': \"Ger")


def test_matrix_spalten_nach_bereich(roh, node_exe):
    a = roh.index("const NOTIF_TYPES={")
    b = roh.index("\n", roh.index("const _NOTIF_SPALTEN="))
    js = (roh[a:b] + "\nvar cats=_NOTIF_SPALTEN.map(function(t){return NOTIF_TYPES[t].cat;});"
          "process.stdout.write(JSON.stringify({cats:cats,n:_NOTIF_SPALTEN.length,alle:Object.keys(NOTIF_TYPES).length}));")
    r = json.loads(run_node_snippet(node_exe, js))
    assert r["n"] == r["alle"]
    # jede Kategorie ein zusammenhaengender Block = passt zum colSpan-Kopf
    bloecke = [c for i, c in enumerate(r["cats"]) if i == 0 or r["cats"][i - 1] != c]
    assert len(bloecke) == len(set(bloecke)), bloecke
    # Umkehr: die alte Reihenfolge (NOTIF_TYPES) ist NICHT blockweise
    js2 = roh[a:b] + "\nprocess.stdout.write(JSON.stringify(Object.keys(NOTIF_TYPES).map(function(t){return NOTIF_TYPES[t].cat;})));"
    alt = json.loads(run_node_snippet(node_exe, js2))
    ab = [c for i, c in enumerate(alt) if i == 0 or alt[i - 1] != c]
    assert len(ab) != len(set(ab))
    assert roh.count("_NOTIF_SPALTEN.map(") == 2


def test_matrix_kopf_klebt_und_knoepfe(roh):
    css = "table.epk-ad-matrix thead tr:nth-child(2) th { position: sticky; top: 40px; z-index: 1; }"
    assert css in roh
    assert "table.epk-ad-matrix thead tr:first-child th { position: sticky; top: 0; z-index: 1; height: 40px;" in roh
    assert 'borderCollapse:"separate",borderSpacing:0' in roh
    assert 'border:"1px solid "+V.bd,borderRadius:6,background:V.bg,color:V.acTx,cursor:"pointer",fontSize:UI.fMeta,fontWeight:600,marginLeft:"auto"' in roh


def test_monatsabrechnung_ma_filter_eigene_zeile(roh):
    assert 'onChange: e=>setSelMA(e.target.value), style: {...II(),flex:isMob?"1 1 100%":1,minWidth:140}' in roh


def test_planung_kennzeichen_umbruch_und_zeitraum(roh):
    i = roh.index("const fzLine=fzKz.length?")
    fz = roh[i:roh.index(":null;", i)]
    assert "textOverflow:'ellipsis'" not in fz and "whiteSpace:'nowrap'" not in fz
    assert "overflowWrap:'anywhere'" in fz
    assert '"Mo ", dateFmt(0), " – Sa "  , dateFmt(5)' in roh


def test_buero_reiter_raster_am_handy(roh):
    assert "'data-bx-reiter':_bxMob?\"raster\":\"leiste\"" in roh
    assert 'gridTemplateColumns:"repeat(3,minmax(0,1fr))"' in roh
