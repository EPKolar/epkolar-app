# -*- coding: utf-8 -*-
"""v3.9.1110 GF 24.11. "Zucken der Kameras ist noch da".

Ursache: Der 1105-Puffer lud das Einzelbild unsichtbar per new Image() vor, setzte danach aber die Quelle am SICHTBAREN
<img>. Liefert die Kamera ohne Zwischenspeicher, laedt der Browser dort ein zweites Mal - das sichtbare Bild ist kurz leer.
Jetzt zwei Ebenen: das sichtbare Bild (an) bleibt unveraendert stehen, das neue (neu) liegt unsichtbar darueber und wird mit
seinem onLoad zu "an" - dasselbe <img>-Element (key = URL), also kein zweites Laden und nie eine leere Kachel.
"""
import io
import os
import re

HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html")


def _kachel():
    s = io.open(HTML, encoding="utf-8", newline="").read()
    i = s.index("function KameraKachel(")
    return s[i:re.compile(r"\nfunction [A-Z]").search(s, i + 10).start()]


def _fehler(k):
    f = []
    if "new Image()" in k:
        f.append("Vorladen per new Image (zweites Laden am sichtbaren Bild)")
    if "[snap.an,snap.neu].filter(Boolean).map(function(u){var laedt=u===snap.neu;" not in k:
        f.append("keine zwei Ebenen")
    if "return h('img',{key:u,src:u," not in k:
        f.append("img nicht per URL verschluesselt (Element wuerde neu geladen)")
    if "opacity:laedt?0:1}" not in k.split("data-kam-snap")[1].split("bild.modus==='mjpeg'")[0]:
        f.append("neue Ebene nicht unsichtbar")
    if "function snapDa(u){fehlerRef.current=0;setSnap(function(s){return s.neu===u?{an:u,neu:''}:s;});}" not in k:
        f.append("Tausch nicht erst nach onLoad")
    if "setSnap(function(s){return s.an===ziel||s.neu===ziel?s:{an:s.an,neu:ziel};});" not in k:
        f.append("sichtbares Bild wird beim Takt angefasst")
    return f


def test_kein_zucken_zwei_ebenen():
    assert _fehler(_kachel()) == []


def test_umkehrprobe():
    k = _kachel()
    for alt, neu in [
        ("opacity:laedt?0:1}", "opacity:1}"),
        ("return h('img',{key:u,src:u,", "return h('img',{key:'snap',src:u,"),
        ("{an:s.an,neu:ziel}", "{an:ziel,neu:''}"),
    ]:
        kaputt = k.replace(alt, neu, 1)
        assert kaputt != k and _fehler(kaputt), alt
