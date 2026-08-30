"""v3.9.709 — PlanRadar Fokus-Zoom: Flex-Offset-Korrektur (Handy-Pinch driftete).

Root-Cause: der world-Container (transform-Div) wird per `justify-content:center /
align-items:center` im Gesten-Div flex-ZENTRIERT. Sein transform-origin (0,0) sitzt
dadurch NICHT an der Viewport-Ecke, sondern um den Flex-Offset o versetzt (empirisch
gemessen: kleiner Plan +30/+235px, A4-Render −448/−538px). Die Fokus-Zoom-Mathematik
(`_planZoomAt`) hält einen Punkt `mid` fix — aber `mid` muss im world-Layout-Frame
liegen. Vorher wurde `mid = finger - viewport.left` (Viewport-Frame) benutzt → der Zoom
driftete um o·(r−1) pro Schritt (auf dem Handy: Pinch nicht auf dem Finger zentriert).

Fix: alle vier Fokus-Pfade (Pinch, Doppeltipp, Buttons/_zoomCenter, Mausrad) rechnen den
world-Layout-Ursprung via _worldOrigin() heraus. `_planZoomAt` selbst bleibt unverändert
(reine Funktion) — diese Tests pinnen die Invariante + die Frame-Übersetzung an den
Aufrufstellen.
"""
import json
from _hilfen import nur_code
from conftest import run_node_snippet, _extract_fn


def _zoomfn(index_html):
    fn = _extract_fn(index_html, "_planZoomAt")
    assert fn, "_planZoomAt nicht gefunden"
    return fn


def _newpos(node_exe, index_html, C, tx, s, F, r):
    """Screen-Position des Weltpunkts, der VOR dem Zoom unter Finger F lag, NACH dem Zoom.

    Geometrie: screenPos(wx) = C + tx + wx*s   (C = Screen-X des Layout-Ursprungs, inkl.
    Flex-Offset). Korrekter Fokus: mid = F - C (Layout-Frame). Invariante: der Punkt bleibt
    unter F.
    """
    fn = _zoomfn(index_html)
    snippet = fn + "\n" + (
        "var C=%r,tx=%r,s=%r,F=%r,r=%r;" % (C, tx, s, F, r)
        + "var wx=(F-C-tx)/s;"
        + "var mid=F-C;"
        + "var o=_planZoomAt({s:s,tx:tx,ty:0},{x:mid,y:0},r,0.4,6);"
        + "var pos=C+o.tx+wx*o.s;"
        + "process.stdout.write(JSON.stringify({pos:pos,ns:o.s,tx:o.tx}));"
    )
    return json.loads(run_node_snippet(node_exe, snippet))


# ── Invariante: Weltpunkt bleibt unter dem Finger, bei beliebigem Flex-Offset ──
def test_focus_fixed_positive_offset(node_exe, index_html):
    # kleiner Plan: Flex-Offset +30px
    res = _newpos(node_exe, index_html, C=30, tx=0, s=1, F=200, r=2)
    assert abs(res["pos"] - 200) < 1e-6


def test_focus_fixed_negative_offset(node_exe, index_html):
    # A4-Plan: Flex-Offset negativ, mit Pan/Zoom im Ausgangszustand
    res = _newpos(node_exe, index_html, C=-447.6, tx=-50, s=1.2, F=180, r=1.5)
    assert abs(res["pos"] - 180) < 1e-6


def test_focus_fixed_zoom_out(node_exe, index_html):
    res = _newpos(node_exe, index_html, C=88, tx=120, s=2.5, F=260, r=0.6)
    assert abs(res["pos"] - 260) < 1e-6


def test_ignoring_offset_drifts_by_o_times_r_minus_1(node_exe, index_html):
    # Beweis Root-Cause: mid=F (Viewport-Frame, o=30 ignoriert) → Punkt landet o·(r−1)=30px
    # VOR dem Finger. Genau dieser Fehler war der Bug.
    fn = _zoomfn(index_html)
    snippet = fn + "\n" + (
        "var C=30,tx=0,s=1,F=200,r=2;var wx=(F-C-tx)/s;var mid=F;"
        "var o=_planZoomAt({s:s,tx:tx,ty:0},{x:mid,y:0},r,0.4,6);"
        "var pos=C+o.tx+wx*o.s;process.stdout.write(JSON.stringify({drift:pos-F}));"
    )
    res = json.loads(run_node_snippet(node_exe, snippet))
    assert abs(res["drift"] + 30) < 1e-6


# ── Statische Guards: alle vier Pfade übersetzen in den world-Layout-Frame ──
def test_worldorigin_helper_and_ref(index_html):
    assert "const _worldOrigin = () =>" in index_html
    assert "const worldRef = _react.useRef.call(void 0, null);" in index_html
    assert "ref: worldRef," in index_html


def test_pinch_uses_world_frame_but_keeps_locked_formula(index_html):
    # mid ist jetzt world-Layout-relativ (Flex-Offset abgezogen)
    assert "const _fx=_wo?(_mx-_wo.x+pan.x):(_vr?(_mx-_vr.left):_mx)" in index_html
    # locked Fokus-Formel (v3.9.142) unverändert — die Invariante hängt daran
    assert "setPan(pp=>({x:_fx-(_fx-pp.x)*r, y:_fy-(_fy-pp.y)*r}));return nz;});" in index_html
    assert "const _mx=(pts[0].x+pts[1].x)/2, _my=(pts[0].y+pts[1].y)/2;" in index_html


def test_all_four_paths_call_worldorigin(index_html):
    """Pinch + Doppeltipp + _zoomCenter + Mausrad ziehen alle den world-Ursprung heraus.

    v3.9.913 - DIE ZAHL IST WEG. Vorher: `index_html.count("_worldOrigin()") >= 4`.

    Der Docstring dieser Datei nennt die vier Pfade beim Namen - die Zahl war
    also von Anfang an nur ihr Stellvertreter, und ein schlechter: roh 6,
    kommentarblind 4. Zwei der sechs Treffer waren Prosa. Waere einer der vier
    Pfade auf den alten Viewport-Frame zurueckgefallen (genau der Fehler, den
    v3.9.709 behoben hat), haetten die zwei Kommentar-Treffer die Zahl bei >=4
    gehalten - der Riegel waere GRUEN geblieben, waehrend der Pinch auf dem Handy
    wieder driftet. Jetzt wird je Pfad an seinem Anker nachgesehen.
    """
    code = nur_code(index_html)
    for pfad, anker, fenster in (
        ("Pinch (Fingermitte)",
         "const _mx=(pts[0].x+pts[1].x)/2, _my=(pts[0].y+pts[1].y)/2;", 260),
        ("Doppeltipp (<300ms, <28px)",
         "Math.hypot(e.clientX-_last.x, e.clientY-_last.y) < 28){", 260),
        ("_zoomCenter (Buttons, Viewport-Mitte)",
         "const _fx = _vr ? _vr.width/2 : 0, _fy = _vr ? _vr.height/2 : 0;", 260),
        # Anker bewusst der Handler-Kopf, NICHT die gesuchte Zeile selbst -
        # sonst meldet der Riegel "Anker nicht auffindbar" statt zu sagen, dass
        # dieser Pfad den Ursprung nicht mehr zieht.
        ("Mausrad", "const _wh = (e) => {", 200),
    ):
        i = code.find(anker)
        assert i != -1, "Anker des Pfades %s nicht mehr auffindbar: %r" % (pfad, anker)
        assert "_worldOrigin()" in code[i:i + fenster], (
            "Fokus-Pfad %s zieht den world-Layout-Ursprung nicht mehr heraus - dort "
            "driftet der Zoom wieder um den Flex-Offset (v3.9.709)." % pfad
        )


def test_zoomcenter_keeps_locked_center_line(index_html):
    # locked (v3.9.142): Viewport-Mitte als Rohwert; Übersetzung in Layout-Frame passiert danach
    assert "const _fx = _vr ? _vr.width/2 : 0, _fy = _vr ? _vr.height/2 : 0;" in index_html
