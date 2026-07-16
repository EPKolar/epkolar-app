# -*- coding: utf-8 -*-
"""v3.9.731 — Register #16a-Rest: Wartelisten-Zeile ziehbar + Live-Drop-Feedback + KW-Tab-Hover-Wechsel.

Sebastian (#16-Rest): Auch ein Wartelisten-Eintrag laesst sich auf einen Tag ziehen — mit denselben
Pin-Regeln wie ein Chip (nur auf einen Tag SEINES Monteurs). Waehrend des Ziehens faerbt sich die Ziel-
Zelle live gruen (passt), orange (Zeile stimmt, aber Tag ist voll -> Pin erzwingt trotzdem) oder rot
(fremde Monteur-Zeile -> Drop verboten). Zieht man ueber einen KW-Tab, wechselt nach 600 ms die Woche.

PURER Kern (node-eval):
  1. warteliste-Eintrag mit zugewiesenem Monteur traegt monteurId (fuer "Drop nur in seiner Zeile").
     Der ohneMonteur-Fall (kein Monteur im Schein) traegt KEINE monteurId.
  2. _dispoDropFeedback(dragMid, cellMid, restMin, dauerMin) klassifiziert das Live-Feedback:
     'block' (fremde Zeile) / 'ok' (passt) / 'tight' (Zeile ok, Kapazitaet reicht nicht).
Die Pointer-Interaktion (Waitlist-Ghost, Zell-Highlight, KW-Hover-Timer) ist struktur-gepinnt.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "d16arest731.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_warteliste_traegt_monteurid(index_html, node_exe, tmp_path):
    """Ein Schein mit Monteur, aber ohne freien Tag -> Warteliste-Eintrag traegt monteurId (ziehbar).
       Ein Schein ohne Monteur -> ohneMonteur:true und KEINE monteurId (nicht ziehbar)."""
    js = _block(index_html) + _OK + u"""
var cfg={monteure:[{id:'M1',name:'A'}],tage:[{key:'mo',woche:0,normMin:120}],
  firma:{},dist:function(){return 0;},kapAbzug:{},hatFz:function(){return true;},horizont:1,
  scheine:[{id:'VOLL',adrKey:'a',dauerMin:600,monteurId:'M1',alterMs:1},
           {id:'KEINM',adrKey:'b',dauerMin:60,alterMs:2}]};
var r=_dispoPlan(cfg);
var wVoll=r.warteliste.filter(function(w){return w.scheinId==='VOLL';})[0];
var wKein=r.warteliste.filter(function(w){return w.scheinId==='KEINM';})[0];
ok(wVoll && wVoll.monteurId==='M1' && wVoll.ohneMonteur===false,'VOLL: Warteliste traegt monteurId M1');
ok(wKein && wKein.ohneMonteur===true && !wKein.monteurId,'KEINM: ohneMonteur, keine monteurId');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


# v3.9.759 (#8-13 Cleaning): die 3 _dispoDropFeedback-Tests entfernt — die Funktion war toter Code
# (0 Aufrufe; das Live-Drop-Feedback spiegelt seit #22a die WRITE-Wand _dispoDropOk, s.u. struktur-Test).


def test_panel_16arest_struktur(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    body = index_html[start:end]
    # Live-Drop-Feedback: Klassifizierer im Panel + Feedback-State + farbige Zell-Border.
    # v3.9.740 #22a: das Feedback spiegelt jetzt die WRITE-Wand (_dispoDropOk) statt _dispoDropFeedback.
    assert "_dispoDropOk" in body, "Live-Drop-Feedback nutzt die Write-Wand nicht"
    assert "_dropFb" in body, "kein Feedback-State fuer die live gefaerbte Zielzelle"
    # KW-Tab-Hover-Wechsel waehrend des Drags (600 ms)
    assert "_kwHoverRef" in body, "kein KW-Tab-Hover-Timer beim Ziehen"
    assert "600" in body, "600-ms-Hover-Schwelle fehlt"
