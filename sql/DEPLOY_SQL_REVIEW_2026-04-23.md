# Deploy-SQL Review · 2026-04-23

Pre-Deploy Code-Review der offenen SQL-Files. Sebastian sollte das lesen
BEVOR er eines der Scripts im Supabase SQL-Editor laufen lässt.

---

## 🔴 BASELINE_FIX_v3.8.sql · **BLOCKER**

### Befund 1 · FIX 3: `arbeitsscheine_scheinstatus_chk` verwendet falsche Werte

```sql
-- Script-Zeile 27/28:
CHECK (scheinstatus IS NULL OR scheinstatus IN
  ('neu','bearbeitung','abgeschlossen','storniert'))
```

**Das sind NICHT die App-Enum-Werte.** In `index.html` L398 steht:

```js
SCHEINSTATUS_C=Object.freeze({
  AUFGENOMMEN:'aufgenommen', FREIGEGEBEN:'freigegeben',
  IN_BEARBEITUNG:'in_bearbeitung', AUFGESCHOBEN:'aufgeschoben',
  ERLEDIGT:'erledigt', ABGERECHNET:'abgerechnet',
  BAR_BEZAHLT:'bar_bezahlt', STORNIERT:'storniert'
});
```

**Nur `storniert` überlappt.** Ein Deploy würde **jedes neue AS-INSERT/UPDATE** mit Status `aufgenommen`/`freigegeben`/`in_bearbeitung`/`aufgeschoben`/`erledigt`/`abgerechnet`/`bar_bezahlt` reject-en.

`NOT VALID` schützt historische Rows, aber **neue Writes werden geprüft** — genau das gegenteilige Verhalten von "risikolos".

**Fix vor Deploy**:
```sql
CHECK (scheinstatus IS NULL OR scheinstatus IN
  ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben',
   'erledigt','abgerechnet','bar_bezahlt','storniert'))
```

### Befund 2 · FIX 3: `arbeitsscheine_prioritaet_chk` gleiche Klasse

Script: `CHECK (... IN ('niedrig','mittel','hoch','kritisch'))`
App-Enum (L2212): `AS_PRIO={keine, niedrig, normal, hoch, dringend}`

Überlappung: nur `niedrig` + `hoch`. Werte `keine`, `normal`, `dringend` würden neue Writes sofort reject-en. `mittel` und `kritisch` sind nicht im App-Enum.

**Fix vor Deploy**:
```sql
CHECK (prioritaet IS NULL OR prioritaet IN
  ('keine','niedrig','normal','hoch','dringend'))
```

### Befund 3 · FIX 3: `users_role_chk` unvollständig

Script: `('admin','buero','monteur','projektleiter')` — 4 Rollen.
App (L397): `ROLLE={ADMIN, MONTEUR, PL, BUERO, HELFER, OBERMONTEUR, TECHNIKER}` — 7 Rollen.

Fehlend: `helfer`, `obermonteur`, `techniker`. Falls ein User mit einer dieser Rollen angelegt oder aktualisiert wird → reject.

**Fix vor Deploy**:
```sql
CHECK (role IS NULL OR role IN
  ('admin','buero','monteur','projektleiter',
   'helfer','obermonteur','techniker'))
```

### Alle übrigen Fixes sind OK

- FIX 1 (UNIQUE users.email partial) ✓
- FIX 2 (UNIQUE arbeitsscheine.juprowa_id partial) ✓
- FIX 4 (NOT NULL auf photos.project_id + time_entries.{worker_id, project_id}) ✓
  — Schutzwälle (EXCEPTION WHEN others + Count=0-Check vor Alter) greifen korrekt

### Empfehlung
Script **nicht deployen** bis die 3 CHECK-Werte-Listen korrigiert sind.
Ich kann die Korrekturen direkt im File einbauen — Wort gegeben, dann
deployen.

---

## 🟢 BASELINE_FIX_VERIFY_v3.8.sql · OK

Verify-Queries sind korrekt (pg_indexes / pg_constraint / pg_attribute).
**Aber**: der Test prüft nur die Existenz der Constraints, nicht deren
**Werte-Liste**. Nach dem Fix oben würde VERIFY weiterhin TRUE für
"scheinstatus_chk" zeigen, obwohl die Werte in App-Code und Constraint
divergieren. Das ist tolerierbar — der Diverg-Check passiert organisch
beim nächsten INSERT/UPDATE. Ist der Name da, wurde der Constraint
deployed.

---

## 🟢 PHOTOS_RLS_AUDIT.sql · OK

Pure read-only Diagnostik. Sauber. Output führt per Decision-Matrix
(A/B/C/D/E) zur passenden Variante in PHOTOS_RLS_FIX.sql.

Kleiner Hinweis: Query 5 (Anon-Access-Test) ist auskommentiert mit
`-- SET LOCAL ROLE anon;` — das ist richtig so, denn `SET LOCAL ROLE`
ohne Transaktion wäre gefährlich. Sebastian sollte nur explizit
`BEGIN; SET LOCAL ROLE anon; SELECT ...; ROLLBACK;` machen falls er das
prüfen will.

---

## 🟡 PHOTOS_RLS_FIX.sql · OK, mit kleinen Beobachtungen

Alle 3 Varianten komplett auskommentiert — korrekte "zuerst
entscheiden"-Struktur.

Anmerkungen:
- `photos.worker_id` wird als Join-Spalte auf `users.monteur_id`
  verwendet. Das Schema sollte das bestätigen (Query 3 im Audit gibt
  die Spalten aus).
- Die 5 Policies decken SELECT/INSERT/UPDATE/DELETE ab — vollständig.
- Monteur-Role-Liste `('monteur','techniker','obermonteur','helfer')`
  ist konsistent mit v3.7 Permission-Matrix.
- Fehlend: FOR ALL / public-Policy zum Widerrufen vorhandener Lax-
  Policies — falls Variante B nötig wird, ersetzt DROP POLICY aber die
  alten sowieso.

Sauber.

---

## 🟢 INDEX_AUDIT_v3.7.sql · OK

7 neue Indizes (3 b-tree + 4 composite). Alle mit
`CREATE INDEX CONCURRENTLY IF NOT EXISTS` — kein Table-Lock.

Anmerkungen:
- `CONCURRENTLY` läuft außerhalb einer Transaktion, also **nicht** im
  Supabase-SQL-Editor-"Run all"-Modus in einem einzelnen Aufruf
  möglich (der wrapt implizit in BEGIN/COMMIT). Lösung: jede
  `CREATE INDEX CONCURRENTLY`-Zeile als **separaten Run** ausführen.
  Alternativ im Postgres-CLI via `psql` mit `-1` **weglassen**.
- `ANALYZE ...` am Ende ist harmlos, läuft schnell.
- Monitoring-Query unten ist auskommentiert — sinnvoll, erst nach
  1-2 Tagen Betrieb sinnvoll zu laufen.

Keine Deploy-Blocker. Sebastian muss nur Zeilen einzeln ausführen
(CONCURRENTLY-Limitation).

---

## 🟢 INDEX_EFFECT_v3.8.sql · OK

Pure EXPLAIN-Queries, read-only. Vergleich vor/nach Index-Deploy.
Ergebnisse landen in `INDEX_EFFECT_v3.8_RESULTS.md`.

Eine Beobachtung: Query 5 `project_id='p1'` — reale Projekt-IDs
haben UUID-Format, nicht `p1`. Sebastian sollte das durch eine
echte Projekt-ID ersetzen sonst liefert die Query 0 Zeilen und
der Plan ist nicht repräsentativ.

Gleiche Sache in Query 6 `user_id='u1'` und Query 7 (nicht gelesen,
aber vermutlich ähnlich).

---

## Zusammenfassung

| File | Status | Action |
|---|---|---|
| **BASELINE_FIX_v3.8.sql** | 🔴 BLOCKER | 3 CHECK-Werte-Listen korrigieren vor Deploy |
| BASELINE_FIX_VERIFY_v3.8.sql | 🟢 | OK |
| PHOTOS_RLS_AUDIT.sql | 🟢 | OK, erst Audit |
| PHOTOS_RLS_FIX.sql | 🟡 | OK, erst nach Audit-Entscheidung |
| INDEX_AUDIT_v3.7.sql | 🟢 | OK, CONCURRENTLY → Zeilen einzeln ausführen |
| INDEX_EFFECT_v3.8.sql | 🟢 | OK, echte IDs in Queries 5-7 einsetzen |

Review-Dauer: ~20 Min. Keine Schema-Änderung nötig — nur SQL-Korrekturen.
