-- ═══════════════════════════════════════════════════════════════════
-- VERIFY_TRIGGER_BODIES_v1.sql
-- READ-ONLY. Aendert NICHTS. Kann jederzeit gefahrlos ausgefuehrt werden.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- ── WARUM ES DIESE DATEI GIBT ─────────────────────────────────────
-- sql/security_triggers_LIVE_v3911.sql gibt sich als Live-Stand der
-- fuenf Security-Trigger aus. Es ist eine REKONSTRUKTION.
--
-- Fuer EINEN der fuenf wurde das am 14.07.2026 gemessen:
--   guard_urlaub_edit   Live: 1746 Zeichen   Repo: 953 Zeichen
--   -> ~800 Zeichen echter Logik fehlen in der Repo-Datei.
-- Ein CREATE OR REPLACE auf dieser Basis haette sie KOMMENTARLOS
-- geloescht (kein Fehler, kein Rollback, keine Warnung). Beinahe
-- passiert ueber sql/STEMPEL_TERMINAL_v2.sql.
--
-- DIE ANDEREN VIER WURDEN NIE GEMESSEN.
-- Gleiche Datei, gleicher Rekonstruktionsvorgang, gleicher Tag. Es gibt
-- keinen Grund anzunehmen, dass ausgerechnet die vollstaendig sind. Und
-- es sind keine Nebensaechlichkeiten:
--   guard_users_privilege  — Schutz gegen Rechte-Eskalation
--   guard_admin_only       — Admin-Gate
--   guard_projects         — Projekt-Schutz
--   guard_kontingent       — Urlaubskontingent-Schutz
--
-- Diese Datei misst alle fuenf auf einmal und stellt sie den
-- Repo-Werten gegenueber. Ergebnis "ABWEICHUNG" heisst: die Repo-Datei
-- ist fuer diese Funktion KEINE Replace-Basis.
--
-- Normalform = Funktionskoerper (prosrc, also der Text zwischen den
-- Dollar-Quotes), Whitespace-Laeufe zu einem Space, getrimmt, dann MD5.
-- Diese Methode ist gegengeprueft: sie liefert fuer die Repo-Fassung von
-- guard_urlaub_edit exakt die 953 Zeichen, die Chat-Claude gemessen hat.
-- ═══════════════════════════════════════════════════════════════════

WITH repo(fn, repo_len, repo_md5) AS (
  VALUES
    -- Aus sql/security_triggers_LIVE_v3911.sql berechnet (Claude Code, 14.07.2026)
    ('guard_urlaub_edit',      953, '46dd96ad12438636b7929b78a49a66c8'),
    ('guard_kontingent',       387, '26bb760bc19d932174ef55b038c14b85'),
    ('guard_users_privilege',  680, 'd3f029b094ccdb68e569d337f2e4c5a0'),
    ('guard_admin_only',       300, '88c95f06d048b2966d51879fe7b7a37b'),
    ('guard_projects',         328, 'ba09f470a8d334e4d186c6320d492754')
),
live AS (
  SELECT p.proname::text AS fn,
         length(btrim(regexp_replace(p.prosrc, '\s+', ' ', 'g'))) AS live_len,
         md5(btrim(regexp_replace(p.prosrc, '\s+', ' ', 'g')))    AS live_md5
    FROM pg_proc p
   WHERE p.pronamespace = 'public'::regnamespace
     AND p.proname IN ('guard_urlaub_edit','guard_kontingent',
                       'guard_users_privilege','guard_admin_only','guard_projects')
)
SELECT r.fn,
       l.live_len,
       r.repo_len,
       l.live_len - r.repo_len AS fehlende_zeichen,
       CASE
         WHEN l.fn IS NULL              THEN '❓ nicht in der DB gefunden'
         WHEN l.live_md5 = r.repo_md5   THEN '✅ identisch — Repo ist Replace-Basis'
         ELSE                                '⛔ ABWEICHUNG — Repo ist KEINE Replace-Basis'
       END AS befund
  FROM repo r
  LEFT JOIN live l ON l.fn = r.fn
 ORDER BY (l.live_len - r.repo_len) DESC NULLS LAST;

-- ═══════════════════════════════════════════════════════════════════
-- ERWARTUNG fuer guard_urlaub_edit: ⛔ ABWEICHUNG, ~793 fehlende Zeichen
-- (1746 live - 953 repo). Das ist der bereits bekannte Fall und dient
-- hier als Kontrolle, dass die Messung ueberhaupt richtig rechnet.
--
-- Zeigt eine der ANDEREN vier ebenfalls ⛔, dann ist auch dort Logik in
-- der Repo-Datei verlorengegangen, die niemand mehr kennt.
--
-- ── FUER JEDE ABWEICHENDE FUNKTION: Ist-Stand sichern ───────────────
--   select pg_get_functiondef(oid)
--     from pg_proc
--    where pronamespace='public'::regnamespace
--      and proname='<funktion>';
-- Ergebnis 1:1 ablegen unter docs/wip/<funktion>_LIVE_<datum>.sql.
-- ERST DANN darf jemals ein CREATE OR REPLACE darauf aufbauen.
-- ═══════════════════════════════════════════════════════════════════
