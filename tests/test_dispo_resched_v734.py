# -*- coding: utf-8 -*-
"""v3.9.734 — Dispo: fixe Termine per Drag zwischen Tagen umterminieren.

Sebastian (16.07., live): "drag und drop verschiebung zwischen tagen geht noch nicht." Vorschlags-Chips
liessen sich schon ziehen (Pin, #16a), aber die FIXEN Zukunfts-Termine (📌, aus fixMap) hatten bewusst
keinen Drag — genau die will man aber zwischen Tagen verschieben (umterminieren). Jetzt: fixe Kachel auf
einen Tag DESSELBEN Monteurs ziehen -> terminBestaetigt wird auf den Zieltag gesetzt (updAs/E4b, Monteur/
Dauer/terminZeit bleiben; terminBestaetigt ist Push-Feld -> normaler Reschedule-Push). Fremde Zeile oder
derselbe Tag -> kein Write.

PURER Kern (node-eval): _dispoCanResched(fromMid,toMid,fromIso,toIso) -> nur true bei gleichem Monteur
UND anderem, gueltigem Tag. Die Drag-Geste + der updAs-Write sind struktur-gepinnt.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "resched734.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


# v3.9.759 (#8-13 Cleaning): die 3 _dispoCanResched-Tests entfernt — die Funktion war toter Code
# (0 Aufrufe; Reschedule laeuft seit #22a ueber den einheitlichen onDrop-Write, s.u.).


def test_panel_resched_ist_jetzt_ondrop(index_html):
    # v3.9.740 #22a: das Umterminieren fixer Termine laeuft jetzt ueber den EINHEITLICHEN Drop-Write (onDrop),
    # nicht mehr ueber einen eigenen Reschedule-Pfad. Die fixe Kachel ist ziehbar und schreibt via onDrop.
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    assert "onDrop" in body, "DispoPanel kennt den einheitlichen Drop-Write nicht"
    assert "onDrop?_chipDrag(f.scheinId" in body, "fixe Kachel schreibt nicht ueber onDrop"


def test_dispopanel_signatur_ondrop(index_html):
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein,onDrop})" in index_html
