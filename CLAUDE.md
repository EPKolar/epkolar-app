# EPKolar-App — Claude-Code Hinweise

## Repo-Pfad / Environment

**Repo liegt physisch auf:** `\\srvdc02\Projekte\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app`

**Laufwerksbuchstabe ist pro PC verschieden gemappt:**
- PC `technik` (Inner-Claude/CC): `Z:`
- Sebastians Desktop: `T:`

> Auf `technik` ist `T:` ein **anderer** Share (`\\srvdc02\Technik`) — NICHT das Repo. Vor `cd T:\…` immer `git rev-parse --show-toplevel`.

### Regeln für git / node / npm

- IMMER lokal gemappten Laufwerksbuchstaben verwenden (auf `technik`: `Z:`). NIE den rohen UNC-Pfad `\\srvdc02\…` — CMD/npm haben Bugs damit (»UNC paths are not supported«, neue cmd-shell auf `C:\Windows`).
- Edge-Function-Deploys NUR aus `C:\temp\epkfn` (`supabase` CLI verträgt weder UNC noch Netzlaufwerk).
- Vor jedem Commit verifizieren:
  ```
  cd /d "Z:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app"
  git rev-parse --show-toplevel
  # erwartet: //srvdc02/Projekte/05_Claude/02_Baumanagment & Zeiterfassungs - APP/03_Repos/epkolar-app
  ```

## Versionierung — 4 Stellen synchron halten

Bei jedem App-Bump:
1. `index.html` `var SW_VER='epkolar-vX.Y.Z'` (Z.15)
2. `index.html` `const APP_VERSION="X.Y.Z-supabase"` (Z.~2463) — Versions-Historie als trailing comment-Chain
3. `sw.js` Header-Kommentar Zeile 1
4. `sw.js` `const CACHE_NAME = "epkolar-vX.Y.Z"` (Z.2)

## Triade vor jedem Push

```
python scripts/node_check.py index.html    # exit 0
python scripts/_bracket_check.py index.html # () -1, {} 0, [] 0 (Baseline)
node sql/_check_version.js                  # ✓ versions synced
python -m pytest tests/ -q                  # alle grün (aktuell 993)
```

## Push-Weg

`git push origin main`. KEIN `gh`. Remote-Verify per `curl raw.githubusercontent.com/EPKolar/epkolar-app/main/sw.js` nach jedem Push.

## Hart nicht anfassen

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Writes: nur Sebastian via Supabase-SQL-Editor (`jiggujpruejkaomgxarp`). Plugin zeigt auf falsche Org. SQ.push-DELETE/POST/PUT durch die App ist OK (das ist die normale Offline-Queue).
- Diagnose-Aufträge sind strikt read-only. Keine selbst-initiierten Fixes.
