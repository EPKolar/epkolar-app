# -*- coding: utf-8 -*-
"""v3.9.732 — Register #16b: Dauer-Griff am Vorschlags-Chip.

Sebastian (#16b): Am Rand eines Vorschlags-Chips sitzt ein Griff (≡). Zieht man ihn horizontal,
aendert sich die geplante Dauer in 15-min-Schritten (min 30, max Tagesnorm), der Balken zieht live
mit, das Label zeigt die neue Dauer. Uebernommen wird die geaenderte Dauer erst mit ✓ Uebernehmen
(als dauer HH:MM:SS via updAs/E4b — KEIN neuer Push, byte-gleich zum manuellen Buero-Edit).

PURER Kern (node-eval): _dispoDauerSnap(baseMin, deltaPx, pxPerStep, normMin) rechnet die neue Dauer:
Pixel-Weg -> 15-min-Raster (DISPO_ZEITRASTER_MIN), geklemmt auf [30, normMin]. Die Pointer-Geste
(Griff, Live-Balken, Uebernahme als dauer) ist struktur-gepinnt.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "d16b732.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_raster_konstante(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(DISPO_ZEITRASTER_MIN===15,'15-min-Raster');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dauersnap_kein_delta(index_html, node_exe, tmp_path):
    """Ohne Pixel-Weg bleibt die Dauer (auf 15 gerundet)."""
    js = _block(index_html) + _OK + u"""
ok(_dispoDauerSnap(120,0,30,510)===120,'kein Delta -> 120');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dauersnap_schritt_rechts(index_html, node_exe, tmp_path):
    """Ein Griff-Schritt nach rechts (deltaPx == pxPerStep) = +15 min."""
    js = _block(index_html) + _OK + u"""
ok(_dispoDauerSnap(120,30,30,510)===135,'+1 Schritt -> 135');
ok(_dispoDauerSnap(120,60,30,510)===150,'+2 Schritte -> 150');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dauersnap_klemmt_min30(index_html, node_exe, tmp_path):
    """Weit nach links ziehen faellt nie unter 30 min."""
    js = _block(index_html) + _OK + u"""
ok(_dispoDauerSnap(60,-900,30,510)===30,'unter 30 -> 30');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_dauersnap_klemmt_maxnorm(index_html, node_exe, tmp_path):
    """Weit nach rechts ziehen ueberschreitet nie die Tagesnorm."""
    js = _block(index_html) + _OK + u"""
ok(_dispoDauerSnap(480,900,30,510)===510,'ueber Norm -> 510');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_16b_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # Dauer-Griff (Handle), Snap-Rechnung, Override-Dauer-State, Uebernahme nutzt die geaenderte Dauer.
    # v3.9.733: Geste ist jetzt VERTIKAL (Kachel-Hoehe ziehen, ns-resize) statt horizontal (Sebastian).
    assert "_dispoDauerSnap" in body, "Dauer-Griff rechnet nicht mit _dispoDauerSnap"
    assert "_dauerDrag" in body, "kein Dauer-Griff (Pointer-Geste) am Chip"
    assert "_dauerOv" in body, "keine Override-Dauer (Live) vor der Uebernahme"
    assert "ns-resize" in body, "Hoehen-Griff (vertikal) fehlt — Sebastian: Kachel in der Hoehe ziehen"
    # Uebernahme schreibt die GEAENDERTE Dauer (_eff), nicht die urspruengliche c.dauerMin.
    assert "onUebernehmen(c.scheinId,m.id,t.iso,_eff,_dispoMinToHHMM(_win.startMin))" in body, "Uebernahme uebergibt nicht die geaenderte Dauer"
    assert "onUebernehmen(c.scheinId,m.id,t.iso,c.dauerMin)" not in body, "alte Uebernahme-Dauer (c.dauerMin) noch vorhanden"
