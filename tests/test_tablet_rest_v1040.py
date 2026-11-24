# -*- coding: utf-8 -*-
"""v3.9.1040 Tablet-Rest - Riegel fuer die P3-Funde der Tablet-Pruefung 17.11.2026 (BERICHT.md Abschnitt 1).

Jeder Riegel hat eine Umkehrprobe: der alte Zustand wird in den Text zurueckgebaut und
der Riegel MUSS dann anschlagen - sonst misst er nichts (feedback_schutz_nie_ausgeloest).

(a) Zeiterfassung "Neuer Eintrag": Knopfleiste lag unter der Bildschirmtastatur
(b) Emojis in der sichtbaren Oberflaeche (Suche, Glocke, Mikrofon, Werkzeuge, OFFA-Seite, Kundenportal)
(c) Diagramm-Zahlen ueber Legende / Nachbarbalken
(d) Offline: doppelte Streifen; Material zeigte offline eine erfundene "0 Anforderungen"
(e) abgeschnittene Texte (Plan-Auswahl, Gewerk, Exportpfad, Material-Matrix, Fuehrerscheine)
(f) Leerzustand Projektfilter, Samstag neutral, Kaestchen 22 px Bild / 44 px Tippflaeche, Plus-Knopf
(g) Bueroportal-Zeitmatrix: Dezimalkomma in der Anzeige (nicht in den Dateien)
"""
import json
import re
import shutil

import pytest

from conftest import run_node_snippet
from _hilfen import nur_code

# Bildzeichen-Emojis; das Schliess-Kreuz U+2715 und Pfeile sind Typografie, keine Emojis
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u26FF\u2705\u274C\u2B50\u23F0-\u23FA]|\\\\uD83[CDE]\\\\u[0-9A-Fa-f]{4}")


def _block(html, anfang, ende):
    a = html.find(anfang)
    assert a != -1, anfang
    b = html.find(ende, a + len(anfang))
    assert b != -1, ende
    return html[a:b]


def _ohne_meldungen(code):
    """Toasts duerfen Emojis tragen (Hausregel) - nur die Oberflaeche zaehlt."""
    return re.sub(r"__toast[^;]*;?", "", code)


# ── (a) Bildschirmtastatur ──────────────────────────────────────────────────

def _tastatur_ok(html):
    code = nur_code(html)
    hat_vv = 'de.style.setProperty("--epk-vvh"' in code and 'vv.addEventListener("resize",setz)' in code
    huelle = code.count('height:"var(--epk-vvh,100dvh)"') >= 2
    leiste = all(('\'data-dlg-leiste\':"%s",style:{display:"flex"' % k) in code for k in ("ze", "pz"))
    klebt = code.count('position:"sticky",bottom:0,zIndex:2,background:V.cd') >= 2
    return hat_vv and huelle and leiste and klebt


def test_a_dialog_folgt_dem_sichtbaren_ausschnitt(index_html):
    assert _tastatur_ok(index_html)
    assert "onFocus:_dlgFokusSicht" in index_html, "Fokus-Feld wird nicht in die Mitte geholt"


def test_a_umkehrprobe(index_html):
    alt = index_html.replace('height:"var(--epk-vvh,100dvh)"', 'bottom:0')
    assert not _tastatur_ok(alt)
    alt2 = index_html.replace('position:"sticky",bottom:0,zIndex:2,background:V.cd', 'zIndex:2,background:V.cd')
    assert not _tastatur_ok(alt2)


# ── (b) Emojis ──────────────────────────────────────────────────────────────

BEREICHE = [
    ("Globale Suche", "/* ═══ GLOBAL SEARCH OVERLAY ═══ */", "/* ═══ NOTIFICATION PANEL ═══ */"),
    ("Benachrichtigungen", "/* ═══ NOTIFICATION PANEL ═══ */", "/* ═══ PHOTO QUEUE PANEL ═══ */"),
    ("Mikrofon", "function MicBtn({onText,style}){", "function PwInput("),
    ("Projekt-OFFA-Seite", "function VOffa({p,entries,kw,yr,monteure,ww}){", "\nfunction "),
]


def _emojis(html, anfang, ende):
    return EMOJI.findall(_ohne_meldungen(nur_code(_block(html, anfang, ende))))


@pytest.mark.parametrize("name,anfang,ende", BEREICHE)
def test_b_keine_emojis(index_html, name, anfang, ende):
    gef = _emojis(index_html, anfang, ende)
    assert not gef, "%s zeigt noch Emojis: %r" % (name, gef[:8])


def test_b_umkehrprobe(index_html):
    a = index_html.replace('_ikVw("glocke","Benachrichtigungen")', '"🔔 Benachrichtigungen"', 1)
    assert _emojis(a, *BEREICHE[1][1:])
    b = index_html.replace('_ik(listening?"stopp":"mikrofon",18)', 'listening?"⏹️":"🎤"', 1)
    assert _emojis(b, *BEREICHE[2][1:])


def test_b_werkzeuge_zeigen_ikone_statt_emoji(index_html):
    code = nur_code(index_html)
    assert "function _wzKatIk(k,gr)" in code
    for k, ik in (("elektro", "blitz"), ("mess", "lineal"), ("kabel", "verbindung")):
        assert re.search(r'%s:\{l:"[^"]+",i:"[^"]+",ik:"%s"' % (k, ik), code), k
    # Auswahllisten: kein Emoji vor der Beschriftung
    assert "React.createElement('option', { key: k, value: k}, v.i, \" \" , v.l)" not in code
    assert code.count("_wzKatIk(kat)") >= 3


def test_b_ikonen_fuer_mikrofon_vorhanden(index_html):
    code = nur_code(index_html)
    assert re.search(r"Object\.assign\(IKON,\{mikrofon:\[", code)
    assert "stopp:[" in code
    assert "'aria-label': listening?\"Spracherkennung stoppen\":\"Spracheingabe starten\"" in code


def test_b_offa_seite_nur_beschriftung(index_html):
    """VOffa: nur die Beschriftung wurde getauscht - keine neue Logik (kein onClick)."""
    blk = _block(index_html, "function VOffa({p,entries,kw,yr,monteure,ww}){", "\nfunction ")
    assert "onClick" not in blk
    assert 'const ascP=pe.slice(0,5).map(' in blk, "ASC-Vorschau unveraendert"


def test_b_suche_umlaut_kaputt_repariert(index_html):
    blk = _block(index_html, "/* ═══ GLOBAL SEARCH OVERLAY ═══ */", "/* ═══ NOTIFICATION PANEL ═══ */")
    assert "f\\\\u00fcr" not in blk, "'Keine Ergebnisse f\\u00fcr' stand woertlich im Bild"
    assert '"Keine Ergebnisse für \\""' in blk


# ── (c) Diagramme ───────────────────────────────────────────────────────────

def test_c_balkenspalte_passt_in_barH(index_html):
    blk = _block(index_html, "const BarChart=({data,labels,max,color,unit,color2,data2,legend})=>(", "const HBarChart=")
    assert "(barH-20)" not in blk
    assert blk.count("(barH-40)") == 2


def test_c_umkehrprobe_barH(index_html):
    alt = index_html.replace("(barH-40)", "(barH-20)")
    blk = _block(alt, "const BarChart=({data,labels,max,color,unit,color2,data2,legend})=>(", "const HBarChart=")
    assert "(barH-20)" in blk


def _svgbar_ys(node_exe, html):
    fn = _block(html, "function SvgBar(", "\nfunction SvgHBar(")
    js = ("const React={createElement:(t,p,...k)=>({t,p:p||{},k})};const V={dm:'#666'};const UI={fMeta:12};" + fn +
          "const svg=SvgBar({data:[{v:0},{v:232.6},{v:112},{v:0},{v:0},{v:0},{v:0},{v:0},{v:0},{v:0},{v:0},{v:0}]});"
          "const g=svg.k[0];const ys=g.map(x=>{const t=x.k.filter(c=>c&&c.t==='text');return t[t.length-1].p.y;});"
          "const bars=g.map(x=>x.k[0].p.y);console.log(JSON.stringify({ys,bars}));")
    return json.loads(run_node_snippet(node_exe, js))


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_c_zahl_steht_ueber_dem_hoeheren_nachbarn(node_exe, index_html):
    r = _svgbar_ys(node_exe, index_html)
    # Balken 2 (112) neben dem hoeheren Balken 1 (232,6): seine Zahl muss ueber dessen Oberkante stehen
    assert r["ys"][2] < r["bars"][1], r


@pytest.mark.skipif(shutil.which("node") is None, reason="node fehlt")
def test_c_umkehrprobe_zahl_auf_dem_nachbarn(node_exe, index_html):
    i = index_html.index("y: (function(){var _top=function(j)")
    e = index_html.index("})()", i) + 4
    alt = index_html[:i] + "y: many?(i%2===0?y-4:y-16):y-4" + index_html[e:]
    r = _svgbar_ys(node_exe, alt)
    assert not (r["ys"][2] < r["bars"][1]), r


# ── (d) Offline ─────────────────────────────────────────────────────────────

def test_d_offline_nur_ein_streifen(index_html):
    ob = _block(index_html, "function OfflineBanner({pendingCount,syncStatus}){", "\nfunction ")
    assert "if(!online&&syncStatus&&syncStatus.connected===false)return null;" in ob
    code = nur_code(index_html)
    assert '" Offline — Änderungen werden lokal gespeichert und später synchronisiert"' in code
    # die neue Version steht bei Stoerung als Knopf im Streifen, der blaue Streifen nur mit Verbindung
    assert "swUpdate&&syncStatus.connected&&syncStatus.serverOk&&React.createElement" in code
    assert "'data-update-knopf': \"1\"" in code


def test_d_umkehrprobe_offline(index_html):
    alt = index_html.replace("if(!online&&syncStatus&&syncStatus.connected===false)return null;", "", 1)
    ob = _block(alt, "function OfflineBanner({pendingCount,syncStatus}){", "\nfunction ")
    assert "connected===false)return null" not in ob


def _material_ehrlich(html):
    code = nur_code(html)
    return ("_setOrdFehl(!mo||!!mo.__rlsFehler);" in code and "if(_vmMountRef.current)_setOrdFehl(true);" in code
            and '_ordFehl?(navigator.onLine===false?"Offline – Daten nicht geladen":"Daten nicht geladen")' in code)


def test_d_material_keine_erfundene_null(index_html):
    assert _material_ehrlich(index_html)


def test_d_umkehrprobe_material(index_html):
    alt = index_html.replace('_ordFehl?(navigator.onLine===false?"Offline – Daten nicht geladen":"Daten nicht geladen"):', "", 1)
    assert not _material_ehrlich(alt)


# ── (e) abgeschnittene Texte ────────────────────────────────────────────────

def test_e_texte_brechen_um(index_html):
    code = nur_code(index_html)
    assert 'title: selPlan?((selPlan.geschoss?selPlan.geschoss+" · ":"")+(selPlan.name||"")):"Plan / Geschoss wählen"' in code
    assert 'whiteSpace:"nowrap"}}, w) );})("Gewerk"' not in code
    assert "_322(0,20)" not in code, "Exportordner wieder nach 20 Zeichen abgeschnitten"
    assert "React.createElement('thead', null, React.createElement('tr', { style: {background:V.bg}}, React.createElement('th', { scope: \"col\"" in code
    assert "hasDims&&!isMob&&cat.dims.map(d=>(React.createElement('span'" not in code
    assert "title: \"Führerschein: \"+m.fs, style: {display:\"inline-flex\",flexWrap:\"wrap\"" in code


def test_e_umkehrprobe(index_html):
    alt = index_html.replace('overflowWrap:"break-word",hyphens:"auto"}, title: w, lang: "de"}, w) );})("Gewerk"',
                             'overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}, w) );})("Gewerk"', 1)
    assert 'whiteSpace:"nowrap"}}, w) );})("Gewerk"' in nur_code(alt)


# ── (f) Kleinigkeiten ───────────────────────────────────────────────────────

def test_f_projektfilter_leerzustand(index_html):
    code = nur_code(index_html)
    assert "fil.length===0&&React.createElement('div', { 'data-epk': \"proj-leer\"" in code
    for t in ("Keine abgeschlossenen Projekte", "Keine archivierten Projekte", "Kein Projekt passt zur Suche"):
        assert t in code


def test_f_samstag_neutral(index_html):
    code = nur_code(index_html)
    assert "#7f1d1d" not in code and "#991b1b" not in code, "roter Samstag zurueck"
    assert "isSa?V.bg:V.cd" in code


def test_f_umkehrprobe_samstag(index_html):
    alt = index_html.replace('(isSa?"#475569,#64748b":"#1e293b,#334155")', '(isSa?"#7f1d1d,#991b1b":"#1e293b,#334155")', 1)
    assert "#7f1d1d" in nur_code(alt)


def _kaestchen_ok(html):
    g = _block(nur_code(html), "const GCSS=()=>`", "`;")
    m = re.search(r"@media \(pointer: coarse\), \(max-width: 768px\)\{html input\[type=checkbox\]\{-webkit-appearance:none !important;appearance:none !important;[^}]*center/22px 22px", g)
    return bool(m) and "html input[type=checkbox]:checked{background-image:" in g


def test_f_kaestchen_klein_gezeichnet_tippflaeche_bleibt(index_html):
    assert _kaestchen_ok(index_html)
    # die 44-px-Hausregel steht unveraendert (Riegel test_touch_ui_rest_v1037 prueft sie im Einzelnen)
    assert re.search(r'input\[type="checkbox"\],\s*input\[type="radio"\],[^{]*\{\s*min-height: 44px !important;\s*min-width: 44px !important;', index_html)


def test_f_umkehrprobe_kaestchen(index_html):
    alt = index_html.replace("center/22px 22px", "center/44px 44px", 1)
    assert not _kaestchen_ok(alt)


def test_f_plan_legende_nicht_unter_plusknopf(index_html):
    code = nur_code(index_html)
    assert code.count('left: 10, maxWidth: "calc(100% - 96px)", overflow: "hidden", zIndex: 10') == 2


# ── (g) Bueroportal ─────────────────────────────────────────────────────────

def test_g_anzeige_mit_komma_dateien_unveraendert(index_html):
    code = nur_code(index_html)
    assert '_n(kwTotal,2), "h")' not in code and '_n(ps.hrs,1)+" Std."' not in code
    assert 'fmtStd(kwTotal), " h")' in code and 'fmtStd(ps.hrs)+" Std."' in code  # Paket 13 (GF 24.11.2026): Stunden-Anzeige zentral ueber fmtStd (genau zwei Nachkommastellen, Komma, leer bleibt leer) - Pin bewusst nachgezogen
    # Export-HTML (Datei) bleibt beim Punkt-Format von _n
    assert code.count("html+='<td class=\"num\">'+_n(kwTotal,2)+'</td>") == 2


def test_g_umkehrprobe(index_html):
    alt = index_html.replace('fmtStd(ps.hrs)+" Std."', '_n(ps.hrs,1)+" Std."', 1)
    assert '_n(ps.hrs,1)+" Std."' in nur_code(alt)
