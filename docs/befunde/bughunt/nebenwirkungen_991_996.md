# Nebenwirkungen der elf Kuren aus v3.9.991 bis v3.9.996

**Frage:** Hat eine der Kuren eine Wirkung auf einen AUFRUFER, die niemand
gesehen hat?

**Quelle der Wahrheit:** `index.html` im Arbeitsbaum (v3.9.996, unveraendert
seit `1d6a6e5`; `git diff 1d6a6e5..HEAD -- index.html` ist LEER, obwohl HEAD
waehrend der Messung auf `ab039e0` weitergelaufen ist) und der Commit-Verlauf
`a9c04d9..1d6a6e5`. NICHT die Befundzettel.

**Messstand:** `index.html` = 30430 Zeilen, `git rev-parse --short HEAD` =
`ab039e0`, `index.html` auf dem Stand von `1d6a6e5`.

**Werkzeuge:** alle Zaehler laufen ueber `scripts/code_scan.py::ist_code`.
Das ist hier nicht Zierrat: die Kur-Kommentare ZITIEREN die alten Formen
woertlich (`HIER STAND \`limit=5000\``, `HIER STAND \`if(_d>0)\``,
`x||192.5`, `1 -> 2 Nachkommastellen`). Wer rohen Dateitext durchsucht,
findet seine eigene Begruendung und haelt sie fuer Code.

---

## 0. Der KOEDER — findet diese Messung eine Nebenwirkung ueberhaupt?

Eine Null ohne Koeder ist von „ich habe nichts gesucht“ nicht zu
unterscheiden. Das Verfahren ist in allen Faellen dasselbe: **nicht die
geaenderte Stelle zaehlen, sondern die AUFRUFER, und je Aufrufer sagen, was
jetzt anders passiert.** Drei Koeder belegen, dass es traegt:

| Koeder | Befehl | Erwartung | Gemessen |
|---|---|---|---|
| **K1 — der BEKANNTE Fall (B2/v3.9.995)** | `python scripts/nw_b2_b3_leseaufrufe.py --stand v995` | die Aufrufer-Erhebung muss die zehn `limit=1`-Aufrufe nennen, auf die der Melder damals falsch feuerte | **15 Aufrufer mit eigener Grenze, davon 10x `limit=1`** — genau die Grundgesamtheit des bekannten Fehlers |
| **K2 — kuenstlich zurueckgedreht (P2)** | `python scripts/nw_p2_nachkommastellen.py --koeder` | eine der vier kurierten Stellen auf 1 Stelle zurueck ⇒ genau EIN Fund mehr | `N=1: 1 → 2`, `N=2: 4 → 3`. Genau eins |
| **K3 — eine falsch gelistete Tabelle (D2)** | `python scripts/nw_d2_waechtertafel.py --koeder` | `notifications` kuenstlich in die Waechtertafel ⇒ muss als verdaechtig gemeldet werden | `notifications ... 🔴 GEHOERT NACH DER EIGENEN BEGRUENDUNG NICHT IN DIE TAFEL` |
| **K4 — eine Kurstelle zurueckgedreht (P4)** | `python scripts/nw_p4_ktgstd.py --koeder` | `_resturlaubK` auf die alte falsy-Form ⇒ ein `_ktgStd` weniger, ein `\|\|192.5` mehr | `_ktgStd: 15 → 14`, `REST \|\|192.5: 0 → 1 (Z22507)`. Genau eins |

Die Koeder sind VERSCHIEDENER Form (ein bekannter Echtfall, zwei
zurueckgedrehte Kuren, ein falsch aufgenommener Tafel-Eintrag) — ein
einzelner Koeder, der die Luecke des Zaehlers teilt, wuerde die Blindheit nur
bestaetigen.

**Ein Zaehler von mir war dabei selbst falsch, und das gehoert hierher:**
`route_map()` prueste die Codemaske am OEFFNENDEN Anfuehrungszeichen — das
gilt als Zeichenkette, nicht als Code. Ergebnis: „ROUTE_MAP: 0 Wege“ und eine
Tafel, auf der ALLE 23 Eintraege als moeglicherweise wirkungslos dastanden.
Das sah aus wie ein grosser Befund und war ein Messfehler. Geprueft wird
jetzt die schliessende eckige Klammer; die ist Code. Vorher `0 Wege`,
nachher `40 Wege`.

---

## 1. Ergebnis je Kur — alle zwoelf Kuerzel, auch die unauffaelligen

> Der Auftrag spricht von ELF Kuren, nennt aber ZWOELF Kuerzel
> (Z1, Z3, Z6, P2, P3, P4, D1, D3, B3, D2, B1, B2). Die Elf sind die elf
> BEFUNDE der Jagd; B2 ist in v3.9.995 kuriert und in v3.9.996 nachgebessert
> worden. Hier stehen alle zwoelf.

| Kur | Aufrufer gezaehlt | Ergebnis |
|---|---|---|
| **Z1** Kalenderjahr → ISO-Jahr | 12 Lesestellen von `yr` (ProjectShell) + 7 (VZeit/VBer) | geprueft, **sauber**. Jede Lesestelle steht in einem ISO-Wochen-Zusammenhang (`kwD(yr,kw)`, `getISO(yr,kw)`, `_getMaxKW(yr)`, „KW x / yr“). Keine Jahres-Filterung, kein Monatsgitter im Ausschnitt |
| **Z3** `kwOf` an beiden Enden | 5 Verbraucher (`days.map` x3, `days.forEach`, `days[w*7]`) | geprueft, **sauber**. Die Tage werden nur ueber `dk(d)` (Y-M-D) und `kwOf` gelesen; `kwOf` nullt die Uhrzeit inzwischen SELBST, ist also von `startMon` unabhaengig |
| **Z6** negative Differenzen | 2 Kurstellen (Z16249, Z25600), 2 Geschwister (Z16304, Z26062) | geprueft, **1 Nebenbefund (N7)**. 🔴 Die Auftragspraemisse ist widerlegt — s. Abschnitt 3 |
| **P2** Rundung 1 → 2 Stellen | 5 Zahlen auf dem Blatt, 2 auf dem Zwilling | 🔴 **NEBENWIRKUNG N1** — eine Zahl DESSELBEN Blattes blieb auf einer Stelle |
| **P3** Plausibilitaetswaechter | **1** Aufrufer (`saveAs`, Z11297) | geprueft, **sauber**. Kein Schleifen-/Effekt-Trigger, also kein Toast-Sturm. `_asUebernahmeBedarf` erzwingt `fz>0||st>0`, damit ist `_h>0` immer wahr; neu blockiert wird nur `_h>24` |
| **P4** `_ktgStd` statt 14x `\|\|192.5` | 14 Aufrufe + 1 Definition, 0 Reste | geprueft, **sauber** — mit einer Einschraenkung (N8, Altbestand) |
| **D1** Fehlschlag beim Patch meldet | 1 Aufrufer (fire-and-forget), Rueckgabewert unbenutzt | geprueft, **sauber**. Der Patch ist die LETZTE Anweisung des aeusseren `try`; nach dem inneren `catch` folgt kein Code mehr |
| **D3** `_fotoAufbereiten` | 4 Aufrufstellen, alle vier in einer `forEach`-Schleife ueber eine MEHRFACH-Auswahl | 🔴 **NEBENWIRKUNG N5** (Doppeltoast / Toast-Sturm). Die unbehandelte Ablehnung ist dagegen ALT, nicht neu |
| **B3** `limit=5000` nur ohne eigene Grenze | **15** Aufrufer mit eigener Grenze (der Commit sagt „genau einer“) | 🔴 **NEBENWIRKUNG N2 und N3** |
| **D2** Waechtertafel 10 → 23 | 23 Eintraege, alle mit Weg in ROUTE_MAP; 22 mit PUT-Stelle | geprueft, **kein Fehl-Hinweis unter den 13 neuen** — aber 4 neue Tabellen erben eine bestehende Fehlalarm-Strecke (N6); dazu ein Altbefund (N9) |
| **B1** Krankmeldungen ueber die Kennung | **2** Aufrufer von `MAAttesteSection` | 🔴 **NEBENWIRKUNG N4** — der eine der beiden uebergibt eine LEERE Kennung |
| **B2** Melder fuer gekappte Listen | 151 Leseaufrufe, 136 ohne eigene Grenze, 15 mit | geprueft; die Nachbesserung aus v3.9.996 wirkt. 🔴 **NEBENWIRKUNG N3** (`_sbGetUsersSafe` ist ausgenommen worden, obwohl es nicht ausgenommen gehoert) |

---

## 2. Die Funde, nach Schwere

### N1 — P2: „eventuelle Minderstunden“ blieb auf EINER Nachkommastelle 🔴🔴

**Kur:** P2 (v3.9.992), Rundung 1 → 2 Nachkommastellen, vier Stellen.

**Betroffener Aufrufer:** `exportWochenStz`, das GEDRUCKTE Blatt selbst
(`index.html` Zeile 25676–25747), Zeile **25741**.

**Befehl:**
```
python scripts/nw_p2_nachkommastellen.py
```
```
=== Wochen-Stundenbestaetigung (exportWochenStz, das Blatt aus P2) (Zeile 25676 bis 25747) ===
  Nachkommastellen=1 : 1 Stellen
  Nachkommastellen=2 : 4 Stellen
    N=1  Z25741   _n(Math.abs(diff),1)      <-- Minderstunden
    N=2  Z25689   _n(dt,2)                  <-- Tageszelle (Tagessumme)
    N=2  Z25689   _n(dt,2)                  <-- Tageszelle (Arbeitszeit)
    N=2  Z25734   _n(weekTotal,2)           <-- Wochenstunden
    N=2  Z25740   _n(diff,2)                <-- Mehrstunden
```

**Was jetzt anders passiert:** Z25740 und Z25741 drucken DIESELBE Groesse
`diff`, nur nach Vorzeichen getrennt. Seit P2 steht die positive Haelfte auf
zwei Stellen und die negative auf einer. Auf einem unterschriebenen Blatt
steht damit:

* Wochenstunden `36.42` (zwei Stellen, neu),
* Minderstunden `2.1` statt `2.08` (eine Stelle, unveraendert),
* und `38.5 − 36.42 = 2.08 ≠ 2.1`.

Das ist genau der Fehler, gegen den P2 gebaut wurde („ein unterschriebenes
Blatt, das nicht aufgeht“) — auf demselben Blatt, in der Zeile direkt unter
der kurierten. Die vier gemessenen Stellen stimmen mit dem Commit ueberein;
die fuenfte Zahl war nie Teil der Zaehlung.

**Gewollt?** NEIN. Der Commit begruendet Z25740 ausdruecklich mit „auf zwei
Stellen wie der Rest des Blattes“ — Z25741 IST der Rest des Blattes.

**Wo ein Riegel fehlt:** `tests/test_blatt_geht_auf_v992.py` misst laut
Commit „ausdruecklich die VIER STELLEN und nicht die Klassenregel“. Ein
Riegel, der VIER Stellen festnagelt, kann eine FUENFTE nicht sehen. Der
Riegel, der hier fehlt, lautet: *auf diesem Blatt hat jede Stundenzahl
dieselbe Stellenzahl* — das misst Wirkung statt Anwesenheit.

---

### N2 — B3: der Commit sagt „genau ein Aufruf betroffen“, es sind 15 🔴

**Kur:** B3 (v3.9.993). `_sbGet`/`_sbGetOrder` haengen `limit=5000` nur noch
an, wenn der Aufrufer keine eigene Grenze gesetzt hat.

**Befehl:**
```
python scripts/nw_b2_b3_leseaufrufe.py
```
```
Leseaufrufe gesamt: 151   (_sbGet 134, _sbGetOrder 12, _sbGetUsersSafe 5)
MIT eigener Grenze: 15
   limit='+       1x      limit=1        10x
   limit=10000    1x      limit=200       2x     limit=4  1x
OHNE eigene Grenze: 136
```

Der B3-Commit sagt: *„Genau ein Aufruf ist betroffen ... Fuer die uebrigen 112
Aufrufe aendert sich nichts.“* Die v3.9.996-Messung sagt: *„12 mit eigener
Grenze (10x limit=1, 2x limit=200)“*. Gemessen sind **15** — `limit=4` und
`limit='+_mb` fehlen in beiden Zaehlungen. Fuer jeden dieser 15 galt vorher
die Helfer-Grenze 5000 (der Helfer-Parameter stand zuletzt in der Adresse),
jetzt gilt die eigene.

Zwei davon sind eine echte Verhaltensaenderung:

**N2a — `_juprowaDrainPending` (Zeile 4334): die „bounded batch“ war nie
gebunden.**
```
async function _juprowaDrainPending(maxBatch){
  const _mb=(typeof maxBatch==='number'&&maxBatch>0)?maxBatch:10;
  ...
  pending=await _sbGet('arbeitsscheine','push_pending=eq.true&...&limit='+_mb);
  for(const row of pending){ await _juprowaPush(row.id); ... }
```
Der Kommentar darueber sagt, wozu die Funktion existiert: *„Drain pending
push-queue in bounded batches. Ersetzt _juprowaPushAll als Auto-Sync-Safety-
Net (pushAll hing bei grosser Queue, 4-Min-Timeout). Limit 10 bleibt
innerhalb Sync-Runtime.“* Genau dieses Limit 10 wurde bis v3.9.993 von der
Helfer-Grenze 5000 ueberschrieben — die Kur gegen den 4-Minuten-Timeout war
seit ihrem Bau **wirkungslos**, und B3 hat sie nebenbei scharf gestellt.

*Gewollt?* Die WIRKUNG ja — sie stellt die ausdrueckliche Absicht von
v3.8.42 her. Genannt oder gemessen wurde sie nirgends, und die Richtung ist
sichtbar: der Drain nimmt jetzt 10 je Lauf statt alles auf einmal.

**N2b — die uebrigen 13 sind harmlos, einzeln nachgesehen:**
`limit=1` x10 lesen `rows[0]` oder pruefen nur `Array.isArray` (Proben,
Erreichbarkeitspruefungen) · `limit=4` (Z16048) macht direkt danach
`r.slice(0,4)` · `limit=10000` ist der Lieferantenkatalog, also der im
Commit genannte Fall · `limit=200` — siehe N3.

---

### N3 — B3: eine bestehende RLS-Probe misst jetzt an einer kleineren Stichprobe 🔴

**Betroffener Aufrufer:** die eingebaute Selbstprobe `T-110 „Monteur sieht
nur eigene AS“`, `index.html` Zeile **1324**.

```js
const r=await _sbGet('arbeitsscheine','select=id,monteur&limit=200');
const all=Array.isArray(r)?r:[];
const own=all.filter(a=>a.monteur===mid).length;
const foreign=all.length-own;
return{pass:foreign===0, ...};
```

**Was jetzt anders passiert:** vor B3 lieferte dieser Aufruf bis zu 5000
Zeilen (die Helfer-Grenze gewann), seit B3 genau 200. Der Riegel prueft
weiterhin `foreign===0` — aber an einem Fuenfundzwanzigstel der Grundgesamt-
heit. Leckt der Zeilenschutz erst jenseits von Zeile 200, meldet die Probe
jetzt GRUEN. **Eine STICHPROBE nach Merkmal A sagt nichts ueber B**: die
Probe misst einwandfrei, nur eine andere Menge.

Die Schwester `T-111 „Admin sieht viele AS“` (Zeile 1336) prueft `n>=20` und
bleibt bei 200 unberuehrt.

**Gewollt?** NEIN, und es ist nirgends genannt. B3 war eine Kur am
Lieferantenkatalog; dass sie das Messfenster eines RLS-Riegels verengt, steht
in keinem Commit.

---

### N4 — B1: in „Mein Profil“ verschwinden die Atteste bei leerer Kennung 🔴🔴

**Kur:** B1 (v3.9.995). Aus dem ODER wurde ein VORRANG:
```js
const mine=(rows||[]).filter(r=>
  r&&r.worker_id ? String(r.worker_id)===String(workerId)
                 : (!!workerName && r&&r.worker_name===workerName));
```

**Betroffene Aufrufer — beide gezaehlt:**
```
python scripts/nw_z1_z6_b1.py
```
```
Z10359  React.createElement(MAAttesteSection,{workerId:(curUser&&curUser.monteurId)||"",
                                              workerName:(curUser&&curUser.name)||"", ...})
Z10464  React.createElement(MAAttesteSection,{workerId:selM.id, workerName:selM.n, ...})
Z29217  function MAAttesteSection({workerId,workerName,curUser,isMob})   <-- Definition
```

**Was jetzt anders passiert:** Aufrufer **Z10359** („Mein Profil“) uebergibt
`workerId` mit einem ausdruecklichen Rueckfall auf **`""`**. Ist
`curUser.monteurId` leer — ein Benutzer ohne verknuepften Monteursatz —,
dann gilt fuer jede Zeile, die eine Kennung TRAEGT:
`String(r.worker_id) === String("")` → falsch. Die Zeile faellt heraus, und
der Namenszweig wird gar nicht erst erreicht, weil er nur fuer Zeilen OHNE
Kennung gilt.

* **vorher:** `(workerId && ...) || (workerName && r.worker_name===workerName)`
  — bei leerer Kennung trug der Name, die Atteste waren da.
* **nachher:** die Liste ist LEER.

Der Waechter am Kopf der Komponente
(`if(!workerId&&!workerName){setItems([]);return;}`) faengt das nicht ab: ein
Name ist ja vorhanden.

Das ist dieselbe Wirkung, gegen die B1 gebaut wurde („die Unterlagen waren in
der Datenbank noch da und in der Uebersicht weg“) — nur mit einer anderen
Ursache. Es geht um Gesundheitsdaten.

**Gewollt?** NEIN. Die Absicht war „hat die Zeile eine Kennung, MUSS sie
passen“ — gemeint war: passen zu einer ECHTEN Kennung. Ein leerer
Vergleichswert ist keine Kennung, sondern eine fehlende.

**Wo ein Riegel fehlt:** der Riegel `tests/test_zuordnung_und_grenze_v995.py`
hat sechs Proben zur Zuordnung. Keine faehrt den Fall `workerId===""`. Der
fehlende Fall heisst: *leere Kennung + vorhandener Name + Zeilen MIT Kennung
⇒ die Liste darf nicht leer sein.*

Der zweite Aufrufer (Z10464, Mitarbeiter-Detail) uebergibt `selM.id` und ist
nicht betroffen.

---

### N5 — D3: zwei Fehlertoasts je Foto, und einer je Datei der Mehrfachauswahl

**Kur:** D3 (v3.9.993). `_fotoAufbereiten` meldet dem Nutzer und reicht den
Fehler weiter.

**Befehl:**
```
python scripts/nw_d3_fotoaufbereiten.py
python scripts/nw_d3_vorzustand.py
```
```
Aufrufstellen von _fotoAufbereiten: 4
  Z7092    OFFEN   (KundenPortal, Mangel-Fotos)
  Z17135   OFFEN   (VMang, Mangel-Fotos)
  Z18484   CATCH   .catch(e=>{...window.__toast("❌ Plan-Upload fehlgeschlagen: "+file.name,"error")})
  Z22666   CATCH   .catch(e=>{...window.__toast("❌ AU-Upload fehlgeschlagen: "+f.name,"error")})
OHNE .catch und ohne await: 2
Globaler Auffang: window.onunhandledrejection Zeile 3237
```

**Die Frage des Auftrags — entsteht ein unbehandelter Fehler? — ist mit JA zu
beantworten, aber das ist KEINE Nebenwirkung der Kur.** Gegenprobe am Stand
VOR der Kur (`530f6c8`):
```
VOR DER KUR - alle compressPhoto-Aufrufe: 10, davon OHNE .catch: 6
    Z7018    OFFEN    compressPhoto(file,2400,0.88).then(ph=>createThumbnail(...   -> heute Z7092
    Z17061   OFFEN    compressPhoto(file,2400,0.88).then(ph=>createThumbnail(...   -> heute Z17135
    Z18410   CATCH    ...                                                          -> heute Z18484
    Z22592   CATCH    ...                                                          -> heute Z22666
```
`compressPhoto` hat an genau diesen beiden Stellen schon vorher abgelehnt.
Der Weg ueber `window.onunhandledrejection` (Zeile 3237: `console.error`,
Ringpuffer `window.__EP_ERRORS` und eine Zeile
`action:'promise_rejection'` in `activity_log` ueber `_epkLogErrorThrottled`)
war also vorher dieselbe. **Unveraendert, kein Befund an der Kur.**

**Was WIRKLICH neu ist:**

1. **Doppeltoast.** An Z18484 und Z22666 gab es bereits einen eigenen
   Fehlertoast. Seit D3 kommt der Toast aus `_fotoAufbereiten` dazu: der
   Nutzer bekommt fuer EINEN Fehlschlag ZWEI rote Meldungen
   („… konnte nicht verarbeitet werden … bitte noch einmal aufnehmen“ und
   „❌ Plan-Upload fehlgeschlagen: …“).
2. **Toast-Sturm bei Mehrfachauswahl.** Alle vier Stellen laufen in einer
   Schleife ueber die Dateiauswahl (`forEach(file=>…)` bzw. `forEach(f=>…)`,
   zwei davon mit `multiple: true`). Zwanzig HEIC-Bilder vom iPhone ergeben
   heute 20 bzw. 40 Fehlertoasts; vorher waren es null.

**Gewollt?** Die Meldung ja, ausdruecklich. Die VERVIELFACHUNG nicht — sie
ist in keinem Commit genannt. Schwere: niedrig (Laerm, kein Datenverlust);
die Kur bleibt in der Sache richtig, denn vorher passierte gar nichts.

---

### N6 — D2: vier neue Tabellen erben eine bestehende Fehlalarm-Strecke

**Befehl:**
```
python scripts/nw_d2_waechtertafel.py
```
```
Tafel _RLS_SILENT_DENIAL_LABELS: 23 Eintraege (Zeile 2659..2685)
ROUTE_MAP: 40 Wege
Tafel-Eintraege OHNE Weg in ROUTE_MAP (koennen NIE feuern): keiner
SQ.push-Stellen im CODE: 186   (PUT=95, POST=49, DELETE=41, ohne Verb=1)
Loeschkaskade beim Loeschen eines Projekts loescht:
  plans, tickets, checklists, defects, project_documents, project_folders,
  photos, material_orders, bautagebuch
```

**Die Frage des Auftrags — ist unter den 13 eine, die nach der eigenen
Begruendung haette draussen bleiben muessen? — Antwort: nach allem, was ohne
Datenbank messbar ist, NEIN.**

* Kein toter Eintrag wie `fz_schaeden`: alle 23 haben einen Weg in
  `ROUTE_MAP`, 22 von 23 haben mindestens eine PUT/PATCH-Stelle.
* Kein Upsert-Muster: die fuenf Kandidaten, bei denen „0 Zeilen = nie
  angelegt“ normal sein koennte, haben alle einen ausdruecklichen POST-Weg
  VOR dem PUT — `supplier_configs` sogar mit
  `if(isNew){…POST…} else{…PUT…}` (Zeile 14083/14084), `checklists`,
  `project_folders`, `gefahrstoff_folders` und `bauprovisorien_mieten`
  ebenso.
* Der Waechter wirft NICHT neu; ein Fehlalarm kostet einen falschen
  Fehlertoast, keinen Datensatz.

**Was trotzdem dazugekommen ist:** vier der dreizehn —
`checklists`, `project_documents`, `material_orders`, `project_folders` —
stehen in der **Loeschkaskade von `projects`**. Wird ein Projekt geloescht
und danach ein noch in der Warteschlange liegender PUT auf ein Kind
abgearbeitet, trifft er 0 Zeilen und der Nutzer liest „keine
Schreibberechtigung“, obwohl das Recht nie das Problem war.

**Gewollt?** Die Strecke ist nicht neu — `plans` und `bautagebuch` standen
mit derselben Eigenschaft schon vorher in der Tafel. D2 hat die Angriffs-
flaeche von zwei auf sechs Tabellen verdreifacht, ohne das zu nennen.
Schwere: niedrig.

---

### N7 — Z6: die beiden Geschwister tragen die kurierte Form noch

**Kur:** Z6 (v3.9.991). `if(_d>0)` ist an den zwei Speicherstellen (Z16249,
Z25600) entfallen.

**Betroffene Aufrufer:** die Pausen-Auswahl derselben Masken, **Z16304** und
**Z26062**:
```js
setAddPause(pp);
if(addVon&&addBis){const d=_wrapHrs(addVon,addBis)-pp; if(d>0) setAddHours(Math.round(d*2)/2);}
```
Das ist woertlich die Form, die Z6 als Fehler benannt hat.

**Was jetzt anders passiert:** waehlt jemand eine Pause, die so lang ist wie
die Anwesenheit, bleibt im Formularfeld die ALTE Stundenzahl stehen (z. B.
8) — waehrend das Speichern seit Z6 mit „Die Pause ist so lang wie die
Anwesenheit oder laenger“ abbricht. Anzeige und Speichern widersprechen
einander. Kein Datenverlust, aber die Maske sagt etwas anderes als der
Knopf. Schwere: niedrig.

---

### N8 — P4: das Feld laesst sich weiterhin nicht leeren (Altbestand, nicht neu)

**Befehl:**
```
python scripts/nw_p4_ktgstd.py
```
```
_ktgStd-Stellen im CODE (inkl. Definition): 15     -> 14 Aufrufe, wie im Commit
REST der alten Form `||192.5` im CODE: 0
Geschwisterfeld `woche`: `||38.5` im CODE: 7  (NICHT kuriert - dieselbe falsy-Falle)
`vorjahr||0`: 11   `ueberstunden||0`: 5   (harmlos: der Rueckfall IST 0)
```

Die Frage des Auftrags — verhaelt sich der Helfer bei `0`, `""`, `null`,
`undefined` und einer nicht-numerischen Zeichenkette wie gewollt? — ist mit
JA zu beantworten, und die 14 Stellen stimmen. Drei Punkte gehoeren
trotzdem in den Befund:

1. **Eine `0`, die absichtlich auf 192,5 fallen sollte, gibt es nicht.** Die
   Objekt-Vorgaben `{stunden:192.5,…}` fuer einen FEHLENDEN Satz sind
   unangetastet geblieben, und der Waechter gegen das Ueberschreiben echter
   Werte (`kontUnlesbar`, v3.9.914) haengt an `_rlsLeer(data)`, nicht am Wert
   192,5 — es gibt also kein Merkmal, das durch die echte 0 kaputtginge.
2. **Der Commit behauptet zuviel.** Er sagt „Das Feld liess sich ausserdem
   nicht leeren.“ — geheilt ist das nicht: das Eingabefeld (Zeile 22939)
   ruft `stunden:_ktgStd(e.target.value)`, und `_ktgStd("")` gibt 192,5
   zurueck. Wer das Feld leert, sieht weiterhin 192,5. Das ist **kein
   Rueckschritt** (vorher stand dort `parseFloat(e.target.value)||192.5`,
   gleiches Ergebnis), aber die Kur loest diesen Teil ihrer eigenen
   Ankuendigung nicht ein.
3. **Nebenbei repariert und nirgends genannt:** `_ktgStd` gibt immer eine
   ZAHL zurueck. Die alte Form gab eine nicht-leere ZEICHENKETTE weiter —
   `"150"||192.5` ergibt `"150"`, und `"150"+(ks.vorjahr||0)` ergibt die
   Zeichenkette `"1500"`. Diese Falle ist mit P4 verschwunden.
4. **Das Geschwisterfeld blieb.** `woche` steht an 7 Stellen weiterhin als
   `||38.5` — dieselbe falsy-Falle, mit 0 als moeglicher Angabe. Nicht Teil
   der Kur, aber derselbe Fehler eine Spalte weiter.

---

### N9 — D2/Altbestand: `forms` ist ein Tafel-Eintrag ohne PUT-Weg

`nw_d2_waechtertafel.py` meldet fuer `forms`: **PUT=0, POST=0, DELETE=2**.
Das ist genau das Merkmal, an dem `fz_schaeden` als toter Eintrag erkannt
wurde: ein Name in der Tafel, den kein Schreibweg je erreicht. `forms` stand
vor v3.9.994 in der Tafel und ist von den elf Kuren nicht beruehrt — der
Befund gehoert trotzdem hierher, weil die D2-Zaehlung „23 wirksame
Tabellen“ ihn mitzaehlt. **Nicht abschliessend geprueft** (s. Abschnitt 4).

---

## 3. Wo eine Praemisse des Auftrags durch die Messung widerlegt ist

**„Z6: die Uebernahme rechnet jetzt auch negative Differenzen. Vertraegt der
weitere Weg (Speichern, Summieren, Anzeige) negative Stunden?“ —
WIDERLEGT.** Negative Stunden erreichen den weiteren Weg nicht. Die kurierte
Zeile lautet vollstaendig (Zeile 16249, wortgleich 25600):

```js
if(_rVon&&_rBis){const _d=_wrapHrs(_rVon,_rBis)-addPause;
  _h2=Math.round(_d*100)/100;/* … */
  if(_d<=0){if(window.__toast)window.__toast("⚠️ Die Pause ist so lang wie die
    Anwesenheit oder laenger (…). Bitte Zeiten oder Pause korrigieren.","error",6000);
    return;}}
```

`_d<=0` bricht mit `return` ab, BEVOR irgendetwas gespeichert wird. Die Kur
rechnet negative Differenzen zwar aus, reicht sie aber nicht weiter. Die
Frage nach dem weiteren Weg stellt sich nicht.

*(Ein Randfall dazu, gemessen: ist `addPause` keine Zahl, wird `_d` zu NaN.
`NaN<=0` ist FALSCH, der neue Abbruch greift also nicht — aber die bestehende
Pruefung `!(h>0&&h<=24)||isNaN(h)` eine Zeile weiter faengt ihn. Der Nutzer
bekommt die unschaerfere alte Meldung statt der neuen. Kein Verlust.)*

**„B3 ist genau ein Aufruf betroffen.“ — WIDERLEGT, es sind 15 (N2).**

**„Ich erwarte 1 bis 3 weitere Nebenwirkungen, am ehesten bei P2, D2 oder
D3.“ — der Anker hat NICHT gehalten**, in beide Richtungen:
* Die ZAHL ist zu klein: gefunden sind **5 echte Nebenwirkungen** (N1–N5)
  plus vier Nebenbefunde (N6–N9).
* Die STELLEN stimmen nur zum Teil: P2 ja (N1, und es ist der schwerste
  Fund), D3 ja (N5, aber schwaecher als vermutet — die unbehandelte
  Ablehnung ist Altbestand), D2 **nein** (kein Fehl-Hinweis unter den 13).
  Die beiden schwersten Funde neben P2 liegen bei **B3** und **B1** — zwei
  Kuren, die im Anker gar nicht vorkamen.

---

## 4. Was NICHT gemessen werden konnte, und warum

1. **Ob PostgREST bei zwei `limit`-Parametern den ERSTEN oder den LETZTEN
   nimmt.** Der B3-Commit setzt voraus: *„die Adresse trug danach ZWEI
   limit-Parameter, der des Helfers stand ZULETZT“* — und daraus folgt, dass
   der Helfer gewann. **Diese Praemisse ist in keinem Commit gemessen.** Sie
   entscheidet alles: gewinnt der LETZTE, dann haben sich fuer 15 Aufrufer
   die Ergebnismengen geaendert (N2, N3); gewinnt der ERSTE, hat B3 nichts
   geaendert und der Befund, gegen den B3 gebaut wurde (der auf 5000 gekappte
   Lieferantenkatalog), hat nie existiert. Nicht messbar in diesem Auftrag:
   es braucht EINEN Aufruf gegen die REST-Schnittstelle, und
   Datenbankzugriffe sind Nicht-Ziel. **Das ist der wichtigste offene Punkt
   dieses Befunds.**
2. **Ob eine der 23 Tabellen einen Zeilenschutz hat, bei dem eine
   ERFOLGREICHE Aenderung die Zeile fuer den eigenen SELECT unsichtbar
   macht.** Dann liefert PostgREST mit `return=representation` HTTP 200 und
   ein leeres Array, und der D2-Waechter meldet faelschlich „keine
   Schreibberechtigung“. Kandidaten waeren `projects` (Archivieren) und
   `finkzeit` (Freigabe). Das steht in den RLS-Regeln der Datenbank, nicht im
   Quelltext.
3. **Ob `forms` (N9) wirklich keinen Schreibweg hat.** Gemessen sind nur die
   `SQ.push`-Stellen mit erkennbarer `url:`-Zeichenkette (186 von 186, eine
   davon ohne erkennbares Verb). Ein Weg, der die Adresse zur Laufzeit
   zusammensetzt, faellt aus dieser Zaehlung heraus.
4. **Der UMFANG der Z1-Messung.** Die Lesestellen von `yr` sind in einem
   AUSSCHNITT von 400 Zeilen ab dem Funktionskopf gezaehlt, nicht im ganzen
   Rumpf. Grund: `code_scan._klammer_zu` kennt keine Regex-Literale und
   lieferte fuer `exportWochenStz` einen Rumpf von 25676 bis 30431 — also bis
   zum Dateiende. Der Ausschnitt ueberdeckt beide Komponenten vollstaendig
   (ProjectShell endet vor VDash bei 16032, VZeit vor 16599), aber er ist ein
   Ausschnitt, und **der Ausschnitt eines Riegels ist selbst die Luecke**.
5. **Kein einziger Fund ist im laufenden Programm nachgestellt worden.** Alle
   Aussagen sind Quelltext-Aussagen. Bei N1 (die gedruckte Zahl), N4 (die
   leere Attestliste) und N3 (die verengte Stichprobe) waere eine Messung am
   laufenden Programm der bessere Beleg.

---

## 5. Latent, aber genannt: `_sbGetUsersSafe` ist von B3 ausgenommen geblieben

Teil von N3, gehoert aber eigenstaendig festgehalten:

```js
async function _sbGetUsersSafe(filter){
  const url=SB_REST+"/users?select="+_USER_SAFE_COLS+(filter?"&"+filter:"")+"&limit=5000";
  ...
  return _sbGrenzeMelden("users",filter,await r.json());
}
```

B3 hat `_sbGet` und `_sbGetOrder` bedingt gemacht, `_sbGetUsersSafe`
**nicht** — dort haengt `&limit=5000` weiterhin bedingungslos an. Der Melder
aus v3.9.996 laeuft aber auch hier und steigt bei eigener Grenze frueh aus.
Die Begruendung der Nachbesserung („wer selbst eine Grenze schreibt, kappt
mit Absicht und weiss es“) trifft hier **nicht zu**: die Helfer-Grenze wird
zusaetzlich angehaengt und kappt still weiter — nur meldet es jetzt niemand
mehr.

Heute ist das unerreichbar: keiner der 5 `_sbGetUsersSafe`-Aufrufe setzt eine
eigene Grenze (gemessen mit `nw_b2_b3_leseaufrufe.py`). Der erste, der es
tut, faellt in genau diese Luecke. **Hier fehlt ein Riegel:** *jeder Leser,
der `_sbGrenzeMelden` aufruft, muss die Grenze auch bedingt anhaengen.*

---

## 6. Die Messskripte

| Skript | misst |
|---|---|
| `scripts/nebenwirkung_helfer.py` | gemeinsame Hilfen; liest mit `newline=''`, stellt `stdout` auf UTF-8, alle Suchen ueber `code_scan.ist_code` |
| `scripts/nw_b2_b3_leseaufrufe.py` | B2/B3 — alle 151 Leseaufrufe, getrennt nach eigener Grenze; `--stand v995` faehrt denselben Zaehler gegen den bekannten Fehler (Koeder K1) |
| `scripts/nw_p2_nachkommastellen.py` | P2 — jede `_n(x,N)`-Stelle des gedruckten Blattes und seines Zwillings; `--koeder` dreht eine kurierte Stelle zurueck (K2) |
| `scripts/nw_p4_ktgstd.py` | P4 — die 14 `_ktgStd`-Aufrufe, die Reste der alten Form, das Geschwisterfeld `woche`; `--koeder` (K-P4) |
| `scripts/nw_d2_waechtertafel.py` | D2 — Tafel gegen `ROUTE_MAP` und die 186 `SQ.push`-Stellen, Loeschkaskade; `--koeder` nimmt `notifications` auf (K3) |
| `scripts/nw_d3_fotoaufbereiten.py` | D3 — die 4 Aufrufstellen und ihre `.catch`-Lage |
| `scripts/nw_d3_vorzustand.py` | D3-Gegenprobe gegen `530f6c8` — war die unbehandelte Ablehnung schon vorher da? |
| `scripts/nw_z1_z6_b1.py` | Z1 (Lesestellen von `yr`), Z6 (Weg hinter der Kur, Geschwister), B1 (Aufrufer von `MAAttesteSection`) |

Alle Skripte sind **lesend**. Keines schreibt in `index.html`.
