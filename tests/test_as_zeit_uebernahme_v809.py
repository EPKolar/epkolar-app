# -*- coding: utf-8 -*-
"""v3.9.809 — AS-Zeit -> Zeiterfassung-Uebernahme (Sebastian-Entscheid 21.07., MASSGEBLICH).

ZIEL-REGEL:
- Uebernahme GENAU EINMAL je Schein (Idempotenz ueber Marker ze_uebernommen, NICHT ueber
  "existiert ein time_entry"). Geloeschter time_entry bleibt geloescht -> nie Auto-Neu.
- Spaetere Schein-Zeit-Aenderung: MONTEUR -> time_entry zieht automatisch mit (Update ohne Rueckfrage);
  BUERO/PL -> _confirmModal, nur bei Ja. Edge (Sebastian-DEFAULT): eine Buero-Handkorrektur wird durch
  eine spaetere Monteur-Aenderung ueberschrieben (Monteur laeuft ohne confirm).
- 2B: hours = (fahrzeit+stunden)/60. 4B: project_id leer, taetigkeit "Arbeitsschein <Nr>".
- Bestehender Schreibweg (addEntry-Muster SQ /api/entries fuer den Insert, _sbPatch fuer das Update),
  time_entries + ze_uebernommen sind NIE Push-Felder -> KEIN Juprowa/OFFA-Push.

Die pure Entscheidungslogik (_asUebernahmeBedarf/_asUebernahmeStunden/_asZeitRolleConfirm) per node-eval;
der async I/O-Teil (_sbGet/_confirmModal/SQ/_sbPatch) ist nicht node-testbar -> Verdrahtung statisch gepinnt.
"""
from conftest import run_node_snippet, _extract_fn


def _call(node_exe, index_html, name, js):
    src = _extract_fn(index_html, name)
    assert src, name + " nicht in index.html gefunden"
    snip = src + ";process.stdout.write(String(" + name + "(" + js + ")))"
    return run_node_snippet(node_exe, snip).strip()


# ── T1-Trigger (Zeit + Arbeit begonnen + Monteur), Marker NICHT Teil von _asUebernahmeBedarf ──
def test_trigger_t1(node_exe, index_html):
    base = "{id:'x',monteur:'w2',fahrzeit:15,stunden:390,"
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", base + "scheinstatus:'in_bearbeitung'}") == "true"
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", base + "scheinstatus:'erledigt'}") == "true"
    # Arbeit noch nicht begonnen -> nicht zu frueh uebernehmen.
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", base + "scheinstatus:'aufgenommen'}") == "false"
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", base + "scheinstatus:'freigegeben'}") == "false"


def test_bedarf_guards(node_exe, index_html):
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", "{id:'x',monteur:'w2',fahrzeit:0,stunden:0,scheinstatus:'in_bearbeitung'}") == "false"
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", "{id:'x',monteur:'',fahrzeit:15,scheinstatus:'in_bearbeitung'}") == "false"
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", "{monteur:'w2',fahrzeit:15,scheinstatus:'in_bearbeitung'}") == "false"
    # #5: stornierter Schein bucht NIE (auch mit Zeit).
    assert _call(node_exe, index_html, "_asUebernahmeBedarf", "{id:'x',monteur:'w2',fahrzeit:15,stunden:30,scheinstatus:'storniert'}") == "false"


# ── 2B: Fahrt + Arbeit = EIN Stundenwert ──
def test_stunden_2b(node_exe, index_html):
    assert _call(node_exe, index_html, "_asUebernahmeStunden", "{fahrzeit:15,stunden:390}") == "6.75"
    assert _call(node_exe, index_html, "_asUebernahmeStunden", "{fahrzeit:30,stunden:30}") == "1"
    assert _call(node_exe, index_html, "_asUebernahmeStunden", "{fahrzeit:0,stunden:0}") == "0"


# ── Rollen-Weiche: Office (Buero/PL/Admin) braucht confirm, Monteur-Rollen laufen auto ──
def test_rolle_confirm(node_exe, index_html):
    # #7 Denylist: Office UND unbekannte/leere Rollen -> confirm (sicherer Default); nur Feld-Rollen -> auto.
    for confirm in ("buero", "projektleiter", "admin", "", "lager", "unbekannt"):
        assert _call(node_exe, index_html, "_asZeitRolleConfirm", "'" + confirm + "'") == "true", confirm
    for feld in ("monteur", "helfer", "obermonteur", "techniker"):
        assert _call(node_exe, index_html, "_asZeitRolleConfirm", "'" + feld + "'") == "false", feld


# ── Verdrahtung (I/O nicht node-testbar -> statisch gepinnt) ──
def test_verdrahtung(index_html):
    assert "const _asZeitUebernahme=async(schein)=>{" in index_html, "async Uebernahme-Helfer fehlt"
    # #2 Idempotenz ueber MARKER aus dem STATE (_row), nicht ueber gemergtes s (kein stale-Form-Shadow); create nur wenn !ze_uebernommen.
    assert "if(!_row.ze_uebernommen){" in index_html, "Marker-Gate (create-once, auf _row) fehlt"
    assert "updAs(s.id,{ze_uebernommen:true});" in index_html, "Marker-Set fehlt"
    # #4 Update nur bei echter Schein-Zeit-Aenderung (Vergleich _row vs s).
    assert "if(Number(_row.fahrzeit||0)===Number(s.fahrzeit||0)&&Number(_row.stunden||0)===Number(s.stunden||0))return;" in index_html, "Zeit-Aenderungs-Gate fehlt"
    # 2B/4B Insert-Format ueber awaited _sbPost (v811 #3: r.ok-bestaetigt).
    assert ('await _sbPost("time_entries",{id:_eid,worker_id:s.monteur,project_id:"",'
            'arbeitsschein_id:s.id,date:_tag,hours:_h,taetigkeit:"Arbeitsschein "+(s.nummer||"")' in index_html), \
        "Insert-Format (awaited _sbPost, 4B project_id leer / arbeitsschein_id / taetigkeit) veraendert"
    # #3 (v811): Marker ze_uebernommen NUR nach bestaetigtem Insert -> updAs(marker) steht NACH dem awaited _sbPost.
    _ins = index_html.index('await _sbPost("time_entries"')
    _mrk = index_html.index("updAs(s.id,{ze_uebernommen:true});")
    assert _mrk > _ins, "Marker-Set (updAs) steht nicht NACH dem awaited Insert -> stiller Verlust moeglich"
    # Insert-Fehler -> catch -> return OHNE Marker (Retry beim naechsten Save).
    assert "return;/* Marker NICHT setzen" in index_html, "catch-Zweig bricht nicht sauber ohne Marker ab"
    # Spaetere Aenderung: bestehenden Eintrag ueber arbeitsschein_id finden.
    assert '_sbGet("time_entries","arbeitsschein_id=eq."+encodeURIComponent(s.id)+"&select=id,hours")' in index_html
    # Geloescht bleibt geloescht -> kein Auto-Neu.
    assert "if(!_ex||!_ex.length)return;" in index_html, "geloescht-bleibt-geloescht-Guard fehlt"
    # Nur bei echter Aenderung anfassen.
    assert "if(Math.abs(Number(_cur.hours||0)-_h)<0.005)return;" in index_html, "no-op-bei-unveraendert-Guard fehlt"
    # Office -> confirm; Monteur -> auto (kein confirm-Zweig). Edge faellt aus "Monteur ohne confirm".
    assert "if(_asZeitRolleConfirm(curUser&&curUser.role)){" in index_html, "Rollen-Weiche-Gate fehlt"
    assert "_confirmModal(" in index_html
    # Update ueber den bestehenden _sbPatch-Weg.
    assert 'await _sbPatch("time_entries",_cur.id,{hours:_h});' in index_html, "Update-Pfad fehlt"
    # Trigger sitzt am saveAs-Ende.
    assert "_asZeitUebernahme({..._finalForm,id:editId});" in index_html, "saveAs-Trigger fehlt"


def test_kein_juprowa_kein_push(index_html):
    a = index_html.index("const _asZeitUebernahme=async(schein)=>{")
    b = index_html.index("\n  };", a)
    block = index_html[a:b]
    assert "juprowa" not in block.lower(), "Uebernahme darf keinen Juprowa/Push-Bezug haben"
    assert 'await _sbPost("time_entries"' in block, "Insert nicht ueber awaited _sbPost (v811 #3)"
    assert '_sbPatch("time_entries"' in block, "Update nicht ueber _sbPatch"
    # scheinart-Push (v799) bleibt entfernt -> kein Push-Pfad-Regress.
    start = index_html.index("const JUPROWA_PUSH_FIELDS={")
    pf = index_html[start:index_html.index("};", start)]
    assert "scheinart:'AK_AUFART'" not in pf
