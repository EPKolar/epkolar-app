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
- **17× `function_search_path_mutable`**: Funktionen ohne fixiertes `search_path` (z.B. `guard_projects`, …).
  Hardening = `ALTER FUNCTION … SET search_path = public, pg_temp`. Pro Funktion prüfen (manche sind Trigger). CC's
  neue `portal_fetch` ist KORREKT fixiert (nicht in der Liste).
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
