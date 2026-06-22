-- ═══════════════════════════════════════════════════════════════════════════
-- EPKolar — weekplan_rows (Multi-User-Sync, Zeilen-Level-Storage)  v1
-- ═══════════════════════════════════════════════════════════════════════════
-- Datum:    2026-06-22
-- Status:   READY-TO-EXECUTE — Human-Run-Gate (Sebastian / Chat-Claude)
-- Auftrag:  v3.9.500 Architektur-Refactor — weekplans-Blob raus, Zeilen-Tabelle rein.
--
-- ▶ HINTERGRUND
--   Bisher: weekplans speichert pro KW EINE Row mit data=JSON.stringify(rows).
--           saveWeek (Z.15694) sendet user's komplette rows-Liste → _sbUpsert
--           macht voller Overwrite. Live-Test (Chat-Claude): Gerät A speichert
--           Projekt-A, Gerät B (alter Stand) speichert 300ms später → A's
--           Projekt WEG. Last-Write-Wins auf KW-Ebene.
--
--   Neu:    Jede Planungs-Zeile (BVH + z-Daten) ist eine eigene DB-Row in
--           weekplan_rows. Save = UPSERT pro Zeile statt ganze KW. Konflikt
--           nur noch wenn ZWEI User dieselbe ZEILE gleichzeitig speichern
--           (selten) — statt jede beliebige Änderung in der Woche (häufig).
--
-- ▶ DATEN-MODELL (verifiziert gegen Frontend, Z.15426/15546/15694)
--   row.id     → text (float-timestamp + "Math.random()", z.B. "1719037892311.42")
--   row.bvh    → text (Baustellen-/Projekt-Name)
--   row.projId → text (FK auf projects.id, kann leer sein bei Freitext-BVH)
--   row.bem    → text (Bemerkung)
--   row.z      → jsonb {Mo:{ma:[ids],fz:[ids]}, Di:..., Mi:..., Do:..., Fr:..., Sa:...}
--
-- ▶ NICHT AUSFÜHREN ohne Pre-Check (siehe Schritt 0 unten).
-- ═══════════════════════════════════════════════════════════════════════════


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 0 — Pre-Check (READ-ONLY)
-- ───────────────────────────────────────────────────────────────────────────
-- 0.1) Existiert die Ziel-Tabelle bereits?
--    SELECT to_regclass('public.weekplan_rows');
--    -- erwartet: NULL bei Erst-Apply, oder Klasse bei idempotentem Re-Apply.
--
-- 0.2) Snapshot der existierenden weekplans (Backup-Referenz für die
--    spätere Migration WEEKPLAN_MIGRATE_v1.sql):
--    SELECT count(*) FROM public.weekplans;
--    SELECT count(*), sum(jsonb_array_length(
--      CASE WHEN jsonb_typeof(data::jsonb)='array' THEN data::jsonb ELSE '[]'::jsonb END
--    )) AS expected_row_count
--    FROM public.weekplans;
--    -- expected_row_count merken — Migration muss exakt dieselbe Anzahl liefern.
--
-- 0.3) Helper-Funktionen vorhanden (Pre-Check aus RLS_WELLE_1):
--    SELECT proname FROM pg_proc
--    WHERE proname IN ('is_hr','current_monteur_id')
--      AND pronamespace='public'::regnamespace;


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 1 — Tabelle anlegen (idempotent)
-- ───────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.weekplan_rows (
  row_id      TEXT PRIMARY KEY,                     -- = frontend row.id (float-timestamp.random)
  year        INTEGER NOT NULL,
  week        INTEGER NOT NULL,
  sort_order  INTEGER NOT NULL DEFAULT 0,           -- Reihenfolge in der Woche (Index in rows-Array)
  bvh         TEXT DEFAULT '',
  proj_id     TEXT DEFAULT '',
  bem         TEXT DEFAULT '',
  z           JSONB DEFAULT '{}'::jsonb,            -- {Mo:{ma,fz},Di:...,Sa:...}
  updated_by  TEXT DEFAULT '',
  updated_at  TIMESTAMPTZ DEFAULT NOW(),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Index für KW-Lookup (Lade-Pfad: WHERE year=? AND week=?):
CREATE INDEX IF NOT EXISTS idx_weekplan_rows_year_week
  ON public.weekplan_rows(year, week);

-- Trigger: updated_at automatisch (idempotent — Function vor Re-Create löschen):
CREATE OR REPLACE FUNCTION public.weekplan_rows_set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_weekplan_rows_updated_at ON public.weekplan_rows;
CREATE TRIGGER trg_weekplan_rows_updated_at
  BEFORE UPDATE ON public.weekplan_rows
  FOR EACH ROW EXECUTE FUNCTION public.weekplan_rows_set_updated_at();


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 2 — RLS aktivieren
-- ───────────────────────────────────────────────────────────────────────────
ALTER TABLE public.weekplan_rows ENABLE ROW LEVEL SECURITY;

-- Vorerst: alle authenticated dürfen lesen/schreiben. Frontend gated via
-- isAdmin (admin/projektleiter, ggf. buero) wie in der bestehenden saveWeek.
-- Spätere Härtung kann in RLS_WELLE_2 erfolgen (analog forms-Pattern).
--
-- HINWEIS: Drop-Loop mit erweitertem Pattern-Filter (v6-Erfahrung — auch
-- auth.role()-basierte offene Policies fangen):

DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
    WHERE schemaname='public' AND tablename='weekplan_rows'
      AND 'authenticated'::text = ANY(roles)
      AND (
        (cmd<>'INSERT' AND (qual='true' OR qual='(true)' OR qual LIKE '%auth.role()%authenticated%'))
        OR
        (cmd='INSERT' AND (with_check='true' OR with_check='(true)' OR with_check LIKE '%auth.role()%authenticated%'))
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.weekplan_rows', pol.policyname);
    RAISE NOTICE 'weekplan_rows: dropped open: %', pol.policyname;
  END LOOP;
END $$;

DROP POLICY IF EXISTS weekplan_rows_select ON public.weekplan_rows;
DROP POLICY IF EXISTS weekplan_rows_insert ON public.weekplan_rows;
DROP POLICY IF EXISTS weekplan_rows_update ON public.weekplan_rows;
DROP POLICY IF EXISTS weekplan_rows_delete ON public.weekplan_rows;

CREATE POLICY weekplan_rows_select ON public.weekplan_rows
  FOR SELECT TO authenticated USING (true);

CREATE POLICY weekplan_rows_insert ON public.weekplan_rows
  FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY weekplan_rows_update ON public.weekplan_rows
  FOR UPDATE TO authenticated USING (true) WITH CHECK (true);

CREATE POLICY weekplan_rows_delete ON public.weekplan_rows
  FOR DELETE TO authenticated USING (true);


-- ───────────────────────────────────────────────────────────────────────────
-- SCHRITT 3 — Verifikation
-- ───────────────────────────────────────────────────────────────────────────
-- 3.1) Struktur:
--    SELECT column_name, data_type, column_default
--    FROM information_schema.columns
--    WHERE table_schema='public' AND table_name='weekplan_rows'
--    ORDER BY ordinal_position;
--
-- 3.2) Indices:
--    SELECT indexname, indexdef FROM pg_indexes
--    WHERE schemaname='public' AND tablename='weekplan_rows';
--
-- 3.3) Policies:
--    SELECT policyname, cmd, qual::text, with_check::text
--    FROM pg_policies WHERE schemaname='public' AND tablename='weekplan_rows';
--    -- erwartet: 4 Policies (select/insert/update/delete), alle qual=true
--    --           bzw. with_check=true (frontend-gated für jetzt).
--
-- 3.4) Trigger:
--    SELECT tgname FROM pg_trigger WHERE tgrelid='public.weekplan_rows'::regclass;
--    -- erwartet: trg_weekplan_rows_updated_at
--
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK (falls Test fehlschlägt)
-- ═══════════════════════════════════════════════════════════════════════════
-- DROP TABLE IF EXISTS public.weekplan_rows CASCADE;
-- DROP FUNCTION IF EXISTS public.weekplan_rows_set_updated_at() CASCADE;
-- ═══════════════════════════════════════════════════════════════════════════
