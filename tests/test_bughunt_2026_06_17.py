"""Bug-Hunt-Marathon 2026-06-17 (v3.9.407) — Welle-1-Fixes.

Static-Source-Regression-Guards:
 - FleetView Service-Fälligkeit: date-only lokal parsen (+"T00:00:00"), kein UTC-Mitternacht-Flip.
 - Material-Order createdById: leerer FK -> null (nicht "").
 - Audit-CSV-Export: Formel-Injektion-Schutz im Zellen-Formatter.
"""
import re
from pathlib import Path

INDEX = Path(__file__).parent.parent / 'index.html'


def _txt():
    return INDEX.read_text(encoding='utf-8')


def test_fleetview_service_faellig_local_parse():
    """Positiv: FleetView serviceFaellig parst date-only lokal (+T00:00:00)."""
    text = _txt()
    assert 'const d=new Date(f.naechstService+"T00:00:00");return d<=new Date();' in text, \
        'v3.9.407 Regression: FleetView serviceFaellig muss +"T00:00:00" lokal parsen'


def test_fleetview_service_warn_local_parse():
    """Positiv: FleetView serviceWarn (Listen-Karte) parst date-only lokal."""
    text = _txt()
    assert 'f.naechstService&&new Date(f.naechstService+"T00:00:00")<=new Date()' in text, \
        'v3.9.407 Regression: FleetView serviceWarn muss +"T00:00:00" lokal parsen'


def test_fleetview_no_bare_naechstservice_utc_parse():
    """Negativ-Guard: bare new Date(f.naechstService) ohne T00:00:00 darf NICHT zurückkehren."""
    text = _txt()
    bad = re.findall(r'new Date\(f\.naechstService\)(?!\+)', text)
    assert not bad, \
        'v3.9.407 Regression: bare new Date(f.naechstService) (UTC-Flip) zurückgekehrt'


def test_material_order_created_by_id_null_not_empty():
    """Positiv: createdById faellt auf null (nicht "") -> FK/owner-RLS sauber."""
    text = _txt()
    assert '{createdById:(curUser&&curUser.monteurId)||null}' in text, \
        'v3.9.407 Regression: createdById muss ||null sein (FK-Null-Muster), nicht ||""'
    assert '{createdById:(curUser&&curUser.monteurId)||""}' not in text, \
        'v3.9.407 Regression: createdById ||"" (leerer FK) zurückgekehrt'


def test_audit_csv_formula_injection_guard():
    """Positiv: CSV-Zellen-Formatter neutralisiert fuehrende = + - @ \\t \\r."""
    text = _txt()
    # Eindeutiges Fragment des Formel-Injektion-Guards im Audit-CSV _cf-Formatter
    assert r'/^[=+\-@\t\r]/.test(s)' in text, \
        'v3.9.407 Regression: CSV _cf Formel-Injektion-Schutz fehlt'


# ── v3.9.408: Storage-Waisen-Fix (Bucket-Objekt beim Loeschen mitentfernen) ──

def test_sb_delete_obj_helper_exists():
    """Positiv: gemeinsamer Best-Effort Storage-Objekt-Delete-Helper existiert."""
    text = _txt()
    assert re.search(r'async function _sbDeleteObj\(bucket,path\)\{', text), \
        'v3.9.408 Regression: _sbDeleteObj-Helper fehlt'
    # Helper nutzt _authRetry + _fT + DELETE (kein roher fetch, kein JWT-Waise)
    seg = text[text.index('async function _sbDeleteObj'):text.index('async function _sbDeleteObj')+600]
    assert '_authRetry(' in seg and '_fT(' in seg and 'method:"DELETE"' in seg, \
        'v3.9.408 Regression: _sbDeleteObj muss _authRetry+_fT+DELETE nutzen'


def test_gefahrstoff_delfile_removes_object():
    """Positiv: gefahrstoff delFile entfernt Storage-Objekt mit."""
    text = _txt()
    assert 'if(fi.storage_path)_sbDeleteObj(SB_GEF_BUCKET,fi.storage_path)' in text, \
        'v3.9.408 Regression: delFile muss Storage-Objekt mitloeschen'


def test_gefahrstoff_delfolder_removes_objects():
    """Positiv: gefahrstoff delFolder entfernt Storage-Objekte der enthaltenen Dateien."""
    text = _txt()
    assert 'files.filter(x=>ids.has(x.folder_id)&&x.storage_path).forEach(x=>_sbDeleteObj(SB_GEF_BUCKET,x.storage_path))' in text, \
        'v3.9.408 Regression: delFolder muss Storage-Objekte der Ordner-Dateien mitloeschen'


def test_personaldoku_delitem_removes_object():
    """Positiv: fahrbew + anmeldung delItem entfernen Storage-Objekt mit (epkolar-docs)."""
    text = _txt()
    cnt = text.count('if(it.storage_path)_sbDeleteObj(SB_DOCS_BUCKET,it.storage_path)')
    assert cnt >= 2, \
        f'v3.9.408 Regression: beide delItem (fahrbew+anmeldung) muessen Storage-Objekt mitloeschen (gefunden {cnt})'


def test_delsvcdoc_uses_helper_not_raw_fetch():
    """Negativ-Guard: _delSvcDoc nutzt _sbDeleteObj statt rohem fetch ohne _authRetry."""
    text = _txt()
    sds = text[text.index('const _delSvcDoc='):text.index('const _delSvcDoc=')+400]
    assert '_sbDeleteObj(SB_FZ_BUCKET' in sds, \
        'v3.9.408 Regression: _delSvcDoc muss _sbDeleteObj nutzen'
    assert 'fetch(SB_STORAGE' not in sds, \
        'v3.9.408 Regression: _delSvcDoc darf keinen rohen fetch(SB_STORAGE ...) mehr nutzen'


# ── v3.9.409: P1 Tages-Mehrstunden + Rechte-Haertung (Defense-in-Depth) + onOnline ──

def test_tagesstz_mehrstunden_diff_not_full():
    """P1 Positiv: Tages-Stundenbestaetigung zeigt Mehrstunden-DIFFERENZ (dt-8.5), nicht volle dt."""
    text = _txt()
    assert '"eventuelle Mehrstunden: "+_n(dt-8.5,1)+"h"' in text, \
        'v3.9.409 Regression: Tages-Mehrstunden muss dt-8.5 sein (nicht volle Tagesstunden)'
    assert '"eventuelle Mehrstunden: "+_n(dt,1)+"h"' not in text, \
        'v3.9.409 Regression: alte volle-dt-Variante zurueckgekehrt'


def test_urlaub_bulk_handlers_admin_guard():
    """Positiv: updateEntry/bulkApprove/rejectAll tragen if(!isAdmin)return."""
    text = _txt()
    for sig in ['const updateEntry=(key,changes)=>{if(!isAdmin)return;',
                'const bulkApprove=()=>{if(!isAdmin)return;',
                'const rejectAll=m=>{if(!isAdmin)return;']:
        assert sig in text, f'v3.9.409 Regression: Handler-Guard fehlt: {sig}'


def test_gefahrstoff_handlers_canedit_guard():
    """Positiv: gefahrstoff addFolder/renameFolder/delFolder/delFile tragen if(!canEdit)return."""
    text = _txt()
    for sig in ['const addFolder=()=>{if(!canEdit)return;',
                'const renameFolder=(fo)=>{if(!canEdit)return;',
                'const delFolder=async(fo)=>{if(!canEdit)return;',
                'const delFile=async(fi)=>{if(!canEdit)return;']:
        assert sig in text, f'v3.9.409 Regression: gefahrstoff Handler-Guard fehlt: {sig}'
    # onUpload (gefahrstoff, folder_id:cur) muss !canEdit im Guard haben
    gu = text[text.index('const meta={id:id,folder_id:cur,')-1200:text.index('const meta={id:id,folder_id:cur,')]
    assert 'if(!fls||!fls.length||!canEdit)return;' in gu, \
        'v3.9.409 Regression: gefahrstoff onUpload braucht !canEdit-Guard'


def test_ononline_uses_countmine():
    """Positiv: onOnline-Auto-Flush nutzt SQ.countMine() (nicht count())."""
    text = _txt()
    assert 'const cnt=await SQ.countMine();/* v3.9.409' in text, \
        'v3.9.409 Regression: onOnline muss SQ.countMine() nutzen'


# ── v3.9.410: QuickEditPin Self-Assign-Klemme + Rechte-Haertung + Pickerl-TZ ──

def test_quickeditpin_self_assign_clamp():
    """P2 Positiv: QuickEditPin bekommt isMtField/vpMid-Props + klemmt assignee im _save."""
    text = _txt()
    assert 'function QuickEditPin({ticket, monteure, isAdmin, isMtField, vpMid,' in text, \
        'v3.9.410 Regression: QuickEditPin muss isMtField/vpMid-Props annehmen'
    assert 'const _isMtEdit=!!isMtField&&!isAdmin; const _effAsg=_isMtEdit?(vpMid||ticket.assignee):asg;' in text, \
        'v3.9.410 Regression: QuickEditPin _save muss assignee klemmen (wie TicketDetail)'
    # Call-Site reicht Props durch
    assert 'React.createElement(QuickEditPin, { ticket: quickTicket, monteure: monteure, isAdmin: isAdmin, isMtField: _vpIsField, vpMid: _vpMid,' in text, \
        'v3.9.410 Regression: QuickEditPin-Call-Site muss isMtField/vpMid durchreichen'


def test_saveproject_admin_guard():
    """Positiv: saveProject traegt if(!isAdmin)return."""
    text = _txt()
    assert 'const saveProject=()=>{\n    if(!isAdmin)return;' in text, \
        'v3.9.410 Regression: saveProject Handler-Guard fehlt'


def test_wz_save_pushwzsh_wzedit_guard():
    """Positiv: WZ save + _pushWzSh tragen canDo("wz_edit",curUser)-Guard."""
    text = _txt()
    assert 'const _pushWzSh=(wzId)=>{if(!canDo("wz_edit",curUser))return;' in text, \
        'v3.9.410 Regression: _pushWzSh wz_edit-Guard fehlt'
    assert 'const save=()=>{\n    if(!canDo("wz_edit",curUser))return;' in text, \
        'v3.9.410 Regression: WZ save wz_edit-Guard fehlt'


def test_zeit_inline_hours_canedit_guard():
    """Positiv: updateEntryHours traegt if(!_canEditEntry)return."""
    text = _txt()
    assert 'const updateEntryHours=(iso,entryIdx,newHours)=>{\n    if(!_canEditEntry)return;' in text, \
        'v3.9.410 Regression: updateEntryHours _canEditEntry-Guard fehlt'


def test_pickerl_deadline_local_parse():
    """Positiv: Pickerl-Deadline-Notification parst date-only lokal (+T00:00:00)."""
    text = _txt()
    assert 'const diff=Math.ceil((new Date(f.pickerl+"T00:00:00")-now)/TIME_DAY);if(diff>=0&&diff<=7)fire("fz_pick_"' in text, \
        'v3.9.410 Regression: Pickerl-Deadline muss +"T00:00:00" lokal parsen (wie Service)'


# ── v3.9.411: Input-Validierung (OCR-Dezimal + 24h-Cap) ──

def test_ocr_tank_prefill_dot_decimal():
    """P2 Positiv: Tank-Modal-Prefill nutzt Punkt-Dezimal (type=number-kompatibel)."""
    text = _txt()
    assert "String(init.liter).replace(',','.')" in text, \
        'v3.9.411 Regression: Liter-Prefill muss Punkt-Dezimal sein (type=number)'
    assert "String(init.preis).replace(',','.')" in text, \
        'v3.9.411 Regression: Preis-Prefill muss Punkt-Dezimal sein (type=number)'
    assert "String(init.liter).replace('.',',')" not in text, \
        'v3.9.411 Regression: alte Komma-Variante (leert type=number-Feld) zurueckgekehrt'


def test_zeit_24h_cap_matrix_and_inline():
    """Positiv: Stunden-24h-Obergrenze in saveMatrixCell + updateEntryHours (Paritaet addEntry)."""
    text = _txt()
    assert 'if(!isFinite(_h)||_h<0||_h>24){' in text, \
        'v3.9.411 Regression: saveMatrixCell braucht 24h-Obergrenze'
    assert 'if(newHours>24||newHours<0){window.__toast&&window.__toast("⚠️ Max 24 h pro Tag","warn");return;}' in text, \
        'v3.9.411/414 Regression: updateEntryHours braucht 24h-Cap + <0-Guard'


# ── v3.9.412: ChartBox fmt auch fuer HBar/Line/Pie/Donut (nicht nur Bar) ──

def test_chartbox_fmt_all_chart_types():
    """Positiv: SvgHBar/SvgLine/SvgPie nehmen fmt-Param + ChartBox reicht fmt an alle durch."""
    text = _txt()
    # Signaturen nehmen fmt
    assert 'function SvgHBar({data,width=300,height=0,color="#f97316",fmt})' in text, \
        'v3.9.412 Regression: SvgHBar muss fmt-Param nehmen'
    assert 'function SvgLine({data,width=320,height=150,color="#f97316",fmt})' in text, \
        'v3.9.412 Regression: SvgLine muss fmt-Param nehmen'
    assert 'function SvgPie({data,size=150,donut=false,fmt})' in text, \
        'v3.9.412 Regression: SvgPie muss fmt-Param nehmen'
    # ChartBox-Dispatch reicht fmt an alle Typen durch
    assert 'tp==="hbar"&&React.createElement(SvgHBar, { data: data, color: color, fmt: fmt})' in text, \
        'v3.9.412 Regression: ChartBox muss fmt an SvgHBar durchreichen'
    assert 'tp==="line"&&React.createElement(SvgLine, { data: data, color: color, fmt: fmt})' in text, \
        'v3.9.412 Regression: ChartBox muss fmt an SvgLine durchreichen'
    assert 'tp==="donut"&&React.createElement(SvgPie, { data: data, donut: true, fmt: fmt})' in text, \
        'v3.9.412 Regression: ChartBox muss fmt an SvgPie(donut) durchreichen'


# ── v3.9.413: Mobile/Lifecycle — Plan-Viewer Touch + Timer-Cleanup + a11y ──

def test_planviewer_touch_action_none():
    """P1 Positiv: Plan-Viewer Pointer-Surface hat touchAction:none (Pan/Pinch auf Touch)."""
    text = _txt()
    assert 'style: {position: "absolute", inset: 0, touchAction: "none"' in text, \
        'v3.9.413 Regression: Plan-Viewer Pointer-Surface braucht touchAction:none'


def test_stz_save_timers_unmount_cleanup():
    """P2 Positiv: stzSaveTimers werden beim Unmount geraeumt (kein setState-after-unmount)."""
    text = _txt()
    assert 'Object.values(stzSaveTimers.current).forEach(t=>{try{clearTimeout(t);}catch(_){}});},[]);' in text, \
        'v3.9.413 Regression: stzSaveTimers-Unmount-Cleanup fehlt'


def test_mobshellnav_aria_label():
    """P3 Positiv: mob-shell-nav Icon-Buttons haben aria-label."""
    text = _txt()
    assert "onClick: ()=>doNav(n.id), title: n.l, 'aria-label': n.l" in text, \
        'v3.9.413 Regression: mob-shell-nav aria-label fehlt'


# ── v3.9.414: Pickerl-Zaehler TZ-Konsistenz (Nachzug adversariale Review) ──

def test_no_bare_pickerl_utc_parse():
    """Negativ-Guard: bare new Date(f.pickerl) ohne T00:00:00 darf NICHT zurueckkehren
    (Pickerl-Zaehler 9525/19309 + Deadline-Notification — gleiche TZ-Bug-Klasse wie naechstService)."""
    text = _txt()
    bad = re.findall(r'new Date\(f\.pickerl\)(?!\+)', text)
    assert not bad, \
        f'v3.9.414 Regression: bare new Date(f.pickerl) (UTC-Flip) zurueckgekehrt ({len(bad)}x)'
