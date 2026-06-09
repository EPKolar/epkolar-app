-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK zu fix_material_catalogs_anon_v3.9.213.sql
-- Supabase: jiggujpruejkaomgxarp, schema public.
-- ═══════════════════════════════════════════════════════════════════════════
--
-- ZWECK: Setzt den anon-DML-Lockdown auf public.material_catalogs zurück, falls
--   nach Apply ein Schreib-/Lese-Problem auftritt. Stellt den anon-Zustand aus
--   dem Snapshot (Block 0 der Forward-Migration) wieder her und entfernt die in
--   Block 4 angelegten authenticated-DML-Defense-Policies.
--
-- HINWEIS: Der ursprüngliche anon-DML-Zugriff war eine LEAK-Fläche — dieser
--   Rollback ist NUR für den Notfall (z.B. wenn unerwartet ein anon-Pfad doch
--   benötigt wurde). Bevorzugt: Forward-Migration korrigieren statt anon-DML
--   dauerhaft wiederherstellen.
--
-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK A — in Block 4 angelegte authenticated-DML-Policies entfernen
--   (nur die durch die Forward-Migration NEU erzeugten Namen; falls schon
--    vorher gleichnamige Policies existierten, Snapshot konsultieren!)
-- ═══════════════════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS material_catalogs_auth_insert ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_auth_update ON public.material_catalogs;
DROP POLICY IF EXISTS material_catalogs_auth_delete ON public.material_catalogs;

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK B — anon Table-Grants aus Snapshot wiederherstellen
--   Spielt exakt die anon-Privilegien zurück, die VOR der Forward-Migration
--   bestanden (aus _rls_snapshot_matcat_v39213). Idempotent — GRANT ist No-Op,
--   wenn das Recht bereits besteht.
-- ═══════════════════════════════════════════════════════════════════════════
DO $$
DECLARE r record;
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables
             WHERE table_schema='public' AND table_name='_rls_snapshot_matcat_v39213') THEN
    FOR r IN
      SELECT DISTINCT privilege
      FROM public._rls_snapshot_matcat_v39213
      WHERE kind='grant' AND tablename='material_catalogs' AND grantee='anon'
        AND privilege IN ('INSERT','UPDATE','DELETE','TRUNCATE')
    LOOP
      EXECUTE format('GRANT %s ON public.material_catalogs TO anon;', r.privilege);
    END LOOP;
  ELSE
    RAISE NOTICE 'Snapshot-Tabelle _rls_snapshot_matcat_v39213 fehlt — manueller Grant-Restore nötig (siehe BLOCK B-MANUELL).';
  END IF;
END $$;

-- BLOCK B-MANUELL (nur falls Snapshot-Tabelle fehlt — vorher prüfen, was anon
--   tatsächlich vor dem Lockdown durfte; NICHT blind alles granten):
--   GRANT INSERT, UPDATE, DELETE ON public.material_catalogs TO anon;   -- ggf. TRUNCATE

-- ═══════════════════════════════════════════════════════════════════════════
-- BLOCK C — etwaige anon-DML-Policies wiederherstellen (NUR falls vorher vorhanden)
--   Im Snapshot prüfen, ob anon-DML-Policies existierten; nur dann unkommentieren
--   und mit den EXAKTEN qual/with_check aus dem Snapshot rekonstruieren.
--   (Standardfall: es gab KEINE benannten anon-DML-Policies — dann hier nichts tun.)
-- ═══════════════════════════════════════════════════════════════════════════
--   SELECT polname, roles, cmd, qual, with_check
--   FROM public._rls_snapshot_matcat_v39213
--   WHERE kind='policy' AND 'anon' = ANY(roles) AND cmd IN ('INSERT','UPDATE','DELETE','ALL');
--   -- Beispiel-Rekonstruktion (REKONSTRUKTION — gegen Snapshot verifizieren!):
--   -- CREATE POLICY material_catalogs_anon_insert ON public.material_catalogs
--   --   FOR INSERT TO anon WITH CHECK (<with_check aus Snapshot>);

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFY (nach Rollback):
--   SELECT grantee, privilege_type FROM information_schema.role_table_grants
--   WHERE table_schema='public' AND table_name='material_catalogs' AND grantee='anon'
--   ORDER BY privilege_type;
--   → entspricht wieder dem Vor-Lockdown-Zustand aus dem Snapshot.
--
--   SELECT polname, roles, cmd FROM pg_policies
--   WHERE schemaname='public' AND tablename='material_catalogs' ORDER BY cmd, polname;
--   → die in Block A entfernten material_catalogs_auth_*-Policies sind weg.
-- ═══════════════════════════════════════════════════════════════════════════
