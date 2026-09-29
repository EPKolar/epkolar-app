# Stiller Datenverlust — Bughunt 30.09.2026

**Gebiet:** alles, wo ein Monteur glaubt, etwas sei gespeichert, und es ist
nicht gespeichert.

**Umfang der Messung.** `index.html` allein, 30 310 Zeilen, Fassung
`APP_VERSION="3.9.990-supabase"`, Arbeitsbaum auf `99037e4` (die Datei selbst
ist seit `114922c` unverändert). Gemessen wurde **nur der Quelltext** — kein
Lauf im Browser, keine DB-Abfrage. Wo eine Aussage einen Lauf gebraucht
hätte, steht sie als ⚪ und nicht als 🔴.

**Kein Eingriff.** `index.html` wurde nicht angefasst, kein `commit`, kein
Push. Diese Datei ist die einzige, die dieser Lauf im Repository angelegt hat.

---

## Ergebnis in Zahlen

| Stufe | Anzahl |
|---|---:|
| 🔴 Datenverlust / falsche Zahl beim Nutzer | **4** |
| 🟡 falsch, aber folgenlos oder selbstheilend | **5** |
| ⚪ nicht zu Ende gemessen | **2** |
| ✅ nachgesehen und in Ordnung | **9 Klassen** |

Die drei schärfsten:

1. **B1** — Zeitänderung am Arbeitsschein: der Monteur bestätigt „Zeitänderung
   auf 7,50 h übernehmen?", die Übernahme scheitert, und **er sieht überhaupt
   nichts**. Schein und Zeiterfassung stehen danach auf verschiedenen Stunden.
2. **B3** — drei Wege, auf denen ein Foto beim Anhängen **lautlos
   verschwindet**: `compressPhoto` wirft bei nicht lesbaren Dateien, und an
   drei von elf Aufrufstellen fängt das niemand auf.
3. **B4** — der 0‑Zeilen‑Wächter, der 2026‑06 gegen den stillen
   RLS‑Erfolg gebaut wurde, deckt **11 von 27** Tabellen ab, die per
   `PUT`/`PATCH` aus der Warteschlange geschrieben werden. Bei den anderen 16
   gilt „HTTP 200 mit 0 getroffenen Zeilen" weiter als Erfolg, und das Element
   wird aus der Warteschlange **gelöscht**.

---

## Wie hier gemessen wurde

Das vorhandene Werkzeug `scripts/stille_schreibfehler.py` misst genau **eine**
Form: ein leeres (oder nur kommentiertes) `catch` am **innersten** `try` um
einen Schreibaufruf. Sein Ergebnis auf dieser Fassung: 844 try/catch‑Paare,
69 `_sb*`‑Schreibaufrufe, **3** verworfene Schreibfehler — alle drei
`plz_geo`/`plz_distanz` und alle drei begründet. Das ist richtig und
vollständig **für diese Form**.

Dieser Lauf hat vier weitere Formen gemessen. Jede mit eigener Eichung; eine
Null ohne bestandene Eichung steht hier nicht als Ergebnis.

| | Form | Köder | Ergebnis |
|---|---|---|---|
| A | Schreibaufruf **ohne `await`**, ohne `.then`, ohne `.catch` | 9 Köder je Handhabungsform (`FREILAUF`, `awaited`, `return`, `void`, `then` mit/ohne `catch`, `zugewiesen`, `Promise.all`) | 0 echte (7 „Treffer" waren die Definitionen der Helfer selbst) |
| B | `.then(...)` **ohne** `.catch(...)` | 3 Köder (Kette mit `catch`, ohne `catch`, mit `finally`) | 33 Ketten, davon **2** mit Datenverlust |
| C | `catch`, das den Fehler **nur in die Konsole** schreibt | 13 Köder je `catch`-Rumpfform | **11** Stellen |
| D | Folgearbeit **hinter** einem `await` im selben Block, bei schweigendem `catch` | 2 Köder (mit / ohne Folgearbeit) | **1** Stelle |
| E | Zustand **vor** der Serverbestätigung gesetzt, keine Rücknahme im `catch` | 2 Köder | 4 Stellen, davon 0 neue |

Zerlegt wurde durchgängig per Klammerabgleich, nie per `slice` zwischen zwei
Namen. Für Klasse D wird die Folgearbeit auf **derselben Klammertiefe**
gemessen wie der Aufruf — ein roher Reststring hätte die schließenden
Klammern umgebender Blöcke als „Arbeit" mitgezählt und aus 1 Treffer 5
gemacht.

### 🔴 Zwei eigene Messfehler, die während des Laufs aufgefallen sind

Beide gehören in den Bericht, weil sie sonst der nächste Leser wiederholt.

**(1) Mein Sichtbarkeits-Muster kannte den Hauptkanal der App nicht.**
Klasse C fragt: „zeigt dieses `catch` dem Nutzer etwas?" Dazu braucht es die
Liste der Ausgabewege. Meine erste Liste enthielt `_showToast` — **57**
Vorkommen — und **nicht** `window.__toast` — **665** Vorkommen. Damit galten
neun sauber meldende Funktionen (`delPhoto`, `delWzPhoto`, `_saveTpl`,
`_imeiSpeichern`, `addTank`, `_addAsFotos`, `_assign`, `_speichern`,
`_juprowaSync`) als stumm. Aufgefallen ist es **nicht am Riegel**, sondern
beim Ansehen eines gemeldeten Falls: `delPhoto` (Z19178) meldet einwandfrei.
Das ist [[mlg-regel-koeder-teilt-die-luecke]] — mein Köder benutzte dieselbe
Schreibweise wie mein Muster. Nach der Korrektur: Klasse C bleibt bei **11**
(keiner der elf hat einen Toast), die Liste der „stumm schreibenden"
Funktionen fällt von **29 auf 0**.

**(2) `code_scan._klammer_zu` kennt keine Regex-Literale.**
`_translateAndExec` enthält `/^\/api\/([a-z_-]+?)(?:\/(.+))?$/i`. Der
Klammerabgleich überspringt Zeichenketten, aber kein Regex; ein
Anführungszeichen darin öffnet eine Zeichenkette, die nie geschlossen wird.
Gemessen: der Funktionsrumpf kam mit **2 195 Zeilen** zurück statt mit
**341** — also viermal so viel Code, wie die Funktion hat. Jede Zahl daraus
wäre eine Aussage über eine fremde Grundgesamtheit gewesen. Der Abgleich
läuft seither über `code_scan.ist_code`, das Regex-Literale kennt; geeicht
gegen eine kurze Funktion mit bekanntem Ende (`_sbDeleteWhere`, 4 Zeilen).

**(3) Eine Null, die kein Ergebnis war.** Für die Doppelklick-Suche habe ich
`SQ.push`-Aufrufe gezählt, deren `id` im Argument erzeugt wird
(`uid()`, `Date.now()`, `crypto.randomUUID()`). Ergebnis: **0 von 50**. Der
Köder war bestanden — und die Null trotzdem wertlos: Z13977 schreibt
`{id:_uuid(), ...}`, und `_uuid()` stand nicht in meiner Liste. Wieder eine
zweite Schreibweise. Die Doppelklick-Frage steht deshalb unten als ⚪ und
nicht als ✅.

---

# 🔴 Die Befunde

## 🔴 B1 — Zeitänderung am Arbeitsschein verschwindet lautlos

**Stelle:** `index.html:11134`, in `_asZeitUebernahme` (Definition Z11098),
Komponente `ArbeitsscheinView`.

```
11126  const _ex=await _sbGet("time_entries","arbeitsschein_id=eq."+…);
11127  if(!_ex||!_ex.length)return;
11128  const _cur=_ex[0];
11129  if(Math.abs(Number(_cur.hours||0)-_h)<0.005)return;
11130  if(_asZeitRolleConfirm(curUser&&curUser.role)){
11131    const _ok=await _confirmModal("Zeitänderung auf "+_n(_h,2)+"h in die Zeiterfassung übernehmen?");
11132    if(!_ok)return;
11133  }
11134  await _sbPatch("time_entries",_cur.id,{hours:_h});
11135  if(window.__toast)window.__toast("⏱ Zeiterfassung aktualisiert: "+…);
11136 }catch(_e){console.warn('[as-zeit-uebernahme]',_e&&_e.message||_e);}
```

**Ablauf.** Ein Arbeitsschein, dessen Zeit **schon einmal** in die
Zeiterfassung übernommen wurde (`ze_uebernommen === true`), wird geöffnet;
Arbeitszeit oder Fahrzeit werden geändert; **Speichern**. `saveAs` ruft am
Ende `_asZeitUebernahme({..._finalForm,id:editId})` (Z11191, absichtlich ohne
`await`). Dort greift der `else`-Zweig ab Z11125: der bestehende
`time_entries`-Eintrag wird gesucht und per `PATCH` auf die neuen Stunden
gesetzt. Büro/PL bekommen vorher noch den Bestätigungsdialog aus Z11131.

**Was der Nutzer sieht.** Toast „✅ Schein aktualisiert" (aus `saveAs`), dann
den Bestätigungsdialog, dann — bei Ausfall des `PATCH` — **nichts**. Kein
Erfolgstoast (Z11135 steht *hinter* dem `await` im selben `try` und fällt mit
aus), keine Fehlermeldung (Z11136 schreibt nur in die Konsole).

**Was wirklich passiert ist.** `arbeitsscheine` trägt die neue Zeit,
`time_entries` trägt die alte. Der Schein gilt als übernommen
(`ze_uebernommen` bleibt `true`), also wird beim nächsten Speichern **nicht**
erneut versucht. Die Abweichung ist dauerhaft und lohnrelevant.

**Wie gemessen.** Klasse C (`catch` nur Konsole) und Klasse D (Folgearbeit
hinter dem `await`) melden **dieselbe** Stelle — Klasse D mit genau einem
Treffer auf der ganzen Datei, bei bestandener Eichung. `_sbPatch` wirft
belegbar: seine Definition Z2273 prüft 401 und 403, ruft `_onAuthFail` und wirft, und jeder
Nicht‑2xx wirft mit `"HTTP"+status`.

**Die Asymmetrie ist der Beleg.** Der **Einfüge**-Zweig derselben Funktion
(Z11104–11123, erstmalige Übernahme) hat alles: eigenes `try/catch` um den
`_sbPost`, eine Sonderbehandlung für den UNIQUE‑Konflikt eines
Parallelgeräts (Z11111, v3.9.815), einen Toast „⚠️ Schein-Zeit noch NICHT
übernommen (offline/Serverfehler) — wird beim nächsten Speichern erneut
versucht" (Z11118) und ein bewusstes Nicht‑Setzen des Merkers. Der
**Änderungs**-Zweig, 11 Zeilen weiter unten, hat davon nichts. Der Zwilling
wurde geheilt, das Geschwister nicht.

---

## 🔴 B2 — Der Juprowa-Abgleich meldet Scheine als geschrieben, die nicht geschrieben wurden

**Stelle:** `index.html:3979` und `index.html:3985`, in `_juprowaSync`
(Definition Z3911).

```
3979   try{await _sbPatch("arbeitsscheine",existing.id,_mapBody(upd));}catch(e){console.warn('[silent-await]',…);}
3980   if(hasFieldChanges){updated++;}else{skipped++;}
…
3985   try{await _sbPost("arbeitsscheine",_mapBody(newAs));}catch(e){console.warn('[silent-await]',…);}
3986   newItems.push(newAs);
3987   added++;
…
3995   if(!silent) window.__toast("🔄 Juprowa: "+added+" neu, "+updated+" aktualisiert, "+skipped+" unverändert")
```

**Ablauf.** Büro drückt den Juprowa-Sync-Knopf (oder der Auto-Sync läuft).
Für jeden Schein wird entweder gepatcht (Z3979) oder eingefügt (Z3985).
Jeder der beiden Aufrufe steckt in einem **eigenen** `try`, dessen `catch`
nur `console.warn` schreibt — und **der Zähler steht hinter dem `catch`**,
also läuft er in jedem Fall hoch.

**Was der Nutzer sieht.** „🔄 Juprowa: 12 neu, 3 aktualisiert, 40
unverändert".

**Was wirklich passiert ist.** Bei RLS‑Ablehnung, 4xx oder Netzausfall: null
geschriebene Zeilen bei einer Meldung über 15. Z3992 lädt anschließend
`_asPullFresh` **frisch aus der DB** — die Liste zeigt also die Wahrheit,
während der Toast etwas anderes behauptet. Das Büro liest die Zahl, nicht die
Liste.

**Was das relativiert.** Juprowa ist die autoritative Quelle; beim nächsten
Abgleich wird derselbe Schein wieder als neu/geändert erkannt und erneut
versucht. Es geht also **keine Nutzereingabe** verloren, der Zustand heilt
sich beim nächsten Lauf. Deshalb steht hier 🔴 für *„falsche Zahl beim
Nutzer"*, nicht für *„Datenverlust"* — und das ist nicht dasselbe, auch wenn
beide dieselbe Farbe haben.

**Ein Seiteneffekt heilt nicht mit.** In `upd` kann `push_pending=true`
stecken (Z3976, Prio-Heilung v3.9.798). Fällt der `PATCH` aus, wird das Feld
nicht gesetzt und der zugehörige Juprowa-Push (`AK_PRIOR 4`) läuft nicht —
bis der nächste Abgleich die Heilbedingung erneut erkennt.

**Wie gemessen.** Klasse C, Stellen 3 und 4 der elf. Beide `catch`-Rümpfe
enthalten ausschließlich `console.warn`; nach der Korrektur des
Sichtbarkeitsmusters (siehe oben) hat sich an dieser Einordnung nichts
geändert.

---

## 🔴 B3 — Drei Wege, auf denen ein angehängtes Foto lautlos verschwindet

**Der Ausgangspunkt ist gemessen, nicht vermutet:** `compressPhoto`
(Z6281) **wirft**. Zwei Wege:

```
6284   reader.onerror=()=>reject(new Error("Datei nicht lesbar"));
6287   img.onerror=()=>reject(new Error("Bild ungültig"));
```

`createThumbnail` (Z6268) wirft dagegen nie — es ruft bei `onerror` einfach
`resolve(dataUrl)`.

Von **elf** Aufrufstellen von `compressPhoto` sind acht abgesichert
(`.catch(...)` oder ein `try`, dessen `catch` meldet). Drei sind es nicht:

| Stelle | Ort | Handhabung |
|---|---|---|
| `index.html:7008` | `KundenPortal`, Feld „📷 Foto aufnehmen / auswählen" | `.then(…)` ohne `.catch`, kein `try` |
| `index.html:17029` | `VMang`, Knopf „📷 Foto" am neuen Mangel | `.then(…)` ohne `.catch`, kein `try` |
| `index.html:16888` | `VMang`, `uploadDefectPhoto` (Z16886) | `await`, `catch` schreibt nur `console.warn` |

**Ablauf (alle drei gleich).** Monteur bzw. Kunde tippt auf „Foto", wählt im
Dateidialog ein Bild, das der Browser nicht dekodieren kann — HEIC/HEIF vom
iPhone in einem Android-Chrome, ein abgebrochener Kamera-Schreibvorgang, ein
Bild, das die Canvas-Grenze reißt.

**Was der Nutzer sieht.** Der Dateidialog schließt sich, und **nichts
passiert**. Kein Vorschaubild, keine Meldung. Bei Z16888 fällt zusätzlich der
Erfolgstoast „📷 Foto hinzugefügt" (Z16894) mit aus, weil er im selben `try`
hinter dem `await` steht — dieselbe Form wie B1.

**Was wirklich passiert ist.** Bei Z7008/Z17029 eine unbehandelte Zusage: der
Browser schreibt „Uncaught (in promise) Error: Bild ungültig" in eine
Konsole, die auf der Baustelle niemand offen hat. Das Foto kommt weder in
`newMangel.photos`/`newPhotos` noch in die Foto-Warteschlange. Der Mangel
wird ohne Nachweisfoto gespeichert — bei einem Kundenportal-Mangel ohne das
Bild, das der Kunde zur Begründung mitschicken wollte.

**Der Beleg, dass es anders geht,** steht 40 Zeilen weiter: `captureAndQueue`
(Z3547) fasst denselben Aufruf in ein `try`, dessen `catch` „⚠ Foto-Aufnahme
fehlgeschlagen: …" zeigt (Z3572, v3.5.146 — „besser informative Message statt
silent return"). Dieselbe Kur an drei Stellen nicht angekommen.

**Wie gemessen.** Klasse B über alle `.then`-Ketten der Datei (33 ohne
`.catch`, Ketten per Klammerabgleich abgegangen, Eichung an drei
selbstgebauten Ketten bestanden), danach je Aufrufstelle das innerste
umschließende `try` bestimmt. Die übrigen 31 Ketten ohne `.catch` sind
harmlos, weil ihr Kopf nicht ablehnen kann — `captureAndQueue`,
`PhotoQ.add/getAll/count/flush/remove/clear` sind alle vollständig in
`try/catch` gefasst; das wurde je Funktion einzeln geprüft, nicht angenommen.

---

## 🔴 B4 — Der 0-Zeilen-Wächter deckt 11 von 27 Tabellen

**Stelle:** `index.html:2947–2956`, in `_translateAndExec`.

```
2947   const _patchRes=await _sbPatch(table,idOrSub,patchData);
2954   if(_RLS_SILENT_DENIAL_LABELS[table]&&Array.isArray(_patchRes)&&_patchRes.length===0){
2955     window.__toast("⚠️ "+_RLS_SILENT_DENIAL_LABELS[table]+" NICHT gespeichert — keine Schreibberechtigung. …")
2956   }
```

**Warum es diesen Wächter gibt** (Kommentar Z2948, v3.9.306): PostgREST
antwortet auf einen `PATCH`, der keine Zeile trifft, mit **HTTP 200 und einem
leeren Array**. Ohne Prüfung ist das von Erfolg nicht zu unterscheiden. Genau
so ging 2026 der Tankbeleg verloren, und genau so kam freigegebener Urlaub
„nach Reload wieder offen" (v3.9.623, `absences`).

**Der Befund ist der Zuschnitt.** `_RLS_SILENT_DENIAL_LABELS` (Z2616) enthält **11**
Tabellen: `absences`, `arbeitsscheine`, `bautagebuch`, `fahrzeuge`, `forms`,
`fz_schaeden`, `material_catalogs`, `plans`, `time_entries`, `users`,
`workers`. Aus der Warteschlange werden per `PUT`/`PATCH` aber **27**
Tabellen geschrieben. Ungedeckt sind **16**:

| Tabelle | Stellen | Beispielzeilen |
|---|---:|---|
| `werkzeuge` | 14 | 29601, 29706, 29714, 29715, 29721 |
| `defects` | 11 | 16921, 16931, 16935, 16942, 16954 |
| `projects` | 5 | 15678, 15689, 15801, 18317 |
| `finkzeit` | 4 | 23297, 23303, 23333, 23352 |
| `project_documents` | 3 | 19434, 19444, 19450 |
| `tickets` | 3 | 16913, 18385, 18440 |
| `bauprovisorien_mieten` | 2 | 29385, 29398 |
| `bauprovisorien`, `checklists`, `fz_termine`, `gefahrstoff_folders`, `material_orders`, `notifications`, `project_folders`, `supplier_configs`, `supplier_orders`, `worker_projects` | je 1 | 29373, 16660, 27964, 29182, 20296, 9133, 19391, 13978, 20886, 10174 |

**Ablauf.** Monteur ändert in der Werkzeugansicht den Standort eines
Werkzeugs. `SQ.push({url:"/api/werkzeuge/<id>",method:"PUT",body:…})`, Toast,
Ansicht weiter. `doSync` drainiert, `_translateAndExec` patcht, `_patchRes`
ist `[]`, Z2954 greift nicht (`werkzeuge` steht nicht in der Liste),
`return{ok:1}` — und in `doSync` (Z8998) landet die Kennung in `okIds`, aus
denen `SQ.removeMany` das Element **löscht**.

**Was der Nutzer sieht.** „Gespeichert". Der Zustand bleibt, bis er die App
neu lädt.

**Was wirklich passiert ist.** Die Datenbank trägt den alten Wert, die
Warteschlange ist leer, es gibt keinen Wiederholversuch und keinen Eintrag in
`syncQueueFailed`. Nach dem nächsten Laden ist die Änderung fort.

**Wann 0 Zeilen entstehen.** Zwei Ursachen, und nur die erste hängt an RLS:

* **RLS-Filter** — dafür wurde der Wächter gebaut; der Kommentar Z2952 nennt
  ihn ausdrücklich „Defense-in-Depth für RLS-Welle-1", also für den Fall, dass
  RLS auf weiteren Tabellen scharf gestellt wird.
* **Die Kennung existiert am Server nicht** — und das ist von RLS unabhängig
  und **im eigenen Entwurf vorgesehen**: `doSync` verwirft ein Element nach
  fünf Fehlversuchen (Z9017). Ist das verworfene Element das `POST`, das den
  Datensatz anlegen sollte, trifft **jeder weitere `PATCH` auf diese Kennung
  dauerhaft 0 Zeilen** — und wird dauerhaft als Erfolg gemeldet. Der *Verwurf*
  wird noch angezeigt („⚠ N Sync-Einträge nach 5 Versuchen verworfen", Z9033);
  die Folgeschreibvorgänge auf den nie angelegten Datensatz nicht mehr.

**Wie gemessen.** `_RLS_SILENT_DENIAL_LABELS` und `ROUTE_MAP` per
Klammerabgleich auf dem Code-Feld gelesen (Eichung bestanden, siehe
Messfehler (2)); alle 188 `SQ.push`-Aufrufe per Klammerabgleich zerlegt,
Methode und Adresse je Aufruf herausgezogen, Ressource über `ROUTE_MAP` auf
die Tabelle abgebildet, gegen die Wächterliste gestellt.

**Noch nicht gemessen** und deshalb hier ausdrücklich gesagt: **ob** auf einer
der 16 Tabellen heute RLS scharf ist. Das ist eine DB-Frage, kein Quelltext.
Die *zweite* Ursache (Kennung existiert nicht) trägt den Befund ohne jede
RLS-Annahme.

---

# 🟡 Folgenlos oder selbstheilend

## 🟡 B5 — Eine unbekannte Route gilt als Erfolg und wird aus der Warteschlange gelöscht

**Stellen:** `index.html:2633`, `2913`, `2942`, `2958`.

```
2633   if(!m)return{ok:1}; // ignore unrecognized
2913   if(!entry){console.warn("[api] Unknown route:",url);return{ok:1};}
2942   if(!idOrSub){console.warn("[api] PUT without ID:",url);return{ok:1};}
2958   if(!idOrSub){console.warn("[api] DELETE without ID:",url);return{ok:1};}
```

Jedes `return{ok:1}` heißt für `doSync`: erledigt, Element entfernen. Eine
Ressource, die die Oberfläche in die Warteschlange legt und die
`ROUTE_MAP` (Z2307) nicht kennt, ist damit **ein permanenter, lautloser Verlust** mit
einer Konsolenzeile als einziger Spur.

**Gemessen: heute trifft es nichts.** Alle 188 `SQ.push`-Aufrufe zerlegt, die
Adressen herausgezogen: **37** verschiedene Ressourcen als Literal, dazu die
drei Unterrouten `/api/notifications/batch`, `/read-all`, `/clear`. Alle 37
stehen in `ROUTE_MAP` (die 40 Schlüssel hat), alle drei Unterrouten haben
einen eigenen `idOrSub`-Zweig (Z2684, 2700, 2709). Keine Adresse wird aus
einem Variablennamen zusammengesetzt; die einzige dynamische Stelle (Z11191)
ist ein Ternär aus zwei Literalen. Der Testfall `/api/ztest<i>` (Z930) räumt
seine Warteschlange selbst auf.

**Warum es trotzdem hier steht.** Der Mechanismus **hat schon einmal
zugeschlagen**, und zwar genau so: Kommentar Z2318 — *„v3.9.399 FIX:
anmeldungen fehlte in ROUTE_MAP → /api/anmeldungen war No-op"*. Eine neue
Ressource, bei der jemand den `ROUTE_MAP`-Eintrag vergisst, ist wieder ein
stiller Totalverlust — und nichts im Bau merkt es. Der Abgleich
„SQ.push-Adressen ⊆ ROUTE_MAP-Schlüssel" ist maschinell prüfbar; dass er
heute aufgeht, ist gemessen, aber nicht gesichert.

## 🟡 B6 — Beim Löschen kann 0 Zeilen gar nicht erkannt werden

**Stelle:** `index.html:2957–2967` (`DELETE`-Zweig) und `_sbDelete` (Definition Z2278).

Der 0-Zeilen-Wächter aus B4 steht **nur** im `PUT`/`PATCH`-Zweig. Im
`DELETE`-Zweig gibt es ihn nicht — und er könnte dort auch nicht stehen:
`_sbDelete` schickt `_sbH()` (Z1464, **ohne** `Prefer`) statt `_sbWH()`
(Z1483, das `Prefer: return=representation` setzt) und gibt fest `{ok:1}`
zurück. Die Antwort enthält also keine Zeilen, aus denen man 0
ablesen könnte. Ein `DELETE`, das RLS wegfiltert oder dessen Kennung nicht
existiert, ist strukturell nicht von einem erfolgreichen unterscheidbar.

**Was der Nutzer sieht:** die Zeile ist weg. **Was passiert ist:** sie ist in
der Datenbank. Nach dem nächsten Laden ist sie wieder da. Kein Datenverlust —
die verlorene Handlung ist eine Löschung — und der Fehler verrät sich beim
Neuladen. Deshalb 🟡.

## 🟡 B7 — Die Lösch-Kaskade eines Projekts hinterlässt Waisen

**Stelle:** `index.html:2965`.

```
for(const _kt of _kids){try{await _sbDeleteWhere(_kt,_pid);}catch(_ce){console.warn("[api] cascade "+_kt+":",_ce…);}}
```

Neun Kindtabellen (`plans`, `tickets`, `checklists`, `defects`,
`project_documents`, `project_folders`, `photos`, `material_orders`,
`bautagebuch`) werden vor dem Projekt gelöscht, jede in ihrem eigenen `try`.
Scheitert eine, läuft die Kaskade weiter und Z2967 löscht das Projekt
trotzdem — die Kinder verwaisen mit einer `project_id`, die es nicht mehr
gibt. Niemand erfährt es.

Der Kommentar Z2960 nennt das als **Absicht**: „fehlende Spalte/RLS blockt
das Projekt-Delete nicht", und er nennt auch den richtigen Weg: ein
`ON DELETE CASCADE` in der Datenbank. Bewusste Entscheidung, deshalb 🟡 und
kein Befund gegen den Autor — aber die *Folge* ist unsichtbar, und das muss
irgendwo stehen.

## 🟡 B8 — Ein `try` um einen nicht abgewarteten Aufruf fängt nichts

**Stelle:** `index.html:3996`.

```
try{const _u=JSON.parse(localStorage.getItem('epkolar_user')||'null');
    _sbPost("activity_log",{user_id:…,action:"juprowa_pull",details:…});
}catch(e){console.warn('[silent-json]',…);}
```

`_sbPost` steht ohne `await` und ohne `.catch`. Das `try` fängt nur das
synchrone `JSON.parse`; die Ablehnung des `_sbPost` läuft als unbehandelte
Zusage daran vorbei. Betroffen ist das Protokoll, nicht die Nutzdaten —
folgenlos.

**Dass das ein Muster ist, weiß der Autor:** 250 Zeilen weiter steht
derselbe Aufruf **richtig**, mit Begründung (Z4244): *„v3.9.220 #9:
fire-and-forget braucht .catch — umschließendes try fängt nur das synchrone
JSON.parse, nicht die async _sbPost-Rejection"*. Drei Geschwister (Z4242,
4244, 4250) haben das `.catch(()=>{})`; Z3996 nicht.

Dies ist der **einzige** echte Freilauf-Treffer der Klasse A auf der ganzen
Datei.

## 🟡 B9 — Ein leeres `catch` macht aus jedem Wiederholversuch eine Speicher-Waise

**Stelle:** `index.html:3527`, in `PhotoQ.flush`.

```
if(!publicUrl){const storagePath=_storagePath("photos",ph.projectId,ph.name||"photo.jpg");
  publicUrl=await _sbUploadFile(storagePath,ph.dataUrl);
  try{await PhotoQ.update(ph.id,{file_path:publicUrl});}catch(_pu){}}
```

Der Kommentar darüber (Z3525, v3.9.579) sagt, wozu das `file_path` gespeichert wird:
*„bereits hochgeladene URL wiederverwenden statt re-upload — sonst erzeugt
jeder DB-Post-Fail-Retry via `_storagePath` (Date.now()-Präfix) ein NEUES
Storage-Objekt → Waise ohne DB-Verweis."* Genau dieses Speichern steht in
einem leeren `catch`. Scheitert es (IndexedDB voll, Schreibfehler), ist die
Kur wirkungslos und jeder Wiederholversuch legt erneut eine Waise im
Speicher-Bucket ab. Keine Nutzdaten verloren, nur Müll und Speicherplatz —
und `PhotoQ.update` schluckt seinerseits alles mit `console.warn`.

---

# ⚪ Nicht zu Ende gemessen

## ⚪ C1 — Der Erfolgstoast steht vor der Persistenz

**Gemessen:** **188** `SQ.push`-Aufrufe im Code, davon **15** mit `await`. In
den übrigen 173 läuft der Aufrufer sofort weiter — Z11191 ist das Muster:
`SQ.push({...})`, dann Vibration, dann Toast „✅ Schein aktualisiert", dann
`setSub("liste")`, `setEditId(null)`.

`SQ.push` (Z3467) kann nicht ablehnen — `_serial` (Z3466) hängt ein
`.catch(()=>{})` an — und sein inneres `catch` zeigt bei einem
IndexedDB-Fehler einen Toast: „⚠️ Änderung konnte nicht zwischengespeichert
werden — Gerätespeicher evtl. voll…" (v3.9.574). Der Nutzer bekommt also
**beide** Meldungen, die falsche zuerst.

**Was fehlt:** ein Lauf, der zeigt, was bei einem Neuladen im Fenster
zwischen Toast und `ODB.save` passiert. Das ist eine Messung im Browser mit
gedrosseltem IndexedDB, nicht im Quelltext. Keine Behauptung ohne diesen Lauf.

## ⚪ C2 — Doppeltes Absenden: nicht vollständig gemessen

**Vorhanden sind Riegel:** `_epkSyncInflight` (Z8968, mit Begründung „zwei
rapid clicks … konnten beide durchflashen → doppelte Server-Writes"),
`_saveAsInFlightRef` mit 800‑ms‑Fenster (Z11139), `_addEntryInFlightRef`,
`__addKmInFlight`, `__addTankInFlight`, `setSubmittingMangel`, `setSaving`,
`setBusy`, `tplSaving`. Die großen Anlegewege tragen also einen.

**Warum hier keine Zahl steht:** meine Zählung der Anlegewege ohne Riegel
lieferte 0 von 50, und diese Null war wertlos — `_uuid()` fehlte in meinem
Muster (siehe Messfehler (3)). Eine ungeeichte Null wird hier nicht als
Ergebnis geführt. Zu klären bleibt außerdem, ob `_translateAndExec` einen
Doppelklick ohnehin abfängt: bei `mapped.id` läuft der `POST` über
`_sbInsertIfAbsent` (Z2940, `ON CONFLICT DO NOTHING`), was **gleiche**
Kennungen entschärft — zwei Klicks erzeugen aber in der Regel **zwei**
Kennungen.

---

# ✅ Nachgesehen und in Ordnung

Damit niemand zweimal sucht. Jede Zeile ist eine Messung, keine Einschätzung.

1. **Die sechs Schreib-Helfer sind sauber.** `_sbPost`, `_sbUpsert`,
   `_sbInsertIfAbsent`, `_sbPatch`, `_sbDelete`, `_sbDeleteWhere`
   (Definitionen Z2221, 2226, 2265, 2273, 2278, 2284) prüfen jeder auf 401
   und 403, rufen `_onAuthFail` und werfen mit Status im
   Text; jeder Nicht‑2xx wirft. Am Helfer ist nichts zu reparieren — das war
   die Vorgabe und sie hält.

2. **Klasse A auf Helfer-Ebene: kein Fall.** Die sieben Treffer der ersten
   Zählung (Z1737, 2221, 2226, 2265, 2273, 2278, 2284) waren die
   **Definitionen** der Helfer selbst — `async function _sbPost(` enthält
   `_sbPost(`. Echter Freilauf bleibt genau einer: B8.

3. **Klasse A eine Ebene höher: kein Fall.** 210 `async`-Definitionen; 158
   können werfen (Rumpf nicht vollständig in `try/catch`, oder das `catch`
   wirft weiter); davon schreiben 45 direkt oder über die Warteschlange; **9**
   schreiben direkt **und** werden irgendwo ohne `await`/`.catch` gerufen —
   `_addAsFotos`, `_assign`, `_imeiSpeichern`, `_juprowaSync`, `_saveTpl`,
   `_speichern`, `addTank`, `delPhoto`, `delWzPhoto`. **Alle neun melden dem
   Nutzer.** Geprüft nach der Korrektur des Sichtbarkeitsmusters; vorher las
   sich dieselbe Messung als 29 stumme Fälle.

4. **`delPhoto` (Z19178) und `delWzPhoto` (Z29630)** löschen erst, ändern
   dann den Zustand, und ihr `catch` zeigt „❌ Foto konnte nicht gelöscht
   werden — bitte erneut versuchen". Vorbildlich.

5. **Klasse E: keine optimistische Anzeige ohne Rücknahme.** Vier Stellen
   setzen Zustand vor einem direkten Schreibaufruf: Z5375 (Geo-Zwischen-
   speicher, begründet), Z8649 und Z8658 (Erstbefüllung `INIT_PROJECTS` /
   `MONT` beim ersten Start — ein Fehler dort heißt „leere App", nicht
   „falsche Anzeige"), Z24206 (`WorkerNfcPanel`, mit Rücknahme im `catch`).
   Das optimistische Muster lebt in der Warteschlange, und dort ist es
   Absicht: das Element bleibt liegen, bis es durch ist.

6. **Der Vertrag zwischen Warteschlange und Übersetzer ist vollständig.**
   37 Ressourcen + 3 Unterrouten aus 188 `SQ.push`-Aufrufen, alle in
   `ROUTE_MAP` bzw. mit eigenem Zweig. Siehe B5 — der Mechanismus bleibt eine
   Falle, aber heute steht nichts darin.

7. **Der Verwurfsweg in `doSync` schweigt nicht.** Nach fünf Fehlversuchen:
   Eintrag in `ODB("syncQueueFailed")` mit `failedAt`, `lastError` und den
   Feldnamen des Rumpfes (Z9024), eine `console.error`-Zeile mit HTTP-Status,
   und **ein Toast** „⚠ N Sync-Einträge nach 5 Versuchen verworfen: …"
   (Z9033, gedrosselt auf eine Meldung je Lauf). Transiente Fehler (offline,
   5xx, 408, 429) halten die Warteschlange und stoppen den Lauf; permanente
   4xx laufen in den Zähler. 403 fällt seit v3.9.159 bewusst in den Zähler
   statt die Warteschlange zu verstopfen.

8. **Speichermangel wird gemeldet, nicht verschluckt.** `SQ.push` (Toast in
   Z3475) und `PhotoQ.add` (Z3497; Z3502 nutzt `ODB.set` statt `ODB.save`,
   damit `QuotaExceeded` wirklich wirft) führen beide zu einem Toast;
   `PhotoQ.add` gibt `false` zurück, und `captureAndQueue` (Z3547, Auswertung
   Z3558) wertet das aus.
   `SQ.count`/`PhotoQ.count` setzen bei Lesefehler einen Merker
   (`_leseFehler`), damit die 0 nicht als „nichts offen" durchgeht.

9. **Der Storage-Upload im Übersetzer wirft weiter, statt zu schlucken**
   (Z2935, v3.9.861) — mit einer der besten Begründungen der Datei: ein
   geschluckter Upload-Fehler hätte entweder die Warteschlange mit einem
   20‑MB‑Rumpf verkeilt oder nach fünf Versuchen still verworfen, während die
   Oberfläche den Upload als erledigt zeigt.

---

## Was als nächstes zu messen wäre

Nicht als Auftrag, sondern damit die Lücken benannt sind:

* **B4 zu Ende bringen:** auf welchen der 16 ungedeckten Tabellen ist RLS
  heute scharf? Das ist eine Abfrage in der Datenbank, nicht im Quelltext.
* **C1:** ein Lauf im Browser mit gedrosseltem IndexedDB — was passiert bei
  einem Neuladen zwischen Toast und `ODB.save`?
* **C2:** die Anlegewege ohne Doppelklick-Riegel, mit einem Muster, das
  *jede* Schreibweise der Kennungs-Erzeugung kennt — mindestens `uid()`,
  `_uuid()`, `Date.now()`, `crypto.randomUUID()` — und einem Köder je Form.
* **Ein Riegel für B5:** „jede Adresse in einem `SQ.push` hat einen
  `ROUTE_MAP`-Schlüssel". Das ist in zwanzig Zeilen prüfbar und hätte
  v3.9.399 verhindert.
