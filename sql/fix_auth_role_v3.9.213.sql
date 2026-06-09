-- NICHT ANGEWENDET — wartet auf Editor-Run durch Sebastian/Chat-Claude (CC hat keinen DB-Schreibzugriff).
-- =============================================================================
-- fix_auth_role_v3.9.213.sql
-- THEMA: public.auth_role() liest die kanonische Rolle aus public.users
--        (WHERE auth_user_id = auth.uid()), Fallback 'anon' wenn kein Match.
-- ANGLEICHUNG an den bereits angewendeten is_staff()/current_user_role()-Fix
--   (beide lesen users.role via auth_user_id=auth.uid(), NICHT mehr app_metadata.role).
--   Beleg: docs/handoff/HANDOFF-2026-06-09-DATENSCHUTZ.md Z.40;
--          _archiv/sql/ALL_SQL_ONEPASTE.sql Z.76-78 (current_user_role-Vorlage).
-- =============================================================================
--
-- 🔴 PFLICHT-CAPTURE VOR APPLY (Live-Body von auth_role() ist NICHT im Repo!):
--   Der einzige Repo-Hinweis ist ein ALTER ... SET search_path in
--   sql/harden_function_search_path_v3.9.157.sql (Z.7). Der FUNKTIONSKÖRPER und
--   die EXAKTE Signatur (Rückgabetyp/Default/Volatilität) sind NICHT belegt.
--   → Der untenstehende Body ist eine REKONSTRUKTION nach dem Muster von
--     current_user_role(). VOR dem Apply ZWINGEND die Live-Definition ziehen und
--     diffen:
--
--       SELECT pg_get_functiondef('public.auth_role()'::regprocedure);
--
--   Prüfe insbesondere:
--     1) RÜCKGABETYP: unten als RETURNS text angenommen (Annahme, da Rollen=text
--        und in ~20 Policies typischerweise gegen text-Literale verglichen wird).
--        Falls Live abweicht → Datei anpassen, NICHT blind übernehmen.
--     2) DEFAULT/FALLBACK-WERT: unten 'anon'. Die harden-Datei Z.4 dokumentiert
--        "auth_role='anon'" für anonyme Sessions → 'anon' ist konsistent.
--        Falls Live einen anderen Default liefert (z.B. NULL oder '') → angleichen.
--     3) Ob die Live-Version evtl. zusätzlich app_metadata/JWT als Quelle nutzt —
--        diese Quelle wird hier BEWUSST entfernt (veraltet/inkonsistent, siehe
--        migrate_fahrbewilligungen_v3.9.203.sql Z.30-31).
--
-- ⚠️ WARNUNG — BLAST RADIUS:
--   auth_role() steckt in ~20 RLS-Policies. Eine Verhaltensänderung wirkt sofort
--   auf alle diese Policies. APPLY ERST nach Smoke-Test ALLER 5 Rollen
--   (admin, buero, projektleiter, techniker, monteur) + anon. Bei Fehlverhalten
--   sofort fix_auth_role_v3.9.213_ROLLBACK.sql einspielen (gecapturte Live-Def).
--
--   Hinweis: Falls die ALTE Live-Version aus app_metadata.role gelesen hat, KANN
--   sich der Rückgabewert je User ändern (app_metadata war teils null/inkonsistent
--   — buero=null, ein PL=monteur). Das ist die BEABSICHTIGTE Korrektur, aber Policy-
--   Auswirkungen pro Tabelle vor dem Apply durchdenken.
-- =============================================================================

-- ─── REKONSTRUKTION — vor Apply gegen Live-Def verifizieren! ─────────────────
CREATE OR REPLACE FUNCTION public.auth_role()
RETURNS text
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT COALESCE(
    (SELECT role FROM public.users WHERE auth_user_id = auth.uid() LIMIT 1),
    'anon'
  );
$$;

-- EXECUTE-Grant idempotent sicherstellen (Helper wird von authenticated genutzt;
-- anon ruft Policies, die auth_role() referenzieren, ebenfalls aus → beide granten,
-- analog zur ursprünglichen anon-tauglichen Semantik 'anon').
GRANT EXECUTE ON FUNCTION public.auth_role() TO authenticated;
GRANT EXECUTE ON FUNCTION public.auth_role() TO anon;

-- =============================================================================
-- VERIFY (nach Apply manuell ausführen — NICHT Teil des Apply-Transaktionsblocks):
--
--   -- Attribute erhalten? (STABLE, SECURITY DEFINER, search_path)
--   SELECT proname, prosecdef, provolatile, proconfig
--   FROM pg_proc WHERE proname = 'auth_role' AND pronamespace = 'public'::regnamespace;
--   -- erwartet: prosecdef = true, provolatile = 's' (STABLE),
--   --           proconfig = {search_path=public,\ pg_temp}
--
--   -- Pro Rolle einloggen (Frontend/JWT) und prüfen:
--   --   admin         -> SELECT public.auth_role();  =>  'admin'
--   --   buero         -> SELECT public.auth_role();  =>  'buero'
--   --   projektleiter -> SELECT public.auth_role();  =>  'projektleiter'
--   --   techniker     -> SELECT public.auth_role();  =>  'techniker'
--   --   monteur       -> SELECT public.auth_role();  =>  'monteur'
--   --   anon (kein Login) -> SELECT public.auth_role();  =>  'anon'
--
--   -- Smoke der ~20 abhängigen Policies: je Rolle erwartete Sichtbarkeit der
--   -- betroffenen Tabellen gegen Soll (sql/RLS_RECONCILE_v3.8.md) prüfen.
-- =============================================================================
