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

## Behauptet ein Kommentar eine Eigenschaft, muss ein Test sie beweisen

Ein Kommentar wie „DST-sicher", „stempelt NICHT", „COLORS.ERROR raus" ist eine **Absichts-
erklärung, kein Fakt** — bis ein Test ihn belegt. Am 14.07.2026 waren **alle drei** dieser
wörtlichen Commit-Behauptungen falsch, und alle drei standen als Tatsache im Code:

- *„Basis 12:00 → DST-sicher"* — die Schleife verlor im Frühjahr einen ganzen Tag aus der
  Lohnabrechnung.
- *„Im Antrags-Modus stempelt der Scan NICHT"* — er stempelte in jedem Zustand außer `ident`.
- *„v3.9.697: COLORS.ERROR raus"* — an einer von drei Stellen stand es noch drin.

**Regel:** Behauptet ein Kommentar eine nicht-triviale Eigenschaft, schreib den Test, der sie
beweist — im selben Commit. Das gilt besonders für alles Lohnrelevante und für jede „X passiert
NICHT"-Aussage (die sind am teuersten, weil sie ein Schweigen versprechen).

## `CREATE OR REPLACE` auf Live-Objekte — NIE aus einer Repo-Rekonstruktion

**Regel:** Bevor eine Live-Funktion/-View per `CREATE OR REPLACE` ersetzt wird, **immer zuerst den
Ist-Body aus der DB ziehen** und darauf aufbauen. Eine Datei im Repo, die behauptet, den Live-Stand
abzubilden, ist eine **Behauptung**, kein Beweis.

```sql
-- 1) Ist-Stand holen (das ist die einzige Wahrheit):
select pg_get_functiondef(oid) from pg_proc
 where pronamespace='public'::regnamespace and proname='<funktion>';

-- 2) Normalform-Hash des FUNKTIONSKÖRPERS (prosrc = nur der Text zwischen den
--    Dollar-Quotes; Whitespace-Läufe → ein Space, trimmen, dann MD5).
--    Das ist das Standard-Werkzeug: zwei Bodies sind identisch, wenn ihr Hash gleich ist.
select md5(btrim(regexp_replace(prosrc, '\s+', ' ', 'g')))   as body_md5,
       length(btrim(regexp_replace(prosrc, '\s+', ' ', 'g'))) as body_len
  from pg_proc
 where pronamespace='public'::regnamespace and proname='<funktion>';
```

Denselben Hash über den Body in der Repo-Datei rechnen. **Weichen Hash oder Länge ab, ist die
Repo-Datei keine Replace-Basis** — Punkt. Nicht „wahrscheinlich schon", nicht „nur Formatierung".

### Absolute Regel für die fünf Security-Trigger (unbefristet)

`sql/security_triggers_LIVE_v3911.sql` rekonstruiert fünf Trigger:
`guard_urlaub_edit` · `guard_kontingent` · `guard_users_privilege` · `guard_admin_only` ·
`guard_projects`.

> **KEIN `CREATE OR REPLACE` auf irgendeinen dieser fünf, dessen Live-Body nicht als
> `docs/wip/<name>_LIVE_<datum>.sql` gesichert UND hash-verifiziert ist.**

Gemessen wurde bisher nur `guard_urlaub_edit` — Live **1746** Zeichen normalisiert gegen **953** in
der Repo-Datei. **~800 Zeichen echter Logik fehlen dort.** Ein Replace hätte sie kommentarlos
gelöscht: kein Fehler, kein Rollback, keine Warnung. Die anderen vier stammen aus derselben
Rekonstruktion und sind bis zur Messung **unverifiziert** — darunter `guard_users_privilege`, der
Schutz gegen Rechte-Eskalation.

`sql/VERIFY_TRIGGER_BODIES_v2.sql` misst alle fünf auf einmal gegen die DB (read-only, gefahrlos).
**Vor jedem Eingriff ausführen.**

### Jede Mess-Query trägt einen Kontrollwert. Ohne getroffenen Kontrollwert ist der Lauf ungültig.

Eine Messung, deren Ergebnis „plausibel aussieht", ist kein Beweis — sie ist eine Vermutung mit
Nachkommastellen. **Jede Mess-Query braucht einen Wert, dessen Soll man unabhängig kennt.**

Am 14.07.2026 hat genau das den Fehler gefangen: Die Verify-Query lieferte für
`guard_urlaub_edit` ein Delta von **879** statt der erwarteten **~793**. Das Ergebnis der Query sah
für sich genommen völlig glaubwürdig aus („alle fünf Trigger weichen ab") — **nur der verfehlte
Kontrollwert verriet, dass die Messung selbst kaputt war.** Ohne ihn hätten wir vier Trigger
„saniert", die nie ein Problem hatten.

### Muster: Cross-Engine-Normalisierung (die Falle dahinter)

> **Niemals zwei Werte vergleichen, die von zwei verschiedenen Engines normalisiert wurden.**

Die kaputte Query verglich die **live-Seite (von Postgres normalisiert)** gegen die **repo-Seite
(von Python normalisiert)**. Beide benutzten `\s+` — aber `\s` bedeutet nicht dasselbe:

| Engine | `\s` matcht |
|---|---|
| Python | ASCII-Whitespace **und Unicode-Whitespace** (U+00A0 usw.) |
| Postgres | `[[:space:]]` — **nur ASCII** |

Enthält der Text ein geschütztes Leerzeichen, kollabiert Python es mit, Postgres nicht. **Gleicher
Text, andere Länge, anderer MD5.** Lokal reproduziert: derselbe 8-Zeilen-Body ergibt 120 Zeichen
(Python) vs. 132 (Postgres).

**Und das ist hier kein Laborfall:** Die Trigger wurden per **Copy-Paste aus dem Chat** in den
SQL-Editor deployed — genau dabei entstehen unsichtbare Unicode-Leerzeichen in der Einrückung.

**Regel:** Beide Seiten eines Vergleichs durch **dieselbe** Engine schicken. Geht das nicht,
die Zeichenklasse **explizit** ausschreiben (`[ \t\n\r\f\v]`) statt `\s` zu vertrauen — und im
Zweifel vorher zählen, ob überhaupt Nicht-ASCII-Whitespace im Text steckt.

### `sql/` im main-Checkout ist eine geladene Waffe

> **Niemals einen ungepushten Arbeitsstand in `sql/` liegen lassen.**
> Work in Progress gehört nach `docs/wip/` oder in einen Branch.

**Grund:** Sebastian kopiert SQL **direkt aus `C:\repos\epkolar-app\sql\`** in den Supabase-Editor
und führt es aus. Was dort liegt, ist damit potenziell **live** — auch ein Entwurf, auch ein
halbfertiger Stand, auch eine Datei, die „nur zum Draufschauen" gedacht war. Zwischen „ich lege das
mal ab" und „das läuft auf der Produktionsdatenbank" liegt kein Gate.

Konkret passiert am 14.07.2026: `STEMPEL_TERMINAL_v2.sql` lag zwischen zwei Commits mit einem
**aktiven** `CREATE OR REPLACE guard_urlaub_edit()` in `sql/` — aufgebaut auf der unvollständigen
Rekonstruktion. Wäre sie in diesem Fenster ausgeführt worden, hätte sie ~800 Zeichen Live-Logik
gelöscht. (Sie wurde es nachweislich nicht — kein Repo-Body passt zum Live-Stand.)

**Praktisch heißt das:** Gefährliche Abschnitte werden **auskommentiert**, nicht „später noch
scharf gemacht". Eine Datei in `sql/` muss zu jedem Zeitpunkt gefahrlos ausführbar sein.

**Warum das eine harte Regel ist — 14.07.2026, um Haaresbreite:**
`sql/security_triggers_LIVE_v3911.sql` gab sich als Live-Stand von `guard_urlaub_edit()` aus. Der
Vergleich ergab: **Live 1746 Zeichen normalisiert, Repo-Datei 953.** Es fehlten ~800 Zeichen echter
Logik. Ein `CREATE OR REPLACE` auf dieser Basis (in `STEMPEL_TERMINAL_v2.sql` bereits vorbereitet)
hätte sie **kommentarlos gelöscht** — kein Fehler, kein Rollback, keine Warnung. Die
Urlaubs-Absicherung wäre still um Logik ärmer gewesen, die niemand mehr kennt.

Der Unterschied zum Boot-Crash desselben Tages: Den hätte ein Browser in fünf Sekunden gefunden.
**Diesen hier hätte nie jemand gefunden.**

## Hart nicht anfassen

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Writes: nur Sebastian via Supabase-SQL-Editor (`jiggujpruejkaomgxarp`). Plugin zeigt auf falsche Org. SQ.push-DELETE/POST/PUT durch die App ist OK (das ist die normale Offline-Queue).
- Diagnose-Aufträge sind strikt read-only. Keine selbst-initiierten Fixes.
