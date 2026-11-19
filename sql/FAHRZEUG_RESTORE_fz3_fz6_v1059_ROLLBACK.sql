-- IDEMPOTENT
-- =====================================================================================
-- FAHRZEUG_RESTORE_fz3_fz6_v1059_ROLLBACK.sql  —  nimmt FAHRZEUG_RESTORE_fz3_fz6_v1059_ENTWURF.sql zurueck
-- STATUS: ENTWURF — nur durch Sebastian (SQL-Editor, Projekt jiggujpruejkaomgxarp).
--
-- Loescht GENAU die zwei wiederhergestellten Zeilen fahrzeuge.id IN ('fz3','fz6') — sonst nichts.
-- Kein CASCADE (es gibt auch keinen Fremdschluessel auf fahrzeuge). Kind-Zeilen (fz_positions, fz_latest,
-- fz_fahrten von fz3) bleiben unberuehrt stehen — so wie vor dem Restore.
-- Laeuft im SQL-Editor als Inhaber; der v1059-Loeschschutz (trg_fahrzeuge_kein_hartloeschen) sperrt nur
-- App/API-Aufrufe und laesst diesen Weg zu.
-- Ein zweiter Lauf findet 0 Zeilen und aendert nichts.
-- =====================================================================================

BEGIN;

DO $$
DECLARE r record; v_n int;
BEGIN
  SELECT count(*) INTO v_n FROM public.fahrzeuge;
  RAISE NOTICE 'VORHER: fahrzeuge=%', v_n;
  FOR r IN SELECT id, kennzeichen, updated_at FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6') ORDER BY id LOOP
    RAISE NOTICE 'wird entfernt: % % (updated_at %)', r.id, r.kennzeichen, r.updated_at;
  END LOOP;
END $$;

DELETE FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6');

DO $$
DECLARE v_n int; v_rest int;
BEGIN
  SELECT count(*) INTO v_n FROM public.fahrzeuge;
  SELECT count(*) INTO v_rest FROM public.fahrzeuge WHERE id IN ('fz3', 'fz6');
  IF v_rest <> 0 THEN RAISE EXCEPTION 'NACHHER: fz3/fz6 noch da (%)', v_rest; END IF;
  RAISE NOTICE 'NACHHER: fahrzeuge=%', v_n;
END $$;

COMMIT;
