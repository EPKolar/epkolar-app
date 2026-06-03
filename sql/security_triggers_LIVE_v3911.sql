-- ============================================================================
-- SECURITY-TRIGGER — BEREITS LIVE AUSGEFÜHRT (Chat-Claude via Supabase SQL-Editor, 2026-06-03)
-- ============================================================================
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
