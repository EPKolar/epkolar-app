# -*- coding: utf-8 -*-
"""Trennung Stempeluhr (A, Lohn, Minuten, stempel_log) / Zeiterfassung (B, Verrechnung, Stunden, time_entries).

Befund: C:/repos/epk-trennung-befund.md (24.11.2026). Geprueft mit den echten Funktionen (Node), je Regel eine
Umkehrprobe, die auf dem alten bzw. falschen Code rot wird:
- Verrechnung liest nur time_entries (kein stempel_log, keine Minutenfelder der PZE).
- Monatsabschluss-Chip "Verrechnung offen": App-entries (_mapEntry: p/pid statt project_id) muessen dem
  Projekt zugeordnet werden - vorher landeten sie als Freitext und Projekt-Saetze griffen nicht.
- PZE: Anwesenheit aus stempel_log (Minuten), Projektzeit getrennt (Stunden*60) - Einheitengrenze.
- Entfernungszulage-Vorbelegung erwartet STUNDEN (>6); Minuten waeren ein Einheitenfehler.
Bewusst NICHT geprueft (nicht wahr, Entscheidung beim Inhaber): Zulagen aus stempel_log.
"""
import io
import json
import os
import subprocess

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(s, name):
    i = s.index("function " + name + "(")
    ends = [x for x in (s.find("\nfunction ", i + 10), s.find("\nasync function ", i + 10),
                        s.find("\nvar ", i + 10), s.find("\nif(typeof window", i + 10)) if x > 0]
    return s[i:min(ends)]


def _node(code, ausdruck):
    r = subprocess.run(["node", "-e", code + "\nconsole.log(JSON.stringify(" + ausdruck + "));"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


VR = ("_vrNorm", "_vrBezug", "_vrSatzWirksam", "_vrIstVerrechnet", "_vrKW", "_vrR", "_vrAuswerten", "_vrNachMonteur")
ALT_BEZUG = 'var pid=String(e.project_id||e.projekt||"").trim();'
NEU_BEZUG = 'var pid=String(e.project_id||e.projekt||e.p||e.pid||"").trim();'


def _vr_code(s):
    return "const TIME_DAY=24*60*60*1000;\n" + "\n".join(_fn(s, n) for n in VR)


# App-entries wie _mapEntry sie liefert (kein project_id/worker_id), Projekt p1 voll verrechnet
APP_E = [{"id": "e1", "p": "p1", "pid": "p1", "w": "w1", "worker": "w1", "date": "2026-11-10", "datum": "2026-11-10",
          "hours": 8, "stunden": 8, "task": "Montage", "taetigkeit": "Montage", "arbeitsschein_id": ""}]
P = [{"id": "p1", "nr": "PA1", "name": "Halle"}]
SATZ = [{"bezug_typ": "projekt", "bezug_ref": "p1", "voll": True, "verrechnet_bis": None}]
AUSDRUCK = "_vrNachMonteur(_vrAuswerten(%s,%s,[],%s,[]))" % (json.dumps(APP_E), json.dumps(P), json.dumps(SATZ))


def test_monatsabschluss_verrechnung_ordnet_app_entries_dem_projekt_zu():
    s = _src()
    assert s.count(NEU_BEZUG) == 1
    r = _node(_vr_code(s), AUSDRUCK)
    assert r[0]["id"] == "w1" and r[0]["offen"] == 0 and r[0]["verrechnet"] == 8
    assert r[0]["auftraege"][0]["typ"] == "projekt"


def test_umkehrprobe_alter_bezug_macht_projekt_zu_freitext():
    code = _vr_code(_src())
    assert code.count(NEU_BEZUG) == 1
    r = _node(code.replace(NEU_BEZUG, ALT_BEZUG), AUSDRUCK)
    assert r[0]["offen"] == 8 and r[0]["auftraege"][0]["typ"] == "freitext", "alter Code muss rot sein"


VERBOTEN_IN_VERRECHNUNG = ("stempel_log", "nettoMin", "_pzeBuildRows", "_pzeTagRow", "evs")


def _verrechnung_frei_von_stempel(text):
    return [w for w in VERBOTEN_IN_VERRECHNUNG if w in text]


def test_verrechnung_liest_keine_stempelzeit():
    s = _src()
    for n in VR + ("VerrechnungView", "_vrLadeSaetze", "_vrLadeHaken"):
        assert _verrechnung_frei_von_stempel(_fn(s, n)) == [], n
    # Umkehrprobe: der Pruefer schlaegt an, wenn Stempelzeit hineingemischt wird
    kaputt = _fn(s, "_vrAuswerten").replace("var h=parseFloat(e.stunden||e.hours)||0;",
                                             "var h=parseFloat(e.stunden||e.hours||(e.nettoMin/60))||0;")
    assert _verrechnung_frei_von_stempel(kaputt) == ["nettoMin"]


def test_verrechnung_summe_gleich_summe_der_eintraege_in_stunden():
    e = [{"date": "2026-11-10", "project_id": "p1", "arbeitsschein_id": "", "hours": 7.5, "worker_id": "w1"},
         {"date": "2026-11-11", "project_id": "", "arbeitsschein_id": "s1", "hours": 0.25, "worker_id": "w1"}]
    r = _node(_vr_code(_src()), "_vrAuswerten(%s,%s,[],[],[]).reduce(function(a,x){return a+x.summe;},0)" % (json.dumps(e), json.dumps(P)))
    assert abs(r - 7.75) < 1e-9


def _pze_code(s, mutation=None):
    fn = _fn(s, "_pzeTagRow")
    if mutation:
        assert fn.count(mutation[0]) == 1
        fn = fn.replace(*mutation)
    stubs = ("function _stPairEvents(){return [];}function _stRoundGehen(x){return x;}function _stRoundKommen(x){return x;}"
             "function _stTagNetto(){return 0;}function _pzeUngerade(){return false;}function _pzeAutoPause(){return false;}\n")
    return stubs + fn


def test_pze_projektzeit_stunden_mal_60_getrennt_von_anwesenheit():
    r = _node(_pze_code(_src()), "_pzeTagRow([], 'monteur', {}, 8.5, 7.5, false)")
    assert r["projMin"] == 450 and r["nettoMin"] == 0 and r["sollMin"] == 510


def test_umkehrprobe_pze_einheit_ohne_mal_60():
    r = _node(_pze_code(_src(), ("projMin:Math.round((projStd||0)*60)", "projMin:Math.round((projStd||0))")),
              "_pzeTagRow([], 'monteur', {}, 8.5, 7.5, false)")
    assert r["projMin"] != 450, "Einheitenfehler muss auffallen"


def test_pze_pdf_anwesenheit_aus_stempel_log():
    s = _src()
    pdf = _fn(s, "_pzePdf")
    assert "_sbGet('stempel_log'" in pdf and "_pzeBuildRows(worker,von,bis,evs," in pdf
    assert "r.ez=(r.nettoMin>360);" in _fn(s, "_pzeBuildRows")


def test_ez_vorbelegung_erwartet_stunden_grenze_6():
    s = _src()
    code = _fn(s, "_ezDayEff")
    r = _node(code, "[_ezDayEff(6,undefined,false),_ezDayEff(6.25,undefined,false),_ezDayEff(360,undefined,false),_ezDayEff(0.5,undefined,false)]")
    # 6 h -> nein, 6,25 h -> klein; 360 (Minuten statt Stunden) wuerde faelschlich klein -> Eingang muss Stunden sein
    assert r == ["", "klein", "klein", ""]
    # v3.9.1107 GF 24.11. "Zulage auf Stempeluhr": die Tagesmenge kommt jetzt aus nettoMin - Eingang muss trotzdem STUNDEN sein
    for n in ("_ezTageAusStempel", "_pzePdf"):
        f = _fn(s, n)
        assert "Math.round(r.nettoMin/60*100)/100" in f, n + ": Minuten muessen in Stunden umgerechnet werden"
    assert "_ezTageAusStempel(stz&&stz.evs" in _fn(s, "_bxMaStand")


def test_monatsabschluss_chip_heisst_projektstunden():
    f = _fn(_src(), "MonatsabschlussView")
    assert 'chip("Projektstunden "' in f and 'chip("Stunden "' not in f
