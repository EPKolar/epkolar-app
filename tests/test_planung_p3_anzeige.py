# -*- coding: utf-8 -*-
"""Planung P3 (16.11.2026, Befund am A55) - nur Anzeige, keine Planungslogik.

  1  Wochenpfeile waren Textzeichen (◀ ▶, "Nächste Woche ▶", "◀ Diese Woche") -> Linienikonen.
  2  MA-Uebersicht: Projektnamen in Projektfarbe (Lila ausserhalb CI), in GROSSBUCHSTABEN wie
     erfasst und einzeilig abgeschnitten -> CI-Textfarbe (V.tx), lesbare Schreibweise
     (_wpNameLesbar), zwei Zeilen, voller Name im title.
  3  Fahrzeug-Kennzeichen in der Tageszelle ("TU-…") und Projektname bei den Spezialfahrzeugen
     (_kurz 18/22) wurden abgeschnitten -> Umbruch statt Abschneiden, voller Name im title.
_dispoPlan (md5) ist nicht beruehrt. Jeder Riegel hat eine Umkehrprobe.
"""
import json
import re
import subprocess

from conftest import EPK_TEST_TIMEOUT


def _ohne_kommentare(t):
    return re.sub(r"/\*.*?\*/", "", t, flags=re.S)


def _weekplan(src):
    i = src.index("\nfunction WeekPlan(")
    return _ohne_kommentare(src[i:src.index("\nfunction AbsView(", i)])


def _funktion(src, name):
    a = src.index("\nfunction " + name + "(") + 1
    return src[a:src.index("\n}\n", a) + 2]


def _befunde(wp):
    b = []
    for z in ("◀", "▶", "◄", "►"):
        if z in wp:
            b.append("Pfeil als Textzeichen: " + z)
    for ik in ('_ik("links",isMob?20:16)', '_ik("rechts",isMob?20:16)', '_zpIk("links","Diese Woche")'):
        if ik not in wp:
            b.append("Ikone fehlt: " + ik)
    if "color:pc" in wp:
        b.append("Projektname in Projektfarbe statt CI-Text")
    if wp.count("_wpNameLesbar(p.bvh)") != 2 or wp.count("title:p.bvh") + wp.count("title: p.bvh") < 2:
        b.append("MA-Uebersicht: Projektname nicht lesbar/ohne vollen Namen im title")
    if "_kurz(rr.bvh" in wp:
        b.append("Spezialfahrzeuge: Projektname wieder gekappt")
    if 'textOverflow:"ellipsis",verticalAlign:"middle"}}, f.conflict' in wp or 'whiteSpace:"normal",overflowWrap:"anywhere",display:"inline-block"' not in wp:
        b.append("Fahrzeug-Kennzeichen in der Tageszelle wird abgeschnitten")
    return b


def test_planung_anzeige_p3(index_html):
    assert _befunde(_weekplan(index_html)) == []


def test_umkehrproben_planung_anzeige(index_html):
    wp = _weekplan(index_html)
    kaputt = [
        wp.replace('_ik("rechts",isMob?20:16)', '"▶"', 1),
        wp.replace("color:V.tx,lineHeight:1.25,display:'-webkit-box'", "color:pc,lineHeight:1.25,display:'-webkit-box'", 1),
        wp.replace("_wpNameLesbar(rr.bvh)", "_kurz(rr.bvh,18)", 1),
        wp.replace('whiteSpace:"normal",overflowWrap:"anywhere",display:"inline-block"', 'whiteSpace:"nowrap",display:"inline-block"', 1),
        wp.replace("_wpNameLesbar(p.bvh)", "p.bvh", 1),
    ]
    for i, k in enumerate(kaputt):
        assert k != wp, "Umkehrprobe %d greift nicht" % i
        assert _befunde(k), "Umkehrprobe %d wurde nicht erkannt" % i


NODE = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8')+"\n;global.f=_wpNameLesbar;");
process.stdout.write(JSON.stringify(["DR.-GSCHMEIDLERSTRASSE 12","EFH MAIER / GARAGE","Haus Müller","ÖBB-HALLE","",null,"123"].map(x=>f(x))));
"""


def _namen(node_exe, tmp_path, quelle):
    q = tmp_path / "n.js"
    q.write_text(quelle, encoding="utf-8")
    s = tmp_path / "nl.js"
    s.write_text(NODE, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    return json.loads(p.stdout.decode("utf-8"))


def test_name_lesbar(index_html, node_exe, tmp_path):
    r = _namen(node_exe, tmp_path, _funktion(index_html, "_wpNameLesbar"))
    assert r == ["Dr.-Gschmeidlerstrasse 12", "EFH Maier / Garage", "Haus Müller", "ÖBB-Halle", "", "", "123"], r


def test_umkehrprobe_name_bleibt_gross(index_html, node_exe, tmp_path):
    q = _funktion(index_html, "_wpNameLesbar")
    alt = q.replace("if(!t||/[a-zäöü]/.test(t)", "if(true", 1)
    assert alt != q
    assert _namen(node_exe, tmp_path, alt)[0] == "DR.-GSCHMEIDLERSTRASSE 12"
