-- ═══════════════════════════════════════════════════════════
-- v3.9.98 absences-Altlast-Repair + Konsolidierungs-Vorbereitung
-- Sebastian-Spec 2026-06-03: KEINEN Run ohne Schreibpfad-Decision (Code-Fix Z14027)!
-- ═══════════════════════════════════════════════════════════
--
-- KONTEXT:
-- - 30 absences-Rows haben worker_id = NAME ("Günther", "Pinger", "Schmid", "Paschinger")
-- - id-Key Format "Name_YYYY-MM-DD"
-- - from_date/to_date leer
-- - Code Z14027 schreibt aktiv worker_id=sel (Name) → Code-Fix nötig BEVOR diese Migration
--
-- AUSFÜHREN NUR NACH:
-- 1. Code-Fix Z14027 (worker_id=NAME → worker_id=wX) deployed
-- 2. Sebastian-Decision absences vs urlaubsantraege Konsolidierung
-- 3. Backup von public.absences

-- ═══════════════════════════════════════════════════════════
-- BLOCK 1: Backup zuerst (lokale Kopie als rollback-Quelle)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public.absences_backup_v3998 AS
  SELECT * FROM public.absences WHERE 1=0;  -- Schema-only first

INSERT INTO public.absences_backup_v3998 SELECT * FROM public.absences;
-- Verify: SELECT count(*) FROM public.absences_backup_v3998;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 2: NAME → wX Mapping (Sebastian-Spec)
-- ═══════════════════════════════════════════════════════════
-- Sebastian-Mapping aus Live-Diagnose:
--   Günther    = w6
--   Pinger     = w4
--   Schmid     = w5
--   Paschinger = w1

UPDATE public.absences SET worker_id = 'w6' WHERE worker_id = 'Günther';
UPDATE public.absences SET worker_id = 'w4' WHERE worker_id = 'Pinger';
UPDATE public.absences SET worker_id = 'w5' WHERE worker_id = 'Schmid';
UPDATE public.absences SET worker_id = 'w1' WHERE worker_id = 'Paschinger';

-- Verify (sollten alle 4 Updates returnen, total 30 Rows nach Sebastian's Befund):
-- SELECT worker_id, count(*) FROM public.absences GROUP BY worker_id;

-- ═══════════════════════════════════════════════════════════
-- BLOCK 3: from_date/to_date aus id-Key rekonstruieren
-- ═══════════════════════════════════════════════════════════
-- id-Pattern: "Name_YYYY-MM-DD"
-- Extrahiere Datum-Substring nach erstem "_"

UPDATE public.absences
SET
  from_date = CASE
    WHEN from_date IS NULL OR from_date = '' OR from_date = '1970-01-01'::date
    THEN substring(id from '[0-9]{4}-[0-9]{2}-[0-9]{2}')::date
    ELSE from_date
  END,
  to_date = CASE
    WHEN to_date IS NULL OR to_date = '' OR to_date = '1970-01-01'::date
    THEN substring(id from '[0-9]{4}-[0-9]{2}-[0-9]{2}')::date
    ELSE to_date
  END
WHERE
  (from_date IS NULL OR from_date = '' OR from_date = '1970-01-01'::date)
  OR (to_date IS NULL OR to_date = '' OR to_date = '1970-01-01'::date);

-- HINWEIS: Wenn from_date/to_date als TEXT (nicht DATE) gespeichert sind,
-- die ::date casts entfernen und stattdessen:
--   from_date = substring(id from '[0-9]{4}-[0-9]{2}-[0-9]{2}')

-- ═══════════════════════════════════════════════════════════
-- BLOCK 4: Verify
-- ═══════════════════════════════════════════════════════════

-- SELECT
--   worker_id,
--   from_date,
--   to_date,
--   id,
--   count(*) AS rows
-- FROM public.absences
-- GROUP BY worker_id, from_date, to_date, id
-- ORDER BY worker_id, from_date;

-- Erwartet nach Run:
-- - 30 Rows total
-- - worker_id ∈ {w1, w4, w5, w6}
-- - from_date/to_date alle gefüllt
-- - id-Keys unverändert (NAME_YYYY-MM-DD bleibt — id nicht repariert!)

-- ═══════════════════════════════════════════════════════════
-- BLOCK 5 (OPTIONAL): id-Key auf wX-Prefix migrieren
-- ═══════════════════════════════════════════════════════════
-- VORSICHT: ändert primary-key-Pattern. Client-localStorage caches verlieren Match.
-- Erst nach Code-Side cache-cleanup deployen.

-- UPDATE public.absences SET id = worker_id || '_' || substring(id from '[0-9]{4}-[0-9]{2}-[0-9]{2}')
-- WHERE id NOT LIKE worker_id || '%';

-- ═══════════════════════════════════════════════════════════
-- ROLLBACK (manuell, nur wenn nötig)
-- ═══════════════════════════════════════════════════════════
/*
TRUNCATE public.absences;
INSERT INTO public.absences SELECT * FROM public.absences_backup_v3998;
DROP TABLE public.absences_backup_v3998;
*/

-- ═══════════════════════════════════════════════════════════
-- CONSOLIDATION (separater Sprint — Sebastian-Decision)
-- ═══════════════════════════════════════════════════════════
-- Option A: absences und urlaubsantraege beide behalten
--   - absences = Tag-Marker (Kalender)
--   - urlaubsantraege = Antrag (von/bis-Range, status, grund)
-- Option B: Konsolidieren auf urlaubsantraege
--   - INSERT INTO urlaubsantraege SELECT ... FROM absences (Range pro worker+type pro Monat)
--   - Code-Side: AbsView.tog umstellen auf urlaubsantraege POST
-- Option C: Konsolidieren auf absences
--   - urlaubsantraege deprecaten
--
-- Empfehlung: Option A behalten — Trennung Kalender vs Antrag ist sauber.
