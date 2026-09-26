# MERGE_ANALYSE — Objekt-Merge bei ausstehendem PUT (v3.9.847/848)

**Auftrag:** Analyse, keine Aenderung. Diese Datei ist die einzige, die dieser Lauf angelegt hat.
**Messgrundlage:** `C:\repos\epkolar-app\index.html` und `sw.js`, Arbeitsbaum auf `69acad0` (v3.9.934).
**Kein DB-Zugriff.** Alles unten Stehende ist aus dem CODE gemessen, nicht aus der Datenbank. Die
Abschnitte sind durchgehend mit **GEMESSEN** / **SCHLUSS** markiert.

**Belege sind Zeichenketten zum Greppen, keine Zeilennummern** — an `index.html` arbeitet parallel ein
zweiter Lauf, die Zeilen bewegen sich. Gegengemessen: alle unten zitierten Belegzeichenketten kommen in
`HEAD:index.html` genau so oft vor wie im Arbeitsbaum (`git show HEAD:index.html | grep -c -F "<string>"`),
der parallele Lauf hat also keine der Messstellen veraendert. Er arbeitet an der Projektlisten-Darstellung
(Hunks 15665–15732); der Fortschritt-Regler als Eingabestelle existiert vorher und nachher genau einmal.

---

## 0. Kernbefund — die Auftragsannahme trifft so nicht zu

Der Auftrag lautet: „bei einem ausstehenden PUT gewinnt das GANZE lokale Objekt. Aendert ein zweites Geraet
parallel ein ANDERES Feld derselben Zeile, geht diese Aenderung bis zum Drain verloren."

Gemessen sind daraus **zwei voneinander unabhaengige Dinge** geworden, und nur eines davon ist wahr:

| | Was | Befund |
|---|---|---|
| **Kanal 1** | Geht Lucias Feld auf dem SERVER verloren? | **NEIN** — fuer Projekte, Mitarbeiter und Fahrzeuge. Alle drei senden seit laengerem nur die GEAENDERTEN Felder. Der Feld-Merge, den der Auftrag als Alternative 3a vorschlaegt, ist auf dem Schreibweg **bereits gebaut**. |
| **Kanal 2** | Sieht Martina Lucias Feld? | **NEIN, aber** — das ist reine Anzeige-Veraltung, sie heilt beim naechsten Start nach dem Drain, und kein Serverwert geht dabei kaputt. Genau und ausschliesslich das hat v847/v848 veraendert. |
| **Kanal 3** | Der eigentliche Befund | Projekte, Mitarbeiter und Fahrzeuge werden **genau einmal pro App-Start** vom Server gelesen. Innerhalb einer Sitzung kommt Lucias Aenderung bei Martina **ueberhaupt nie** an — mit oder ohne ausstehenden PUT. Daneben ist der Merge eine Rundungsstelle. |
| **Kanal 4** | Wo der befuerchtete Verlust WIRKLICH passiert | `worker-projects` (Dispo-Zuweisung Mitarbeiter↔Projekt). Dort ist es ein echter, **dauerhafter** Verlust auf dem Server — nicht „bis zum Drain". |

Der Rest dieser Datei belegt diese vier Zeilen.

---

## 1. Welche Felder real betroffen waeren

### 1.1 Was der Merge tatsaechlich tut — GEMESSEN

Beleg (`index.html`, eine Zeile, in `HEAD` identisch):

> `_v848PendingProjPuts.has(x.id)&&_prevById.has(x.id)`

Der volle Ausdruck lautet:

```
const _srv = prj.filter(x=>!_v848PendingProjDeletes.has(x.id))
  .map(x => (_v848PendingProjPuts.has(x.id) && _prevById.has(x.id))
              ? _prevById.get(x.id)        // <— das GANZE lokale Objekt
              : _mapProject(x));
```

`_prevById.get(x.id)` ist die komplette lokale Zeile. Die Server-Zeile wird **verworfen**, nicht
feldweise gemischt. Das ist der Objekt-Merge, den der Auftrag beschreibt — bestaetigt.
Dieselbe Form dreimal: `setProjects`, `setMonteure` (Beleg `v3.9.848 Reload-Merge wie Fahrzeuge v847`)
und `setFahrzeuge` (Beleg `v3.9.847 Reload-Merge wie Werkzeuge v842`).

Die Schutzmenge ist eine Menge von **IDs**, nicht von Feldern. Beleg: `let _v848PendingProjPuts=new Set();`
und der Aufbau `_v848PendingProjPuts.add(_id)` — befuellt aus der URL (`_u.split("/").pop()`), nie aus
`it.body`. **Der Merge weiss, WELCHE ZEILE aussteht, und wirft die Information weg, WELCHE FELDER
ausstehen — obwohl sie im SQ-Eintrag direkt daneben liegt.** Das ist der eigentliche Hebel (Abschnitt 3d).

### 1.2 Was der Schreibweg sendet — GEMESSEN, und hier kippt die Annahme

Der generische PUT-Weg ist ein **PATCH**, kein Zeilen-Ersatz. Beleg: `const patchData={...mapped};delete patchData.id;`
gefolgt von `const _patchRes=await _sbPatch(table,idOrSub,patchData);`, und `_sbPatch` ist
`method:"PATCH"` auf `?id=eq.<id>`. **Es werden also genau die Spalten geschrieben, die im Body stehen —
sonst keine.** Damit haengt alles am Body, und der ist:

**Projekte — Feld-Diff. GEMESSEN.** Beleg:

> `return d;})():{...form}`

Der volle Ausdruck im Speichern-Pfad:

```
const _orig=_editProjOrig.current;
const _diff=_orig ? (()=>{const d={};Object.keys(form).forEach(k=>{if(form[k]!==_orig[k])d[k]=form[k];});return d;})()
                  : {...form};
...
if(Object.keys(_diff).length) SQ.push({url:"/api/projects/"+editP,method:"PUT",body:_diff});
```

Der eigene Kommentar daneben nennt Anlass und Absicht: `v3.9.606 #19: Feld-Diff statt Voll-Form-PUT ->
unveraenderte Felder (z.B. status) clobbern keine parallele Aenderung (archiveP/Zweit-Edit)`.
`_orig` ist der Schnappschuss vom Oeffnen des Formulars, nicht der aktuelle `projects`-State — der
Kommentar sagt das ausdruecklich (`_orig=Snapshot vom Edit-Oeffnen, NICHT current projects`). Genau
dadurch fehlt ein Feld, das Lucia inzwischen geaendert hat, im Diff und wird nicht ueberschrieben.

**Den Voll-Form-Zweig `{...form}` habe ich gegengeprueft — er ist fuer ein bestehendes Projekt
unerreichbar. GEMESSEN:** `setEditP(` kommt ausserhalb des Versionskommentars viermal vor, dreimal als
`setEditP(null)` und genau einmal als `setEditP(p.id)`; diese eine Stelle setzt den Schnappschuss im
selben Ausdruck: `setForm(_fo);_editProjOrig.current={..._fo};setEditP(p.id);`. Es gibt keinen Pfad,
auf dem `editP` gesetzt und `_editProjOrig.current` null ist.

Zahlenfelder gegengeprueft (sonst waere `form[k]!==_orig[k]` bei `0` vs `"0"` falsch-positiv und wuerde
ein *nicht* angefasstes Feld mitsenden): Schnappschuss `betrag:p.betrag||0` und
`budgetStunden:(_bs!=null&&_bs!==""?parseFloat(_bs):null)`, Eingabe `betrag:Math.max(0,...)` und
`budgetStunden:e.target.value===""?null:Math.max(0,...)`. Beide Seiten sind Zahlen. Kein Scheindiff.

**Mitarbeiter — ein Feld pro PUT. GEMESSEN.** Beleg:

> `body:{[apiField]:v}`

```
const updMonteur=(id,f,v)=>{ ... setTimeout(()=>{
  const apiField = f==="n"?"name" : f==="r"?"role" : f==="tel"?"phone" : f;
  SQ.push({url:"/api/workers/"+id,method:"PUT",body:{[apiField]:v}});
},800); };
```

Ein einziger PUT-Aufrufer, ein Feld, 800 ms je Feld entprellt (`const k=id+"_"+f`). Zwei Leute an zwei
Geraeten, die zwei verschiedene Mitarbeiterfelder aendern, koennen sich **nicht** gegenseitig
ueberschreiben.

**Fahrzeuge — spaltenweise. GEMESSEN.** Der Helfer nimmt einen dritten Parameter, der den Body auf die
eigene Spalte einschraenkt: `const _body=(typeof syncBody==="function")?syncBody(updated):(syncBody!==undefined?syncBody:updated);`
Die eigene Historie nennt das als schon durchgekaempft: `v3.9.234` / `v3.9.252` / `v3.9.286`,
Stichwort „Voll-Row-Clobber", damit „Parallel-Edits an km_log/tank_log/schaeden/serviceheft auf anderem
Geraet bleiben erhalten". Ein Unteragent hat alle Aufrufstellen des Helfers maschinell durchgezaehlt:
42 echte Aufrufe, alle mit drittem Parameter; die vier belegfreien Treffer sind Prosa in Kommentaren.

**SCHLUSS:** der befuerchtete dauerhafte Feldverlust bei Projekten, Mitarbeitern und Fahrzeugen
**existiert nicht**. Nicht weil der Merge ihn abfaengt — der Merge ist tatsaechlich ein Objekt-Merge —
sondern weil der Schreibweg das kaputte Feld nie mitsendet. Der Merge betrifft nur den Bildschirm.

### 1.3 Welche Felder also real auffallen — und nur als veraltete ANZEIGE

Nicht „alle Felder von `projects`". Betroffen ist, was tatsaechlich aus **zwei verschiedenen
Eingabestellen** kommt, denn nur dann aendern zwei Personen ohne Voneinanderwissen dieselbe Zeile.
GEMESSEN, je mit Belegzeichenkette:

| Feld | Eingabestelle A | Eingabestelle B | Beleg B |
|---|---|---|---|
| `status` | Status-Auswahl im Projektformular | **Archivieren-Knopf** in der Listen-Aktion | `body:{status:"archiv"}` |
| `fortschritt` | „Fortschritt %"-Eingabe im Formular | **Regler auf der Projektkachel** | `body:{fortschritt:v}` |
| `plan_layers` | — | **Plan-Ebenen im Plaene-Reiter**, eigener Pfad | `body:{plan_layers:next}` |

Das ist die ganze Liste fuer `projects`. Alle uebrigen 17 Formularfelder (`nr`, `name`, `kunde`,
`gewerk`, `strasse`, `plz`, `ort`, `betrag`, `budgetStunden`, `budgetEuro`, `start`, `ende`, `kundenNr`,
`ansprechpartner`, `telefon`, `emailKunde`, `portalCode`) haben **genau eine** Eingabestelle, das
Projektformular. Zwei Personen kollidieren dort nur, wenn sie dasselbe Feld tippen — und dann ist
„der Letzte gewinnt" die richtige Antwort, kein Fehler.

Zwei Felder stehen im Formularobjekt, haben aber **keine gerenderte Eingabe** und sind praktisch
eingefroren: `type` und `matchcode` (letzteres nur lesend als Kachel-Untertitel, `sub: p.matchcode`).
Zwei weitere existieren auf der Zeile, werden aber von keiner Eingabe geschrieben: `createdBy` und
`tags` — deshalb der Kommentar am optimistischen Update: `merge statt replace — verdeckte Felder
(createdBy/tags) bleiben erhalten`.

Fuer **Mitarbeiter**: zwoelf Felder, **alle aus demselben Detail-Dialog**, jedes als eigener PUT.
Es gibt keine zweite Eingabestelle. `stundensatz` steht im Mapper (`_mapWorker`) und in der
Kostenrechnung, hat aber keine Eingabe — **SCHLUSS:** derzeit nicht aus der App editierbar.

Fuer **Fahrzeuge**: die Master-Felder (`typ`, `farbe`, `fahrer`, `pickerl`, `vignette_*`,
`naechstService`, `versicherung`, `reifen`, `scheibenwischer`, `tracker_*`) haben je eine Eingabestelle
und je einen eigenen Body. Mehrfach bespielt sind:
* `kmStand` — aus drei Stellen (`addKm`, `qDoKm`, und jede Tank-Buchung schreibt `kmStand` mit),
* `tankLog` — aus drei Stellen (Tankformular, QR-Schnellaktion `qDoTank`, „Batch Tanken" `batchSave`).

### 1.4 Der Rest, der NICHT an der Zeile haengt — GEMESSEN

Vieles, was sich wie ein Projekt- oder Mitarbeiterfeld anfuehlt, ist eine eigene Ressource und vom
Objekt-Merge gar nicht beruehrt: Dispo-Zuweisung (`/api/worker-projects/`), Plaene (`/api/plans/`),
Tickets (`/api/tickets/`), Maengel (`/api/defects/`), Regie- und Abnahmeformulare (`forms`, gefiltert
nach `form_type`), Kompetenzen (`worker_kompetenzen`), Urlaubskontingent (`ODB.load("urlaubskontingent")`,
nach NAME verschluesselt), NFC, Fahrbewilligung, Anmeldung, Atteste, Fahrtenbuch.

### 1.5 Wo es wirklich weh tut — GEMESSEN, und das ist neu

Zwei Stellen verlieren echte Daten, und **keine von beiden ist die aus dem Auftrag**:

**(a) `worker-projects` — dauerhafter Verlust, kein Drain-Fenster.** Beleg `body:{projects:nxt}`:

```
const toggleProj=(mid,pid)=>{ ... SQ.push({url:"/api/worker-projects/"+mid,method:"PUT",body:{projects:nxt}}); };
```

Serverseitig wird das zu **erst alles loeschen, dann neu einfuegen**. Beleg
`worker-projects: Alte Zuweisungen konnten nicht entfernt werden`, davor:
`fetch(SB_REST+"/worker_projects?worker_id=eq."+encodeURIComponent(idOrSub), ... method:"DELETE"...)`,
danach `_sbUpsert("worker_projects",rows)`. Setzt Martina einen Haken, waehrend Lucias Haken auf
demselben Mitarbeiter noch nicht in Martinas Geraet angekommen ist, loescht Martinas Liste Lucias
Zuweisung **endgueltig** weg. Das ist genau der Schaden, den der Auftrag bei den Stammdaten befuerchtet
— nur eine Ressource weiter.

**(b) JSON-Sammelspalten bei Fahrzeugen.** `schaeden`, `serviceheft`, `termine`,
`verbrauchsmaterial`, `tankLog`, `kmLog` werden bei jeder Einzelaenderung **als ganzes Array bzw.
ganzes Objekt** zurueckgeschrieben (Beleg: die Form `u=>({schaeden:u.schaeden})`, ebenso `_svcSync`,
`_vmSync`, `_zulSync`). Zwei Schadensmeldungen von zwei Geraeten fast gleichzeitig: eine verschwindet.
Die Spalte ist gegen unbeteiligte Spalten geschuetzt, aber nicht gegen sich selbst.

---

## 2. Wie lang das Drain-Fenster typisch ist

### 2.1 Untere Grenze — GEMESSEN

Beleg `_batchDelay:1500`, und der Aufzug im selben Objekt:

```
_batchDelay:1500,
...
if(SQ._timer)clearTimeout(SQ._timer);
SQ._timer=setTimeout(()=>{if(navigator.onLine&&window.__doSync)window.__doSync();},SQ._batchDelay);
```

1,5 s nach dem **letzten** Eintrag (`clearTimeout` bei jedem weiteren Eintrag — eine Tippfolge schiebt
den Termin vor sich her). Davor liegt je Eingabestelle noch eine eigene Entprellung: Mitarbeiterfeld
800 ms (`const k=id+"_"+f` ... `},800)`), Fortschritt-Regler 300 ms (`debounce("slider_"+p.id,...,300)`).

**Belegte untere Grenze: ~2,3 s** fuer ein Mitarbeiterfeld (800 + 1500), ~1,5 s fuer Formular-Speichern,
plus eine Netzrunde. Im Normalfall online: **wenige Sekunden.**

### 2.2 Obere Grenze — GEMESSEN: es gibt keine

Das ist der Teil, der nicht geschaetzt werden darf. **Es gibt keinen periodischen Wiederholversuch.**
Nachgemessen, nicht vermutet: ich habe alle `setInterval(`-Stellen der Datei aufgelistet (21 Stueck) und
alle Vorkommen von `doSync` — **keine einzige Wiederholung auf Zeitbasis**. Die Ausloeser sind
abschliessend:

| Ausloeser | Beleg | Bedingung |
|---|---|---|
| Neuer Warteschlangen-Eintrag | `SQ._timer=setTimeout(` | nur `if(navigator.onLine)` |
| App-Start / Anmeldung | `if(cnt>0) doSync();` | einmal je `curUser`-Wechsel |
| Verbindung kommt zurueck | `setTimeout(doSync,2000)` | nur `if(cnt>0)`, mit `SQ.countMine()` |
| Service-Worker-Hintergrundsync | `SYNC_TRIGGER` | **nur an OFFENE Clients**, siehe unten |
| Knopf „Jetzt synchronisieren" | `onClick: ()=>{doSync();}` | Handarbeit |
| ~15 Einzelstellen nach bestimmten Aktionen | `if(window.__doSync)window.__doSync();` | punktuell |

Und `doSync` bricht an **vier** Stellen ab, **ohne einen neuen Termin zu setzen** — GEMESSEN:

1. `if(window._epkSyncInflight)return;` bzw. `if(syncStatus.syncing)return;` — feuert der 1,5-s-Termin,
   waehrend ein Lauf schon unterwegs ist, kehrt der Aufruf zurueck, **und es ist kein Termin mehr offen**
   (`clearTimeout` hat ihn ja verbraucht). Der Eintrag wartet auf den *naechsten* Ausloeser. Dass das
   real ist, steht im eigenen Code als Warnung an anderer Stelle: `ein bereits in-flight Batch-Sync
   (SQ._batchDelay) den __doSync-Aufruf per Guard sofort zurückgibt`.
2. `if(!_authToken){ ... return; }` — abgelaufene Anmeldung. Dass das laenger dauern kann, ist
   einkalkuliert: `10 skips in Folge ohne _authToken — User sollte neu einloggen`.
3. `if(navigator.onLine)` klammert den ganzen Abfluss; offline geschieht nichts, und der Termin aus
   (1) prueft `navigator.onLine` **vor** dem Aufruf, laeuft also ins Leere.
4. `if(_transient){fail++;break;}` — 5xx/408/429/offline stoppt den Lauf, die Warteschlange bleibt,
   **nichts plant einen zweiten Versuch**.

Der Service-Worker hilft hier nicht: `sw.js` reagiert auf `sync` nur mit
`self.clients.matchAll().then(clients => clients.forEach(client => client.postMessage({type:'SYNC_TRIGGER'})))`.
**Ohne offenen Tab gibt es keinen Client, also keinen Abfluss.** Der Hintergrundsync ist ein Weckruf an
eine laufende App, kein eigener Absender.

### 2.3 Die belegte Zeitspanne

* **Online, ungestoert:** ~2–3 s (1.4 s/2.3 s Entprellung + eine Netzrunde). Das Fenster ist hier so
  kurz, dass es praktisch nicht auffaellt.
* **Zweiter Eintrag trifft einen laufenden Sync:** offen bis zum naechsten Ausloeser. Da eine Bueroperson
  meist weitertippt, ist das wieder Sekunden — aber **belegt garantiert ist es nicht.**
* **Offline / Funkloch:** bis die Verbindung zurueckkommt, **plus 2 s**. Tablet im Keller: Minuten bis
  Stunden.
* **Tab war offline geschlossen:** bis zum **naechsten App-Start** (`if(cnt>0) doSync();`). Tage moeglich.
* **Anmeldung abgelaufen:** bis zur naechsten Anmeldung.

**SCHLUSS:** „Das Drain-Fenster ist kurz" gilt fuer den Normalfall und fuer sonst nichts. Es gibt im
Code **keine obere Schranke**, weil es keinen periodischen Wiederholversuch gibt. Fuer die
Entscheidung heisst das: die Haeufigkeit ist niedrig, der Einzelfall aber unbegrenzt lang — und
unsichtbar, weil kein Serverfehler entsteht.

### 2.4 Der Befund, der grosser ist als das Drain-Fenster — GEMESSEN

Fuer `projects`, `monteure` und `fahrzeuge` laeuft der Merge **nur im Boot-Effekt**. Dessen
Abhaengigkeitsliste ist `},[curUser]);` — er feuert bei App-Start und bei Anmeldewechsel, sonst nicht.

Gegengeprueft, dass es keinen zweiten Server-Leser gibt: alle Schreiber der drei Zustaende aufgelistet.
`setProjects` — neun Stellen: eine ODB-Cache-Ladung, der Merge, eine Saat (`setProjects(INIT_PROJECTS)`),
Rest lokale optimistische Bearbeitung. `setMonteure` — sechs, gleiches Bild. `setFahrzeuge` — fuenfzehn,
gleiches Bild. **Keine davon liest waehrend der Sitzung neu vom Server.**

Der 60-s-Umlauf (`const POLL_INTERVAL=60000;`, `setInterval(pollForChanges,POLL_INTERVAL)`) holt
**Maengel und Abwesenheiten**, keine Stammdaten. Der stuendliche `loadAll(true)` gehoert der
Buero-Export-Ansicht und schreibt `setAllEntries`/`setAllBT`/`setAllRegie`/`setAllMaengel` — die
Stammdaten beruehrt er nicht.

**SCHLUSS, und das ist der wichtigste Satz dieser Analyse:** Martina sieht Lucias Aenderung an einem
Projekt, einem Mitarbeiter oder einem Fahrzeug **nicht nach 1,5 Sekunden und nicht nach 60, sondern
erst beim naechsten App-Start** — ganz unabhaengig davon, ob ein PUT aussteht. Das Drain-Fenster ist
ein Ausschnitt eines viel groesseren Fensters, das niemand geschlossen hat.

---

## 3. Alternativen, je mit Kosten

### 3a. Feld-Merge statt Objekt-Merge (nur geaenderte Felder senden)

**Auf dem Schreibweg: bereits gebaut, fuer alle drei Sammlungen.** Abschnitt 1.2, GEMESSEN.
Projekte `v3.9.606`, Mitarbeiter ein Feld je PUT, Fahrzeuge `v3.9.234`/`252`/`286`. **Zu tun: nichts.**
Wer das jetzt „einfuehrt", baut es zum zweiten Mal.

Was auf dem Schreibweg offen bleibt, sind die Sammelbehaelter aus 1.5:

| Stelle | Aenderung | Anzufassen | Risiko | Loest NICHT |
|---|---|---|---|---|
| `worker-projects` | je Zuweisung ein POST/DELETE statt Alles-ersetzen | 3: `toggleProj`; der `worker-projects`-Zweig in `_translateAndExec`; der Boot-Leser `API.request("GET","/api/worker-projects")` | **niedrig** — der stabile Schluessel existiert schon: `id:idOrSub+"_"+pid`, also ist ein Einzel-DELETE/Upsert von sich aus wiederholbar. Das Alles-loeschen ist heute die Doppel-Vermeidung; die uebernimmt der PK. | zwei Personen am **selben** Haken |
| Fahrzeug-Sammelspalten | pro Eintrag eine Zeile statt JSON-Array | 5 Body-Former (`_schSync`, `_svcSync`, `_vmSync`, `_zulSync`, `termine`) **plus Schemaaenderung** | **hoch** — neue Tabellen, Migration, RLS, Umzug der Altdaten. Der eigene Kommentar hat den Zweitspeicher bewusst wieder eingesammelt: `fz_schaeden-Zweitspeicher entfernt — Single-Source = fahrzeuge.schaeden JSON`. | nichts an Projekten/Mitarbeitern |

### 3b. Konflikt-Dialog „wie bei `weekplan_rows`"

**Korrektur der Auftragsannahme, GEMESSEN: bei `weekplan_rows` gibt es keinen Konflikt-Dialog.**
Ich habe alle 14 Treffer auf `weekplan_rows` und alle Treffer auf `Konflikt` gelesen. Gefunden wurde:

1. **Zeilen-Ebene als Speicherform** (`v3.9.500: Zeilen-Level-Storage für Multi-User-Sync`). Eine
   DB-Zeile je Dispo-Zeile mit `row_id`, statt eines jsonb-Klotzes je Woche. Zwei Leute in
   verschiedenen Zeilen derselben Woche kollidieren dadurch **strukturell nicht mehr**.
2. **Eine Schmutzmenge, gefuellt aus einem Schnappschuss-Vergleich.** Beleg:
   `const snapshot=JSON.stringify({bvh:r.bvh||"",projId:r.projId||"",bem:r.bem||"",z:r.z||{},_so:i*10});`
   `const prev=_wpLastSaved.current.get(r.id);` `if(prev!==snapshot)_wpDirtyIds.current.add(r.id);`
   Gesendet werden **nur** die schmutzigen Zeilen, je als eigener Eintrag
   (`SQ.push({url:"/api/weekplan-rows",method:"POST",body:u})` in einer Schleife).
3. **Eine Schutzmenge, die nur das Angefasste schuetzt**, und die nur beim Umlauf greift (`if(isPoll)`):
   `protectedIds` = `__wpDirtyRowIds` ∪ `__wpPendingRowIds` ∪ `__wpDeletedRowIds`.
4. **30-s-Umlauf plus Reload bei Tab-Fokus** (`},30000);` mit `if(document.visibilityState!=='visible')return;`).
5. **Ein Haken im Abfluss, der die Mengen nach Server-Bestaetigung raeumt** (`window.__wpDirtyRowIds.delete(_rid)`).

Das ist **dieselbe Idee wie hier, nur eine Ebene feiner**: Schutz fuer das, was der Nutzer wirklich
angefasst hat, nicht fuer alles, was er gerade in der Hand haelt. Ein Dialog kommt nicht vor.

**Was es gekostet hat — GEMESSEN an der Historie:** zwei Versionen (`v3.9.500` Speicherform,
`v3.9.501` Wettlaufschutz), eine neue Tabelle, neue UUIDs fuer Wochen-Kopien
(`neue UUID-IDs für KW-Kopien — sonst PK-Kollision in weekplan_rows`), drei globale `window`-Mengen,
ein Haken mitten im `doSync`, eine Schranke im Umlauf. Und es ist **immer noch nicht feldweise**:
innerhalb einer Zeile geht das `z`-jsonb komplett mit.

**Der naechste echte Konflikt-Hinweis im Bestand** ist `v3.9.786` — und er ist bewusst **nicht
blockierend**: ein Satz im Bestaetigungsdialog (`⚠ Konflikt: an diesem Tag sind bereits ... erfasst`)
plus eine Textmarke in der Liste und ein Verweis „Konflikt lösen ▸", der den Nutzer in den richtigen
Reiter schickt. **Kein Auflöser, keine Feldauswahl.** Auch das ist eine Antwort auf die Frage, wie in
diesem Bestand mit Konflikten umgegangen wird: man macht sie sichtbar und laesst den Menschen hingehen.

**Kosten eines echten Konflikt-Dialogs, wenn man ihn baute:** Er braucht eine Grundversion je Satz.
`updated_at` wird bei **jedem** PATCH gestempelt (`patchData.updated_at=new Date().toISOString()`) und
`projects`/`workers`/`fahrzeuge` stehen nicht auf der Ausnahmeliste — aber **niemand liest es zurueck**,
und `_mapProject`/`_mapWorker` muessten es erst durchreichen. Dazu kommt das Ablauf-Problem: SQ-Eintraege
sind abgeschickt-und-vergessen. Der Dialog erschiene **waehrend des Abflusses** — laut Abschnitt 2.3
moeglicherweise Stunden spaeter oder beim naechsten App-Start.
**Risiko: hoch, und zwar am Menschen.** Eine Rueckfrage zu einer Aenderung, an die sich niemand mehr
erinnert, ist schlechter als ein stilles „der Letzte gewinnt". **Loest nicht:** den Offline-Fall, also
genau den Fall, in dem das Fenster gross ist.

### 3c. Den Umlauf auf die Stammdaten ausdehnen (gegen Kanal 3)

Das behebt, was Martina und Lucia tatsaechlich auffaellt (2.4). Vorbilder liegen fertig da: der
60-s-Maengel-Umlauf **traegt den Pending-Merge bereits** (`v3.9.597 #4 Bug-Hunt: Poll war Voll-Overwrite
von forms.maengel → un-gesyncte optimistische Edits ... bis zu 60s zurueckgesetzt (belegter
Prod-Vorfall)`), und der Wochenplan-Umlauf hat den Fokus-Reload.

**Anzufassen: 1** neue `useEffect` plus Wiederverwendung des bestehenden SQ-Abtasters.
**Risiko: mittel, und mit klarer Reihenfolge.** Ein Umlauf **ohne** 3d macht es schlimmer, nicht
besser: die Anzeige-Veraltung tritt dann **alle 60 s** ein statt einmal je App-Start. Genau diese
Fehlerklasse steht schon einmal als belegter Produktionsvorfall im Code (`v3.9.597`).
**Loest nicht:** den Verlust bei `worker-projects`.

### 3d. Schmutzige FELDER statt ausstehender ZEILEN — der Weg, den der Bestand schon fast gebaut hat

Die Beobachtung aus 1.1: die Schutzmenge sammelt IDs aus der **URL** und laesst `it.body` liegen.
Und weil der Schreibweg laut 1.2 **ohnehin nur geaenderte Felder sendet**, ist `Object.keys(it.body)`
**exakt** die Liste der Felder, die geschuetzt werden muessen. Sie liegt im SQ-Eintrag bereit.

Aus

```
else if(_u.startsWith("/api/projects/")&&_m==="PUT"){const _id=_u.split("/").pop();if(_id) _v848PendingProjPuts.add(_id);}
```

wird eine `Map<id, Set<feld>>`, und aus

```
? _prevById.get(x.id)                  // ganzes lokales Objekt
```

wird eine Auflage nur der ausstehenden Felder auf die **frische Server-Zeile**.

**Anzufassen: 4 Stellen.** Ein Abtastblock (die sechs `else if`-Zeilen fuer projects/workers/fahrzeuge)
und die drei Verbraucher `setProjects`, `setMonteure`, `setFahrzeuge`. Kein Schema, keine DB, keine
Migration, keine neue Oberflaeche, kein `updated_at`, keine Rueckfrage an den Nutzer.

**Das Risiko, ehrlich benannt — die Schluesselnamen stimmen nicht ueberall ueberein.** Der Body traegt
API-Namen, der State camelCase-Namen. GEMESSEN ist die Umsetzungsliste vollstaendig und klein:
* Mitarbeiter: **drei** Namen, an genau einer Stelle nachlesbar —
  `const apiField=f==="n"?"name":f==="r"?"role":f==="tel"?"phone":f;` (also `name→n`, `role→r`, `phone→tel`).
* Projekte: **einer** — `plan_layers→planLayers`. Alle anderen PUT-Bodies tragen die camelCase-Schluessel
  des Formularobjekts (`kundenNr`, `portalCode`, `emailKunde`, `budgetStunden`, `budgetEuro`, `start`,
  `ende`) oder identische (`status`, `fortschritt`).
* Fahrzeuge: **einer, und ein Sonderfall** — `_mapFahrzeug` liefert camelCase *und* behaelt
  `km_log`/`tank_log`; die Bodies sind camelCase. Aufpassen bei `tankLog_add`: das ist **kein Feld**,
  sondern eine Anweisung, die `_translateAndExec` aufloest — sie muss auf `tankLog` abgebildet werden.

Wird eine dieser fuenf Umsetzungen vergessen, faellt das betroffene Feld beim Start auf den Serverstand
zurueck — also **genau das heutige Verhalten fuer dieses eine Feld**, keine Verschlechterung. Das ist
ein gutartiges Versagen, und es ist mit einem Riegel pruefbar, der **Wirkung** misst: Server-Zeile mit
geaendertem Fremdfeld + ausstehender PUT auf Eigenfeld → beide muessen nach dem Merge dastehen. Mit
Koeder: derselbe Riegel muss ROT werden, wenn man die Feldmenge auf „alles" aufweitet.

**Loest nicht:** zwei Personen am selben Feld (last-write-wins bleibt, richtig so); die
Fahrzeug-Sammelspalten; `worker-projects`; und **Kanal 3 nicht** — dafuer braucht es 3c.

### 3e. Was noch im Bestand liegt und hier nicht passt

* **`_sbInsertIfAbsent`** (`ON CONFLICT PK DO NOTHING`, `v3.9.620`) — loest Doppel-Einfuegen bei
  verlorener Antwort, nicht Feldverlust.
* **0-Zeilen-Waechter** (`_RLS_SILENT_DENIAL_LABELS`, `v3.9.306`) — faengt den stillen RLS-Abweis.
  Gutes Vorbild fuer „nicht still scheitern", aber kein Merge.
* **Der eindeutigkeitsbasierte Wettlauf-Erkenner** (`v3.9.815`, `_asZeitDupErr`: 23505/HTTP409 →
  „der Partner war schneller, das gilt als Erfolg") — der Bestand hat also schon ein Muster fuer
  „gleichzeitig, und es ist kein Fehler". Anwendbar nur, wo ein Unique-Schluessel existiert.
* **Nichts tun.** Kostet 0, und ist nach Abschnitt 1.2 fuer Kanal 1 sogar vertretbar. Vertretbar ist es
  **nicht** fuer `worker-projects` (echter Verlust) und unbefriedigend fuer Kanal 3.

---

## 4. Empfehlung

**Den Konflikt-Dialog nicht bauen.** Er loest ein Problem, das nach Abschnitt 1.2 nicht existiert, er
kostet das meiste, und er kommt beim einzigen Fall mit einem grossen Zeitfenster — offline — zum
falschen Zeitpunkt beim falschen Menschen an. Der Bestand hat sich zweimal gegen diese Bauform
entschieden (bei `weekplan_rows` per Zeilen-Ebene, bei `v3.9.786` per nicht blockierendem Hinweis),
und beide Male war das richtig.

**Stattdessen, in dieser Reihenfolge:**

**1. `worker-projects` auf Einzel-Zuweisungen umstellen.** Das ist der einzige gemessene Ort, an dem
Lucias Arbeit **dauerhaft** verschwindet, und zwar schon heute ohne jedes Drain-Fenster. Drei Stellen,
niedriges Risiko, der stabile Schluessel `worker_id+"_"+project_id` liegt schon im Code. Es ist der
kleinste Aufwand mit dem einzigen echten Datenverlust dahinter. Wenn nur eine Sache gemacht wird: diese.

**2. Den Merge auf schmutzige Felder umstellen (3d).** Vier Stellen, kein Schema, kein Dialog. Er nimmt
die Information, die im SQ-Eintrag **schon drinsteht**, und hoert auf, sie wegzuwerfen. Er macht die
Anzeige-Veraltung aus Kanal 2 vollstaendig verschwinden, und er ist die **Voraussetzung** fuer Schritt 3
— ohne ihn wuerde ein Umlauf die Fehlerklasse aus `v3.9.597` alle 60 s statt einmal je Start erzeugen.
Die fuenf Namensumsetzungen sind gemessen und aufgezaehlt; sie sind die ganze Schwierigkeit.

**3. Danach den Umlauf auf die Stammdaten ausdehnen (3c).** Das ist der Punkt, an dem Martina und
Lucia zum ersten Mal sehen, was die andere getan hat. **Dass sie es heute die ganze Sitzung lang nicht
sehen, ist der groessere Befund dieser Analyse — und er stand nicht im Auftrag.** Der Objekt-Merge aus
v847/v848 hat ein Fenster von wenigen Sekunden diskutabel gemacht, waehrend daneben ein Fenster von
Stunden offen steht, das niemand bemerkt hat, weil dabei kein Fehler entsteht und nichts kaputtgeht —
die Daten sind nur alt.

**4. Die Fahrzeug-Sammelspalten bewusst liegen lassen**, bis jemand einen konkreten Vorfall dazu
meldet. Sie brauchen eine Schemaaenderung, der Bestand hat den Zweitspeicher einmal bewusst wieder
eingesammelt, und zwei gleichzeitige Schadensmeldungen am **selben** Fahrzeug sind bei dieser
Betriebsgroesse selten. Das ist eine Entscheidung fuer spaeter, keine Schuld.

**Begruendung in einem Satz:** der Feld-Merge ist auf dem Schreibweg schon gebaut, also ist der
befuerchtete Verlust bei Projekten, Mitarbeitern und Fahrzeugen gar keiner — es bleiben ein echter
Verlust an einer anderen Stelle (`worker-projects`), eine Anzeige-Veraltung, die vier Zeilen kostet,
und ein Umlauf, der fehlt; ein Konflikt-Dialog loest von diesen drei Dingen kein einziges.

---

## 5. Was gemessen ist und was Schluss ist

**GEMESSEN (Code, Belegzeichenkette im Text, in `HEAD` und Arbeitsbaum identisch vorhanden):**
* Der Merge ersetzt die Server-Zeile durch das ganze lokale Objekt; die Schutzmenge enthaelt IDs aus
  der URL, nicht Felder aus dem Body.
* Der generische PUT ist ein PATCH und schreibt nur die Spalten im Body.
* Der Projekt-PUT ist ein Feld-Diff; der Voll-Form-Zweig ist unerreichbar (`setEditP(p.id)` nur an der
  Stelle, die den Schnappschuss setzt); die Zahlenfelder erzeugen keinen Scheindiff.
* Der Mitarbeiter-PUT traegt genau ein Feld; es gibt genau einen PUT-Aufrufer.
* Der Fahrzeug-PUT ist spaltenweise (42 Aufrufe, alle mit Body-Former).
* `worker-projects` ist serverseitig Alles-loeschen-dann-einfuegen.
* `_batchDelay:1500`; Entprellung 800 ms (Mitarbeiter) und 300 ms (Regler).
* Es gibt **keinen** periodischen `doSync` (alle 21 `setInterval` und alle `doSync`-Vorkommen geprueft);
  vier Abbruchzweige ohne neuen Termin; der SW-Hintergrundsync erreicht nur offene Clients.
* `projects`/`monteure`/`fahrzeuge` werden nur im Boot-Effekt (`},[curUser]);`) vom Server gelesen;
  der 60-s-Umlauf holt Maengel/Abwesenheiten, der stuendliche `loadAll` gehoert der Export-Ansicht.
* `weekplan_rows` hat **keinen** Konflikt-Dialog, sondern Zeilen-Ebene + Schmutzmenge aus
  Schnappschuss-Vergleich + 30-s-Umlauf + Raeumung im Abfluss.
* Die fuenf Namensumsetzungen fuer 3d, je an ihrer Fundstelle.

**SCHLUSS (Folgerung aus dem Gemessenen, nicht selbst beobachtet):**
* Dass bei Projekten/Mitarbeitern/Fahrzeugen **kein** serverseitiger Feldverlust auftritt. Ich habe
  keinen Lauf mit zwei Geraeten gefahren; das folgt aus PATCH + Diff-Body.
* Dass `type`, `matchcode`, `createdBy`, `tags`, `stundensatz` derzeit nicht aus der App editierbar sind
  (keine gerenderte Eingabe gefunden — ein Negativbefund, also der schwaechere).
* Die Einschaetzung der Haeufigkeit („selten", „bei dieser Betriebsgroesse") — Erfahrungswert, nicht gemessen.
* Die Reihenfolge der Empfehlung.

**NICHT MESSBAR OHNE DB-ZUGRIFF — ausdruecklich offen:**
* Ob `projects.updated_at`, `workers.updated_at`, `fahrzeuge.updated_at` in der **laufenden** DB
  existieren. Aus dem Code: sie werden bei jedem PATCH gestempelt und stehen nicht auf der
  Ausnahmeliste; ein Fehlen ergaebe `PGRST204` → Verwerfen nach fuenf Versuchen. Da das Bearbeiten
  funktioniert, **SCHLUSS:** sie existieren. Ein Beleg ist das nicht.
* Ob `worker_projects` den PK auf `id` in der Form `worker_id+"_"+project_id` fuehrt, und ob RLS ein
  Einzel-DELETE erlaubt. **Vor Schritt 1 in der DB nachzusehen.**
* Ob der ausgelieferte Stand diesem Arbeitsbaum entspricht. Ich habe Arbeitsbaum **und** `HEAD`
  gegeneinander gemessen, aber nicht den Live-Stand. Nach dem Muster dieses Bestandes gilt: **was live
  laeuft, ist erst belegt, wenn es am Live-Stand nachgemessen ist.**
* Keine Aussage dieser Datei stammt aus einer Datei unter `sql/`.
