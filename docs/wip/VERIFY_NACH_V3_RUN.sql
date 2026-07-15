-- ═══════════════════════════════════════════════════════════════════
-- VERIFY_NACH_V3_RUN.sql — Kontrolle NACH dem Lauf von TERMINAL_FINAL_v3.sql.
-- READ-ONLY. Aendert nichts. Jederzeit gefahrlos ausfuehrbar.
-- Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Prueft drei Dinge auf einmal:
--   1) guard_urlaub_edit traegt den v3-VOLL-Body (Live-Body + stempel_terminal-Zweig).
--   2) Alle 7 Kiosk-RESTRICTIVE-Sperren sind da (is_kiosk_role).
--   3) Der Terminal-User existiert (public.users role='stempel_terminal').
--
-- KONTROLLWERT-PFLICHT: erst wenn ALLE drei "OK" liefern, ist der Run vollstaendig.
-- Ein Fehltreffer -> nicht weiterinterpretieren, melden.
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) Trigger-Body: v3-VOLL (mit Zweig) ─────────────────────────────
-- Normalform des prosrc (ASCII-\s kollabiert, getrimmt) MUSS treffen:
--   md5 = 47e149855e03893c429563ad5b2136c6   len = 2434
-- (Das ist der v3-Body INKL. stempel_terminal-Zweig. Zum Vergleich: der
--  reine Live-Body OHNE Zweig war 284dc6f19d45f4a8804ddb69e74e8ef6 / 1746.)
SELECT
  md5(btrim(regexp_replace(prosrc, '\s+', ' ', 'g')))    AS body_md5,
  length(btrim(regexp_replace(prosrc, '\s+', ' ', 'g'))) AS body_len,
  CASE WHEN md5(btrim(regexp_replace(prosrc, '\s+', ' ', 'g'))) = '47e149855e03893c429563ad5b2136c6'
        AND length(btrim(regexp_replace(prosrc, '\s+', ' ', 'g'))) = 2434
       THEN '✅ OK — v3-Body mit Terminal-Zweig aktiv'
       ELSE '⛔ ABWEICHUNG — nicht der erwartete v3-Body' END AS befund
FROM pg_proc
WHERE pronamespace = 'public'::regnamespace AND proname = 'guard_urlaub_edit';

-- ── 2) Kiosk-RESTRICTIVE-Sperren: Soll 7 ─────────────────────────────
SELECT count(*) AS kiosk_policies,
       CASE WHEN count(*) = 7 THEN '✅ OK — 7 Sperren' ELSE '⛔ erwartet 7' END AS befund
FROM pg_policies
WHERE schemaname = 'public' AND policyname LIKE '%\_no\_kiosk' ESCAPE '\'
  AND permissive = 'RESTRICTIVE';

-- ── 3) Terminal-User: Soll 1 Zeile ───────────────────────────────────
SELECT count(*) AS terminal_user,
       CASE WHEN count(*) = 1 THEN '✅ OK — 1 stempel_terminal'
            WHEN count(*) = 0 THEN '⛔ kein Terminal-User (public.users-Zeile fehlt)'
            ELSE '⚠ mehr als einer — pruefen' END AS befund
FROM public.users
WHERE role = 'stempel_terminal';

-- Erwartung gesamt: 3x ✅. Der Helper is_kiosk_role() und die RPC
-- stempel_terminal_workers() koennen zusaetzlich per pg_proc geprueft werden,
-- sind aber nicht Teil des v3-Runs (schon am 14.07. gelaufen).
