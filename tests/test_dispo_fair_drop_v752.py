# -*- coding: utf-8 -*-
"""v3.9.752 — Register #30 (P1, Screenshot): Verschieben prueft FAIR und lehnt EHRLICH ab.

Sebastian:
- 30a Eigengewicht: bei der Drop-Kapazitaetspruefung die eigene Dauer des gezogenen Chips aus der Belegung
  des Ziel-(und Quell-)Tages herausrechnen — sonst scheitert Umsortieren am eigenen Gewicht. Wand = Tagesnorm.
- 30b Ablehn-Grund mit Zahlen: die erste zutreffende Ursache, beziffert ("Tagesnorm: 6,5h belegt, 1h frei —
  3h passt nicht", "vergangen", "Urlaub (X)", "gesperrt", "Mittagspause").
- 30d "00:00"-Startzeit verboten: ein Chip ohne gueltige berechnete Startzeit rendert nie 00:00.

PURE Kerne (node-eval): _dispoDropOk (Wand mit rausgerechnetem Eigengewicht) + _dispoAblehnGrund(hardLabel,
normMin,usedMin,dauerMin,eigen).
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "fair752.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_eigengewicht_selber_chip_erlaubt(index_html, node_exe, tmp_path):
    """Norm 7,5h(450), 7h(420) belegt inkl. 4h(240)-Chip: den 4h-Chip auf DEMSELBEN Tag -> erlaubt;
    ein fremder 1h-Chip dazu -> abgelehnt. Wand = Tagesnorm (kein Reserve-Abzug fuer die Hand)."""
    js = _block(index_html) + _OK + u"""
// restMin fuer die Hand = normMin - usedMin (+ Eigengewicht, wenn der Chip schon auf dem Tag liegt)
var norm=450, used=420, eigen=240;
var restSelf=(norm-used)+eigen; // 30 + 240 = 270
ok(_dispoDropOk('M1','M1',false,restSelf,eigen)===true,'derselbe 4h-Chip re-droppen -> erlaubt');
var restFremd=(norm-used); // 30, fremder Chip ist NICHT auf dem Tag -> kein Eigengewicht
ok(_dispoDropOk('M1','M1',false,restFremd,60)===false,'fremder 1h-Chip -> abgelehnt (nur 30 min frei minus Puffer)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_ablehngrund_beziffert(index_html, node_exe, tmp_path):
    js = _block(index_html) + _OK + u"""
ok(_dispoAblehnGrund('vergangen',450,0,60,0)==='vergangen','harter Grund gewinnt');
ok(_dispoAblehnGrund('',450,390,180,0).indexOf('Tagesnorm')>=0,'Norm-Grund bei Ueberlast');
var g=_dispoAblehnGrund('',450,390,180,0);
ok(g.indexOf('6,5')>=0||g.indexOf('6.5')>=0,'nennt belegt-Stunden');
ok(_dispoAblehnGrund('',450,120,120,0)===null,'passt -> kein Grund (null)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_panel_00uhr_verboten(index_html):
    body = _panel(index_html)
    # 30d: ein Chip ohne gueltige Startzeit rendert "keine Luecke", nie 00:00.
    assert "keine Lücke" in body or "keine Luecke" in body, "kein 30d-Guard 'keine Luecke' fuer ungueltige Startzeit"
    assert "startMin!=null" in body or "startMin==null" in body or "_gueltigeZeit" in body, "kein Start-Gueltigkeits-Guard im Chip-Render"


def test_panel_ablehngrund_genutzt(index_html):
    body = _panel(index_html)
    assert "_dispoAblehnGrund" in body, "Toast/Feedback nutzt den bezifferten Ablehn-Grund nicht"
