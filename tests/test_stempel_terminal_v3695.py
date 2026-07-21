"""v3.9.695 Terminal-User lauffaehig — Rollenquellen-Konsolidierung.

WARUM DAS EIN EIGENER TESTBLOCK IST:
Die erste Fassung von STEMPEL_TERMINAL erkannte die Rolle ueber den JWT-Claim
`app_metadata.role`. Das waere STILL gescheitert: der Client liest diesen Claim nirgends
(das Wort kommt in index.html kein einziges Mal vor), und `auth_role()` — der Helper, auf
dem der Grossteil der RLS sitzt — liest `public.users.role`. Das Terminal haette sich
erfolgreich angemeldet und waere danach an jeder einzelnen Policy verhungert.

ENTSCHEID: EINE Rollenwahrheit = auth_role() = public.users.role. Die Tests halten fest,
dass der Client diese Wahrheit benutzt und nicht heimlich wieder ein JWT parst.
"""
import re


def _code(s):
    """Block-Kommentare entfernen — geprueft wird der CODE, nicht die Prosa.

    Ohne das pruefen sich die Regressionstests unten selbst ins Knie: die Datei ERKLAERT in
    Kommentaren ausfuehrlich, warum sie app_metadata / einen rohen workers-Read /
    return=representation NICHT benutzt. Ein nackter Substring-Test findet genau diese
    Erklaerungen und schlaegt Alarm ueber die Warnung statt ueber den Fehler.
    """
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


# ══════════════════════════════════════════════════════════════════════════════
# 1) Rollenquelle
# ══════════════════════════════════════════════════════════════════════════════
def test_client_parst_niemals_das_jwt(index_html):
    """Die Regression, die alles ausgeloest hat: kein app_metadata im Client."""
    assert "app_metadata" not in _code(index_html), \
        "Der Client liest wieder einen JWT-Claim. Die Rollenwahrheit ist public.users.role " \
        "(curUser.role / auth_role()) — sonst laufen Client und RLS auseinander."


def test_terminal_rolle_wird_wie_lager_display_erkannt(index_html):
    assert "const _isStempelTerminal=curUser.role==='stempel_terminal';" in index_html
    # Gegenprobe: das Vorbild steht unveraendert daneben.
    assert "const _isLagerDisplay=curUser.role==='lager_display';" in index_html


# ══════════════════════════════════════════════════════════════════════════════
# 2) Das Gate
# ══════════════════════════════════════════════════════════════════════════════
def test_gate_laesst_terminal_durch(index_html):
    assert "_canKiosk=_isLagerDisplay||_isStempelTerminal||(curUser.role==='admin'&&!!_kioskScreen)" in index_html
    assert "if(_scr==='stempel'&&(_isStempelTerminal||curUser.role==='admin'))" in index_html


def test_terminal_kommt_nur_auf_die_stempeltafel(index_html):
    """Sperre, nicht Komfort: das Stempel-Terminal wird IMMER auf 'stempel' gezwungen (kein ?screen-Umweg auf
    den Wochenplan). v3.9.784: nur der Nicht-Terminal-Fallback wurde erweitert (Boot-aufgeloeste Ansicht
    window.__kioskScreen > ?screen > Default 'monteure', ueberlebt den ?cc=-Hardreset). Der Terminal-Zweig
    ('stempel' zuerst) ist unveraendert."""
    assert "const _scr=_isStempelTerminal?'stempel':((typeof window!=='undefined'&&window.__kioskScreen)||_kioskScreen||'monteure');" in index_html


def test_monteur_kommt_weiterhin_nicht_rein(index_html):
    """Das Gate kennt genau drei Wege hinein: lager_display, stempel_terminal, admin+?screen.
    Ein Monteur (oder buero/PL) erfuellt keinen davon."""
    m = re.search(r"const _canKiosk=(.*?);", index_html)
    assert m
    bedingung = m.group(1)
    for rolle in ("monteur", "buero", "projektleiter", "techniker", "helfer"):
        assert rolle not in bedingung, f"Rolle '{rolle}' kommt im Kiosk-Gate vor"


# ══════════════════════════════════════════════════════════════════════════════
# 3) workers-Ladeweg ueber die RPC
# ══════════════════════════════════════════════════════════════════════════════
def test_workers_kommen_aus_der_rpc(index_html):
    assert "SB_REST+'/rpc/stempel_terminal_workers'" in index_html


def test_kein_roher_workers_read_mehr_in_der_tafel(index_html):
    """Der rohe Read wuerde nicht nur an der fehlenden Policy scheitern — er wuerde bei
    einem Staff-Login SVNR/Reisepass/Telefon in den Speicher eines Wandpanels holen.
    RLS ist eine ZEILEN-, keine SPALTEN-Sperre; nur die RPC kann Spalten wegschneiden."""
    m = re.search(r"function StempelTafel\(props\)\{.*?\n\}\n", index_html, re.S)
    assert m, "StempelTafel nicht gefunden"
    tafel = _code(m.group(0))
    assert "_sbGet('workers'" not in tafel


def test_rpc_fehler_wird_klassifiziert(index_html):
    """Fehlende RPC (SQL nicht gelaufen) != Netzproblem — Teil-A-Muster."""
    m = re.search(r"function StempelTafel\(props\)\{.*?\n\}\n", index_html, re.S)
    tafel = m.group(0)
    assert "_stErrKind(e)" in tafel
    assert "sql/STEMPEL_TERMINAL_v2.sql" in tafel


# ══════════════════════════════════════════════════════════════════════════════
# 4) Antrag: PK-Konflikt statt SELECT
# ══════════════════════════════════════════════════════════════════════════════
def _submit(index_html):
    m = re.search(r"async function _submitAntrag\(\)\{.*?\n  \}", index_html, re.S)
    assert m, "_submitAntrag nicht gefunden"
    return m.group(0)


def test_antrag_liest_absences_nicht(index_html):
    """Das Terminal hat bewusst NUR eine INSERT-Policy auf absences. Ein SELECT waere ein
    Datenschutz-Rueckschritt (fremde Abwesenheiten am oeffentlichen Wandpanel) und wuerde
    an der RLS ohnehin scheitern."""
    body = _code(_submit(index_html))
    assert "_sbGet('absences'" not in body
    assert "return=representation" not in body


def test_doppelantrag_wird_am_pk_konflikt_erkannt(index_html):
    body = _submit(index_html)
    assert "r.status===409" in body
    assert "23505" in body
    assert "skip++" in body


def test_status_bleibt_beantragt(index_html):
    """Unveraendert kritisch: der DB-Trigger guard_urlaub_edit() prueft hart auf 'beantragt'."""
    body = _submit(index_html)
    assert "status:'beantragt'" in body
    assert "status:'ausstehend'" not in body


def test_netzfehler_wird_ehrlich_gemeldet(index_html):
    """Kein SyncQueue-Nachreichen beim Antrag: eine nachgereichte Zeile wuerde ihr Duplikat
    still schlucken (ignore-duplicates) und der Monteur wuesste nie, ob er beantragt hat."""
    body = _submit(index_html)
    assert "_stErrKind(e)==='net'" in body
    assert "Keine Verbindung" in body


# ══════════════════════════════════════════════════════════════════════════════
# 5) Der Zustand "Trigger noch nicht freigeschaltet"
#
# Abschnitt 5 von STEMPEL_TERMINAL_v2.sql ist STILLGELEGT: die Repo-Rekonstruktion des
# Live-Triggers (security_triggers_LIVE_v3911.sql) war unvollstaendig — Live 1746 Zeichen
# normalisiert, Repo 953 — ein CREATE OR REPLACE haette ~800 Zeichen Live-Logik kommentarlos
# geloescht. Bis der echte Live-Body vorliegt (v3), lehnt guard_urlaub_edit() jeden
# Terminal-Antrag mit RAISE EXCEPTION ab (PostgREST -> HTTP 400, 'urlaub: ...' im Body).
#
# Das ist ein ERWARTETER Zwischenzustand, kein Bug. Der Monteur steht aber vor der Wand und
# darf dafuer kein nacktes "Fehler" sehen.
# ══════════════════════════════════════════════════════════════════════════════
def test_trigger_ablehnung_wird_verstaendlich_gemeldet(index_html):
    body = _submit(index_html)
    assert "indexOf('urlaub:')" in body, \
        "Die Trigger-Ablehnung wird nicht erkannt — der Monteur saehe nur 'Antrag konnte nicht " \
        "eingereicht werden' und wuesste nicht, dass Stempeln trotzdem geht."
    assert "noch nicht freigeschaltet" in body
    assert "Stempeln funktioniert normal" in body, \
        "Die Meldung muss sagen, was WEITERHIN geht — sonst probiert der Mann auch das Stempeln nicht."
