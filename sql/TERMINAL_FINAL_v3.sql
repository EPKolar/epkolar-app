-- ═══════════════════════════════════════════════════════════════════
-- TERMINAL_FINAL_v3.sql — das EINE Run-Paket fuer die Stempel-Terminal-Rolle.
-- IDEMPOTENT. Human-Run-Gate. Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Sebastian fuehrt DIESES Dokument EINMAL aus. Es hat zwei Abschnitte:
--   A) guard_urlaub_edit() — Replace auf dem ECHTEN Live-Body (docs/wip/
--      guard_urlaub_edit_LIVE_2026-07-14.sql) plus der minimal-invasive
--      stempel_terminal-Zweig.
--   B) Kiosk-RESTRICTIVE-Sperren (is_kiosk_role + 7 Tabellen) — der Inhalt
--      von KIOSK_RESTRICTIVE_FIX_v1.sql, hier gebuendelt.
--
-- Die RPC + Policies der Terminal-Rolle (STEMPEL_TERMINAL_v2.sql Abschnitte
-- 1-4) sind am 14.07. bereits gelaufen und werden hier NICHT wiederholt.
--
-- ── SELBST-NACHWEIS (vom Generator geprueft) ───────────────────────
-- Der Trigger-Body in Abschnitt A, MINUS des stempel_terminal-Zweigs,
-- ergibt normalisiert (prosrc, ASCII-\s kollabiert, getrimmt):
--   md5 = 284dc6f19d45f4a8804ddb69e74e8ef6   len = 1746
-- Das ist exakt der am 14.07. in der DB gemessene Live-Stand von
-- guard_urlaub_edit(). Der Replace fuegt also AUSSCHLIESSLICH den
-- Terminal-Zweig hinzu und loescht keine Live-Logik.
--
-- WICHTIG: v3911 (Repo-Rekonstruktion) war fuer ALLE FUENF guard_*-Trigger
-- unvollstaendig (kalibrierte Messung 15.07.: +793/+99/+69/+66/+19 Zeichen).
-- Nur guard_urlaub_edit wird hier angefasst — auf Basis des Live-Bodys, NICHT
-- der Rekonstruktion. Die anderen vier bleiben unberuehrt; ihre Live-Bodies
-- liegen als docs/wip/<name>_LIVE_2026-07-14.sql.
-- ═══════════════════════════════════════════════════════════════════

-- ═══ ABSCHNITT A: guard_urlaub_edit() = Live-Body + stempel_terminal-Zweig ═══
CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
DECLARE c_role text; c_perms text; c_override text; c_sub text; c_monteur text;
BEGIN
  c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
  IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass
  SELECT u.role, u.permissions, u.perms_override, u.monteur_id
    INTO c_role, c_perms, c_override, c_monteur
    FROM public.users u WHERE u.auth_user_id::text = c_sub;
  -- v3.9.703: Stempel-Terminal (Kiosk-Login, public.users-Zeile role='stempel_terminal', KEINE monteur_id).
  -- Darf per NFC-Scan fuer JEDE worker_id einen Antrag im Status 'beantragt' anlegen. NUR INSERT, kein
  -- UPDATE/DELETE, kein Selbst-Genehmigen. Steht NACH dem users-Lookup (braucht c_role) und VOR dem
  -- Voll-Zugriff-Check; kein bestehender Live-Zweig wird umgangen (das Terminal hat keine monteur_id und
  -- wuerde die Eigentuemer-Zweige unten ohnehin nie erfuellen).
  IF c_role = 'stempel_terminal' THEN
    IF TG_OP = 'INSERT' AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'stempel_terminal darf nur INSERT mit status=beantragt';
  END IF;
  -- v3.9.453: Voll-Zugriff (Genehmigen/Bearbeiten) = admin/projektleiter/buero (= canDo('abs_approve') im Frontend)
  -- ODER urlaub_edit-Perm via permissions ODER perms_override (Frontend gewaehrt es ueber perms_override).
  -- Vorher nur admin + permissions-Spalte -> buero/PL + perms_override-User (z.B. Schober) liefen in die Exception.
  IF c_role IN ('admin','projektleiter','buero')
     OR (c_perms    IS NOT NULL AND c_perms    LIKE '%"urlaub_edit"%')
     OR (c_override IS NOT NULL AND c_override LIKE '%"urlaub_edit":true%')
  THEN RETURN COALESCE(NEW, OLD); END IF;
  -- DELETE: only own + still beantragt
  IF TG_OP = 'DELETE' THEN
    IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
    RAISE EXCEPTION 'Nur eigene offene Antraege loeschbar';
  END IF;
  -- INSERT: only own, status must be beantragt
  IF TG_OP = 'INSERT' THEN
    IF NEW.worker_id = c_monteur AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'Nur eigene Antraege im Status beantragt anlegbar';
  END IF;
  -- UPDATE: only own, only while beantragt, may not self-approve
  IF TG_OP = 'UPDATE' THEN
    IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' AND NEW.status IN ('beantragt','storniert') THEN RETURN NEW; END IF;
    RAISE EXCEPTION 'Nur eigene offene Antraege aenderbar, kein Selbst-Genehmigen';
  END IF;
  RETURN COALESCE(NEW, OLD);
END; $function$


-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK ABSCHNITT A (manuell) — exakter Live-Body 1:1, stellt den Stand
-- vor diesem Paket wieder her. Zum Zuruecksetzen die folgenden Zeilen
-- ent-kommentieren und ausfuehren:
-- 
-- CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
--  RETURNS trigger
--  LANGUAGE plpgsql
--  SECURITY DEFINER
--  SET search_path TO 'public', 'pg_temp'
-- AS $function$
-- DECLARE c_role text; c_perms text; c_override text; c_sub text; c_monteur text;
-- BEGIN
--   c_sub := current_setting('request.jwt.claims', true)::json->>'sub';
--   IF c_sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass
--   SELECT u.role, u.permissions, u.perms_override, u.monteur_id
--     INTO c_role, c_perms, c_override, c_monteur
--     FROM public.users u WHERE u.auth_user_id::text = c_sub;
--   -- v3.9.453: Voll-Zugriff (Genehmigen/Bearbeiten) = admin/projektleiter/buero (= canDo('abs_approve') im Frontend)
--   -- ODER urlaub_edit-Perm via permissions ODER perms_override (Frontend gewaehrt es ueber perms_override).
--   -- Vorher nur admin + permissions-Spalte -> buero/PL + perms_override-User (z.B. Schober) liefen in die Exception.
--   IF c_role IN ('admin','projektleiter','buero')
--      OR (c_perms    IS NOT NULL AND c_perms    LIKE '%"urlaub_edit"%')
--      OR (c_override IS NOT NULL AND c_override LIKE '%"urlaub_edit":true%')
--   THEN RETURN COALESCE(NEW, OLD); END IF;
--   -- DELETE: only own + still beantragt
--   IF TG_OP = 'DELETE' THEN
--     IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
--     RAISE EXCEPTION 'Nur eigene offene Antraege loeschbar';
--   END IF;
--   -- INSERT: only own, status must be beantragt
--   IF TG_OP = 'INSERT' THEN
--     IF NEW.worker_id = c_monteur AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
--     RAISE EXCEPTION 'Nur eigene Antraege im Status beantragt anlegbar';
--   END IF;
--   -- UPDATE: only own, only while beantragt, may not self-approve
--   IF TG_OP = 'UPDATE' THEN
--     IF OLD.worker_id = c_monteur AND OLD.status = 'beantragt' AND NEW.status IN ('beantragt','storniert') THEN RETURN NEW; END IF;
--     RAISE EXCEPTION 'Nur eigene offene Antraege aenderbar, kein Selbst-Genehmigen';
--   END IF;
--   RETURN COALESCE(NEW, OLD);
-- END; $function$
-- ═══════════════════════════════════════════════════════════════════

-- ═══ ABSCHNITT B: Kiosk-RESTRICTIVE-Sperren (is_kiosk_role + 7 Tabellen) ═══
-- Deckungsgleich mit sql/KIOSK_RESTRICTIVE_FIX_v1.sql. Sperrt beide Kiosk-Rollen
-- (lager_display + stempel_terminal) von GPS/Kunden UND von time_entries/forms/
-- bautagebuch (kein Kiosk braucht sie). fahrzeuge/projects/absences bewusst NICHT
-- (die Lager-Tafeln nutzen sie; dort schuetzt das Client-Scoping).

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
-- SEBASTIAN: Terminal-User anlegen (auth.users ist tabu fuer Claude Code).
-- Die App-Benutzerverwaltung kann die Rolle NICHT vergeben (ihr Dropdown kommt
-- aus Object.keys(ROLES), und ROLES kennt weder lager_display noch
-- stempel_terminal) — der SQL-Weg unten ist der einzige.
--
--   1. Supabase Dashboard -> Authentication -> Users -> "Add user"
--      (z.B. stempel@ep-kolar.local, Passwort setzen). KEIN app_metadata noetig.
--   2. Die zugehoerige public.users-Zeile anlegen (DAS ist die Rollenquelle,
--      die auth_role() liest). auth_user_id = UUID aus Schritt 1:
--      -- INSERT INTO public.users (id, auth_user_id, username, name, role)
--      -- VALUES (gen_random_uuid(), '<AUTH-UUID>', 'stempel', 'Stempel-Terminal',
--      --         'stempel_terminal');
--      Spaltennamen vorher am bestehenden lager-User pruefen:
--      -- SELECT id, auth_user_id, username, name, role, monteur_id
--      --   FROM public.users WHERE role = 'lager_display';
--      Der Terminal-User bekommt bewusst KEINE monteur_id.
--   3. Verifizieren (als Terminal-User eingeloggt): SELECT public.auth_role();
--      -- muss 'stempel_terminal' liefern.
--   4. Client ist ab v3.9.695 fertig (Gate + RPC-Ladeweg + Antrag). Kein
--      weiterer App-Schritt noetig.
-- ═══════════════════════════════════════════════════════════════════
