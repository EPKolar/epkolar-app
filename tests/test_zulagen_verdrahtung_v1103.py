# -*- coding: utf-8 -*-
"""Zulagen-Pruefung 24.11.2026 (GF: "Seite Zulagen pruefen, auch Verknuepfung und Verdrahtung").

Funde und Riegel (jeweils mit Umkehrprobe am Altstand):
1. _ezFetch liefert bei Netz-/Serverfehler still {} -> Tabelle und PZE-PDF rechneten mit der reinen Vorbelegung
   statt der gesetzten Tagesstufen (lohnrelevant). Jetzt Ladezustand ezStand/pzeEzStand: Hinweis, Klick gesperrt,
   PZE-PDF in Zulagen UND Stempelzeiten gesperrt, bis die Stufen des Monats geladen sind. _ezFetch byte-gleich.
2. Untere Monatsnavigation (_shiftYm) zog den Kalender (ezCursor) nicht mit.
3. Wochenansicht ueber den Monatswechsel: Tage des Nachbarmonats zeigten 0 h/Vorschlag und waren klickbar,
   obwohl ihre Stufen nicht geladen sind.
4. Zulagensaetze: system_config schrieb nur der Admin (Probe 24.11.: Buero -> P0001). GF 24.11.: Buero darf die
   Saetze aendern -> DB-Freigabe nur fuer kv_rules (sql/SYSTEM_CONFIG_KV_RULES_BUERO_v1.sql), Maske fuer admin+buero.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(s, name):
    i = s.index("function " + name + "(")
    j = s.index("\nfunction ", i + 10)
    return s[i:j]


def _ohne_kommentare(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def _pruef_ladezustand(kv):
    k = _ohne_kommentare(kv)
    # v3.9.1107: Stand erst ok, wenn Tagesstufen UND Stempeluhr geladen sind
    ok = ("setEzStand((r&&(r.ok||r.missing))&&s.status==='ok'?'ok':'fehler');" in k
          and "disabled:!ezWid||ezStand!=='ok'" in k
          and "onToggle:ezStand==='ok'?_ezToggle:" in k
          and "ezStand==='fehler'?h('div',{role:'alert','data-ez-ladefehler':'1'" in k)
    return ok


def test_1_ladefehler_sperrt_pdf_und_klick():
    assert _pruef_ladezustand(_fn(_src(), "KVZulagenReport"))


def test_1_umkehrprobe():
    kv = _fn(_src(), "KVZulagenReport")
    alt = kv.replace("disabled:!ezWid||ezStand!=='ok'", "disabled:!ezWid", 1)
    assert alt != kv and not _pruef_ladezustand(alt)


def test_1_stempelzeiten_pdf_gesperrt():
    s = _ohne_kommentare(_src())
    assert "setPzeEzStand((r&&(r.ok||r.missing))?'ok':'fehler');" in s
    assert "h('button',{onClick:_pdf,disabled:pzeEzStand!=='ok'," in s


def test_1_ezfetch_unveraendert():
    f = _src()
    i = f.index("async function _ezFetch(ym){")
    j = f.index("async function _ezSet(", i)
    assert "return{ok:false,missing:false,flags:{}};" in f[i:j], "Fehlerfall liefert weiter ok:false - darauf baut ezStand"


def test_2_monatsnavigation_zieht_kalender_mit():
    kv = _ohne_kommentare(_fn(_src(), "KVZulagenReport"))
    m = re.search(r"const _shiftYm=\(delta\)=>\{(.*?)\};", kv)
    assert m and "setEzCursor(nym+'-01');" in m.group(1)
    alt = m.group(1).replace("setEzCursor(nym+'-01');", "")
    assert "setEzCursor" not in alt  # Umkehrprobe: ohne die Zeile fehlt die Kopplung


def test_3_woche_nachbarmonat_nicht_klickbar():
    ez = _ohne_kommentare(_fn(_src(), "EZKalender"))
    assert "if(props.ym)wd=wd.map(function(o){return {iso:o.iso,inMonth:String(o.iso).slice(0,7)===props.ym};});" in ez
    assert "var clickable=inM;" in ez
    kv = _fn(_src(), "KVZulagenReport")
    assert "h(EZKalender,{wid:ezWid,view:ezView,cursor:ezCursor,ym:ym," in kv


def test_4_saetze_nur_admin():
    kv = _ohne_kommentare(_fn(_src(), "KVZulagenReport"))
    # GF 24.11.: Buero darf die Saetze aendern (DB: system_config_kv_rules_buero_v1) - Maske fuer admin UND buero
    assert "!(props.curUser&&(props.curUser.role==='admin'||props.curUser.role==='buero'))?h('span',{'data-ez-saetze-nur-admin':'1'" in kv
    assert "Ändern können Büro und Admin." in kv
