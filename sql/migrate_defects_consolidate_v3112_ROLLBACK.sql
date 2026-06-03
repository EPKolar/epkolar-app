-- ============================================================================
-- B-A defects-Doppelfeld-Konsolidierung — ROLLBACK (v3.11.2-data)
-- ============================================================================
-- Stellt die kanonischen Spalten (prio/images/zugewiesen/frist) aus dem Snapshot
-- `_defects_snapshot_v3112` wieder her, der von der Forward-Migration angelegt wurde.
--
-- ⚠️ VORAUSSETZUNG: Snapshot-Tabelle muss noch existieren (NICHT vorher gedroppt).
--   Prüfen:  SELECT count(*) FROM public._defects_snapshot_v3112;
--
-- Restauriert NUR die 4 kanonischen Spalten (das sind die einzigen, die die Forward-
-- Migration verändert hat). Die deprecated-Spalten wurden datentechnisch NICHT angefasst
-- (nur per COMMENT markiert) — sie bleiben unverändert.
--
-- Die DEPRECATED-COMMENTs werden hier zusätzlich entfernt (existence-guarded), damit der
-- Rollback den Schema-Zustand möglichst vollständig zurücksetzt.
-- ============================================================================

BEGIN;

-- ---- 0) Snapshot-Existenz absichern ----------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema='public' AND table_name='_defects_snapshot_v3112'
  ) THEN
    RAISE EXCEPTION 'ROLLBACK ABGEBROCHEN: Snapshot public._defects_snapshot_v3112 existiert nicht. Kein Rollback möglich.';
  END IF;
END $$;

-- ---- 1) Kanonische Spalten aus Snapshot restaurieren -----------------------
UPDATE public.defects d
   SET prio       = s.prio,
       images     = s.images,
       zugewiesen = s.zugewiesen,
       frist      = s.frist
  FROM public._defects_snapshot_v3112 s
 WHERE d.id = s.id;

-- ---- 2) DEPRECATED-COMMENTs entfernen (nur wo Spalte existiert) -------------
DO $$
DECLARE col text;
BEGIN
  FOREACH col IN ARRAY ARRAY['priority','fotos','worker','assignee','deadline'] LOOP
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='defects' AND column_name=col
    ) THEN
      EXECUTE format('COMMENT ON COLUMN public.defects.%I IS NULL', col);
      RAISE NOTICE 'DEPRECATED-Kommentar von defects.% entfernt.', col;
    END IF;
  END LOOP;
END $$;

-- ---- VERIFY (vor COMMIT) ---------------------------------------------------
-- Restaurierte Rows == Snapshot-Rows:
--   SELECT count(*) FROM public.defects d JOIN public._defects_snapshot_v3112 s ON d.id=s.id
--     WHERE d.prio IS DISTINCT FROM s.prio OR d.images IS DISTINCT FROM s.images
--        OR d.zugewiesen IS DISTINCT FROM s.zugewiesen OR d.frist IS DISTINCT FROM s.frist;  -- erwartet 0

COMMIT;

-- Snapshot bleibt bewusst erhalten (für erneuten Forward/Rollback-Zyklus).
-- Endgültiges Aufräumen NUR manuell nach Bestätigung:
--   DROP TABLE public._defects_snapshot_v3112;
