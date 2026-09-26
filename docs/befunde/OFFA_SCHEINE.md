# OFFA-Hinweis: die Bedingung ist gemessen — die Scheine sind es NICHT

**Auftrag:** herausfinden, wie der OFFA-Hinweis zustande kommt, und die
betroffenen Arbeitsscheine mit Namen auf den Tisch legen.

**Ergebnis in einem Satz:** Die Bedingung im Quelltext ist vollständig
gemessen (Abschnitt 2). Die betroffenen Scheine sind **NICHT GEMESSEN** —
dieser Lauf hat **keinen lesenden Zugang zu den Zeilen** der Tabelle
`arbeitsscheine` bekommen. Eine Zahl wird deshalb **nicht genannt**
(Abschnitt 5 zeigt den Nachweis, dass „null Scheine" hier keine Aussage wäre).

**Was dieser Lauf angefasst hat:** nur diese Datei. `index.html` wurde nicht
geändert. An der Datenbank lief ausschließlich **GET** — kein INSERT/UPDATE/
DELETE, kein DDL. Kein Browser, kein Playwright.

## 0. Messgrundlage

| Was | Stand |
|---|---|
| `index.html` beim Messen | 3 642 306 Zeichen, md5 `3edb30c2e3c895884c87ec3890e721cf` |
| `APP_VERSION` | `3.9.943-supabase` |
| Abtaster | `scripts/code_scan.py`, **Eichung bestanden: 22 von 22** in jedem Lauf |
| Ziel-DB | `jiggujpruejkaomgxarp.supabase.co` |
| Messdatum | 26.09.2026 |

Kennzeichnung: **GEMESSEN (Code)** = mit `code_scan` im Quelltext gelesen ·
**GEMESSEN (DB)** = echte Anfrage gegen die laufende Datenbank ·
**AUS DATEI** = steht in einer Repo-Datei, sagt nichts über live ·
**SCHLUSS** = Folgerung · **NICHT GEMESSEN** = offen und benannt.

Zeilennummern gelten gegen den oben genannten Stand. Die Datei wird in dieser
Sitzung von anderen Läufen bearbeitet — im Zweifel über den **Ankertext**
suchen, nicht über die Zeilennummer.

---

## 1. Es gibt DREI OFFA-Zahlen, nicht eine — GEMESSEN (Code)

Das ist der erste Befund, und er ist wichtig, weil „der OFFA-Hinweis" in der
App nicht eindeutig ist. Drei verschiedene Stellen zählen Arbeitsscheine und
melden etwas über OFFA/Juprowa — mit **drei verschiedenen Bedingungen**:

| # | Anzeige | Zeile | Bedingung je Schein | nennt die Scheine? |
|---|---|---|---|---|
| **A** | Banner in der AS-Liste: „⚠ N offene(r) Schein(e) evtl. in OFFA abgeschlossen — bitte in OFFA prüfen (kein Feed-Update seit >7 Tagen trotz Pull; die App ändert den Status NICHT selbst)." | **11417** | `_isOffaVerwaist` (Abschnitt 2) | **NEIN** — kein `onClick`, kein Filterwert, keine Liste |
| **B** | Chef-Sorgenkind-Kachel: „Juprowa Push-Stau: N" | **24421** / Anzeige **24646–24648** | `push_pending===true \|\| push_pending==='true'` | **ja** — Klick setzt `window.__asFilter='push_pending'`, der Listenfilter kennt diesen Wert (Zeile **11000**) |
| **C** | KPI-Kachel „Push ausstehend" im Juprowa-Bereich | **14422** | `a.push_pending && a.juprowa_id` | nein (reine Zahl) |

**SCHLUSS:** Der Hinweis, der warnt **ohne die Scheine zu nennen**, ist **A**.
B ist anklickbar und filtert die Liste, C ist eine reine Kennzahl.

Der Auftrag sprach von „Scheine wurden nicht übertragen". Wörtlich trifft das
**B/C** (`push_pending` = lokal geändert, noch nicht nach OFFA gepusht).
„Nennt sie aber nicht" trifft **A**. Unten ist **A** ausgemessen, weil das
die Stelle ohne Namensliste ist; die Abfragen für B und C stehen in
Abschnitt 4 daneben, weil die Zahl davon abhängt, welche der drei gemeint war.

### Nebenbefund zu A (GEMESSEN, Code)

Das Banner A hat **keinen** Klickpfad und es gibt **keinen** Filterwert
`verwaist` in der Statusliste (Zeile 11000 kennt nur `alle`, `offen_bearb`,
`fertig`, `push_pending` und einen Status-Gleichheitsfall). Wer das Banner
sieht, hat in der App **keine** Möglichkeit, die gemeinten Scheine anzeigen zu
lassen. Der einzelne Schein trägt zwar im Formularkopf ein Abzeichen
„⚠ in OFFA prüfen" (Zeile **11669**, `_isVerwaist(form)`) — aber man muss ihn
schon geöffnet haben, um es zu sehen.

---

## 2. Die Bedingung von Hinweis A — GEMESSEN (Code)

### 2.1 Die reine Funktion, Zeilen 4003–4015

```js
var OFFA_VERWAIST_TAGE=7;
/* v3.9.728 #18a: verwaister OFFA-Schein — juprowa-gebunden + offen (AS_GRP_OFFEN) + juprowa_sync_at aelter
   als OFFA_VERWAIST_TAGE, OBWOHL nach dem sync ein Pull lief (der Schein haette aktualisiert werden koennen,
   wurde aber nicht -> ServicePad liefert in OFFA abgeschlossene Scheine nicht mehr im Feed). KEINE Auto-
   Statusaenderung (die App erfindet keinen Status) — nur ein Pruef-Badge. PURE, testbar. */
function _isOffaVerwaist(s,lastPullMs,nowMs){
  if(!s||!s.juprowa_id||!s.juprowa_sync_at)return false;
  if(AS_GRP_OFFEN.indexOf(s.scheinstatus)<0)return false;
  var syncMs=new Date(s.juprowa_sync_at).getTime(); if(!syncMs)return false;
  if((nowMs-syncMs)<=OFFA_VERWAIST_TAGE*864e5)return false;
  return !!(lastPullMs&&lastPullMs>syncMs);
}
```

### 2.2 Die fünf Teilbedingungen, einzeln

| # | Bedingung | Feld | wo definiert |
|---|---|---|---|
| 1 | `juprowa_id` gesetzt (truthy) | `arbeitsscheine.juprowa_id` | Z 4009 |
| 2 | `juprowa_sync_at` gesetzt (truthy, nicht `""`) | `arbeitsscheine.juprowa_sync_at` | Z 4009 |
| 3 | `scheinstatus` ∈ **`AS_GRP_OFFEN`** = `["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"]` | `arbeitsscheine.scheinstatus` | Z 4010, Definition Z **3699** |
| 4 | `new Date(juprowa_sync_at).getTime()` ist **parsbar und ≠ 0** | — | Z 4011 |
| 5 | `jetzt − syncMs` **> 7 Tage** (`OFFA_VERWAIST_TAGE*864e5`, strikt größer) | — | Z 4012, Konstante Z **4003** |
| 6 | `lastPullMs` gesetzt **und** `lastPullMs > syncMs` | **nicht in der DB** — siehe 2.3 | Z 4013 |

Die **Zahl** im Banner ist `_verwaisteN`, Zeile **10804**:

```js
const _lastJupPull=(typeof window!=='undefined'&&(window.__lastJuprowaPull||parseInt(localStorage.getItem("epk_last_juprowa_pull"),10)))||0;   // Z 10802
const _isVerwaist=(a)=>{try{return !!(window._isOffaVerwaist&&window._isOffaVerwaist(a,_lastJupPull,Date.now()));}catch(e){return false;}};      // Z 10803
const _verwaisteN=(arbeitsscheine||[]).filter(_isVerwaist).length;                                                                              // Z 10804
```

Sichtbar wird das Banner nur bei `(_verwaisteN>0 && canSync)` (Zeile 11417) und
nur im Unterreiter `sub==="liste"`. `canSync` ist Zeile **10799**:
`curUser.role` ∈ `admin | projektleiter | buero`. Ein Monteur sieht den Hinweis
also nie, egal wie viele Scheine betroffen sind.

### 2.3 Teilbedingung 6 ist GERÄTELOKAL — und damit nicht aus der DB messbar

`lastPullMs` kommt aus `window.__lastJuprowaPull` bzw. aus
`localStorage["epk_last_juprowa_pull"]`. Gesetzt wird der Wert am Erfolgs-Ende
des Juprowa-Pulls, Zeile **3977**:

```js
try{var _jpms=Date.now();window.__lastJuprowaPull=_jpms;localStorage.setItem("epk_last_juprowa_pull",String(_jpms));}catch(e){...}
```

**SCHLUSS, mit Folgen für jede Messung:**

* Die Zahl im Banner ist **pro Gerät und pro Browserprofil verschieden**. Ein
  frisch installiertes Gerät (leerer `localStorage`, noch kein Pull in dieser
  Sitzung) hat `lastPullMs === 0` → Bedingung 6 ist falsch → das Banner zeigt
  **0**, egal wie alt die Scheine sind.
* Aus der Datenbank lassen sich nur die Bedingungen **1–5** messen. Das Ergebnis
  davon ist eine **Obermenge** der Banner-Zahl. Auf einem Gerät, das regelmäßig
  pullt, fallen Obermenge und Banner-Zahl zusammen, weil `lastPull` (heute)
  dann zwangsläufig größer ist als ein `sync_at`, das älter als 7 Tage ist.
* Wer die Banner-Zahl **exakt** nachstellen will, braucht zusätzlich den
  `epk_last_juprowa_pull` **des betroffenen Geräts**. Das ist hier **NICHT
  GEMESSEN**.

---

## 3. Das Schema — GEMESSEN (DB)

Mit dem ANON-Schlüssel aus dem öffentlich ausgelieferten Bündel (`index.html`,
`SUPABASE_KEY`, JWT-Rolle **`anon`**, geprüft) gegen PostgREST, **nur GET**.
Spaltenexistenz geht so, auch ohne Zeilen zu sehen: `?select=<spalte>` gibt
HTTP 400 `42703`, wenn es die Spalte nicht gibt.

**KÖDER:** `?select=DIESE_SPALTE_GIBT_ES_NICHT_koeder` → HTTP 400 `42703`, und
`DIESE_TABELLE_GIBT_ES_NICHT_koeder` → HTTP 404 `PGRST205`. Die Probe kann
Abwesenheit also wirklich erkennen; ohne diesen Nachweis wäre jedes
„vorhanden" unten wertlos.

| Spalte | vorhanden | Typ (Probe `?spalte=gt.ZZ_kein_datum_ZZ`) |
|---|---|---|
| `nummer` | ja | Textfamilie (200) |
| `kund_nr` | ja | Textfamilie |
| `kund_name` | ja | Textfamilie |
| `scheinstatus` | ja | Textfamilie |
| `juprowa_id` | ja | **integer** (400 `22P02 invalid input syntax for type integer`) |
| `juprowa_sync_at` | ja | **timestamp with time zone** (400 `22007`) |
| `aufg_zeit` | ja | Textfamilie (200) |
| `termin_bestaetigt` | ja | Textfamilie (200) |
| `abschluss_datum` | ja | Textfamilie (200) |
| `created_at` | ja | **timestamp with time zone** (400 `22007`) |
| `updated_at` | ja | timestamptz-Familie |
| `push_pending`, `last_push_at` | ja | — |
| `kundName`, `datum`, `aufg_datum`, `aufgenommen_am`, `erfasst_am` | **nein** | je 400 `42703` |

**Merke für die Altersspalte:** ein reines „Erfassungsdatum" gibt es nicht.
Für das Alter taugen `created_at` (echter Zeitstempel) und `aufg_zeit` /
`termin_bestaetigt` (Text, vom Mapper `_mapArbeitsschein` auf `aufgZeit` /
`terminBestaetigt` gelegt, Zeile **2046**).

---

## 4. Die Abfragen, die die Scheine nennen würden

Fertig zum Ausführen, sobald ein lesender Zugang da ist (Service-Role,
Supabase-MCP nach OAuth, oder SQL-Editor). **Nur SELECT.**

### 4.1 Hinweis A — verwaiste OFFA-Scheine (Bedingungen 1–5)

```sql
select nummer, kund_nr, kund_name, juprowa_id, juprowa_sync_at,
       created_at, aufg_zeit, termin_bestaetigt, scheinstatus
from public.arbeitsscheine
where juprowa_id is not null
  and juprowa_sync_at is not null
  and scheinstatus in ('aufgenommen','freigegeben','in_bearbeitung','aufgeschoben')
  and juprowa_sync_at < now() - interval '7 days'
order by juprowa_sync_at asc;
```

Als PostgREST-GET (Stichtag 26.09.2026 → Grenze 19.09.2026):

```
GET /rest/v1/arbeitsscheine
  ?select=nummer,kund_nr,kund_name,juprowa_id,juprowa_sync_at,created_at,aufg_zeit,termin_bestaetigt,scheinstatus
  &juprowa_id=not.is.null
  &scheinstatus=in.(aufgenommen,freigegeben,in_bearbeitung,aufgeschoben)
  &juprowa_sync_at=lt.2026-09-19T00:00:00Z
  &order=juprowa_sync_at.asc
```

Das Ergebnis ist die **Obermenge**; Bedingung 6 (`lastPull > sync_at`) muss am
Gerät geprüft werden. Bedingung 4 (`getTime()` ≠ 0) fällt in SQL weg, weil die
Spalte `timestamptz` ist — ein unparsbarer Wert kann dort nicht stehen.

### 4.2 Hinweis B — Push-Stau

```sql
select nummer, kund_nr, kund_name, juprowa_id, push_pending, push_error,
       last_push_at, local_updated_at, scheinstatus
from public.arbeitsscheine
where push_pending is true
order by local_updated_at asc nulls last;
```

Achtung: der Code prüft `push_pending===true || push_pending==='true'` — er
rechnet also mit einem **Text** `'true'`. Ob die Spalte `boolean` oder `text`
ist, ist hier **NICHT GEMESSEN** (die Typprobe braucht dafür einen Wert, den
`gt.ZZ…` bei `boolean` nicht liefert). Im Zweifel
`where push_pending::text in ('true','t')`.

### 4.3 Hinweis C — Push ausstehend

wie 4.2, zusätzlich `and juprowa_id is not null`.

---

## 5. KÖDER-NACHWEIS: warum hier keine Zahl steht

Die Regel lautet: eine leere Grundgesamtheit ist kein Ergebnis. Genau der Fall
ist eingetreten, und der Köder hat ihn aufgedeckt.

| Probe | Antwort |
|---|---|
| **Bedingungsabfrage** aus 4.1 (anon) | HTTP **200**, Rumpf `[]` |
| **KÖDER 1 — dieselbe Abfrage OHNE jede Einschränkung**: `arbeitsscheine?select=nummer&limit=5` | HTTP **200**, Rumpf `[]` |
| `arbeitsscheine?select=id&limit=3` mit `Prefer: count=exact` | HTTP 200, `Content-Range: */0` |
| **KÖDER 2 — sieht dieser Schlüssel IRGENDWO Zeilen?** `material_catalogs`, `projects`, `users`, `workers`, `plz_geo`, `fahrzeuge`, `tickets`, `worker_projects`, `dispo_blocks`, `activity_log` | **alle** HTTP 200, `Content-Range: */0`, **0 Zeilen** |
| KÖDER 3 — erfundene Spalte / erfundene Tabelle | 400 `42703` / 404 `PGRST205` — der Anfrageweg funktioniert und meldet Fehler sauber |

**SCHLUSS:** Die `[]` der Bedingungsabfrage bedeutet **nicht** „null betroffene
Scheine". Sie bedeutet „dieser Schlüssel sieht in *keiner* Tabelle *irgendeine*
Zeile" — RLS lässt `anon` keine Zeile durch. Der Messweg liefert also gar
nichts und **kann** deshalb auch nichts finden. Eine Zahl aus dieser Messung
wäre erfunden, und sie wäre die gefährliche Sorte: ein Zähler, der nichts
findet, meldet ein grünes Ergebnis.

### Welche Lesewege geprüft und verworfen wurden

| Weg | Befund |
|---|---|
| ANON-Schlüssel aus `index.html` | **benutzt** — reicht für Schema, nicht für Zeilen (RLS) |
| `$env:SUPABASE_SERVICE_ROLE` (von `scripts/db_migrate_all.ps1` erwartet) | **nicht gesetzt** (Umgebung geprüft) |
| Supabase-CC-Plugin (MCP) | **nicht angemeldet** — `~/.claude/mcp-needs-auth-cache.json` führt `plugin:supabase:supabase`; die Anmeldung ist eine Sebastian-Aktion |
| `.env`-Datei im Repo | existiert nicht |
| `supabase/migrations/` | existiert nicht (nur `supabase/functions/`) |
| anon-freigegebene RPCs (`sql/`-Suche nach `TO anon`) | nur `auth_role`, `login_lookup`, `login_username_lookup`, `is_hr`, `portal_fetch(text)`, `portal_submit_defect`, `portal_confirm_abnahme`, `stempel_terminal_stempel` — **keiner** liefert Arbeitsscheine ohne Portal-Token |
| Anmeldung als echter Benutzer | **nicht versucht** — dafür bräuchte es Zugangsdaten; danach zu suchen ist in dieser Umgebung gesperrt und wurde nicht umgangen |
| Browser/Playwright | vom Auftrag **verboten** |

**Der kürzeste Weg zur Zahl:** Sebastian meldet den Supabase-MCP an (OAuth),
oder setzt `SUPABASE_SERVICE_ROLE` für einen Lauf, oder fährt 4.1 selbst im
SQL-Editor. Die Abfrage steht fertig oben.

---

## 6. NICHT GEMESSEN

1. **Die betroffenen Scheine selbst.** Nummer, Kunde, `juprowa_sync_at`,
   Alter, Status — **keine einzige Zeile gelesen**. Kein lesender Zugang
   (Abschnitt 5).
2. **Die Anzahl.** Weder für A noch für B noch für C. Die Rede war von
   **drei** — diese Zahl ist in diesem Lauf **weder bestätigt noch
   widerlegt**. Sie wird hier auch nicht wiederholt, damit sie nicht durch
   Abschreiben zur Messung wird. Mögliche Gründe für eine Abweichung, falls
   die Abfrage später eine andere Zahl liefert:
   * **andere der drei Bedingungen gemeint** — A (verwaist, >7 Tage) und B
     (`push_pending`) sind völlig verschiedene Mengen und können gleichzeitig
     verschiedene Zahlen zeigen;
   * **Gerätestand** — A hängt an `epk_last_juprowa_pull` des Geräts
     (Abschnitt 2.3); ein anderes Gerät zeigt eine andere Zahl;
   * **Zeitpunkt** — die 7-Tage-Grenze wandert täglich; ein Schein, der heute
     zählt, zählte gestern noch nicht;
   * **Rolle** — als Monteur ist das Banner unsichtbar (`canSync`);
   * **lokaler Stand statt DB** — A/B/C zählen über das React-Array
     `arbeitsscheine`, also über den **zuletzt geladenen** Stand inklusive
     lokaler, noch nicht gepushter Änderungen. Die DB-Abfrage aus 4.1 zählt
     den Serverstand. Die beiden müssen nicht übereinstimmen.
3. **Der Typ von `push_pending`** (`boolean` vs. `text`) — siehe 4.2.
4. **Ob der Live-Stand der Tabelle dem Schema aus Abschnitt 3 entspricht,
   über die Spaltenexistenz hinaus** — Policies, Primärschlüssel,
   Vorgabewerte und Trigger sind mit `anon` nicht lesbar.
5. **Ob `_isOffaVerwaist` live so läuft wie in Zeile 4008.** Gemessen ist der
   Quelltext im Arbeitsbaum. Was auf GitHub Pages ausgeliefert wird, ist
   **AUS DATEI** abgeleitet, nicht gemessen.
6. **`tests/test_offa_verwaist_v728.py`** existiert (AUS DATEI) und wurde in
   diesem Lauf **nicht ausgeführt** — der Auftrag verbot, bestehende
   Prüfungen anzufassen; ausgeführt habe ich sie auch nicht.
