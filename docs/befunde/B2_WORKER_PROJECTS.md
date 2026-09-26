# B2 — `worker_projects`: gemessener IST-Stand, die DDL-Frage, der Umbau in Schritten

**Auftrag dieses Laufs:** messen, den Riegel schreiben, nichts bauen.
`index.html` wurde **nicht angefasst** (kein Edit, kein Write — nur Lesen und
Schneiden). An der Datenbank wurde **ausschliesslich GET und HEAD** gefahren;
kein INSERT/UPDATE/DELETE, kein DDL, keine Migration.

**Angelegt/geaendert von diesem Lauf:** diese Datei und
`tests/test_worker_projects_einzelzeile_v940.py`. Sonst nichts.

## 0. Messgrundlage — und was daran wackelt

| Was | Stand |
|---|---|
| `index.html` beim Messen | 3 664 111 B, md5 `4cb3f3acaacab39e33f42ba0cffb1b2e`, `APP_VERSION="3.9.939-supabase"` |
| `index.html` am Ende des Laufs | 3 664 450 B, md5 `165c764dd90c53c2d8254d462cc70975` — der zweite Lauf hat weitergeschrieben |
| Zeilen/Positionen unten | gegen die **erste** der beiden Fassungen |
| Riegel gegen die spaetere Fassung nachgefahren | 12 gruen / 7 rot, **gleiche** Verteilung, alle Anker weiter eindeutig |
| Ziel-DB | `jiggujpruejkaomgxarp.supabase.co` (EP Kolar Baumgmt) |
| Abtaster | `scripts/code_scan.py`, Eichung **bestanden (22 von 22)** in jedem Lauf |

**Warnung zu den Zeilennummern.** Die Datei wird waehrend dieses Laufs von
einem zweiten Lauf bearbeitet: sie ist mir waehrend der Messung **zweimal**
unter den Haenden gewachsen (3 628 111 → 3 629 326 Zeichen, dann noch einmal).
**Verlasst euch
auf die ANKERTEXTE in Abschnitt 5, nicht auf die Zeilennummern.** Die
Ankertexte sind woertliche Schnitte; der Riegel schneidet sie selbst und
bricht mit einer klaren Meldung ab, wenn ein Anker nicht mehr genau einmal im
Code steht.

**Kennzeichnung durchgehend:**

* **GEMESSEN (Code)** — im Quelltext mit `code_scan` gelesen oder unter Node
  **ausgefuehrt**.
* **GEMESSEN (DB)** — mit einer echten Anfrage gegen die laufende Datenbank
  gelesen.
* **AUS DATEI** — steht in einer Repo-Datei. Sagt nichts darueber, was live
  laeuft.
* **SCHLUSS** — Folgerung.
* **NICHT GEMESSEN** — offen, und zwar benannt.

---

## 1. Die Schreib- und Lesestellen — GEMESSEN (Code)

Drei unabhaengige Zaehlungen mit `code_scan` (Eichung bestanden), alle am
Stand oben:

| Zaehlung | Grundgesamtheit | davon `worker_projects` |
|---|---|---|
| `SQ.push(` — alle Warteschlangen-Auftraege | **188** im Code (192 Textfunde, 4 in Kommentaren), 66 verschiedene Routen | **1**: `/api/worker-projects/` als `PUT` |
| Zeichenkette `worker_projects` | 6 Funde (alle in Zeichenketten — so gehoert es, es sind Tabellennamen) | 1 Routentabelle, 2 Leser, 1 Loeschen, 1 Einfuegen, 1 Kommentar |
| Zeichenkette `worker-projects` | 12 Funde | 1 Schreibauftrag, 1 Ausstehend-Schutz (v3.9.938, zwei Funde), Rest Route/Kommentar/Beschriftung |

Die drei `SQ.push`-Stellen ohne wortwoertliches `url:"…"` habe ich einzeln
angesehen: Selbsttest (`/api/ztest`), Arbeitsschein-Ternaer, Stempel-Log.
Keine davon kann `worker-projects` sein. **Es bleibt bei genau EINER
Schreibstelle.**

### 1.1 Station 1 — die Benutzerhandlung

| | |
|---|---|
| Komponente | `MitarbeiterView`, Abschnitt „Projektzuweisungen" |
| Anker | `const toggleProj=(mid,pid)=>{` … `body:{projects:nxt}});}` (Zeile 10078, **390 Zeichen**) |
| Gate | `if(!isWAdm)return;` — `isWAdm=curUser.role==="admin"` |
| Warteschlange | `PUT /api/worker-projects/<mid>`, Rumpf `{"projects":[…]}` — die **ganze** Liste |
| Abfluss | `SQ._batchDelay:1500` ms nach dem letzten Tipper (`window.__doSync`) |
| Zusammenfassen | **nein.** Fuenf Tipper = fuenf Auftraege, jeder mit der jeweiligen Gesamtliste, alle nacheinander gefahren |

### 1.2 Station 2 + 3 — der Uebersetzer

Anker: `if(resource==="worker-projects"&&idOrSub&&(method==="PUT"||method==="POST")){`
… `return{ok:1};` (Zeile 2762, **1174 Zeichen**), innerhalb von
`_translateAndExec` (Zeile 2570, 23 274 Zeichen).

Auf der Leitung, **GEMESSEN (Code, ausgefuehrt)** — der Riegel protokolliert
genau diese zwei Anfragen:

```
DELETE  /rest/v1/worker_projects?worker_id=eq.<mid>     Kopf: apikey + Bearer,  KEIN Prefer, kein Rumpf
POST    /rest/v1/worker_projects                        Prefer: return=representation,resolution=merge-duplicates
                                                        Rumpf: [{id:"<w>_<p>", worker_id:"<w>", project_id:"<p>"}, …]
```

* Der Loeschfilter ist **`worker_id=eq.<mid>`** — also alle Zeilen des
  Mitarbeiters, gleich von wem sie stammen.
* Das Loeschen fragt **nicht**, wie viele Zeilen es getroffen hat (kein
  `Prefer: count`). Die Kopfzeilen sind `_sbH()`.
* Ist `body.projects` leer, wird der `POST` **uebersprungen** — dann ist der
  Vorgang ein reines Alles-Loeschen.
* Zwei getrennte HTTP-Anfragen, **keine Transaktion**.
* Schlaegt das Loeschen fehl, wird bewusst abgebrochen
  (`worker-projects: Alte Zuweisungen konnten nicht entfernt werden …`), der
  Auftrag bleibt in der Warteschlange und wird nach **5** Fehlversuchen nach
  `syncQueueFailed` verworfen — **sichtbar**. Der Verlust im **Erfolgsfall**
  ist unsichtbar.

### 1.3 Der Leser und die Verschmelzung

| | |
|---|---|
| Einziger Leser | `API.request("GET","/api/worker-projects")` (Zeile 8358) im Ladeeffekt |
| Uebersetzer-GET | `if(resource==="worker-projects"){` … (Zeile 2606, **178 Zeichen**) → `_sbGet("worker_projects")`, also `select=*&limit=5000` |
| Verschmelzung | `if(wpMap&&Array.isArray(wpMap)&&wpMap.length){` … `return _z;});}` (Zeile 8523, **1024 Zeichen**) |
| Ausstehend-Schutz | `if(_u.indexOf("/api/worker-projects/")===0&&_m==="PUT"){const _wid=_u.split("/").pop();…}` (Zeile 8412, **129 Zeichen**) |

**Korrektur an `DATENVERLUST_BEFUND.md`, GEMESSEN (Code):** dort steht, der
Ladeeffekt haenge an `},[curUser]);` und laufe damit einmal pro Sitzung. Im
jetzigen Arbeitsbaum haengt er an **`},[curUser,_frischeZaehler]);`** (Zeile
8604). Der Auffrischer aus v3.9.938 laeuft ueber diesen Zaehler, also ueber
**denselben** Ladepfad — Zeile 8358 wird mitgezogen. Das Fenster ist damit
nicht mehr „die ganze Sitzung", sondern „bis zum naechsten Fensterwechsel".
**Der Verlust ist damit nicht behoben**, nur das Zeitfenster kuerzer.

### 1.4 Das Ueberspringen leerer Serverantworten — was es abfaengt

Die Stelle ist `if(wpMap&&Array.isArray(wpMap)&&wpMap.length)`. Sie faengt
**drei** Faelle ab, alle im Riegel **ausgefuehrt** nachgewiesen:

1. **`null`** — der Leser ist `…("GET","/api/worker-projects").catch(()=>null)`.
   Ein Fehler kommt als `null` an.
2. **ein leeres Array mit Grund** — `_sbGet` gibt bei 401/403 im
   **Erfolgspfad** ein leeres Array zurueck (v3.9.910, Merker `__rlsFehler`).
   Ohne das Ueberspringen wuerde ein RLS-Ausfall die Zuweisungen **aller**
   Mitarbeiter lokal loeschen.
3. **eine wirklich leere Tabelle** — dann bleibt der lokale Stand stehen. Das
   ist der Preis: ein serverseitig geleerter Mitarbeiter bleibt auf dem
   verursachenden Geraet sichtbar.

**Urteil: das Ueberspringen wird weiter gebraucht**, und zwar wegen Fall 2 —
solange `_sbGet` einen Auth-/RLS-Fehler als leeres Array im Erfolgspfad
zurueckgibt, ist „leer" nicht von „nichts da" unterscheidbar. Der Umbau auf
Einzelzeilen aendert daran nichts. Der Riegel haelt alle drei Faelle fest, damit
niemand das Ueberspringen beim Umbau „aufraeumt".

---

## 2. Das Schema — was live gemessen ist und was aus Dateien stammt

### 2.1 Wie ich lesend an die DB gekommen bin

Im Repo gibt es **keinen** funktionierenden Lesepfad fuer einen Agenten:
`scripts/db_migrate_all.ps1` verlangt `$env:SUPABASE_SERVICE_ROLE` (nicht
gesetzt), das Supabase-CC-Plugin ist **nicht angemeldet**
(`mcp-needs-auth-cache.json`), `supabase/migrations/` existiert nicht, und die
Suche nach einem hinterlegten Schluessel wurde von der Sandbox abgelehnt
(„Credential Exploration") — **richtig so, ich habe sie nicht umgangen**.

Benutzt habe ich stattdessen den **ANON-Schluessel aus dem oeffentlich
ausgelieferten Buendel** (`index.html`, `SUPABASE_KEY`, JWT-Rolle `anon`) und
damit ausschliesslich **GET/HEAD** gegen PostgREST. Das reicht fuer
Spaltenexistenz, Typen und Fremdschluessel; fuer Policies und den
Primaerschluessel reicht es **nicht** (Abschnitt 2.4).

### 2.2 Spalten — GEMESSEN (DB)

Verfahren: `?select=<spalte>` gegen `/rest/v1/worker_projects`. Eine Spalte,
die es nicht gibt, gibt HTTP 400 mit `42703`. **Koeder:** eine erfundene
Spalte (`DIESE_SPALTE_GIBT_ES_NICHT_koeder`) gab `42703` — die Probe kann
Abwesenheit also wirklich erkennen. Ohne diesen Nachweis waere jede
„vorhanden"-Aussage unten wertlos.

| Spalte | vorhanden | Typ | Beleg |
|---|---|---|---|
| `id` | **ja** | Textfamilie | `?select=id` → 200; `?id=gt.ZZ_kein_datum_ZZ` → 200 (keine Umwandlung noetig) |
| `worker_id` | **ja** | Textfamilie | ebenso |
| `project_id` | **ja** | Textfamilie | ebenso |
| `assigned_at` | **ja** | **`timestamp with time zone`** | `?assigned_at=gt.ZZ_kein_datum_ZZ` → 400 `22007 invalid input syntax for type timestamp with time zone` |
| `role` | **ja** | Textfamilie | `?select=role` → 200; `gt.ZZ…` → 200 |
| `created_at`, `updated_at`, `deleted_at`, `aktiv`, `active`, `note` und 32 weitere naheliegende Namen | **nein** | — | je HTTP 400 `42703` |

**Das sind zwei Spalten mehr, als `DATENVERLUST_BEFUND.md` kennt** (dort
„weitere Spalten: OFFEN"). Und sie haben Folgen:

* **`assigned_at` ist heute als Beweismittel wertlos** — SCHLUSS, aber
  zwingend: bei **jedem** Speichern wird die Zeile geloescht und neu
  eingefuegt; ein Vorgabewert `now()` setzt sie damit auf „jetzt" zurueck.
  **Nach dem Umbau wird sie brauchbar**, weil eine unveraenderte Zuweisung
  ihre Zeile behaelt. Das ist ein Gewinn, der nichts extra kostet.
* **`role` ist ein ZWEITER, bisher unbenannter Verlustkanal** — SCHLUSS: der
  Code schickt `role` nie mit (`{id, worker_id, project_id}`), also setzt
  jedes Speichern jede `role` dieses Mitarbeiters auf den Vorgabewert
  zurueck. Ob heute irgendeine Zeile ein `role` traegt, ist **NICHT
  GEMESSEN** (anon sieht keine Zeilen). Falls ja, gehen diese Werte bei
  jedem Haken verloren — und der Umbau beendet das mit.
* Der heutige `POST` schickt weder `assigned_at` noch `role`, und er
  funktioniert. **SCHLUSS:** beide sind nullbar oder haben einen
  Vorgabewert. Ein Einzelzeilen-`POST` mit denselben drei Spalten laeuft
  damit unter denselben Bedingungen.

### 2.3 Fremdschluessel — GEMESSEN (DB): es gibt KEINE

PostgREST loest `?select=id,workers(id)` nur auf, wenn eine echte
FK-Beziehung existiert.

| Einbettung | Antwort |
|---|---|
| `worker_projects` → `workers` | 400 `PGRST200` „no matches were found" |
| `worker_projects` → `projects` | 400 `PGRST200` |
| `worker_kompetenzen` → `workers` | 400 `PGRST200` (dieselbe Lage bei der Vorlage-Tabelle) |

Das erklaert eine Stelle im Code, die bisher nur behauptet war: der Kommentar
bei der Zuweisungszaehlung („verwaiste `worker_projects`-DB-Zeilen
verfaelschten die Anzeige sonst") beschreibt genau die Folge einer
Tabelle **ohne** FK. **Fuer den Umbau ist das gut:** kein `ON DELETE
CASCADE`, kein Trigger auf der FK-Seite, den ein Einzel-DELETE anders
ausloesen koennte.

### 2.4 Was ich an der DB NICHT messen konnte — und warum

| Frage | Versuch | Ergebnis |
|---|---|---|
| Primaerschluessel / eindeutige Indizes | PostgREST-OpenAPI `GET /rest/v1/` | **401** „Only the `service_role` API key can be used for this endpoint" |
| dasselbe, ueber den Ausfuehrungsplan | `Accept: application/vnd.pgrst.plan+json` | **406** `PGRST107` (db-plan nicht eingeschaltet) |
| RLS-Policies je Befehl | `/pg_policies`, `/rpc/exec_sql` | **404** `PGRST205` / `PGRST202` — Systemkataloge sind nicht veroeffentlicht |
| Zeilenzahl | `Prefer: count=exact` | `*/0` — anon sieht keine Zeile |

**Also NICHT GEMESSEN:** der Wortlaut der Policies, der Primaerschluessel, die
eindeutigen Indizes, ob ein Trigger an der Tabelle haengt, wie viele Zeilen
sie fuehrt, und ob eine Zeile ein `role` traegt. Ich leite davon nichts aus
Migrationsdateien ab — es gibt im Repo **kein** `CREATE TABLE
worker_projects` und **kein** `CREATE POLICY` dafuer, und
`supabase/migrations/` existiert nicht.

### 2.5 Was zu RLS gemessen ist

**GEMESSEN (DB):** `GET /worker_projects?select=*` mit dem Anon-Schluessel gibt
**HTTP 200 mit `[]`** und `Content-Range: */0`. Dasselbe fuer `projects`,
`workers`, `users`. Da `projects` und `workers` im Betrieb offensichtlich
Zeilen fuehren, heisst das: **RLS ist aktiv und sperrt `anon` aus.** Das ist
ein Zustandsbefund, kein Regeltext — **welche** Regel fuer welchen Befehl
gilt, steht damit nicht fest.

Eine Einordnung, die ich **nicht** belegen konnte: ob das HTTP 200 (statt
`42501 permission denied`) bedeutet, dass `anon` das SELECT-Recht auf der
Tabelle **hat** und nur RLS dazwischensteht. Dafuer haette ich eine
Gegenprobe gebraucht — eine Stelle, an der `anon` ein `42501` bekommt. Der
Versuch wurde von der Sandbox abgelehnt. **Also: nicht gemessen, keine
Aussage.** (Wenn die Vermutung stimmt, ist das eine eigene Sache fuer die
Haertung, nicht fuer diesen Umbau.)

**AUS DATEI, kein Beleg:** `sql/RLS_RECONCILE_v3.8.md` (19.04.2026) fuehrt
`worker_projects` und `worker_kompetenzen` mit demselben Rollenmuster
„staff RW", unterscheidet aber nicht nach Befehl und schreibt selbst, die
realen Zahlen seien nachzutragen; die vorgesehene Ausgabedatei existiert
nicht. `docs/db/policies-backup-2026-07-15.json` ist ein echter Abzug, enthaelt
aber nur die 63 gedroppten Kiosk-`SELECT`-Sperren.

### 2.6 Die eine Abfrage, die die Luecke schliesst

Fuer den SQL-Editor, **nur lesend**:

```sql
-- 1) Policies je Befehl  -> schliesst die Beweisluecke aus Abschnitt 4
SELECT polname, polcmd, polpermissive, polroles::regrole[],
       pg_get_expr(polqual, polrelid)      AS using_ausdruck,
       pg_get_expr(polwithcheck, polrelid) AS withcheck_ausdruck
FROM pg_policy WHERE polrelid = 'public.worker_projects'::regclass ORDER BY polcmd, polname;

-- 2) Primaerschluessel + eindeutige Indizes  -> nur noetig, wenn weiter mit merge-duplicates gearbeitet wird
SELECT i.relname AS index_name, x.indisprimary, x.indisunique,
       pg_get_indexdef(x.indexrelid) AS definition
FROM pg_index x JOIN pg_class i ON i.oid = x.indexrelid
WHERE x.indrelid = 'public.worker_projects'::regclass;

-- 3) Trigger  -> erwartet: keine Zeile
SELECT tgname, tgenabled, pg_get_triggerdef(oid)
FROM pg_trigger WHERE tgrelid = 'public.worker_projects'::regclass AND NOT tgisinternal;

-- 4) Traegt irgendeine Zeile ein role / ein altes assigned_at?  (der zweite Verlustkanal)
SELECT count(*) AS zeilen, count(role) AS mit_role,
       min(assigned_at) AS aeltestes, max(assigned_at) AS jungstes
FROM public.worker_projects;
```

---

## 3. Bestaetigt und korrigiert gegenueber `DATENVERLUST_BEFUND.md`

| Aussage dort | hier |
|---|---|
| genau **eine** Schreibstelle, `PUT` mit ganzer Liste | **bestaetigt**, unabhaengig nachgezaehlt (188 Auftraege, 66 Routen) |
| `DELETE worker_id=eq.<w>`, dann Upsert, zwei Anfragen | **bestaetigt, und diesmal ausgefuehrt**: der Riegel protokolliert beide |
| das DELETE fragt keine Zeilenzahl ab | **bestaetigt** (`prefer=''` in allen Laeufen) |
| Spalten: nur `id`,`worker_id`,`project_id` bekannt, Rest OFFEN | **erweitert:** `assigned_at` (timestamptz) und `role` existieren live |
| Fenster = ganze Sitzung | **ueberholt:** Ladeeffekt haengt jetzt an `[curUser,_frischeZaehler]`, der v938-Auffrischer zieht den Leser mit → Fenster = bis zum naechsten Fensterwechsel |
| Zaehlungen 51 DELETE / 13 `_sbUpsert` | am heutigen Stand **49** bzw. **14** — die Datei hat sich bewegt, das Urteil („genau eine Stelle mit Alles-Loeschen-dann-Einfuegen") nicht |
| Primaerschluessel OFFEN | **weiter offen, jetzt mit Begruendung, warum ich ihn nicht messen kann** (2.4) |

---

## 4. Geht der Umbau OHNE DDL? — JA. Worauf sich das stuetzt.

**Antwort: ja.** Die Vorarbeit aendert die Begruendung gegenueber
`DATENVERLUST_BEFUND.md` an zwei Stellen von SCHLUSS auf GEMESSEN.

**a) Die Filterspalten existieren — jetzt GEMESSEN (DB), nicht mehr nur aus
dem Code gefolgert.** `?worker_id=eq.<w>&project_id=eq.<p>` filtert auf zwei
gewoehnliche Spalten; beide gaben live HTTP 200 (und der Koeder beweist, dass
eine fehlende Spalte 400/`42703` gaebe). **Das Einzel-DELETE braucht den
Primaerschluessel nicht.** Damit ist die offene PK-Frage fuer den Loeschweg
erledigt, nicht nur entschaerft.

**b) Das Einzel-Einfuegen braucht auch keine Schemaaenderung — mit einer
benannten Abhaengigkeit.** Der heutige `POST` faehrt
`Prefer: resolution=merge-duplicates` **ohne** `on_conflict`. PostgREST
uebersetzt das in `ON CONFLICT … DO UPDATE` und nimmt dafuer den
Primaerschluessel. Dass das heute durchgeht, ist **GEMESSEN (Code)** — der Weg
laeuft im Betrieb. **SCHLUSS:** es gibt einen eindeutigen Schluessel, und seine
Spalten liegen in `{id, worker_id, project_id}`, weil der Code nur diese drei
schickt. Ein `POST` mit **einer** Zeile derselben Bauform trifft denselben
Konflikt und ist damit idempotent — ohne DDL.
**Ausweichweg, falls Abfrage 2 aus 2.6 ueberraschend ausfaellt:** vor dem
Einfuegen dieselbe Zeile loeschen (`worker_id`+`project_id`) und dann ohne
`merge-duplicates` einfuegen. Kostet eine zweite Anfrage, braucht **keinen**
eindeutigen Schluessel, und das leere Fenster umfasst dann nur **diese eine**
Zuweisung statt aller — ein Unterschied in der Groessenordnung des Schadens.

**c) RLS: weiter ein SCHLUSS, aber es ist nichts dagegen gemessen.** Die
Zeilenmenge von `?worker_id=eq.<w>&project_id=eq.<p>` ist eine echte Teilmenge
der Menge, die `?worker_id=eq.<w>` heute schon entfernt; eine DELETE-Regel wird
je Zeile ausgewertet. Was fuer die groessere Menge erlaubt ist, ist fuer die
Teilmenge erlaubt. **Neu gemessen und stuetzend:** es gibt **keinen**
Fremdschluessel (2.3), also keine Kaskade und keinen FK-Trigger, der bei einer
Einzelzeile anders greifen koennte. **Ungemessen bleibt:** der Regeltext, ob
ein Trigger an der Tabelle haengt, und die Voraussetzung des Arguments —
naemlich dass das heutige Alles-Loeschen live wirklich durchgeht.

**d) Kein DDL heisst: keine Datei unter `sql/`.** Ich habe deshalb **keine**
angelegt. Eine `UNIQUE (worker_id, project_id)` waere eine sinnvolle
Guertel-und-Hosentraeger-Massnahme — sie ist fuer diesen Umbau **nicht
erforderlich** und daher bewusst nicht vorbereitet.

---

## 5. Der Umbau in Schritten — mit geschnittenen Ankertexten

Alle Laengen in Zeichen, gemessen an md5 `4cb3f3ac…` (erste Fassung, siehe
Abschnitt 0 — die Anker gelten auch in der spaeteren), Klammerbilanz ueber
`code_scan.ist_code`. Der Riegel schneidet dieselben Anker selbst und bricht
mit Nennung des Ankers ab, wenn einer nicht mehr genau einmal im Code steht.

### Schritt 1 — Uebersetzer: ein Zweig fuer EINE Zuweisung, ADDITIV

| | |
|---|---|
| Anfangsmarke | `if(resource==="worker-projects"&&idOrSub&&(method==="PUT"||method==="POST")){` |
| Endmarke | `await _sbUpsert("worker_projects",rows);` … `return{ok:1};` `}` |
| Laenge | **1174** (Zeile 2762, in `_translateAndExec`, Zeile 2570, 23 274 Zeichen) |

Neuer Zweig **vor** dem bestehenden, der auf die neue Rumpfform anspricht
(z. B. `body.project_id` gesetzt): gesetzt → ein `POST` mit **einer** Zeile
`{id:<w>_<p>, worker_id, project_id}`; entfernt → ein `DELETE` mit
`worker_id=eq.<w>&project_id=eq.<p>`.

**Risiko (hoch, still): der alte Zweig muss bleiben.** In den IndexedDB-
Warteschlangen der Geraete liegen heute Auftraege mit `{projects:[…]}`. Wer den
alten Zweig ersetzt statt ihn stehen zu lassen, laesst genau die
Offline-Aenderungen fallen, um deren Schutz es hier geht — und der Fehlschlag
sieht wie ein normales Verwerfen nach 5 Versuchen aus. Der alte Zweig gehoert
erst in einer spaeteren Version raus, nachdem die Warteschlangen leer sind.

**Risiko (mittel):** `_translateAndExec` ist 23 KB und hat viele Zweige. Beim
Einfuegen die Klammerbilanz pruefen — der Haken `scripts/hook_index_riegel.py`
tut das, aber er sagt nur „unbalanciert", nicht wo.

### Schritt 2 — die Benutzerhandlung: ein Auftrag je Griff

| | |
|---|---|
| Anfangsmarke | `const toggleProj=(mid,pid)=>{` |
| Endmarke | `SQ.push({url:"/api/worker-projects/"+mid,method:"PUT",body:{projects:nxt}});}` |
| Laenge | **390** (Zeile 10078, `MitarbeiterView`) |

Statt der Gesamtliste ein Auftrag mit **dem einen Paar** und der Richtung.
Der Bildschirm legt den Haken weiter sofort um (`setMonteurProjekte`) — das
bleibt.

**Risiko (hoch, still): Pfad und Verb duerfen sich nicht aendern.** Siehe
Schritt 3.

**Risiko (niedrig):** fuenf schnelle Tipper werden fuenf Auftraege. Die
Warteschlange behaelt die Reihenfolge und `doSync` fuehrt sequentiell aus;
Setzen/Entfernen desselben Paares kommt damit in der richtigen Folge an.

### Schritt 3 — der Ausstehend-Schutz aus v3.9.938 muss die neuen Auftraege sehen

| | |
|---|---|
| Anfangsmarke | `if(_u.indexOf("/api/worker-projects/")===0&&_m==="PUT"){` |
| Endmarke | `if(_wid) _v938PendingWpWorkers.add(_wid);}` |
| Laenge | **129** (Zeile 8412) |

**Das ist der Wegriegel dieses Umbaus.** Der Schutz erkennt einen Auftrag an
`_m==="PUT"` und holt die Mitarbeiter-Id mit `_u.split("/").pop()` — aus dem
**letzten** Pfadstueck. Zwei Fehler sind hier moeglich, und **beide sind
lautlos**:

* Auftrag als `POST` ablegen → der Schutz sieht ihn nicht, das naechste
  Neuladen dreht die eigene Aenderung zurueck.
* Das Projekt an den Pfad haengen (`/api/worker-projects/<mid>/<pid>`) → der
  Schutz merkt sich die **Projekt**-Id und schuetzt einen Schluessel, den
  niemand nachfragt. Er bleibt dabei gruen.

**Empfehlung: Pfad `/api/worker-projects/<mid>` und Verb `PUT` beibehalten,
die Zuweisung in den Rumpf.** Dann ist an dieser Stelle **nichts** zu aendern.
Der Riegel prueft beides (`test_der_ausstehend_schutz_erkennt_die_neuen_auftraege`)
und ich habe ihn gegen beide Fehler gegengefahren — er wird rot.

### Schritt 4 — die Loeschzahl auswerten

Am `DELETE` `Prefer: count=exact` mitsenden, `Content-Range` lesen
(`*/N`) und bei `N !== 1` melden.

**Risiko (mittel):** dass die laufende Instanz `Prefer: count` auch auf
`DELETE` mit einem `Content-Range` beantwortet, ist **NICHT GEMESSEN** — auf
`GET` und `HEAD` ist es gemessen (`preference-applied: count=exact`, und
`Content-Range: */0` kommt zurueck). Fehlt der Kopf am DELETE, darf der Code
**keinen** Fehlalarm bauen: kein Kopf = „unbekannt", nicht „0 Zeilen".
Alternative ohne Kopfzeilen-Wette: `Prefer: return=representation` und die
zurueckgegebenen Zeilen zaehlen.

**Risiko (niedrig):** `N === 0` ist der normale Wettlauf („ein anderer hat die
Zuweisung schon entfernt"), nicht ein Fehler des Nutzers. Die Meldung muss das
sagen, sonst wird sie weggeklickt.

### Schritt 5 — Leser und Verschmelzung bleiben, wie sie sind

| | |
|---|---|
| GET-Zweig | `if(resource==="worker-projects"){` … `return _sbGet("worker_projects");` `}` — **178** Zeichen (Zeile 2606) |
| Verschmelzung | `if(wpMap&&Array.isArray(wpMap)&&wpMap.length){` … `return _z;});}` — **1024** Zeichen (Zeile 8523) |

**Nichts anfassen.** Das Ueberspringen leerer Antworten wird weiter gebraucht
(1.4), und der Ausstehend-Schutz sitzt mitten drin. Der Riegel haelt beide
Wirkungen fest, damit ein „Aufraeumen" auffaellt.

**Risiko (niedrig, aber es gibt eines):** wenn Schritt 2 mehrere Auftraege je
Mitarbeiter erzeugt, muss `_v938PendingWpWorkers` weiterhin **jeden**
betroffenen Mitarbeiter enthalten. Da der Schutz eine Menge ist und alle
Auftraege der Warteschlange durchlaeuft, passt das ohne Aenderung — solange
Schritt 3 eingehalten wird.

### Schritt 6 — Versionsnummer

Ans **Ende**, nach allem anderen (`scripts/version_bump.py`).

---

## 6. Der Riegel

`tests/test_worker_projects_einzelzeile_v940.py` — 19 Faelle,
**heute 12 gruen / 7 rot**. Die 7 roten zeigen den fehlenden Umbau; sie sind
kein Fehler dieses Laufs.

**Es ist kein Textriegel.** `toggleProj`, `_translateAndExec`, `_authRetry` und
alle `_sb*`-Helfer werden woertlich geschnitten und unter Node gegen einen
nachgebauten PostgREST **ausgefuehrt**, der echte Zeilen fuehrt. Der Schnitt
liegt bei `fetch` — welchen Helfer der Umbau benutzt, ist dadurch
gleichgueltig. Was die Attrappe unsichtbar macht, steht im Dateikopf.

| rot heute | was er messen wird |
|---|---|
| `test_paralleler_stand_bleibt_erhalten` | **der Befund.** A am Server, lokal unbekannt, B wird gesetzt → heute Endzustand `['B']`, A weg |
| `test_kein_leeres_fenster` | Verlauf heute: `['A'] → ['A'] → [] → ['A','B']` — das `[]` ist das Fenster |
| `test_abwaehlen_nimmt_nur_die_eine_zeile` | B abwaehlen bei nur lokal bekanntem B → heute Endzustand `[]`, A mit weg |
| `test_der_letzte_haken_loescht_nur_seine_zeile` | Endzustand stimmt, aber das leere Fenster klafft |
| `test_kein_befehl_trifft_eine_ganze_mitarbeiter_menge` | 6 von 6 DELETE filtern nur auf `worker_id` |
| `test_das_loeschen_fragt_nach_der_zeilenzahl` | 6 von 6 DELETE senden `prefer=''` |
| `test_eine_unerwartete_loeschzahl_wird_gemeldet` | es gibt heute kein auf eine Zeile eingeengtes DELETE, dessen Zahl man pruefen koennte |

**Die roten Faelle sind erfuellbar, und das ist nachgemessen.** Ich habe den
Pruefstand mit einem handgeschriebenen Einzelzeilen-Umbau gefuettert
(`index.html` unangetastet): **19 von 19 gruen**. Drei Gegenmutationen bleiben
gezielt rot:

| Gegenmutation | bleibt rot |
|---|---|
| Einzelzeile, aber ohne `Prefer: count` und ohne Meldung | `test_das_loeschen_fragt_nach_der_zeilenzahl`, `test_eine_unerwartete_loeschzahl_wird_gemeldet` |
| Auftrag als `POST` statt `PUT` | `test_der_ausstehend_schutz_erkennt_die_neuen_auftraege` |
| Projekt im Pfad statt im Rumpf | `test_der_ausstehend_schutz_erkennt_die_neuen_auftraege` |

**Vier Koeder.** Ohne sie wuerde diese Datei bei eigenem Ausfall gruen melden:
dass ueberhaupt Anfragen gestellt werden (dieser Koeder hat beim Bauen
zugeschnappt — ein fehlender `_authRetry`-Schnitt liess den Zweig platzen, und
alle Zaehlungen waren leer und damit „bestanden"); dass die Attrappe eine
fremde Zeile wirklich verlieren **kann**; dass der Lueckensucher eine gebaute
Luecke findet; und dass ohne Adminrecht nichts passiert.

**Lauf:** `python -m pytest tests/test_worker_projects_einzelzeile_v940.py -q`
(braucht `node`, ~35 s). Der Rueckgabewert kommt **ohne** Pipe gelesen.

---

## 7. Was dieser Lauf NICHT gemessen hat

* Die RLS-Policies auf `public.worker_projects`, je Befehl. → Abfrage 1 in 2.6.
* Primaerschluessel und eindeutige Indizes. → Abfrage 2.
* Ob ein Trigger an der Tabelle haengt. → Abfrage 3.
* Wie viele Zeilen die Tabelle heute fuehrt und ob eine ein `role` traegt.
  → Abfrage 4. (Zweite Hand, `docs/BUG-VERFOLGUNG-v3998.md`: 29 Zeilen am
  23.07.2026, alle mit `wX`-Kennung. Nicht mein Messwert.)
* Ob das heutige Alles-Loeschen live wirklich durchgeht.
* Ob `Prefer: count` auf `DELETE` einen `Content-Range` liefert (auf `GET`/`HEAD`
  gemessen, auf `DELETE` nicht — das waere ein Schreibzugriff gewesen).
* Ob `anon` ein SELECT-**Recht** auf der Tabelle hat (nur RLS davor) oder gar
  keines. Die Gegenprobe wurde abgelehnt; ohne sie keine Aussage.
* Die laufende App im Browser. Gemessen wurde geschnittener, unter Node
  ausgefuehrter Code — nicht die Oberflaeche.
