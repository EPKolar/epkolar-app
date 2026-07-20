# -*- coding: utf-8 -*-
"""v3.9.760 — Register #1 Teil 2: 🚫-Toggle (dispo_blocks Write-Pfad).

Toggle-Geste je Monteur×Tag-Zelle (Gate Buero/PL/Admin = onToggleBlock nur von der Eltern-Komponente
gereicht; Monteure sehen den Dispo-Tab nicht, §96). Sperren -> Grund-Prompt (Default "gesperrt"),
Entsperren -> Confirm am 🔓-Toggle. Vergangenheit: kein Toggle. Write: dispo_blocks INSERT/DELETE
(EIGENE Tabelle — arbeitsscheine-Whitelist bleibt 5; KEIN Push/OFFA). Nach r.ok: window.__dispoBlocks
spiegeln + _setTick-Recompute -> Sperre wirkt sofort (Kap 0, data-hardblock, #22a greift). 42P01/404 ->
sichtbarer Hinweis, NIE stiller Fehlschlag, NIE grün ohne r.ok (v699).

v745-Garantie ERWEITERT (nicht gebrochen): der DispoPanel-Body bleibt schreibfrei — der dispo_blocks-Write
liegt in der Eltern-Prop onToggleBlock, im Panel steht nur die Geste (Prompt/Confirm = UI) + _setTick.
"""
import re
import subprocess


def _panel(index_html):
    start = index_html.index("function DispoPanel({")
    end = index_html.index("function ArbeitsscheinView({", start)
    return index_html[start:end]


# ---------------------------------------------------------------- static wiring

def test_ontoggleblock_in_signatur(index_html):
    assert "function DispoPanel({arbeitsscheine,monteure,wpHistory,abs,onUebernehmen,onOpenSchein,onDrop,onToggleBlock,onRefreshScheine})" in index_html, \
        "onToggleBlock fehlt in der DispoPanel-Signatur (ReferenceError-Risiko, v741-Lektion)"


def test_panel_body_bleibt_schreibfrei(index_html):
    """v745-Garantie erweitert: der dispo_blocks-Write ist NICHT im Panel-Body (nur der onToggleBlock-Aufruf)."""
    body = _panel(index_html)
    assert "onToggleBlock(" in body, "Panel ruft die onToggleBlock-Prop nicht"
    # Kein direkter Write im Panel — weder AS noch dispo_blocks:
    assert "updAs(" not in body, "updAs im DispoPanel-Body (verboten)"
    assert "SQ.push" not in body, "SQ.push im DispoPanel-Body (verboten)"
    assert '_sbPost("dispo_blocks"' not in body and "_sbPost('dispo_blocks'" not in body, \
        "dispo_blocks-INSERT liegt im Panel-Body statt in der Eltern-Prop"
    assert "_sbDeleteWhere(\"dispo_blocks\"" not in body and "_sbDeleteWhere('dispo_blocks'" not in body, \
        "dispo_blocks-DELETE liegt im Panel-Body statt in der Eltern-Prop"


def test_toggle_kopfstreifen_gegen_kollision(index_html):
    """v3.9.763 P3-Nachbesserung: die Zelle reserviert einen Kopfstreifen (paddingTop), wenn der Toggle
    gerendert wird, damit das absolut positionierte Toggle nie ueber Karten/Chips liegt."""
    body = _panel(index_html)
    assert "var _hasToggle=(typeof onToggleBlock==='function')" in body, "_hasToggle-Bedingung fehlt"
    assert "paddingTop:_hasToggle?18:4" in body, "kein reservierter Kopfstreifen (paddingTop) fuer die Toggle-Zelle"


def test_toggle_hat_vergangenheits_guard(index_html):
    body = _panel(index_html)
    assert "var _toggleBtn=function(m,t){" in body, "_toggleBtn-Renderer fehlt"
    m = re.search(r"var _toggleBtn=function\(m,t\)\{[\s\S]+?\};", body)
    seg = m.group(0)
    assert "t.iso<_built.heute" in seg, "kein Vergangenheits-Guard im Toggle (kein Write in die Vergangenheit)"
    assert "onToggleBlock!=='function'" in seg, "kein Gate (onToggleBlock-Praesenz) im Toggle"


def test_eltern_write_auf_dispo_blocks_gated_und_rok(index_html):
    """Der Write sitzt in der Eltern-Prop: dispo_blocks INSERT/DELETE, canSync-gated, 42P01/404-Hinweis,
    r.ok-gated (nie grün ohne Erfolg), window.__dispoBlocks-Spiegelung."""
    i = index_html.index("onToggleBlock: canSync?function(workerId,iso,grund){")
    seg = index_html[i:i + 2000]
    assert '_sbPost("dispo_blocks"' in seg, "INSERT nicht auf dispo_blocks"
    assert '_sbDeleteWhere("dispo_blocks"' in seg, "DELETE nicht auf dispo_blocks"
    assert "window.__dispoBlocks" in seg, "window.__dispoBlocks wird nicht gespiegelt (kein Sofort-Effekt)"
    assert "42P01" in seg, "kein 42P01/Tabelle-fehlt-Handling"
    assert "return{ok:true}" in seg and "return{ok:false}" in seg, "nicht r.ok-gated (v699: nie grün ohne Erfolg)"
    assert "canSync?" in index_html[i - 20:i + 30], "onToggleBlock nicht auf canSync (Buero/PL/Admin) gegated"


# ---------------------------------------------------------------- node-eval Toggle-Kern

_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js, name):
    f = tmp_path / name
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout, (r.stdout or "") + (r.stderr or "")


def test_toggle_kern(index_html, node_exe, tmp_path):
    """Modelliert die Toggle-Entscheidungen (mirror des Panel-Codes): Gate, Vergangenheit, Blocked-Erkennung,
    Richtung (blocked->null/DELETE, frei->grund/INSERT), Default-Grund."""
    js = _OK + u"""
var HEUTE='2026-07-20';
// _toggleBtn-Gate: sichtbar nur mit Callback UND iso>=heute:
function canToggle(hasCb, iso){ return !!(hasCb && HEUTE && iso>=HEUTE); }
ok(canToggle(true,'2026-07-21')===true,'Zukunft + Callback -> Toggle sichtbar');
ok(canToggle(true,'2026-07-20')===true,'heute -> Toggle sichtbar');
ok(canToggle(true,'2026-07-19')===false,'Vergangenheit -> KEIN Toggle');
ok(canToggle(false,'2026-07-21')===false,'kein Callback (Monteur/§96) -> KEIN Toggle');

// blocked-Erkennung aus blocksMap:
function isBlocked(blocks, mid, iso){ var k=mid+'_'+iso; return (blocks[k]!==undefined && blocks[k]!==null); }
var blocks={'m1_2026-07-21':'Schulung'};
ok(isBlocked(blocks,'m1','2026-07-21')===true,'gesperrter Tag erkannt');
ok(isBlocked(blocks,'m1','2026-07-22')===false,'freier Tag nicht gesperrt');

// Richtung + Grund-Default (mirror _toggleBlock):
function toggleArg(isBlocked, promptVal){
  if(isBlocked) return null;                          // -> DELETE
  if(promptVal===null) return 'ABBRUCH';              // Prompt abgebrochen -> kein Write
  var g=String(promptVal).trim()||'gesperrt';         // Default-Grund
  return g;                                           // -> INSERT mit grund
}
ok(toggleArg(true,undefined)===null,'gesperrt -> null (Entsperren/DELETE)');
ok(toggleArg(false,'Urlaub')==='Urlaub','frei + Grund -> INSERT mit Grund');
ok(toggleArg(false,'   ')==='gesperrt','leerer Grund -> Default gesperrt');
ok(toggleArg(false,'')==='gesperrt','leerer String -> Default gesperrt');
ok(toggleArg(false,null)==='ABBRUCH','Prompt-Abbruch -> kein Write');

// r.ok-Gate fuer den Recompute (mirror .then): nur bei r.ok!==false neu rechnen:
function recompute(r){ return !!(r && r.ok!==false); }
ok(recompute({ok:true})===true,'Erfolg -> Recompute');
ok(recompute({ok:false})===false,'Fehlschlag -> KEIN Recompute (nie grün ohne r.ok)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js, "toggle760.js")
