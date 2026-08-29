"""v3.9.691 Stempeluhr Teil A (Rollout-Haerte).

Zwei Bereiche im Sentinel-Block STEMPEL-HELPERS (Z.2037-2085) und in der Komponente
StempelTafel (ab Z.5774):

  1) _stErrKind(e) klassifiziert Lesefehler in 'missing' (Tabelle/Spalte fehlt, SQL nicht
     gelaufen) / 'net' (Netz weg, Stempel wird nachgereicht) / 'other' (unbekannt, kein Write).
     STEMPEL_HID_GAP_MS=200 ist die Inter-Key-Timeout-Konstante fuer den HID-Wedge-Puffer.
  2) Rollout-Haertung in StempelTafel: Inter-Key-Timeout (Puffer verwirft sich bei Luecke
     > STEMPEL_HID_GAP_MS, NICHT bei Enter selbst), Entfernen des lokalen _uuid-Schattens
     (der einen Nicht-UUID-Fallback 'st_'+Date.now()+... hatte -> 22P02 in Postgres ->
     Stempel landet still in syncQueueFailed) und der
     Netzfehler-Pfad, der (anders als 'missing') KEIN return vor dem SQ.push hat.
"""
import re
import json
import pytest
from conftest import run_node_snippet, _extract_fn


def _helpers(index_html):
    m = re.search(r"//@STEMPEL-HELPERS-START(.*?)//@STEMPEL-HELPERS-END", index_html, re.S)
    assert m, "STEMPEL-HELPERS-Block nicht gefunden (Sentinel-Kommentare fehlen)"
    return m.group(1)


def _eval(node_exe, index_html, expr):
    snippet = _helpers(index_html) + "\nprocess.stdout.write(JSON.stringify((" + expr + ")))"
    return json.loads(run_node_snippet(node_exe, snippet))


def _stempel_tafel_src(index_html):
    src = _extract_fn(index_html, "StempelTafel")
    assert src, "function StempelTafel nicht gefunden"
    return src


# ═══════════════════════════════════════════════════════════════════
# 1) _stErrKind — pure Klassifizierung (Node-Eval)
# ═══════════════════════════════════════════════════════════════════
def test_errkind_missing_http404_mit_42p01(node_exe, index_html):
    expr = "_stErrKind(new Error('HTTP404 {\"code\":\"42P01\",\"message\":\"relation missing\"}'))"
    assert _eval(node_exe, index_html, expr) == "missing"


def test_errkind_missing_does_not_exist_text(node_exe, index_html):
    expr = "_stErrKind(new Error('column \"nfc_uid\" does not exist'))"
    assert _eval(node_exe, index_html, expr) == "missing"


def test_errkind_net_failed_to_fetch(node_exe, index_html):
    expr = "_stErrKind(new Error('Failed to fetch'))"
    assert _eval(node_exe, index_html, expr) == "net"


def test_errkind_net_http5xx(node_exe, index_html):
    expr = "_stErrKind(new Error('HTTP500 boom'))"
    assert _eval(node_exe, index_html, expr) == "net"


def test_errkind_other_http400(node_exe, index_html):
    # 400 ist weder in der missing- noch in der net-Liste (die net-Liste kennt nur
    # HTTP408/HTTP429/HTTP5xx) -> faellt durch auf 'other', kein stiller Write-Versuch.
    expr = "_stErrKind(new Error('HTTP400 kaputt'))"
    assert _eval(node_exe, index_html, expr) == "other"


def test_hid_gap_ms_konstante(node_exe, index_html):
    assert _eval(node_exe, index_html, "STEMPEL_HID_GAP_MS") == 200


# ═══════════════════════════════════════════════════════════════════
# 2) Inter-Key-Timeout im Key-Handler — String-Asserts gegen index_html
# ═══════════════════════════════════════════════════════════════════
def test_interkey_timeout_verwirft_puffer_bei_grosser_luecke(index_html):
    assert "if(e.key&&e.key.length===1){_buf.current=(_gap>STEMPEL_HID_GAP_MS?\"\":_buf.current)+e.key;}" in index_html


def test_enter_zweig_steht_vor_zeichen_zeile_und_ist_ungefiltert(index_html):
    """Der Reset gilt NICHT fuer Enter: der Enter-Zweig steht VOR der Zeichen-Zeile im
    Quelltext und liest _buf.current roh, ohne die Gap-Pruefung."""
    enter_line = "if(e.key==='Enter'){const uid=_buf.current;_buf.current=\"\";if(uid)_process(uid);return;}"
    char_line = "if(e.key&&e.key.length===1){_buf.current=(_gap>STEMPEL_HID_GAP_MS?\"\":_buf.current)+e.key;}"
    assert enter_line in index_html
    assert char_line in index_html
    assert index_html.index(enter_line) < index_html.index(char_line)
    # Der Enter-Zweig selbst enthaelt keinerlei Gap-/Timeout-Pruefung.
    assert "STEMPEL_HID_GAP_MS" not in enter_line


# ═══════════════════════════════════════════════════════════════════
# 3) Regression: lokaler _uuid-Schatten entfernt
# ═══════════════════════════════════════════════════════════════════
def test_kein_lokales_uuid_schatten_in_stempeltafel(index_html):
    """v3.9.691 Teil A: In StempelTafel gab es vormals ein LOKALES `const _uuid=...`, das
    das globale _uuid (echte RFC4122-v4, mit crypto.randomUUID + getRandomValues-Fallback)
    ueberschattete. Der lokale Fallback war 'st_'+Date.now()+... — KEINE gueltige uuid.
    stempel_log.id ist als uuid-Spalte typisiert; Postgres haette den Insert mit 22P02
    (invalid input syntax for type uuid) abgelehnt. doSync wertet das nach 5 Versuchen als
    permanenten Fehler -> der Stempel landet lautlos in syncQueueFailed, der Kiosk quittiert
    aber gruen: die Schicht des Mitarbeiters fehlt, ohne dass irgendwer es merkt. Betroffen
    waere jeder Kiosk OHNE Secure Context (http://192.168.x.x im LAN) gewesen, weil
    crypto.randomUUID nur unter https/localhost existiert und genau dort der Fallback griff.
    Das globale _uuid (Z.4102) hat einen korrekten v4-Fallback und ist vom Selbsttest TC-U
    abgedeckt. Diese Zeile prueft: kein `const _uuid=` mehr innerhalb der Komponente."""
    src = _stempel_tafel_src(index_html)
    assert "const _uuid=" not in src


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_st_id_fallback_string_lebt_nur_noch_in_kommentaren(index_html):
    """ABWEICHUNG vom Auftrag: der Auftrag verlangt woertlich, dass der String
    'st_'+Date.now() NIRGENDS mehr im File vorkommt. Das stimmt so nicht ganz — der String
    taucht laut index.html an zwei Stellen weiterhin als PROSA auf: im Selbsttest-Titel
    (Zeile ~2818, "UUID-Schatten entfernt: ... Fallback 'st_'+Date.now() ...") und im
    Erklaerkommentar direkt vor StempelTafel (Zeile ~5804), die BEIDE den behobenen Bug
    dokumentieren. Das ist beabsichtigt und korrekt — der Kommentar erklaert ja gerade,
    WARUM der Schatten weg ist. Ein harter `assert "'st_'+Date.now()' not in index_html`
    wuerde daher fehlschlagen, obwohl der Bug behoben ist. Diese Tests pruefen stattdessen
    das, was wirklich zaehlt: der String kommt nirgends mehr als CODE vor, das heisst nicht
    mehr in einer Zuweisung/als Objekt-Property, die daraus eine id baut."""
    assert index_html.count("'st_'+Date.now()") == 2, (
        "Erwartet: Fallback-String kommt genau in den zwei bekannten Kommentaren vor "
        "(Selbsttest-Titel + Erklaerkommentar) — Anzahl hat sich veraendert, bitte pruefen."
    )
    # Kein Code-Muster, das aus dem String eine id baut (z.B. `id:'st_'+Date.now()` oder
    # `='st_'+Date.now()` als Zuweisung).
    assert re.search(r"[:=]\s*'st_'\+Date\.now\(\)", index_html) is None
    # Die tatsaechlich verwendete id-Erzeugung ist das globale _uuid().
    assert "const row={id:_uuid(),worker_id:worker.id,direction:dir,ts:nowIso,device:_dev};" in index_html


# ===============================================================
# 4) _evCache - v3.9.899 ENTFERNT, samt der Ref selbst
# ===============================================================
# Dieser Abschnitt hatte DREI Zusicherungen. Zwei davon sicherten eine echte
# Eigenschaft (die Ref wird aus dem Read befuellt / nach dem Schreiben
# nachgefuehrt) - sie wurden in v3.9.769 korrekt stillgelegt, mit der
# Begruendung: der Pin testet toten Code. Die dritte,
#
#     def test_evcache_existiert_als_ref(index_html):
#         assert "const _evCache=_react.useRef.call(void 0, {});" in index_html
#
# sicherte nur die EXISTENZ und blieb aktiv. Sie hat damit ein Jahr lang eine
# Ref am Leben gehalten, in die nichts schreibt und aus der niemand liest -
# und mit ihr den Kommentar daneben, der drei Zusagen machte, die es nie gab.
# Genau wie _kapReal in v3.9.896: die Existenz toter Zeilen ist keine
# Eigenschaft. Die Nachfolge-Zusicherung steht in test_niegelesen_v899.py -
# sie prueft, dass die Richtung weiter vom Server kommt (RPC
# stempel_terminal_stempel) und der Lesepfad bei 401/403 abbricht, statt
# offline zu raten. Das ist die Eigenschaft; die Ref war nur ihr Schatten.


# ═══════════════════════════════════════════════════════════════════
# 5) Netzfehler-Pfad erreicht trotzdem SQ.push (kein return im net-Zweig)
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_missing_zweig_endet_mit_return(index_html):
    assert "if(_kind==='missing'){setTblErr('stempel_log fehlt — sql/STEMPEL_v1.sql ausführen');_showFb({kind:'error'});return;}" in index_html


@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_net_zweig_endet_nicht_mit_return_vor_offline_true(index_html):
    """Nach der missing-Pruefung faengt `if(_kind!=='net'){...return;}` den 'other'-Fall ab
    (return) — der verbleibende 'net'-Fall faellt OHNE eigenen return direkt durch zu
    `_offline=true;` und damit weiter bis zum SQ.push. Ein Netzfehler darf den Scan also
    NIE kommentarlos verwerfen."""
    assert "if(_kind!=='net'){_showFb({kind:'error'});return;}\n        _offline=true;" in index_html
    assert "SQ.push({url:'/api/stempel-log',method:'POST',body:row});" in index_html


# ═══════════════════════════════════════════════════════════════════
# 6) device-Werte fuer offline-gebuchte Stempel
# ═══════════════════════════════════════════════════════════════════
@pytest.mark.skip(reason="v3.9.769 Stufe 1 Weg B: der alte Client-INSERT-Scanpfad (Lookup+Read+direkter stempel_log-POST, evCache, SQ.push-Offline-Puffer, Client-Cooldown/Uebernacht/Netto am Panel) ist durch den SECURITY-DEFINER-RPC stempel_terminal_stempel ersetzt. Richtung/Doppel-Scan/Uebernacht leben jetzt im RPC (sql/STEMPEL_TERMINAL_RPC_v3.sql, gepinnt in test_stempel_terminal_rpc_v769), kein-falsches-gruen + Client-Cooldown + unknown-Chip im neuen App-Pfad (ebd.). Dieser Pin testet toten Code.")
def test_device_werte_kiosk_offline_varianten(index_html):
    assert "const _dev=_unsicher?'kiosk:offline?':(_offline?'kiosk:offline':'kiosk');" in index_html
