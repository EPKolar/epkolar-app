-- EPKolar DB-Index-Vorschläge v3.7 · Block 12 Addendum
-- Ergänzung zu sql/INDEX_AUDIT_v3.6.sql (schon vorhandene Indizes NICHT re-createn,
-- sind bereits CREATE IF NOT EXISTS). Dieses File fügt v3.7-spezifische hinzu.
-- ============================================================

-- 1. Partial-Index auf aktive AS (spart Platz, Query-Plan nutzt Index nur für offen)
--    Ergänzt ix_as_monteur_status aus v3.6.
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_as_termin_offen
  ON arbeitsscheine(termin_bestaetigt, termin_vorschlag)
  WHERE scheinstatus IN ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben');

-- 2. time_entries: Project-Sichtweite
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_te_project_datum
  ON time_entries(project_id, date DESC);

-- 3. Fahrtenbuch worker+datum (Monatsübersicht-Queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_fb_worker_datum
  ON fahrtenbuch(worker_id, datum DESC);

-- 4. as_kommentare — AS-Detail-View lädt Kommentare per as_id
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_kommentare_as_created
  ON as_kommentare(as_id, created_at DESC);

-- 5. Photos per entity (Detail-Views)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_photos_entity
  ON photos(entity_type, entity_id, taken_at DESC);

-- 6. worker_projects Lookup (Monteur-Zuordnung)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_wp_worker
  ON worker_projects(worker_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_wp_project
  ON worker_projects(project_id);

-- 7. defects (Mängel) per project
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_defects_project_status
  ON defects(project_id, status);

-- ── ANALYZE ─────────────────────────────
ANALYZE arbeitsscheine;
ANALYZE time_entries;
ANALYZE fahrtenbuch;
ANALYZE as_kommentare;
ANALYZE photos;
ANALYZE worker_projects;
ANALYZE defects;

-- ── Voraussetzung ──────────────────────
-- v3.6 Indizes (sql/INDEX_AUDIT_v3.6.sql) zuerst ausführen:
--   ix_as_monteur_status, ix_as_status_termin, ix_as_nummer, ix_as_push_pending,
--   ix_te_worker_date, ix_notif_user_unread, ix_activity_user_created,
--   ix_activity_action_created, ix_sa_fts_german, ix_abs_worker_date,
--   ix_mo_project_created, ix_bt_project_datum

-- ── Monitoring-Query (Index-Usage-Check nach 1-2 Tagen Betrieb) ──
/*
SELECT
  schemaname,
  relname AS table_name,
  indexrelname AS index_name,
  idx_scan,
  idx_tup_read,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size,
  CASE WHEN idx_scan = 0 THEN '❌ UNUSED — DROP candidate' ELSE '✓ used' END AS status
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND indexrelname LIKE 'ix_%'
ORDER BY idx_scan ASC, pg_relation_size(indexrelid) DESC;
*/
