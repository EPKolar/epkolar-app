# OPEN BUGS — Stand v3.9.569 (2026-06-29)

Konsolidierte Liste der **echten** offenen Bugs nach dem Hunt-Pass auf v3.9.568/569.
Vollständige Befundliste (inkl. Defense-in-depth + Dead-Code): `FINDINGS_v3568.md`.
Der alte `docs/handoff/BUGHUNT-2026-06-17-OFFEN.md` ist ~75% stale (siehe Kopf-Notiz dort).

---

## 🔴 EINZIGER echter offener Bug mit Handlungsbedarf

### A-2 · Juprowa Status-Roundtrip 4→1 / 15→11
- **Was:** `JUPROWA_STATUS_MAP` (`index.html:3017`) ist nicht-injektiv (4 und 15 kollabieren auf
  `freigegeben`/`bar_bezahlt` wie 1/11). Der Push-Builder `_juprowaReversMap` (`:3307`) schreibt
  ohne Dirty-Check den kanonischen Reverse → ein gepullter OFFA-Status **4 wird als 1**, **15 als 11**
  zurückgepusht, auch ohne echte Status-Änderung. Stille, OFFA-seitig irreversible Korruption.
- **Schwere:** MEDIUM (Korrektheit, externe Buchhaltung).
- **Fix:** STAGED auf lokalem Branch `a2-juprowa-roundtrip` (Commit `b72742d`, v3.9.570) — Dirty-Check
  gegen `juprowa_raw.AK_AUFSTATUS`. Builder-only, `_juprowaPush` unberührt. **NICHT gepusht.**
- **Dry-Run:** `scripts/a2_dryrun.mjs` → alle 10 OFFA-Codes roundtrip-stabil (4→4, 15→15) verifiziert.
- **⚠️ FREIGABE-BEDARF (Sebastian):**
  1. Tabu-Auslegung bestätigen (`_juprowaReversMap`-Edit ändert Push-Verhalten, auch wenn `_juprowaPush`
     selbst nicht editiert ist).
  2. Erst NACH Sicht des Dry-Runs den Live-Deploy (= ermöglicht echten OFFA-Push) freigeben.
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
- **PW-Rotation** `34kolar70` → durch Sebastian ausgeführt (`ROTATE_PW_stage.sql`-Muster). Geteiltes Standard-PW eliminiert (admin/lindhuber/schober/aliti/lager je eigenes), git-History-Eintrag damit wertlos.

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
