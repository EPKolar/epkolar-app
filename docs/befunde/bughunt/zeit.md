# Bughunt Zeit- und Datumsrechnung — `index.html`

Stand: 30.09.2026 · Baum `C:\repos\epkolar-app`, HEAD `8aa883d`, `index.html` = 30 309 Zeilen / 3 770 595 Byte
Nur gelesen. Keine Datei außer dieser geändert, kein Commit, kein Push.

**Umfang der Messung:** die Funktionen und Ausdrücke, die unten namentlich genannt sind. Alle Läufe mit
`TZ=Europe/Vienna` (node 24.13.1) gegen eine unabhängig gebaute ISO-8601-Referenz (rein UTC/kalendarisch).
Gemessen wurde durch Ausschneiden der echten Zeilen aus `index.html` (Zeilenbereiche, kein Nachtippen) und
Ausführen mit echten Werten. Messskripte liegen im Kratzverzeichnis dieser Sitzung
(`…/scratchpad/zeit/t1_kw.js`, `t2_jahreswechsel.js`, `t3_dauer.js`, `t4_kwof.js`, `t5_kwof_detail.js`,
`t6.js`, `t7_pickerl.js`) — sie sind absichtlich NICHT ins Repo gelegt.

**Nicht gemessen** (kein Zugang in diesem Auftrag): die laufende App im Browser, die Datenbank, ob die
Stempeluhr (`?screen=stempel`) produktiv benutzt wird, echte `stempel_log`-Zeilen.

---

## Zählung

| Stufe | Anzahl |
|---|---|
| 🔴 | 6 |
| 🟡 | 3 |
| ⚪ | 2 |
| ✅ nachgesehen und in Ordnung | 28 Stellen |

Die drei schärfsten: **Z1** (Projekt-Zeiterfassung schreibt am Jahreswechsel Einträge auf Daten ein Jahr
daneben), **Z2** (die erste KW des neuen Jahres ist in der Wochenplanung nicht erreichbar, während die
Lagertafel sie schon zeigt), **Z3** (ab 2027 zeigt die Team-Timeline ab Mittag das ganze Jahr über die
falsche KW).

---

## 🔴 Z1 — `yr` ist das KALENDERjahr, `kw` die ISO-Woche: am Jahreswechsel liegt die ganze Wochenmaske ein Jahr daneben

**Stelle**

* `index.html:16122` (VZeit, Projekt-Zeiterfassung)
  `const yr=new Date().getFullYear();`
* `index.html:16108` — `const [calKw,setCalKw]=…useState(isoW());`
* `index.html:16123` — `const kwMon=…()=>{const d=new Date(yr,0,4);d.setDate(d.getDate()-(d.getDay()||7)+1+(calKw-1)*7);return d;}`
* `index.html:16124-16126` — `dayDate/dateFmt/isoDate` hängen alle an `kwMon`
* `index.html:16244` — `var iso=isoDate(i);`  → `index.html:16263` `setAddDay(iso)` → `index.html:16146` `datum:addDay,date:addDay`
* dieselbe Verwechslung ein zweites Mal: `index.html:15818` `const yr=new Date().getFullYear();` zusammen
  mit `index.html:15817` `const [kw,setKw]=…useState(isoW());` — durchgereicht an
  `VDash` (`index.html:15927` `const dates=kwD(yr,kw);`),
  `VBer` (`index.html:16292` `const wStart=getISO(yr,kw);`) und
  `VOffa` (`index.html:21248` `const dates=kwD(yr,kw);`)

`isoW()` liefert die ISO-Wochennummer, die zum ISO-WOCHENJAHR gehört (`isoWY()`, Z.4749). Ende Dezember
bzw. Anfang Januar sind Kalenderjahr und ISO-Wochenjahr verschieden. Dann wird eine Wochennummer in das
falsche Jahr eingesetzt — und weil `setDate(4-dw+1+(kw-1)*7)` nicht kappt, rutscht das Ergebnis um ein
ganzes Jahr.

**Auslöser und Folge (gemessen)**

| Tag | VZeit zeigt Woche ab | richtig wäre | Versatz |
|---|---|---|---|
| 29.–31.12.2025 (Mo/Di/Mi, **Arbeitstage**) | 2024-12-30 | 2025-12-29 | −364 Tage |
| 01.–03.01.2027 (Fr/Sa/So) | 2028-01-03 | 2026-12-28 | +371 Tage |
| 01.+02.01.2028 | 2028-12-25 | 2027-12-27 | +364 Tage |
| 31.12.2029 (Mo, **Arbeitstag**) | 2029-01-01 | 2029-12-31 | −364 Tage |
| 30.+31.12.2030, 29.–31.12.2031 (Mo/Di/Mi) | Vorjahresanfang | — | −364 Tage |

Über 2020–2035 gesweept: **26 Kalendertage** betroffen, 1–3 Tage an jedem Jahreswechsel, in VZeit UND in
VDash/VBer/VOffa dieselben 26 Tage.

Folge für den Nutzer: an diesen Tagen stehen in der Projekt-Zeiterfassung sechs Spalten mit Datumsangaben
aus einem anderen Jahr. Wer dort einen Eintrag anlegt, bucht ihn auf dieses falsche Datum — `datum`/`date`
kommen aus `isoDate(i)`. Der Toast meldet „✅ x h gespeichert". Die Stunden sind damit nicht verloren,
sondern liegen in der Auswertung eines fremden Jahres; im richtigen Monat fehlen sie. VDash/VBer/VOffa
zeigen an denselben Tagen die Wochenauswertung einer Woche, die ein Jahr entfernt liegt — in der Regel
also 0 h für alles.

🔴 **Der 29./30./31.12.2025 waren gewöhnliche Arbeitstage.** Es ist NICHT geprüft, ob damals Einträge
angelegt wurden — das wäre in `time_entries` mit `date` zwischen 2024-12-30 und 2025-01-05 nachzusehen.

**Wie gemessen** — `t2_jahreswechsel.js`: die Ausdrücke aus 16122/16108/16123 und 15818/15817 + `kwD`
(Z.4752) 1:1 aus der Datei geschnitten, gegen „Montag der ISO-Woche, in der heute liegt" verglichen, Sweep
20.12.–12.01. für jedes Jahr 2020–2035. Eichung: `2026-06-17` liefert in beiden Nachbauten `2026-06-15`,
also fällt ein Tag mitten im Jahr nicht auf.

```
2027-01-01 (Fr): ISO KW53/2026 | VZeit-Montag 2028-01-03 (soll 2026-12-28) | VDash 2028-01-03..2028-01-09
2025-12-29 (Mo): ISO KW1/2026  | VZeit-Montag 2024-12-30 (soll 2025-12-29) | VDash 2024-12-30..2025-01-05
```

Bemerkenswert: der KW-Vor-Knopf in VZeit (`index.html:16219`, `setCalKw(k=>Math.min(_getMaxKW(isoWY()),k+1))`)
kappt gegen das ISO-WOCHENJAHR, `kwMon` zwei Zeilen darüber rechnet mit dem KALENDERjahr. Dieselbe Datei,
dieselbe Ansicht, zwei Jahresbegriffe.

---

## 🔴 Z2 — Die Wochenplanung kann die erste KW des neuen Jahres nicht öffnen; die Lagertafel zeigt sie trotzdem

**Stelle**

* `index.html:21297` — `const curKw=isoW();const yr=isoWY();`
* `index.html:21300` — `const _wpKey=(k)=>yr+'-'+k;` (Schreibschlüssel, `yr` ist eine Konstante, kein State)
* `index.html:21451-21452` — `const switchKw=(newKw)=>{ newKw=Math.max(1,Math.min(_getMaxKW(yr),newKw)); … }`
* Leseseite Kiosk: `index.html:7288-7295` — `_kOff=kioskDisplayWeekOffset(new Date())`,
  `today.setDate(today.getDate()+7*_kOff)`, `const kw=isoWof(today);const yr=isoWYof(today);`,
  `const rows=(wpHistory[yr+'-'+kw]||wpHistory[kw]||[])`

`yr` in `WeekPlan` ist das ISO-Wochenjahr von HEUTE und ändert sich nie. Die Klammer aus v3.9.666 verhindert
damit zwar das Misfile, macht aber die Navigation über die Jahresgrenze tot: bei `kw === _getMaxKW(yr)` gibt
`Math.min` wieder `kw` zurück, bei `kw === 1` gibt `Math.max` wieder `1` zurück.

**Auslöser**: Arbeitswoche 28.–31.12.2026 (KW53/2026, alles Arbeitstage). „Nächste Woche ▶" bleibt auf
KW53. Umgekehrt ab Mo 04.01.2027: „◀ Vorige Woche" bleibt auf KW1, der Plan von KW53/2026 (Schlüssel
`2026-53`) ist aus der Ansicht nicht mehr aufrufbar — es gibt keinen Jahresumschalter.

**Folge für den Nutzer**: Die Wochenplanung für die erste Woche des neuen Jahres lässt sich in der letzten
Arbeitswoche des alten Jahres GAR NICHT anlegen. Genau dann springt die Lagertafel (`?screen=planung`,
Auto-Sprung ab Freitag 09:00 Wiener Zeit, `kioskDisplayWeekOffset`, Z.4758) auf die Folgewoche und liest
einen Schlüssel, den die Planungsansicht an diesem Tag nicht schreiben kann. Auf dem Fernseher im Lager
hängt eine LEERE Tafel mit der Überschrift „KW 1 ▶ nächste Woche". Zusätzlich bleibt der fertige Plan der
letzten Dezemberwoche ab dem 4. Januar unerreichbar.

**Wie gemessen** — `t2_jahreswechsel.js`, Abschnitt „Kiosk vs. WeekPlan-Schreibkey":

```
Freitag 2026-12-25: Kiosk liest "2026-53" | WeekPlan kann schreiben: 2026-1 .. 2026-53 | erreichbar: true
Freitag 2027-01-01: Kiosk liest "2027-1"  | WeekPlan kann schreiben: 2026-1 .. 2026-53 | erreichbar: false
Freitag 2025-12-26: Kiosk liest "2026-1"  | WeekPlan kann schreiben: 2025-1 .. 2025-52 | erreichbar: false
Freitag 2024-12-27: Kiosk liest "2025-1"  | WeekPlan kann schreiben: 2024-1 .. 2024-52 | erreichbar: false
```

Tote Navigation, Sweep 2020–2035: **224 Tage** (die ganze erste und die ganze letzte ISO-Woche jedes
Jahres), z. B. `2021-01-04 … 2021-01-10: „Vorige Woche" bleibt auf KW1`.

Nebenbefund derselben Stelle: `index.html:21861` schreibt in die Druck-/Excel-Kopfzeile `{kw,yr}` und
`index.html:21460` den DB-Satz `year:yr,week:kw` — beides mit demselben konstanten `yr`. Solange die
Klammer greift, entsteht daraus kein falscher Satz; fällt die Klammer, wird sofort misgefiled.

---

## 🔴 Z3 — `kwOf` in der Team-Timeline: falscher Versatzterm plus nicht genullte Uhrzeit → ab 2027 das ganze Jahr KW+1 ab Mittag

**Stelle** — `index.html:23050` (AbsView, `subView==="timeline"`, „🗓️ Team-Timeline")

```js
const kwOf=d=>{const t2=new Date(d);t2.setDate(t2.getDate()-((d.getDay()+6)%7)+3);
  const jan4=new Date(t2.getFullYear(),0,4);
  return 1+Math.round(((t2-jan4)/TIME_DAY-(t2.getDay()+6)%7+3)/7);};
```

Zwei Fehler übereinander:

1. Der Versatzterm `-(t2.getDay()+6)%7+3` ist auf dem Donnerstag IMMER `0`. Richtig wäre
   `-3+((jan4.getDay()+6)%7)` — so steht es in den beiden korrekten Zwillingen `index.html:7810` (`_isoKW`)
   und `index.html:11417` (`calTitle`). Der fehlende Term wird bisher nur von `Math.round` verdeckt.
2. `index.html:23046` — `const startMon=(()=>{const d=new Date(); … })()` — **`d` wird nicht auf
   Mitternacht genullt.** Alle 7·WEEKS Tage in `days` (Z.23047) tragen die aktuelle Uhrzeit, und
   `weekBounds` (Z.23051) füttert `kwOf` mit `days[w*7]`. Damit wandert `(t2-jan4)/TIME_DAY` im Tagesverlauf
   um bis zu 0,96 Tage — und schiebt den von `Math.round` gedeckten Fehler über die 0,5-Grenze.

**Auslöser**: ein ISO-Jahr, in dem der 4. Januar ein MONTAG ist, ab 12:00 Ortszeit (Winterzeit) bzw. 13:00
(Sommerzeit — die DST-Stunde verschiebt die Kippschwelle mit). Das sind **2027** und **2038**. Zusätzlich
der 01. und 02.01.2028 ab 12:00.

**Folge für das Büro**: Über den Spaltengruppen der Team-Timeline steht „KW42", wo KW41 liegt. Die Spalten
selbst (Datum, Balken, Kollisionsmarkierung) sind richtig — falsch ist nur die Zahl, an der sich das Büro
beim Absprechen von Urlaub orientiert. Ab dem 4. Januar 2027, jeden Nachmittag, 362 Kalendertage des Jahres.

**Wie gemessen** — `t4_kwof.js` / `t5_kwof_detail.js`, Sweep 2024–2038 × {00,06,11,12,13,18,23} Uhr gegen die
ISO-Referenz. Eichung: ein absichtlich kaputter Zwilling (immer KW+1) wird in 24 von 24 Stunden gefunden,
der Sucher ist also nicht blind.

```
kwOf (Z.23050) Abweichungen je Jahr: {"2027":1231,"2028":8,"2038":1231}
   2027-01-04 12:30 -> KW2 statt KW1        2027 — 4. Januar ist ein Mo
   11.01. (Winterzeit, echte KW2):  falsch ab 12:00
   05.07. (Sommerzeit, echte KW27): falsch ab 13:00
   betroffene Kalendertage 2027: 362      (2026: 0, 2028: 2, 2038: 362)
2028-01-01 12:30 (Sa) -> KW53 statt KW52
```

Rechenweg am Einzelfall (`t6.js`, 11.01.2027, echte KW2):

```
00:00 | Do der Woche Thu Jan 14 2027 00:00 | (t2-jan4)/Tag = 10.0000 | Versatzterm 0 | kwOf = 2
12:00 | Do der Woche Thu Jan 14 2027 12:00 | (t2-jan4)/Tag = 10.5000 | Versatzterm 0 | kwOf = 3
```

`10.5/7 = 1.5`, `Math.round(1.5) = 2` → KW3. Mit dem richtigen Versatzterm `-3` wäre es `7.5/7 = 1.07 → 1`
und damit unter allen Uhrzeiten richtig.

**Gegenprobe**: dieselbe Messung an `_isoKW` (Z.7810) und `_kwFromDate` (Z.12985) ergibt über 2024–2038 und
alle sieben Uhrzeiten **0 Abweichungen**. Beide nullen vorher auf Mitternacht. Der Fehler sitzt allein in
Z.23050.

---

## 🔴 Z4 — Übernacht-Schicht in der Stempeluhr: acht Stunden zählen als null, und der Saldo fällt doppelt

**Stelle**

* `index.html:5022` — `_pzeDayKey(ts)` gruppiert nach dem LOKALEN Kalendertag
* `index.html:5026` — `_pzeGroupByDay`
* `index.html:2364` — `_stPairEvents(events)`: ein `gehen` ohne offenes `kommen` IM SELBEN Tagesbündel
  wird verworfen
* `index.html:2371` — `_stTagNetto`
* `index.html:12345` — `_pzeBuildRows` iteriert Kalendertage und holt `byDay[k]`

**Auslöser**: Kommen Mo 15.06.2026 22:00, Gehen Di 16.06.2026 06:00.

**Folge für den Mitarbeiter**: `2026-06-15` trägt nur den `kommen`-Stempel, `2026-06-16` nur den
`gehen`-Stempel. Kein Tag paart auf, beide Tage liefern netto 0 min. Die tatsächlich anwesenden 8 h
erscheinen NIRGENDS. Der Monatssaldo verliert an dieser einen Nacht 2 × 8:30 h = **−17 h**. Im PZE-Monatsblatt
(`_pzePdf`) und im Excel steht an beiden Tagen 0:00 Gesamt und −8:30 Saldo.

Mildernd: beide Tage werden von `_pzeUngerade` (Z.5035) als inkonsistent markiert und landen in der
Fehler-Queue (`index.html:12596` `_fehler`), das Büro sieht sie also. Nicht mildernd: es gibt **keinen Weg,
eine Übernacht-Schicht richtig abzubilden** — auch die additive Korrektur (`index.html:12612` `_saveKorr`,
`new Date(korr.datum+'T00:00:00').setHours(hh,mm)`) kann nur einen Stempel auf EINEM Kalendertag nachtragen.

**Wie gemessen** — `t3_dauer.js`, Abschnitt 1 (Rolle „Monteur", Pausenregel `{default:60}`):

```
EICHUNG Normaltag Mo 07:00-16:30: brutto 570 pause 60 netto 510 soll 510 saldo 0 ungerade false
Tagesschluessel: ["2026-06-15","2026-06-16"]
  2026-06-15: Stempel 1, Paare 0, netto 0 min, soll 510, SALDO -510 min, ungerade=true
  2026-06-16: Stempel 1, Paare 0, netto 0 min, soll 510, SALDO -510 min, ungerade=true
  tatsaechlich anwesend: 480 min = 8 h — davon in der Rechnung: 0 min
```

**Nicht gemessen**: ob die Stempeluhr produktiv benutzt wird. Der Kopfkommentar Z.2351 nennt sie noch
„Fundament (DORMANT)", die PZE-Ansicht samt Monatsblatt-PDF und Korrekturweg ist aber vollständig gebaut.
Trifft die Stufe nur, wenn nachts gestempelt wird.

---

## 🔴 Z5 — Der Pausenabzug greift an jedem gestempelten Tag in voller Höhe, auch am 4,5-Stunden-Freitag

**Stelle**

* `index.html:2359` — `const STEMPEL_PAUSE_MIN=60;`
* `index.html:2360` — `STEMPEL_PAUSE_FALLBACK={Backoffice:0,default:60}`
* `index.html:2363` — `_stPauseAbzug(role,rules)` → `rules[role] ?? rules.default ?? 60`
* `index.html:2371-2376` — `_stTagNetto`: `return Math.max(0,brutto-_stPauseAbzug(role,rules));`
  („Abzug EINMAL/Tag, nie negativ")
* dagegen im selben Regelwerk: `index.html:2480` — `KV_RULES_FALLBACK={ … pauseAbStd:6, pauseMin:30, … }`
  und `index.html:2521` — `_kvTagesnorm`: Freitag = **4,5 h** Tagesnorm

`_stTagNetto` benutzt von `pauseAbStd` und `pauseMin` NICHTS. Die Datei führt damit zwei widersprüchliche
Pausenregeln: „ab 6 h, 30 min" (KV-Block) und „immer, 60 min" (Stempel-Block).

**Auslöser**: ein normaler Freitag. Tagesnorm 4,5 h. Der Mitarbeiter stempelt 07:00 kommen, 11:30 gehen.

**Folge für den Mitarbeiter**: 4,5 h anwesend, netto 3,5 h, Soll 4,5 h → **Saldo −1:00 an jedem Freitag**.
Um die Freitagsnorm zu erreichen, müsste er 5,5 h anwesend sein. Bei einem Halbtag von 2 h Anwesenheit
bleibt 1 h übrig — 60 Minuten Pause für eine Zwei-Stunden-Anwesenheit.

**Wie gemessen** — `t3_dauer.js`, Abschnitt 2 (Rolle „Monteur", `{default:60}`):

```
  07:00-09:00 (2 h anwesend) -> netto  60 min = 1.00 h  (Abzug 60 min)
  07:00-11:00 (4 h anwesend) -> netto 180 min = 3.00 h  (Abzug 60 min)
  07:00-12:00 (5 h anwesend) -> netto 240 min = 4.00 h  (Abzug 60 min)
  07:00-13:00 (6 h anwesend) -> netto 300 min = 5.00 h  (Abzug 60 min)
  07:00-16:00 (9 h anwesend) -> netto 480 min = 8.00 h  (Abzug 60 min)
```

Ob 60 min unbedingt die Betriebsregel sind, ist über `system_config.stempel_pause_rules`
(`_stLoadPauseRules`, Z.2380) überschreibbar und hier NICHT gemessen. Der Widerspruch zu `pauseAbStd:6`
im eigenen KV-Block besteht unabhängig davon: es gibt keine Schwelle, ab der überhaupt abgezogen wird.

---

## 🔴 Z6 — Manuelle Erfassung: ist (bis − von) ≤ Pause, wird der ALTE Stundenwert gespeichert

**Stelle**

* `index.html:2447-2452` — `_zeitEffektiveStunden(von,bis,pause)`: `return d>0?Math.round(d*100)/100:null;`
* `index.html:16141-16146` (VZeit `addEntry`) und wortgleich `index.html:25479` (ZeiterfassungView)

```js
const _rVon=_zeitRundVon(addVon), _rBis=_zeitRundBis(addBis);
let _h2=addHours;
if(_rVon&&_rBis){const _d=_wrapHrs(_rVon,_rBis)-addPause;if(_d>0)_h2=Math.round(_d*100)/100;}
const h=_h2; … stunden:Math.round(h*100)/100
```

* Vorbelegungen: `index.html:16112-16115` — `addVon "07:00"`, `addBis "16:00"`, `addPause 1`, **`addHours 8`**
* `index.html:16196-16198` — die `onChange`-Handler aktualisieren `addHours` ebenfalls nur `if(d>0)`

Ist die Differenz kleiner oder gleich der Pause, wird `_h2` NICHT neu berechnet und behält die Vorbelegung
`8`. Gleichzeitig gibt `_zeitEffektiveStunden` `null` zurück, das Stundenfeld (Z.16199) wird wieder
beschreibbar und zeigt `addHours` = 8.

**Auslöser**: Von 08:00, Bis 09:00, Pause bleibt auf der Vorbelegung „1h" (ein kurzer Einsatz).

**Folge für den Nutzer**: Gespeichert wird `von:"08:00", bis:"09:00", pause:1, stunden:8`. Der Satz
widerspricht sich selbst; Wochenexcel und Stundenbestätigung drucken „08:00–09:00 · 8,0h". Sieben Stunden
zu viel auf Lohn und Projektkosten, mit grünem Erfolgs-Toast. Bei Von = Bis dasselbe.

**Wie gemessen** — `t3_dauer.js`, Abschnitt 5 (Nachbau von 16141-16146, `addHours`-Vorbelegung 8):

```
  von 08:00 bis 08:30 Pause 1h: _zeitEffektiveStunden=null | addEntry speichert stunden=8
  von 08:00 bis 08:00 Pause 1h: _zeitEffektiveStunden=null | addEntry speichert stunden=8
  von 08:00 bis 09:00 Pause 1h: _zeitEffektiveStunden=null | addEntry speichert stunden=8
  von 16:00 bis 07:00 Pause 1h: _zeitEffektiveStunden=14   | addEntry speichert stunden=14
```

Die Zahl 8 steht dabei im Feld — sie ist nicht unsichtbar. Die Einstufung 🔴 begründet sich darauf, dass
ein lohnrelevanter Satz mit einer Zahl gespeichert wird, die aus einer VORBELEGUNG stammt und nichts mit
den daneben gespeicherten Uhrzeiten zu tun hat. Der Kommentar in Z.2441-2446 verspricht ausdrücklich das
Gegenteil („`_zeitEffektiveStunden` liefert GENAU die Zahl, die addEntry speichern wird") — für `d<=0`
hält er nicht.

Letzte Zeile der Messung als Nebenbefund: vertauschte Eingabe 16:00/07:00 ergibt über den
Übernacht-Wrap 14 h und wird ohne Rückfrage gebucht.

---

## 🟡 Z7 — `setMonth(+6)` läuft am Monatsende über: Kalibrierfrist bis zu drei Tage zu spät

**Stelle** — `index.html:29952` (Werkzeug-Scan, „Kalibrierung erledigt")

```js
const nd=new Date();nd.setMonth(nd.getMonth()+6);
const _patch={letzteKalib:td2(),naechsteKalib:_ymd(nd),status:"verfuegbar"};
```

**Auslöser**: Kalibrierung am 31.08. bestätigt.

**Folge**: `naechsteKalib` wird `03.03.` (in einem Schaltjahr `02.03.`) statt `28./29.02.`. Das Werkzeug gilt
bis zu drei Tage länger als kalibriert; `_wzKalibFaellig` (`index.html:4740`) schlägt entsprechend später
an. Kein Datenverlust, aber eine Frist, die sich selbst verlängert.

**Wie gemessen** — `t4_kwof.js`, letzter Abschnitt, Sweep über alle Tage 2026–2027 gegen „gleicher Tag im
Monat +6, am Monatsende gekappt": **13 Überlauf-Fälle in zwei Jahren**.

```
2026-03-31 +6 Mon -> 2026-10-01 (erwartet 2026-09-30)
2026-08-29 +6 Mon -> 2027-03-01 (erwartet 2027-02-28)
2026-08-31 +6 Mon -> 2027-03-03 (erwartet 2027-02-28)
2026-10-31 +6 Mon -> 2027-05-01 (erwartet 2027-04-30)
2026-12-31 +6 Mon -> 2027-07-01 (erwartet 2027-06-30)
2027-08-30 +6 Mon -> 2028-03-01 (erwartet 2028-02-29)
```

---

## 🟡 Z8 — Am Fälligkeitstag selbst geben zwei Stellen zwei verschiedene Antworten

**Stelle**

* `index.html:863` — `window._pickerlStatus=(datum,warnDays)=>{ … const diff=(d-new Date())/TIME_DAY;if(diff<0)return 'overdue'; … }`
* `index.html:15423` — Fahrzeug-Termine-Liste: `const diff=Math.ceil((d-new Date())/TIME_DAY); … sub:diff<0?"ÜBERFÄLLIG":diff+"T"`
* Dritte Konvention: `index.html:4740` `_wzKalibFaellig` → `w.naechsteKalib<=td2()` (reiner ISO-Vergleich)

`_pickerlStatus` vergleicht einen Zeitpunkt (lokale Mitternacht des Fälligkeitstags) mit JETZT. Eine Sekunde
nach Mitternacht ist `diff` negativ.

**Auslöser**: Pickerl-Datum 30.09.2026, Blick in die App am 30.09.2026 um 09:00.

**Folge**: Das Fahrzeug trägt das rote „overdue" (Status-Punkt, KPI-Kachel, `pickerFaellig` Z.15044),
während die Termin-Liste unmittelbar daneben „0T" schreibt, also NICHT überfällig. Ein Tag Differenz zwischen
zwei Anzeigen derselben Zahl; welche Konvention gewollt ist („letzter gültiger Tag" oder „erster
Verfallstag") steht in keinem Kommentar und ist hier nicht entscheidbar.

**Wie gemessen** — `t7_pickerl.js` (Eichung: ein Datum 2030 liefert überall „nicht fällig"):

```
Faelligkeitsdatum = 30.09.2026, Messung am 30.09.2026:
  00:00 -> _pickerlStatus='warn'     | Termin-Liste sub='0T' | Kalib-Regel faellig=true
  01:00 -> _pickerlStatus='overdue'  | Termin-Liste sub='0T' | Kalib-Regel faellig=true
  09:00 -> _pickerlStatus='overdue'  | Termin-Liste sub='0T' | Kalib-Regel faellig=true
  23:00 -> _pickerlStatus='overdue'  | Termin-Liste sub='0T' | Kalib-Regel faellig=true
am Vortag 29.09.2026 15:00: _pickerlStatus='warn' | Termin-Liste sub='1T'
```

---

## 🟡 Z9 — `_kioskWeekRange` bricht die Prämisse, die zwei Zeilen darüber begründet wird

**Stelle** — `index.html:2236`

```js
function _kioskWeekRange(){ … const x=new Date();x.setHours(0,0,0,0);const dw=x.getDay()||7;
  x.setDate(x.getDate()-(dw-1));x.setDate(x.getDate()+7*kioskDisplayWeekOffset(new Date())); … }
```

`kioskDisplayWeekOffset` (Z.4758) leitet Wochentag und Stunde ausdrücklich über
`Intl.DateTimeFormat(timeZone:'Europe/Vienna')` ab, weil laut eigenem Kommentar (Z.4755) „kein roher
getDay/getHours auf evtl. falsch/UTC-konfiguriertem Kiosk-PC" verwendet werden soll. Der Aufrufer bestimmt
den Wochenanfang trotzdem mit rohem `x.getDay()`. Gleiches Muster in `index.html:7282` (Abwesenheits-RPC)
und `index.html:7289-7290` (Spaltenraster der Tafel).

**Folge**: Solange die Kiosk-Uhr richtig gestellt ist, kommt dasselbe heraus (gemessen: Offset und Raster
stimmen an allen geprüften Tagen überein). Steht der Kiosk-PC auf UTC oder einer fremden Zone, springt der
Offset nach Wiener Zeit, das Spalten- und Abfrageraster aber nach der Gerätezone — Überschrift und Inhalt
können dann um eine Woche auseinanderlaufen. **Kein Gerät mit falscher Zone gemessen**, deshalb 🟡 und
nicht 🔴: die Inkonsistenz ist belegt, der Schaden nicht.

---

## ⚪ Z10 — `_wrapHrs` über die Zeitumstellung: Uhrenzeit statt Arbeitszeit

**Stelle** — `index.html:5103`

```js
function _wrapHrs(von,bis){const v=new Date("2000-01-01T"+(von||"00:00")),
  b=new Date("2000-01-01T"+(bis||"00:00"));let h=(b-v)/36e5;if(h<0)h+=24;return h;}
```

Der feste Ankertag 01.01.2000 ist DST-frei — das ist bewusst und macht die Funktion reproduzierbar. Damit
liefert sie für 22:00–06:00 IMMER 8 h, auch in den zwei Nächten pro Jahr, in denen die Schicht 7 bzw. 9
Stunden dauert.

**Wie gemessen** — `t3_dauer.js`, Abschnitt 4:

```
Schicht 22:00-06:00, Nacht 24./25.10.2026 (Umstellung): _wrapHrs = 8 h, tatsaechlich 9 h
Schicht 22:00-06:00, Nacht 28./29.03.2026 (Umstellung): _wrapHrs = 8 h, tatsaechlich 7 h
Stempeluhr (ms-basiert) rechnet dieselbe Nacht: 9 h -> DST-korrekt
```

**⚪, nicht 🔴**: die beiden Wege widersprechen sich (Stempeluhr rechnet nach echter Dauer, manuelle
Erfassung nach Uhrenstand), aber welcher Wert lohnrichtig ist, ist eine Betriebsentscheidung und steht
nirgends in der Datei. Zu Ende gemessen ist nur die Abweichung, nicht ihr Vorzeichen.

---

## ⚪ Z11 — 29. Februar als Eintrittsdatum in der EFZG-Staffel

**Stelle** — `index.html:2580` `_kvDienstjahre`, `index.html:2592` `_efzgArbeitsjahrStartMs`
(`new Date(y,e.getMonth(),e.getDate())` → 29.02. in einem Nicht-Schaltjahr wird 01.03.).
Rechnerisch nachvollzogen, aber nicht mit echten `workers.eintritt`-Werten gemessen — ob überhaupt jemand
am 29.02. eingetreten ist, konnte hier nicht geprüft werden. Wirkung höchstens ein Tag auf den Beginn des
laufenden Arbeitsjahres.

---

## ✅ Nachgesehen und in Ordnung — bitte nicht zweimal prüfen

Alles hier ist gemessen, nicht nur gelesen. Referenz war jeweils eine unabhängig gebaute ISO-8601-Rechnung
bzw. ein Nachrechnen mit echten Werten. Umfang je Zeile in Klammern.

**ISO-Kalenderwoche und Wochenjahr**

* `isoW` / `isoWY` (`index.html:4748`, `4749`) und ihre argumentnehmenden Klone `isoWof` / `isoWYof`
  (`4769`, `4770`) — **0 Abweichungen** an allen 9 497 Tagen 2015–2040, Woche UND Wochenjahr.
* `_getMaxKW` (`index.html:4751`) — **0 Abweichungen** 2015–2040; 53-Wochen-Jahre korrekt erkannt:
  2015, 2020, 2026, 2032, 2037.
* `kwD(y,k)` (`index.html:4752`) — für jedes Jahr 2015–2040 und jede KW 1…maxKW: alle sieben Tage liegen
  in der richtigen ISO-Woche des richtigen ISO-Jahres, Tag 0 ist immer ein Montag. **0 Abweichungen.**
  Auch die Jahresgrenze: `kwD(2026,1)` = 29.12.2025 … 04.01.2026.
* `_ezKW` (`index.html:11925`, rein UTC) — **0 Abweichungen** 2015–2040.
* `_isoKW` (`index.html:7810`) und die Inline-Fassung in `calTitle` (`index.html:11417`) —
  **0 Abweichungen** 2024–2038 × 7 Uhrzeiten (beide nullen auf Mitternacht).
* `_kwFromDate` (`index.html:12985`) — **0 Abweichungen** 2024–2038 × 7 Uhrzeiten.
* `_pzeKW` (`index.html:5079`) — verankert auf `T12:00`, damit unabhängig vom Tagesrand.

**Monats- und Wochenraster**

* `weeksOf(y,m)` (`index.html:4773`) — 2024–2030, alle 84 Monate: jeder Monatstag kommt vor, jede Woche
  hat 7 Tage, Start immer Montag. **0 Abweichungen.**
* `_ezMonthGrid` / `_ezWeekDays` (`index.html:11895`, `11914`) — iterieren kalendarisch über `setDate`,
  Abbruch über Jahr·12+Monat; Dezember rollt korrekt ins Folgejahr.
* `_ezFetch`-Monatsfenster (`index.html:12395 f.`) — `new Date(jahr, monat, 1)` mit 1-basiertem Monat als
  0-basiertem Index ergibt korrekt den Ersten des Folgemonats, Dezember inklusive Jahressprung.
* Fahrtenbuch-Monatsfenster (`index.html:24920-24924`) — `to=_ymd(new Date(_fbJ,_fbM,1))`, exklusiv,
  Monatslänge korrekt (die in v3.9.897 behobene 32-Tage-Fassung ist weg).
* Stempel-Monatsfenster (`index.html:12397-12400`, `12560-12562`) — lokale Mitternacht → `toISOString`,
  Ende über `setDate(+1)` statt `+86400000`; die 25-Stunden-Nacht Ende Oktober ist abgedeckt.
* `_fbZeitraum` (`index.html:26462`) — `heute` / `woche` / `vormonat` / Monat, alles aus lokalen
  Komponenten; `new Date(y,m-1,1)` trägt den Januar korrekt ins Vorjahr, `new Date(y,m,0)` liefert den
  letzten Vormonatstag.

**Feiertage**

* `_easterSunday` (`index.html:4980`) — gegen zwölf bekannte Ostersonntage 2020–2030 und 2038:
  **0 Abweichungen.**
* `_isATFeiertag` (`index.html:4987`) — liefert für 2026 und 2027 je genau 13 Tage, und zwar die
  vollständige österreichische Liste; der 26.10. ist seit v3.9.875 drin, Karfreitag richtigerweise nicht.
  2026: 01.01 · 06.01 · 06.04 · 01.05 · 14.05 · 25.05 · 04.06 · 15.08 · 26.10 · 01.11 · 08.12 · 25.12 · 26.12.
  2027: 01.01 · 06.01 · 29.03 · 01.05 · 06.05 · 17.05 · 27.05 · 15.08 · 26.10 · 01.11 · 08.12 · 25.12 · 26.12.
  Eichung des Suchers: 26.10.2026 → true, 27.10.2026 → false.

**Dauer und Rundung**

* `_stRoundKommen` / `_stRoundGehen` (`index.html:2361`, `2362`) — Millisekunden-basiert, damit
  DST-unabhängig; Kommen auf, Gehen ab, Rasterwerte unverändert.
* `_zeitParse` / `_zeitFmt` / `_zeitRundVon` / `_zeitRundBis` (`index.html:2426`–`2471`) — 7:03 → 07:05,
  16:47 → 16:45; die 23:56–23:59-Kappung auf 23:55 greift; Müll („abc", „7:3", "") kommt unverändert
  zurück und wird von den Aufrufern als „leer" behandelt.
* `_pzeAutoPause` (`index.html:5045`) — legt die Pause mittig in die Anwesenheit (07:00–16:30, 60 min
  → 11:15–12:15) und ist als „autom." gelabelt.
* `_pzeTagRow` / `_pzeSummen` (`index.html:5053`, `5080`) — Normaltag 07:00–16:30, Rolle Monteur, 60 min:
  brutto 570, Pause 60, netto 510, Soll 510, Saldo 0, `ungerade=false`. Der angezeigte Pausenwert ist
  der TATSÄCHLICH angewandte (`brutto-netto`), nicht der Regelwert.
* `_pzeUngerade` (`index.html:5034`) — offener Tag (1× kommen) wird als inkonsistent markiert und NICHT
  als Fehltag gezählt.
* `_pzeBuildRows` (`index.html:12345`) — Tagesiteration über `setDate(+1)` mit ISO-String-Abbruch, kein
  `+TIME_DAY`; März behält 31 Zeilen.
* `_pzeDayKey` (`index.html:5022`) — lokaler Kalendertag, kein UTC-Kippen; ein Stempel um 23:30 bleibt
  auf dem heutigen Tag.
* `_kvTagesnorm` (`index.html:2521`) — Mo–Do 8,5 / Fr 4,5 / Sa,So,Feiertag 0.
* `_kvTagZuschlag` (`index.html:2526`) — Kumulationssperre, Mehrarbeitsband vor 50/100 %.

**Datumsvergleiche und Tagesschleifen**

* `_antragWerktage` und `_materialisiereAbsence` (`index.html:24349`, `24360`) — `T00:00:00` plus
  `setDate(+1)`, damit über die Oktober-Umstellung stabil.
* `_sollRange` (`index.html:24651`) — dieselbe Schleifenform, mit Guard.
* `_wpMaSichtbarAmTag` / `_maIstEhemalig` (`index.html:10024`, `10037`) — reiner ISO-String-Vergleich,
  kein `new Date`.
* `_ezHeuteISO` (`index.html:12007`) — `Intl` mit `en-CA` und `timeZone:'Europe/Vienna'`, Fallback auf
  lokale Komponenten.
* `_ezWtag` (`index.html:11887`) — `T12:00:00Z` plus Wiener Zone, kein Tagesrand-Kippen.
* `_ymd` (`index.html:4722`) und `dk` (`index.html:4743`) — lokale Komponenten statt `toISOString`.
* `_fyOf` (`index.html:4747`) — Geschäftsjahr 1.7.–30.6., Monatsgrenze und Jahresbeschriftung korrekt.
* `_dispoZeitkonflikte` (`index.html:5816`) — die Überlappungsprüfung hat keinen Tages-/Monteursfilter,
  wird aber ausschließlich pro (Monteur, Tag) aufgerufen (`index.html:10500`, `10665`); die Paarung ist
  damit richtig eingegrenzt.
* Excel-Wochenblöcke der PZE (`index.html:12634-12639`) — `flush` auf KW-Wechsel; auch ein Monat, der
  KW52 und KW1 enthält (Dezember) bricht korrekt um.
* `kioskDisplayWeekOffset` (`index.html:4758`) — Wiener Wochentag und Stunde über `Intl`, `hh===24`
  abgefangen, Freitag ab 09:00 bis Sonntag 23:59 → 1, sonst 0.
* `_kioskWienNow` / `_kioskDailyShouldReset` (`index.html:3271`, `3288`) — Wiener Datum und Stunde,
  Erst-Lauf ohne Reload, Marker gleich heute → kein Reset.
* `_asZeitUebernahme`-Datum (`index.html:11105`) — Termin-`slice(0,10)`, sonst heutiges lokales Datum.
* `activity_log`-Tagesfilter (`index.html:14875`) — `new Date(td2()+"T00:00:00").toISOString()`, also
  lokale Mitternacht als UTC-Zeitpunkt.

---

## Was NICHT gemessen werden konnte

* Die laufende App am Schirm: alle Befunde sind an den ausgeschnittenen Funktionen und Ausdrücken
  gemessen, nicht am gerenderten DOM. Für Z1/Z2/Z3 hieße eine Bestätigung am Schirm: Systemuhr auf
  29.12.2025 bzw. 04.01.2027 bzw. 11.01.2027 13:00 stellen und die jeweilige Ansicht öffnen.
* Die Datenbank: ob in `time_entries` Sätze mit Datum 30.12.2024–05.01.2025 liegen (Z1, Dezember 2025),
  und ob `stempel_log` überhaupt Nachtstempel enthält (Z4).
* `system_config.stempel_pause_rules` — der reale Pausenabzug je Rolle (Z5).
* Ein Kiosk-PC mit falsch gestellter Zeitzone (Z9).
