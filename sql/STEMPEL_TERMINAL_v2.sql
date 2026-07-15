-- ═══════════════════════════════════════════════════════════════════
-- ⚠️ TEILWEISE ÜBERHOLT — Stand 15.07.2026:
--   • Abschnitte 1-4 (RPC stempel_terminal_workers + stempel_log/system_config/
--     absences-Policies) sind am 14.07. GELAUFEN. Nicht erneut nötig.
--   • Abschnitt 5 (guard_urlaub_edit-Replace) ist STILLGELEGT und wird ERSETZT
--     durch sql/TERMINAL_FINAL_v3.sql — dort auf dem ECHTEN Live-Body statt der
--     unvollständigen Rekonstruktion. NICHT den hier auskommentierten Abschnitt 5
--     scharf schalten.
-- Diese Datei bleibt als Historie/Doku der Abschnitte 1-4. Für den letzten Schritt:
--   → sql/TERMINAL_FINAL_v3.sql (das eine Run-Paket).
-- ═══════════════════════════════════════════════════════════════════
-- STEMPEL_TERMINAL_v2.sql — eigene Kiosk-Rolle fuer die Stempeluhr (App v3.9.638+)
--
-- v2 ERSETZT v1 VOLLSTAENDIG. v1 ist NIE gelaufen und wurde geloescht.
-- Der Unterschied ist nicht kosmetisch: v1 erkannte die Rolle ueber den
-- JWT-Claim app_metadata.role. Das war falsch. Der Client liest diesen Claim
-- NIRGENDS (das Wort 'app_metadata' kommt in index.html kein einziges Mal vor),
-- und auth_role() — der Helper, auf dem der Grossteil der RLS sitzt — liest
-- public.users.role. v1 haette also eine Rollenquelle geprueft, die weder der
-- Client noch der Rest der Datenbank benutzt: das Terminal haette sich
-- angemeldet und waere anschliessend an jeder Policy verhungert.
-- ENTSCHEID Sebastian: EINE Rollenwahrheit = auth_role() = public.users.role.
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
-- Rollen-Erkennung wie bei lager_display: ueber public.users.role, gelesen via
-- public.auth_role() (SELECT role FROM public.users WHERE auth_user_id=auth.uid()).
-- Der Kiosk-Account IST ein Datensatz in public.users — er ist nur kein
-- Mitarbeiter: er hat keine monteur_id. Genau darum braucht der Urlaubs-Trigger
-- weiter unten einen eigenen Zweig (siehe Abschnitt 5).
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
  IF NOT ( public.auth_role() = 'stempel_terminal'
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
  USING ( public.auth_role() = 'stempel_terminal' );

DROP POLICY IF EXISTS stempel_log_insert_terminal ON public.stempel_log;
CREATE POLICY stempel_log_insert_terminal ON public.stempel_log
  AS PERMISSIVE FOR INSERT TO authenticated
  WITH CHECK ( public.auth_role() = 'stempel_terminal' );

-- Bewusst KEINE UPDATE-/DELETE-Policy fuer stempel_terminal — append-only.

-- ── 3) system_config: nur der eine Key 'stempel_pause_rules', nur lesend ──
-- Verengt auf genau diesen Key, damit die Terminal-Rolle keine anderen
-- system_config-Werte (z.B. kv_rules, ticket_templates) sehen kann.
DROP POLICY IF EXISTS system_config_select_stempel_terminal ON public.system_config;
CREATE POLICY system_config_select_stempel_terminal ON public.system_config
  AS PERMISSIVE FOR SELECT TO authenticated
  USING (
    public.auth_role() = 'stempel_terminal'
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
    public.auth_role() = 'stempel_terminal'
    AND status = 'beantragt'
  );

-- ╔══════════════════════════════════════════════════════════════════════════╗
-- ║  ⛔ ABSCHNITT 5 IST STILLGELEGT — NICHT WIEDER SCHARF SCHALTEN.           ║
-- ║                                                                          ║
-- ║  Der CREATE OR REPLACE FUNCTION guard_urlaub_edit() weiter unten ist      ║
-- ║  KOMPLETT AUSKOMMENTIERT. Er darf so NICHT ausgefuehrt werden.            ║
-- ║                                                                          ║
-- ║  GRUND (Chat-Claude, MD5-Vergleich in der DB, 14.07.2026):                ║
-- ║  security_triggers_LIVE_v3911.sql ist eine REKONSTRUKTION und sie ist     ║
-- ║  UNVOLLSTAENDIG. Der echte Live-Body hat normalisiert 1746 Zeichen, die   ║
-- ║  Repo-Datei nur 953. Es fehlen ~800 Zeichen echter Logik.                 ║
-- ║                                                                          ║
-- ║  Ein CREATE OR REPLACE auf Basis dieser Rekonstruktion haette die         ║
-- ║  fehlenden ~800 Zeichen KOMMENTARLOS GELOESCHT. Kein Fehler, kein         ║
-- ║  Rollback, keine Warnung — die Urlaubs-Absicherung waere still um         ║
-- ║  Logik aermer gewesen, die niemand mehr kennt.                            ║
-- ║                                                                          ║
-- ║  DIE REGEL, DIE DARAUS FOLGT:                                             ║
-- ║  CREATE OR REPLACE auf ein LIVE-Objekt NIEMALS auf Basis einer            ║
-- ║  Repo-Rekonstruktion. Immer zuerst den Ist-Body aus der DB ziehen         ║
-- ║  (pg_get_functiondef) und DARAUF aufbauen.                                ║
-- ║                                                                          ║
-- ║  NAECHSTER SCHRITT (v3): Sobald der echte Live-Body als                   ║
-- ║  docs/wip/guard_urlaub_edit_LIVE_2026-07-14.sql im Repo liegt, wird       ║
-- ║  dieser Abschnitt NEU aufgebaut: vollstaendiger Live-Body + der           ║
-- ║  minimal-invasive stempel_terminal-Zweig an der richtigen Stelle.         ║
-- ║  Der Live-Body liegt Claude Code NICHT vor (kein DB-Zugriff).             ║
-- ║                                                                          ║
-- ║  BIS DAHIN: Die Abschnitte 1-4 dieser Datei (RPC + Policies) sind         ║
-- ║  unbedenklich und koennen laufen. Der Urlaubs-Antrag am Terminal          ║
-- ║  funktioniert aber ERST, wenn der Trigger-Zweig da ist — bis dahin        ║
-- ║  scheitert er am RAISE EXCEPTION des bestehenden Triggers. Stempeln       ║
-- ║  (Kommen/Gehen) funktioniert dagegen sofort.                              ║
-- ╚══════════════════════════════════════════════════════════════════════════╝
--
-- ── 5) TRIGGER-KONFLIKT: guard_urlaub_edit() muss angepasst werden ────────
-- ACHTUNG: Die folgende Analyse basiert auf der UNVOLLSTAENDIGEN Rekonstruktion
-- sql/security_triggers_LIVE_v3911.sql. Sie beschreibt den Konflikt korrekt,
-- aber der Loesungscode darunter ist NICHT lauffaehig (siehe Kasten oben).
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
-- (Rollen-Erkennung laeuft ueber public.auth_role() = public.users.role, nicht
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
-- CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
-- RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
-- DECLARE
--   me record;
--   sub text := auth.jwt() ->> 'sub';
-- BEGIN
--   IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass
-- 
--   SELECT role, perms_override, monteur_id INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
-- 
--   -- NEU (v2): Stempel-Terminal. Der Terminal-User HAT eine Zeile in public.users
--   -- (role='stempel_terminal') — genau wie der Lager-Kiosk (lager_display). Er hat aber
--   -- KEINE monteur_id, kann den Self-Service-Zweig unten also nie erreichen: dessen
--   -- Bedingung NEW.worker_id = me.monteur_id waere immer NULL = falsch, und JEDER
--   -- Terminal-Antrag waere unten am RAISE EXCEPTION gestorben. Darum dieser Zweig.
--   -- Er steht NACH dem users-Lookup (er braucht me.role) und VOR dem Admin-Check.
--   -- Erlaubt ist ausschliesslich INSERT mit status='beantragt', fuer BELIEBIGE
--   -- worker_id (der Mitarbeiter identifiziert sich per NFC-Chip, nicht per Login).
--   -- Kein UPDATE, kein DELETE, kein Selbst-Genehmigen.
--   IF me.role = 'stempel_terminal' THEN
--     IF TG_OP = 'INSERT' AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN
--       RETURN NEW;
--     END IF;
--     RAISE EXCEPTION 'urlaub: stempel_terminal darf nur INSERT mit status=beantragt';
--   END IF;
-- 
--   IF me.role = 'admin' OR (me.perms_override -> 'urlaub_edit')::text = 'true' THEN
--     RETURN COALESCE(NEW, OLD);                            -- Verwalter: voll
--   END IF;
--   -- Monteur-Self-Service: nur eigene, nur Status 'beantragt', kein Selbst-Genehmigen
--   IF TG_OP = 'INSERT' THEN
--     IF NEW.worker_id = me.monteur_id AND COALESCE(NEW.status,'beantragt') = 'beantragt' THEN RETURN NEW; END IF;
--   ELSIF TG_OP = 'UPDATE' THEN
--     IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' AND NEW.status = 'beantragt' THEN RETURN NEW; END IF;
--   ELSIF TG_OP = 'DELETE' THEN
--     IF OLD.worker_id = me.monteur_id AND OLD.status = 'beantragt' THEN RETURN OLD; END IF;
--   END IF;
--   RAISE EXCEPTION 'urlaub: keine Berechtigung (nur eigene Anträge im Status beantragt)';
-- END $$;
-- Trigger-Bindung trg_guard_urlaub_absences bleibt unveraendert (CREATE OR
-- REPLACE FUNCTION aendert nur den Funktionsbody, nicht die Trigger-
-- Registrierung aus security_triggers_LIVE_v3911.sql — kein erneutes
-- CREATE TRIGGER noetig/gewuenscht).

-- ═══════════════════════════════════════════════════════════════════
-- SEBASTIAN: User anlegen (Auth ist tabu fuer Claude Code — kein
-- auth.users-INSERT in dieser Datei). Vorgehen analog zum bestehenden
-- Lager-Kiosk-User (lager/lager_display):
--
-- GEPRUEFT (v2): Die App-Benutzerverwaltung kann diese Rolle NICHT vergeben.
-- Ihr Rollen-Dropdown wird aus Object.keys(ROLES) gebaut (index.html ~Z.11102),
-- und ROLES (~Z.3183) enthaelt weder 'lager_display' noch 'stempel_terminal' —
-- beides sind Geraete-Rollen ausserhalb des Mitarbeiter-Rollenmodells. Der
-- SQL-Weg unten ist also NICHT die bequeme Abkuerzung, sondern der einzige.
--
--   1. Supabase Dashboard → Authentication → Users → "Add user"
--      (z.B. stempel@ep-kolar.local, Passwort setzen). Die auth.users-Zeile
--      legt NUR Sebastian an — auth ist tabu fuer Claude Code.
--      KEIN raw_app_meta_data noetig. v1 verlangte das; es war falsch.
--   2. Die zugehoerige public.users-Zeile anlegen — DAS ist die Rollenquelle,
--      die auth_role() liest und auf der alle Policies dieser Datei sitzen.
--      auth_user_id ist die UUID aus Schritt 1 (im Dashboard am User sichtbar):
--
--      -- INSERT INTO public.users (id, auth_user_id, username, name, role)
--      -- VALUES (
--      --   gen_random_uuid(),
--      --   '<AUTH-UUID-AUS-SCHRITT-1>',
--      --   'stempel',
--      --   'Stempel-Terminal',
--      --   'stempel_terminal'
--      -- );
--
--      Spaltennamen vorher gegen die LIVE-Tabelle pruefen (der bestehende
--      lager-User ist die beste Vorlage):
--      -- SELECT id, auth_user_id, username, name, role, monteur_id
--      --   FROM public.users WHERE role = 'lager_display';
--      Der Terminal-User bekommt bewusst KEINE monteur_id — er ist kein
--      Mitarbeiter. Genau darum braucht der Urlaubs-Trigger (Abschnitt 5)
--      seinen eigenen Zweig.
--   3. Verifizieren, dass die Rollenquelle greift (als Terminal-User eingeloggt):
--      -- SELECT public.auth_role();   -- muss 'stempel_terminal' liefern
--   4. Client: App-Gate + RPC-Ladeweg sind ab App-Version v3.9.695 drin
--      (curUser.role==='stempel_terminal' im ?screen=stempel-Gate, workers-Load
--      ueber stempel_terminal_workers(), Antrags-Doppelpruefung ueber den
--      PK-Konflikt statt ueber ein absences-SELECT). Kein weiterer Client-
--      Schritt noetig.
--   5. Diese Datei ist rein additiv: der bestehende Admin-Betrieb des Kiosks
--      (is_staff()-Policies aus STEMPEL_v1.sql) bleibt unangetastet. Der
--      Admin-Preview ueber ?screen=stempel funktioniert unveraendert weiter.
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
-- -- Body muss den neuen "IF me.role = 'stempel_terminal' THEN ..."-Zweig enthalten,
-- -- und zwar NACH dem SELECT ... INTO me aus public.users (er braucht me.role) und
-- -- VOR dem Admin-Check. Steht er davor, ist me noch leer und der Zweig greift nie.
-- -- 'jwt_role' darf im Body NICHT mehr vorkommen (das war die v1-Rollenquelle).
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
