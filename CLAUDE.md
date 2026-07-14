# EPKolar-App — Claude-Code Hinweise

## Repo-Pfade — Arbeitsklon vs. Spiegel (seit 13.07.2026)

| Pfad | Rolle |
|---|---|
| **`C:\repos\epkolar-app`** | **Arbeitsklon — der einzige.** Alle Edits, Tests, Commits, Pushes laufen hier. |
| `\\srvdc02\Projekte\…\03_Repos\epkolar-app` (Z:/T:) | **Nur Ablage/Spiegel.** **Keine Edits, keine Commits, kein Push — und kein Pull durch Claude Code.** |

> **Claude Code führt KEINE git-Befehle mehr über Z:/SMB aus — auch keinen Abschluss-Pull.**
> Gemessen 13.07.2026: ein einziger `git pull` über das Share brauchte **74 Minuten**.
>
> **Der Spiegel aktualisiert sich seit 13.07.2026 selbst:** geplanter Task `EPKolar-Spiegel-Pull`
> auf srvdc02, täglich 05:00, läuft als SYSTEM mit portablem MinGit (`D:\tools\git`, kein Installer).
> Aktion: `git -C "D:\Projekte\…\epkolar-app" pull --ff-only origin main`
> (`--ff-only` als Schutz — der Spiegel darf **nie** mergen). Server-lokaler Pfad ist `D:\Projekte\…`,
> **nicht** der UNC-Pfad. Erster Lauf verifiziert: Exit 0, 127 s, Stashes unversehrt.
>
> Der Spiegel enthält seit 13.07. ohnehin keine Unikate mehr — beide Stashes liegen als Patch in
> `docs/wip/`. GitHub ist die Quelle der Wahrheit.

**Warum:** Das srvdc02-Share ist für git/pytest unbrauchbar langsam. Gemessen am 12.07.2026:
pytest 2h04 (lokal: 21 min) · `git push` 28–30 min (lokal: Sekunden) · `git commit`/`git status`
laufen regelmäßig in Minuten-Timeouts, ein gekillter Lauf hinterlässt eine stale
`.git/index.lock` · dazu ein SMB-Aussetzer mitten im git-Befehl
(»unable to open object pack directory: Function not implemented«).

> **Achtung Laufwerksbuchstaben (nur noch für den Spiegel relevant):** auf PC `technik` ist das
> Repo unter `Z:`, auf Sebastians Desktop unter `T:`. Auf `technik` ist `T:` ein **anderer** Share
> (`\\srvdc02\Technik`) — NICHT das Repo.

**Stashes leben nur auf dem srvdc02-Spiegel** (`stash@{0}` Flotte-GPS-WIP, `stash@{1}` Sebastian-WIP)
und bleiben dort unangetastet. Der Flotte-WIP ist zusätzlich als
`docs/wip/FLOTTE_GPS_WIP_2026-07.patch` versioniert und damit auch im Arbeitsklon vorhanden.

### Regeln für git / node / npm

- Im Arbeitsklon `C:\repos\epkolar-app` arbeiten. Nie den rohen UNC-Pfad `\\srvdc02\…` als
  Arbeitsverzeichnis — CMD/npm haben Bugs damit (»UNC paths are not supported«).
- Edge-Function-Deploys NUR aus `C:\temp\epkfn` (`supabase` CLI verträgt weder UNC noch Netzlaufwerk).
- Vor jedem Commit verifizieren:
  ```
  cd /d C:\repos\epkolar-app
  git rev-parse --show-toplevel
  # erwartet: C:/repos/epkolar-app
  ```

### Tests

Voller Lauf direkt im Arbeitsklon: `python -m pytest tests/ -q` (~21 min, ~1172 Tests).
Gate ist **voller Lauf grün** — keine fixe Testzahl. Auf dem Share NIE testen.

## Versionierung — 4 Stellen synchron halten

Bei jedem App-Bump:
1. `index.html` `var SW_VER='epkolar-vX.Y.Z'` (Z.15)
2. `index.html` `const APP_VERSION="X.Y.Z-supabase"` (Z.~2463) — Versions-Historie als trailing comment-Chain
3. `sw.js` Header-Kommentar Zeile 1
4. `sw.js` `const CACHE_NAME = "epkolar-vX.Y.Z"` (Z.2)

## Gates vor jedem Push

```
python scripts/node_check.py index.html     # exit 0
python scripts/_bracket_check.py index.html # () -1, {} 0, [] 0 (Baseline)
node sql/_check_version.js                  # ✓ versions synced
python -m pytest tests/ -q                  # voller Lauf grün (~40 s)
```

### …und danach der Browser-Check. NICHT optional.

```
python -m http.server 8899 --bind 127.0.0.1   # im Repo-Wurzelverzeichnis, im Hintergrund
# Seite laden (Playwright/Chrome), dann prüfen:
#   - Console: 0 errors
#   - typeof APP_VERSION !== 'undefined'   (sonst ist der Script-Body abgebrochen)
#   - document.querySelector('#root').children.length > 0   (React gemountet)
```

**Warum das ein Pflicht-Gate ist — teuer gelernt am 14.07.2026:** v3.9.691 hinterließ
`window._stUuid=_stUuid;` in der Export-Zeile, obwohl `_stUuid` gelöscht war. Ergebnis:
`ReferenceError` auf **Top-Level** → der gesamte Script-Body danach (also die komplette App)
wurde nie definiert. **Die Live-App war über vier Versionen hinweg tot** und niemand hat es
gemerkt.

Keines der bestehenden Gates konnte das finden, und das ist kein Zufall:

| Gate | Warum es blind war |
|---|---|
| `node_check.py` | **parst** die Datei, **führt sie nicht aus**. Syntaktisch war alles korrekt. |
| `pytest` | statisch (String-/Regex-Asserts über den Quelltext). |
| Node-Eval-Tests | die Export-Zeile steht hinter `if(typeof window!=='undefined')` — **in Node gibt es kein `window`**. Der Zweig wurde übersprungen, der Fehler konnte dort gar nicht auftreten. |

**Kein Gate hat das Bundle je geladen.** Ein Browser hätte es in fünf Sekunden gefunden.
Zusätzlich fängt `tests/test_window_exports_defined.py` jetzt genau diese Fehlerklasse
statisch ab (mit Selbsttest: kaputte Zeile → rot, gesunde → grün).

## Push-Weg

`git push origin main`. KEIN `gh`. Remote-Verify per `curl raw.githubusercontent.com/EPKolar/epkolar-app/main/sw.js` nach jedem Push.

## Hart nicht anfassen

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Writes: nur Sebastian via Supabase-SQL-Editor (`jiggujpruejkaomgxarp`). Plugin zeigt auf falsche Org. SQ.push-DELETE/POST/PUT durch die App ist OK (das ist die normale Offline-Queue).
- Diagnose-Aufträge sind strikt read-only. Keine selbst-initiierten Fixes.
