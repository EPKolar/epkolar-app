"""v3.9.693 Stempeluhr Teil F + G.

TEIL F — NFC-Chip im Mitarbeiter-Formular (WorkerNfcPanel):
  Chips koennen im Buero zugeordnet werden statt nur am Kiosk. Drei Fallen, die hier
  festgenagelt werden:
    - Enter im Chip-Feld darf das UMGEBENDE Worker-Formular nicht submitten (der HID-Wedge
      schliesst jede UID mit Enter ab — ohne preventDefault haette jeder Chip-Scan nebenbei
      den ganzen Mitarbeiter-Datensatz gespeichert).
    - Kollisionspruefung VOR dem Patch, gegen einen FRISCHEN Read (nicht gegen lokalen State).
    - 23505 (unique_violation auf workers_nfc_uid_uidx) wird abgefangen und uebersetzt.

TEIL G — Urlaubs-/ZA-Antrag am Wandpanel:
  Der Antrag geht EXAKT den bestehenden Self-Service-Datenweg (submitRequest in AbsView).
  Der kritischste Punkt: status ist woertlich 'beantragt'. 'ausstehend' ist NUR der
  Client-Map-Wert — der DB-Trigger guard_urlaub_edit() prueft hart auf 'beantragt', ein
  Antrag mit 'ausstehend' wuerde an der DB scheitern.
"""
import re


# ══════════════════════════════════════════════════════════════════════════════
# TEIL F — WorkerNfcPanel
# ══════════════════════════════════════════════════════════════════════════════
def test_nfc_panel_existiert(index_html):
    assert "function WorkerNfcPanel(" in index_html


def test_nfc_panel_ist_eingehaengt(index_html):
    assert "React.createElement(WorkerNfcPanel," in index_html


def test_enter_submittet_das_worker_formular_nicht(index_html):
    """Der HID-Wedge schliesst mit Enter ab. Ohne preventDefault+stopPropagation haette
    ein Chip-Scan das umgebende Formular abgeschickt."""
    m = re.search(r"function WorkerNfcPanel\(.*?\n\}\n", index_html, re.S)
    assert m, "WorkerNfcPanel-Koerper nicht gefunden"
    body = m.group(0)
    assert "if(e.key==='Enter'){e.preventDefault();e.stopPropagation();" in body


def test_kollisionspruefung_gegen_frischen_read(index_html):
    """Nicht gegen den lokalen State pruefen — ein anderer Buero-Rechner koennte den Chip
    gerade vergeben haben."""
    m = re.search(r"function WorkerNfcPanel\(.*?\n\}\n", index_html, re.S)
    body = m.group(0)
    assert "_sbGet('workers','nfc_uid=eq.'" in body
    assert "bereits" in body  # "Chip ist bereits <Name> zugeordnet."


def test_23505_wird_abgefangen(index_html):
    m = re.search(r"function WorkerNfcPanel\(.*?\n\}\n", index_html, re.S)
    body = m.group(0)
    assert "23505" in body, "unique_violation vom Index workers_nfc_uid_uidx wird nicht behandelt"


def test_chip_entfernen_setzt_null(index_html):
    m = re.search(r"function WorkerNfcPanel\(.*?\n\}\n", index_html, re.S)
    body = m.group(0)
    assert "_sbPatch('workers',workerId,{nfc_uid:null})" in body


def test_kein_neues_ddl_noetig(index_html):
    """Spalte + Unique-Index existieren bereits aus STEMPEL_v1.sql — das Panel darf
    keinen neuen REST-Pfad erfinden."""
    m = re.search(r"function WorkerNfcPanel\(.*?\n\}\n", index_html, re.S)
    body = m.group(0)
    assert "_sbPatch('workers'" in body
    assert "/api/" not in body  # kein eigener SyncQueue-Pfad


# ══════════════════════════════════════════════════════════════════════════════
# TEIL G — Antrag am Terminal
# ══════════════════════════════════════════════════════════════════════════════
def _submit(index_html):
    m = re.search(r"async function _submitAntrag\(\)\{.*?\n  \}", index_html, re.S)
    assert m, "_submitAntrag nicht gefunden"
    return m.group(0)


def test_status_ist_beantragt_nicht_ausstehend(index_html):
    """DER kritische Test des ganzen Features.

    'ausstehend' ist nur der Client-seitige Wert der absApprovals-Map. Der DB-Trigger
    guard_urlaub_edit() prueft COALESCE(NEW.status,'beantragt')='beantragt'. Ein Antrag mit
    status='ausstehend' wuerde von der DB abgelehnt — und zwar erst beim Sync, also lange
    nachdem der Monteur am Panel ein gruenes Haekchen gesehen hat.
    """
    body = _submit(index_html)
    assert "status:'beantragt'" in body
    assert "status:'ausstehend'" not in body


def test_ein_datensatz_pro_werktag(index_html):
    """Kein Range-Datensatz: from_date == to_date, PK = Name_YYYY-MM-DD (wie submitRequest)."""
    body = _submit(index_html)
    assert "from_date:ds,to_date:ds" in body
    assert "id:aWorker.name+'_'+ds" in body


def test_wochenende_und_feiertage_uebersprungen(index_html):
    """_stdVonTagK liefert an Sa/So/Feiertag 0 -> kein Antragsdatensatz, exakt wie im App-Self-Service."""
    body = _submit(index_html)
    assert "_stdVonTagK(d,38.5)" in body
    assert "if(std<=0)continue;" in body


def test_schreibweg_ist_die_syncqueue(index_html):
    body = _submit(index_html)
    assert "SQ.push({url:'/api/absences',method:'POST'" in body


def test_doppelantrag_wird_uebersprungen_nicht_ueberschrieben(index_html):
    body = _submit(index_html)
    assert "skip++" in body
    assert "bereits" in body


def test_identifikation_stempelt_nicht(index_html):
    """Im Antrags-Modus identifiziert der Scan nur — er darf keinen Stempel buchen."""
    assert "if(_amodeRef.current==='ident')" in index_html


def test_timeout_vergisst_die_identifikation(index_html):
    """Datenschutz am Wandpanel: nach 30s faellt jeder Screen auf Idle zurueck UND vergisst,
    wer sich identifiziert hat. Der Erfolgs-Screen haelt 5s."""
    m = re.search(r"const ms=\(amode==='done'\)\?5000:30000;", index_html)
    assert m, "30s-Timeout fehlt"
    m2 = re.search(r"setAmode\(''\);setAWorker\(null\);setAMsg\(''\);\},ms\);", index_html)
    assert m2, "Der Timeout vergisst die Identifikation nicht (setAWorker(null) fehlt)"


def test_keine_salden_am_panel(index_html):
    """Fremde Augen: am Wandpanel duerfen keine Urlaubssalden/Resturlaub stehen."""
    m = re.search(r"if\(amode\)\{.*?\n  \}", index_html, re.S)
    assert m, "Antrags-Screens nicht gefunden"
    screens = m.group(0)
    for verboten in ("_resturlaubK", "urlaubskontingent", "Resturlaub", "Saldo"):
        assert verboten not in screens, f"'{verboten}' darf am Wandpanel nicht sichtbar sein"
