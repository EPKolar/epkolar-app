-- ═══════════════════════════════════════════════════════════════════
-- VERIFY_TRIGGER_BODIES_v2.sql
-- READ-ONLY. Aendert NICHTS. Jederzeit gefahrlos ausfuehrbar.
--
-- ERSETZT v1. v1 HAT FALSCH GEMESSEN — und zwar so, dass man es fast
-- geglaubt haette. Was v1 falsch machte und warum das eine ganze
-- Fehlerklasse ist, steht unten. Erst lesen, dann ausfuehren.
-- ═══════════════════════════════════════════════════════════════════
--
-- ── DER FEHLER IN v1 ──────────────────────────────────────────────
-- v1 verglich AEPFEL MIT BIRNEN:
--   live-Seite  von POSTGRES normalisiert:  regexp_replace(prosrc,'\s+',' ','g')
--   repo-Seite  von PYTHON   normalisiert:  re.sub(r'\s+',' ',body).strip()
--
-- Zwei Regex-Engines mit ZWEI VERSCHIEDENEN DEFINITIONEN VON \s:
--   Python   \s  = ASCII-Whitespace  UND  Unicode-Whitespace (U+00A0 usw.)
--   Postgres \s  = [[:space:]]       = NUR ASCII-Whitespace
--
-- Enthaelt der Body ein geschuetztes Leerzeichen (U+00A0), kollabiert Python
-- es mit, Postgres nicht. Postgres zaehlt dann MEHR Zeichen und liefert einen
-- ANDEREN md5 — aus demselben, voellig unveraenderten Body.
--
-- Lokal reproduziert (8-Zeilen-Body mit NBSP in der Einrueckung):
--   Python-Normalform    120 Zeichen   md5 15141b83...
--   Postgres-Normalform  132 Zeichen   md5 4fece232...
-- Beide Werte aus DEMSELBEN Body. Nur die Engine gewechselt.
--
-- ── WARUM DAS HIER KEIN THEORETISCHES PROBLEM IST ─────────────────
-- Diese Trigger wurden per COPY-PASTE AUS DEM CHAT in den Supabase-SQL-Editor
-- deployed. Genau dabei entstehen unsichtbare Unicode-Leerzeichen in der
-- Einrueckung. Pro eingerueckter Zeile 2 Zeichen Differenz — fuer die
-- beobachteten 86 Zeichen braucht es ~43 solcher Zeilen. Fuer einen
-- 1700-Zeichen-plpgsql-Body voellig normal.
--
-- Die Repo-Datei security_triggers_LIVE_v3911.sql enthaelt NACHWEISLICH kein
-- Unicode-Whitespace (beide Normalisierungen liefern dort identische Werte).
-- Der Verdacht richtet sich also ausschliesslich auf den LIVE-Body.
--
-- ── FOLGE FUER DIE BISHERIGE AUSSAGE ──────────────────────────────
-- "Alle fuenf Trigger weichen ab" stammt aus der FEHLERHAFTEN Messung und ist
-- damit UNBEWIESEN. Belegt ist einzig guard_urlaub_edit (1746 gegen 953 Repo) —
-- und selbst dort ist der exakte Delta-Wert erst nach dieser Messung sicher.
-- ═══════════════════════════════════════════════════════════════════

-- ══════════════════════════════════════════════════════════════════
-- ABFRAGE 1 — DIE ENTSCHEIDENDE: Steckt Unicode-Whitespace im Body?
--
-- Das beantwortet die Anomalie (1746 vs. 1832) ENDGUELTIG:
--   nbsp_und_co > 0  -> die Differenz ist ein MESSARTEFAKT. Der Trigger hat
--                       sich nie geaendert. Niemand hat etwas deployed.
--   nbsp_und_co = 0  -> die Differenz ist ECHT. Dann hat jemand den Trigger
--                       waehrend der Session veraendert und wir muessen wissen,
--                       wer und womit.
-- ══════════════════════════════════════════════════════════════════
SELECT p.proname::text                                    AS funktion,
       length(p.prosrc)                                   AS roh_zeichen,
       -- Anzahl NICHT-ASCII-Whitespace-Zeichen im Body (U+00A0 geschuetztes
       -- Leerzeichen, U+2007, U+202F, U+2009, U+200B Zero-Width-Space):
       length(p.prosrc)
         - length(translate(p.prosrc,
                            chr(160)||chr(8199)||chr(8239)||chr(8201)||chr(8203),
                            ''))                          AS nbsp_und_co
  FROM pg_proc p
 WHERE p.pronamespace = 'public'::regnamespace
   AND p.proname IN ('guard_urlaub_edit','guard_kontingent',
                     'guard_users_privilege','guard_admin_only','guard_projects')
 ORDER BY 3 DESC, 1;

-- ══════════════════════════════════════════════════════════════════
-- ABFRAGE 2 — Beide Normalisierungen nebeneinander, plus Kontrollwert.
--
-- A = Postgres-nativ  (\s = nur ASCII)          <- was v1 auf der live-Seite tat
-- B = Unicode-tolerant (U+00A0 & Co. vorher zu ' ' uebersetzt)  <- was Python tut
--
-- ── EINGEBAUTER KONTROLLWERT — OHNE IHN IST DER LAUF UNGUELTIG ────
-- Fuer guard_urlaub_edit MUSS EINE der beiden Varianten exakt
--     len = 1746   und   md5 = 284dc6f19d45f4a8804ddb69e74e8ef6
-- liefern. Das ist der unabhaengig gemessene Ist-Stand von ~22:05.
--   Trifft Variante B  -> B ist die kanonische Normalform. Die Repo-Hashes
--                         (unten) sind mit genau dieser Semantik gerechnet und
--                         damit direkt vergleichbar.
--   Trifft Variante A  -> dann war die 22:05-Messung ASCII-nativ und die
--                         Unicode-Erklaerung faellt; Anomalie neu aufrollen.
--   Trifft KEINE       -> LAUF UNGUELTIG. Nicht weiterrechnen, nicht
--                         interpretieren, melden. Dann stimmt eine der beiden
--                         Grundannahmen nicht und jede Schlussfolgerung darauf
--                         waere geraten.
-- Genau dieser Mechanismus hat den v1-Fehler gefangen: der Kontrollwert wurde
-- verfehlt (879 statt ~793), und DARAN ist der Messfehler aufgefallen — nicht
-- am Ergebnis, das plausibel aussah.
-- ══════════════════════════════════════════════════════════════════
WITH repo(fn, repo_len, repo_md5) AS (
  -- Aus sql/security_triggers_LIVE_v3911.sql berechnet. Die Repo-Datei enthaelt
  -- kein Unicode-Whitespace, darum sind diese Werte fuer BEIDE Varianten gueltig.
  VALUES
    ('guard_urlaub_edit',      953, '46dd96ad12438636b7929b78a49a66c8'),
    ('guard_kontingent',       387, '26bb760bc19d932174ef55b038c14b85'),
    ('guard_users_privilege',  680, 'd3f029b094ccdb68e569d337f2e4c5a0'),
    ('guard_admin_only',       300, '88c95f06d048b2966d51879fe7b7a37b'),
    ('guard_projects',         328, 'ba09f470a8d334e4d186c6320d492754')
),
live AS (
  SELECT p.proname::text AS fn,
         -- Variante A: Postgres-nativ, \s = nur ASCII-Whitespace
         btrim(regexp_replace(p.prosrc, '\s+', ' ', 'g'))                    AS norm_a,
         -- Variante B: Unicode-Leerzeichen zuerst zu ' ' uebersetzen, dann kollabieren
         btrim(regexp_replace(
                 translate(p.prosrc,
                           chr(160)||chr(8199)||chr(8239)||chr(8201)||chr(8203),
                           '     '),
                 '\s+', ' ', 'g'))                                           AS norm_b
    FROM pg_proc p
   WHERE p.pronamespace = 'public'::regnamespace
     AND p.proname IN ('guard_urlaub_edit','guard_kontingent',
                       'guard_users_privilege','guard_admin_only','guard_projects')
)
SELECT r.fn,
       length(l.norm_a) AS a_len, md5(l.norm_a) AS a_md5,
       length(l.norm_b) AS b_len, md5(l.norm_b) AS b_md5,
       r.repo_len,
       CASE
         WHEN l.fn IS NULL                THEN '❓ nicht in der DB'
         WHEN md5(l.norm_b) = r.repo_md5  THEN '✅ identisch (Variante B)'
         WHEN md5(l.norm_a) = r.repo_md5  THEN '✅ identisch (Variante A)'
         ELSE                                  '⛔ ABWEICHUNG — Repo ist KEINE Replace-Basis'
       END AS befund,
       CASE
         WHEN r.fn <> 'guard_urlaub_edit' THEN ''
         WHEN md5(l.norm_b) = '284dc6f19d45f4a8804ddb69e74e8ef6' AND length(l.norm_b) = 1746
           THEN '★ KONTROLLE OK — Variante B ist kanonisch'
         WHEN md5(l.norm_a) = '284dc6f19d45f4a8804ddb69e74e8ef6' AND length(l.norm_a) = 1746
           THEN '★ KONTROLLE OK — Variante A ist kanonisch'
         ELSE '⛔⛔ KONTROLLWERT VERFEHLT — DIESER LAUF IST UNGUELTIG, NICHT INTERPRETIEREN'
       END AS kontrolle
  FROM repo r
  LEFT JOIN live l ON l.fn = r.fn
 ORDER BY (r.fn <> 'guard_urlaub_edit'), r.fn;

-- ══════════════════════════════════════════════════════════════════
-- FUER JEDEN BESTAETIGTEN ABWEICHLER: Ist-Stand sichern, BEVOR ihn jemand anfasst
--   select pg_get_functiondef(oid) from pg_proc
--    where pronamespace='public'::regnamespace and proname='<funktion>';
-- Ergebnis 1:1 ablegen unter docs/wip/<funktion>_LIVE_<datum>.sql.
--
-- ERST DANN darf ein CREATE OR REPLACE darauf aufbauen — siehe die absolute
-- Regel in CLAUDE.md.
-- ══════════════════════════════════════════════════════════════════
