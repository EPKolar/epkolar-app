# HANDOFF · v3.8.45 Bug-Hunt-Batch2 · 2026-04-24

**Baseline:** `e3c2e35` (v3.8.44 + Handoff)
**End-State:** `82ce580` · tag `v3.8.45` · origin/main synced

## TL;DR

3 von 4 geplanten Items in v3.8.45 abgeschlossen, S7.2 (Modal-Helper) ehrlich geskipped wegen Aufwand-Risk-Verhältnis. Pytest 203/203 unverändert grün. Brackets stabil über 5 Code-Edits + Bump.

## Commits (4)

| SHA | Subject | Finding |
|---|---|---|
| `4d2c550` | docs: inline comment for delFolder audit | S3.4 |
| `37e1135` | docs: inline comment for delPhoto audit | S3.5 |
| `1343f31` | fix(safety): _safeJsonParse migration batch 2 (+9 sites) | S2.1 |
| `82ce580` | v3.8.45 bump after bughunt-batch2 fixes | — |

## Delta per Finding

### S3.4 · delFolder Guard-Audit ✅
- **Befund:** L10191 hat bereits `if(!isAdmin)return;` Guard.
- **Bewertung:** Strenger als `canDo("folder_delete")` = isA||isPL||isB. Bewusst restriktiver wegen rekursiver Lösch-Logik (Unterordner + Datei-Reassignment + SB-DELETE pro fid).
- **Aktion:** Inline-Kommentar L10192 als Audit-Marker. Kein Code-Fix nötig.

### S3.5 · delPhoto canDo-Audit ✅
- **Befund:** L9998 hat bereits `if(!isAdmin)return;` Guard.
- **Bewertung:** Strenger als `canDo("doc_delete")` = isA||isPL||isB. Bewusst restriktiver, da DB-DELETE auf `photos`-Table irreversibel + Storage-File-Dangle.
- **Aktion:** Inline-Kommentar L9999. Kein Code-Fix nötig.

### S2.1 · _safeJsonParse Migration Batch 2 ✅
- **9 weitere Sites migriert** (in 3 Batches à 3, jeder mit Triade-Verify):

| Batch | Lines | Bereich |
|---|---|---|
| A | 370, 371, 1133 | epk_timer Stop/Get + HTTP-Body-Parse |
| B | 3429, 3991, 4195 | Defect-Photos arr + Form-Data + Auto-Notif Cooldown |
| C | 7277, 7313, 14986 | Dashboard-Vis + Weather-Cache + Fahrzeug-Favs |

- **H1 ausgenommen:** epkolar_user/_auth, juprowa_*, JWT-Parses, perms.
- **Kumulativ v3.8.44+v3.8.45:** 5+9 = **14 von 51 Sites** migriert.

### S7.2 · _confirmModal-Helper ⛔ SKIPPED
- **Aufwand-Schätzung:** 1.5h+ (Modal-Component, useState, Promise-Wrap, 2-3 Pilot-Migrationen, Tests).
- **Risiko:** Native `confirm()` → Promise-basiertes Modal hat subtile UX-Unterschiede (Click-outside-cancel, ESC-Key-Behavior). Pilot-Migration ohne vollständige UX-Verifikation riskant.
- **Begründung:** v3.8.45-Session-Budget war 2h Total, S2.1-Batch+Audits brauchten ~30 min, S7.2 würde verbleibendes Budget komplett fressen ohne abgeschlossene Migration.
- **Empfehlung:** Separater Block (Samstag oder eigene Session) mit voller UX-Verifikation in Browser.

## Tests

- **203/203 grün** (unverändert vs. v3.8.44).
- Keine neuen Tests in dieser Session — `_safeJsonParse`-Tests von v3.8.44 (10) decken die erweiterte Nutzung implizit ab.
- Brackets: `() -2 {} 0 [] 0` stabil über alle 5 Code-Edits + Bump.

## H-Rules-Bilanz

- **H0 Pfad-Lock:** ✅
- **H1 Kritische Zonen:** ✅ Auth/Juprowa/SyncQueue/_mapBody/OFFA/DATANORM unberührt
- **H2 Kein Supabase-Write:** ✅
- **H3 Bracket-Drift:** n/a
- **H4 Bump am Ende:** ✅ ein v3.8.45-Bump nach allen Fixes
- **H5 Triade nach jedem Fix:** ✅
- **H6 2× Skip-Regel:** n/a (nur 1 Skip S7.2)
- **H7 Direkt main:** ✅ kein Branch
- **H8 Ehrlich:** ✅ S7.2 transparent als SKIP mit Begründung
- **H9 Kein Branch-Merge:** ✅

## Remaining (für nächste Session)

- **S7.2** `_confirmModal`-Helper + 12 Pilot-Migrationen (1.5-2h, eigene Session)
- **S2.3** OFFA-PDF-Datum-Guard (H1-Zone, mit Sebastian-Input)
- **37 weitere JSON.parse-Sites** (pro-Section bei Code-Touch)
- **Restliche Bug-Hunt-Findings** aus `sql/BUGHUNT_REPORT_20260428.md` mittel/niedrig-Severity

## KeepAwake

PID 22056 läuft, Cleanup steht für Sebastians Rückkehr So 27.04 11:00.
