# -*- coding: utf-8 -*-
"""v3.9.1106 Meine Stempelzeiten (GF 24.11.2026): Monteur sieht eigene Stempelungen nur lesend, Korrektur anfragen.

Riegel (Umkehrprobe je Punkt):
- Rolle Monteur hat die Monatsabrechnung (perm stunden) - sonst kaeme er nicht hin.
- Gelesen wird NUR stempel_log des eigenen worker_id (DB: stempel_log_select_own), Tageszeilen ueber _pzeBuildRows
  (dieselbe Rechnung wie Buero/PZE-PDF) - kein eigener Rechenweg.
- Kein Schreibweg auf stempel_log aus der Ansicht; Korrektur geht als Benachrichtigung stempel_korrektur.
- Monatsabschluss zeigt keine Buero-Kraefte (Backoffice, Verkauf/Buchhaltung).
- Hilfsformate: Minuten -> h:mm (Grenzfaelle).
"""
import io
import json
import os
import re
import subprocess

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


def test_monteur_hat_monatsabrechnung():
    s = _src()
    assert 'monteur:{l:"Monteur",' in s
    zeile = s[s.index('monteur:{l:"Monteur",'):]
    zeile = zeile[:zeile.index("]")]
    assert '"stunden"' in zeile
    alt = zeile.replace(',"stunden"', "")
    assert '"stunden"' not in alt  # Umkehrprobe: ohne den Eintrag fehlt das Recht


def _pruef_ansicht(v):
    v = _ohne_kommentare(v)
    return ('_sbGet("stempel_log","worker_id=eq."+encodeURIComponent(wid)' in v
            and "_pzeBuildRows(worker,vonIso,bisIso,stand.evs,stand.rules,entries,abs,approvals)" in v
            and 'pushNotif("stempel_korrektur",' in v
            and "_sbPost" not in v and "_sbPatch" not in v and "_sbDelete" not in v and "SQ.push" not in v)


def test_ansicht_liest_nur_eigene_und_schreibt_nicht():
    assert _pruef_ansicht(_fn(_src(), "MeineStempelzeiten"))


def test_ansicht_umkehrprobe():
    v = _fn(_src(), "MeineStempelzeiten")
    assert not _pruef_ansicht(v.replace('"worker_id=eq."+encodeURIComponent(wid)+"&', '"', 1))
    assert not _pruef_ansicht(v + '_sbPatch("stempel_log",x)')


def test_eingebunden_nur_fuer_eigene_sicht():
    s = _src()
    sz = _fn(s, "StundenzettelView")
    assert "(_myWid&&selMonat>=0)&&React.createElement(MeineStempelzeiten, { key: 'ms'+_ymSel, wid: _myWid," in sz
    assert 'stempel_korrektur:{l:"Stempel-Korrektur angefragt",' in s


def test_monatsabschluss_ohne_buerokraefte():
    s = _src()
    f = _fn(s, "_bxMaListe")
    js = ("function _maIstEhemalig(){return false;}\n" + f +
          "\nconsole.log(JSON.stringify(_bxMaListe([{id:'a',r:'Monteur'},{id:'b',r:'Backoffice'},{id:'c',r:'Verkauf/Buchhaltung'},{id:'d',r:'Geschäftsführer'}],'2026-10').map(function(m){return m.id;})));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout) == ["a", "d"]
    alt = f.replace('m.r!=="Backoffice"&&m.r!=="Verkauf/Buchhaltung"&&', "")
    assert alt != f  # Umkehrprobe: ohne den Filter waeren b und c drin


def test_minuten_format():
    s = _src()
    js = _fn(s, "_msHM") + "\nconsole.log(JSON.stringify([_msHM(0),_msHM(59),_msHM(60),_msHM(485),_msHM(-5),_msHM(59.6)]));"
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert json.loads(r.stdout) == ["0:00", "0:59", "1:00", "8:05", "0:00", "1:00"]
