# 🔴 Kundenportal Security-Audit (Agententeam Welle 6, 2026-06-06)

**KRITISCH für Sebastian — server-seitig, NICHT im Client fixbar.** Das Kundenportal läuft **unauthentifiziert**: Portal-Nutzer sind nie eingeloggt → `_authToken=null` → **jede Portal-Anfrage geht mit dem hartkodierten anon-`SUPABASE_KEY`** (im ausgelieferten JS sichtbar). Der „Zugangscode" wird **nur client-seitig** verglichen (`tryPortal` L4122 `portalCode===code`). **Der gesamte Access-Boundary ist damit anon-RLS.** Wenn die anon-Policies permissiv sind, ist das Portal ein voller Kunden-Daten-Leak + Cross-Project-Write — **unabhängig vom Code**.

## ✅ Client-seitig gehärtet (v3.9.154)
- **Portal-Token-Entropie**: Generator nutzte `Math.random()` 4-stellig + 3-Zeichen-Präfix aus der öffentlichen Projektnummer (~13 bit, trivial brute-forcebar, nicht crypto). → jetzt `crypto.getRandomValues` 6 Zeichen aus 31er-Alphabet ohne 0/O/1/I/L (~30 bit). **Notwendig, aber NICHT hinreichend** — der Code-Match bleibt client-only, RLS muss zeilenscopen.

## 🔴 SEBASTIAN-SERVER-AUDIT — anon-RLS-Policies prüfen (load-bearing)
Für die **anon**-Rolle in Supabase, pro Tabelle:

1. **`projects`** — anon SELECT MUSS verweigert oder spalten-/zeilenrestriktiv sein. Aktuell liest der Client die **ganze Tabelle inkl. ALLER `portal_code`** (`_sbGet("projects","portal_code=not.is.null...")` L4121). Ist anon-SELECT offen → `fetch(REST+"/projects",{headers:{apikey:SUPABASE_KEY}})` dumpt **alle Kunden, Adressen, Emails, Vertragsbeträge (`betrag`) + alle Portal-Codes** in einem Request. **Wichtigster Punkt.**
2. **`defects`** — anon SELECT/INSERT/UPDATE MUSS zeilen-scoped auf den server-validierten Portal-Kontext sein, NICHT auf client-geliefertes `project_id=eq.`. Sonst:
   - SELECT: jedes Projekt-`project_id` einsetzbar (ids `p1`,`p4` trivial enumerierbar) → fremde Kunden-Mängel + Fotos leaken. Der `&melder=eq.Kunde`-Filter (L4159) ist client-only Defense-in-Depth, server-seitig wirkungslos.
   - INSERT (Mangel melden, L4213): `project_id`/`melder`/`kunde_status` sind client-gesetzt → Portal-Nutzer kann Defect in **jedes** Projekt posten + `melder` fälschen.
   - UPDATE (Abnahme, L4230): `PUT /defects/{id}` mit `{status:"behoben",kunde_status:"abgenommen"}` auf **jede** Defect-id → Status-Eskalation/Fälschung fremder/interner Defects. Spalten-Whitelist nötig (`_mapBody` reicht beliebige Felder durch).
3. **`project_documents`, `plans`, `checklists`** — anon SELECT scoped auf freigegebene Zeilen des richtigen Projekts. Insbesondere **`plans`** wird OHNE `kunde_freigabe`-Filter geholt (L4170, nur client-seitig gefiltert L4173) → server-seitig müssen nicht-freigegebene Pläne geblockt sein.

## ⏳ Weitere Funde (niedriger / Client)
- **P2 `_portalSync` Cross-Context** (L4185): Portal flusht die **globale** syncQueue (nicht nach Session/Rolle getrennt). Auf geteiltem Gerät: Staff loggt aus → Kunde nutzt Portal → `window.__doSync=_portalSync` versucht Staff-Items unter anon-Key zu flushen (meist RLS-fail, aber Loop `break`t → Queue stockt; was anon-RLS erlaubt, läuft im falschen Kontext). project_id ist im Body eingebacken → **kein** Re-Routing, aber Cross-Context-Execution. Fix: Items nach Session/Rolle taggen, Portal flusht nur portal-origin-Items. (Auch: `_portalSync` ohne Retry-Cap, siehe AGENT-REVIEW-FINDINGS Welle 2.)
- **P3 reviewNote-Disclosure**: interner `reviewNote`/zugewiesener Techniker wird dem Kunden für seine eigenen Mängel gezeigt (L4361-4362). Prüfen ob review notes kundentauglich sind.
- **P3 XSS aktuell verteidigt**: Kunden-Text (name/beschreibung) ist NICHT sanitisiert, aber überall via React (auto-escape) ODER `esc()` in Exporten gerendert → kein aktiver Stored-XSS. **Aber**: AS/Formular-Reports nutzen `document.write(el.innerHTML)` (L9914/L7081) — wenn je ein Defect-Feld in einen `document.write`-Export kommt, MUSS `esc()`. Guard/Kommentar empfohlen.

## ✅ Korrekt verteidigt
Kein service-role-Key im Client; users-Tabelle hinter `login_lookup`-RPC + Spalten-Allowlist; Mangel-Text längenlimitiert + Doppel-Submit-Guard; bestehende Report-Exporte escapen via `esc()`/`_e()`; `_openFileUrl` via Blob + noopener; Portal zeigt nur das eine gematchte Projekt (keine Enumeration in der UI).
