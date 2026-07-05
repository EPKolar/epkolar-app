# HANDOFF 2026-07-05 ABEND — autonomer Lauf (abgebrochen, sauber abgeschlossen)

> Autonome Session vom 05.07.2026 (Fortsetzung nach v670). Von Sebastian vorzeitig beendet
> wegen massiver Netzlaufwerk-I/O-Probleme (Z:), die einen Großteil des Zeitbudgets fraßen.
> Es wurde nur **Fertiges + Getestetes** committed/gepusht. Basis: live v3.9.670, HEAD `d29ab4a`.

---

## Finale Versionen dieser Session

| Version | Inhalt | Commit |
|---|---|---|
| **v3.9.671** | Montagezulage Phase 1 (manuelle Vergabe je MA-Tag) — storage-freier Teil | (Tip des gebündelten Pushes) |
| **v3.9.672** | HOTFIX ProjList TDZ — „Tab Projekte lud nicht" | (Tip des gebündelten Pushes) |

**Bündelung:** EIN gebündelter Push (v671 + v672 + Docs). Finale Version live: **3.9.672**.

## Testanzahl vorher / nachher

- **Vorher (v3.9.670):** ~1162 (Full-Pytest-Baseline; in dieser Session wegen I/O-Konkurrenz nicht sauber durchgelaufen, siehe unten).
- **Nachher (v3.9.672):** siehe finalen Full-Pytest im Push-Commit. **Neue Test-Files:** `test_kv_montagezulage_v3671.py` (11 Tests), `test_projlist_ismob_tdz_v3672.py` (1 Test: ProjList isMob-vor-gridCols; ein breiter TDZ-Scan über alle `function`-Blöcke wurde erprobt, aber verworfen — die naive Brace-Extraktion meldet bei großen Komponenten wie `App` Nested-Scope-False-Positives; sauberer Scope-Scan bräuchte echten JS-Parser).
- Gates je finaler Stand grün: `node_check.py`=0 · Bracket-Baseline **`() -1` / `{} 0` / `[] 0`** (durch keine Edit verschoben — Jahr-Extraktion via `slice(0,4)` statt Regex) · `_check_version.js` Triple synchron 3.9.672.

---

## GEBAUT (im Push)

### v3.9.671 — Montagezulage Phase 1 (manuell)
Sebastian-Entscheid (KV Metallgewerbe Abschn. VIII Pkt. 5): Zulage wird **manuell pro Mitarbeiter-Tag** vom Büro/PL vergeben, KEINE Auto-Erkennung Baustelle/Werkstatt/Fahrt, keine Wegzeiten, keine Lehrlinge. App rechnet `zulagefähige Tages-Std (ohne Pause) × Satz(Jahr des Tages)`.

- `KV_RULES_FALLBACK.montagezulage = {2026:1.155, 2027:1.178}` — Satz nach **Jahr des Eintrags-Datums** (nie rückwirkend), `montagezulageStd` bleibt Fallback für unbekannte Jahre.
- Pure-Fns im `//@KV-ZULAGEN`-Block (window-scope, exportiert):
  - `_kvMontagezulageSatz(datum, satzQuelle)` — Jahr via `slice(0,4)` (kein Regex → Bracket-Baseline unberührt), Komma-Coercion `"1,155"→1.155` (Muster v664), unbekanntes Jahr → Fallback.
  - `_kvMontagezulageTag(stdOhnePause, datum, satzQuelle, flag)` — `flag` falsy → 0; `0h` → 0; sonst `std × Satz(Jahr)`. Kein optional chaining.
- `KVRulesConfig._save` **object-tolerant** gemacht (Objekt-Feld je Eintrag Komma→Punkt coercen statt `String(obj)` = `[object Object]`-Korruption) + editierbare **Jahres-Satz-UI** (Gate admin, Persistenz `system_config` key `kv_rules`). `montagezulageStd`-Zeile relabelt „Montagezulage-Fallback (unbek. Jahr)".
- **Direkt-Verifikation der Pure-Fns via node:** 8h·2026-12-31=9,24 · 8h·2027-01-01=9,424 · flag=false→0 · 0h→0 · 2030→Fallback 11,55 · Komma „1,155"→1,155. Alle korrekt.
- **DDL `sql/MONTAGEZULAGE_v1.sql` NUR gestaged** (Human-Run-Gate, KEIN Auto-Apply). Wortlaut unten.
- **Phase 2 (Vergabe-UI + Report-Flag-Umstellung) NICHT gebaut** (braucht die ausgeführte Tabelle) — Spec in `KV_ENTSCHEIDUNG_v668.md`.

### v3.9.672 — HOTFIX ProjList TDZ (Chat-Claude-Befund, live bestätigt)
- **Ist:** In `ProjList` stand `const _gridCols=isMob?…` **vor** `const isMob=ww<600;` → `ReferenceError: Cannot access 'isMob' before initialization` (TDZ). `ViewBoundary:projekte` fing den Fehler → **Tab Projekte lud nicht**. `isAdmin`/`_seeBetrag` standen korrekt davor, nur `isMob` war zu spät.
- **Soll/Fix:** Die komplette `_gridCols`-Zeile (inkl. v3.9.644-Kommentar) **unverändert** hinter `const isMob=ww<600;` verschoben. Sonst nichts geändert. (index.html: isMob-decl Z.11754 < `_gridCols` Z.11755.)
- **Regression-Guard:** `test_projlist_ismob_tdz_v3672.py` — ProjList: `const isMob=ww<600;` muss VOR `_gridCols=isMob` stehen.
- **Herkunft (Handoff-Recherche):** die Umsortierung stammt vermutlich aus dem v656–667-Reorg-Lauf; ein `git log -S "_gridCols=isMob"` konnte wegen Zeitbudget/Session-Ende nicht mehr sauber ausgeführt werden → offen.
- **Breiter TDZ-Scan verworfen:** ein Scan über alle `function`-Blöcke meldete `App` als vermeintlichen Offender — das ist ein Nested-Scope-False-Positive der naiven Brace-Extraktion (App läuft live, kein echtes TDZ). Ein sauberer Scan bräuchte einen JS-Parser. Falls du weitere „X vor Deklaration verwendet"-Fälle vermutest: mit echtem Parser (z. B. acorn) prüfen, nicht per Regex.

---

## NICHT GEBAUT — mit Grund

- **Netzlaufwerk-Zeitverlust (Hauptgrund):** Z: wurde im Sessionverlauf extrem langsam. Ein Full-Pytest brauchte >60 min unter I/O-Konkurrenz mit Bug-Hunt-Subagenten; `git`/`ripgrep` liefen wiederholt in Timeouts; ein stale `.git/index.lock` blockierte zwischenzeitlich alle git-Writes. Das fraß ~1,5–2 h Budget. Details in Auto-Memory `feedback_epkolar_pytest_io` + `feedback_git_lock_znetwork`.
- **B2-1 Montagezulage Phase 2 (Vergabe-UI + Report/CSV auf Flags):** nicht gebaut. Braucht die ausgeführte Tabelle `montagezulage_tage` und ist lohnrelevant-nah (Report-Rechnung) → unter I/O-Druck nicht sauber testbar. Spec steht (siehe unten „Wartet auf Sebastian").
- **B2-2 B034 `tickets.page`:** nicht gebaut. `sql/B034_tickets_page_column.sql` existiert bereits im Repo (aus früherem Lauf). Kein neues DDL nötig; Frontend-Anbindung offen.
- **B2-3 `sync_supplier` Edge-Function:** nicht angefasst (Deploy war ohnehin TABU).
- **Block C Fixes (Stempeluhr/Flotte):** NUR analysiert (2 Subagenten fertig), **keine Fixes gebaut** — Feature-Stopp kam vor der Fix-Phase. Autonom-fixbare Befunde unten dokumentiert (für nächste Session).
- **KV Punkt 2/3/4:** unverändert offen (lohnrelevant, Freigabe ausstehend).

---

## Subagenten-Befunde (Bug-Hunt, read-only) — für nächste Session

**2 von 5 Subagenten fertig** (Stempeluhr, Flotte). Urlaub/Abwesenheit, Kiosk, Exporte **abgebrochen (Analyse unvollständig)** durch Session-Restart.

### Autonom fixbar (klare Ursache, additiv/lokal, nicht lohnrelevant) — NÄCHSTE SESSION
- **Flotte #2 (P2)** — `index.html:~21722`. Ist: Leer-Banner nennt `fz_positions` / `sql/GPS_v1.sql`. Soll: gelesen wird die View `fz_latest` (v663) → bei 42P01 muss `fz_latest` / `GPS_LATEST_v1.sql` genannt werden. Reiner String-Fix. Failure: Operator führt beim Pilot die falsche SQL aus.
- **Flotte #1 (P2)** — Marker-Builder `~21648` + `_flotteLatestPerVehicle`. Ist: nur `lat/lon==null`-Check. Soll: auch `!isFinite(lat/lon)` und Null-Island `0/0` verwerfen. Failure: Tracker ohne Fix liefert 0/0 → `fitBounds` zieht Karte auf Golf von Guinea / `L.marker([NaN,NaN])` wirft. Additiver Guard.
- **Stempel #4 (P3)** — `~5684`. Ist: `_lastScan.current[worker.id]=_nowMs` wird VOR dem `_sbGet('stempel_log',…)` gesetzt; bei Read-Fehler 12s-Sperre trotz Nicht-Stempel. Soll: Set erst nach erfolgreichem `SQ.push`.
- **Stempel #6 (P3)** — HID-Buffer `_buf` nur bei Enter geleert; kein Inter-Key-Idle-Reset (~200 ms). Additiv, kosmetisch.

### NUR dokumentieren (lohnrelevant / Produktentscheid / Schema-Verify) — für Sebastian
- **Stempel #1 (P2, lohnrelevant):** `_stTagNetto` zieht Pauschal-Pause auch dann ab, wenn die Pause bereits als Lücke zwischen zwei Kommen/Gehen-Paaren gestempelt wurde → **doppelter Pausenabzug** (Split-Shift 08–12 / 13–17 = 8h → fälschlich 7h). Fix bräuchte „Abzug = max(0, Rolle-Pause − gestempelte Gaps)".
- **Stempel #2 (P2, Go-Live-Lücke):** Übernacht-Schichten setzen `netto=null` mit Verweis „Netto im Büro" — aber es gibt **keine** Büro-Auswertung von `stempel_log`. Jede Schicht über Mitternacht = Netto-Blindfleck, sobald Terminals live gehen. Fehlendes Feature/Produktentscheid.
- **Stempel #3 (P2):** `_stPairEvents` verwirft bei zwei aufeinanderfolgenden KOMMEN das erste Intervall still (Offline-Replay / 2. Terminal / manueller Insert). Ergebnisverändernd → defensiv paaren + flaggen (kein rein additiver Fix).
- **Stempel #5 (P3, lohnrelevant):** Pausenabzug ignoriert `pauseAbStd:6`-Schwelle — ein 3h-Tag verliert trotzdem 60 min.
- **Flotte #3 (P3):** `new Date(ts)` überall — falls `fz_positions.ts` tz-naiv (`timestamp` statt `timestamptz`), verschieben sich Relativzeit + 24h-Inaktiv-Schwelle um den Wien-Offset. **Schema verifizieren** (tz vs. naiv) VOR jedem Fix.
- **Flotte #4 (P3):** Map-Init-Effekt (Deps `[]`) hat keinen Retry, wenn Leaflet `L` beim Mount fehlt (CDN blockiert) → GPS-Tab tot bis Remount. Infra-Entscheid Selfhost vs. Retry.
- **Flotte #5/#6 (P3):** Marker-Label-Edits erst beim 60s-Poll sichtbar; stale `_openFid` öffnet Popup bei intermittierendem Tracker ungefragt wieder. Kosmetik/Timing.

---

## Wartet auf Sebastian

1. **SQL-Run-Gate:** `sql/MONTAGEZULAGE_v1.sql` liegt bereit (Wortlaut unten). Sobald du sie im Supabase-SQL-Editor (Projekt `jiggujpruejkaomgxarp`) ausführst, kann Phase 2 (Vergabe-UI + Report-Flags) gebaut werden. `sql/B034_tickets_page_column.sql` liegt ebenfalls bereit (aus früherem Lauf).
2. **Montagezulage Phase 2 Freigabe-Detail:** Gültigkeitsdatum-Muster der Satz-Overrides bestätigen (Vorschlag: `{satz, gueltig_ab}` in `system_config`, „größtes gueltig_ab ≤ Eintrags-Datum"). Details in `KV_ENTSCHEIDUNG_v668.md`.
3. **KV Punkt 2/3/4** (Freigabe-Format „2A, 3 …, 4 raus") — lohnrelevant, kein autonomer Change. Punkt 4 (`taggeldNacht` toter Knopf) ist risikolos entfernbar.
4. **Dispo 6→7 Tage (Mo–So):** Produktentscheid ja/nein (Kiosk/Grid noch 6-tägig).
5. **`.github/workflows/pages.yml` pushen:** braucht PAT mit `workflow`-Scope, dann Pages-Source „GitHub Actions" (robuster gegen Build-Throttle).
6. **`urlaubskontingent.urlaub`-Drop:** bleibt gestaged bis explizites „Spalte droppen".
7. **Lager-User-Passwort für Kiosk-PDF:** Auth-Pfade sind für mich TABU.
8. **Kiosk-ZA-RPC:** explizite Autorisierung ausstehend.

---

## Block A — MEMORY.md-Pfad-Klärung

- `git ls-files | grep -i memory` = **leer** → MEMORY.md ist **NICHT im Repo** getrackt (bestätigt Chat-Claudes Tarball-Fund).
- Die MEMORY.md liegt in der **Claude-Auto-Memory**: `C:\Users\technik\.claude\projects\C--Users-technik\memory\MEMORY.md` (11.320 B, geändert 05.07. 08:48). Die frühere „MEMORY.md aktualisiert"-Meldung bezog sich auf diese Auto-Memory, nicht auf eine Repo-Datei. **Nicht committen.**

---

## Wortlaut `sql/MONTAGEZULAGE_v1.sql` (gestaged, NICHT ausgeführt)

```sql
-- MONTAGEZULAGE_v1.sql — Fundament manuelle Montagezulage (App v3.9.671)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — Human-Run-Gate (Sebastian).
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).

CREATE TABLE IF NOT EXISTS public.montagezulage_tage (
  worker_id  text NOT NULL,
  datum      date NOT NULL,
  aktiv      boolean NOT NULL DEFAULT true,
  created_by text,
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (worker_id, datum)
);

ALTER TABLE public.montagezulage_tage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS montagezulage_tage_select_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_select_staff ON public.montagezulage_tage
  FOR SELECT USING (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_insert_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_insert_staff ON public.montagezulage_tage
  FOR INSERT WITH CHECK (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_update_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_update_staff ON public.montagezulage_tage
  FOR UPDATE USING (is_staff()) WITH CHECK (is_staff());

DROP POLICY IF EXISTS montagezulage_tage_delete_staff ON public.montagezulage_tage;
CREATE POLICY montagezulage_tage_delete_staff ON public.montagezulage_tage
  FOR DELETE USING (is_staff());

-- ROLLBACK: DROP POLICY x4; DROP TABLE IF EXISTS public.montagezulage_tage;
```

(`sql/B034_tickets_page_column.sql` liegt separat bereits im Repo — in dieser Session nicht angefasst.)
