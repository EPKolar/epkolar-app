-- ============================================================================
-- SECURITY-TRIGGER — BEREITS LIVE AUSGEFÜHRT (Chat-Claude via Supabase SQL-Editor, 2026-06-03)
-- ============================================================================
--
-- ╔════════════════════════════════════════════════════════════════════════╗
-- ║  ⛔ DIESE REKONSTRUKTION IST UNVOLLSTÄNDIG.                             ║
-- ║     NIEMALS ALS BASIS FÜR EIN "CREATE OR REPLACE" VERWENDEN.            ║
-- ║                                                                        ║
-- ║  Gemessen am 14.07.2026 (MD5-Vergleich der Normalform gegen die DB):    ║
-- ║    Live-Body guard_urlaub_edit()  = 1746 Zeichen                        ║
-- ║    Diese Datei                    =  953 Zeichen                        ║
-- ║  Es fehlen ~800 Zeichen ECHTER Logik. Welche, war zum Zeitpunkt des     ║
-- ║  Fundes noch nicht analysiert.                                          ║
-- ║                                                                        ║
-- ║  Ein CREATE OR REPLACE auf dieser Grundlage hätte diese ~800 Zeichen    ║
-- ║  KOMMENTARLOS GELÖSCHT: kein Fehler, kein Rollback, keine Warnung.      ║
-- ║  Die Urlaubs-Absicherung wäre still um Logik ärmer gewesen, die         ║
-- ║  niemand mehr kennt. Beinahe passiert über sql/STEMPEL_TERMINAL_v2.sql  ║
-- ║  (dort Abschnitt 5 deshalb stillgelegt).                                ║
-- ║                                                                        ║
-- ║  MASSGEBLICH IST AUSSCHLIESSLICH DER IST-STAND AUS DER DB:              ║
-- ║    select pg_get_functiondef(oid) from pg_proc                          ║
-- ║     where pronamespace='public'::regnamespace                           ║
-- ║       and proname='guard_urlaub_edit';                                  ║
-- ║  Gesicherter Live-Body: docs/wip/guard_urlaub_edit_LIVE_2026-07-14.sql  ║
-- ║                                                                        ║
-- ║                                                                        ║
-- ║  ⚠️ UND DAS BETRIFFT NICHT NUR guard_urlaub_edit.                       ║
-- ║  Diese Datei rekonstruiert FÜNF Trigger. Gemessen wurde bisher genau    ║
-- ║  EINER — und der war 800 Zeichen zu kurz. Gleiche Datei, gleicher       ║
-- ║  Rekonstruktionsvorgang, gleicher Tag. Es gibt keinen Grund            ║
-- ║  anzunehmen, dass ausgerechnet die anderen vier vollständig sind:       ║
-- ║      guard_kontingent        (Urlaubskontingent-Schutz)                 ║
-- ║      guard_users_privilege   (Schutz gegen Rechte-Eskalation!)          ║
-- ║      guard_admin_only        (Admin-Gate)                               ║
-- ║      guard_projects          (Projekt-Schutz)                           ║
-- ║  Sie sind ALLE als unverifiziert zu behandeln, bis gemessen.            ║
-- ║                                                                        ║
-- ║  ── PRÄZISIERUNG 14.07. spät ──────────────────────────────────────     ║
-- ║  Die erste Verify-Query (v1) hat FALSCH gemessen: sie verglich eine     ║
-- ║  von Postgres normalisierte Live-Seite gegen eine von Python            ║
-- ║  normalisierte Repo-Seite — zwei Engines, zwei Definitionen von \s.     ║
-- ║  Ihre Aussage „alle fünf weichen ab" ist damit UNBEWIESEN und kann      ║
-- ║  ein reines Messartefakt sein (unsichtbare Unicode-Leerzeichen aus      ║
-- ║  dem Copy-Paste-Deploy). → sql/VERIFY_TRIGGER_BODIES_v2.sql klärt das.  ║
-- ║                                                                        ║
-- ║  UNBERÜHRT davon bleibt der Kernbefund: 1746 gegen 953 sind ~800        ║
-- ║  Zeichen Unterschied. Whitespace-Artefakte erklären davon höchstens     ║
-- ║  ~86. Der Rest ist ECHTE LOGIK, die in dieser Datei fehlt.              ║
-- ║                                                                        ║
-- ║  → sql/VERIFY_TRIGGER_BODIES_v2.sql misst alle fünf auf einmal gegen    ║
-- ║    die DB (read-only, gefahrlos, ändert nichts). Ausführen, bevor       ║
-- ║    irgendjemand irgendeinen dieser Trigger anfasst.                     ║
-- ║                                                                        ║
-- ║  Diese Datei bleibt als HISTORIE liegen — sie wird nicht gelöscht,      ║
-- ║  aber sie ist keine Wahrheit.                                           ║
-- ╚════════════════════════════════════════════════════════════════════════╝
--
-- ⚠️ NICHT erneut ausführen / NICHT überschreiben. Diese Datei ist DOKU + Rollback-Basis.
-- Die LIVE-Version in der DB ist maßgeblich; die CREATE-Statements hier sind aus der
-- Beschreibung REKONSTRUIERT (Logik korrekt, Formulierung kann minimal abweichen).
--
-- 5 SECURITY-DEFINER-Trigger, alle: auth_user_id::text = (auth.jwt() ->> 'sub') (UUID-Cast!).
-- KEIN JWT (service_role / Edge-Function) → BYPASS (Trigger lässt durch).
-- admin behält IMMER vollen Zugriff.
--
-- | Tabelle           | Trigger                    | Funktion                |
-- | absences          | trg_guard_urlaub_absences  | guard_urlaub_edit()     |
-- | urlaubskontingent | trg_guard_kontingent       | guard_kontingent()      |
-- | users             | trg_guard_users_privilege  | guard_users_privilege() |
-- | system_config     | trg_guard_system_config    | guard_admin_only()      |
-- | projects          | trg_guard_projects         | guard_projects()        |
-- ============================================================================

-- Hilfs-Annahme: aktueller User
--   SELECT role, perms_override, monteur_id FROM public.users
--   WHERE auth_user_id::text = (auth.jwt() ->> 'sub')

-- ── 1) absences : guard_urlaub_edit() ───────────────────────────────────────
-- admin ODER urlaub_edit = VOLL (alle Anträge anlegen/ändern/genehmigen).
-- Monteur: nur EIGENE (worker_id = eigene monteur_id) im Status 'beantragt',
--          KEIN Selbst-Genehmigen (status darf nicht auf genehmigt/abgelehnt durch Antragsteller).
-- no-jwt → bypass.
-- Empfehlung: urlaub_edit per WERT prüfen, nicht per String-Match (siehe HINWEIS unten).
CREATE OR REPLACE FUNCTION public.guard_urlaub_edit()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE me record; sub text := auth.jwt() ->> 'sub';
BEGIN
  IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;  -- service_role bypass
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
CREATE TRIGGER trg_guard_urlaub_absences BEFORE INSERT OR UPDATE OR DELETE ON public.absences
  FOR EACH ROW EXECUTE FUNCTION public.guard_urlaub_edit();

-- ── 2) urlaubskontingent : guard_kontingent() ───────────────────────────────
-- Nur admin ODER urlaub_edit dürfen schreiben.
CREATE OR REPLACE FUNCTION public.guard_kontingent()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE me record; sub text := auth.jwt() ->> 'sub';
BEGIN
  IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT role, perms_override INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
  IF me.role = 'admin' OR (me.perms_override -> 'urlaub_edit')::text = 'true' THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'urlaubskontingent: nur admin/urlaub_edit';
END $$;
CREATE TRIGGER trg_guard_kontingent BEFORE INSERT OR UPDATE OR DELETE ON public.urlaubskontingent
  FOR EACH ROW EXECUTE FUNCTION public.guard_kontingent();

-- ── 3) users : guard_users_privilege() ──────────────────────────────────────
-- Nicht-Admin darf privilege-relevante Spalten NICHT ändern; legit Self-Update (phone etc.) erlaubt.
CREATE OR REPLACE FUNCTION public.guard_users_privilege()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE me record; sub text := auth.jwt() ->> 'sub';
BEGIN
  IF sub IS NULL THEN RETURN NEW; END IF;
  SELECT role INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
  IF me.role = 'admin' THEN RETURN NEW; END IF;
  IF NEW.role IS DISTINCT FROM OLD.role
     OR NEW.locked IS DISTINCT FROM OLD.locked
     OR NEW.permissions IS DISTINCT FROM OLD.permissions
     OR NEW.perms_override IS DISTINCT FROM OLD.perms_override
     OR NEW.auth_user_id IS DISTINCT FROM OLD.auth_user_id
     OR NEW.monteur_id IS DISTINCT FROM OLD.monteur_id THEN
    RAISE EXCEPTION 'users: privilege-relevante Felder nur durch admin änderbar';
  END IF;
  RETURN NEW;  -- legit Self-Update (phone, last_login, login_count, …)
END $$;
CREATE TRIGGER trg_guard_users_privilege BEFORE UPDATE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public.guard_users_privilege();

-- ── 4) system_config : guard_admin_only() ───────────────────────────────────
CREATE OR REPLACE FUNCTION public.guard_admin_only()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE me record; sub text := auth.jwt() ->> 'sub';
BEGIN
  IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT role INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
  IF me.role = 'admin' THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'system_config: nur admin';
END $$;
CREATE TRIGGER trg_guard_system_config BEFORE INSERT OR UPDATE OR DELETE ON public.system_config
  FOR EACH ROW EXECUTE FUNCTION public.guard_admin_only();

-- ── 5) projects : guard_projects() ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.guard_projects()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE me record; sub text := auth.jwt() ->> 'sub';
BEGIN
  IF sub IS NULL THEN RETURN COALESCE(NEW, OLD); END IF;
  SELECT role INTO me FROM public.users WHERE auth_user_id::text = sub LIMIT 1;
  IF me.role IN ('admin','projektleiter') THEN RETURN COALESCE(NEW, OLD); END IF;
  RAISE EXCEPTION 'projects: nur admin/projektleiter';
END $$;
CREATE TRIGGER trg_guard_projects BEFORE INSERT OR UPDATE OR DELETE ON public.projects
  FOR EACH ROW EXECUTE FUNCTION public.guard_projects();

-- ============================================================================
-- HINWEIS (siehe docs/handoff/URLAUB-RIGHTS-LOGIC-FOR-TRIGGER.md):
-- Falls die Live-Funktion urlaub_edit per String-Match (perms ~ '%urlaub_edit%') prüft, ist der
-- Aberkennungsfall {"urlaub_edit": false} falsch (String vorhanden → würde erlauben). Sauber ist der
-- WERT-Check (perms_override -> 'urlaub_edit')::text = 'true'. Solange niemand urlaub_edit:false setzt,
-- ist der Unterschied unsichtbar.
--
-- Rollback aller 5: sql/security_triggers_LIVE_v3911_ROLLBACK.sql
-- ============================================================================
