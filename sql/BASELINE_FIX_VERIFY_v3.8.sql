-- ============================================================
-- BASELINE-FIX VERIFY v3.8.19
-- Nach Ausführung von BASELINE_FIX_v3.8.sql laufen lassen.
-- Erwartung: 8 Rows, Spalte `applied` überall TRUE.
-- ============================================================

SELECT 'users_email_unique' as check_item,
       EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='users_email_unique_idx') as applied
UNION ALL
SELECT 'arbeitsscheine_juprowa_id_unique',
       EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='arbeitsscheine_juprowa_id_unique_idx')
UNION ALL
SELECT 'arbeitsscheine_scheinstatus_chk',
       EXISTS(SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_scheinstatus_chk')
UNION ALL
SELECT 'arbeitsscheine_prioritaet_chk',
       EXISTS(SELECT 1 FROM pg_constraint WHERE conname='arbeitsscheine_prioritaet_chk')
UNION ALL
SELECT 'users_role_chk',
       EXISTS(SELECT 1 FROM pg_constraint WHERE conname='users_role_chk')
UNION ALL
SELECT 'photos_project_id_notnull',
       (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.photos'::regclass AND attname='project_id')
UNION ALL
SELECT 'time_entries_worker_id_notnull',
       (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.time_entries'::regclass AND attname='worker_id')
UNION ALL
SELECT 'time_entries_project_id_notnull',
       (SELECT attnotnull FROM pg_attribute WHERE attrelid='public.time_entries'::regclass AND attname='project_id');

-- ============================================================
-- Bei FALSE → Fix nicht appliziert (z.B. Exception im DO-Block).
-- RAISE NOTICE-Output aus BASELINE_FIX_v3.8.sql prüfen.
-- ============================================================
