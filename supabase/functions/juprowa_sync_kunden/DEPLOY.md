# Deploy: juprowa_sync_kunden (Edge-Function, Kundenstamm-Sync)

Ersetzt die DB-RPC `juprowa_fetch_kunden` für den Button — die RPC läuft ~7,5s und sprengt
das `statement_timeout=8s` der `authenticated`-Rolle (→ 500, Code 57014). Die Edge-Function
läuft ausserhalb dieses Timeouts. **GET-only gegen Juprowa**, Upsert nur in `kunden`.

## Reihenfolge (WICHTIG — gleiche Falle wie beim Bauprovisorien-Schema)
1. **Du deployst** die Function (Befehl unten).
2. **Testen** (Befehl unten) — muss `{ ok:true, imported:6457, ... }` liefern.
3. **Erst danach** stellt CC den Button in `index.html` von der RPC auf die Edge-Function um
   (eigener Commit, voller Gate) und pusht. Vorher NICHT — sonst ruft der Button eine
   nicht-existente Function.

## 1. Deploy (PowerShell, Copy-Paste) — läuft bei dir aus C:\temp\epkfn
```powershell
$src = "T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app\supabase\functions\juprowa_sync_kunden"
$dst = "C:\temp\epkfn\supabase\functions\juprowa_sync_kunden"
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item "$src\index.ts" $dst -Force
Set-Location C:\temp\epkfn
supabase functions deploy juprowa_sync_kunden --project-ref jiggujpruejkaomgxarp
```
(verify_jwt bleibt Default = an; die Function prüft zusätzlich is_staff().)

## 2. Test nach Deploy
Einfachster Weg — in der laufenden App (als admin/buero/projektleiter eingeloggt) in der
Browser-Konsole:
```js
fetch(SUPABASE_URL + "/functions/v1/juprowa_sync_kunden", {
  method: "POST",
  headers: { "Authorization": "Bearer " + _authToken, "Content-Type": "application/json" },
  body: "{}"
}).then(r => r.json()).then(console.log)
```
Erwartet: `{ ok:true, source_count:6458, deduped:6457, imported:6457, batches:13, duration_ms:<…> }`.

## 3. Danach: Button-Umstellung (macht CC)
`_kSync` in `index.html` ruft dann `SUPABASE_URL + "/functions/v1/juprowa_sync_kunden"`
(Bearer `_authToken`) statt `SB_REST + "/rpc/juprowa_fetch_kunden"`. Toast zeigt `imported`.
Voller Gate (Version-Triple, node-check, pytest) + Push + Live-Verify.

## Notiz zur DB-RPC
`juprowa_fetch_kunden` bleibt bestehen (funktioniert via service_role/cron ohne 8s-Limit) —
nur der **Button** wechselt auf die Edge-Function. `_juprowaPush`/OFFA unberührt.
