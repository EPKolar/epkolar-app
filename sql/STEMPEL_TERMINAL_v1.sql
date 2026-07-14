-- ═══════════════════════════════════════════════════════════════════
-- STEMPEL_TERMINAL_v1.sql — eigene Kiosk-Rolle fuer die Stempeluhr (App v3.9.638+)
-- IDEMPOTENT. NICHT automatisch ausgefuehrt — HUMAN-RUN-GATE.
-- Ausfuehren im Supabase SQL-Editor (Projekt jiggujpruejkaomgxarp).
--
-- Zweck: StempelTafel (?screen=stempel) laeuft aktuell NUR als eingeloggter
-- Admin (App-Gate curUser.role==='admin', index.html ~Z.7376). Das Terminal
-- steht am Werkstor/Eingang und darf kein Admin-Login tragen. Diese Datei
-- legt das DB-seitige Fundament fuer eine eigene Rolle 'stempel_terminal'
-- an — analog zum bestehenden Lager-Kiosk (lager_display, siehe
-- KIOSK_PII_RPCS_stage.sql / KIOSK_PII_LOCKDOWN_stage.sql).
--
-- Rollen-Erkennung wie bei lager_display: NICHT ueber public.users.role,
-- sondern ueber ((auth.jwt() -> 'app_metadata') ->> 'role'). Kiosk-Accounts
-- sind Geraete-Logins, keine Mitarbeiter-Datensaetze in public.users.
--
-- Prinzip "nur die Felder, die die Tafel liest": RLS ist ZEILEN-, keine
-- SPALTEN-Beschraenkung. Fuer workers (enthaelt mehr als die Tafel braucht)
-- wird darum — 1:1 das Muster von kiosk_field_workers() (lager_display) —
-- eine SECURITY-DEFINER-RPC mit minimaler Spaltenliste verwendet statt
-- einer rohen Tabellen-Policy. stempel_log hat dagegen keine ueber die
-- Tafel hinausgehenden PII-Spalten, dort genuegt eine direkte Policy.
--
-- Verifiziert gegen index.html StempelTafel (Funktion ab Z.5699):
--   - Z.5746: _sbGet('workers','select=id,name,role,nfc_uid&order=name.asc')
--   - Z.5794/5803: _sbGet('stempel_log', worker_id=eq...&ts=gte...) und
--                  worker_id=eq...&order=ts.desc&limit=1  (Richtungs-Check,
--                  ueber BELIEBIGE Worker-IDs — das Terminal ist an keinen
--                  einzelnen Mitarbeiter gebunden, "eigene Zeilen" heisst
--                  hier: Zeilen der EIGENEN Domaene stempel_log, nicht
--                  Zeilen-Owner=Terminal. Ohne breite SELECT auf stempel_log
--                  kann die Tafel Kommen/Gehen nicht bestimmen.)
--   - Z.5809: SQ.push(...POST /api/stempel-log...) → INSERT stempel_log
--   - Z.5749/_stLoadPauseRules (index.html ~Z.2066): SELECT system_config
--                  key='stempel_pause_rules'. OPTIONAL — bei fehlendem
--                  Zugriff faellt der Client auf STEMPEL_PAUSE_FALLBACK
--                  zurueck (kein Crash, siehe try/catch dort).
--
-- KEIN UPDATE, KEIN DELETE auf stempel_log fuer diese Rolle — die
-- Stempeluhr ist append-only. Es werden bewusst KEINE Update/Delete-
-- Policies angelegt; RLS ist Default-Deny, das allein reicht.
--
-- system_config ist seit migrate_system_config_hardening_v3108.sql per
-- Policy system_config_admin_all auf is_admin() eingeschraenkt (FOR ALL).
-- Diese Datei fuegt NUR eine zusaetzliche, auf genau EINEN Key verengte
-- SELECT-Policy fuer stempel_terminal hinzu (kein Zugriff auf andere
-- system_config-Keys).
--
-- ── ERWEITERUNG 2026-07-14 (Abschnitte 4+5): Urlaub/ZA-Antrag am Terminal ──
-- Mitarbeiter sollen am Wandpanel per NFC-Scan auch einen Urlaubs-/
-- Zeitausgleichs-Antrag einreichen koennen (Sebastian-Entscheid: EIN
-- Terminal-Login, KEINE eigenen User pro Mitarbeiter — Identifikation
-- ausschliesslich per workers.nfc_uid, das Terminal schreibt den Antrag
-- FUER den gescannten Mitarbeiter). Abschnitt 4 legt dafuer die INSERT-
-- Policy auf absences an. Abschnitt 5 behandelt den dabei entdeckten
-- Trigger-Konflikt mit guard_urlaub_edit() (siehe dort).
-- ═══════════════════════════════════════════════════════════════════

-- ── 1) workers: minimale Kiosk-Sicht per RPC (KEINE rohe Tabellen-Policy) ──
-- Analog kiosk_field_workers() (lager_display). Liefert exakt die 4 Felder,
-- die StempelTafel liest: id, name, role, nfc_uid. Kein Telefon, keine
-- Adresse, kein Lohn/Sonstiges aus workers.
CREATE OR REPLACE FUNCTION public.stempel_terminal_workers()
RETURNS TABLE(id text, name text, role text, nfc_uid text)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path TO 'public', 'pg_temp'
AS $function$
BEGIN
  IF NOT ( ((auth.jwt() -> 'app_metadata') ->> 'role') = 'stempel_terminal'
           OR public.is_staff() ) THEN
    RAISE EXCEPTION 'not authorized' USING errcode = '42501';
  END IF;
  RETURN QUERY
    SELECT w.id, w.name, w.role, w.nfc_uid
    FROM public.workers w
    ORDER BY w.name ASC;
END
$function$;

REVOKE ALL ON FUNCTION public.stempel_terminal_workers() FROM public, anon;
GRANT EXECUTE ON FUNCTION public.stempel_terminal_workers() TO authenticated;

-- ── 2) stempel_log: SELECT (Richtungsbestimmung) + INSERT (Buchen) ────────
-- Tabelle/RLS existieren bereits aus STEMPEL_v1.sql (is_staff()-Policies).
-- Hier NUR die zusaetzlichen Policies fuer die neue Terminal-Rolle.
-- Breite SELECT ist noetig: die Tafel muss fuer JEDEN gescannten Mitarbeiter
-- dessen Tages-/letzte Zeile lesen koennen, nicht nur "eine eigene" Zeile.
DROP POLICY IF EXISTS stempel_log_select_terminal ON public.stempel_log;
CREATE POLICY stempel_log_select_terminal ON public.stempel_log
  AS PERMISSIVE FOR SELECT TO authenticated
  USING ( ((auth.jwt() -> 'app_metadata') ->> 'role') = 'stempel_terminal' );

DROP POLICY IF EXISTS stempel_log_insert_terminal ON public.stempel_log;
CREATE POLICY stempel_log_insert_terminal ON public.stempel_log
  AS PERMISSIVE FOR INSERT TO authenticated
  WITH CHECK ( ((auth.jwt() -> 'app_metadata') ->> 'role') = 'stempel_terminal' );

-- Bewusst KEINE UPDATE-/DELETE-Policy fuer stempel_terminal — append-only.

-- ── 3) system_config: nur der eine Key 'stempel_pause_rules', nur lesend ──
-- Verengt auf genau diesen Key, damit die Terminal-Rolle keine anderen
-- system_config-Werte (z.B. kv_rules, ticket_templates) sehen kann.
DROP POLICY IF EXISTS system_config_select_stempel_terminal ON public.system_config;
CREATE POLICY system_config_select_stempel_terminal ON public.system_config
  AS PERMISSIVE FOR SELECT TO authenticated
  USING (
    ((auth.jwt() -> 'app_metadata') ->> 'role') = 'stempel_terminal'
    AND key = 'stempel_pause_rules'
  );

-- ── 4) absences: NUR INSERT (Urlaub-/ZA-Antrag am Terminal) ───────────────
-- Die Tafel bietet neben Kommen/Gehen neu eine Aktion "Urlaub/Zeitausgleich
-- beantragen". Nach Chip-Scan + Zeitraum-Auswahl schreibt der Client pro
-- Werktag (Sa/So/Feiertage werden client-seitig uebersprungen) eine Zeile
-- nach absences — im Namen des gescannten Mitarbeiters (NEW.worker_id =
-- dessen workers.id), nicht des Terminal-Accounts selbst.
--
-- WITH CHECK erzwingt woertlich status = 'beantragt' — NICHT 'ausstehend'.
-- 'ausstehend' ist nur ein CLIENT-seitiger Anzeige-/Map-Wert; der DB-Trigger
-- guard_urlaub_edit() (sql/security_triggers_LIVE_v3911.sql) prueft hart
-- auf COALESCE(NEW.status,'beantragt') = 'beantragt'. Eine Policy auf
-- 'ausstehend' wuerde JEDEN Terminal-Antrag am Trigger scheitern lassen
-- (RAISE EXCEPTION), ohne dass die RLS-Policy selbst je den Fehler zeigt —
-- schwer zu debuggendes Symptom, deshalb hier explizit festgehalten.
--
-- Bewusst KEIN UPDATE, KEIN DELETE fuer stempel_terminal auf absences — das
-- Terminal reicht Antraege nur EIN, es kann nichts genehmigen/aendern/
-- loeschen. Genehmigung bleibt vollstaendig Buero-Aufgabe (admin/urlaub_edit
-- ueber die bestehenden Policies aus migrate_urlaub_edit_rls_v3111.sql).
--
-- Bewusst KEIN SELECT fuer stempel_terminal auf absences: die Tafel braucht
-- keine Lesesicht auf bestehende Antraege, um einen neuen anzulegen. Ein
-- Doppel-Antrag fuer denselben Mitarbeiter+Tag wird ueber den PRIMARY KEY
-- abgefangen (id-Format "Name_YYYY-MM-DD" bzw. "workerId_YYYY-MM-DD", siehe
-- migrate_absences_fix_v3998.sql) — ein zweiter INSERT mit identischer id
-- schlaegt am PK-Unique-Constraint fehl, kein SELECT noetig, um das vorher
-- zu pruefen. Sollte die App spaeter doch eine Lesesicht brauchen (z.B. um
-- "bereits beantragt" anzuzeigen), muesste eine SELECT-Policy so eng wie
-- moeglich sein (z.B. nur heutiges Datum, nur status), NICHT breit wie bei
-- stempel_log.
--
-- KEIN Zugriff (keinerlei Policy, auch nicht SELECT) auf urlaubskontingent
-- fuer stempel_terminal — Resturlaub/Kontingent darf am Wandpanel bewusst
-- NICHT sichtbar sein (fremde Augen an einem oeffentlich zugaenglichen
-- Geraet). urlaubskontingent hat bereits eigene RLS
-- (migrate_urlaub_edit_rls_v3111.sql); da dort keine stempel_terminal-
-- Policy existiert (weder hier noch anderswo), bleibt die Tabelle fuer diese
-- Rolle vollstaendig gesperrt (RLS ist Default-Deny).
DROP POLICY IF EXISTS absences_insert_terminal ON public.absences;
CREATE POLICY absences_insert_terminal ON public.absences
  AS PERMISSIVE FOR INSERT TO authenticated
  WITH CHECK (
    ((auth.jwt() -> 'app_metadata') ->> 'role') = 'stempel_terminal'
    AND status = 'beantragt'
  );

-- ── 5) TRIGGER-KONFLIKT: guard_urlaub_edit() muss angepasst werden ────────
-- GEPRUEFT gegen sql/security_triggers_LIVE_v3911.sql (Live-Funktion,
-- rekonstruiert, s. dortiger Header): guard_urlaub_edit() erlaubt
-- Nicht-Admins/Nicht-urlaub_edit NUR den Self-Service-Zweig
--   TG_OP='INSERT' AND NEW.worker_id = me.monteur_id AND status='beantragt'
-- wobei "me" per
--   SELECT role, perms_override, monteur_id FROM public.users
--   WHERE auth_user_id::text = (auth.jwt() ->> 'sub')
-- ermittelt wird.
--
-- Der Terminal-Account ist — analog stempel_terminal_workers() und
-- lager_display — ein reiner Geraete-Login OHNE Zeile in public.users
-- (Rollen-Erkennung laeuft ueber (auth.jwt()->'app_metadata'->>'role'), nicht
-- ueber public.users.role). Damit liefert obiges SELECT fuer den Terminal-
-- Account KEINE Zeile: me.role und me.monteur_id sind NULL.
--   - me.role = 'admin' → NULL = 'admin' → false (kein Admin-Bypass)
--   - (me.perms_override -> 'urlaub_edit')::text = 'true' → NULL, false
--   - NEW.worker_id = me.monteur_id → NEW.worker_id = NULL → NULL (nie true,
--     auch nicht wenn NEW.worker_id zufaellig NULL waere)
-- → der Self-Service-Zweig greift fuer stempel_terminal NIE, jeder Antrag
-- laeuft in den finalen RAISE EXCEPTION. JA, der Trigger MUSS angepasst
-- werden — ohne Anpassung scheitert JEDER Terminal-Urlaubsantrag am
-- Trigger, unabhaengig von der absences-Policy aus Abschnitt 4.
--
-- FIX: neuer Zweig ganz oben (nach dem service_role-Bypass, vor dem
-- public.users-Lookup), der stempel_terminal ausschliesslich fuer
-- TG_OP='INSERT' mit status='beantragt' durchlaesst — fuer BELIEBIGE
-- worker_id, weil das Terminal per Definition fuer FREMDE Mitarbeiter
-- schreibt (das ist der ganze Sinn des Features: der Chip-Inhaber hat
-- keinen eigenen monteur_id-Login). UPDATE/DELETE bleiben fuer
-- stempel_terminal explizit gesperrt (RAISE EXCEPTION) — Defense-in-Depth
-- zusaetzlich zur fehlenden RLS-Policy aus Abschnitt 4 (kein UPDATE/DELETE
-- dort angelegt).
--
-- IDEMPOTENT (CREATE OR REPLACE). Aenderung ist minimal-invasiv: der
-- bestehende Admin-/urlaub_edit-/Monteur-Self-Service-Pfad ist Zeichen fuer
-- Zeichen unveraendert, nur der neue stempel_terminal-Zweig kommt davor.
CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE
  me record;
  sub text := auth.jwt() ->> 'sub';
  jwt_role text := (auth.jwt() -> 'app_metadata') ->> 'role';
BEGIN
  IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass

  -- Stempel-Terminal (Kiosk-Login, KEINE Zeile in public.users, KEIN
  -- monteur_id): darf per NFC-Scan fuer JEDE worker_id einen neuen Antrag
  -- im Status 'beantragt' anlegen. Kein Update/Delete.
  IF jwt_role = 'stempel_terminal' THEN
    IF TG_OP = 'INSERT' AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN
      RETURN NEW;
    END IF;
    RAISE EXCEPTION 'urlaub: stempel_terminal darf nur INSERT mit status=beantragt';
  END IF;

  SELECT role, perms_override, monteur_id INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
  IF me.role = 'admin' OR (me.perms_override -> 'urlaub_edit')::text = 'true' THEN
    RETURN COALESCE(NEW, OLD);                            -- Verwalter: voll
  END IF;
  -- Monteur-Self-Service: nur eigene, nur Status 'beantragt', kein Selbst-Genehmigen
  IF TG_OP = 'INSERT' THEN
    IF NEW.worker_id = me.monteur_id AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
  ELSIF TG_OP = 'UPDATE' THEN
    IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' AND NEW.status = 'beantragt' THEN RETURN NEW; END IF;
  ELSIF TG_OP = 'DELETE' THEN
    IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
  END IF;
  RAISE EXCEPTION 'urlaub: keine Berechtigung (nur eigene Anträge im Status beantragt)';
END $$;
-- Trigger-Bindung trg_guard_urlaub_absences bleibt unveraendert (CREATE OR
-- REPLACE FUNCTION aendert nur den Funktionsbody, nicht die Trigger-
-- Registrierung aus security_triggers_LIVE_v3911.sql — kein erneutes
-- CREATE TRIGGER noetig/gewuenscht).

-- ═══════════════════════════════════════════════════════════════════
-- SEBASTIAN: User anlegen (Auth ist tabu fuer Claude Code — kein
-- auth.users-INSERT in dieser Datei). Vorgehen analog zum bestehenden
-- Lager-Kiosk-User (lager/lager_display):
--
--   1. Supabase Dashboard → Authentication → Users → "Add user"
--      (z.B. E-Mail stempel@ep-kolar.local oder aehnlich, Passwort setzen).
--   2. Am neuen User "Edit" → raw_app_meta_data (JSON) ergaenzen:
--        { "role": "stempel_terminal" }
--      (Analog dem bestehenden lager_display-User — dort greift exakt
--      dasselbe Claim-Feld in den RESTRICTIVE- und RPC-Policies.)
--   3. Client-seitig fehlt noch das App-Gate: index.html ~Z.7376 laesst
--      ?screen=stempel aktuell NUR fuer curUser.role==='admin' zu. Damit
--      der neue Terminal-User die Tafel ueberhaupt sehen kann, muss diese
--      Bedingung um 'stempel_terminal' erweitert werden UND StempelTafel
--      muss auf stempel_terminal_workers() statt des rohen
--      _sbGet('workers', 'select=id,name,role,nfc_uid...') umgestellt
--      werden (sonst laeuft der Terminal-User in die fehlende workers-
--      Policy). DAS ist eine App-Code-Aenderung, NICHT Teil dieser
--      SQL-Datei — separater Schritt, danach Client-Deploy. Der neue
--      Urlaub/ZA-Antrags-Flow (Abschnitt 4+5 oben) braucht ebenso noch
--      client-seitige UI (Aktion "Urlaub/Zeitausgleich beantragen" in
--      StempelTafel, POST auf absences mit status='beantragt') — DB-seitig
--      ist das Fundament nach dieser Datei fertig, die UI fehlt noch.
--   4. Bis Schritt 3 umgesetzt ist, bleibt der Kiosk unveraendert per
--      Admin-Login betrieben. Diese Datei ist rein additiv und stoert den
--      bestehenden Admin-Betrieb NICHT (is_staff()-Policies aus
--      STEMPEL_v1.sql bleiben unangetastet).
-- ═══════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════
-- ROLLBACK (manuell, NICHT Teil des Vorwaerts-Laufs):
--   DROP POLICY IF EXISTS system_config_select_stempel_terminal ON public.system_config;
--   DROP POLICY IF EXISTS stempel_log_insert_terminal ON public.stempel_log;
--   DROP POLICY IF EXISTS stempel_log_select_terminal ON public.stempel_log;
--   DROP POLICY IF EXISTS absences_insert_terminal ON public.absences;
--   REVOKE EXECUTE ON FUNCTION public.stempel_terminal_workers() FROM authenticated;
--   DROP FUNCTION IF EXISTS public.stempel_terminal_workers();
--   -- Den Auth-User selbst loescht/deaktiviert Sebastian im Dashboard.
--
--   -- guard_urlaub_edit() auf den Vor-Erweiterung-Stand zuruecksetzen
--   -- (identisch zur Live-Version aus security_triggers_LIVE_v3911.sql,
--   -- OHNE stempel_terminal-Zweig):
--   CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
--   RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
--   DECLARE me record; sub text := auth.jwt() ->> 'sub';
--   BEGIN
--     IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
--     SELECT role, perms_override, monteur_id INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
--     IF me.role = 'admin' OR (me.perms_override -> 'urlaub_edit')::text = 'true' THEN
--       RETURN COALESCE(NEW, OLD);
--     END IF;
--     IF TG_OP = 'INSERT' THEN
--       IF NEW.worker_id = me.monteur_id AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
--     ELSIF TG_OP = 'UPDATE' THEN
--       IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' AND NEW.status = 'beantragt' THEN RETURN NEW; END IF;
--     ELSIF TG_OP = 'DELETE' THEN
--       IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
--     END IF;
--     RAISE EXCEPTION 'urlaub: keine Berechtigung (nur eigene Anträge im Status beantragt)';
--   END $$;
--   -- ACHTUNG: dieser Rollback macht auch den Rollback aus Abschnitt 4
--   -- (DROP POLICY absences_insert_terminal) NOTWENDIG BEGLEITEND — sonst
--   -- kann die RLS-Policy Antraege durchlassen, die der Trigger danach
--   -- wieder hart blockt (verwirrendes Fehlerbild). Beide immer zusammen
--   -- zurueckrollen.
-- ═══════════════════════════════════════════════════════════════════

-- ── Verifikation nach dem Run (auskommentiert, read-only) ────────────
-- select proname, pg_get_function_result(oid) from pg_proc
--   where pronamespace='public'::regnamespace and proname='stempel_terminal_workers';
--
-- select tablename, policyname, cmd, permissive, roles from pg_policies
--   where schemaname='public'
--     and tablename in ('stempel_log','system_config','absences')
--     and policyname like '%terminal%'
--   order by tablename, policyname;
-- -- erwartet: stempel_log_select_terminal (SELECT), stempel_log_insert_terminal (INSERT),
-- --           system_config_select_stempel_terminal (SELECT), absences_insert_terminal (INSERT)
-- --           — alle PERMISSIVE. KEINE Zeile fuer urlaubskontingent erwartet.
--
-- select proname, pg_get_functiondef(oid) from pg_proc
--   where pronamespace='public'::regnamespace and proname='guard_urlaub_edit';
-- -- Body muss den neuen "IF jwt_role = 'stempel_terminal' THEN ..."-Zweig
-- -- direkt nach dem service_role-Bypass enthalten.
--
-- -- Manueller Rollen-Test (nach Schritt 2 der Sebastian-Anleitung, als
-- -- stempel_terminal-User eingeloggt):
-- --   select * from public.stempel_terminal_workers();          -- 4 Spalten, alle Mitarbeiter
-- --   select * from public.stempel_log limit 5;                 -- lesbar
-- --   insert into public.stempel_log (worker_id,direction,device)
-- --     values ('test','kommen','kiosk');                       -- erlaubt
-- --   update public.stempel_log set direction='gehen' where worker_id='test'; -- MUSS scheitern (RLS)
-- --   delete from public.stempel_log where worker_id='test';    -- MUSS scheitern (RLS)
-- --   insert into public.absences (id,worker_id,from_date,to_date,type,status)
-- --     values ('test_2099-01-01','test','2099-01-01','2099-01-01','urlaub','beantragt');
-- --     -- MUSS gelingen (RLS-Policy UND Trigger lassen durch)
-- --   insert into public.absences (id,worker_id,from_date,to_date,type,status)
-- --     values ('test_2099-01-02','test','2099-01-02','2099-01-02','urlaub','genehmigt');
-- --     -- MUSS scheitern (status != 'beantragt' -> RLS WITH CHECK greift zuerst)
-- --   update public.absences set status='genehmigt' where id='test_2099-01-01'; -- MUSS scheitern (kein UPDATE fuer stempel_terminal)
-- --   delete from public.absences where id='test_2099-01-01';                  -- MUSS scheitern (kein DELETE fuer stempel_terminal)
-- --   select * from public.urlaubskontingent limit 1;                          -- MUSS scheitern (keine Policy fuer stempel_terminal)
-- ═══════════════════════════════════════════════════════════════════
