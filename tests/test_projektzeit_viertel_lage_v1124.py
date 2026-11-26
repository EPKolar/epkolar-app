# -*- coding: utf-8 -*-
"""Projektzeit-Auswahl (ViertelZeitWahl, v3.9.1124): die Auswahl verdeckt ihr eigenes Feld NIE - im ECHTEN Browser.

Befund GF 26.11.2026 (Tablet): klappt die Auswahl nach oben auf, weil unten zu wenig Platz ist, liegt sie ueber dem Feld,
zu dem sie gehoert. Ursache: auf() rechnete mit einer ANGENOMMENEN Hoehe von 400 px und setzte nach oben nur die
Oberkante (Feld-Oberkante - 404). Ist das Klappfeld wirklich hoeher (Nachtstunden aufgeklappt, groessere Geraeteschrift),
waechst es nach unten ueber das Feld; passt keine Seite, lag es unten ueber den Bildschirmrand hinaus.

Kur: echte Hoehe messen (_vzwLage): unter das Feld, sonst ueber das Feld mit der Unterkante an der Feld-Oberkante,
sonst neben das Feld, sonst scrollbar im groesseren freien Raum - nie ueber dem Feld-Rechteck. Neu gerechnet bei
Scrollen/Groessenaenderung/Nachtstunden. Handy-Blatt: liegt das Feld dahinter, wird gescrollt; geht das nicht, wird das
Blatt bis unter das Feld gekuerzt, solange die Minuten-Zeile ganz sichtbar bleibt; sonst traegt der Blattkopf Feldname und
gespeicherten Wert ("Feld Von: 07:25").

Supabase ist abgefangen wie in test_projektzeit_viertel_v1124.py (dieselben Hilfen). Jede Messung liefert eine
Maengelliste (leer = gruen). Die Umkehrprobe baut die alte 400-px-Rechnung in eine KOPIE der Datei ein und verlangt rot.
"""
import functools
import io
import os
import socketserver
import threading

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from test_projektzeit_viertel_v1124 import WURZEL, _Still, _dialog, _oeffne  # noqa: E402


@pytest.fixture(scope="module")
def server():
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(_Still, directory=WURZEL))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield "http://127.0.0.1:%d/index.html" % srv.server_address[1]
    srv.shutdown()
    srv.server_close()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as pw:
        try:
            br = pw.chromium.launch()
        except Exception as e:  # pragma: no cover
            pytest.skip("Chromium nicht startbar: %s" % e)
        yield br
        br.close()


@pytest.fixture(scope="module")
def quelle():
    return io.open(os.path.join(WURZEL, "index.html"), encoding="utf-8", newline="").read()


# Feld an eine Bildschirmhoehe schieben: der Dialog-Scrollbehaelter bekommt oben/unten Luft, dann wird er gescrollt.
SETZ = r"""([feld, ziel]) => { const k = document.querySelector('[data-vzw="' + feld + '"] [data-vzw-feld]'); let e = k.parentElement;
  while (e && !/(auto|scroll)/.test(getComputedStyle(e).overflowY)) e = e.parentElement;
  if (!e) return null; e.style.paddingTop = '700px'; e.style.paddingBottom = '700px';
  const r = k.getBoundingClientRect(); e.scrollTop += (r.top - ziel); const r2 = k.getBoundingClientRect(); return [r2.top, r2.bottom]; }"""
SCROLLE = r"""([feld, dy]) => { const k = document.querySelector('[data-vzw="' + feld + '"] [data-vzw-feld]'); let e = k.parentElement;
  while (e && !/(auto|scroll)/.test(getComputedStyle(e).overflowY)) e = e.parentElement; e.scrollTop += dy; }"""
# Feld-Rechteck = das ganze Eingabefeld (PC: Textfeld samt Knopf darin; Beruehrung: der Feld-Knopf)
LAGE = r"""(feld) => { const k = document.querySelector('[data-vzw="' + feld + '"] [data-vzw-feld]');
  const f = (k.tagName === 'INPUT' ? k.parentElement : k).getBoundingClientRect();
  const pe = document.querySelector('[data-vzw-panel]'); if (!pe) return null; const p = pe.getBoundingClientRect();
  const ueber = !(p.bottom <= f.top || p.top >= f.bottom || p.right <= f.left || p.left >= f.right);
  return {f: [f.top, f.bottom, f.left, f.right].map(Math.round), p: [p.top, p.bottom, p.left, p.right].map(Math.round),
          ueberlappt: ueber, drinnen: p.top >= 0 && p.left >= 0 && p.bottom <= innerHeight && p.right <= innerWidth,
          seite: pe.getAttribute('data-vzw-seite'), sichtbar: getComputedStyle(pe).visibility}; }"""


def _pruef(s, feld, was, m):
    l = s.evaluate(LAGE, feld)
    if l is None:
        m.append("%s: Auswahl nicht offen" % was)
        return
    if l["ueberlappt"]:
        m.append("%s: Auswahl verdeckt das Feld (Feld %s, Auswahl %s, seite %s)" % (was, l["f"], l["p"], l["seite"]))
    if not l["drinnen"]:
        m.append("%s: Auswahl ragt aus dem Bild (Auswahl %s)" % (was, l["p"]))
    if l["sichtbar"] != "visible":
        m.append("%s: Auswahl unsichtbar (%s)" % (was, l["sichtbar"]))


def _messe_klappfeld(browser, url, beruehrung, index_body=None):
    """Tablet (Beruehrung) bzw. PC (Maus) 1280x800: Feld oben, Mitte, unten, ganz unten; jeweils auch mit Nachtstunden
    (Klappfeld ~100 px hoeher). Danach: offen scrollen -> neu gerechnet, weiterhin frei."""
    m = []
    art = "Tablet" if beruehrung else "PC"
    for feld in ("Von", "Bis"):
        for ziel in (80, 420, 700, 740):
            ctx, s, schreib, fehler = _dialog(browser, url, 1280, 800, beruehrung, index_body)
            try:
                if s.evaluate(SETZ, [feld, ziel]) is None:
                    m.append("%s: kein Scrollbehaelter im Dialog - Messung ohne Aussage" % art)
                    return m
                s.wait_for_timeout(100)
                _oeffne(s, feld)
                s.wait_for_timeout(100)
                _pruef(s, feld, "%s %s Feld bei y=%d" % (art, feld, ziel), m)
                s.click('[data-vzw-panel="%s"] [data-vzw-nacht]' % feld)
                s.wait_for_timeout(150)
                _pruef(s, feld, "%s %s Feld bei y=%d + Nachtstunden" % (art, feld, ziel), m)
                if ziel == 420:
                    # offen scrollen: Feld wandert 300 px nach oben -> neue Lage, wieder frei
                    s.evaluate(SCROLLE, [feld, 300])
                    s.wait_for_timeout(150)
                    if s.query_selector('[data-vzw-panel]'):
                        _pruef(s, feld, "%s %s nach Scrollen" % (art, feld), m)
                if fehler:
                    m.append("JS-Fehler: %s" % fehler[:2])
            finally:
                ctx.close()
    return m


def _messe_handy(browser, url, index_body=None):
    """Handy 390x844: das Blatt verdeckt das Feld nicht (Scrollen oder Kuerzen); sonst muss der Blattkopf Feld + Wert zeigen.
    Fall 2: Dialog mit Scrollweg und Feld weit unten -> das Feld wird ueber das Blatt gescrollt."""
    m = []
    for feld, wert in (("Von", "07:25"), ("Bis", "16:15")):
        for scrollweg in (False, True):
            ctx, s, schreib, fehler = _dialog(browser, url, 390, 844, True, index_body)
            try:
                if scrollweg and s.evaluate(SETZ, [feld, 760]) is None:
                    m.append("Handy: kein Scrollbehaelter - Messung ohne Aussage")
                    return m
                s.wait_for_timeout(100)
                _oeffne(s, feld)
                s.wait_for_timeout(200)
                r = s.evaluate(r"""(feld) => { const k = document.querySelector('[data-vzw="' + feld + '"] [data-vzw-feld]').getBoundingClientRect();
                  const pe = document.querySelector('[data-vzw-panel]'); const p = pe.getBoundingClientRect();
                  const mz = pe.querySelector('[role=listbox][aria-label=Minute]').getBoundingClientRect();
                  const kw = pe.querySelector('[data-vzw-kopfwert]');
                  return {fo: k.top, fu: k.bottom, blatt: p.top, unten: innerHeight - p.bottom, minute: mz.bottom, kopf: kw ? kw.textContent.trim() : ''}; }""", feld)
                was = "Handy %s%s" % (feld, " (Dialog mit Scrollweg)" if scrollweg else "")
                frei = r["fu"] <= r["blatt"] and r["fo"] >= 0
                if not frei and r["kopf"] != "Feld %s: %s" % (feld, wert):
                    m.append("%s: Blatt verdeckt das Feld (Feld %d-%d, Blatt ab %d) und der Kopf zeigt es nicht (%r)"
                             % (was, r["fo"], r["fu"], r["blatt"], r["kopf"]))
                if scrollweg and not frei:
                    m.append("%s: Feld trotz Scrollweg hinter dem Blatt (Feld %d-%d, Blatt ab %d)" % (was, r["fo"], r["fu"], r["blatt"]))
                if r["unten"] > 2:
                    m.append("%s: Blatt nicht mehr unten (%d px)" % (was, r["unten"]))
                if r["minute"] > 844:
                    m.append("%s: Minuten-Zeile abgeschnitten (bis %d)" % (was, r["minute"]))
                if not r["kopf"].startswith("Feld %s: " % feld):
                    m.append("%s: Blattkopf ohne Feld/Wert (%r)" % (was, r["kopf"]))
                if fehler:
                    m.append("JS-Fehler: %s" % fehler[:2])
            finally:
                ctx.close()
    return m


ALLE_LAGEN = r"""() => { if (typeof _vzwLage !== 'function') return ['_vzwLage fehlt'];
  const m = []; const vws = [[1280, 800], [800, 1280], [1024, 600], [600, 400]];
  for (const [vw, vh] of vws) for (let top = -20; top <= vh; top += 17) for (const hf of [30, 44, 120]) for (const left of [0, 20, 300, vw - 120])
    for (const hoehe of [150, 388, 486, 700, 1400]) {
      const f = {top: top + 0.4, bottom: top + hf + 0.4, left: left + 0.5, right: left + 104.5}; const b = Math.min(340, vw - 16);
      if (f.bottom < 0 || f.top > vh) continue;
      const l = _vzwLage(f, hoehe, b, vw, vh); const h = Math.min(hoehe, l.maxH);
      const p = {top: l.top, bottom: l.top + h, left: l.left, right: l.left + b};
      if (!(p.bottom <= f.top || p.top >= f.bottom || p.right <= f.left || p.left >= f.right)) m.push(JSON.stringify({vw, vh, f, hoehe, l}));
      if (p.top < 0 || p.left < 0 || p.bottom > vh || p.right > vw) m.push('aus dem Bild ' + JSON.stringify({vw, vh, f, hoehe, l}));
    }
  return m.slice(0, 5); }"""


# ── Tests ────────────────────────────────────────────────────────────────────
def test_tablet_auswahl_verdeckt_feld_nicht(browser, server):
    assert _messe_klappfeld(browser, server, True) == []


def test_pc_auswahl_verdeckt_feld_nicht(browser, server):
    assert _messe_klappfeld(browser, server, False) == []


def test_handy_blatt_verdeckt_feld_nicht(browser, server):
    assert _messe_handy(browser, server) == []


def test_lagerechnung_alle_faelle(browser, server):
    """_vzwLage fuer viele Feldlagen, Feldhoehen, Klappfeldhoehen und Bildschirme: nie ueber dem Feld, nie aus dem Bild."""
    ctx, s, schreib, fehler = _dialog(browser, server, 1280, 800, True)
    try:
        assert s.evaluate(ALLE_LAGEN) == []
    finally:
        ctx.close()


# ── Umkehrprobe: die alte 400-px-Rechnung MUSS auffallen ─────────────────────
ALT_LAGE = ("var l=(function(){var hoehe=400;var top=r.bottom+4;if(top+hoehe>window.innerHeight-8&&r.top-4-hoehe>=8)top=r.top-4-hoehe;"
            "return {top:Math.round(top),left:Math.round(Math.max(8,Math.min(r.left,window.innerWidth-b-8))),breite:b,"
            "maxH:Math.max(200,window.innerHeight-Math.round(top)-8),seite:\"alt\"};})();")
NEU_LAGE = "var l=_vzwLage({top:r.top,bottom:r.bottom,left:r.left,right:r.right},nat,b,window.innerWidth,window.innerHeight);"


def test_umkehr_alte_400px_rechnung(browser, server, quelle):
    assert quelle.count(NEU_LAGE) == 1
    k = quelle.replace(NEU_LAGE, ALT_LAGE).encode("utf-8")
    m = _messe_klappfeld(browser, server, True, k)
    assert any("verdeckt das Feld" in x for x in m), m
