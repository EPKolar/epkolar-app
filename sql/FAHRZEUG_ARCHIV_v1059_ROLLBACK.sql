-- IDEMPOTENT
-- =====================================================================================
-- FAHRZEUG_ARCHIV_v1059_ROLLBACK.sql  —  nimmt FAHRZEUG_ARCHIV_v1059_ENTWURF.sql zurueck
-- STATUS: ENTWURF — nur durch Sebastian (SQL-Editor, Projekt jiggujpruejkaomgxarp).
--
-- REIHENFOLGE: erst kiosk_fahrzeuge() auf den alten Rumpf (liest archiviert_am sonst ins Leere), dann Trigger und
--   Funktionen weg, ZULETZT die Spalten. Die Spalten werden NUR entfernt, wenn kein Fahrzeug archiviert ist —
--   sonst Abbruch: ein DROP COLUMN wuerde archivierte Fahrzeuge kommentarlos wieder in alle Listen holen und die
--   Information "archiviert am/von" vernichten. Erst im Admin-Archiv wiederherstellen (oder bewusst per SQL
--   update ... set archiviert_am = null), dann diesen Rollback laufen lassen.
-- Achtung: nach dem Rollback ist Hart-Loeschen ueber die App wieder moeglich (Zustand vor v1059).
-- Kein CASCADE.
-- =====================================================================================

BEGIN;

-- 0. Vorpruefung: keine archivierten Fahrzeuge
DO $$
DECLARE v_arch int := 0;
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_schema = 'public' AND table_name = 'fahrzeuge' AND column_name = 'archiviert_am') THEN
    EXECUTE 'SELECT count(*) FROM public.fahrzeuge WHERE archiviert_am IS NOT NULL' INTO v_arch;
  END IF;
  IF v_arch > 0 THEN
    RAISE EXCEPTION 'Rollback abgebrochen: % Fahrzeug(e) sind archiviert - erst wiederherstellen, sonst geht die Archiv-Information verloren', v_arch;
  END IF;
  RAISE NOTICE 'VORHER: archivierte Fahrzeuge = % (ok)', v_arch;
END $$;

-- 1. kiosk_fahrzeuge() woertlich wie vor v1059 (Stand 19.11.2026, gelesen per pg_get_functiondef)
CREATE OR REPLACE FUNCTION public.kiosk_fahrzeuge()
 RETURNS TABLE(id text, kennzeichen text, typ text, modell text, status text)
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  IF NOT ( public.auth_role() = 'lager_display'
           OR public.is_staff() ) THEN
    RAISE EXCEPTION 'not authorized' USING errcode = '42501';
  END IF;
  RETURN QUERY
    SELECT f.id::text, f.kennzeichen::text, f.typ::text, f.modell::text, f.status::text
    FROM public.fahrzeuge f
    ORDER BY f.kennzeichen ASC;
END
$function$;

-- 2. Trigger + Funktionen
DROP TRIGGER IF EXISTS trg_fahrzeuge_kein_hartloeschen ON public.fahrzeuge;
DROP TRIGGER IF EXISTS trg_fahrzeuge_archiv_nur_admin ON public.fahrzeuge;
DROP FUNCTION IF EXISTS public.fahrzeuge_kein_hartloeschen();
DROP FUNCTION IF EXISTS public.fahrzeuge_archiv_nur_admin();

-- 3. Spalten (nur leer, siehe Vorpruefung)
ALTER TABLE public.fahrzeuge DROP COLUMN IF EXISTS archiviert_von;
ALTER TABLE public.fahrzeuge DROP COLUMN IF EXISTS archiviert_am;

-- 4. Nachher
DO $$
DECLARE v_spalten int; v_trg int; v_fn int;
BEGIN
  SELECT count(*) INTO v_spalten FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'fahrzeuge' AND column_name IN ('archiviert_am', 'archiviert_von');
  SELECT count(*) INTO v_trg FROM pg_trigger WHERE tgname IN ('trg_fahrzeuge_kein_hartloeschen', 'trg_fahrzeuge_archiv_nur_admin');
  SELECT count(*) INTO v_fn FROM pg_proc WHERE proname IN ('fahrzeuge_kein_hartloeschen', 'fahrzeuge_archiv_nur_admin');
  RAISE NOTICE 'NACHHER: Spalten=% Trigger=% Funktionen=% (erwartet 0/0/0)', v_spalten, v_trg, v_fn;
END $$;

COMMIT;
