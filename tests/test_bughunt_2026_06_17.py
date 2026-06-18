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


# ── v3.9.415: Notif read-reconcile + TicketDetail-Badge status-aware ──

def test_notif_read_reconcile_monotonic():
    """P1 Positiv: Notif-Merge zieht read serverseitig nach (monoton true)."""
    text = _txt()
    assert 'const reconciled=prev.map(n=>srvById.has(n.id)?{...n,read:n.read||srvById.get(n.id).read}:n);' in text, \
        'v3.9.415 Regression: Notif read-reconcile (monoton) fehlt'
    assert 'const merged=[...reconciled,...srvMapped.filter(n=>!ids.has(n.id))]' in text, \
        'v3.9.415 Regression: Merge muss reconciled statt prev nutzen'


def test_ticketdetail_due_badge_status_aware():
    """P3 Positiv: TicketDetail-Faelligkeits-Badge nicht rot bei erledigt/storniert etc."""
    text = _txt()
    assert '(_dueIsPast(ticket.dueDate)&&ticket.status!=="erledigt"&&ticket.status!=="abgenommen"&&ticket.status!=="abgeschlossen"&&ticket.status!=="storniert")?"#ef4444":"#71717a"' in text, \
        'v3.9.415 Regression: TicketDetail-Badge muss Status ausschliessen'


# ── v3.9.416: a11y — PdfViewerModal ESC + Zeit-Sheet Tap-outside ──

def test_pdfviewer_esc_handler():
    """Positiv: PdfViewerModal hat ESC-Keydown-Handler."""
    text = _txt()
    assert 'const _h=e=>{if(e.key==="Escape")onClose();};window.addEventListener("keydown",_h);return ()=>window.removeEventListener("keydown",_h);},[onClose]);' in text, \
        'v3.9.416 Regression: PdfViewerModal ESC-Handler fehlt'


def test_zeit_sheet_tap_outside_close():
    """Positiv: Zeit-Eintrag-Bottom-Sheet schliesst per Tap-outside (Backdrop onClick + Panel stopPropagation)."""
    text = _txt()
    assert "onClick:()=>{setAddDay(null);setEditEntry(null);}/* v3.9.416: Tap-outside" in text, \
        'v3.9.416 Regression: Zeit-Sheet Backdrop-onClick fehlt'
    assert 'onClick:e=>e.stopPropagation()/* v3.9.416: Klicks im Panel schließen nicht */' in text, \
        'v3.9.416 Regression: Zeit-Sheet Panel-stopPropagation fehlt'


# ── v3.9.417: P1 Datenverlust (_syncThenReload) + Datums-Korrektheit ──

def test_bwb_edit_uses_synthenreload_not_blind_timeout():
    """P1 Negativ-Guard: editMonteurEntries/openMultiEntryEdit nutzen _syncThenReload,
    nicht mehr blinden setTimeout(loadAll,1000) der den Batch-Sync ueberholt."""
    text = _txt()
    assert 'setTimeout(()=>loadAll(true),1000)' not in text, \
        'v3.9.417 Regression: blinder setTimeout(loadAll,1000) zurueckgekehrt (Reload ueberholt Sync → Datenverlust)'


def test_dashboard_6month_no_setmonth_overflow():
    """P2 Positiv: 6-Monats-Charts nutzen new Date(y,m-i,1) (Tag 1), kein setMonth-Overflow."""
    text = _txt()
    assert 'const _dm=new Date();const d=new Date(_dm.getFullYear(),_dm.getMonth()-i,1);' in text, \
        'v3.9.417 Regression: 6-Monats-Loop muss Tag 1 explizit setzen'
    assert 'const d=new Date();d.setMonth(d.getMonth()-i);' not in text, \
        'v3.9.417 Regression: setMonth-Overflow-Variante zurueckgekehrt'


def test_fleet_service_termin_local_parse():
    """P2 Positiv: Fleet-Service-Termin-Liste parst t.datum date-only lokal."""
    text = _txt()
    assert 'const d=t.datum?new Date(t.datum+"T00:00:00"):null;' in text, \
        'v3.9.417 Regression: Fleet-Service-Termin braucht +"T00:00:00"'


def test_pickerl_badges_local_parse():
    """P3 Positiv: Dashboard-/QR-Pickerl-Badges parsen date-only lokal."""
    text = _txt()
    assert 'const pickerl=myFz.pickerl?new Date(myFz.pickerl+"T00:00:00"):null;' in text, \
        'v3.9.417 Regression: Dashboard-Pickerl-Badge braucht +"T00:00:00"'
    assert 'new Date(fzScannedItem.pickerl+"T00:00:00")>new Date()' in text, \
        'v3.9.417 Regression: QR-Pickerl-Badge braucht +"T00:00:00"'


# ── v3.9.418: DB-Schema-Mismatch (schema-verifiziert gegen jiggujpruejkaomgxarp) ──

def test_time_entries_no_phantom_stunden_column():
    """P1 Positiv: saveMatrixCell sendet nur 'hours' — time_entries hat keine Spalte
    'stunden' (sonst PostgREST-400 → Drop → Inline-Edit verschwindet)."""
    text = _txt()
    assert 'method:"PUT",body:{hours:_h}}' in text, \
        'v3.9.418 Regression: saveMatrixCell muss nur {hours:_h} senden'
    assert 'body:{hours:_h,stunden:_h}' not in text, \
        'v3.9.418 Regression: Phantom-Spalte stunden im PUT-Body zurueckgekehrt (→400/Drop)'


def test_as_signature_maps_to_real_columns():
    """P1 Positiv: AS-saveAs mappt sigMA/sigKunde auf reale Spalten unterschrift_monteur/_kunde
    (arbeitsscheine hat KEINE sig_ma/sig_kunde → sonst 400 → ganze Speicherung dropt)."""
    text = _txt()
    assert "const c={...b,unterschriftMonteur:b.sigMA||\"\",unterschriftKunde:b.sigKunde||\"\"};delete c.sigMA;delete c.sigKunde;" in text, \
        'v3.9.418 Regression: AS-saveAs sigMA/sigKunde-Normalisierung fehlt'
    # Reverse-Map spiegelt Signatur beim Laden zurueck in sigMA/sigKunde
    assert 'sigMA:a.sigMA||a.unterschrift_monteur||"",sigKunde:a.sigKunde||a.unterschrift_kunde||""' in text, \
        'v3.9.418 Regression: _mapArbeitsschein muss sigMA/sigKunde aus unterschrift_* spiegeln'


# ── v3.9.438: BWB zaehlt Sonntag mit — lokale 7-Tage-Woche (Chef-Entscheid) ──
# (loest v3.9.419 ab: damals Mo-Sa gegen Phantom-Sonntag; jetzt Sonntag MIT-gesammelt,
#  daher keine leere Phantomzeile mehr, sondern eine echte 7. Zeile wie bei generateBWB.)

def test_bwb_counts_sunday_local_seven_days():
    """exportBauwochenbericht zaehlt den Sonntag mit (Konsistenz mit generateBWB):
    eine LOKALE 7-Tage-Woche BWB_DAYS treibt Gather, Review-Modal UND Render (i<7).
    Die komponentenweite DAYS bleibt Mo-Sa (Matrix/Wochentabelle/Tages-Stz unberuehrt)."""
    text = _txt()
    # Lokale 7-Tage-Woche existiert und treibt Gather + Review.
    assert 'const BWB_DAYS=["Mo","Di","Mi","Do","Fr","Sa","So"];' in text, \
        'v3.9.438 Regression: lokale 7-Tage-Woche BWB_DAYS fehlt'
    assert 'BWB_DAYS.forEach((_,i)=>{' in text, \
        'v3.9.438 Regression: Gather-Loop muss BWB_DAYS (7 Tage) nutzen'
    assert 'const reviewRows=BWB_DAYS.map((dayName,i)=>{' in text, \
        'v3.9.438 Regression: Review-Modal-Rows muessen BWB_DAYS nutzen'
    # Render-Loop laeuft jetzt ueber 7 Tage.
    assert 'for(let i=0;i<7;i++){/* v3.9.438: Mo-So' in text, \
        'v3.9.438 Regression: BWB-Render-Loop muss i<7 (Mo-So) sein'
    # Komponentenweite DAYS bleibt Mo-Sa (NICHT global auf 7 erweitert).
    assert 'const DAYS=["Mo","Di","Mi","Do","Fr","Sa"];' in text, \
        'v3.9.438 Regression: globale DAYS darf NICHT auf Sonntag erweitert worden sein'
    assert 'for(let i=0;i<6;i++){/* v3.9.419: Mo-Sa' not in text, \
        'v3.9.438 Regression: alter Mo-Sa-Render-Loop (i<6) darf nicht zurueckkehren'


# ── v3.9.420: Notif-GET serverseitig auf eigene user_id filtern ──

def test_notif_get_user_id_filter():
    """Positiv: Notifications-GET filtert serverseitig auf curUser.id (Staff bekam sonst
    via RLS is_staff() ALLE Notifs → 200-Grenze verdraengte eigene)."""
    text = _txt()
    assert '_nuf="user_id=eq."+encodeURIComponent(_cu.id)' in text, \
        'v3.9.420 Regression: Notif-GET user_id-Filter fehlt'
    assert 'return _sbGetOrder("notifications","created_at.desc",_nuf).then(r=>r.slice(0,200));' in text, \
        'v3.9.420 Regression: Notif-GET muss gefilterten _sbGetOrder nutzen'


# ── v3.9.421: AS-Edit Diff-PUT statt Voll-Row (Lost-Update-Fix) ──

def test_as_diff_put_not_full_row():
    """P2 Positiv: saveAs patcht nur geaenderte Felder (Diff gegen geladene Baseline),
    sendet kein _finalForm-Full-Row mehr → konkurrierende Server-Updates (juprowa_*)
    werden nicht von stalem Client-Stand ueberschrieben."""
    text = _txt()
    assert 'const _diff={};for(const _dk in _finalForm){if(JSON.stringify(_finalForm[_dk])!==JSON.stringify(_origAs[_dk]))_diff[_dk]=_finalForm[_dk];}' in text, \
        'v3.9.421 Regression: AS Diff-Berechnung fehlt'
    # Body baut auf _diff (nicht _finalForm) + Empty-Diff-Guard vor SQ.push
    assert 'if(Object.keys(_asBody).length>0)SQ.push({url:editId?"/api/arbeitsscheine/"+editId' in text, \
        'v3.9.421 Regression: AS-PUT braucht Empty-Diff-Guard'
    assert ':_diff);' in text, \
        'v3.9.421 Regression: _asBody muss aus _diff gebaut werden (nicht _finalForm)'


# ── v3.9.422: _portalSync transient/permanent-Split (kein Queue-Wedge) ──

def test_portalsync_no_blind_break():
    """P3 Positiv: _portalSync bricht nicht mehr bei JEDEM Fehler ab (Wedge); permanente
    4xx werden uebersprungen, nur transiente (Netz/5xx/429/408) brechen ab."""
    text = _txt()
    assert 'if(/failed to fetch|networkerror|http5|http429|http408/.test(_m))break;}}if(done.length)await SQ.removeMany(done);};' in text, \
        'v3.9.422 Regression: _portalSync transient/permanent-Split fehlt'
    assert 'done.push(item.id);}catch(e){break;}}' not in text, \
        'v3.9.422 Regression: alter blinder catch{break} im _portalSync zurueckgekehrt'


# ── v3.9.423: epkolar-files Storage-Waisen-Cleanup (Foto/Plan/Doc) ──

def test_epk_files_orphan_cleanup():
    """P3 Positiv: Foto/Plan/Doc-Loeschen entfernt das public-Bucket-Objekt mit (best-effort)."""
    text = _txt()
    assert 'function _epkFilesPath(v){' in text, \
        'v3.9.423 Regression: _epkFilesPath-Helper fehlt'
    # delPhoto + deletePlan + delDoc rufen _epkFilesPath → _sbDeleteObj(SB_BUCKET,...)
    assert 'const _sp=_epkFilesPath(photoUrl(ph));if(_sp)_sbDeleteObj(SB_BUCKET,_sp);' in text, \
        'v3.9.423 Regression: delPhoto Storage-Cleanup fehlt'
    assert '_epkFilesPath(_pl.file_path||_pl.file_url||"");if(_ps)_sbDeleteObj(SB_BUCKET,_ps);' in text, \
        'v3.9.423 Regression: deletePlan Storage-Cleanup fehlt'
    assert "if(_ds)_sbDeleteObj(SB_BUCKET,_ds);" in text, \
        'v3.9.423 Regression: delDoc Storage-Cleanup fehlt'


# ── v3.9.424: Budget-Ampel vereinheitlicht (echter Stundensatz + €85-Fallback, budget_euro, 85/100) ──

def test_budget_ampel_unified_kalk_helper():
    """Positiv: gemeinsamer _projKalkKosten-Helper mit €85-Pauschalfallback (nie 0)."""
    text = _txt()
    assert 'const _projKalkKosten=pid=>' in text, \
        'v3.9.424 Regression: gemeinsamer _projKalkKosten-Helper fehlt'
    assert '(m&&parseFloat(m.stundensatz)>0)?parseFloat(m.stundensatz):_PAUSCHAL_SATZ' in text, \
        'v3.9.424 Regression: €85-Pauschalfallback (nie 0) fehlt'
    assert 'const _PAUSCHAL_SATZ=85;' in text, \
        'v3.9.424 Regression: _PAUSCHAL_SATZ=85 fehlt'


def test_budget_ampel_table_uses_budget_euro_and_helper():
    """Positiv: Tabellen-Ampel rechnet _projKalkKosten ÷ budget_euro, Schwellen 85/100, ⚪ ohne Budget."""
    text = _txt()
    assert 'const costEst=_projKalkKosten(p.id);' in text, \
        'v3.9.424 Regression: Tabellen-Ampel nutzt _projKalkKosten nicht'
    assert "const amp=budgetPct==null?'⚪':(budgetPct>100?'🔴':budgetPct<85?'🟢':'🟡');" in text, \
        'v3.9.424 Regression: Tabellen-Ampel Schwellen 85/100 + ⚪-Fallback fehlen'
    assert 'const costEst=usedH*85;' not in text, \
        'v3.9.424 Regression: alter €85-vs-betrag-Pfad zurueckgekehrt'
    # Budget-Karte nutzt denselben Helper
    assert 'const kalk=_projKalkKosten(p.id);' in text, \
        'v3.9.424 Regression: Budget-Karte muss denselben _projKalkKosten-Helper nutzen'
    # UI-Hinweis auf €85-Pauschalsatz
    assert 'inkl. €85-Pauschalsatz für Mitarbeiter ohne hinterlegten Satz' in text, \
        'v3.9.424 Regression: €85-UI-Hinweis fehlt'


# ── v3.9.425: Auslastungs-Ampel 70/90/100 + Heutige-AS nur offene (Chef-Entscheide) ──

def test_heute_as_only_open():
    """Positiv: Heutige-AS-KPI zaehlt nur offene (AS_GRP_OFFEN), wie ueberfaellige."""
    text = _txt()
    assert "const heuteAS=arbeitsscheine.filter(a=>AS_GRP_OFFEN.includes(a.scheinstatus)&&(a.terminBestaetigt||a.terminVorschlag||'').startsWith(_td)).length;" in text, \
        'v3.9.425 Regression: Heutige-AS muss auf AS_GRP_OFFEN filtern'


def test_auslastung_ampel_70_90_100():
    """Positiv: Auslastungs-Ampel (_ampBar/_ampTx/_ampLbl) nutzt 70/90/100 (4-stufig), nicht mehr 70/95."""
    text = _txt()
    assert "const _ampBar=pct=>pct<70?'#22c55e':pct<90?'#eab308':pct<=100?'#f97316':'#ef4444';" in text, \
        'v3.9.425 Regression: _ampBar muss 70/90/100 sein'
    assert "const _ampLbl=pct=>pct<70?'🟢 Luft für neue Aufträge':pct<90?'🟡 gut ausgelastet':pct<=100?'🟠 am Anschlag':'🔴 überlastet';" in text, \
        'v3.9.425 Regression: _ampLbl muss 4-stufig 70/90/100 sein'
    assert "const _ampBar=pct=>pct<70?'#22c55e':pct<=95?'#eab308':'#ef4444';" not in text, \
        'v3.9.425 Regression: alte 70/95-Schwelle zurueckgekehrt'


# ── v3.9.427: FZ-Schaden Single-Source JSON (Option a) — fz_schaeden-Zweitspeicher entfernt ──

def test_fz_schaden_single_source_json():
    """Option a (Chef-Entscheid): die fz_schaeden-Zweitspeicher-Writes (addSchaden,
    qDoSchaden, Status-Edit) sind entfernt → Single-Source = fahrzeuge.schaeden JSON.
    Kein /api/schaeden/-POST mehr im Client. (GET-Resolver/POST-Handler im api-Layer
    bleiben als toter, harmloser Code — separate Cleanup.)"""
    text = _txt()
    assert '/api/schaeden/' not in text, \
        'v3.9.427 Regression: fz_schaeden-Zweitspeicher-Write zurueckgekehrt (Option a = Single-Source JSON)'
    assert 'fz_schaeden-Zweitspeicher entfernt (Option a)' in text, \
        'v3.9.427 Regression: Single-Source-Marker-Kommentar fehlt'


# ── v3.9.431: G2 focus/visibility-Reload-Clobber + _wmTimer-Leak ──

def test_g2_sync_inflight_guard():
    """G2 Positiv: _syncInFlight-Ref + Guard in focus/visibility-Listenern verhindert,
    dass ein loadAll waehrend des Sync-Drains den optimistischen Matrix-Wert clobbert."""
    text = _txt()
    assert 'const _syncInFlight=_react.useRef.call(void 0, false);' in text, \
        'v3.9.431 Regression: _syncInFlight-Ref fehlt'
    assert 'finally{_syncInFlight.current=false;}' in text, \
        'v3.9.431 Regression: _syncThenReload muss _syncInFlight in finally zuruecksetzen'
    assert 'const _onVis=()=>{if(document.visibilityState==="visible"&&!_syncInFlight.current)loadAll(true);};' in text, \
        'v3.9.431 Regression: _onVis-Guard fehlt'
    assert 'const _onFocus=()=>{if(!_syncInFlight.current)loadAll(true);};' in text, \
        'v3.9.431 Regression: _onFocus-Guard fehlt'


def test_wmtimer_unmount_cleanup():
    """Positiv: _wmTimer (Monteur-Feld-Debounce) wird beim Unmount geraeumt."""
    text = _txt()
    assert 'Object.values(_wmTimer.current).forEach(t=>{try{clearTimeout(t);}catch(_){}});},[]);' in text, \
        'v3.9.431 Regression: _wmTimer-Unmount-Cleanup fehlt'


# ── v3.9.435: Phantom-"X Antraege zur Genehmigung" — stale absApprovals-Merge ──

def test_absapprovals_merge_server_over_stale_pending():
    """Bug (16 Antraege nach DB-seitiger Genehmigung): beim Laden darf stale lokales
    'ausstehend' einen definitiven Server-Status (genehmigt/abgelehnt) NICHT mehr
    ueberschreiben; nur definitive lokale Entscheidung gewinnt (Merge = _resolveApprK-Praezedenz)."""
    text = _txt()
    assert "for(const k in apprMap){const pv=m[k];if(pv!=='genehmigt'&&pv!=='abgelehnt')m[k]=apprMap[k];}return m;" in text, \
        'v3.9.435 Regression: absApprovals-Merge (Server gewinnt ueber stale ausstehend) fehlt'
    assert "setAbsApprovals(prev=>({...apprMap,...prev}))" not in text, \
        'v3.9.435 Regression: alter prev-wins-Merge (stale ausstehend gewinnt) zurueckgekehrt'


# ── v3.9.436: CSP frame-src/object-src erlaubt Supabase-Host (PDF-Viewer-iframe) ──

def test_csp_frame_src_allows_supabase():
    """PDF-Viewer (Dokumente/Fahrbewilligungen) laedt signierte Storage-URLs in ein iframe;
    frame-src/object-src muessen den Supabase-Host erlauben, sonst blockiert der Browser."""
    text = _txt()
    assert "frame-src 'self' blob: data: https://jiggujpruejkaomgxarp.supabase.co;" in text, \
        'v3.9.436 Regression: frame-src muss den Supabase-Host erlauben (sonst PDF-iframe blockiert)'
    assert "object-src 'self' blob: data: https://jiggujpruejkaomgxarp.supabase.co;" in text, \
        'v3.9.436 Regression: object-src muss den Supabase-Host erlauben'


# ── v3.9.437: Zeiterfassung Inline 0h => Eintrag loeschen (statt still No-Op) ──

def test_inline_zero_hours_deletes_entry():
    """Chef-Entscheid: korrigiert ein Monteur die Stunden inline auf 0, wird der Eintrag
    GELOESCHT (DELETE + entries-Prop + dayEntries), statt dass die DB still den alten Wert
    behaelt (vorher: Save-Zweig feuerte nur bei newHours>0)."""
    text = _txt()
    assert "else if(entry.id&&!(newHours>0)){" in text, \
        'v3.9.437 Regression: 0h-Loeschzweig in updateEntryHours fehlt'
    # Im Debounce-Save muss bei 0 ein DELETE auf denselben Eintrag erfolgen + lokale Bereinigung.
    assert 'SQ.push({url:"/api/entries/"+entry.id,method:"DELETE",body:{}});\n            setEntries(prev=>prev.filter(x=>x.id!==entry.id));' in text, \
        'v3.9.437 Regression: 0h muss DELETE + entries-Prop-Bereinigung ausloesen'
    assert "setDayEntries(prev=>{const c={...prev};c[iso]=(c[iso]||[]).filter(x=>(x.id||\"\")!==entry.id);return c;});" in text, \
        'v3.9.437 Regression: 0h muss die Zeile aus dayEntries (per id) entfernen'
