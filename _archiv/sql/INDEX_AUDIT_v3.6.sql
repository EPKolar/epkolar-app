-- EPKolar DB-Index-Vorschläge v3.6.0 · Block 11 Audit
-- ===============================================
-- Manuell im Supabase SQL-Editor ausführen. KEIN autom. Deploy.
-- Jeder Index ist CONCURRENTLY und IF NOT EXISTS — safe für Live-DB.
-- Nach jedem CREATE INDEX: EXPLAIN ANALYZE gegen die Ziel-Query laufen lassen
-- um den Performance-Gain zu messen.

-- ───────────────────────────────────────────────
-- 1. arbeitsscheine: Worker-scoped + Status-Filter
-- Typische Monteur-Query: WHERE monteur=? AND scheinstatus IN ('aufgenommen','in_bearbeitung','freigegeben')
-- Ohne Index: Seq-Scan. Mit Index: Index-Scan auf monteur, dann Filter.
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_as_monteur_status
  ON arbeitsscheine(monteur, scheinstatus);

-- Zusätzlich: WHERE scheinstatus IN ('aufgenommen',...) ORDER BY termin_bestaetigt
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_as_status_termin
  ON arbeitsscheine(scheinstatus, termin_bestaetigt DESC);

-- Nummer-Lookup (Juprowa-Sync-Match, OFFA-Import-Dup-Check)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_as_nummer
  ON arbeitsscheine(UPPER(nummer));

-- Juprowa-Push-Pending-Filter
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_as_push_pending
  ON arbeitsscheine(push_pending, juprowa_id)
  WHERE push_pending = true;

-- ───────────────────────────────────────────────
-- 2. time_entries: Worker + Datum
-- Typische Query: WHERE worker_id=? AND date>=? AND date<=?
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_te_worker_date
  ON time_entries(worker_id, date DESC);

-- ───────────────────────────────────────────────
-- 3. notifications: User + Unread
-- Typische Query: WHERE user_id=? AND read=false ORDER BY created_at DESC
-- Partial-Index (nur unread) spart Platz und ist ultra-schnell.
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_notif_user_unread
  ON notifications(user_id, created_at DESC)
  WHERE read = false OR read = 0;

-- ───────────────────────────────────────────────
-- 4. activity_log: User + Timestamp (Audit-UI)
-- Typische Query: WHERE user_id=? ORDER BY created_at DESC LIMIT 200
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_activity_user_created
  ON activity_log(user_id, created_at DESC);

-- Action-Filter (Login/Failed/...)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_activity_action_created
  ON activity_log(action, created_at DESC);

-- ───────────────────────────────────────────────
-- 5. supplier_articles: Full-Text-Search (25k Rows!)
-- Typische Query: WHERE bezeichnung ILIKE '%xxx%' OR kt1 ILIKE '%xxx%'
-- GIN-Index mit to_tsvector gibt O(log N) statt O(N).
-- ACHTUNG: Index-Build dauert bei 25k Rows einige Sekunden.
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sa_fts_german
  ON supplier_articles
  USING gin(to_tsvector('german',
    coalesce(bezeichnung,'') || ' ' ||
    coalesce(kt1,'') || ' ' ||
    coalesce(artikel_nr,'')
  ));

-- Alternative / zusätzlich: Trigram-Index für substring-Match (ILIKE '%x%')
-- Braucht pg_trgm extension
-- CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sa_trgm
--   ON supplier_articles USING gin(bezeichnung gin_trgm_ops);

-- ───────────────────────────────────────────────
-- 6. absences: Worker + Date-Range (Urlaubsantrag-Listen)
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_abs_worker_date
  ON absences(worker_id, date DESC);

-- ───────────────────────────────────────────────
-- 7. material_orders: Project-scoped
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_mo_project_created
  ON material_orders(project_id, created_at DESC);

-- ───────────────────────────────────────────────
-- 8. bautagebuch: Project + Datum
-- ───────────────────────────────────────────────
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_bt_project_datum
  ON bautagebuch(project_id, datum DESC);

-- ───────────────────────────────────────────────
-- ANALYZE (Statistiken aktualisieren nach Index-Erstellung)
-- ───────────────────────────────────────────────
ANALYZE arbeitsscheine;
ANALYZE time_entries;
ANALYZE notifications;
ANALYZE activity_log;
ANALYZE supplier_articles;
ANALYZE absences;
ANALYZE material_orders;
ANALYZE bautagebuch;

-- ───────────────────────────────────────────────
-- OPTIONAL: Index-Nutzung prüfen nach 1 Tag Betrieb
-- ───────────────────────────────────────────────
/*
SELECT
  schemaname,
  relname AS table_name,
  indexrelname AS index_name,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND indexrelname LIKE 'ix_%'
ORDER BY idx_scan DESC;
-- idx_scan = 0 nach 1 Tag → Index unused, kann DROP INDEX CONCURRENTLY
*/
