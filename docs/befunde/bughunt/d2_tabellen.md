# D2 — Welche Tabellen der 0-Zeilen-Wächter noch nicht deckt

**Auftrag.** Die Tafel `_RLS_SILENT_DENIAL_LABELS` (`index.html:2616`) sagt dem
Wächter bei `index.html:2954`, für welche Tabellen „HTTP 200 mit leerem Array"
als **abgewiesener Schreibvorgang** zu gelten hat statt als Erfolg. Steht eine
Tabelle nicht darin, gilt die Abweisung als Erfolg, der Auftrag wird aus der
Warteschlange gelöscht, und die Eingabe des Monteurs ist weg.

**Kein Eingriff.** `index.html` wurde nicht angefasst — kein Edit, kein Write,
kein Commit, kein Push. Diese Datei ist die einzige, die dieser Lauf angelegt
hat.

---

## 0. Umfang und Methode

**Umfang.** `index.html` allein, 30 375 Zeilen, `APP_VERSION="3.9.993-supabase"`
(Zeile 3115). Arbeitsbaum auf `530f6c8`, `index.html` darin **verändert**
(uncommitted). Gemessen wurde **nur der Quelltext**. Über den tatsächlichen
Zeilenschutz der laufenden Datenbank sagt dieser Bericht **nichts** — dafür gab
es hier keinen Zugang.

**Grundgesamtheit.** Eine Tabelle zählt, wenn es im Quelltext mindestens einen
`SQ.push`-Aufruf mit `method:"PUT"` oder `method:"PATCH"` gibt, dessen
`/api/<route>` über `ROUTE_MAP` (Zeile 2307, 40 Einträge) auf sie zeigt.
`API.request` scheidet als zweiter Weg aus: alle 7 Aufrufstellen sind `GET`
(gemessen, nicht angenommen).

**Werkzeug.** Ein eigener JS-Tokenizer
(`scratchpad/scan_sq.py`) klassifiziert jedes Zeichen der Datei als Code,
String, Template-Literal, Kommentar oder Regex-Literal; erst danach wird
`SQ.push(` gesucht und das Argument per Klammerabgleich **nur über
Code-Zeichen** geholt. Kommentare werden vor der Auswertung ausgeblendet —
die Datei enthält riesige deutsche Kommentare, in denen fast jeder
Tabellenname vorkommt, und zwei davon sind 284 000 bzw. 88 500 Zeichen lang.

### Die Eichung — und was sie gefangen hat

Eine Köder-Datei mit **17 Positiv-Fällen** und **3 Negativ-Kontrollen**:
beide Anführungszeichen-Schreibweisen, Ternär außerhalb *und* innerhalb des
Objekts, Regex im Rumpf, `)` und `}` im String, Template-Literal im Rumpf,
Backtick im Kommentar, `method:` als Variable, verschachtelte Objekte —
gegen einen auskommentierten, einen blockkommentierten und einen
in einem String stehenden `SQ.push`.

**Der erste Anlauf war grün und falsch.** Er meldete 23 Tabellen. Drei
Tabellen, die *in der Tafel stehen* (`absences`, `material_catalogs`,
`fz_schaeden`), hatten angeblich **null** Schreibstellen — das war der Anlass
nachzusehen, nicht die Zahl 23. Ursache: innerhalb einer
Template-Interpolation `${…}` behandelte der Tokenizer Regex-Literale nicht.
An dieser Stelle, Zeile 20578:

```js
`<!doctype html>…<title>Warenkorb ${_e((p.nr||p.name||"").replace(/"/g,""))}</title>…`
```

hielt er das `"` in `/"/g` für einen String-Anfang und verschluckte danach
**138 904 Zeichen** — die Zeilen 20578 bis rund 21700 samt der
`material-catalogs`-Schreibstelle. Der Fehler pflanzte sich fort: ab dort
wurde ein Backtick in einem Kommentar (`Aufloesung ueber \`monteure\``, Zeile
22258) als Template-Anfang gelesen und riss weitere 46 964 Zeichen mit, dann
noch einmal 39 833. Der Lauf hat das **nicht gemeldet** — er hat einfach
weniger gefunden.

Nach der Kur (Interpolationen sind ein vollwertiger Code-Kontext, mit
Kommentaren, Strings, Regex und verschachtelten Templates) und mit fünf
zusätzlichen Ködern genau für diese Formen: **17 von 17 Positiv-Fällen
gefunden, 0 von 3 Negativ-Kontrollen** — und in `index.html` stieg die Zahl
der gefundenen `SQ.push`-Aufrufe von 148 auf **188**. Die längsten
Nicht-Code-Strecken sind seither nur noch die zwei echten Riesenkommentare
und zwei base64-Bilddaten.

---

## 1. Die Zahlen

| | |
|---|---:|
| `SQ.push`-Aufrufe im Code (ohne Kommentare/Strings) | **188** |
| davon mit `PUT` oder `PATCH` | **98** |
| daraus Schreibstellen je Tabelle (ein Aufruf kann zwei Tabellen treffen, z. B. Zeile 18491 `defects`+`tickets`) | 105 |
| **distinkte Supabase-Tabellen, die per `PUT`/`PATCH` über die Warteschlange beschrieben werden** | **27** |
| Einträge in `_RLS_SILENT_DENIAL_LABELS` heute | 11 |
| davon, die eine der 27 Tabellen treffen | **10** |
| **ungedeckt** | **17** |
| Fälle mit nicht-literaler `method:`-Angabe (unauswertbar) | **0** |

**Der Plausibilitätsanker hat gehalten — bei der Gesamtzahl.** 27 beschreibbare
Tabellen, und die genannten Einzelzahlen stimmen auf den Punkt:
`werkzeuge` 14, `defects` 11, `projects` 5, `finkzeit` 4, dazu `tickets` (3)
und `project_documents` (3).

**Bei der Zahl der ungedeckten hat er nicht gehalten: es sind 17, nicht 16.**
Die Rechnung „27 − 11 = 16" setzt voraus, dass alle 11 Tafel-Einträge unter den
27 sind. Einer ist es nicht:

> 🔴 **`fz_schaeden` ist ein toter Eintrag.** Die Tabelle wurde in **v3.9.432**
> abgeschafft — Einzelquelle ist seither das JSON-Feld `fahrzeuge.schaeden`.
> `index.html:2726` sagt das ausdrücklich und gibt
> `return {ok:1,skipped:"fz_schaeden_removed"}` zurück; in `ROUTE_MAP` gibt es
> gar keine Route dorthin. Der Eintrag kann nie feuern. Er schadet nicht, aber
> er täuscht eine Deckung vor, die es nicht gibt.

Das ist auch die Korrektur an `docs/befunde/bughunt/datenverlust.md`, B4:
dort steht „11 von 27 … bei den anderen 16". Richtig ist **10 von 27, die
anderen 17**.

---

## 2. Die 17 ungedeckten Tabellen

Zweck jeweils aus den Schreibstellen selbst erschlossen.

### 2.1 Die 13, die in den Textblock gehören

| Tabelle | Schreib­stellen | Zweck im Betrieb | Beschriftungs­vorschlag |
|---|---:|---|---|
| `werkzeuge` | **14** | Werkzeug ausgeben / zurücknehmen (`status`, `zugewiesen`, `projekt`), Standort umbuchen, Barcode nachtragen, Serviceheft-Eintrag. Die meisten Schreibstellen der ganzen App. | `Werkzeug-Änderung` |
| `projects` | 5 | Projekt-Stammdaten bearbeiten, archivieren, Fortschritt in %, Plan-Ebenen. | `Projekt-Änderung` |
| `finkzeit` | 4 | Monatsabrechnung: Fink-Stunden eintragen, „abgeglichen" setzen, PDF hochladen, Freigabe mit Unterschrift. | `Monatsabrechnung` |
| `project_documents` | 3 | Dokument in einen Ordner verschieben, Kundenfreigabe an/aus. | `Dokument-Änderung` |
| `bauprovisorien_mieten` | 2 | Miet-Zeile am Bauprovisorium ändern, Rechnungs-Pfad nachtragen. | `Bauprovisorium-Miete` |
| `bauprovisorien` | 1 | Bauprovisorium bearbeiten. | `Bauprovisorium-Änderung` |
| `checklists` | 1 | Checklisten-Punkte abhaken (`items`, `status`). | `Checklisten-Eintrag` |
| `material_orders` | 1 | Material-Bestellung ändern. | `Material-Bestellung` |
| `supplier_configs` | 1 | Lieferanten-Einstellung speichern. | `Lieferanten-Einstellung` |
| `supplier_orders` | 1 | Status einer Lieferantenbestellung setzen. | `Lieferanten-Bestellung` |
| `fz_termine` | 1 | Fahrzeug-Termin als erledigt markieren. | `Fahrzeug-Termin` |
| `gefahrstoff_folders` | 1 | Gefahrstoff-Ordner umbenennen. | `Gefahrstoff-Ordner` |
| `project_folders` | 1 | Projekt-Ordner umbenennen. | `Ordner-Umbenennung` |

Zeilennummern der Schreibstellen:

```
werkzeuge             29667 29772 29780 29781 29787 29788 29819 29866
                      29867 29868 30018 30081 30103 30121
projects              15729 15740 15852 (zweimal) 18368
finkzeit              23363 23369 23399 23418
project_documents     19485 19495 19501
bauprovisorien_mieten 29451 29464
bauprovisorien        29439
checklists            16711
material_orders       20347
supplier_configs      14029
supplier_orders       20937
fz_termine            28030
gefahrstoff_folders   29248
project_folders       19442
```

### 2.2 Unsichere Fälle — NICHT ungeprüft übernehmen

Diese vier sind gemessen ungedeckt, dürfen aber nicht einfach in die Tafel.

**🔴 `worker_projects` (1 Schreibstelle, Zeile 10203) — ein Eintrag wäre tot.**
`PUT /api/worker-projects/<id>` mit gesetztem `body.project_id` wird in
`_translateAndExec` bei **Zeile 2823** abgefangen (v3.9.941, „EINE ZUWEISUNG,
EINE ZEILE"): der Zweig macht `_sbUpsert` bzw. ein eingeengtes `DELETE` und
gibt `return{ok:1}` zurück. Der alte Zweig daneben endet bei Zeile 2839
ebenfalls mit `return{ok:1}`. **Kein `worker-projects`-`PUT` erreicht je die
generische CRUD-Strecke und damit den Wächter.** Ein Tafel-Eintrag sähe aus
wie Schutz und wäre keiner.

**🟡 `defects` (11) und `tickets` (3) — hier gibt es bereits eine
Entscheidung.** Der Kommentar an der `plans`-Zeile (`index.html:2626`,
v3.9.478) sagt wörtlich: *„defects/tickets UPDATE = authenticated → bewusst
NICHT gelistet, sonst False-Positive bei 0-Row-Edge."* Wer sie aufnimmt,
kippt eine ausdrückliche frühere Entscheidung — das ist möglich, aber es ist
eine Entscheidung und kein Versehen, und sie gehört ausgesprochen. Mit
zusammen 14 Schreibstellen sind das die zwei größten Posten der Liste.

**🟡 `notifications` (1 Schreibstelle, Zeile 9162).** Der einzige Schreibweg
ist `PUT /api/notifications/<id>` mit `{read:1}`. Die Strecke erreicht den
Wächter (der `notifications`-Block bei Zeile 2685 endet mit dem Kommentar
*„Regular notification CRUD falls through"*). Aber null getroffene Zeilen ist
hier ein **normaler** Ausgang: `notifications/clear` und `read-all` löschen
bzw. ändern dieselben Zeilen, und eine zwischenzeitlich gelöschte
Benachrichtigung ergibt 0 Zeilen ohne jede Rechteverletzung. Das gäbe einen
Fehl-Toast für einen Vorgang, den der Monteur gar nicht bemerkt hat.

### 2.3 Eine Eigenschaft, die für alle gilt

Der Wächter kann nicht zwischen „RLS hat abgewiesen" und „die Zeile gibt es
nicht" unterscheiden — beides ist HTTP 200 mit leerem Array. Bei `absences`
war genau das **gewollt** (v3.9.623: der Antrag war nie am Server angelegt,
und der Monteur sollte es erfahren). Bei `checklists` liegt derselbe Fall vor:
zusammengesetzter Schlüssel, `encodeURIComponent(id)`. Das ist kein
Gegenargument, aber es ist die Eigenschaft, die man mit jedem neuen Eintrag
mitkauft.

---

## 3. Der Textblock

Einzusetzen in `_RLS_SILENT_DENIAL_LABELS`, `index.html:2616`.

> ⚠️ **Die bestehende `absences`-Zeile (2627) ist heute der letzte Eintrag und
> endet OHNE Komma.** Sie braucht ein Komma ans Ende, bevor der Block folgt.
> Der Block selbst endet ohne Komma, genau wie die Tafel heute.

Die Versionsnummer `v3.9.994` ist der Nachfolger des Arbeitsbaum-Stands
`3.9.993`; falls der Hauptlauf anders bumpt, ist sie mitzuziehen.

```js
  werkzeuge:"Werkzeug-Änderung"/* v3.9.994: 14 Schreibstellen (Ausgabe/Rücknahme, Standort, Barcode, Serviceheft) — der größte ungedeckte Posten. */,
  projects:"Projekt-Änderung"/* v3.9.994: Stammdaten, Archivieren, Fortschritt-%, Plan-Ebenen. */,
  finkzeit:"Monatsabrechnung"/* v3.9.994: Fink-Stunden, Abgleich-Haken, PDF-Upload, Freigabe mit Unterschrift. finkzeit steht schon in der updated_at-Blacklist (v3.9.206) — der PATCH geht ohne updated_at raus. */,
  project_documents:"Dokument-Änderung"/* v3.9.994: Ordner-Verschieben und Kundenfreigabe. */,
  bauprovisorien_mieten:"Bauprovisorium-Miete"/* v3.9.994: hat KEINE updated_at-Spalte (v3.9.582, Blacklist) — der 0-Zeilen-Fall ist hier der einzige Hinweis. */,
  bauprovisorien:"Bauprovisorium-Änderung"/* v3.9.994 */,
  checklists:"Checklisten-Eintrag"/* v3.9.994: zusammengesetzter Schlüssel wie absences — 0 Zeilen heißt auch hier „nie am Server angelegt", und genau das soll der Monteur erfahren. */,
  material_orders:"Material-Bestellung"/* v3.9.994 */,
  supplier_configs:"Lieferanten-Einstellung"/* v3.9.994 */,
  supplier_orders:"Lieferanten-Bestellung"/* v3.9.994 */,
  fz_termine:"Fahrzeug-Termin"/* v3.9.994 */,
  gefahrstoff_folders:"Gefahrstoff-Ordner"/* v3.9.994 */,
  project_folders:"Ordner-Umbenennung"/* v3.9.994 */
```

**Nicht im Block enthalten**, mit Begründung in §2.2: `worker_projects`
(erreicht den Wächter nie), `defects` und `tickets` (ausdrückliche
Gegen-Entscheidung v3.9.478), `notifications` (0 Zeilen ist dort ein normaler
Ausgang).

Falls der Hauptlauf `defects` und `tickets` doch aufnimmt — die Entscheidung
liegt bei ihm, nicht bei diesem Bericht —, wären das die zwei Zeilen; der
Kommentar an der `plans`-Zeile 2626 müsste dann **mitgeändert** werden, sonst
widerspricht die Tafel sich selbst:

```js
  defects:"Mangel-Änderung"/* v3.9.994: kehrt die Entscheidung aus v3.9.478 um (siehe plans-Zeile) — 11 Schreibstellen, darunter die Kunden-Freigabe eines Mangels. */,
  tickets:"Ticket-Änderung"/* v3.9.994: siehe defects. */
```

---

## 4. Was dieser Bericht NICHT sagt

* **Nichts über den Zeilenschutz der echten Datenbank.** Ob eine dieser 27
  Tabellen heute überhaupt abweist, ist hier nicht messbar. Die Tafel ist
  Defense-in-Depth: sie wirkt in dem Augenblick, in dem eine Regel scharf
  gestellt wird — und genau dann merkt es sonst niemand.
* **Nichts über `POST` und `DELETE`.** Der Wächter sitzt ausschließlich im
  `PUT`/`PATCH`-Zweig (Zeile 2954). Ein stiller 0-Zeilen-`DELETE` ist von
  dieser Messung nicht erfasst.
* **Nichts über Schreibwege am `_translateAndExec` vorbei.** Direkte
  `_sbPatch`/`_sbUpsert`-Aufrufe im UI-Code gehen weder durch die
  Warteschlange noch durch den Wächter; sie waren nicht Gegenstand des
  Auftrags. `fz_schaeden`, `fahrzeuge` (Tank-/km-Zweig, Zeile 2746) und
  `worker_projects` sind Beispiele dafür, dass es solche Wege gibt.
