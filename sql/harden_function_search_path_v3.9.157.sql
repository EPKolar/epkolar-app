-- ✅ APPLIZIERT 2026-06-07 (CC, Bug-Hunt). Advisor function_search_path_mutable: 17 → 4 (juprowa out-of-scope).
-- Jede Funktion vorher gelesen: ALLE Refs qualifiziert (public.users, auth.jwt/uid, current_setting) oder
-- pg_catalog (now/json) → SET search_path = public, pg_temp ist 100% sicher (kein unqualifizierter Ref bricht).
-- Verifiziert: Helfer-Funktionen liefern weiter korrekt (auth_role='anon', current_user_role=null, is_staff=false).

-- SECURITY-DEFINER-Helfer (in RLS genutzt):
ALTER FUNCTION public.auth_role()          SET search_path = public, pg_temp;
ALTER FUNCTION public.current_monteur_id() SET search_path = public, pg_temp;
ALTER FUNCTION public.current_user_pk()    SET search_path = public, pg_temp;
ALTER FUNCTION public.current_user_role()  SET search_path = public, pg_temp;
ALTER FUNCTION public.is_staff()           SET search_path = public, pg_temp;
ALTER FUNCTION public.login_lookup(text)   SET search_path = public, pg_temp;
-- Trigger-Funktionen:
ALTER FUNCTION public.guard_admin_only()                SET search_path = public, pg_temp;
ALTER FUNCTION public.guard_kontingent()                SET search_path = public, pg_temp;
ALTER FUNCTION public.guard_projects()                  SET search_path = public, pg_temp;
ALTER FUNCTION public.guard_urlaub_edit()               SET search_path = public, pg_temp;
ALTER FUNCTION public.guard_users_privilege()           SET search_path = public, pg_temp;
ALTER FUNCTION public.update_supplier_orders_updated_at() SET search_path = public, pg_temp;
ALTER FUNCTION public.update_updated_at()               SET search_path = public, pg_temp;

-- NICHT angefasst (out-of-scope, Sebastian): juprowa_fetch_worksheets, juprowa_get_config,
--   juprowa_push_worksheet, juprowa_update_passport (4 Funktionen bleiben function_search_path_mutable).

-- ─────────────────────────────────────────────────────────────────────────────
-- 🔎 BEFUND (NICHT gefixt — Produkt-/Security-Entscheidung Sebastian): is_staff() Rollen-Strings
-- is_staff() prüft  role IN ('admin','buero','pl','vadmin').  Echte Rollen: admin/buero/projektleiter/
-- techniker/monteur. → 'pl' und 'vadmin' matchen NIEMANDEN (toter Code-Smell), 'projektleiter'/'techniker'
-- sind nicht enthalten. EFFEKTIV ist is_staff() = (admin OR buero) — das TRIFFT die dokumentierte Absicht
-- (index.html Z.831 "admin/buero: sieht alle Tabellen; monteur: nur eigene") → KEIN akuter Funktionsbruch.
-- Das Modell ist bewusst nuanciert: guard_projects erlaubt ('admin','projektleiter') Projekt-Edits, aber
-- is_staff (Alle-Daten-Zugriff auf arbeitsscheine/time_entries/notifications/urlaub/fahrtenbuch/…) bleibt
-- admin/buero. projektleiter/techniker haben eine monteur_id → sehen ihre EIGENEN Datensätze (nicht null).
-- OFFENE FRAGE für Sebastian: Sollen projektleiter/techniker ALLE arbeitsscheine/Zeiten sehen?
--   - JA → is_staff() auf  role IN ('admin','buero','projektleiter','techniker')  ändern (broadent Zugriff!).
--   - NEIN (Status quo) → optional die toten Strings 'pl'/'vadmin' entfernen (semantik-neutral):
--       CREATE OR REPLACE FUNCTION public.is_staff() ... role IN ('admin','buero') ...
-- CC hat is_staff() NICHT geändert (Über-Granting von RLS-Zugriff = gefährlich, nicht blind).
