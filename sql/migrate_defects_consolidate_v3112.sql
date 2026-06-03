-- ============================================================================
-- B-A defects-Doppelfeld-Konsolidierung (v3.11.2-data) — Sebastian-Service-Role-Run im SQL-Editor
-- ============================================================================
-- KONTEXT (CC-Code-Analyse v3.9.105 / _mapDefect index.html ~Z1752):
--   Die `defects`-Tabelle hat aus einer unvollständigen Migration DOPPELFELDER.
--   KANONISCH (das schreiben ALLE aktiven Writer — /api/defects POST Z4124 + Z10159):
--     prio  |  images  |  zugewiesen  |  frist
--   DEPRECATED Synonyme (nur noch Read-Fallback im Normalizer, KEIN Writer schreibt sie mehr):
--     priority → prio
--     fotos    → images
--     worker   → zugewiesen   (Legacy)
--     assignee → zugewiesen   (Legacy — Z10180 sendet noch assignee+zugewiesen parallel)
--     deadline → frist
--   READER sind durch _mapDefect bereits vereinheitlicht (liest beide Namen). Nur ALTBESTAND-Rows
--   können Daten in den deprecated-Spalten + LEERE kanonische Spalten haben.
--
-- ENTSCHEIDUNG (Sebastian): KANONISCH = prio/images/zugewiesen/frist.
--   Diese Migration kopiert NUR dort, wo kanonisch leer UND deprecated befüllt ist
--   (keine Überschreibung gültiger kanonischer Werte). Anschließend werden deprecated-Spalten
--   per COMMENT als DEPRECATED markiert. Es wird NICHTS gedroppt.
--
-- ⚠️⚠️ KRITISCH FÜR CHAT-CLAUDE — VOR DEM RUN PRÜFEN:
--   Es ist NICHT bekannt, welche deprecated-Spalten im LIVE-Schema tatsächlich existieren.
--   Diese Migration ist column-existence-guarded (DO-Block + information_schema.columns +
--   EXECUTE format(...)) — sie wirft KEINEN Fehler, wenn eine Spalte fehlt. Bitte trotzdem
--   vorab das Schema sichten:
--     SELECT column_name, data_type FROM information_schema.columns
--      WHERE table_schema='public' AND table_name='defects' ORDER BY column_name;
--   und prüfen, ob priority/fotos/worker/assignee/deadline existieren.
--
-- SICHERHEIT: idempotent, in Transaktion, vorher Snapshot `_defects_snapshot_v3112`.
--   Rollback: sql/migrate_defects_consolidate_v3112_ROLLBACK.sql
-- ============================================================================

BEGIN;

-- ---- 0) Snapshot für Rollback-Referenz -------------------------------------
DROP TABLE IF EXISTS public._defects_snapshot_v3112;
CREATE TABLE public._defects_snapshot_v3112 AS TABLE public.defects;

-- ---- 1) prio  ← priority  (nur wo prio leer & priority existiert+befüllt) ---
-- Column-existence-guarded: läuft NUR, wenn defects.priority im Live-Schema existiert.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='priority'
  ) THEN
    EXECUTE $sql$
      UPDATE public.defects
         SET prio = priority
       WHERE (prio IS NULL OR prio = '')
         AND priority IS NOT NULL AND priority <> ''
    $sql$;
    EXECUTE $sql$
      COMMENT ON COLUMN public.defects.priority IS
        'DEPRECATED v3.11.2 — kanonisch = prio. Nicht mehr schreiben (Read-Fallback nur via _mapDefect). Nicht gedroppt.'
    $sql$;
    RAISE NOTICE 'defects.priority: konsolidiert nach prio + als DEPRECATED markiert.';
  ELSE
    RAISE NOTICE 'defects.priority existiert NICHT im Schema — übersprungen.';
  END IF;
END $$;

-- ---- 2) images ← fotos  (nur wo images leer & fotos existiert+befüllt) ------
-- Hinweis: fotos/images sind JSON/Array-Text. "leer" = NULL, '', '[]', '{}'.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='fotos'
  ) THEN
    EXECUTE $sql$
      UPDATE public.defects
         SET images = fotos
       WHERE (images IS NULL OR images::text = '' OR images::text = '[]' OR images::text = '{}')
         AND fotos IS NOT NULL
         AND fotos::text <> '' AND fotos::text <> '[]' AND fotos::text <> '{}'
    $sql$;
    EXECUTE $sql$
      COMMENT ON COLUMN public.defects.fotos IS
        'DEPRECATED v3.11.2 — kanonisch = images. Nicht mehr schreiben (Read-Fallback nur via _mapDefect). Nicht gedroppt.'
    $sql$;
    RAISE NOTICE 'defects.fotos: konsolidiert nach images + als DEPRECATED markiert.';
  ELSE
    RAISE NOTICE 'defects.fotos existiert NICHT im Schema — übersprungen.';
  END IF;
END $$;

-- ---- 3) zugewiesen ← COALESCE(worker, assignee) ----------------------------
-- Zwei deprecated-Quellen. Priorität: worker zuerst, dann assignee. Beide einzeln guarded.
-- Daher dynamische COALESCE-Liste aus den TATSÄCHLICH existierenden Spalten.
DO $$
DECLARE
  has_worker   boolean;
  has_assignee boolean;
  src          text;
BEGIN
  SELECT EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='worker')   INTO has_worker;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='assignee') INTO has_assignee;

  IF has_worker AND has_assignee THEN
    src := 'COALESCE(NULLIF(worker,''''), NULLIF(assignee,''''))';
  ELSIF has_worker THEN
    src := 'NULLIF(worker,'''')';
  ELSIF has_assignee THEN
    src := 'NULLIF(assignee,'''')';
  ELSE
    src := NULL;
  END IF;

  IF src IS NOT NULL THEN
    EXECUTE format($sql$
      UPDATE public.defects
         SET zugewiesen = %s
       WHERE (zugewiesen IS NULL OR zugewiesen = '')
         AND %s IS NOT NULL
    $sql$, src, src);
    RAISE NOTICE 'defects.zugewiesen: konsolidiert aus %.', src;
  ELSE
    RAISE NOTICE 'defects.worker UND defects.assignee existieren NICHT — zugewiesen-Konsolidierung übersprungen.';
  END IF;

  -- DEPRECATED-Kommentare nur für tatsächlich existierende Spalten.
  IF has_worker THEN
    EXECUTE $sql$
      COMMENT ON COLUMN public.defects.worker IS
        'DEPRECATED v3.11.2 — kanonisch = zugewiesen. Nicht mehr schreiben (Read-Fallback nur via _mapDefect). Nicht gedroppt.'
    $sql$;
    RAISE NOTICE 'defects.worker als DEPRECATED markiert.';
  END IF;
  IF has_assignee THEN
    EXECUTE $sql$
      COMMENT ON COLUMN public.defects.assignee IS
        'DEPRECATED v3.11.2 — kanonisch = zugewiesen. Nicht mehr schreiben (Read-Fallback nur via _mapDefect). Nicht gedroppt.'
    $sql$;
    RAISE NOTICE 'defects.assignee als DEPRECATED markiert.';
  END IF;
END $$;

-- ---- 4) frist ← deadline  (nur wo frist leer & deadline existiert+befüllt) --
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='deadline'
  ) THEN
    EXECUTE $sql$
      UPDATE public.defects
         SET frist = deadline
       WHERE (frist IS NULL OR frist = '')
         AND deadline IS NOT NULL AND deadline <> ''
    $sql$;
    EXECUTE $sql$
      COMMENT ON COLUMN public.defects.deadline IS
        'DEPRECATED v3.11.2 — kanonisch = frist. Nicht mehr schreiben (Read-Fallback nur via _mapDefect). Nicht gedroppt.'
    $sql$;
    RAISE NOTICE 'defects.deadline: konsolidiert nach frist + als DEPRECATED markiert.';
  ELSE
    RAISE NOTICE 'defects.deadline existiert NICHT im Schema — übersprungen.';
  END IF;
END $$;

-- ---- VERIFY (vor COMMIT prüfen — alle erwartet 0!) -------------------------
-- Jede Query ist ebenfalls existence-guarded und gibt count zurück (0 = sauber konsolidiert).
-- Sie zählt Rows, bei denen die KANONISCHE Spalte leer ist, die DEPRECATED aber Daten hat.
-- (Bei nicht-existenter deprecated-Spalte → count 0 by definition / NOTICE skip.)
DO $$
DECLARE c bigint;
BEGIN
  -- a) prio leer aber priority gefüllt
  IF EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='priority') THEN
    EXECUTE $q$ SELECT count(*) FROM public.defects
      WHERE (prio IS NULL OR prio='') AND priority IS NOT NULL AND priority<>'' $q$ INTO c;
    RAISE NOTICE 'VERIFY a) prio<-priority Rest-offen: % (erwartet 0)', c;
  END IF;
  -- b) images leer aber fotos gefüllt
  IF EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='fotos') THEN
    EXECUTE $q$ SELECT count(*) FROM public.defects
      WHERE (images IS NULL OR images::text='' OR images::text='[]' OR images::text='{}')
        AND fotos IS NOT NULL AND fotos::text<>'' AND fotos::text<>'[]' AND fotos::text<>'{}' $q$ INTO c;
    RAISE NOTICE 'VERIFY b) images<-fotos Rest-offen: % (erwartet 0)', c;
  END IF;
  -- c) zugewiesen leer aber worker gefüllt
  IF EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='worker') THEN
    EXECUTE $q$ SELECT count(*) FROM public.defects
      WHERE (zugewiesen IS NULL OR zugewiesen='') AND worker IS NOT NULL AND worker<>'' $q$ INTO c;
    RAISE NOTICE 'VERIFY c) zugewiesen<-worker Rest-offen: % (erwartet 0)', c;
  END IF;
  -- d) zugewiesen leer aber assignee gefüllt
  IF EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='assignee') THEN
    EXECUTE $q$ SELECT count(*) FROM public.defects
      WHERE (zugewiesen IS NULL OR zugewiesen='') AND assignee IS NOT NULL AND assignee<>'' $q$ INTO c;
    RAISE NOTICE 'VERIFY d) zugewiesen<-assignee Rest-offen: % (erwartet 0)', c;
  END IF;
  -- e) frist leer aber deadline gefüllt
  IF EXISTS (SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='defects' AND column_name='deadline') THEN
    EXECUTE $q$ SELECT count(*) FROM public.defects
      WHERE (frist IS NULL OR frist='') AND deadline IS NOT NULL AND deadline<>'' $q$ INTO c;
    RAISE NOTICE 'VERIFY e) frist<-deadline Rest-offen: % (erwartet 0)', c;
  END IF;
END $$;

COMMIT;

-- Nach erfolgreichem VERIFY (alle NOTICE-counts = 0):
--   DROP TABLE public._defects_snapshot_v3112;   (optional aufräumen — ERST nach Smoke-Test!)
