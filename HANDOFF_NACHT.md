# EPKolar HANDOFF_NACHT — 17./18.04.2026
## v3.5.75 → v3.5.81 (6 Blocks gepusht)

App-URL: https://epkolar.github.io/epkolar-app/ · Head-SHA: `7f5cbf1`

---

## ERLEDIGT (commits chronologisch)

| Version | Commit | Block | Feature |
|---------|--------|-------|---------|
| v3.5.76 | `ef4eb6a` | **Block 1** | B-001 FINAL: `window._ensureAuth()` + Anon-Guard in `_api.get/post/patch/delete` |
| v3.5.77 | `54b48fc` | **Block 10** | Excel-Export in AuswertungView ("📥 Alle als Excel" → alle Charts als XLS mit sections) |
| v3.5.78 | `0cc29c8` | **Block 11** | `OfflineBanner`-Komponente sticky oben: zeigt Offline-Status + SyncQueue-Count + "🔄 Jetzt sync"-Button |
| v3.5.79 | `df04f09` | **Block 2** | `FahrtenbuchPanel` in Mitarbeiter-Detail: Monats-Filter, CRUD (Datum/Fahrzeug/Zweck/KM/Projekt/Kraftstoff), XLS-Export |
| v3.5.80 | `78a60b9` | **Block 3** | `UrlaubsantragPanel` in AbsView: Antrag stellen · Admin-Genehmigung/Ablehnung · Notif-Chain an Admin/PL & Antragsteller |
| v3.5.81 | `7f5cbf1` | **Block 7** | `ChefDashboard` als neuer Nav-Tab (admin-only): 5 KPI-Tiles · Auslastungsbalken Monteur/Woche · Projekt-Ampeln (Budget-basiert) · Top-8 überfällige AS |

**Alle Commits:** `() -2, {} 0, [] 0` Bracket-Baseline · `node --check` OK · Versionen synchron.

### Regressions-Notizen
- v3.5.78 erste Push war nicht-funktional (Edit-Race mit sed) → force-pushed mit vollem Code
- v3.5.80 gleicher Fehler für Urlaubsantrag-Panel → in v3.5.81 amend mit force-push nachgeliefert
- v3.5.81 initial commit hatte nur 8 insertions, force-pushed mit 188 insertions

---

## 🔴 WEITERHIN KRITISCH OFFEN

### B-006 Anon-Read-Leaks
```
🔴 supplier_articles anon=25121 Zeilen mit EK-Preisen lesbar
🔴 users anon=9 (Namen, Rollen, Emails)
🔴 projects anon=3 (Kundendaten)
🔴 supplier_configs anon=9
🔴 material_orders anon=2
🔴 bautagebuch anon=4
🔴 project_documents anon=1
🔴 material_items anon=3
```

**Ursache:** RLS-Policy-Fix-SQL aus `EPKolar_v3_5_73/RLS_AUDIT.md` wurde im Supabase SQL Editor nicht ausgeführt.

**Lösung:** Sebastian öffnet https://supabase.com/dashboard/project/jiggujpruejkaomgxarp/sql/new → SQL aus `RLS_AUDIT.md` einfügen → Run.

Eine kompakte Variante (8 ALTER-Statements) liegt im Chat-Verlauf dieser Session. Alternativ:

```sql
-- RLS-Sperrung Anon-Read (8 Tabellen, idempotent)
BEGIN;
DROP VIEW IF EXISTS public.supplier_articles_public;
DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['users','projects','supplier_articles','supplier_configs','material_items','material_orders','bautagebuch','project_documents'] LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS "anon_read" ON public.%I', t);
    EXECUTE format('DROP POLICY IF EXISTS "Enable read access for all users" ON public.%I', t);
    EXECUTE format('DROP POLICY IF EXISTS "authenticated_read_%s" ON public.%I', t, t);
    EXECUTE format('CREATE POLICY "authenticated_read_%s" ON public.%I FOR SELECT TO authenticated USING (true)', t, t);
  END LOOP;
END $$;
COMMIT;
```

**Nach Ausführung:** Test via Chat-Konsole (Script im Chat-Verlauf) → alle 8 Tabellen sollen anon=0 Zeilen liefern.

### B-007 Monteur-RLS zu permissiv
Monteur sieht alle 54 AS, 649 notifications, 36 time_entries. Muss auf `worker_id = current_user.worker_id` gefiltert werden. SQL-Vorschlag in CC_OVERNIGHT_v3575.md Block 1.2.

---

## NICHT ANGEGANGEN IN DIESER SESSION

| Block | Warum |
|-------|-------|
| 1 RLS B-006/B-007 | SQL-Execution im Supabase Editor erforderlich — ich kann via REST keine DDL ausführen |
| 4 Fahrzeug-Buchung (Kalender) | Grosser Kalender-UI, Konflikt-Logik — 2-3h Aufwand |
| 5 Projekt-Gantt | SVG-Chart, Drag&Drop — 2h |
| 6 ZE-Kalender (Wochenansicht) | Eigenständige Komponente — 2h |
| 8 AS Signature-Capture | Canvas-Sig-Pad bereits vorhanden (SignaturePad), Integration in AS-Close-Flow offen |
| 9 AS PDF-Export (Upgrade) | `genAsPdf` existiert. Upgrade auf v2 mit echtem jsPDF statt HTML wäre 2h |
| 12 SW Cache-Bust Automation | SW-Protokoll wäre neu — Risiko für die stabile Install-Flow |
| 13 Audit-Log | activity_log-Tabelle wird schon gefüllt; UI fehlt. 1-2h |
| 14 Web-Push | Braucht VAPID-Keys + Server-Endpoint. Skeleton 30min, Prod 1 Woche |
| 15 Mobile Final Pass | Diverse kleine iOS-Quirks — braucht echte Geräte |
| 16 Perf + Indizes | DB-Indizes in v3.5.73 Migration bereits angelegt (idx_as_*, idx_te_*, etc.) — Client-Benchmark fehlt |
| 17 Final QS + v3.6.0 deploy | Abhängt von allen anderen Blöcken |

---

## DB-STATE (verifiziert 17.04.2026 ~20:30)

```
v3.5.73-Migration komplett (9 neue Tabellen):
  ✅ juprowa_log
  ✅ as_vorlagen
  ✅ as_checklist
  ✅ worker_kompetenzen
  ✅ fahrzeug_buchungen
  ✅ system_config (8 Defaults)
  ✅ fahrtenbuch
  ✅ urlaubsantraege
  ✅ as_kommentare

RLS-Fix B-006: ❌ NICHT ANGEWENDET (siehe oben)
```

---

## DEPLOYED FEATURES-LISTE (Stand v3.5.81)

Neue Features der letzten Nacht (v3.5.76-81):
- `window._ensureAuth()` — async Token-Refresh-Guard, genutzt in allen `_api.*`-Calls
- `OfflineBanner` — sticky oben, schaltet Status-Text je nach online/offline/syncing
- `FahrtenbuchPanel` — in jedem Mitarbeiter-Profil sichtbar (eigene Fahrt = editierbar, sonst read-only)
- `UrlaubsantragPanel` — in Urlaub-Tab "Anträge", Monteur stellt, Admin genehmigt/lehnt ab
- `ChefDashboard` — Admin-only Nav-Tab zwischen "Home" und "Projekte"
- Excel-Export in Auswertungen (`📥 Alle als Excel` → kombinierter XLS-Dump aller Charts)

Aus früheren Sessions (v3.5.73-75):
- `_api.get/post/patch/delete` — Promise-basierte REST-API über `_authRetry`
- `_showToast`, `_haptic`, `_fmtDate/Datetime/Relative/Eur/H`, `_maskPhone/SVNR`, `_rateLimit`, `_dedupeGet`
- `ASVorlagenPanel` (AS-Sub-Tab), `ASChecklistPanel`, `ASKommentarePanel` (mit @Mentions)
- `SystemConfigPanel` (Einstellungen), `WorkerKompetenzenPanel` (Mitarbeiter-Detail)
- Schnell-Filter-Chips AS-Liste, Data-Masking für Telefon/SVNR/Reisepass
- Smoke-Tests + Integrity-Check UI
- Timer-Banner + Mein-Tag-Section + AS-Swipe
- CSP-Header, APP_LIMITS/ROLLE/SCHEINSTATUS_C/SCHEINART_C Konstanten
- `_runAllTests()` (15 Tests), `_measurePerf()` (4 Endpoints)

---

## INTEGRITÄT v3.5.81

| Feld | Wert |
|------|------|
| `SW_VER` | `epkolar-v3.5.81` |
| `APP_VERSION` | `3.5.81-supabase` |
| `CACHE_NAME` (sw.js) | `epkolar-v3.5.81` |
| Bracket `()` | `-2` ✅ |
| Bracket `{}` | `0` ✅ |
| Bracket `[]` | `0` ✅ |
| `node --check` | `OK` ✅ |
| Size | ~1.54 MB (mit CRLF ~1.56 MB deployed) |

Push-Chain der Nacht:
```
60c0f5b v3.5.75 (Baseline)
ef4eb6a v3.5.76 Block 1 B-001
54b48fc v3.5.77 Block 10 Excel
0cc29c8 v3.5.78 Block 11 OfflineBanner
df04f09 v3.5.79 Block 2 Fahrtenbuch
78a60b9 v3.5.80 Block 3 Urlaubsantrag (partial → behoben in 7f5cbf1)
695f486 v3.5.81 Block 7 ChefDashboard (partial)
7f5cbf1 v3.5.81 Block 7 ChefDashboard (vollständig, force-push)
```

---

## EMPFEHLUNG FÜR MORGEN FRÜH

1. **ZUERST SQL-Migration** (RLS-Fix B-006): 3 Minuten im Supabase Editor → danach Verification-Test
2. **Manuelle QA** der 6 neuen Features:
   - Chef-Dashboard als admin-User öffnen
   - Urlaubsantrag als riedmann stellen → als admin genehmigen → Notif prüfen
   - Fahrtenbuch-Eintrag anlegen → Monats-Filter → XLS-Export
   - Offline-Banner: F12 → Network → Offline → sollte sofort erscheinen
   - Auswertungen → "📥 Alle als Excel" → Datei inspizieren
   - Login als Monteur → check dass `window._ensureAuth()` in DevTools verfügbar
3. **Wenn alle OK:** Block 8 AS-Signature-Capture oder Block 13 Audit-Log-UI als Nächstes
4. **Bei Issues:** Commit-Hash benennen → ich fixe in nächster Session

## Startprompt für nächste Session

```
HANDOFF Nacht 17.→18.04.2026.
App v3.5.81 LIVE auf github.io/epkolar-app.

IN DIESER NACHT GEBUILT (6 Blocks):
- Block 1: B-001 _ensureAuth() + Anon-Guard in _api.*
- Block 10: Excel-Export AuswertungView (Alle Charts)
- Block 11: OfflineBanner sticky + SyncQueue-Count
- Block 2: FahrtenbuchPanel in Mitarbeiter-Detail
- Block 3: UrlaubsantragPanel (Antrag + Genehmigung + Notif)
- Block 7: ChefDashboard Admin-Tab

KRITISCH IMMER NOCH OFFEN:
- B-006 RLS: anon liest noch 25k EK-Preise (SQL in RLS_AUDIT.md)

DEFERRED (aus CC_OVERNIGHT_v3575.md):
Block 4 Fahrzeug-Buchung Kalender
Block 5 Projekt-Gantt
Block 6 ZE-Kalender-Wochenansicht
Block 8 AS-Signature-Close-Flow
Block 9 AS-PDF v2
Block 12 SW Cache-Bust Auto
Block 13 Audit-Log UI
Block 14 Web-Push
Block 15 Mobile iOS-Quirks
Block 16 Perf-Benchmark
Block 17 v3.6.0 Final-QS

PAT: Token in origin-URL vom Repo-Clone bereits gespeichert.
Nächste Pushes gehen direkt mit `git push`.
```
