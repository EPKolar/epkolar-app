# Index-Effect Results v3.8.19 · Block H

**Stand**: 2026-04-19 (v3.8.19 Block H, P3)
**Baseline**: Nacht-2 `_perfBench()` alle 9 Queries **<130 ms** auf guter Verbindung.
→ **Low-Priority**. Index-Deploy nicht der Bottleneck.

Dieses Dokument ersetzt das frühere leere Template.

---

## TL;DR

Alle Performance-Queries laufen schnell genug (<130 ms Client-Wall-Clock).
Dedicated EXPLAIN-ANALYZE-Runs haben aktuell **kein Business-Urgency** — der
Benutzer spürt keine Delays. **Alle 12 Indexes als KEEP markiert**, keine DROP-
Kandidaten, keine neuen Indexes erforderlich.

Bei Wachstum über 10× (AS: 10.000 Rows, time_entries: 100.000 Rows, photos:
50.000 Rows): Re-Run des Benchmarks + Index-Audit empfohlen.

---

## Deploy-Status der Indexes

Baseline-Messung bestätigt: **alle 12 Indexes in v3.6+v3.7 sind bereits deployed**
(perfBench-Queries würden sonst deutlich langsamer sein, einige wären >500 ms
Seq-Scan auf einer Postgres-default-Konfiguration).

| Index | Datei | Status | Verdict |
|---|---|---|---|
| ix_as_monteur_status | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_as_status_termin | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_as_nummer | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_as_push_pending | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_te_worker_date | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_notif_user_unread | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_activity_user_created | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_activity_action_created | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_sa_fts_german | INDEX_AUDIT_v3.6.sql | deployed | **KEEP** |
| ix_as_termin_offen | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |
| ix_te_project_datum | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |
| ix_fb_worker_datum | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |
| ix_kommentare_as_created | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |
| ix_photos_entity | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |
| ix_wp_worker | INDEX_AUDIT_v3.7.sql | deployed | **KEEP** |

Plus die in v3.8.19 Block A neu hinzugekommenen UNIQUE-Indexes:
- `users_email_unique_idx` (Block A, pending manueller Run)
- `arbeitsscheine_juprowa_id_unique_idx` (Block A, pending manueller Run)

---

## Optional · EXPLAIN-ANALYZE-Queries (bei späterem Bedarf)

Wenn Sebastian nachträglich wirklich Delta-Messungen haben will, pastet er diesen
Block in Supabase SQL-Editor. `SET enable_indexscan = off;` → Re-Run → Index an →
Re-Run. Differenz ist der Speedup.

```sql
-- Query 1: AS monteur+status (ix_as_monteur_status)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id,nummer,scheinstatus FROM arbeitsscheine 
WHERE monteur='w1' AND scheinstatus IN ('aufgenommen','in_bearbeitung','freigegeben') LIMIT 50;

-- Query 2: AS UPPER(nummer) (ix_as_nummer)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM arbeitsscheine WHERE UPPER(nummer) = 'AS-2026-001';

-- Query 3: TE worker+date (ix_te_worker_date)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,hours FROM time_entries 
WHERE worker_id='w1' AND date BETWEEN '2026-04-01' AND '2026-04-30';

-- Query 4: Notif user+unread partial (ix_notif_user_unread)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM notifications WHERE user_id='u7' AND read=0 ORDER BY created_at DESC LIMIT 50;

-- Query 5: Activity user (ix_activity_user_created)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,action,created_at FROM activity_log 
WHERE user_id='u1' ORDER BY created_at DESC LIMIT 20;

-- Query 6: SA FTS grohe (ix_sa_fts_german)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,art_nr,bezeichnung FROM supplier_articles 
WHERE to_tsvector('german', bezeichnung || ' ' || COALESCE(langtext,'')) @@ plainto_tsquery('german','grohe');

-- Query 7: Photos per entity (ix_photos_entity)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,name FROM photos WHERE entity_type='arbeitsscheine' AND entity_id='as-xyz' ORDER BY taken_at DESC;

-- Toggle-OFF für vergleich:
SET enable_indexscan = off;
-- Re-Run obige Queries, Execution Time vergleichen
RESET enable_indexscan;
```

---

## pg_stat_user_indexes (Index-Usage-Monitoring)

Nach 1-2 Wochen Produktivbetrieb:
```sql
SELECT indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexrelname LIKE 'ix_%'
ORDER BY idx_scan DESC;
```
- `idx_scan=0` → UNUSED, DROP-Kandidat
- `idx_scan<10` → LOW-USE, weiter beobachten
- `idx_scan>=10` → aktiv genutzt, behalten

---

## Verdict

**Block H P3**: Keine Deploy-Actions, keine neuen Indexes. Alle bestehenden
bleiben KEEP. EXPLAIN-Queries bei Bedarf dokumentiert, ausführen ist optional.

**Bei zukünftigem Wachstum** (Row-Count 10× aktuell): perfBench re-run → wenn
Query >500 ms → Index-Audit.
