# Bughunt Rechenfehler — `index.html`

Stand: 30.09.2026 · Baum `C:\repos\epkolar-app` · `origin/main` bei `8aa883d`,
Arbeitsbaum-Fassung `APP_VERSION="3.9.990-supabase"` · `index.html` = 30 309 Zeilen / 3 770 595 Bytes.

Gebiet: alles, wo gerechnet wird und der Nutzer die Zahl glaubt — Arbeitsstunden und ihre
Umrechnung, Pausenabzug, Zulagen, Summen und Zwischensummen, Rundung, Prozente, Mengen und
Preise, Kilometer, Mehrwertsteuer, und alles, was in ein PDF oder einen Export geht.

**Es wurde nichts geändert.** Diese Datei ist die einzige geschriebene Datei.

---

## Zählung

| Stufe | Anzahl |
|---|---|
| 🔴 falsche Zahl beim Nutzer | **4** |
| 🟡 falsch, aber folgenlos oder sichtbar | **4** |
| ⚪ nicht zu Ende gemessen | **4** |
| ✅ nachgesehen und in Ordnung | **17 Punkte** |

Die drei schärfsten: **P3** (Arbeitsschein-Zeit läuft ohne 0–24-Stunden-Wächter in
`time_entries`), **P1/P2** (die beiden Lohn-Excel-Blätter runden je Zeile auf eine
Nachkommastelle und verlieren dadurch 7 Minuten pro Woche), **P4** (ein Urlaubsanspruch
von 0 Stunden ist nicht eingebbar und wird als 192,5 h angezeigt).

---

## Wie hier gemessen wurde

**1. Kommentare wurden aus der Messung genommen — mit Eichung.** Die Datei trägt riesige
deutsche Erklärkommentare (die `APP_VERSION`-Zeile 3113 allein enthält 141 Treffer auf
Steuer-/Netto-/Brutto-Begriffe, alle in Prosa). Für jede Mustersuche wurde deshalb eine
**zeilentreue** Fassung ohne Kommentare erzeugt: Kommentarzeichen werden durch Leerzeichen
ersetzt, Umbrüche bleiben stehen, damit die Zeilennummern mit dem Original übereinstimmen.

Der Entferner ist ein rekursiver Zustandsautomat über Strings, Template-Literale (samt
`${}`-Ausdrücken, die selbst wieder Strings, Regex- und Template-Literale enthalten) und
Regex-Literale. **16 Köder, einer je Form**, plus Gegenproben:

```
EICHUNG ok (16 Fälle)
Zeilen roh: 30309   code: 30309
Zeichen roh: 3735553  code: 3735553   (gleich lang -> zeilen- und spaltentreu)
  "LOHNRELEVANT"            roh 15  -> code  0
  "Sebastian"               roh 213 -> code  4   (die 4 stehen in Strings)
  "function _stTagNetto"    roh  1  -> code  1
  "toFixed("                roh 17  -> code 17
  "React.createElement("    roh 7075 -> code 7071  (4 stecken in Kommentaren)
```

Die Köder deckten dabei genau die zwei Fallen ab, die im Repo schon zugeschnappt sind:
`accept:"image/*"` und `https://*.tile...` werden **nicht** als Kommentarbeginn gelesen (sie
stehen in Strings, der Automat weiß das), und ein Backtick im Kommentar schließt kein
Template-Literal. Ein erster Versuch **war kaputt**: ein Regex-Literal in einem
`${}`-Ausdruck (`.replace(/"/g,"")`, Zeile 20527) ließ den Automaten 138 904 Zeichen als
einen Template-String lesen — danach überlebten 383 Kommentare die Entfernung. Erst die
rekursive Fassung bringt das auf 35, und alle 35 sind **CSS-Kommentare in Stil-Template-Literalen**,
also echter String-Inhalt. Das ist die richtige Richtung: was übrig bleibt, fällt beim Lesen
auf; was zu viel gelöscht wird, wird still nie gemessen.

**2. Jeder Befund ist nachgerechnet, nicht angesehen.** Die Rechenstellen werden
**zeilenweise aus `index.html` geschnitten** und mit `node` ausgeführt — kein Nachbau. Die
Messskripte drucken zuerst den geschnittenen Quelltext (`GESCHNITTEN <zeile>: …`), damit
belegt ist, dass die gemessene Stelle die gemeinte ist. Jede Messung hat eine
**Gegenprobe**: einen Eingabefall, bei dem die Abweichung 0 sein muss.

**3. Zwei Schreibweisen.** Gezählt wurde `React.createElement(` (4 752 Zeilen) **und** die
Kurzform `h('…'` (685 Zeilen) — die Zulagen- und EZ-Ansichten sind komplett in der Kurzform
geschrieben und wären einem Sucher auf `React.createElement` entgangen.

**Umfang dieser Messung:** statisch am Quelltext plus Ausführung der geschnittenen Funktionen
in Node. **Nicht** gemessen: der laufende Browser, die echte Datenbank, und das tatsächliche
Verhalten von `<input type="number">` bei deutscher Komma-Eingabe je Browser/Gebietseinstellung
(siehe ⚪ P12).

---

# 🔴 Die Befunde

## 🔴 P1 — Das Wochen-Excel der Zeiterfassung rundet JEDE Zeile auf eine Nachkommastelle und summiert dann die gerundeten Zeilen: 50,40 h statt 50,52 h

**Stelle:** `index.html:25833` (Zeilenrundung) und `index.html:4949` (Gesamtzeile in `genXls`)

```js
// 25833
stunden:parseFloat(_n(e.hours,1).replace(",","."))||0
// 4949
if(ci===sumCol){const _sv=_n(rows.reduce((s,r)=>s+(parseFloat(r[ci])||0),0),2); …}
```

`_n(v,d)` ist `n.toFixed(d)` (`index.html:4776`). Der gebuchte Stundenwert hat **zwei**
Nachkommastellen (`addEntry` speichert `Math.round(h*100)/100`, `index.html:16145`/`25479`) —
der Export macht daraus **eine**, und die „Gesamt"-Zeile addiert diese gekürzten Werte.
Der Bildschirm derselben Ansicht addiert dagegen die ungekürzten Werte
(`weekTotal`, `index.html:25544`).

**Auslöser:** Mo–Sa jeweils `von 07:00`, `bis 16:25`, Pause `1h`. 16:25 liegt auf dem
5-Minuten-Raster, wird also von `_zeitRundBis` nicht verändert. Gebuchte Stunden je Tag: **8,42**.

**Falsch gegen richtig:**

| | |
|---|---|
| Bildschirm (`weekTotal`) | **50,52 h** (angezeigt als `50,5`) |
| Excel-Zeilen | 8,4 · 8,4 · 8,4 · 8,4 · 8,4 · 8,4 |
| Excel „Gesamt" | **50,40 h** |
| Differenz | **0,12 h = 7 Minuten je Woche** (≈ 30 min je Monat) |

**Folge für den Nutzer:** Das Büro exportiert dieses Blatt je Monteur und Kalenderwoche
(`Zeiterfassung_<Name>_KW<kw>_<jahr>.xls`, Dateiname `index.html:25861`); es ist die
Excel-Grundlage der Stundenabrechnung. Der Monteur hat 50,52 h gebucht, abgerechnet werden
50,40 h. Die Rundung geht in diesem Beispiel einseitig **zu seinen Lasten** — anders als die
5-Minuten-Rundung der Zeiten, die laut Kommentar (`index.html:2416`) bewusst so gewollt ist,
ist dieser Verlust nirgends beschlossen.

**Wie gemessen:** `mess_wochenexport.mjs` — schneidet `ZEIT_RASTER_MIN`/`_zeitParse`/`_zeitFmt`/
`_zeitEffektiveStunden`/`_zeitRundVon`/`_zeitRundBis` (2425–2472), `_n` (4776) und `_wrapHrs`
(5103) aus der Datei, zieht die beiden Rechenstellen als Text und führt sie aus:

```
ZEILENRUNDUNG (25833): stunden:parseFloat(_n(e.hours,1).replace(",","."))||0
GESAMTZEILE   (4949): _n(rows.reduce((s,r)=>s+(parseFloat(r[ci])||0),0),2)
GEBUCHTE STUNDEN je Tag: 8.42 · 8.42 · 8.42 · 8.42 · 8.42 · 8.42
BILDSCHIRM (Σ der Woche): 50.52 h
EXCEL "Gesamt"          : 50.40 h
DIFFERENZ               : 0.12 h = 7 Minuten
GEGENPROBE glatte 8h: Bildschirm 48 · Excel 48.00
```

Die Gegenprobe (glatte 8-Stunden-Tage) zeigt **0** Differenz — der Messfall trennt also, statt
immer etwas zu finden.

**Zum Vergleich, und das ist der Beleg dafür, dass es ein Fehler ist:** Derselbe Bericht als
*Bauwochenbericht* (`index.html:25781`/`25791`) rundet **zwei** Stellen, und der Kommentar dort
nennt genau diesen Grund: „*2 Nachkommastellen wie im Zwilling generateBWB — bei 1 Stelle
stimmten Viertelstunden-Buchungen (.25/.75) nicht mit den aus ungerundeten Werten summierten
Zeilen/Gesamt überein → unterschriebenes Kunden-/ÖBA-Dokument mit nicht aufgehenden Spalten*"
(v3.9.665). Die Kur wurde dort gemacht und hier **nicht**.

---

## 🔴 P2 — Die unterschriftsreife „Arbeitszeit-Bestätigung": die Tagesspalte addiert sich nicht zur gedruckten Wochensumme

**Stelle:** `index.html:25568` (Tageszelle) und `index.html:25613` (Wochensumme)

```js
// 25568, Tageszelle:
${dt>0?_n(dt,1):""}
// 25613, Wochensumme:
<td colspan="2" …>${_n(weekTotal,1)}</td>
```

`dt` ist `dayTotal(i)` (`index.html:25543`), `weekTotal` die Summe der **ungerundeten**
Tageswerte (`index.html:25544`). Gedruckt wird beides mit **einer** Nachkommastelle — die
Tageszellen also gekürzt, die Summe aus den vollen Werten.

**Auslöser:** dieselbe Woche wie P1 (sechs Tage 07:00–16:25, Pause 1 h, je 8,42 h).

**Falsch gegen richtig:**

| | |
|---|---|
| gedruckte Tagesspalte | 8,4 · 8,4 · 8,4 · 8,4 · 8,4 · 8,4 → Spaltensumme **50,40** |
| gedruckte Wochensumme | **50,5** |
| echte Wochensumme | 50,52 |

**Folge für den Nutzer:** Das Blatt heißt „Arbeitszeit - Bestätigung", trägt die
Unterschriftsfelder und geht an den Monteur zur Unterschrift (`exportWochenStz`,
`index.html:25555`). Er unterschreibt ein Dokument, dessen Spalte 50,40 ergibt, während der
Summenkasten 50,5 sagt — und dessen Tageswerte alle 1,2 Minuten unter der Buchung liegen.
Direkt darunter steht `diff = weekTotal − regelH` als „eventuelle Minderstunden": ein
Zahlenpaar, bei dem der Monteur nicht nachrechnen kann, welche der beiden Zahlen gilt.

**Wie gemessen:** `mess_stundenbestaetigung.mjs`, `dayTotal`/`weekTotal` wörtlich aus
25543/25544 geschnitten:

```
GESCHNITTEN 25543: const dayTotal=(off)=>{…reduce((s,e)=>s+(e.hours||0),0);};
GESCHNITTEN 25544: const weekTotal=DAYS.reduce((s,_,i)=>s+dayTotal(i),0);
Tagesspalte im unterschriebenen Blatt: 8.4 · 8.4 · 8.4 · 8.4 · 8.4 · 8.4
Summe der gedruckten Tageswerte     : 50.40
Gedruckte Wochensumme  _n(weekTotal,1): 50.5
Echte Wochensumme                    : 50.52
GEGENPROBE glatte 8h: Spalte 8.0 ×6 = 48 · gedruckte Summe 48.0
```

---

## 🔴 P3 — Die Arbeitsschein-Zeit läuft OHNE den 0–24-Stunden-Wächter in `time_entries`: 90 Stunden an einem Tag

**Stelle:** `index.html:11108` (INSERT) und `index.html:11134` (PATCH), in `_asZeitUebernahme`

```js
// 11108
await _sbPost("time_entries",{id:_eid,worker_id:s.monteur,project_id:"",arbeitsschein_id:s.id,
              date:_tag,hours:_h,taetigkeit:"Arbeitsschein "+(s.nummer||""),gewerk:"elektro"},true);
// 11134
await _sbPatch("time_entries",_cur.id,{hours:_h});
```

`_h` ist `_asUebernahmeStunden(s)` (`index.html:3762`) = `Math.round(((fz+st)/60)*100)/100`,
wobei `fz`/`st` Minuten aus den Feldern „Fahrzeit (hh:mm)" und „Arbeitszeit (hh:mm)"
(`index.html:11768`/`11769`) sind. Der Parser `window._hhmmToMin` (`index.html:875`) nimmt
`\d{1,3}:\d{1,2}` **und** eine nackte Zahl — **letztere als STUNDEN**.

**Es gibt in diesem Weg keinen Plausibilitäts-Wächter.** Gemessen an den Zeilen 11098–11136:
`grep -c "24"` = **0**. Alle anderen fünf Schreibwege nach `time_entries` haben ihn:

| Weg | Stelle | Wächter |
|---|---|---|
| manuelle Erfassung (Projektakte) | 16144 | `if(!(h>0&&h<=24)||isNaN(h))` ✔ |
| manuelle Erfassung (Wochenansicht) | 25482 | `if(!(h>0&&h<=24)||isNaN(h))` ✔ |
| Timer-Stop | 14815 | `if(!(r.hours>0&&r.hours<=24))` ✔ |
| Matrix-Zelle im Büro-Export | 13309 | `if(!isFinite(_h)||_h<0||_h>24)` ✔ |
| „Berichte bearbeiten" (Büro) | 13252 | `if(!Number.isFinite(_he)||_he<=0||_he>24)` ✔ |
| **Arbeitsschein-Zeit-Übernahme** | **11108 / 11134** | **keiner** |

Der Kommentar am manuellen Wächter sagt, warum er da ist: „*v3.8.49 Bug-Fix: Range-Validation
für Stunden 0<h<=24. Vorher akzeptierte h=25 oder h=NaN, resultierend in falschem
Payroll-Output und FinkZeit-Abgleich-Blindflug.*" Dieselbe Begründung gilt hier — nur steht
hier kein Wächter.

**Auslöser:** Der Monteur tippt in „Arbeitszeit (hh:mm)" **`90`** (gemeint: 90 Minuten) und
speichert den Schein.

**Falsch gegen richtig:**

| Eingabe | Feld zeigt nach Blur | `time_entries.hours` | richtig |
|---|---|---|---|
| `0:30` / `8:00` | 00:30 / 08:00 | **8.5** | 8,5 ✔ (Eichung) |
| `0:00` / `90` | 00:00 / **90:00** | **90** | 1,5 |
| `0:00` / `999:59` | 00:00 / 999:59 | **999.98** | — |
| `0:30` / `1,5` | 00:30 / **00:00** | **0.5** | 2,0 |

**Folge für den Nutzer:** Der Eintrag heißt „Arbeitsschein &lt;Nr&gt;" und landet ohne
Projektbezug in `time_entries`. Von dort geht er in **alle** Auswertungen: den
Bauwochenbericht (Kunde/ÖBA unterschreibt), die Wochen-Stundenbestätigung, das
Zeiterfassungs-Excel, die PZE-Projektzeit-Spalte (`_projStd`, `index.html:12349`) und — weil
`_ezDayEff` nur „mehr als 6 Stunden" prüft (`index.html:11943`) — in die Entfernungszulage,
also **Geld**. Ein 90-Stunden-Tag fällt in der Monatssumme auf; ein Tag mit `25` statt `2:30`
tut das nicht.

Mildernd: das Feld zeigt nach dem Verlassen `90:00`, und das Feld „Gesamtzeit" daneben zeigt
es ebenfalls. Der Fehler ist also sichtbar, wenn man hinsieht — aber er wird nicht
abgewiesen, und die anderen fünf Wege weisen ihn ab.

**Wie gemessen:** `mess_as_zeit.mjs` — `window._hhmmToMin` (875), `window._minToHhmm` (874)
und `_asUebernahmeStunden` (3762) geschnitten und ausgeführt. Eichung
`_hhmmToMin("1:30")=90`, `_hhmmToMin("8:00")=480`. Wächter-Gegenprobe:
`awk 'NR>=11098 && NR<=11136' index.html | grep -c "24"` → `0`.

---

## 🔴 P4 — Ein Urlaubsanspruch von 0 Stunden lässt sich nicht eintragen und wird als 192,5 h angezeigt

**Stelle:** `index.html:22833` (Eingabefeld), `index.html:22461` (DB-Lesepfad),
`index.html:22401`/`22617`/`22755` (Rechnung, Anzeige, Excel)

```js
// 22833, Eingabefeld "Anspruch h"
onChange: e=>setKontingent(p=>({...p,[m]:{...ks,stunden:parseFloat(e.target.value)||192.5}}))
// 22461, Lesen aus urlaubskontingent
stunden:parseFloat(k.stunden)||192.5
// 22401
function _resturlaubK(…){const ks=…;return (ks.stunden||192.5)+(ks.vorjahr||0)-ys.urlaubStdGen-(ys.urlaubStdAusstehend||0);}
```

`parseFloat("0")` ist `0`, und `0` ist falsy — `||192.5` ersetzt es. Die 0 hat in diesem Feld
**keinen Ausdruck**. Dasselbe Muster steht fünfmal: im Eingabefeld, im DB-Lesepfad, in
`_resturlaubK`, in der Bildschirmtabelle (`22829`, `22798`) und im Excel (`22755`).

**Auslöser:** Das Büro trägt für eine Ferialkraft / einen Lehrling im ersten Jahr
„Anspruch h = 0" ein — oder der Wert steht in `urlaubskontingent.stunden` schon auf 0.

**Falsch gegen richtig:**

| getippt | gespeichert |
|---|---|
| `150` | 150 ✔ (Eichung) |
| `192.5` | 192.5 ✔ (Eichung) |
| **`0`** | **192.5** |
| **`0.0`** | **192.5** |
| **`""`** (Feld leeren) | **192.5** |

| DB-Wert | App liest |
|---|---|
| 100 | 100 ✔ |
| **0** | **192.5** |

Und damit:

| | |
|---|---|
| Resturlaub bei Anspruch 0 h, nichts genommen | **192,5 h** |
| richtig | **0 h** |

**Folge für den Nutzer:** Der Mitarbeiter sieht in seiner Kontingent-Zeile 192,5 h Anspruch
und 192,5 h Rest, das Büro sieht es in der Kontingent-Tabelle und in
`Kontingent_<jahr>.xls`, dessen „Gesamt"-Zeile (`sumCol:9`, Spalte „Rest h") die 192,5
mitsummiert. Es gibt keinen Weg, das zu korrigieren: jede Eingabe von 0 wird sofort wieder zu
192,5. Zweiter, sicher erreichbarer Teil desselben Defekts: **das Feld lässt sich nicht
leeren** — beim Löschen des Inhalts springt sofort 192,5 hinein, weil `parseFloat("")` `NaN`
ist. Wer also 100 eintragen will, muss den Cursor in „192.5" setzen und darin editieren.

Die Nachbarfelder machen es richtig: `vorjahr:parseFloat(…)||0` und
`ueberstunden:parseFloat(…)||0` haben als Ersatzwert die 0 und sind darum unschädlich. Nur
`stunden` (192,5) und `woche` (38,5) tragen einen Ersatzwert, der ungleich 0 ist.

**Wie gemessen:** `mess_urlaub_und_verbrauch.mjs`, Teil A — `_wocheOfK` (22396),
`_stdVonTagK` (22397), `_resolveApprK` (22398), `_yearStK` (22399–22400) und `_resturlaubK`
(22401) wörtlich geschnitten; `_isATFeiertag` als `false` gesetzt (spielt für diesen Fall
keine Rolle, es gibt keine Abwesenheiten). Eichungen: Anspruch 192,5 → Rest 192,5;
Anspruch 100 → Rest 100.

---

# 🟡 Falsch, aber folgenlos oder sichtbar

## 🟡 P5 — Eine Tankung ohne km-Stand macht aus 8,0 L/100 km eine 0,1

**Stelle:** `index.html:29013` (Ø Verbrauch) und `index.html:29023` (Monatsauswertung)

```js
const sorted=[...(selFz.tankLog||[])].sort((a,b)=>a.km-b.km);
if(sorted.length<2)return"—";
const diff=sorted[sorted.length-1].km-sorted[0].km;
const lit=sorted.slice(1).reduce((s,t)=>s+t.liter,0);
return diff>0?_n((lit/diff*100),1)+" L/100km":"—";
```

Die Division ist gegen 0 geschützt (`diff>0`) — der Fehler ist ein **anderer**: das Feld
„km-Stand" im Tankbeleg-Dialog ist **optional** (`index.html:5984`, kein Pflicht-Stern;
`validateAndCollect` setzt `K=0`, wenn es leer bleibt, `index.html:6018`), und `addTank`
speichert `km:_r.km` unverändert (`index.html:28128`). Eine Tankung mit `km:0` sortiert sich
an den Anfang, wird zu `sorted[0]`, und `diff` ist dann der **ganze Tachostand** statt der
gefahrenen Strecke.

**Auslöser:** drei Tankungen, bei der mittleren wurde das km-Feld leer gelassen:
`km 120000 / 50 L`, `km — / 48 L`, `km 121250 / 52 L`.

**Falsch gegen richtig:**

| | |
|---|---|
| App zeigt | **0,1 L/100km** |
| richtig (100 L auf 1 250 km) | **8,0 L/100km** |
| Eichung: alle drei mit km-Stand | 8,0 L/100km ✔ |

**Folge für den Nutzer:** Der Fuhrpark-Verantwortliche sieht „Ø Verbrauch: 0,1 L/100km" beim
Fahrzeug und in der Monatsauswertung-Tabelle (die über `minKm:Infinity` /
`if(t.km<byMonth[m].minKm)` denselben Nullwert einsammelt, `index.html:29020`) samt
Verbrauchs-Ampel. Eine 0,1 ist so offensichtlich unmöglich, dass niemand sie für echt hält —
darum 🟡 und nicht 🔴. Kein Lohn und keine Rechnung hängen daran. Der Sachbezug wird hieraus
**nicht** gerechnet.

**Wie gemessen:** `mess_urlaub_und_verbrauch.mjs`, Teil B — der IIFE-Rumpf aus 29013 wörtlich
geschnitten und mit beiden Datensätzen ausgeführt.

---

## 🟡 P6 — Die SUMME-Zeile des Preisvergleichs zeigt `0.30000000000000004`

**Stelle:** `index.html:20803`

```js
React.createElement('td', {…}, activePos.reduce((s,p2)=>s+(p2.menge||0),0))
```

Die einzige Stelle in der Datei, an der eine Fließkomma-Summe **ohne jeden Formatierer** als
React-Kind gerendert wird. Gemessen mit einem Sucher auf `}}, X.reduce((…),0)` über die
kommentarfreie Fassung: **1 Treffer**, und der Sucher findet diesen bekannten Fall (Eichung).
Die Menge selbst wird korrekt mit Komma-Ersatz eingelesen (`index.html:20773`:
`parseFloat(String(e.target.value).replace(",","."))`, `step:"any"`), ist also beliebig
dezimal.

**Auslöser:** zwei Positionen mit Menge `0,1` und `0,2` (plausibel bei Einheit m oder kg).

**Falsch gegen richtig:**

| | |
|---|---|
| angezeigt | `0.30000000000000004` |
| richtig | `0,3` |
| Eichung: Mengen 2 + 3 | `5` ✔ |

**Folge für den Nutzer:** Leo/das Büro sieht in der Summenzeile des Preisvergleich-Dialogs
eine 17-stellige Zahl. Kein Geldbetrag hängt daran (die Geldspalten laufen alle durch
`fmt$`), die Bestellmenge je Position ist daneben korrekt — es ist eine unlesbare Anzeige,
keine falsche Bestellung. Zusätzlich fällt die Zahl auf, statt zu täuschen.

**Wie gemessen:** `mess_rest.mjs`, Teil 4 — Ausdruck aus 20803 geschnitten und ausgeführt.

---

## 🟡 P7 — Im selben Dialog schreibt „neue Zeile" gerundet und „Zeile geändert" ungerundet; der Bauwochenbericht geht dadurch um 0,01 h nicht auf

**Stelle:** `index.html:13236` (POST) gegen `index.html:13253` (PUT), beide in
`editMonteurEntries`

```js
// 13236, neue Zeile:
const _h=Math.round((parseFloat(r.stunden)||0)*100)/100;
// 13253, bestehende Zeile:
SQ.push({url:"/api/entries/"+r.id,method:"PUT",body:{date:r.datum,taetigkeit:r.taetigkeit,hours:r.stunden,bemerkung:r.bemerkung}});
```

Der Kommentar am POST-Zweig nennt den Grund für die Rundung ausdrücklich: „*v3.9.383: auf 2
Dezimal runden wie Add-Entry-Pfad → kein Zell-/Summen-Drift (7,333 → 7,33)*". Der PUT-Zweig
zwei Zeilen weiter hat sie nicht. Das Eingabefeld ist `type:"number", step:"0.5"` — ein
Schrittverstoß macht das Feld nur ungültig, der Wert kommt trotzdem durch.

**Auslöser:** Büro tippt `7.3333` in die Stundenspalte einer **bestehenden** Zeile; drei
solche Tage im Bauwochenbericht.

**Falsch gegen richtig:**

| Wert in der DB | gedruckte Tageszellen (`_n(h,2)`, 25781) | Summe der gedruckten Zellen | gedruckte Spaltensumme (`_n(t,2)`, 25791) |
|---|---|---|---|
| 7,3333 (PUT) | 7,33 · 7,33 · 7,33 | **21,99** | **22,00** |
| 7,33 (POST) | 7,33 · 7,33 · 7,33 | 21,99 | 21,99 ✔ |

**Folge für den Nutzer:** Der Bauwochenbericht wird von Kunde/ÖBA unterschrieben und trägt
den Satz „*Gegen diesen Bauwochenbericht kann innerhalb von 48 Stunden Berufung eingelegt
werden*" (`index.html:25813`). Eine Spalte, die um 0,01 h nicht aufgeht, ist auf so einem
Blatt ärgerlich, aber niemandes Geld: 0,01 h = 36 Sekunden. Die Größenordnung macht es 🟡 —
die Fehlerform ist dieselbe wie P1/P2 und wurde in v3.9.665 für den POST-Weg schon einmal
kuriert.

**Wie gemessen:** `mess_rest.mjs`, Teile 2 und 3.

---

## 🟡 P8 — Ein geleertes Stundenfeld im Export-Vorschau-Dialog wird stillschweigend 0,0

**Stelle:** `index.html:6184` (Dialog) und `index.html:4776` (`_n`)

```js
// 6184, im Review-Modal
if(col.type==='number'){const n=parseFloat(raw);r[col.key]=isNaN(n)?(raw===''?'':raw):n;}
// 4776
function _n(v,d){const n=parseFloat(v);return (isNaN(n)||!isFinite(n))?(d!==undefined?(0).toFixed(d):0):…}
```

Ein leeres Zahlenfeld wird zu `''`, und `_n('',1)` ist `"0.0"` — nicht „leer", nicht „—",
sondern eine gedruckte Null.

**Falsch gegen richtig (gemessen):**

| `v` | `_n(v,1)` |
|---|---|
| `"8.5"` | `"8.5"` ✔ |
| `""` | `"0.0"` |
| `"  "` | `"0.0"` |
| `"abc"` | `"0.0"` |
| `"8,5"` | `"8.0"` ← siehe ⚪ P12 |

**Folge für den Nutzer:** Löscht das Büro in der Vorschau versehentlich die Stundenzahl einer
Zeile (statt die Zeile mit ✕ zu entfernen), steht im Excel „0,0" — als hätte der Monteur an
diesem Tag nichts gearbeitet — und die „Gesamt"-Zeile sinkt entsprechend, ohne Hinweis.
Es ist eine Fehleingabe mit sichtbarer Folge im exportierten Blatt, darum 🟡. Die
DB-schreibenden Aufrufer desselben Dialogs (`editMonteurEntries`, `openMultiEntryEdit`) sind
dagegen geschützt und **melden** die übersprungene Zeile (`index.html:13268`).

**Wie gemessen:** `mess_rest.mjs`, Teil 1 — `_n` aus 4776 geschnitten.

---

# ⚪ Nicht zu Ende gemessen

## ⚪ P9 — `_sbGet` kappt JEDE Abfrage stumm bei 5 000 Zeilen, ohne Sortierung

`index.html:2152`:

```js
const parts=[hasSelect?"":"select=*",filter||"","limit=5000"].filter(Boolean);
```

`index.html:12957` ruft `_sbGet("time_entries")` **ohne Filter und ohne `order=`** auf und
füttert daraus den ganzen Büro-Export (Bauwochenbericht, Monteur-Statistik,
Berichte-Bearbeiten). Jenseits von 5 000 Zeilen liefert PostgREST eine beliebige Teilmenge —
ohne `ORDER BY` nicht einmal „die neuesten" —, und der Erfolgstoast meldet
`(te||[]).length`, also „✅ 5000 Zeit, …": ein Deckel, der wie ein Ergebnis aussieht.
Dieselbe Kappung trifft `_sbGet("bautagebuch")`, `_sbGet("defects")` und die Zählung in
`index.html:13771`.

**Warum ⚪:** Der Auslöser ist nicht belegt. Die jüngste Zeilenzahl, die im Repo steht, ist
`docs/handoffs/HANDOFF_2026-08-25.md:168`: „*time_entries 117, absences 158, arbeitsscheine
151*". Bei 117 Zeilen ist der Deckel heute **weit** entfernt — es ist eine schlafende
Fehlerquelle, kein aktueller Rechenfehler. Zu Ende messen heißt: `select=id` mit
`Prefer: count=exact` gegen die echte DB und die Wachstumsrate je Monat. Das war hier nicht
möglich (nur Lesen am Quelltext).

## ⚪ P10 — Der DATANORM-Preis wird sowohl auf Komma geprüft ALS AUCH durch 100 geteilt

`index.html:18621` und `18642`:

```js
preis=parseFloat((parts[9]||"0").replace(",","."))||0;
…
const unitPreis=preis>0?(preis/100)/(pe||1):0;
```

Das `.replace(",",".")` erwartet ein **Dezimalkomma** im Preisfeld; das `/100` erwartet
**Cent als Ganzzahl** („*Price: DATANORM stores in cents → divide by 100*"). Beides zugleich
kann nicht richtig sein. Kommt eine Lieferantendatei mit `12,50` im Preisfeld, wird daraus
`0,125 €` — ein Faktor 100 im Einkaufspreisvergleich. Dieselbe Doppelung steht in
`18603`/`18669`/`18670`/`18701`.

**Warum ⚪:** Ohne eine echte DATANORM-Datei (`.001`/`.dat`) eines der Händler ist nicht
entscheidbar, welche der beiden Annahmen der Bestand tatsächlich trifft. Im Repo liegt keine.
Zu Ende messen heißt: eine echte Datei durch `_parseDatanorm` schicken und den Ausgabepreis
gegen die Händler-Preisliste halten.

## ⚪ P11 — Ein Einkaufspreis von genau 0 fällt auf den Listenpreis zurück

`index.html:20069`:

```js
ek:parseFloat(sa.ek_preis)||parseFloat(sa.listenpreis)||0
```

Dieselbe falsy-Falle wie P4: ein `ek_preis` von 0 (Zugabe, im Paketpreis enthalten) wird zum
**Listenpreis** und geht so in `effEk`, in `bestSupplier` und in alle Spaltensummen des
Preisvergleichs. **Warum ⚪:** ob in `supplier_articles` überhaupt Zeilen mit `ek_preis = 0`
(und nicht NULL) stehen, ist nicht gemessen — dafür braucht es die DB.

## ⚪ P12 — Deutsches Komma in `<input type="number">`

`_n("8,5",1)` ergibt `"8.0"` (gemessen, siehe P8), und der Zahlen-Parser des
Vorschau-Dialogs (`index.html:6184`) würde `"8,5"` zu `8` machen, weil `parseFloat("8,5")`
`8` ist und damit **nicht** `NaN` — kein Wächter schlägt an.

**Warum ⚪:** Ob ein Komma dort je ankommt, hängt am Browser: eine lokalisierte Engine
normalisiert `8,5` zu `"8.5"`, eine nicht lokalisierte gibt `""` zurück (dann greift P8, also
0,0). Beides ist am Quelltext nicht entscheidbar. Zu Ende messen heißt: in Chrome/WebKit mit
`de-AT` **und** mit `en-US` „8,5" in das Feld tippen und `inp.value` lesen. Die Felder mit
`type:"text"` habe ich dagegen geprüft: von den 2 Zahleneingaben ohne `type="number"`
(`index.html:11769` Arbeitszeit hh:mm, `index.html:11790` AS-Materialmenge) geht **keine** in
eine Geldrechnung — die Materialmenge wird nur als Text ins Arbeitsschein-PDF gedruckt
(`index.html:11344`).

---

# ✅ Nachgesehen und in Ordnung — bitte nicht zweimal prüfen

Alles hier ist **gemessen**, nicht überflogen. Wo eine Null das Ergebnis ist, steht dabei,
womit der Sucher geeicht wurde.

1. **19 der 23 Prozentrechnungen haben einen Nullwächter, die übrigen 4 sind Balkenbreiten.** Sucher über die kommentarfreie
   Fassung, geeicht mit 4 Ködern (`Math.round(a/b*100)`, `100*c/d`, `done / tot * 100`,
   `usedMin/norm*100`) und 2 Gegenproben. 23 Treffer, davon 19 mit explizitem
   `tot?`/`>0?`-Guard und 4 ungeschützte Balkenbreiten in CSS (`width:(x/max*100)+"%"`), bei denen ein NaN
   nur eine ungültige CSS-Regel ergibt, keine Zahl.

2. **`_n` wird nirgends mit nur einem Argument aufgerufen.** `_n(v)` ohne Stellenzahl würde
   die rohe Fließkommazahl zurückgeben. Sucher mit Klammertiefen-Zählung, geeicht an
   `_n(x)` / `_n(f(p,q))` (müssen treffen) und `_n(y,2)` (darf nicht treffen): **0 Treffer**
   im Bestand.

3. **Die 6-Stunden-Schwelle der Entfernungszulage kippt nicht durch Fließkomma.**
   `_ezDayEff` (`index.html:11943`) prüft `(parseFloat(std)||0)>6`, und die Tagessumme wird
   in `index.html:12223` fließend aufaddiert. Über **alle** Stundenwerte, die die App
   erzeugen kann (96 Rasterwerte `Math.round(k·5/60·100)/100`), gesucht nach Kombinationen
   mit Dezimalsumme genau 6,00 und Fließkommasumme > 6: **0 von 96² (zwei Buchungen) und
   0 von 96³ (drei Buchungen)**. Zur Gegenprobe: mit *beliebigen* Zwei-Dezimal-Werten gibt
   es 7 196 solche Tripel (z. B. `0,03 + 4,11 + 1,86 = 6.000000000000001` → „klein"), der
   Sucher ist also nicht blind — diese Werte sind aus dem 5-Minuten-Raster nur nicht
   erreichbar. Eichung von `_ezDayEff`: 6,5 → „klein"; 6 → „"; 5,9 → „".

4. **Die Zeile des Abwesenheits-Excel geht auf.** `index.html:22618` rundet Kontingent,
   Verbraucht und Rest **einzeln** auf eine Nachkommastelle — trotzdem gilt
   `rund(K) − rund(V) = rund(R)`: 0 Abweichungen über 11 Teilzeit-Wochenstundenwerte ×
   25 Urlaubstage (275 Fälle). Grund: das Kontingent selbst hat genau eine Nachkommastelle.
   Eichung: `_stdVonTagK` Mo = 8,5 / Fr = 4,5 bei Vollzeit.

5. **Bauwochenbericht: zwei Nachkommastellen, verlustfrei** für alle Werte, die die App
   selbst erzeugt (2 Dezimalstellen). `index.html:25781`/`25791` und der Zwilling in
   `index.html:16287`. Nur handeingetragene Werte mit mehr Stellen
   brechen es (P7).

6. **Stempeluhr und PZE rechnen in ganzen Minuten, ohne Doppelrundung.** `_stTagNetto`
   (2371) summiert gerundete Paare (Kommen auf, Gehen ab, 5-Minuten-Raster) und zieht den
   Pausenabzug **einmal je Tag**, nie negativ; `_pzeTagRow` (5053) leitet die angezeigte
   Pause aus `brutto − netto` ab, zeigt also, was tatsächlich abgezogen wurde; `_pzeSummen`
   (5080) addiert Minuten-Ganzzahlen. Kein `toFixed` im Rechenpfad.

7. **Die Zulagensatz-Maske behandelt das deutsche Komma.** `_ezRateSave`
   (`index.html:12252`): `String(x).replace(',','.')` + `parseFloat` + `isNaN`-Abweisung mit
   Toast. Ebenso `_kvLoadRules` (`index.html:2508`), das **jedes** numerische Feld gegen den
   Fallback Number-coerct und bei NaN den Fallback behält.

8. **`_parseHr` (Matrix-Zelle im Büro-Export, `index.html:13286`)** behandelt Komma und
   NaN: `String(v).replace(",",".").trim()` → `parseFloat` → `isFinite && >=0 ? n : NaN`,
   und der Aufrufer weist `NaN`/`<0`/`>24` mit Toast ab.

9. **5 von 6 Schreibwegen nach `time_entries` haben den 0–24-Stunden-Wächter** (Tabelle in
   P3). Der sechste ist der Befund.

10. **`editMonteurEntries` verschweigt keine übersprungene Zeile.** `index.html:13265`/`13269`
    melden `_skipNote` und `_skipEdit` **zusätzlich** zum Erfolgstoast, nicht als
    `else if` — ein gemischter Lauf (teils gespeichert, teils abgewiesen) zeigt beides.

11. **Fahrtenbuch-Speichern ist vollständig validiert.** `index.html:24934`: `parseInt(…,10)`
    **mit Basis**, `isNaN`-Abweisung, `<0`-Abweisung, `km_ende<=km_start`-Abweisung, und
    Liter/Preis mit `String(x).replace(",",".")`. Die Summen `totalKm`/`totalKraftstoff`
    (`index.html:24968`/`24969`) rechnen aus den Daten, nicht aus der Anzeige.

12. **`_fbSummen` (Flotte, `index.html:26485`)** filtert `isFinite(k)&&k>0` und rundet die
    km-Summe **nach** dem Aufaddieren (`Math.round(km*100)/100`) — die richtige Reihenfolge.

13. **Der Tankbeleg-Dialog validiert streng.** `index.html:6016`: der Preis muss
    `^[0-9]+([.,][0-9]{1,2})?$` erfüllen, der km-Stand `^[0-9]+$`, sonst rote Meldung und
    Fokus aufs Feld; der Literpreis wird als `(P/L).toFixed(3)` erst gezeigt, wenn beide
    Werte > 0 sind.

14. **Es gibt in dieser App keine Mehrwertsteuer-Rechnung.** Geeichter Sucher (`mwst`, `ust`,
    `umsatzsteuer`, `netto`, `brutto`, `steuersatz`, `vat`, `*1.2`, `0.2`) über die
    **kommentarfreie** Fassung: kein einziger Treffer ist eine Steuerrechnung. Die Treffer
    auf `netto`/`brutto` sind ausnahmslos **Arbeitszeit**-Begriffe (`_stTagNetto`,
    `bruttoStd`, `nettoMin`), die 141 Treffer in Zeile 3113 sind die
    `APP_VERSION`-Changelogprosa, und `Zahlung: 8 Tage netto` (`index.html:4968`) ist ein
    Fußzeilentext. Die App führt Einkaufspreise und Budgets, keine Ausgangsrechnungen.

15. **Die „Gesamt"-Zeile von `genXls` ist strukturell richtig.** `index.html:4946`–`4950`:
    `colspan=sumCol` + eine Summenzelle + Leerzellen für die Spalten dahinter ergibt genau
    `headers.length` Zellen (geprüft für den 11-spaltigen Kontingent-Export mit `sumCol:9`).
    Excel bekommt die Zahl über `x:num` mit **Punkt** und sieht sie mit **Komma**
    (`_xAttr`/`_xText`, `index.html:4890`/`4891`). Die Summe entspricht der Summe der
    **angezeigten** Spalte — das ist für eine Spaltensumme das Richtige; der Fehler in P1
    liegt darin, dass die Spalte selbst gekürzt ist, nicht in der Summenzeile.

16. **Die Median-Rechnung der Dispo** (`_dispoMedianJeKlasse` `index.html:5253`,
    `_dispoMedianJeTyp` `index.html:5267`) behandelt gerade Anzahlen korrekt
    (`Math.round((a[n/2-1]+a[n/2])/2)`) und sortiert vorher numerisch.

17. **`parseInt` ohne Basis: 76 Stellen, alle harmlos.** Vollständig aufgelistet und
    durchgesehen. In ES2015+ liest `parseInt` ohne Radix nur `0x`-Präfixe als Hex und **kein**
    Oktal mehr; keine der 76 Stellen kann einen `0x`-Wert bekommen (es sind Zeitstempel,
    Zähler, Datums-Teilstücke, `e.target.value` von `type=number`-Feldern und
    `content-range`-Kopfzeilen).

---

## Was in diesem Lauf NICHT gemessen werden konnte

* **Der laufende Browser.** Alle Befunde sind am Quelltext und an ausgeführten Schnitten
  gemessen, nicht am gerenderten DOM. Für P1/P2/P7 wäre eine Bestätigung am Schirm: eine
  Woche mit `07:00–16:25` und 1 h Pause buchen, dann Excel und Bestätigung öffnen und die
  Zellen vergleichen.
* **Die Datenbank.** P9, P10 und P11 hängen jeweils an einer Zahl, die nur die DB (oder eine
  echte DATANORM-Datei) hergibt.
* **Die Gebietseinstellung des Browsers** (P12).
* **Zeit- und Datumsarithmetik** — die liegt im Nachbarbericht
  `docs/befunde/bughunt/zeit.md` (Z1–Z11) und wurde hier bewusst nicht doppelt gemessen.
  Überschneidungen: keine. `zeit.md` behandelt Kalenderwochen, DST, Übernacht-Schichten und
  den Pausenabzug am Kurztag; dieser Bericht behandelt Rundung, Summen und Wertebereiche.

## Messskripte

Liegen im Sitzungs-Ablagefach (nicht im Repo), damit der Baum unberührt bleibt:

| Datei | prüft |
|---|---|
| `nurcode.py` + `eich.py` | kommentarfreie, zeilentreue Fassung + 16 Köder |
| `suche.py` | Mustersuchen mit Eichung je Muster |
| `mess_wochenexport.mjs` | P1 |
| `mess_stundenbestaetigung.mjs` | P2 |
| `mess_as_zeit.mjs` | P3 |
| `mess_urlaub_und_verbrauch.mjs` | P4, P5 |
| `mess_rest.mjs` | P6, P7, P8 |
| `mess_ez_schwelle.mjs`, `raster.mjs`, `drei.mjs` | ✅ Punkt 3 |
| `abs_export.mjs` | ✅ Punkt 4 |
