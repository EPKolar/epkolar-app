-- ============================================================
-- Index-Effekt-Verify v3.8 · Block 4
-- Sebastian führt VOR + NACH Index-Deploy aus, Results in INDEX_EFFECT_v3.8_RESULTS.md
-- ============================================================
-- EXPLAIN (ANALYZE, BUFFERS) ist die Wahrheit — client-wall-clock via _perfBench()
-- ist complementär aber Netzwerk-lastig.
--
-- Erwartung pro Query:
--   Vor Index: Seq Scan ODER hohe Cost
--   Nach Index: Index Scan / Index Only Scan, deutlich niedrigere Cost
-- ============================================================

-- ── 1. arbeitsscheine nach monteur+status (v3.6 ix_as_monteur_status) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, nummer, kund_name, scheinstatus, termin_bestaetigt
FROM public.arbeitsscheine
WHERE monteur='w6' AND scheinstatus IN ('aufgenommen','in_bearbeitung','freigegeben')
ORDER BY termin_bestaetigt DESC
LIMIT 50;

-- ── 2. arbeitsscheine Volltext-Nummer (v3.6 ix_as_nummer) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM public.arbeitsscheine WHERE UPPER(nummer)='S021123';

-- ── 3. arbeitsscheine termin offen (v3.7 ix_as_termin_offen, Partial) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, termin_bestaetigt FROM public.arbeitsscheine
WHERE scheinstatus IN ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben')
  AND termin_bestaetigt < NOW()
ORDER BY termin_bestaetigt
LIMIT 50;

-- ── 4. time_entries worker+date (v3.6 ix_te_worker_date) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, worker_id, date, hours
FROM public.time_entries
WHERE worker_id='w3'
  AND date >= '2026-04-01'
ORDER BY date DESC
LIMIT 100;

-- ── 5. time_entries project (v3.7 ix_te_project_datum) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, project_id, date, hours
FROM public.time_entries
WHERE project_id='p1'
ORDER BY date DESC
LIMIT 100;

-- ── 6. notifications unread partial (v3.6 ix_notif_user_unread) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, title, created_at
FROM public.notifications
WHERE user_id='u1' AND (read = false OR read = 0)
ORDER BY created_at DESC
LIMIT 20;

-- ── 7. activity_log user (v3.6 ix_activity_user_created) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT action, entity_type, created_at
FROM public.activity_log
WHERE user_id='u1'
ORDER BY created_at DESC
LIMIT 50;

-- ── 8. activity_log action (v3.6 ix_activity_action_created) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT user_id, created_at
FROM public.activity_log
WHERE action='login'
ORDER BY created_at DESC
LIMIT 100;

-- ── 9. supplier_articles GIN Full-Text (v3.6 ix_sa_fts_german) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, bezeichnung, kt1
FROM public.supplier_articles
WHERE to_tsvector('german', coalesce(bezeichnung,'')||' '||coalesce(kt1,''))
      @@ plainto_tsquery('german', 'grohe armatur')
LIMIT 50;

-- ── 10. fahrtenbuch worker (v3.7 ix_fb_worker_datum) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, datum, km_start, km_ende
FROM public.fahrtenbuch
WHERE worker_id='w3'
ORDER BY datum DESC
LIMIT 50;

-- ── 11. as_kommentare per as (v3.7 ix_kommentare_as_created) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, autor_id, body, created_at
FROM public.as_kommentare
WHERE as_id='placeholder-as-id'
ORDER BY created_at DESC
LIMIT 20;

-- ── 12. photos per entity (v3.7 ix_photos_entity) ──
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT id, name, file_path, taken_at
FROM public.photos
WHERE entity_type='arbeitsschein' AND entity_id='placeholder-id'
ORDER BY taken_at DESC;

-- ── pg_stat_user_indexes Snapshot (nach 1-2 Tagen Betrieb erneut ausführen!) ──
SELECT
  relname AS table_name,
  indexrelname AS index_name,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  CASE WHEN idx_scan = 0 THEN '❌ UNUSED — DROP candidate'
       WHEN idx_scan < 10 THEN '⚠ LOW-USE — monitor'
       ELSE '✓ used' END AS status
FROM pg_stat_user_indexes
WHERE schemaname='public'
  AND (indexrelname LIKE 'ix_%')
ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;
