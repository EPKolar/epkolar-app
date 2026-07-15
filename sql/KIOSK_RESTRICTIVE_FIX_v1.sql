-- ═══════════════════════════════════════════════════════════════════
-- KIOSK_RESTRICTIVE_FIX_v1.sql
-- Reparatur einer WIRKUNGSLOSEN ZWEITSICHERUNG. IDEMPOTENT.
-- NICHT automatisch ausgefuehrt — HUMAN-RUN-GATE.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- ── WORUM ES GEHT ─────────────────────────────────────────────────
-- Mehrere Tabellen tragen eine RESTRICTIVE-Policy, die den Lager-Kiosk
-- (lager_display) zusaetzlich hart aussperren soll — eine bewusste
-- Zweitsicherung, weil der Kiosk oeffentlich an der Wand haengt.
--
-- Diese Sperren pruefen die Rolle ueber ((auth.jwt()->'app_metadata')->>'role').
-- Das ist die FALSCHE Rollenquelle. Der lager_display-User traegt seine Rolle
-- in public.users.role (dort liest sie auth_role(), und dort liest sie auch der
-- Client als curUser.role — 'app_metadata' kommt in index.html kein einziges Mal
-- vor). Der Claim ist an diesen Accounts nicht gesetzt, der Vergleich lief also
-- gegen NULL und die Sperre hat NIE gegriffen.
--
-- ── KEIN AKTIVES LECK ─────────────────────────────────────────────
-- Verifiziert (Sebastian/Chat-Claude): fz_fahrten, fz_positions und geo_cache
-- haben als PERMISSIVE-Policy nur is_staff(). lager_display ist NICHT staff.
-- RLS ist Default-Deny — ohne zutreffende PERMISSIVE-Policy kommt der Kiosk
-- ohnehin nicht an die Zeilen. Die RESTRICTIVE-Sperre war der Guertel zum
-- Hosentraeger; kaputt war nur der Guertel.
--
-- Trotzdem reparieren: Eine Sicherung, die man fuer wirksam haelt und die es
-- nicht ist, ist gefaehrlicher als gar keine — sie verleitet dazu, die
-- PERMISSIVE-Seite spaeter zu lockern ("die RESTRICTIVE faengt das ja ab").
--
-- ── ZUSAETZLICH: stempel_terminal ─────────────────────────────────
-- Das neue Stempel-Terminal (sql/STEMPEL_TERMINAL_v2.sql) haengt genauso
-- oeffentlich am Werkstor wie der Lager-Kiosk. Es hat an GPS-Daten
-- (Fahrten, Positionen, Geocoding) nichts verloren. Es wird darum in
-- dieselbe Sperre aufgenommen — bevor jemand auf die Idee kommt, dem
-- Terminal "kurz" eine Staff-Policy zu geben.
-- ═══════════════════════════════════════════════════════════════════

-- Ein Helper, damit die Bedingung an allen vier Stellen identisch ist und
-- eine kuenftige Kiosk-Rolle nur HIER eingetragen werden muss.
CREATE OR REPLACE FUNCTION public.is_kiosk_role()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT public.auth_role() IN ('lager_display', 'stempel_terminal');
$$;

REVOKE ALL ON FUNCTION public.is_kiosk_role() FROM public;
GRANT EXECUTE ON FUNCTION public.is_kiosk_role() TO authenticated, anon;

-- ── 1) fz_fahrten (war: app_metadata, nur lager_display) ─────────────
DROP POLICY IF EXISTS fz_fahrten_no_lager_display ON public.fz_fahrten;
DROP POLICY IF EXISTS fz_fahrten_no_kiosk ON public.fz_fahrten;
CREATE POLICY fz_fahrten_no_kiosk ON public.fz_fahrten AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ── 2) fz_positions (GPS-Rohpunkte) ──────────────────────────────────
DROP POLICY IF EXISTS fz_positions_no_lager_display ON public.fz_positions;
DROP POLICY IF EXISTS fz_positions_no_kiosk ON public.fz_positions;
CREATE POLICY fz_positions_no_kiosk ON public.fz_positions AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ── 3) geo_cache (Reverse-Geocoding — enthaelt Adressen der Fahrten) ─
DROP POLICY IF EXISTS geo_cache_no_lager_display ON public.geo_cache;
DROP POLICY IF EXISTS geo_cache_no_kiosk ON public.geo_cache;
CREATE POLICY geo_cache_no_kiosk ON public.geo_cache AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ── 4) kunden (Kundendaten — Grep-Fund, gleiche kaputte Quelle) ──────
-- sql/KUNDEN_TABLE_v3.9.586.sql Z.37 nutzt denselben app_metadata-Vergleich.
DROP POLICY IF EXISTS kunden_no_lager_display ON public.kunden;
DROP POLICY IF EXISTS kunden_no_kiosk ON public.kunden;
CREATE POLICY kunden_no_kiosk ON public.kunden AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ═══════════════════════════════════════════════════════════════════
-- ── ERWEITERUNG v3.9.699 (Bug-Hunt Befund 1) ─────────────────────────
-- Die drei folgenden Tabellen tragen breite `authenticated`-SELECT-Policies
-- (USING(true), "App-Layer filtert") und lagen damit fuer JEDEN eingeloggten
-- Kiosk offen — inkl. time_entries = die gebuchten Arbeitsstunden der GANZEN
-- Belegschaft. KEINE Kiosk-Tafel (MonteurTafel, WochenplanTafel, StempelTafel)
-- rendert oder braucht diese drei. Darum harte RESTRICTIVE-Sperre fuer BEIDE
-- Kiosk-Rollen — der Guertel zum client-seitigen Hosentraeger (v3.9.699 laedt
-- sie fuer stempel_terminal schon nicht mehr, fuer lager_display time_entries+
-- forms ebenfalls nicht).
--
-- BEWUSST NICHT hier: fahrzeuge, projects, absences, arbeitsscheine. Die
-- Lager-Tafeln (lager_display) nutzen sie legitim (WochenplanTafel bekommt
-- fahrzeuge/abs, MonteurTafel arbeitsscheine). Fuer die schuetzt das
-- Client-Scoping im Bootstrap, nicht eine DB-Sperre — sonst braeche der
-- laufende Lager-Kiosk.
-- ═══════════════════════════════════════════════════════════════════

-- ── 5) time_entries (Arbeitsstunden ALLER Mitarbeiter — sensibelste Tabelle) ─
DROP POLICY IF EXISTS time_entries_no_kiosk ON public.time_entries;
CREATE POLICY time_entries_no_kiosk ON public.time_entries AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ── 6) forms (Formulare/Mängel) ──────────────────────────────────────
DROP POLICY IF EXISTS forms_no_kiosk ON public.forms;
CREATE POLICY forms_no_kiosk ON public.forms AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ── 7) bautagebuch ───────────────────────────────────────────────────
-- Falls die Tabelle existiert; sonst ignoriert Postgres den DROP und der
-- CREATE schlaegt fehl -> dann diesen Block auskommentiert lassen.
DROP POLICY IF EXISTS bautagebuch_no_kiosk ON public.bautagebuch;
CREATE POLICY bautagebuch_no_kiosk ON public.bautagebuch AS RESTRICTIVE
  FOR ALL USING ( NOT public.is_kiosk_role() );

-- ═══════════════════════════════════════════════════════════════════
-- VERIFIKATION (nach dem Lauf):
--
--   -- a) Alle vier RESTRICTIVE-Sperren da, und keine alte mehr:
--   select tablename, policyname, permissive, qual
--     from pg_policies
--    where schemaname='public'
--      and (policyname like '%no_kiosk%' or policyname like '%no_lager_display%')
--    order by tablename;
--   -- erwartet: 4x *_no_kiosk (PERMISSIVE = 'RESTRICTIVE'),
--   --           0x *_no_lager_display
--
--   -- b) Der Helper liefert fuer einen Staff-User false:
--   select public.auth_role(), public.is_kiosk_role();
--
--   -- c) Gegenprobe (als lager-User eingeloggt): muss 0 Zeilen liefern,
--   --    und zwar jetzt wegen der RESTRICTIVE-Sperre, nicht nur wegen
--   --    Default-Deny:
--   --      select count(*) from public.fz_positions;
--
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS fz_fahrten_no_kiosk   ON public.fz_fahrten;
--   DROP POLICY IF EXISTS fz_positions_no_kiosk ON public.fz_positions;
--   DROP POLICY IF EXISTS geo_cache_no_kiosk    ON public.geo_cache;
--   DROP POLICY IF EXISTS kunden_no_kiosk       ON public.kunden;
--   DROP FUNCTION IF EXISTS public.is_kiosk_role();
--   -- Danach stehen die Tabellen wieder auf Default-Deny + is_staff()-PERMISSIVE
--   -- (also weiterhin dicht) — nur ohne die Zweitsicherung.
-- ═══════════════════════════════════════════════════════════════════
