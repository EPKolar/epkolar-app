# Supabase Security-Advisor-Backlog (2026-06-07, Bug-Hunt)

`get_advisors(security)` = **86 Lints (1 ERROR, 85 WARN)**. Fast alles **pre-existing**. **NICHT blind gefixt** —
das Massen-Ändern von Policies/Views/Funktionen auf der Live-Prod-DB ohne Einzel-Review würde die App brechen
(„kein blindes Hardening"). Hier kategorisiert + Empfehlung. Re-run jederzeit via `get_advisors`.

## 🔴 ERROR (1)
- **`security_definer_view` — `public.supplier_articles_public`**: View läuft mit Owner-Rechten (umgeht RLS).
  → Entweder droppen (wird `supplier_articles_safe` jetzt nicht ersetzt? prüfen wer `_public` noch nutzt) oder
  bewusst als gewollt akzeptieren. **Achtung:** das von CC neu angelegte `supplier_articles_safe` ist aus demselben
  Grund ein Definer-View (Monteur hat keinen Basistabellen-Zugriff) — dort INTENTIONAL + nötig.

## WARN-Kategorien
- **30× `rls_policy_always_true`**: Tabellen mit `USING(true)`-Policies für `ALL` (z.B. `authenticated_write_projects`,
  `auth_all_worker_projects` …). = die „~29 authenticated-offenen Tabellen" aus früheren Tasks. Jeder authenticated
  User kann schreiben. **Bewusst out-of-scope** (Sebastian-Entscheidung) — braucht pro Tabelle ein Zugriffsmodell.
- **`function_search_path_mutable` → ✅ 17 auf 4 reduziert (2026-06-07, `sql/harden_function_search_path_v3.9.157.sql`)**:
  13 Funktionen gehärtet (6 SECURITY-DEFINER-Helfer + 7 Trigger) — jede Def vorher gelesen (alle Refs qualifiziert
  → safe), verifiziert non-breaking. **Offen: nur die 4 `juprowa_*`** (bewusst out-of-scope). Dabei der Befund
  **`is_staff()`-Rollen-Strings** (`'pl'/'vadmin'` tot; effektiv = admin/buero = dokumentierte Absicht; ob PL/Techniker
  alle Daten sehen sollen = Sebastian-Entscheidung) — dokumentiert in der SQL-Datei, RLS NICHT blind geändert.
- **18× `anon_security_definer_function_executable` / 18× `authenticated_…`**: Rollen können SECURITY-DEFINER-Funktionen
  ausführen. Enthält CC's `portal_fetch` (gewollt, gehärtet) + Pre-existing. Pro Funktion prüfen, ob die Exposition gewollt ist.
- **1× `public_bucket_allows_listing`**: ein Storage-Bucket erlaubt anon-Listing (Dateinamen-Leak möglich). Bucket prüfen.
- **1× `auth_leaked_password_protection`**: Leaked-Password-Schutz aus → im Dashboard (Auth-Settings) aktivieren (low-risk Win).

## Empfehlung Priorität
1. `public_bucket_allows_listing` + `auth_leaked_password_protection` — kleine, klare Wins (Dashboard/Bucket-Config).
2. `function_search_path_mutable` — eine Welle `ALTER FUNCTION … SET search_path` (pro Funktion testen).
3. `rls_policy_always_true` (die 30) — das große Thema: pro Tabelle Schreib-Scope definieren. Größter Aufwand/Risiko.
4. `security_definer_view` `_public` — klären ob noch genutzt, sonst droppen.

CC hat NICHTS davon angewandt (Prod-DB-Sicherheit = kontrolliert mit dir, kein Blind-Hardening).

## 🆕 Deep-Hunt-Funde 2026-06-07
- **✅ BEHOBEN — Kunden-Portal „Mangel melden" + „Abnahme" waren KAPUTT (403).** Schrieben via Sync-Queue als
  anon auf `defects` (nur authenticated-Policies). Fix (Sebastian-freigegeben, `sql/portal_write_rpcs_v3.9.157.sql`):
  2 SECURITY-DEFINER-RPCs `portal_submit_defect`/`portal_confirm_abnahme` (validieren portal_code, erzwingen
  melder='Kunde'/Status, scoped aufs Projekt) + Frontend v3.9.157 (RPC statt SQ). Live anon-verifiziert.
- **✅ BEHOBEN — Storage-Enumeration:** Bucket `epkolar-files` (public) erlaubte anon volles LISTEN aller Projekt-
  Dateien. Fix (Sebastian-freigegeben, `sql/storage_disable_anon_listing_v3.9.157.sql`): 2 anon/public-SELECT-
  Policies auf storage.objects gedroppt → anon-list jetzt leer, public-URL-Download unberührt (App nutzt nur
  public-URLs). **OFFEN (größer):** Bucket bleibt public → Direkt-URL-Download bei bekanntem Pfad möglich; echter
  Schutz = privat + signed-URLs (Frontend-Refactor).
- **`auth_leaked_password_protection` aus** → im Supabase-Dashboard (Auth-Settings) aktivieren (low-risk, Dashboard).
