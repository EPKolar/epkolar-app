# OPEN BUGS — Stand v3.9.569 (2026-06-29) · Nachtrag 2026-06-30 (v3.9.582)

Konsolidierte Liste der **echten** offenen Bugs nach dem Hunt-Pass auf v3.9.568/569.
Vollständige Befundliste (inkl. Defense-in-depth + Dead-Code): `FINDINGS_v3568.md`.
Der alte `docs/handoff/BUGHUNT-2026-06-17-OFFEN.md` ist ~75% stale (siehe Kopf-Notiz dort).

---

## 🟢 NACHTRAG 2026-06-30 (live **v3.9.582**, HEAD `99915e9`, main == origin; Bauprovisorien scharf)

**Sync-Gesundheits-Check (read-only) — GRÜN, kein Handlungsbedarf:**
- **Pull grün:** arbeitsscheine 108 total, max nummer `S075362`; Juprowa-`WorksheetList` liefert rolling
  56er-Fenster (`S075248`–`S075362`, 0 ohne Nummer). **App-Max == Juprowa-Max == S075362 → kein Gap.**
  `added:0/skipped:56` in jedem Pull ist NORMAL (alle 56 bereits in DB). RPC `juprowa_fetch_worksheets`
  GETtet ohne limit/Datum/Status-Filter; Client `_juprowaSync` (`:3107`) keyt auf `nummer` ohne limit/
  Pagination, überspringt nur leere AK_SCHEINNR (`:3134` — aktuell 0). Pull-Frische: `juprowa_sync_at`
  zuletzt heute 07:34, 56 Scheine heute gesynct. *(Gemeldetes „Schein fehlt" war ein UI-Filter, kein Pull-Defekt.)*
- **Push grün:** push_pending=1 (`S075362`, in_bearbeitung, gerade lokal editiert → drained beim nächsten
  5-Min-Zyklus), push_error=0, `local_updated_at > updated_at` = 0 (**App markiert Änderungen korrekt**),
  max(`last_push_at`) = heute 07:34 (NICHT mehr 24.06 — Push läuft, Auto-Drain `_juprowaDrainPending(10)`
  nach jedem Pull `:3190`). 107/108 mit juprowa_id (1 = lokal angelegter Nicht-Juprowa-Schein, erwartet).

**Dead-Code Phase 3 — ABGESCHLOSSEN (`f3d0ae6`, v3.9.581):** 6 tote Funktionen + `preview/whatsapp_ui_v0.html`
entfernt (doJuprowaSync/FullSync/PushAll, getAllDescendantIds, _planClearPdfCache, _titleCase). **Nichts mehr
offen zu löschen:** `_safeSessionSet` (`:1726`) bleibt (durch `test_sprint77_coverage.py` guard-getestet),
`getWeekplans`/`toggleFZ`/`_V` bewusst behalten, `supplier-sync` Edge-Fn braucht Dashboard/Cron-Klärung.

**Korrektheits-Fixes 2026-06-30 — DONE & live (v3.9.577–580):**
- ✅ **BWB-KW-Kopfzeile** Sonntag im Zeitraum-Label (`dateFmt(0)`–`dateFmt(6)`) → `34aa643` (v3.9.577).
- ✅ **km_stand-Klobber** Tank-Pfad erhöht km_stand nur (`Math.max`), senkt Tacho nicht mehr → `894cdaf` (v3.9.578).
- ✅ **Foto-Storage-Orphans** Upload nutzt bereits hochgeladene URL wieder (kein Waise bei DB-Post-Retry) → `e74b818` (v3.9.579).
- ✅ **FinkZeit #11** Dashboard-Abweichungs-Schwelle auf 0.5h angeglichen (Export-Konsistenz) → `32ebba6` (v3.9.580).

---

## ✅ KEINE offenen Bugs mit Handlungsbedarf mehr (A-2 GESCHLOSSEN 2026-06-30)

### A-2 · Juprowa Status-Roundtrip 4→1 / 15→11 — ✅ GEFIXT & LIVE (v3.9.583, `33ab0ac`)
- **War:** `JUPROWA_STATUS_MAP` (`index.html:3017`) nicht-injektiv (4 und 15 kollabieren auf
  `freigegeben`/`bar_bezahlt` wie 1/11); Push-Builder `_juprowaReversMap` schrieb ohne Dirty-Check den
  kanonischen Reverse → gepullter OFFA-Status **4→1**, **15→11**, auch ohne echte Änderung. Stille,
  OFFA-seitig irreversible Korruption.
- **Fix LIVE:** Branch `a2-juprowa-roundtrip` (`b72742d`) nach main gemerged → **`33ab0ac` (v3.9.583)**,
  gepusht, raw-verifiziert (`_rawSt` live, Version-Triple 3.9.583). Dirty-Check echot
  `juprowa_raw.AK_AUFSTATUS` wenn er auf denselben App-Status abbildet. **NUR Builder geändert;
  `_juprowaPush` + `AK_PRIOR` byte-identisch.** Gate grün (node_check 0, bracket-Baseline, pytest 998/0).
- **Verifiziert:** Dry-Run alle 10 Codes roundtrip-stabil (4→4, 15→15) **+ erster echter Push S075362
  von Sebastian in OFFA als korrekt bestätigt (2026-06-30).** Normalbetrieb freigegeben, kein Push-STOPP mehr.
- **DB-Backup:** `_backup_arbeitsscheine_status_pre_a2_20260630` (108==108) bleibt noch 1–2 Tage liegen,
  dann löschbar.
- **Details:** `HANDOFF_A2_juprowa_status_roundtrip.md`.

---

## ✅ Bereits geschlossen diese Session (kein offener Bug mehr)
- **HIGH A-1 · Kiosk-PII-Leck:** lager_display las workers/arbeitsscheine/projects direkt (SVNR/Reisepass/
  Stundensatz/Kunden-Tel/Adresse). GESCHLOSSEN: RPCs `kiosk_field_workers`/`kiosk_week_arbeitsscheine`
  (minimal, kein PII) + Client v3.9.569 (`d065111`, live) + RLS `lager_display_no_select` RESTRICTIVE
  auf workers/projects/arbeitsscheine. Live-verifiziert (lager_display direct=0, RPC liefert 11/55).
- **A1/B5/B6/B034/A3** aus dem 17.06.-Backlog = stale/bereits gefixt/tot (siehe Backlog-Kopfnotiz).
- **supplier-sync set-credentials** (Validierung) = gefixt+committet (`ac44304`).
- **2b GoTrue-Logins** lindhuber/schober = angelegt (MCP).

### ✅ Gefixt + gepusht 2026-06-30 (Sammellauf)
- **#1 qDoSchaden Datenverlust** (`:21035`) → `3ed7d08` (v3.9.572). Persistiert jetzt via `upd+_schSync` (column-scoped PUT) wie addSchaden/qDoKm/qDoTank.
- **#5 updSt kunde_status-Spiegel** (`:12308`) → `db45153` (v3.9.573). `_DEF2KUNDE`-Map nur für `melder=Kunde`; `_bulkApply` erbt via Delegation. Kunde sieht Abnahme-Button wieder.
- **#2 SQ.push stiller Quota-Verlust** (`:2748`) → `5d54a33` (v3.9.574). Sichtbarer Toast im catch (PhotoQ-Muster) statt stillem Verlust. *(Item bei voller Quota nicht erzwingbar persistierbar — Warnung ist die ehrliche Mitigation; tiefere Queue-Pufferung bewusst NICHT gemacht.)*
- **#4 Zeit-Edit-Guard (orthogonal)** (`:8746`) → `3a4229a` (v3.9.575). Guard VOR dem push, gepinnte SQ.push-Zeile byte-identisch → alle 4 Lohnpfad-Freezes (341/344/345/347) explizit grün, KEIN Rebaseline. NaN/≤0/>24h beim Edit abgewiesen.
- **PW-Rotation** `[altes PW, rotiert, wertlos]` → durch Sebastian ausgeführt (`ROTATE_PW_stage.sql`-Muster). Geteiltes Standard-PW eliminiert (admin/lindhuber/schober/aliti/lager je eigenes), git-History-Eintrag damit wertlos.

---

## ✅ #4 Zeit-Edit-Guard — GEFIXT 2026-06-30 (v3.9.575, `3a4229a`) — orthogonal, Freezes grün
*(Historie/Analyse — der Fix ist live; Details unten dokumentieren warum kein Rebaseline nötig war.)*
- **Was:** `editMonteurEntries`-Save-Pfad (`index.html:8746`) sendet beim Edit bestehender Zeit-Einträge
  `hours:r.stunden` ROH — kein 0–24-/NaN-Guard. Geleertes Feld → NaN/null, Tippfehler → >24h ungeprüft
  in die DB (Lohn-relevant). NEW-Pfad (`:8734`) clampt korrekt (`Math.round((parseFloat||0)*100)/100` + `>0`).
- **Fix ist fertig vorbereitet** (verworfen aus dem Working Tree, reproduzierbar): Guard `_he=parseFloat(r.stunden)`,
  `if(!(_he>0)||_he>24){skip}` + Toast.
- **⚠️ WARUM zurückgestellt — Lohnpfad-Freeze:** Die PUT-Zeile ist durch **4 Regression-Anker** gepinnt:
  `tests/test_v3_9_341/344/345/347` (`assert 'SQ.push({url:"/api/entries/"+r.id,...hours:r.stunden,...}' in index_html`).
  Diese Anker sind **Cross-Feature-Schutz** (Doc-Strings: „v3.9.341 darf NUR DOM-Render anfassen, nicht die
  SQ.push-Logik" / „Regression v3.9.345 darf die ✏️-Monteur-Liste NICHT anfassen") — sie pinnen das **Body-Format**
  gegen versehentliche Änderung durch *andere* Features. Sie schützen KEINE bestimmte Stunden-Behandlung.
- **Verdikt = ORTHOGONAL:** #4 (NaN/>24 abweisen) lässt sich als Guard **VOR** dem `SQ.push` umsetzen, ohne die
  gepinnte Zeile zu berühren → alle 4 Freezes blieben grün (kein Re-Baseline der Test-Anker nötig). Der bisher
  verworfene Diff hatte `hours:r.stunden`→`hours:_he` geändert (= Anker-Bruch); die orthogonale Variante lässt
  die Zeile byte-identisch.
- **Nächster Schritt (Sebastian):** Lohnpfad-Freeze-Review → dann orthogonalen Guard freigeben (Push vor der
  gepinnten Zeile, Zeile unverändert). Voller Gate, eigener Commit.
- **ANALYSE ABGESCHLOSSEN (2026-06-30):** Alle 4 Guards gelesen — sie pinnen ALLE denselben Literal-String
  `SQ.push({url:"/api/entries/"+r.id,...hours:r.stunden,bemerkung:r.bemerkung}})` als reinen Code-Snapshot.
  Doc-Strings: 341 „NUR DOM-Render, nicht SQ.push-Logik" · 344 „NUR neue Pfade, nicht PUT-Logik" · 345 „Liste
  NICHT anfassen" · 347 „PUT-Body UNVERAENDERT". = **Cross-Feature-Schutz des Body-Formats**, KEINE Stunden-
  Wert-Behandlung. → **ORTHOGONAL BESTÄTIGT.** Orthogonaler Diff (Guard VOR dem push, Zeile byte-identisch):
  ```
  if(changed){
    const _he=parseFloat(r.stunden);
    if(!Number.isFinite(_he)||_he<=0||_he>24){_skipEdit++;return;}   // NaN/≤0/>24 abweisen
    SQ.push({url:"/api/entries/"+r.id,method:"PUT",body:{date:r.datum,taetigkeit:r.taetigkeit,hours:r.stunden,bemerkung:r.bemerkung}});  // unveraendert -> alle 4 Freezes gruen
    cnt++;
  }
  ```
  Lässt alle 4 Anker grün (kein Rebaseline). NICHT committet — Lohnpfad, Sebastian-Freigabe.

---

## 🟡 Niedrigprio / Defense-in-depth (kein akuter Handlungsbedarf — Detail in FINDINGS_v3568.md)
- weekplan Dirty/Deleted-Set-Leak im Drop-Pfad (`:6405` vs `:6424`) — Korrektheit, selten.
- weekplan reload-Guard global statt KW-gefiltert (`:16204`).
- `notif_insert` `with_check=true` → lager_display könnte notifications INSERTen (DB-Policy, DiD).
- worker_projects/ROUTE_MAP generischer GET ohne Client-Scope (`:2096/2106`).
- Juprowa Doppel-Push-Race (`:3343` push_pending = Marker, kein Lock) — Verdacht.
- Juprowa optimistische Erfolgs-Zählung bei verschluckten Writes (`:3155/3160`) — selbstheilend via Pull.
