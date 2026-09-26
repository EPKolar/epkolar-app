# WeekPlan (56 Stellen) und die users-Frage (Befund E1) — gemessen, nicht geraten

**Auftrag dieses Laufs:** messen und beschreiben. **Gebaut wurde nichts.**
`index.html` ist **nicht angefasst** (kein Edit, kein Write — nur Lesen und
Schneiden). An der Datenbank lief **ausschliesslich GET** — kein INSERT/UPDATE/
DELETE, kein DDL, keine Migration. **Kein Browser, kein Playwright.** Keine
bestehende Pruefung geaendert, kein `git add/commit/push/stash`.

**Angelegt von diesem Lauf:** nur diese Datei.

## 0. Messgrundlage

| Was | Stand |
|---|---|
| `index.html` bei der Erstmessung | 3 660 051 Zeichen, md5 `359be144407d9b033949cbeccd866892` |
| `index.html` bei der Gegenmessung am Ende | 3 660 751 Zeichen, md5 `f5b6b8b97c5c4510cf11f8f4ce978c36` |
| `APP_VERSION` | `3.9.954-supabase` (beide Staende) |
| Abtaster | `scripts/code_scan.py`, **Eichung bestanden** — 22 von 22 (erste Messung), 21 von 21 (Gegenmessung) |
| Ziel-DB | `jiggujpruejkaomgxarp.supabase.co`, JWT-Rolle `anon` aus dem ausgelieferten Buendel |
| Messdatum | 26.09.2026 |

**Die Datei ist mir waehrend des Laufs unter den Haenden gewachsen** (ein
zweiter Lauf schreibt in `index.html`; die Eichgrundgesamtheit fiel dabei von
22 auf 21 `isMob`-Deklarationen). Die **Zahl 56 ist in beiden Staenden
identisch**. Verlasst euch auf die **Ankertexte**, nicht auf die
Zeichenpositionen und nicht auf die Zeilennummern.

Kennzeichnung durchgehend: **GEMESSEN (Code)** = mit `code_scan` im Quelltext
gelesen · **GEMESSEN (DB)** = echte Anfrage gegen die laufende Datenbank ·
**AUS DATEI** = steht in einer Repo-Datei, sagt nichts ueber live ·
**SCHLUSS** = Folgerung · **NICHT GEMESSEN** = offen und benannt.

---

# TEIL 1 — WeekPlan

## 1.1 Die Abgrenzung — GEMESSEN (Code)

Abgrenzung an der **naechsten Funktionsdeklaration**, wie in
`tests/test_b6_stufe3_v944.py`, **nicht** ueber eine Klammerzaehlung.

| | |
|---|---|
| Funktionsdeklarationen im CODE (Grundgesamtheit) | **464** (Koeder: die Zaehlung fordert > 300) |
| `WeekPlan` | von `function WeekPlan(` bis zur naechsten Deklaration `_wocheOfK` |
| Rumpfgroesse | **113 154 Zeichen = 110,5 kB** — im erwarteten Band (88–160 kB), also **keine davongelaufene Abgrenzung** |
| Vergleich | `ArbeitsscheinView` 158 043 Zeichen, `HomeView` 88 741 Zeichen |

**Nebenbefund (Code):** `WerkzeugView` ist die **letzte** Funktionsdeklaration
der Datei — eine Abgrenzung „bis zur naechsten Deklaration" laeuft dort in
einen `IndexError`, wenn man den Fall nicht abfaengt. Genau das hat mein
erstes Skript getan. In `test_b6_stufe3_v944.py` ist der Fall mit
`decl[k+1] if k+1 < len(decl) else len(roh)` abgedeckt; wer die Abgrenzung
nachbaut, muss das mitnehmen.

## 1.2 Es sind genau 56 — und sie bestehen aus ZWEI Familien

**GEMESSEN (Code).** Alle 124 `fontSize`-Angaben im CODE-Teil von `WeekPlan`
eingesammelt und nach Form sortiert (nicht nach einem vorgefassten Muster):

| Familie | Anzahl |
|---|---|
| **A** nackte Zahl < 12 (`fontSize:11`, `:10`, `:9`, `:9.5`, `:10.5`) | **51** |
| **C** `isMob?<gross>:<klein>` — die Schreibtisch-Zahl unter 12 (v3.9.947-Familie) | **5** |
| B `isMob?<klein>:<gross>` | 0 |
| D andere Bedingung mit einer Zahl unter 12 | 0 |
| — | |
| **Summe unter 12 px** | **56** |
| Rest: Angaben ab 12 px | 66 |
| Rest: `fontSize:UI.fMeta` (= 12, schon gehoben) | 2 |
| **Gesamt** | **124** |

Aufschluesselung von A: `11` 22× · `10` 15× · `9` 11× · `9.5` 2× · `10.5` 1×.

**Wichtig fuer jeden, der die 56 nachzaehlt:** das Muster aus
`test_b6_stufe3_v944.py`
(`fontSize:(?:isMob\?(?:9|10|11):\d+|(?:9|10|11)(?![\d.]))`) findet in
`WeekPlan` nur **48** davon. Die Differenz ist sauber erklaerbar und kein
Widerspruch:

* **+5** die v3.9.947-Familie (`isMob?12:9`, `isMob?12:10`, `isMob?13:11`,
  `isMob?12:11`) — sie kam in der Grundgesamtheit des v944-Musters
  ueberhaupt nicht vor. Das ist wortgleich die Fehlerform, die der Kommentar
  an `const UI={` fuer v3.9.947 selbst festhaelt.
* **+3** die Dezimalgroessen `9.5` (2×) und `10.5` (1×) — vom v944-Muster
  **absichtlich** ausgeschlossen (`(?![\d.])`, weil ein zu weites Muster
  `fontSize:9.5` schon einmal zerschnitten hat).

**Koeder zur Zaehlung:** dasselbe Verfahren findet in `ArbeitsscheinView`
**0** und in `HomeView` **0** Stellen des v944-Musters — die Zaehlung kann
also sowohl finden als auch nicht finden.

## 1.3 Wo die 56 sitzen — GEMESSEN (Code)

Blockgrenzen aus den benachbarten Ankern gelesen; Summe geht restlos auf
(56, kein Rest).

| Anzahl | Zeilen | Block | Groessen |
|---|---|---|---|
| **10** | 21809–21875 | Zellen-Auswahlfenster (Mehrtags-Auswahl MA + Spezialfahrzeuge) | 10, 11, `isMob?12:9`, 10, 11, `isMob?12:9`, 10, 9, 11, 11 |
| 4 | 21915–21932 | Wochenkopf: KW-Navigation, Speicherstand, Ansichtshinweis | `isMob?12:10`, `isMob?13:11`, 11, 11 |
| 1 | 21957 | Excel-Knopf | 11 |
| 5 | 21999–22024 | Mobil: Tagesstreifen + MA-Tageskarten | 9, 11, 9.5, 9.5, 10.5 |
| 4 | 22036–22045 | Tabelle „MA-Uebersicht" (`minWidth:700`, `tableLayout:fixed`) | 11, 11, 11, 10 |
| 4 | 22063–22072 | Projekt-Chipzeile | 11, 11, 11, 11 |
| 4 | 22097–22109 | Abwesenheitsstreifen `_absRow` (`minWidth:800`) | 11, 11, 11, 10 |
| 4 | 22133–22140 | Mobil: Tagesansicht + Zellen-Blatt | 9, 10, 9, 9 |
| 3 | 22159–22166 | Spezialfahrzeuge (Kopf) | 11, 10, 11 |
| 3 | 22187–22189 | Spezialfahrzeug-Streifen (`minWidth:800`) | 10, 10, 10 |
| 2 | 22207–22208 | Wetterstreifen (`minWidth:800`) | 9, 10 |
| **10** | 22273–22300 | Haupttabelle: Zeilen bearbeiten, Pfeil-/Loeschknoepfe | 10, 10, 10, 11, 9, 9, 9, 9, 9, 10 |
| 2 | 22310–22317 | Fusszeile (Drucken, Hinweis) | 11, `isMob?12:11` |

Die **10 im Zellen-Auswahlfenster** und die **10 in der Zeilenbearbeitung**
sind die zwei dichtesten Nester. Beide sind Bedienelemente, nicht Zierde: in
der Zeilenbearbeitung stehen vier **Aktionsknoepfe** auf `fontSize:9`
(`title:"Hoch"`, `"Runter"`, `"Zeile leeren"`, `"Zeile loeschen"`).

---

## 1.4 Was im Weg steht — die Geometrie, GEMESSEN (Code)

### 1.4.1 Die sechs `width:130` sind NICHT die Bildschirmtabelle

Die Nachpruefung der Zahl aus v3.9.944 stimmt — aber die Stelle ist eine
andere als vermutet.

| | |
|---|---|
| `width:130` in `WeekPlan` | **6** im CODE (8 dateiweit, 6 davon hier) |
| Wo | im Argument von `window._exportReviewModal({ … columns:[ … ] })` |
| Was das ist | die **Excel-Exportvorschau**, Untertitel woertlich: „Werte korrigieren — **nur Export, DB bleibt**", Bestaetigungsknopf „Excel exportieren" |
| Sichtbar | erst nach einem Klick auf den Knopf „Excel" |
| Ganze Spaltenliste | `nr` 40 · `bvh` 200 · `mo/di/mi/do_/fr/sa` je **130** · `fahrzeuge` 160 · `bemerkung` 160 = **1340 px** |

**Anker** (`grep -F`, 1×, Laenge 120):

```
{key:"nr",label:"Nr",type:"readonly",width:40},
          {key:"bvh",label:"— BVH / Baustelle",type:"text",width:200},
```

**SCHLUSS:** Diese sechs Zahlen koennen an der Planungsansicht bei 1440 px
**kein Pixel** freimachen. Sie waren in dem gemessenen Lauf mit hoher
Wahrscheinlichkeit nicht einmal im DOM (die Vorschau ist ein Modal hinter
einem Klick). Der Satz aus v3.9.944 — „Die Tabelle fuehrt feste
Spaltenbreiten (`width:130` sechsmal …); wer sie hebt, muss dort zuerst Platz
schaffen" — zeigt an dieser Stelle auf das falsche Bauteil.

### 1.4.2 Die sechs `minWidth:800`: vier im Code, zwei in Kommentaren — und alle vier liegen in einem gewollten Querroller

| Stelle | Zeile | Was | Anker (Laenge 70, dateiweit **1×**) |
|---|---|---|---|
| 1 | 22110 | `_absRow` — Abwesenheitsstreifen | `minWidth:800,borderBottom:"1px solid "+V.bd}}\r\n    ,React.createElemen` |
| 2 | 22185 | Spezialfahrzeug-Streifen | `minWidth:800,borderBottom:"1px solid "+V.bd}}\r\n              , React.c` |
| 3 | 22200 | Wetterstreifen | `minWidth:800}}\r\n        , React.createElement('div', { style: {width:2` |
| 4 | 22227 | **die Haupttabelle** | `minWidth:800,tableLayout:"fixed"}}\r\n          , React.createElement('c` |
| — | 22107, 22176 | zwei **Kommentare** aus v3.9.523, die die Geometrie beschreiben | — |

`overflowX:"auto"` steht in `WeekPlan` **7×** im CODE. Jede der vier
`minWidth:800`-Stellen hat einen: z22118 (ueber `_absRow`), z22177 (ueber den
Spezialfahrzeug-Streifen), z22199 (am Wetterstreifen selbst), z22226 (ueber
der Haupttabelle). Dazu z22031 fuer die MA-Uebersicht (`minWidth:700`) und
zwei Tagesstreifen auf Mobil (z21998, z22132).

**SCHLUSS:** Bei 1440 px ist der Behaelter ~1398 px breit, also **weit ueber
800**. Die Untergrenze `minWidth:800` ist dort **gar nicht aktiv**; sie greift
erst unter 800 px, also am Telefon, wo sie den gewollten Querroller aufspannt.
**Sie kann bei 1440 px nicht die Ursache sein, und sie abzusenken schafft dort
nichts.**

### 1.4.3 Die Geometrie der Streifen — 96 % + 72 px, und das passt erst ab 1800 px

Die drei Streifen und die Haupttabelle folgen demselben Raster (in v3.9.523
absichtlich gleichgezogen, Kommentar woertlich: „28px + 16% + 6×12% + 8% +
44px, minWidth:800 → Tage fluchten mit Tabelle + Wetter").

Gelesen (Code), Streifen = `display:flex, gap:0`:

| Kind | Breite | schrumpfbar |
|---|---|---|
| Einzug | `width:28` | `flexShrink:0` |
| BVH / Beschriftung | `width:"16%"` | `flexShrink:1` |
| Mo–Fr (5 Spalten) | `width:"12%"` je | `flexShrink:1` |
| Sa (6. Spalte) | `width:"6%"` | `flexShrink:1` |
| leere Fuellspalte | `width:"14%"` | `flexShrink:1` |
| rechter Rand | `width:44` | `flexShrink:0` |

Summe: **16 % + 5×12 % + 6 % + 14 % = 96 %**, dazu **28 + 44 = 72 px** fest.

Damit ist die Zeile **ueberbestimmt**: sie passt erst, wenn
`0,96·W + 72 ≤ W`, also **W ≥ 1800 px**. Bei einem Behaelter von 1398 px
sind es `72 − 0,04·1398 = 16,1 px` **zu viel**, und nur `flexShrink:1` haelt
die Zeile zusammen. Der Boden des Schrumpfens ist die **min-content**-Breite
der Kinder — und in `WeekPlan` stehen **19** `whiteSpace:"nowrap"` und **7**
`textOverflow`. **Genau deshalb bewegt eine groessere Schrift hier Breite:**
sie hebt den min-content-Boden, der Schrumpfweg wird kuerzer, und der Rest
bleibt als Ueberschuss stehen.

Die Haupttabelle hat dieselbe Spaltenliste im `colgroup`
(`28 · 16% · 6×(12%/6%) · 14% · 44`), aber `tableLayout:"fixed"` mit
`width:"100%"` — der Browser normiert die ueberbestimmten Spalten auf die
Tabellenbreite. **Die Tabelle rollt dadurch nicht; die Streifen haben diesen
Schutz nicht.**

**Woher 1398 px kommen — SCHLUSS, nicht gemessen:** `.main-pad{padding:20px}`
(Code), also `1440 − 40 = 1400`; die Kartenhuelle um Tabelle und Wetterstreifen
traegt `border:"1px solid "+V.bd`, also `1400 − 2 = 1398`. Das passt auf das
Pixel, ist aber eine **Rechnung, keine Messung** (siehe Abschnitt 4).

### 1.4.4 Die 7 px: was das Protokoll wirklich sagt

Zwei Dinge stehen so nicht im Protokoll und muessen dazu:

**(a) Die Zahlen sind vertauscht notiert.** „7 px quer (1398 von 1405)" liest
sich als `scrollWidth 1398` gegen `clientWidth 1405` — das waere **kein**
Ueberlauf (1398 < 1405). Die Sonde
(`scripts/b3_vier_ansichten_messen.py`) meldet
`ueberschuss = scrollWidth − clientWidth`; ein Ueberschuss von 7 bedeutet
zwingend **clientWidth 1398, scrollWidth 1405**. Nur diese Leseweise ist mit
„7 px" vereinbar.

**(b) Die Liste, aus der die Zahl stammt, enthaelt NUR gewollte Roller.** Im
Quelltext der Sonde:

```js
const roller = [];
… .querySelectorAll('*').forEach(e => {
  if (e.scrollWidth <= e.clientWidth + 1) return;
  const ox = _cs(e).overflowX;
  if (ox !== 'auto' && ox !== 'scroll') return;   // <-- nur auto/scroll
```

`waagrechte_roller` listet also **ausschliesslich** Elemente, die ein
`overflow-x: auto|scroll` tragen — Behaelter, die quer rollen **sollen**. Das
Urteil „die Seite rollt quer" faellt in derselben Sonde ueber `ursache`
(gefiltert mit `!in_rollbar`) und `rollt`.

**SCHLUSS:** Die „7 px quer" sind ein **lokaler Querroller in einem der
sieben `overflowX:"auto"`-Behaelter von WeekPlan**, der 7 px weiter rollt —
nicht ein Querroller der Seite. Das Argument, das die Ausnahme fuer WeekPlan
wirklich traegt, ist **der Beschnitt 1 → 13** (`anzahl_schlimm`: Elemente mit
Text, deren Inhalt breiter ist als der Kasten, **ohne** eigenen Roller). Das
bleibt ein gutes Argument. Die 7 px sind es nicht.

**NICHT GEMESSEN:** welcher der sieben Behaelter es war (die Sonde protokolliert
`weg` und `breitestes_kind` — beides steht im Lauf, nicht in meiner Reichweite,
weil ich keinen Browser fahre).

---

## 1.5 Drei Vorschlaege

### Vorschlag 1 — der kleinste, der kein Pixel kostet: die leere Fuellspalte flexibel machen

**Anker** (`grep -F`, Laenge **26**, **3× dateiweit, alle 3 in `WeekPlan`** —
z22114 `_absRow`, z22191 Spezialfahrzeug-Streifen, z22210 Wetterstreifen):

```
{width:"14%",flexShrink:1}
```

Diese drei `div` haben **keine Kinder** — reine Fuellflaeche rechts vor dem
44-px-Rand. Aus `width:"14%"` ein `flex:"1 1 0%",minWidth:0` zu machen nimmt
die ganze Ueberbestimmung von 96 % + 72 px heraus: die Zeile ist dann bei
**jeder** Breite genau 100 %, der Schrumpfzwang auf Text-Spalten faellt weg,
und **kein sichtbares Element wird kleiner** — die 16 px (und damit die 7)
verschwinden aus einem Kasten, in dem ohnehin nichts steht.

**Risiko:** v3.9.523 hat die Streifen absichtlich auf das Tabellenraster
gelegt („Tage fluchten mit Tabelle + Wetter"). Weil die Tabelle ihre
Ueberbestimmung ueber `tableLayout:fixed` **anders** aufloest als ein
Flex-Streifen, kann die Flucht der Tagesspalten um bis zu 16 px wandern —
besser oder schlechter. **Das ist die ganze Frage an diesem Vorschlag, und
sie ist ohne Schirm nicht entscheidbar.**

**Gegenmessung, die ihn belegt:** `scripts/b3_vier_ansichten_messen.py`,
Ansicht Planung, 1440 px.
1. `waagrechte_roller` enthaelt **keinen** Eintrag mit `ueberschuss` 7 (bzw.
   16) mehr — heute steht dort `clientWidth 1398 / scrollWidth 1405`.
2. `beschnitt.anzahl_schlimm` bleibt bei **1** (darf nicht steigen).
3. Fuer die Flucht braucht es eine Sonde, die es heute **nicht** gibt: die
   linken Kanten der sechs Tagesspalten in Tabelle und Wetterstreifen
   (`getBoundingClientRect().left`) muessen paarweise auf ≤ 1 px
   uebereinstimmen. `scripts/abschnitt_probe.py` misst Streifen, aber nicht
   diese Paarung.

### Vorschlag 2 — der wahrscheinlichste, der wirkt: nur das Telefon heben

Die 51 nackten Zahlen der Familie A in die Form der Familie C bringen:
`fontSize:11` → `fontSize:isMob?12:11`, `fontSize:10` → `isMob?12:10`,
`fontSize:9` → `isMob?12:9`. Die Schreibtisch-Zahl bleibt **byte-gleich
wirksam**, also kann die 1440-px-Geometrie **konstruktionsbedingt nicht
wandern**. Geliefert wird genau der Gewinn, der im Protokoll steht: **49 → 2
bei 390 px**, in der Ansicht, die der Monteur am haeufigsten am Telefon
ansieht.

Die Form ist in dieser Datei bereits belegt — **Anker** (Laenge 60):

* `fontSize:isMob?12:9,padding:isMob?"4px 8px":"2px 5px",border` — **2×**
  dateiweit, beide in `WeekPlan` (z21822, z21839)
* `fontSize:isMob?12:10,color:V.dm}}, dateFmt(0), " — "  , date` — **1×** (z21915)
* `fontSize:isMob?12:11,...(isMob?{textAlign:'center',width:'10` — **1×** (z22317)

**Risiken (drei, alle benannt):**

1. 🔴 **Der bestehende Koeder-Riegel wird rot.**
   `test_weekplan_ist_ausgenommen_und_das_ist_gemessen` verlangt, dass das
   v944-Muster in `WeekPlan` **etwas** findet. Nach der Umstellung findet es
   dort **0** — `fontSize:isMob?12:9` passt nicht auf
   `isMob\?(?:9|10|11):\d+`. Der Riegel wuerde dann melden „die Ausnahme ist
   aufgehoben", obwohl sie am Schreibtisch weiterbesteht. **Diese Pruefung
   habe ich nicht angefasst** (verboten, und richtig so): das ist eine
   Entscheidung fuer Sebastian — entweder der Riegel bekommt die zweite
   Familie ins Muster, oder die Umstellung geschieht in einem Schritt, der
   ihn mit begruendet.
2. Am Telefon **wachsen Zeilen- und Kachelhoehen** (die Tageszellen tragen
   `minHeight:42`, die Auswahlknoepfe `minWidth:52`). Das ist der Grund, warum
   Stufe 3 ansichtsweise gefahren wurde, und es ist zu messen, nicht zu
   vermuten.
3. Die Schuld am Schreibtisch bleibt vollstaendig stehen — 51 Stellen unter
   12 px, dauerhaft. Das ist eine **Verschiebung**, keine Loesung.

**Gegenmessung, die ihn belegt:** `scripts/b3_vier_ansichten_messen.py`,
Ansicht Planung, drei Breiten, alle acht Koeder je Lauf.
* 390 px: `schrift`-Zaehlung „Textstellen < 12 px" **44 → ≤ 5**
  (Protokollzeile „Planung | unveraendert 44").
* 375 px: **49 → ≤ 5**.
* 1440 px: **unveraendert 42**, `beschnitt.anzahl_schlimm` **unveraendert 1**,
  `waagrechte_roller` unveraendert. Jede Abweichung dort widerlegt die
  Behauptung „der Schreibtisch kann sich nicht aendern" — und damit den
  Vorschlag.
* Zusaetzlich `python scripts/node_check.py` (das Dezimalmuster hat hier schon
  einmal `fontSize:9.5` zerschnitten).

### Vorschlag 3 — den ich NICHT empfehle: „erst die festen Breiten absenken"

Der Weg, den der v944-Eintrag selbst nahelegt: `width:130` → z. B. 110 und
`minWidth:800` → z. B. 760, damit „Platz entsteht", und dann alle 56 heben.

**Anker:** die zwei Tabellen aus 1.4.1 und 1.4.2 (Export-Spaltenliste,
Laenge 120, 1×; und die vier `minWidth:800`-Schnitte, je Laenge 70, je 1×).

**Warum ich ihn nicht empfehle — und das ist gemessen, nicht Geschmack:**

* Die sechs `width:130` gehoeren zur **Excel-Exportvorschau**
  (`_exportReviewModal`, „nur Export, DB bleibt"), nicht zur Planungstabelle.
  Sie koennen **an der Ansicht kein Pixel** freimachen; wer sie senkt,
  verkleinert die Spalten im Korrekturdialog vor dem Export.
* `minWidth:800` ist bei 1440 px **nicht aktiv** (Behaelter ~1398 ≫ 800) und
  liegt ausserdem in allen vier Faellen **innerhalb** eines gewollten
  `overflowX:"auto"`. Absenken aendert am Schreibtisch nichts und nimmt dem
  **Telefon** die lesbare Mindestbreite — es verschlechtert genau die
  Ansicht, um die es geht.
* Der eigentliche Engpass, die Ueberbestimmung **96 % + 72 px**, bleibt dabei
  unangetastet.

**Gegenmessung, die mich widerlegen wuerde:** ein Lauf von
`b3_vier_ansichten_messen.py` bei 1440 px, in dem `waagrechte_roller` einen
Eintrag zeigt, dessen `breitestes_kind.tag` `table` ist **und** dessen
`ueberschuss` nach einem Absenken von `minWidth:800` sinkt. Nach dem
Quelltext kann das nicht eintreten — aber genau so waere es zu entscheiden.

---

# TEIL 2 — Befund E1: das Zuordnungsfeld in StundenzettelView

## 2.1 Die Stelle — GEMESSEN (Code)

| | |
|---|---|
| Komponente | `StundenzettelView({monteure,ww,curUser,users,entries,projects,abs,approvals})`, Zeile 23157 |
| Block | „Monatszettel hochladen", hinter `canUpload` (`role==="admin"` ∥ `"buero"` ∥ `rolle==="backoffice"` ∥ `"lagerleitung"` ∥ `username==="schober"`) |
| Feld | `<label>Mitarbeiter</label>` + `<select value=selMA>`, Platzhalter „— Mitarbeiter waehlen —", Zeile 23501/23502 |
| Wirkung des Werts | `selMA` geht als `mitarbeiterId` in den Upload-Datensatz (Zeile 23270) — es ist die **Zuordnung**, nicht ein Filter |
| Vorrat | `allMA`, Zeile 23187 |

**Anker `allMA`-Deklaration** (`grep -F`, 1×, Laenge 150):

```
const allMA=[...(users||[]).filter(u=>u.active!==false),...(monteure||[]).filter(m=>!(users||[]).find(u=>u.monteurId===m.id||u.monteur_id===m.id))];
```

**`allMA` speist ZWEI Felder** — das ist fuer jeden Griff entscheidend:

| Zeile | Feld | Familie nach v3.9.874 |
|---|---|---|
| 23502 | Upload-**Zuordnung**, Platzhalter „— Mitarbeiter waehlen —" | **Zuweisungsliste → `_maWaehlbar`** |
| 23540 | **Filter** ueber die Liste, Platzhalter „Alle Mitarbeiter" | **Filterliste → absichtlich OHNE `_maWaehlbar`** |

Die beiden `option`-Rumpfe sind **byte-identisch** (`allMA.map(m=>(React…`,
Laenge 96, 2× dateiweit). Ein Anker muss deshalb **beim Platzhalter
anfangen**, sonst trifft er beide. Eindeutige Schnitte:

* Zuordnung (Laenge 260, **1×**):
  `React.createElement('option', { value: ""}, "— Mitarbeiter waehlen —"   )` …
  `, allMA.map(m=>(React.createElement('option', { key: m.id, value: m.id}, m.name||m.n||m.id)))`
* Filter (Laenge 250, **1×**):
  `React.createElement('option', { value: ""}, "Alle Mitarbeiter" )` … derselbe `map`.

**Ein Griff auf `allMA` selbst wuerde also beide Felder treffen und damit die
v3.9.874-Entscheidung brechen.** Der Griff gehoert an die Aufrufstelle
Zeile 23502.

### 2.1.1 Der Weg — und ein veralteter Kommentar, der ihn falsch beschreibt

Der Kommentar direkt in `StundenzettelView` (Zeile 23159) sagt: „FINKZEIT
STANDBY (04.06.2026) — komplette View geparkt: der Tab ‚Monatsabrechnung' ist
hinter `FINKZEIT_ENABLED` ausgeblendet, **diese Komponente wird nicht mehr
gerendert**."

**GEMESSEN (Code), Zeile 3092:** `const FINKZEIT_ENABLED=true;` mit dem
Kommentar „v3.9.204 Monatsabrechnung reaktiviert (04.06. geparkt, nicht
geloescht)".

**SCHLUSS:** Der Weg ist **offen** — der Tab `stunden` steht in `_navIds` und
in der Tab-Liste, und die Aufrufstelle Zeile 9788 rendert
`StundenzettelView`. Zusaetzliches Tor: `hasPerm(curUser,"stunden")`. Der
Kommentar in der Komponente ist seit v3.9.204 **falsch** und wuerde jeden, der
E1 pruefen will, in die Irre schicken („geparkt, also unwichtig"). Das ist
ein Wegriegel-Fall mit umgekehrtem Vorzeichen: hier sagt der Quelltext, das
Bauteil sei unerreichbar, obwohl es erreichbar ist.

## 2.2 Das Schema von `public.users` — GEMESSEN (DB), 26.09.2026

Verfahren wie `docs/befunde/OFFA_SCHEINE.md` §3 und
`docs/befunde/B2_WORKER_PROJECTS.md` §2.2: anon-Schluessel aus dem
ausgelieferten Buendel, **nur GET**, `?select=<spalte>&limit=1`. Eine Spalte,
die es nicht gibt, gibt HTTP 400 `42703`.

**KOEDER (alle drei angeschlagen):**

| Probe | Antwort |
|---|---|
| `users?select=DIESE_SPALTE_GIBT_ES_NICHT_koeder` | **400 `42703`** „column users.DIESE_SPALTE_GIBT_ES_NICHT_koeder does not exist" |
| `DIESE_TABELLE_GIBT_ES_NICHT_koeder?select=id` | **404 `PGRST205`** |
| `users?select=id` | **200** |

Die Probe kann Abwesenheit also wirklich erkennen. Ohne das waere jedes
„vorhanden" unten wertlos.

**Vorhanden — 18 Spalten:**

`id` · `username` · `name` · `email` · `role` · `active` · `locked` ·
`monteur_id` · `perms_override` · `permissions` · `last_login` ·
`login_count` · `deactivate_at` · `auth_user_id` · `password_hash` ·
`phone` · `created_at` · `updated_at`

**Nicht vorhanden — je HTTP 400 `42703`** (34 geprueft):

`austritt` · `austritt_datum` · `austrittsdatum` · `austrittdatum` ·
`ausgetreten` · `ausgetreten_am` · `exit_date` · `left_at` · `leave_date` ·
`termination_date` · `kuendigung` · `kuendigungsdatum` · `ende` · `end_date` ·
`valid_until` · `gueltig_bis` · `inactive_since` · `deactivated_at` ·
`deleted_at` · `archived` · `archived_at` · `aktiv` · `eintritt` ·
`eintritt_datum` · `entry_date` · `rolle` · `notif_prefs` · `notifPrefs` ·
`tel` — und die camelCase-Zwillinge `monteurId`, `permsOverride`,
`lastLogin`, `deactivateAt`, `created`.

**Typen (Probe `?spalte=gt.ZZ_kein_datum_ZZ`) — GEMESSEN (DB):**

| Spalte | Antwort | Typ |
|---|---|---|
| `active` | 400 `22P02` „invalid input syntax for type **integer**" | **integer**, nicht boolean |
| `deactivate_at` | 400 `22007` „invalid input syntax for type **date**" | **date** |
| `monteur_id` | 200 | Textfamilie |
| `id` | 200 | Textfamilie |

**Gegenstueck, GEMESSEN (DB):**

| Probe | Antwort |
|---|---|
| `workers?select=austritt` | **200** — `workers` **fuehrt** `austritt` |
| `workers?austritt=gt.ZZ_kein_datum_ZZ` | 200 → **Textfamilie** (passt zu `String(m.austritt).slice(0,10)<h` in `_maIstEhemalig`) |
| `workers?select=eintritt` | 200 |
| `workers?select=n` / `?select=aktiv` | je 400 `42703` (die App-Namen `n`/`r` entstehen erst in `_mapWorker`) |
| `monteure?select=id` | **404 `PGRST205`** — es gibt **keine** Tabelle `public.monteure`; der App-Zustand `monteure` kommt aus `workers` |
| `users?select=id,workers(id)` | 400 `PGRST200` „Could not find a relationship" — **kein Fremdschluessel** users↔workers, PostgREST kann nicht einbetten |
| `users` Zeilenzahl (`Prefer: count=exact`) | `Content-Range: */0` — **anon sieht keine Zeile** (RLS), wie im Auftrag angekuendigt |

## 2.3 Antwort: `_maWaehlbar(allMA, sel)` ist die **halbe** Loesung

Begruendung aus dem gemessenen Schema, Schritt fuer Schritt:

1. `_maWaehlbar` filtert ueber `_maIstEhemalig(m,h)`, und das liest **nur**
   `m.austritt` (GEMESSEN, Code: `return !!(m&&m.austritt&&String(m.austritt).slice(0,10)<h);`).
2. `public.users` fuehrt **kein** `austritt` (GEMESSEN, DB, `42703`) — und auch
   keinen der 20 naheliegenden Ersatznamen.
3. `API.getUsers()` ist `_sbGetUsersSafe("order=name.asc")`, also `select=*`,
   und `_mapUser` gibt `{...u, …}` zurueck (GEMESSEN, Code). Es kommt also
   genau das an, was die Tabelle fuehrt — **kein `austritt`**.
4. `INIT_USERS` fuehrt es ebenfalls nicht (GEMESSEN, Code: 8 Zeilen mit
   `id, username, name, email, role, active, monteurId, lastLogin, created,
   locked, permsOverride`).
5. **SCHLUSS:** `_maIstEhemalig` ist fuer **jede** Zeile aus dem `users`-Teil
   immer `false`. `_maWaehlbar(allMA, sel)` filtert dort **nichts**.

Und es ist nicht die kleinere Haelfte, sondern die **relevante**:

> `allMA` setzt sich aus **allen** `users` (mit `active!==false`) plus jenen
> `monteure` zusammen, die **kein** Login haben. Wer ein Login hat, erscheint
> also **aus dem `users`-Teil** — und genau dieser Teil traegt kein
> `austritt`. Ein ausgetretener Mitarbeiter **mit** Login wird von
> `_maWaehlbar` nicht erfasst. Ein ausgetretener **ohne** Login wird erfasst.

`_maWaehlbar` ist damit **nicht falsch** (der `monteure`-Teil wird korrekt
gefiltert, und der Selbstschutz „der bereits zugewiesene Ausgetretene bleibt
sichtbar" ist genau richtig fuer ein Zuordnungsfeld) — aber es ist **nur die
Haelfte**, und fuer den haeufigeren Fall die stumme Haelfte.

## 2.4 Was fehlt — und ein Vorschlag mit Ankern

Die Datenbank fuehrt das Austrittsdatum **nur an `workers`**, und die
Verbindung ist `users.monteur_id` (GEMESSEN, DB: beide Spalten vorhanden,
**kein** FK — die Verknuepfung muss also in JS geschehen, wie sie es in
`allMA` bereits tut).

**Vorschlag (nicht gebaut):** an der **Aufrufstelle Zeile 23502** — und nur
dort — den Vorrat vor `_maWaehlbar` mit einem `austritt` versehen, das aus dem
verknuepften Worker kommt:

```
const _maZuweisbar = _maWaehlbar(
  allMA.map(m => (m.austritt !== undefined) ? m : {
    ...m,
    austritt: ((monteure||[]).find(w => w.id === (m.monteurId||m.monteur_id)) || {}).austritt || ""
  }), selMA);
```

und im `select` der Zuordnung `allMA.map(...)` → `_maZuweisbar.map(...)`.
Der Filter in Zeile 23540 bleibt **unberuehrt** (v3.9.874: Filter- und
Reportlisten muessen Ausgetretene weiter anbieten).

Das ist tragfaehig, weil `_mapWorker` `austritt` **fuehrt** (GEMESSEN, Code:
`austritt:w.austritt||""`) und `workers.austritt` in der DB existiert
(GEMESSEN, DB). `_maWaehlbar`, `_maIstEhemalig` und `_ezHeuteISO` bleiben
dabei **byte-identisch** — es wird nur der Vorrat vorbereitet.

**Die Restluecke, die damit NICHT zugeht** — und die gehoert Sebastian
vorgelegt, nicht von mir entschieden:

* Ein **Buero-Login ohne `monteur_id`** hat in der ganzen Datenbank kein
  Austrittsdatum. Der einzige gemessene Ausstiegs-Hinweis auf der
  users-Seite ist `deactivate_at` (**date**, vorhanden) zusammen mit
  `active` (**integer**).
* `allMA` filtert `u.active!==false`. Die Umschaltung von `active` auf 0 bei
  faelligem `deactivate_at` passiert im Code aber in einer Schleife, die mit
  `if(curUser.role!=="admin")return;` beginnt (Zeile 13810). **Die Leute, die
  dieses Upload-Feld benutzen duerfen** (`buero`, Backoffice, Lagerleitung),
  **sind keine Admins** — bei ihnen laeuft die Nachfuehrung nie. Ein Login mit
  abgelaufenem `deactivate_at` und noch `active=1` steht in ihrer Liste.
  Der Kommentar dort sagt selbst, die **Login-Sperre** passiere ohnehin
  serverseitig — die **Liste** korrigiert sich aber erst, wenn ein Admin die
  Benutzerverwaltung oeffnet. Ob heute eine Zeile so aussieht, ist **NICHT
  GEMESSEN** (anon sieht keine Zeilen).
* Der saubere Weg waere eine gemeinsame Aussage „ehemalig" auf beiden Seiten
  (`workers.austritt` **oder** `users.deactivate_at <= heute`). Das ist eine
  Regel-Entscheidung, keine Reparatur, und sie braucht eine eigene Messung an
  echten Zeilen.

**Gegenmessung, die den Vorschlag belegen wuerde:** eine Pruefung, die den
geschnittenen Block unter Node **ausfuehrt** (wie
`tests/test_ausgetretene_live_v931.py` und
`tests/test_werkzeuge_vorbereitet_v940.py` es tun — inklusive `UI` in der
Attrappe, sonst wirft Node „UI is not defined") mit drei Faellen:
(1) Ausgetretener **mit** Login erscheint **nicht**,
(2) Ausgetretener **ohne** Login erscheint **nicht**,
(3) ein bereits als `selMA` gesetzter Ausgetretener erscheint **doch** —
sonst loescht der naechste Speichern-Klick eine bestehende Zuordnung.
Plus ein **Koeder**: derselbe Vorrat, `selMA=""`, muss die aktiven
Mitarbeiter liefern (eine leere Liste bestaetigt nichts).

---

# 3. NICHT GEMESSEN

Ausdruecklich und vollstaendig, weil dieser Lauf **keinen Browser** fahren
durfte (knapper Arbeitsspeicher, ein anderer Lauf fuhr Browsersonden):

1. **Die 7 px selbst.** Sie stehen im Protokoll eines **fremden** Laufs. Ich
   habe sie nicht nachgemessen und kann es ohne Schirm nicht. Was ich
   gemessen habe, ist der **Quelltext der Sonde**, die sie erzeugt hat —
   daraus folgt die Einordnung in 1.4.4, nicht eine neue Zahl.
2. **Die 13 Kuerzungen.** Ebenfalls fremder Lauf. Nicht nachgemessen. Dies
   ist das Argument, das die Ausnahme traegt — und es steht ungeprueft.
3. **Welcher der sieben `overflowX:"auto"`-Behaelter** 1398 px breit war und
   welches Kind ihn auf 1405 aufgespannt hat. Die Sonde protokolliert `weg`
   und `breitestes_kind`; ich habe diesen Lauf nicht.
4. **Die 1398 px.** Die Rechnung `1440 − 2×20 (.main-pad) − 2×1 (Kartenrand)`
   trifft auf das Pixel, ist aber eine **Rechnung**. Gemessen ist sie nicht.
5. **Die Flucht** der Tagesspalten zwischen Streifen und Tabelle — heute
   weder vorher noch nachher gemessen; die Sonde dafuer existiert nicht.
6. **Ob die 56 Quellstellen 1:1 den gerenderten 42/44/49 Textstellen
   entsprechen.** Sie tun es sicher nicht (Schleifen erzeugen viele Knoten
   aus einer Stelle, unsichtbare Zweige keinen). Quelltextzahl und
   Schirmzahl sind zwei verschiedene Groessen.
7. **Zeilen in `public.users`.** `Content-Range: */0` — anon sieht wegen RLS
   keine. Ob irgendein Login heute ein gesetztes `deactivate_at` hat, ob
   ueberhaupt ein ausgetretener Mitarbeiter ein aktives Login besitzt, und
   wie viele Zeilen die Tabelle fuehrt: **nicht gemessen.** Auch nicht, ob
   `anon` das SELECT-**Recht** hat und nur RLS davor liegt.
8. **Policies, Vorgabewerte, Trigger, Primaerschluessel** von `public.users` —
   mit `anon` nicht lesbar.
9. **Die Breite der Spalten in der Exportvorschau am Schirm.** Dass die sechs
   `width:130` zur Vorschau gehoeren, ist aus dem Quelltext gemessen; wie der
   Dialog bei 1440 px aussieht, nicht.
10. **Kein `pytest` ueber die Sammlung gefahren** (Auftrag). Die Aussagen zu
    `test_b6_stufe3_v944.py` sind aus dem **Lesen** der Datei, nicht aus einem
    Lauf: insbesondere die Vorhersage „Vorschlag 2 macht
    `test_weekplan_ist_ausgenommen_und_das_ist_gemessen` rot" ist ein
    **Schluss aus dem Muster**, keine beobachtete rote Meldung.
