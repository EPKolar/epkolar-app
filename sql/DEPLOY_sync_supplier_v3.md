# sync_supplier Edge-Function · Deploy-Doku v3.6

## Finding (Block 12)
Die sync_supplier Edge-Function **liegt NICHT im epkolar-app Repo**. Plan erwartete `supabase/functions/sync_supplier/index.ts` — Ordner existiert nicht.

Wahrscheinlich: Function wird direkt im Supabase-Dashboard gepflegt ODER in einem separaten Repo. Sebastian prüft:
```bash
ls /t/03_Repos/epkolar-functions/   # eigenes Function-Repo?
ls /c/Users/technik/supabase-functions/  # local path?
# Oder Direkt im Supabase-Web-Editor: Dashboard → Edge Functions → sync_supplier
```

## Code-Review-Checkliste (wenn Function-Source gefunden wird)

- [ ] Error-Handling auf jeder `await fetch(...)` Zeile (kein silent fail)
- [ ] Timeout-Schutz: fetch mit AbortController, 30s max pro Lieferanten-API
- [ ] Rate-Limiting: z.B. Holter max 1 req/sec (via `await new Promise(r=>setTimeout(r,1000))`)
- [ ] Logging: jeder Lieferant mit timestamp + row-count + bytes in Tabelle `supplier_sync_log`
- [ ] Success/Fail-Counter in Response-Body
- [ ] Retry-Logic: Bei 5xx/network 3x retry mit exponential backoff
- [ ] Batch-Insert in supplier_articles via `on_conflict` (Upsert, nicht Truncate+Insert)
- [ ] RLS-Bypass: Function muss service_role_key nutzen (NICHT anon_key)

## Deploy-Commands (Template — prüfen vor Ausführung)

### Voraussetzung
```bash
# Supabase CLI installiert
npm install -g supabase
# Login
supabase login
# Project-Link
supabase link --project-ref jiggujpruejkaomgxarp
```

### Deploy
```bash
cd <function-repo>
supabase functions deploy sync_supplier \
  --no-verify-jwt \
  --project-ref jiggujpruejkaomgxarp
```

`--no-verify-jwt` weil die Function via pg_cron ohne JWT-Header aufgerufen wird. Wenn aus App aufgerufen mit Bearer-Token, dann `--verify-jwt`.

### Test (manuell)
```bash
# Mit service_role_key aus Dashboard → Project Settings → API → Service Role Key
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
curl -X POST https://jiggujpruejkaomgxarp.supabase.co/functions/v1/sync_supplier \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"supplier":"Holter"}'
```

Erwartete Response:
```json
{"ok":true,"supplier":"Holter","rows_synced":12543,"duration_ms":18420}
```

### Cron-Schedule (Supabase pg_cron)
```sql
-- Via Dashboard → SQL Editor
SELECT cron.schedule(
  'sync_supplier_daily',
  '0 3 * * *',  -- Täglich 03:00 UTC (= 04:00 oder 05:00 Wien je nach DST)
  $$
  SELECT net.http_post(
    url := 'https://jiggujpruejkaomgxarp.supabase.co/functions/v1/sync_supplier',
    headers := '{"Content-Type":"application/json","Authorization":"Bearer <SERVICE_ROLE_KEY>"}'::jsonb,
    body := '{"supplier":"Holter"}'::jsonb
  );
  $$
);

-- Unschedule falls nötig
-- SELECT cron.unschedule('sync_supplier_daily');
```

### Monitoring
```sql
SELECT
  jobname,
  schedule,
  last_run,
  last_status,
  last_return_message
FROM cron.job
LEFT JOIN cron.job_run_details ON job.jobid = job_run_details.jobid
WHERE jobname LIKE 'sync_supplier%'
ORDER BY last_run DESC
LIMIT 10;
```

## Offen für Sebastian
1. Function-Source-Code lokalisieren (Dashboard oder separates Repo?)
2. Wenn Dashboard: Code in dedizierten Commit ins `supabase/functions/sync_supplier/` hier im Repo ablegen → versionierbar
3. Checkliste oben durchgehen
4. Cron-Schedule prüfen: läuft sie aktuell? `last_run` aktuell?

## v3.9.1016 – supplier-sync meldet keinen Scheinerfolg mehr
`supabase/functions/supplier-sync` (action `sync`) antwortet fuer Haendler ohne implementierten Download mit `ok:false, error:"not_implemented"` und setzt `last_sync`/`last_sync_status` NICHT mehr auf `success` (vorher: Platzhalter `rows=[]` + `success` mit 0 Artikeln). Nur Repo, nicht deployt. Download je Haendler in `downloadArticles()` einsetzen. Die App ruft die Function weiterhin nirgends auf; DATANORM kommt per Upload im Reiter Administration > Haendler.

## v3.9.1016 Sammel – Stand laut Prod-DB (16.11.2026), damit niemand "nie funktioniert" liest
- Es GAB einen echten automatischen Sync: die **Dashboard-Function `sync_supplier`** (nicht im Repo) hat am **12.04.2026** fuer **Holter** rund **25.000 Artikel** geladen (`interface_type` shk_connect). Seitdem (rund 7 Monate) lief **kein** Sync mehr – Ursache offen (Cron/Function im Dashboard pruefen, siehe Monitoring oben).
- Die Zugangsdaten sind **nicht geleert**: 5 von 9 Haendlern haben sie gesetzt (Heinze, Holter, Impex, OEAG, SHT). Die App schickt username/password seit v3.9.1016 nur noch bei Neueingabe.
- Die Repo-Function `supabase/functions/supplier-sync` ist ein Platzhalter, nicht der produktive Weg; ihr `not_implemented` sagt nichts ueber `sync_supplier` im Dashboard. Vor einem Deploy die Dashboard-Quelle ins Repo holen (Punkt 2 oben), nicht den Platzhalter deployen.
- Die App zeigt auf der Haendlerkarte "Letzter Sync <Datum>, <n> Artikel" aus `last_sync` / `last_sync_articles`.
