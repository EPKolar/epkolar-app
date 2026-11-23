# -*- coding: utf-8 -*-
"""v3.9.1097 (GF 23.11.2026): "Rolle Buero kann die Zeiterfassung der Mitarbeiter nicht bearbeiten".

Ursache: ZeiterfassungView setzte isAdmin = admin || projektleiter. Daran haengen Mitarbeiter-Auswahl,
Alle-Uebersicht, Loeschen fremder Eintraege und Bauwochenbericht -> das Buero sah nur die eigene Woche.
Die DB erlaubte es schon (time_entries: is_staff()/is_hr() enthalten 'buero'), canDo('zeit_delete')
ebenfalls (isB). Fix: buero in dasselbe Tor. Umkehrprobe: der Altstand (Tor ohne buero) faellt durch.
"""
import io
import os
import re

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _ze(src):
    i = src.index("function ZeiterfassungView(")
    j = src.index("\nfunction ", i + 10)
    return src[i:j]


def _tor(ze):
    m = re.search(r"const isAdmin=([^;]+);", ze)
    assert m, "isAdmin-Tor in ZeiterfassungView nicht gefunden"
    return set(re.findall(r'curUser\.role===\x22([a-z]+)\x22', m.group(1)))


def test_buero_im_tor_der_zeiterfassung():
    assert _tor(_ze(_src())) == {"admin", "projektleiter", "buero"}


def test_tor_steuert_auswahl_uebersicht_loeschen():
    ze = _ze(_src())
    assert "if(!isAdmin){return;}" in ze                       # Alle-Uebersicht
    assert "const _canDelEntry=isAdmin||" in ze                 # fremde Eintraege loeschen
    assert "isAdmin?(\r\n          React.createElement('select',{value:selWorker" in ze  # Mitarbeiter-Auswahl


def test_canDo_zeit_delete_kennt_buero_weiter():
    s = _src()
    assert 'if(action==="zeit_delete")return isA||isPL||isB||(isField&&isOwn);' in s


def test_monteur_bleibt_draussen():
    t = _tor(_ze(_src()))
    for r in ("monteur", "helfer", "techniker", "obermonteur", "lagerleitung"):
        assert r not in t


def test_umkehrprobe_altstand_faellt_durch():
    ze = _ze(_src())
    alt = re.sub(r'\|\|curUser\.role===\x22buero\x22(?=;)', "", ze, count=1)
    assert alt != ze
    assert _tor(alt) == {"admin", "projektleiter"}
    assert _tor(alt) != {"admin", "projektleiter", "buero"}
