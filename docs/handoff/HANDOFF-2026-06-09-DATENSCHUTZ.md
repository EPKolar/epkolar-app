# HANDOFF 2026-06-09 — EPKolar-App Datenschutz-/Datenverlust-Härtung

**Repo:** `T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app` · github.com/EPKolar/epkolar-app · live https://epkolar.github.io/epkolar-app/ · Supabase `jiggujpruejkaomgxarp`
**Stand:** main HEAD = **`30ee5e5` = v3.9.212**, alles gepusht, **726 pytest grün**. Autonomes Pushen auf main erlaubt.

## 🔴🔴 KRITISCHER KONTEXT — PRODUKTIVBETRIEB MIT ECHTEN DATEN
**Backoffice + Lager (schober, pinger) befüllen DB+App LIVE produktiv. Monteure noch NICHT.** Höchste Daten-Vorsicht:
- KEINE destruktiven Ops, kein Clobber. DB-Write nur additiv/explizit. DELETE nur per exakter ID.
- Jede DB-DDL/DML/Policy = explizite Chef-Freigabe (Code-Pushes sind erlaubt, aber jeder Push = SW-Bump = Client-Reload).
- Nur additive, voll-getestete Changes; Push nur nach grüner Triade.

## 1. SOFORT-AKTIONEN FÜR DEN CHEF/SEBASTIAN (nicht von CC machbar)
1. **Alle Büro/Lager-Geräte EINMAL hart neu laden** (Strg+F5 / PWA schließen+öffnen) → auf **v3.9.212**. Grund: SW-Cache hing wiederholt auf alten Versionen; v3.9.209 fixt künftige Updates, aber schon hängende Geräte brauchen 1× Hard-Reload.
2. **Supabase → Auth → Sessions/Tokens** (gegen „ständiges Neu-Anmelden"): JWT-Expiry `3600`→`28800`s (8h); Refresh-Token-Reuse-Interval ≥`10`s (oder Rotation aus). App-Refresh-Code ist robust — das ist reine Config.
3. **Verlorene Mitarbeiter-Edits neu eingeben** (schober/günther/barger Geb-Datum/Führerschein wurden vom Seed überschrieben, nicht wiederherstellbar) — erst NACHDEM alle Admin-Geräte auf v3.9.212 sind.
4. **schober (buero) Schreibtest** nach dem auth_role()-Fix (Bautagebuch/Checkliste anlegen) → sollte jetzt persistieren.

## 2. DIESE SESSION GEFIXT (alle live)
**Code (gepusht):** v3.9.197-199 Gefahrenstoffe (base64-PDF in DB, gemeinsamer `PdfViewerModal`, CSP frame-src) · v3.9.200 Mobile-Crashes (Bell #310 conditional-hook `useSwipeDown`, Mobile-PDF-Button, Sync-Failsafe) · v3.9.201 Wochenplanung read-only Feld-Rollen · v3.9.202 Mitarbeiter-Self-Service (Mein Profil + eigene PW via `API.changePassword`) · v3.9.203 Fahrbewilligungen (Tabelle+RLS via `current_user_role()`) · v3.9.204 FINKZEIT/Monatsabrechnung reaktiviert · v3.9.205 Druck PDF→Bilder (`_pdfToImages`) + A4-quer + Mobile-Padding · v3.9.206 finkzeit Sync-Fix (updated_at-Blacklist) + Sofort-Sync + approved_at · v3.9.207 Druck-Bilder + approved_at · v3.9.208 **Seed-Clobber-Guard** · v3.9.209 **SW-Update-Banner-Fix** · v3.9.210 **Array→TEXT-Drops** (TEXT_JSON_FIELDS += schaeden/termine/serviceheft/verbrauchsmaterial/material/fotos/images) · v3.9.211 Sync-Default „immer" · v3.9.212 **checklists.items** + toggleActive/toggleLock (0/1).

**DB-Migrationen (angewendet via MCP):** gefahrstoff_module · fahrbewilligungen (+current_user_role-Policy) · storage-Policy revert · **updated_at-Spalten** auf project_documents/project_folders/fz_termine · **`auth_role()`→users.role** (Büro/PL-403-Fix, ~20 Policies) · material_catalogs anon-DML revoke · activity_log_insert_anon DROP · supplier_articles_safe EK-Positiv-Maskierung.

## 3. OFFEN — DB-SECURITY (vom Chef freigegeben, aber WEGEN BREAK-RISIKO bewusst angehalten → koordiniert + verifiziert machen)
- **#2 `login_lookup()` gibt bcrypt password_hash an anon** (DB-Funktion `to_jsonb(u.*)`, aufgerufen index.html:2212). ⚠️ Login-Flow nutzt aus dem Ergebnis **email + locked + password_hash (bcrypt-Fallback Z.2233) + role**. NICHT auf id/auth_user_id einschränken (bricht Login!). **Plan:** (a) verifizieren dass GoTrue für ALLE User klappt (alle 10 haben auth_user_id), (b) bcrypt-Fallback-Code retiren, (c) DANN `login_lookup` auf sichere Spalten (id,auth_user_id,email,locked,role,name,monteur_id,perms_override — NICHT password_hash/permissions) einschränken.
- **#5b** `supplier_articles_safe`/`_public` als SECURITY-DEFINER-Views (Advisor). `security_invoker=true` setzen NUR nachdem geprüft, dass kein anon/Portal diese Views liest (sonst Lesezugriff-Bruch). Base-RLS supplier_articles = authenticated true → für authenticated sicher.

## 4. OFFEN — FEATURES/UMBAU (Chef-Wünsche)
- **Monatsabrechnung-Druck fachlich falsch:** hochgeladenes PDF ist die 18-seitige FIRMEN-PZE (ALLE Mitarbeiter) → `druckAnsicht` (index.html ~15224 `_pdfToImages(z.datei)`) rendert alle 18 Seiten pro MA = Datenschutz-Problem (fremde Stunden) + schwer/langsam. **Plan:** beim Upload die MA-Seitenzahl `finkSeite` im `finkzeit.data`-JSON speichern (~15397, wie setFinkStunden) → nur diese Seite rendern (`getPage(finkSeite)`); Leer-Fallback NICHT `<img src=PDF-dataURL>` sondern Fehlertext; statt `setTimeout(500)` auf Bild-onload warten.
- **PDF→Stunden-Auto-Extraktion** (fixt Zeitabgleich): PDF ist TEXT-parsebar ("PZE Monatsübersicht detailliert", je MA `Gesamt`/`Soll`/KW-Summen) → pro MA Monats-Ist-Stunden auslesen → `finkStunden` auto-befüllen.
- **„2 Drucken-Buttons"** in Monatsabrechnung: `exportMonat` „Monatsübersicht drucken" (~15363) + `druckAnsicht` „Drucken" (~15525 Liste, ~15557 PDF-Viewer-Modal) — vereinheitlichen/klarer beschriften.
- **Mitarbeiter-ARCHIVIERUNG statt Löschen** (angefangen): `workers.active`=0 (hat updated_at). Anker: Load-Map ohne `active` index.html:4888 (active ergänzen), Lösch-Button index.html:6049, `delMonteur` ~5919, Liste `monteure.map` ~6009. archiveMonteur(active=0)/restoreMonteur(active=1) + Archiv-Toggle + Detail-Buttons.
- **Monatsabrechnung-Subpage Mobile/Umbau** (nach Hard-Reload bewerten — v3.9.205 Mobile-Padding ist drin, evtl. mehr nötig).
- **M2 (Qualität, kein Verlust):** `bautagebuch.anwesende` (jsonb) wird client-stringifyt (index.html:12662/12665) → roh als Array senden (NICHT in TEXT_JSON_FIELDS), bestehende Rows ggf. normalisieren.

## 5. GOTCHAS / TRIADE (wichtig)
- **Triade pro Change:** `python scripts/_bracket_check.py index.html` (Baseline `() -1 / {} 0 / [] 0`) → node --check auf größtem `<script>`-Block (KEIN `</script>` in Code/Kommentar!) → `python -m pytest tests/ -q > _po.txt 2>&1; echo "EXIT=$?">>_po.txt; tail _po.txt` (NIE `pytest|tail` — maskiert Exit). 726 Tests.
- **Version-Bump 4 Stellen:** `var SW_VER='epkolar-vX'` + `const APP_VERSION="X-supabase"` (index.html) + sw.js Header + `CACHE_NAME`.
- **Linter ändert index.html zwischen Read+Edit** → vor jedem Edit frisch `Read` (Grep zählt nicht).
- **TEXT_JSON_FIELDS (index.html:1683):** TEXT-Spalten mit Array/Objekt-Inhalt MÜSSEN drin sein, sonst PATCH 400 → SyncQueue-Drop nach 5 Versuchen = stiller Verlust. Stringify ist konditional (nur `typeof==='object'`, Z.1688). **updated_at-Injection-Blacklist Z.2168** = notifications/plans/finkzeit/fahrbewilligungen (Tabellen OHNE updated_at-Spalte). Robuster wäre: nur stringify/inject wenn Spalte existiert (information_schema-generiert).
- **RLS-Rollen-Check:** `current_user_role()`/`auth_role()` lesen jetzt beide `users.role WHERE auth_user_id=auth.uid()` (NICHT app_metadata.role = veraltet/inkonsistent). Neue role-gated Policies darauf bauen.
- **MCP-Schreibblock:** Auto-Mode-Classifier blockt breite/security-DB-Changes ohne explizite User-Freigabe (auth_role/open-RLS wurden geblockt bis OK). Pläne/Fahrzeuge/Fotos-Upload via Storage = ES256-JWT wird von Storage-API nicht honoriert → base64-in-DB-Muster nutzen.
- Supabase NUR Plugin-MCP, project_id `jiggujpruejkaomgxarp` (ORG-GUARD vor jedem SQL).

## 6. ERSTE SCHRITTE FRISCHE SESSION
1. `git -C "<repo>" log --oneline -5` + diese Datei lesen + Memory `epkolar_app_hunt_marathon_2026-06-04.md`.
2. Status der Chef-Sofort-Aktionen (§1) erfragen (Hard-Reload erfolgt? schober-Schreibtest ok? Session-Config gesetzt?).
3. Priorisieren mit Chef: Monatsabrechnung-Druck (pro-MA-Seite) + PDF-Auto-Stunden | Mitarbeiter-Archivierung | login_lookup-Härtung (#2).
