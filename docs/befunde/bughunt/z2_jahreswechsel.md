# Z2 — Die Wochennavigation endet an der Jahresgrenze

**Quelle der Wahrheit:** `C:\repos\epkolar-app\index.html`
**Gemessen am:** 2026-09-30, Stand `md5 = df4252375903930f1593e94d442ed838`, 3 779 780 Bytes, 30 375 Zeilen, **30 375 von 30 375 Zeilenenden sind CRLF** (kein einziges reines LF).
**Diese Datei aendert NICHTS an `index.html`.** Sie ist ein Befund plus Ersatztexte.

---

## 🔴 Vorweg: zwei Warnungen, die die Anwendung betreffen

### 1. `index.html` wurde WAEHREND dieser Messung zweimal fortgeschrieben

| Zeitpunkt | Bytes | Zeilen |
|---|---|---|
| 08:39:20 | 3 778 684 | 30 373 |
| 08:42:20 | 3 779 780 | 30 375 |
| 08:43:33 (Messstand dieses Berichts) | 3 779 780 | 30 375 |

Zwischen meinem ersten und zweiten Lesen sind die Zeilennummern um **+19** gewandert. Alle
Zeilennummern unten sind deshalb nur ein **Findehinweis**, kein Anker. Der Anker ist der TEXT.

**Vor dem Einsetzen:** jede Zeichenkette einmal gegenzaehlen. Wenn eine Zahl nicht mehr stimmt,
ist die Datei weitergezogen — dann neu schneiden, nicht abtippen.

### 2. Die ganze Datei ist CRLF — zwei Anker sind ZWEIZEILIG

Die Stellen **A1** und **B1** brauchen einen zweizeiligen Anker, weil die zu aendernde Zeile
woertlich identisch in zwei Bauteilen steht (und ein drittes Mal als Teilzeichenkette einer
8-fach eingerueckten Zeile). Zwischen den beiden Zeilen eines solchen Ankers steht **CRLF**.
Wird der Anker aus dieser Markdown-Datei mit reinem LF kopiert, **trifft er nullmal**.

Sicherer Weg fuer A1 und B1: den Anker mit `sed -n 'A,Bp' index.html` frisch aus der Datei
schneiden, oder mit einem Python-Ersetzer arbeiten, der `\r\n` woertlich setzt
(`io.open(..., 'rb')` / `'wb'` — **niemals** `io.open(p,'w')`, das stellt auf Windows jede
Zeile der Datei auf CRLF um und faerbt 10 000 Zeilen ein).

Alle anderen Anker (A2–A9, B2–B4, C1–C5) sind **einzeilig** und brauchen diese Vorsicht nicht.

---

## 1. Haelt der Plausibilitaetsanker?

**JA, in allen Punkten — mit einer Zahlenkorrektur.**

| Behauptung | Befund |
|---|---|
| `const curKw=isoW();const yr=isoWY();` in `WeekPlan` | ✅ woertlich vorhanden |
| `yr` ist damit Konstante fuer die Lebensdauer des Bauteils | ✅ `const`, kein `setYr`, nirgends neu gesetzt |
| `const _wpKey=(k)=>yr+'-'+k;` baut den Speicherschluessel daraus | ✅ woertlich |
| `switchKw` klemmt mit `Math.max(1,Math.min(_getMaxKW(yr),newKw))` | ✅ woertlich |
| Bei `kw===maxKW` ist „Naechste Woche ▶" tot | ✅ `Math.min(max, max+1) = max` → `setKw(max)` → kein Zustandswechsel |
| KW 1 des Folgejahres ist nicht anlegbar | ✅ der Schluessel `<Folgejahr>-1` kann von `WeekPlan` nie entstehen |
| Dieselbe Klemm-Form an zwei weiteren Stellen, eine inline im Knopf | ✅ — genauer: **vier** weitere Klemmen an **zwei** weiteren Bauteilen (siehe §3) |
| Es gibt keinen Jahresumschalter | ✅ gemessen: `setYr`/`setCalYr`/`setJahr` kommen in keinem der drei Bauteile vor |

**Zahlenkorrektur zur toten Navigation.** Ich messe **223**, nicht 224 (Skript:
`scripts`-frei, Lauf unter `%TEMP%\claude\messung_jahreswechsel.mjs`, `_getMaxKW`/`isoW`/`isoWY`
woertlich aus `index.html` uebernommen; Grundgesamtheit 5 844 Tage, 01.01.2020–31.12.2035):

* **112** Tage, an denen „Woche vor ▶" tot ist (`kw === _getMaxKW(yr)`)
* **111** Tage, an denen „Woche zurueck ◀" tot ist (`kw === 1`)
* Summe **223**

Die Abweichung von 1 gegen die gemeldete 224 liegt an der Intervallkante (2036-01-01 liegt
ausserhalb meiner Grundgesamtheit, gehoert aber zu ISO-KW 1/2036). Der Befund selbst ist
unveraendert — und der **Rueckweg** ist genauso tot wie der Hinweg, was in der Meldung nicht stand.

**Der 01.01.2027 ist bestaetigt, mit einer Praezisierung.**
`_getMaxKW(2026) = 53`. Am 01.01.2027 (Freitag) liefert `isoWY()` → **2026** und `isoW()` → **53**.
`WeekPlan` steht also auf KW 53/2026 = `maxKW` → **▶ ist tot**.
Die Lagertafel `WochenplanTafel` rechnet ihre KW dagegen aus dem **verschobenen** Datum:

```
const kw=isoWof(today);const yr=isoWYof(today);
const rows=(wpHistory[yr+'-'+kw]||wpHistory[kw]||[])...
```

und `today` ist ab **Freitag 09:00 Wiener Zeit** um 7 Tage vorgerueckt (`kioskDisplayWeekOffset`).
Der 01.01.2027 IST ein Freitag. Ab 09:00 an diesem Tag fragt die Tafel also den Schluessel
`2027-1` ab — **gemessen bestaetigt** — den die Planung an dem Tag nicht schreiben kann.
Die Tafel bleibt leer; es gibt keinen Rueckfall auf `2026-53`.

`maxKW` je Jahr, gemessen: 2020:53 · 2021–2025:52 · **2026:53** · 2027–2031:52 · **2032:53** · 2033–2035:52.

---

## 2. Beruehrt die Kur `VOffa` oder etwas mit `juprowa`?

**NEIN — gemessen, nicht vermutet.**

`VOffa`/`juprowa` kommen in `index.html` in **161 Zeilen** vor. In den drei Bereichen, die
diese Kur anfasst, sind es **null**:

| Bereich | Zeilen | VOffa/juprowa-Treffer |
|---|---|---|
| `WeekPlan` | 21347–22450 | **0** |
| `ZeiterfassungView` | 25329–26263 | **0** |
| Projekt-Zeiterfassung (KW-Leiste) | 16155–16285 | **0** |

Der naechstgelegene Treffer liegt bei Zeile 21297 — **vor** dem Beginn von `WeekPlan`.
Kein Ersatztext unten nennt `VOffa` oder `juprowa`, und keiner aendert eine Funktion, die
sie liest. **Die Kur haelt vom eingefrorenen Bereich Abstand.**

---

## 3. Die vollstaendige Liste der Stellen

Drei Bauteile, **19 Stellen** = **23 Ersetzungen** (A10 und C5 fassen je drei Zeilen zusammen).
Nur **A** verliert Daten — die anderen beiden verlieren nur die Navigation.

| # | Bauteil | Zeile¹ | Was es ist | Wirkung heute |
|---|---|---|---|---|
| **A1** | `WeekPlan` | 21347–21348 | `yr` als Konstante deklariert | **Wurzel.** Speicherschluessel, Anzeige, Server-Spalte `year` sind fuer immer auf das Montage-Jahr festgenagelt |
| **A2** | `WeekPlan` | 21502 | `switchKw`-Signatur | nimmt kein Zieljahr entgegen |
| **A3** | `WeekPlan` | 21503 | die zentrale Klemme | `Math.min(maxKW(yr), …)` steht an der Grenze statt darueber zu rollen |
| **A4** | `WeekPlan` | 21508 | `setKw(newKw)` | setzt die KW, nie das Jahr |
| **A5** | `WeekPlan` | 21510 | `_wpGet(newKw)` beim Wechsel | liest aus dem ALTEN Jahr (der Zustand ist hier noch nicht umgesetzt) |
| **A6** | `WeekPlan` | 21392 | Deps des Nachlade-Effekts `[wpHistory,kw]` | reagiert nicht auf einen Jahreswechsel |
| **A7** | `WeekPlan` | 22030 | Knopf „Woche zurueck ◀", **inline geklemmt** | `Math.max(1,kw-1)` → bei KW 1 tot |
| **A8** | `WeekPlan` | 22032 | Knopf „Woche vor ▶", **inline geklemmt** | `Math.min(_getMaxKW(yr),kw+1)` → bei `maxKW` tot |
| **A9** | `WeekPlan` | 22041 | Umschalter „📅 Naechste Woche ▶ / ◀ Diese Woche" | in KW `maxKW` tot; der Rueckweg trifft das falsche Jahr |
| **A10** | `WeekPlan` | 22034–22036 | die drei Abzeichen „Aktuell" / „Vorausplanung" / „Vergangene Woche" | vergleichen **nur die KW-Zahl** — KW 1/2027 gilt als „Vergangene Woche" gegen KW 53/2026 |
| **B1** | `ZeiterfassungView` | 25333–25334 | `yr` als Konstante | Anzeige, XLS-Dateinamen, „Lohnwoche `${yr}`", `kwMon` |
| **B2** | `ZeiterfassungView` | 25940 | `switchKw` (Klemme + Setzer in einer Zeile) | dieselbe Klemme |
| **B3** | `ZeiterfassungView` | 26045 | Abzeichen „Aktuell" | nur KW-Vergleich |
| **B4** | `ZeiterfassungView` | 26053 | Knopf „Zurueck zur laufenden Woche" | nur KW-Vergleich, kein Jahr |
| **C1** | Projekt-Zeiterfassung | 16159 | `calKw`-Zustand ohne Jahr | — |
| **C2** | Projekt-Zeiterfassung | 16174 | `kwMon` rechnet mit `yr=isoWY()` | Datumsspalten immer im HEUTIGEN ISO-Jahr |
| **C3** | Projekt-Zeiterfassung | 16268 | Knopf „Vorherige KW ◀", **inline geklemmt** | `Math.max(1,k-1)` |
| **C4** | Projekt-Zeiterfassung | 16270 | Knopf „Naechste KW ▶", **inline geklemmt** | `Math.min(_getMaxKW(isoWY()),k+1)` |
| **C5** | Projekt-Zeiterfassung | 16271 / 16272 | Abzeichen „Aktuell" / Knopf „Heute" | nur KW-Vergleich |

¹ Findehinweis vom Stand `md5=df42…`. Die Datei wandert — gegenzaehlen, siehe Vorwort.

**Nicht auf der Liste, weil bereits richtig** (gemessen, nicht angenommen):

* `_wpLoadPrevWeek` (`const prevKw=kw>1?kw-1:_getMaxKW(yr-1); const prevYr=kw>1?yr:yr-1;`) — der
  Knopf **„📋 Vorwoche"** greift schon heute korrekt ins Vorjahr. Nur die NAVIGATION kann nicht dorthin.
* `_wpGet` mit seinem Legacy-Rueckfall auf die blosse KW — bleibt unangetastet (siehe A5).
* `API.getWeekplanRows()` laedt `order=year.desc,week.desc,sort_order.asc` **ohne Jahresfilter**.
  `wpHistory` enthaelt also alle Jahre; nach der Kur findet die Navigation dort echte Daten.
  **Kein Ladepfad muss geaendert werden.**
* `setWpHistory(h=>({...h,[_wpKey(kw)]:rows}))` in `switchKw` — legt die ABGEHENDE Woche unter
  dem ABGEHENDEN Jahr ab. Nach der Kur weiterhin richtig, weil `_wpKey` die Closure des
  laufenden Renders benutzt und `setYr` erst danach wirkt. **Nicht anfassen.**
* `_wpYrRef` (nur gesetzt, nirgends gelesen) und die ~12 Anzeige-/Export-/Druck-Leser von `yr`
  (Titel, XLS-Dateiname, `meta.yr`, `savedKws`-Filter, `kwMon`, Wetter-Deps, Server-Feld
  `year:yr`) ziehen **automatisch** mit, sobald A1 sitzt. Genau deshalb ist A1 die Wurzel und
  nicht eine von vielen Stellen.

---

## 4. Wer liest `yr` in `WeekPlan` sonst noch?

Das ist die Frage, die entscheidet, ob A1 harmlos ist. Gemessen: **21 Lesestellen.**

| Lesestelle | Was passiert nach A1 |
|---|---|
| `_wpKey=(k)=>yr+'-'+k` | Schreibschluessel folgt dem angezeigten Jahr ✅ **gewollt** |
| `_wpGet` (ueber `_wpKey`) | Lesen folgt mit ✅ |
| `kwMon=new Date(yr,0,4)` | Montagsdatum + alle sechs Tagesspalten folgen ✅ |
| Wetter-Effekt `},[kw,yr])` | laedt beim Jahreswechsel neu ✅ |
| `switchKw`-Klemme | → A3 |
| `_wpLoadPrevWeek` / `_prevKwDisplay` (`yr-1`) | jetzt relativ zum angezeigten Jahr ✅ **Verbesserung** |
| **Server-Upsert `year:yr, week:kw`** | 🔴 **die wichtigste.** Schreibt die Planung in die Spalte `weekplan_rows.year`. Nach A1 landet KW 1 unter `year=2027` statt `year=2026` — genau das ist die Kur. Vorher war das der Fehlablage-Weg. |
| `_wpYrRef.current=yr` | wird reaktiv, wird aber nirgends gelesen — folgenlos |
| Druck-Vorschau `title:"… KW "+kw+" / "+yr` | ✅ |
| `genXls("📅 Wochenplanung — KW "+kw+" / "+yr, …, "Wochenplanung_KW"+kw+"_"+yr+".xls")` | ✅ |
| `meta={kw,yr,…}` → `_e(meta.yr)` (2 Stellen im Druck-HTML) | ✅ |
| `savedKws` = `Object.keys(wpHistory).filter(k=>k.indexOf(yr+'-')===0)` | 🔴 zeigt nach dem Wechsel die gespeicherten KWs des NEUEN Jahres. Gewollt — die Sprungknoepfe rufen `switchKw(k)` ohne Jahr und bleiben damit im angezeigten Jahr. ✅ konsistent |
| Kopfanzeige `"KW " + kw + " / " + yr` | ✅ |
| `genXls("👷 MA-Uebersicht — KW "+kw+" / "+yr …)` | ✅ |
| ▶-Knopf (A8), Abzeichen (A10) | → eigene Stellen |

**Kein Leser bricht.** Der einzige mit Aussenwirkung ist der Server-Upsert, und dort ist die
Aenderung der Zweck der Uebung.

---

## 5. Die Ersetzungen

**Reihenfolge ist Teil der Kur.** `B2` **muss vor** `A2` eingesetzt werden: solange
`ZeiterfassungView` die Zeichenkette `  const switchKw=(newKw)=>{` noch enthaelt, kommt der
Anker A2 **zweimal** vor. Nach B2 ist er eindeutig.

> **Empfohlene Reihenfolge:** B1 → B2 → B3 → B4 → A1 → A2 → A3 → A4 → A5 → A6 → A7 → A8 → A9 → A10 → C1…C5

---

### A1 — `yr` wird Zustand (ZWEIZEILIGER Anker, dazwischen CRLF)

**Warum zweizeilig:** die Zeile `  const curKw=isoW();const yr=isoWY();/* v3.9.127 F2 */` kommt
als Teilzeichenkette **3×** vor (Z. 21348 `WeekPlan`, Z. 25333 `ZeiterfassungView`, und als
Suffix der 8-fach eingerueckten Z. 15240). Mit der Funktionszeile davor: **1×**.

**ANKER (2 Zeilen, `\r\n` dazwischen) — Vorkommen: 1**

```
function WeekPlan({ww,curUser,wpHistory,setWpHistory,monteure,projects,fahrzeuge,abs}){
  const curKw=isoW();const yr=isoWY();/* v3.9.127 F2 */
```

**ERSATZ (2 Zeilen, `\r\n` dazwischen)**

```
function WeekPlan({ww,curUser,wpHistory,setWpHistory,monteure,projects,fahrzeuge,abs}){
  const curKw=isoW();const curYr=isoWY();const [yr,setYr]=_react.useState.call(void 0, curYr);/* v3.9.127 F2 | v3.9.993 Z2: yr ist ZUSTAND statt Konstante. Vorher war das Jahr auf den Montage-Zeitpunkt festgenagelt: _wpKey, die Klemme in switchKw und die Server-Spalte `year` konnten die Jahresgrenze nicht ueberschreiten — 223 tote Navigationstage 2020-2035, und am 01.01.2027 ab 09:00 fragte die Lagertafel den Schluessel 2027-1 ab, den die Planung an dem Tag nicht schreiben konnte. curYr bleibt das Jahr von HEUTE (fuer die Abzeichen). */
```

**Namenspruefung (gemessen):** `curYr` kommt in `index.html` **0×** als eigenstaendiger Bezeichner
vor (6 Treffer, alle `_curYr` in einem fremden Bauteil ab Z. 10244). `setYr` **0×**.
`_wpStep`, `_tYr`, `_wpOrd` jeweils **0×**. Keine Kollision.

**Hook-Ordnung:** `_react.useState` steht damit als **erster** Hook in `WeekPlan`.
Die Zeile ist die **erste Anweisung** des Rumpfs — kein `return`, kein `if` davor.
Die Reihenfolge ist unbedingt und bei jedem Render gleich. ✅

---

### A2 — `switchKw` nimmt ein Zieljahr entgegen

**ANKER — Vorkommen: 2 vor B2, danach 1. B2 ZUERST EINSETZEN.**

```
  const switchKw=(newKw)=>{
```

**ERSATZ**

```
  const switchKw=(newKw,newYr)=>{
```

---

### A3 — die Klemme rollt ueber die Jahresgrenze, statt dort zu stehen

**ANKER — Vorkommen: 1** (359 Zeichen)

```
    newKw=Math.max(1,Math.min(_getMaxKW(yr),newKw));/* v3.9.666 Bug-Hunt: KW-Cap via _getMaxKW(yr) wie ZeiterfassungView (v3.9.544). Der "Nächste Woche ▶"-Button war ungeklammert und konnte in einem 52-Wochen-Jahr KW53 setzen → Plan wurde unter "<yr>-53" gespeichert und war unter KW01 des Folgejahrs unsichtbar (Misfile). Zentral hier statt pro Call-Site. */
```

**ERSATZ**

```
    let _tYr=yr;if(typeof newYr==='number'&&newYr>0){_tYr=newYr;}else if(newKw<1){_tYr=yr-1;newKw=_getMaxKW(_tYr);}else if(newKw>_getMaxKW(yr)){_tYr=yr+1;newKw=1;}newKw=Math.max(1,Math.min(_getMaxKW(_tYr),newKw));/* v3.9.666 Bug-Hunt: KW-Cap via _getMaxKW(yr) wie ZeiterfassungView (v3.9.544). Der "Nächste Woche ▶"-Button war ungeklammert und konnte in einem 52-Wochen-Jahr KW53 setzen → Plan wurde unter "<yr>-53" gespeichert und war unter KW01 des Folgejahrs unsichtbar (Misfile). Zentral hier statt pro Call-Site. | v3.9.993 Z2: die Klemme ROLLT jetzt. Ueber maxKW hinaus -> KW1 des Folgejahres, unter KW1 -> letzte Woche des Vorjahres; ein ausdrueckliches newYr hat Vorrang (Rueckweg des Umschalters). Danach klemmt Math.max/min gegen das ZIELjahr, nicht mehr gegen das Montage-Jahr — die Schranke bleibt also, sie steht nur an der richtigen Stelle. */
```

`_tYr` ist ab hier im ganzen `switchKw`-Rumpf sichtbar und wird von A4 und A5 gelesen.

---

### A4 — das Jahr mitsetzen

**ANKER — Vorkommen: 1** (17 Zeichen, inkl. der vier fuehrenden Leerzeichen)

```
    setKw(newKw);
```

**ERSATZ**

```
    setKw(newKw);setYr(_tYr);
```

---

### A5 — die Zeilen der ZIELwoche aus dem ZIELjahr lesen

`_wpGet` haengt an der Closure des laufenden Renders, in der `yr` noch das ALTE Jahr ist.
Ohne diese Stelle bliebe die neue Woche leer — und der naechste Autosave wuerde sie leer
zurueckschreiben.

**ANKER — Vorkommen: 1** (61 Zeichen)

```
    const _newRows=padWpRows(migrateRows(_wpGet(newKw)||[]));
```

**ERSATZ**

```
    const _newRows=padWpRows(migrateRows(wpHistory[_tYr+'-'+newKw]||(_tYr===yr?wpHistory[newKw]:null)||[]));/* v3.9.993 Z2: NICHT _wpGet — das haengt am noch nicht umgesetzten yr dieses Renders. Zieljahr direkt bauen. Der Legacy-Rueckfall auf die blosse KW (alte/offline-gecachte Schluessel ohne Jahr) gilt weiter, aber NUR wenn das Jahr gleich bleibt — sonst zeigte ein Jahressprung den Plan eines fremden Jahres. */
```

---

### A6 — der Nachlade-Effekt muss auch auf das Jahr hoeren

**ANKER — Vorkommen: 1** (20 Zeichen)

```
  },[wpHistory,kw]);
```

**ERSATZ**

```
  },[wpHistory,kw,yr]);
```

---

### A7 — Knopf „Woche zurueck ◀"

**ANKER — Vorkommen: 1** (309 Zeichen)

```
          , React.createElement('button', { title: "Woche zurück", 'aria-label': "Woche zurück", onClick: ()=>switchKw(Math.max(1,kw-1)), style: {...bsS(),padding:isMob?"10px 16px":"5px 10px",fontSize:isMob?16:14,minHeight:isMob?44:0,touchAction:'manipulation'}/* v3.9.507 Mobile: größere Tap-Target */}, "◀")
```

**ERSATZ**

```
          , React.createElement('button', { title: "Woche zurück", 'aria-label': "Woche zurück", onClick: ()=>switchKw(kw-1), style: {...bsS(),padding:isMob?"10px 16px":"5px 10px",fontSize:isMob?16:14,minHeight:isMob?44:0,touchAction:'manipulation'}/* v3.9.507 Mobile: größere Tap-Target | v3.9.993 Z2: Klemme raus — switchKw rollt jetzt selbst ins Vorjahr. */}, "◀")
```

---

### A8 — Knopf „Woche vor ▶" (der tote Knopf aus der Meldung)

**ANKER — Vorkommen: 1** (306 Zeichen)

```
          , React.createElement('button', { title: "Woche vor", 'aria-label': "Woche vor", onClick: ()=>switchKw(Math.min(_getMaxKW(yr),kw+1)), style: {...bsS(),padding:isMob?"10px 16px":"5px 10px",fontSize:isMob?16:14,minHeight:isMob?44:0,touchAction:'manipulation'}/* v3.9.483 + v3.9.507 Mobile */}, "▶")
```

**ERSATZ**

```
          , React.createElement('button', { title: "Woche vor", 'aria-label': "Woche vor", onClick: ()=>switchKw(kw+1), style: {...bsS(),padding:isMob?"10px 16px":"5px 10px",fontSize:isMob?16:14,minHeight:isMob?44:0,touchAction:'manipulation'}/* v3.9.483 + v3.9.507 Mobile | v3.9.993 Z2: Klemme raus — switchKw rollt jetzt selbst ins Folgejahr. */}, "▶")
```

---

### A9 — Umschalter „📅 Naechste Woche ▶ / ◀ Diese Woche"

Dieser Knopf ist **zweimal** betroffen: der Hinweg (`curKw+1`) war in KW `maxKW` tot, und der
Rueckweg (`switchKw(curKw)`) haette aus dem Folgejahr die KW `curKw` **dieses** Jahres gesetzt.
Deshalb bekommt der Rueckweg das Jahr ausdruecklich mit.

**ANKER — Vorkommen: 1** (287 Zeichen)

```
          , React.createElement('button', { onClick: ()=>switchKw(kw===curKw?curKw+1:curKw), style: kw===curKw?bpS:bgS, title: kw===curKw?"Kommende Woche vorausplanen (eigener Plan, aktuelle bleibt erhalten)":"Zurück zur aktuellen Woche"}, kw===curKw?"📅 Nächste Woche ▶":"◀ Diese Woche")
```

**ERSATZ**

```
          , React.createElement('button', { onClick: ()=>{if(kw===curKw&&yr===curYr)switchKw(curKw+1);else switchKw(curKw,curYr);}, style: (kw===curKw&&yr===curYr)?bpS:bgS, title: (kw===curKw&&yr===curYr)?"Kommende Woche vorausplanen (eigener Plan, aktuelle bleibt erhalten)":"Zurück zur aktuellen Woche"}, (kw===curKw&&yr===curYr)?"📅 Nächste Woche ▶":"◀ Diese Woche")/* v3.9.993 Z2: „aktuell" ist (Jahr,KW), nicht KW allein — sonst hiess der Knopf in KW 1/2027 „Nächste Woche" und der Rückweg landete in KW 53/2027. */
```

---

### A10 — die drei Abzeichen vergleichen (Jahr, KW) statt nur die KW

Ohne diese drei Zeilen traegt KW 1/2027 das Abzeichen **„Vergangene Woche"** (weil `1 < 53`),
und die Bedienung meldet die Kur als kaputt.
Der Vergleichswert `yr*100+kw` ist streng monoton, weil `kw ≤ 53 < 100`.

**A10a — ANKER, Vorkommen: 1** (95 Zeichen)

```
          , kw===curKw&&React.createElement(Badge, { text: "Aktuell", color: _okG("#22c55e")} )
```

**ERSATZ**

```
          , (kw===curKw&&yr===curYr)&&React.createElement(Badge, { text: "Aktuell", color: _okG("#22c55e")} )
```

**A10b — ANKER, Vorkommen: 1** (179 Zeichen)

```
          , kw>curKw&&React.createElement(Badge, { text: "📅 Vorausplanung"+(kw===curKw+1?" (nächste Woche)":""), color: "#eab308"} )/* v3.9.471: klare Markierung Zukunfts-Woche */
```

**ERSATZ**

```
          , (yr*100+kw)>(curYr*100+curKw)&&React.createElement(Badge, { text: "📅 Vorausplanung"+(((yr===curYr&&kw===curKw+1)||(yr===curYr+1&&kw===1&&curKw===_getMaxKW(curYr)))?" (nächste Woche)":""), color: "#eab308"} )/* v3.9.471: klare Markierung Zukunfts-Woche | v3.9.993 Z2: Vergleich ueber (Jahr,KW). yr*100+kw ist monoton, weil kw<=53<100. „nächste Woche" gilt auch ueber die Jahresgrenze (KW1 des Folgejahres, wenn heute maxKW ist). */
```

**A10c — ANKER, Vorkommen: 1** (91 Zeichen)

```
          , kw<curKw&&React.createElement(Badge, { text: "Vergangene Woche", color: V.dm} )
```

**ERSATZ**

```
          , (yr*100+kw)<(curYr*100+curKw)&&React.createElement(Badge, { text: "Vergangene Woche", color: V.dm} )
```

---

### B1 — `ZeiterfassungView`: `yr` wird Zustand (ZWEIZEILIGER Anker, dazwischen CRLF)

**Warum zweizeilig:** die Deklarationszeile kommt **3×** vor (wie bei A1). Mit der Zeile
darunter (`const [kw,setKw]=…`, fuer sich allein **2×**) ist das Paar **1×**.

**ANKER (2 Zeilen, `\r\n` dazwischen) — Vorkommen: 1**

```
  const curKw=isoW();const yr=isoWY();/* v3.9.127 F2 */
  const [kw,setKw]=_react.useState.call(void 0, curKw);
```

**ERSATZ (2 Zeilen, `\r\n` dazwischen)**

```
  const curKw=isoW();const curYr=isoWY();const [yr,setYr]=_react.useState.call(void 0, curYr);/* v3.9.127 F2 | v3.9.993 Z2: yr ist Zustand, sonst endet auch hier die Wochennavigation an der Jahresgrenze (◀ bei KW1, ▶ bei maxKW). */
  const [kw,setKw]=_react.useState.call(void 0, curKw);
```

**Hook-Ordnung:** davor stehen nur `isMob`/`isAdmin`, `_hkZE`, `fieldMA` — reine Konstanten,
kein Hook, kein `return`. Der neue `useState` wird der erste Hook des Bauteils, unbedingt. ✅

---

### B2 — `ZeiterfassungView`: `switchKw` rollt (EINSETZEN VOR A2)

**ANKER — Vorkommen: 1** (282 Zeichen)

```
  const switchKw=(newKw)=>{setKw(Math.max(1,Math.min(_getMaxKW(yr),newKw)));};/* v3.9.544 Bug-Hunt: KW-Cap via _getMaxKW(yr) (52/53 je Jahr) statt hardcodiert 53 — in 52-Wochen-Jahren war KW53 fälschlich anwählbar (zeigte KW1 des Folgejahrs). Konsistent mit den anderen KW-Views. */
```

**ERSATZ**

```
  const switchKw=(newKw,newYr)=>{let _tYr=yr;if(typeof newYr==='number'&&newYr>0){_tYr=newYr;}else if(newKw<1){_tYr=yr-1;newKw=_getMaxKW(_tYr);}else if(newKw>_getMaxKW(yr)){_tYr=yr+1;newKw=1;}setKw(Math.max(1,Math.min(_getMaxKW(_tYr),newKw)));setYr(_tYr);};/* v3.9.544 Bug-Hunt: KW-Cap via _getMaxKW(yr) (52/53 je Jahr) statt hardcodiert 53 — in 52-Wochen-Jahren war KW53 fälschlich anwählbar (zeigte KW1 des Folgejahrs). Konsistent mit den anderen KW-Views. | v3.9.993 Z2: die Klemme rollt jetzt ueber die Jahresgrenze statt dort zu stehen. */
```

Die ◀/▶-Knoepfe dieses Bauteils rufen bereits `switchKw(kw-1)` bzw. `switchKw(kw+1)`
**ohne eigene Klemme** — sie brauchen **keine** Aenderung und tragen ab hier von selbst.

---

### B3 — `ZeiterfassungView`: Abzeichen „Aktuell"

**ANKER — Vorkommen: 1** (88 Zeichen)

```
          kw===curKw&&React.createElement(Badge,{text:"Aktuell",color:_okG("#22c55e")}),
```

**ERSATZ**

```
          (kw===curKw&&yr===curYr)&&React.createElement(Badge,{text:"Aktuell",color:_okG("#22c55e")}),
```

---

### B4 — `ZeiterfassungView`: Knopf „Zurueck zur laufenden Woche"

**ANKER — Vorkommen: 1** (80 Zeichen)

```
          kw!==curKw&&React.createElement('button',{onClick:()=>switchKw(curKw),
```

**ERSATZ**

```
          (kw!==curKw||yr!==curYr)&&React.createElement('button',{onClick:()=>switchKw(curKw,curYr),
```

Die Folgezeile (`title:"Zurueck zur laufenden Woche (KW …")`) bleibt unveraendert.

---

### C1 — Projekt-Zeiterfassung: Jahr als Zustand

**ANKER — Vorkommen: 1**

```
  const [calKw,setCalKw]=_react.useState.call(void 0, isoW());
```

**ERSATZ**

```
  const [calKw,setCalKw]=_react.useState.call(void 0, isoW());const [calYr,setCalYr]=_react.useState.call(void 0, isoWY());/* v3.9.993 Z2: die KW-Leiste hatte gar kein Jahr — kwMon rechnete immer im HEUTIGEN ISO-Jahr, ◀ klemmte bei 1 und ▶ bei maxKW(isoWY()). */
```

---

### C2 — Projekt-Zeiterfassung: `kwMon` rechnet im gewaehlten Jahr

Danach ist das `const yr=isoWY();` darueber **unbenutzt** (gemessen: `yr` wird in diesem
Bauteil nur an diesen beiden Stellen gelesen). Es bleibt stehen — ein zweizeiliger Anker
waere noetig, weil diese Zeile **2×** vorkommt (auch in einem zweiten Bauteil ab Z. 15869),
und ein unbenutztes `const` kostet nichts. **Nicht anfassen.**

**ANKER — Vorkommen: 1**

```
  const kwMon=_react.useMemo.call(void 0, ()=>{const d=new Date(yr,0,4);d.setDate(d.getDate()-(d.getDay()||7)+1+(calKw-1)*7);return d;},[calKw,yr]);
```

**ERSATZ**

```
  const kwMon=_react.useMemo.call(void 0, ()=>{const d=new Date(calYr,0,4);d.setDate(d.getDate()-(d.getDay()||7)+1+(calKw-1)*7);return d;},[calKw,calYr]);/* v3.9.993 Z2: gewaehltes Jahr statt isoWY(). Der Effekt darunter haengt an kwMon und zieht damit mit. */
```

---

### C3 — Projekt-Zeiterfassung: Knopf „Vorherige KW ◀"

**ANKER — Vorkommen: 1** (278 Zeichen)

```
          React.createElement('button', { onClick: ()=>setCalKw(k=>Math.max(1,k-1)), 'aria-label': "Vorherige Kalenderwoche", title: "Vorherige KW", style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:isMob?13:12,minHeight:isMob?38:0,touchAction:"manipulation"}}, "◀"),
```

**ERSATZ**

```
          React.createElement('button', { onClick: ()=>{if(calKw>1){setCalKw(calKw-1);}else{setCalYr(calYr-1);setCalKw(_getMaxKW(calYr-1));}}, 'aria-label': "Vorherige Kalenderwoche", title: "Vorherige KW", style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:isMob?13:12,minHeight:isMob?38:0,touchAction:"manipulation"}}, "◀"),/* v3.9.993 Z2: unter KW1 in die letzte Woche des Vorjahres statt stehenbleiben */
```

---

### C4 — Projekt-Zeiterfassung: Knopf „Naechste KW ▶"

**ANKER — Vorkommen: 1** (341 Zeichen)

```
          React.createElement('button', { onClick: ()=>setCalKw(k=>Math.min(_getMaxKW(isoWY()),k+1)), 'aria-label': "Nächste Kalenderwoche", title: "Nächste KW", style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:isMob?13:12,minHeight:isMob?38:0,touchAction:"manipulation"}}, "▶"),/* v3.9.483: _getMaxKW(isoWY()) statt hartem 53 */
```

**ERSATZ**

```
          React.createElement('button', { onClick: ()=>{if(calKw<_getMaxKW(calYr)){setCalKw(calKw+1);}else{setCalYr(calYr+1);setCalKw(1);}}, 'aria-label': "Nächste Kalenderwoche", title: "Nächste KW", style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:isMob?13:12,minHeight:isMob?38:0,touchAction:"manipulation"}}, "▶"),/* v3.9.483: _getMaxKW(isoWY()) statt hartem 53 | v3.9.993 Z2: ueber maxKW hinaus in KW1 des Folgejahres statt stehenbleiben */
```

---

### C5 — Projekt-Zeiterfassung: Abzeichen, Anzeige und „Heute"

**C5a — Abzeichen „Aktuell" — ANKER, Vorkommen: 1**

```
          calKw===isoW()&&React.createElement(Badge,{text:"Aktuell",color:_okG("#22c55e")}),
```

**ERSATZ**

```
          (calKw===isoW()&&calYr===isoWY())&&React.createElement(Badge,{text:"Aktuell",color:_okG("#22c55e")}),
```

**C5b — Knopf „Heute" — ANKER, Vorkommen: 1**

```
          React.createElement('button', { onClick: ()=>setCalKw(isoW()), style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:UI.fMeta,marginLeft:4,minHeight:isMob?38:0,touchAction:"manipulation"}}, "Heute")
```

**ERSATZ**

```
          React.createElement('button', { onClick: ()=>{setCalYr(isoWY());setCalKw(isoW());}, style: {...bsS(),padding:isMob?"8px 12px":"4px 8px",fontSize:UI.fMeta,marginLeft:4,minHeight:isMob?38:0,touchAction:"manipulation"}}, "Heute")
```

**C5c — Anzeige zeigt jetzt auch das Jahr — ANKER, Vorkommen: 1**

```
          React.createElement('span', { style: {fontSize:13,fontWeight:700,fontFamily:mono,minWidth:60,textAlign:"center",color:_okG("#10b981")}}, "KW ", calKw),
```

**ERSATZ**

```
          React.createElement('span', { style: {fontSize:13,fontWeight:700,fontFamily:mono,minWidth:74,textAlign:"center",color:_okG("#10b981")}}, "KW ", calKw, " / ", calYr),/* v3.9.993 Z2: ohne Jahresangabe sieht KW 1/2027 genauso aus wie KW 1/2026 */
```

---

## 6. Risikoabschaetzung — was die Aenderung sonst noch beruehrt

### 🔴 Hoch

**1. Die Server-Spalte `weekplan_rows.year` fuellt sich nach der Kur mit anderen Werten.**
Der Upsert schreibt `year:yr, week:kw`. Heute kann `yr` nur das Montage-ISO-Jahr sein.
Nach A1 entsteht erstmals `year=<Folgejahr>, week=1`. Das ist **gewollt** und deckt sich mit
dem Schluessel, den die Lagertafel ohnehin abfragt. Zu pruefen, bevor es live geht:

* `weekplan_rows` PK / Unique — wenn der PK **nur** `row_id` ist (die `DELETE`-Stelle
  filtert `row_id=eq.…`, also sehr wahrscheinlich), ist alles unveraendert. Wenn der PK
  `(year,week,row_id)` waere, entstuenden Zeilen mit neuen Schluesseln — auch das ist richtig,
  aber es ist eine erste Belegung.
* RLS auf `weekplan_rows` darf nicht auf ein Jahr eingeschraenkt sein.
* **Diese Pruefung ist DDL-nah. Sie gehoert an die Datenbank, nicht in den Quelltext-Riegel.**

**2. A5 ist die Stelle, an der ein Fehler still Daten kostet.**
Laedt `_newRows` die falsche (oder eine leere) Liste, schreibt der 800-ms-Autosave sie in
die Zielwoche zurueck. Mindestens zu belegen: nach `switchKw` ueber die Jahresgrenze
enthaelt `rows` genau das, was unter `<Zieljahr>-<ZielKW>` in `wpHistory` steht — und
`_wpDirtyIds` ist leer (das raeumt `switchKw` bereits, unveraendert).

### 🟡 Mittel

**3. Der Legacy-Rueckfall in `_wpGet` bleibt erhalten, wird aber in A5 enger.**
`_wpGet(k) = wpHistory[yr+'-'+k] || wpHistory[k]` gilt weiter fuer die ANGEZEIGTE Woche.
In A5 gilt der Rueckfall nur noch, wenn das Jahr gleich bleibt. Das ist strenger als heute —
und muss es sein: sonst zeigte ein Sprung nach 2027-KW1 den alten, jahrlosen Eintrag `1`
aus einem beliebigen Jahr. Alte Eintraege **im laufenden Jahr** bleiben unveraendert sichtbar.

**4. Zwei Hooks werden neu eingefuegt und zwar jeweils als ERSTER Hook des Bauteils.**
Gemessen: in beiden Faellen ist die Zeile die erste (bzw. viertlogische, aber hook-freie)
Anweisung des Rumpfs; es gibt davor kein `if`, kein `return`, keine Schleife. Die
Hook-Reihenfolge bleibt bei jedem Render gleich. Ein Fehler hier erzeugt keinen stillen
Defekt, sondern „Rendered fewer hooks than expected" — laut, nicht leise.

**5. `savedKws` (die KW-Sprungknoepfe) zeigt nach einem Jahressprung andere Knoepfe.**
Gewollt: es sind die gespeicherten Wochen des angezeigten Jahres. Wer heute KW-Knoepfe
gewohnt ist, sieht nach einem Sprung nach 2027 zunaechst keine — weil dort noch nichts
gespeichert ist. Das ist richtig, aber es sieht beim ersten Mal nach einem Fehler aus.

**6. Der Wetter-Effekt (`},[kw,yr])`) feuert beim Jahreswechsel zusaetzlich.**
Ein Fetch mehr pro Sprung. Er hat einen `AbortError`-Zweig, also kein Leck.

### 🟢 Niedrig

**7. `_wpYrRef`** wird reaktiv, aber nirgends gelesen. Folgenlos.

**8. Druck/XLS/Titel** tragen ab jetzt das angezeigte Jahr statt des Montage-Jahres.
Das aendert Dateinamen (`Wochenplanung_KW01_2027.xls` statt `…_2026.xls`) — die Korrektur,
nicht die Regression.

**9. Der unbenutzte `const yr` in der Projekt-Zeiterfassung (C2).**
Bleibt absichtlich stehen. Kein Linter-Tor im Repo, das darauf anschlaegt.

### Ausdruecklich NICHT beruehrt

* **`VOffa`, `juprowa`, `ZUZEIT.ASC`** — 0 Treffer in allen drei geaenderten Bereichen (§2).
* `WochenplanTafel` (Lagertafel) und `kioskDisplayWeekOffset` — beide rechnen schon heute
  richtig ueber die Jahresgrenze (`isoWof`/`isoWYof` aus dem verschobenen Datum). Sie waren
  nie der Fehler; sie waren der **Zeuge**.
* `API.getWeekplanRows()` und `_loadWeekplansFromRows` — kein Jahresfilter, keine Aenderung.
* `_wpLoadPrevWeek` / „📋 Vorwoche" — war schon jahresfest.
* Die Sync-/Polling-Kette, `__wpPendingRowIds`, `saveDirty`, der `beforeunload`-Flush.

---

## 7. Woran die Kur zu MESSEN ist (nicht Teil dieses Auftrags, aber der Riegel braucht es)

Ein Riegel, der nur nachsieht, ob `setYr` im Quelltext vorkommt, misst **Anwesenheit**.
Was Wirkung misst:

1. **Reine Rechenprobe ohne DOM:** `_getMaxKW` + die Rollover-Formel aus A3 gegen alle
   5 844 Tage 2020–2035. Erwartung nach der Kur: **0** tote Navigationstage (vorher 223).
   Koeder: die Formel mit `yr` statt `_tYr` in der Klemme laufen lassen — der Riegel MUSS
   dann wieder auf 223 gehen. Geht er das nicht, misst er nichts.
2. **Der Schluessel 2027-1:** ab KW 53/2026 einmal ▶ → der geschriebene `_wpKey` muss
   `2027-1` lauten, und `year` im Upsert muss `2027` sein. Das ist die Stelle, an der
   Planung und Lagertafel sich heute verfehlen.
3. **Kommentare zuerst entfernen.** Meine Ersatztexte enthalten die Zeichenketten
   `_getMaxKW(yr)`, `Math.min`, `switchKw` und `2027-1` **in den Kommentaren**. Ein Riegel,
   der rohen Dateitext durchsucht, misst seine eigene Begruendung mit und wird gruen,
   auch wenn der Aufruf fehlt.
4. **`$?` nach einer Pipe** ist der Code des letzten Glieds. Urteil aus der Logdatei.
