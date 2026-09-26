# B3, Stufen 4–7 — vier Ansichten gemessen, je bei 390 px UND 1440 px

Gemessen am **26.09.2026** an der eingefrorenen Kopie
`_mess_stand_939.html`, md5 **`f750cdcb888a46b85f8b8504abec39ea`**
(zu Beginn und am Ende der Sitzung derselbe Wert; `index.html` wurde nicht
angefasst und nicht gelesen).

Ansichten: **Werkzeuge · Planung/Wochenplanung · Home/Startseite ·
Arbeitsschein bearbeiten**, jede bei **390×844** (`is_mobile`, `has_touch`,
also `pointer: coarse`) und bei **1440×900** (`pointer: fine`).
Rolle `admin`, `monteurId=M1`, REST und Auth abgeklemmt. Die Amber-/Orange-
Warnbänder im Bild sind Aufbau-Artefakt und **kein Befund**.

Sonden:

| Datei | was sie tut |
|---|---|
| `scripts/b3_vier_ansichten_messen.py` | die sieben Regeln am gerenderten Schirm, vier Ansichten × zwei Breiten, acht Köder |
| `scripts/b3_bestand_quelltext.py` | Mengengerüst aus dem Quelltext (Handlungen, Felder, Optionen, Schriftgrößen), drei Köder |
| `scripts/b3_home390_beschnitt.py` | Nachtrag: die fünf Beschnittstellen auf Home bei 390 px benennen, ein Köder |

---

## 0. Zuerst: FÜNF Korrekturen an den eigenen Werkzeugen

Jede davon hat in einem Zwischenlauf eine **saubere, falsche Zahl** geliefert.
Sie stehen hier vorn, weil sie erklären, warum die Zahlen weiter unten
belastbar sind — und weil vier davon genau die Fehlerform haben, gegen die
die Regeln aus dem Gedächtnis geschrieben sind.

**K-1 · Der Melder filterte seinen eigenen Köder weg.**
`BESCHNITT_JS` und `QUER_JS` blendeten Elemente mit der Kennung `__k*` aus —
also genau die Köder. Beide meldeten „Köder nicht gefunden", obwohl der Köder
dastand. *Ein Melder, der seinen Köder wegfiltert, ist der Fall, gegen den der
Köder da ist.*

**K-2 · Der Verdeckungsmelder rollte den falschen Roller.**
Erste Fassung: `window.scrollTo(0, scrollHeight)`. Bis 1199 px scrollt aber
nicht die Seite, sondern der Behälter — `@media(max-width:1199px){
.app-shell{height:100dvh;overflow:hidden} .main-pad{flex:1;overflow-y:auto} }`.
Das Fenster gab nur 70 px her, der Inhalt blieb oben stehen. Gemeldet wurden
**sechs „verdeckte" Bedienelemente in Werkzeuge**, die in Wahrheit gar nicht am
Listenende standen. Nach der Korrektur (jeder Roller wird bis an sein Ende
gefahren und das Ankommen belegt): **0 verdeckte Bedienelemente in allen vier
Ansichten.**

**K-3 · „Tippziel" und „Beschriftung" lagen in einem Topf.**
Erste Fassung meldete im Arbeitsschein-Formular **22 Tippziele unter 44 px** —
alle 22 waren 19,5 px hohe **Feldbeschriftungen** über einem 44 px hohen
Eingabefeld. Jetzt zwei Töpfe; die 44-px-Regel gilt nur für den Knopf-Topf.
Aus 23 Befunden wurde **1**.

**K-4 · Die Navigation bewies die falsche Seite.**
Home bei 390 px: `NAV_WAEHLEN_JS` nimmt den *letzten* Knopf mit dem
aria-label — und das ist der **Gruppenknopf der Fußleiste**. Der öffnet den
zuletzt aktiven Reiter seiner Gruppe, und in Gruppe 0 liegt neben Home auch
**Chef**. Die Sonde hat ein vollständiges **Chef-Dashboard vermessen und
„Home" darüber geschrieben** — und der Navigationsnachweis war grün, weil er
nur „≥ 4 `[role=button][aria-label]` und irgendwo das Wort Projekt" prüfte,
was auf das Chef-Dashboard genauso zutrifft. Jetzt: Klick nur auf Knöpfe
außerhalb `.bottom-nav`, und der Nachweis verlangt ein Merkmal, das **nur**
HomeView hat (Kachel-aria-labels `Werkzeugwert`/`Bautagebuch`/
`Monatsabrechnung` bzw. `Tanken`) **und** die Abwesenheit des Chef-Merkmals
`Überblick`. Die Home-Zahlen aus den ersten Läufen (22 Textstellen < 12 px)
waren die des Chef-Dashboards; die richtigen sind **78**.

**K-5 · Die Querroll-Regel kann im Wortlaut nie rot werden — und war trotzdem
verletzt.** Siehe Befund **B4** unten. Der Melder sah auf
`document.scrollingElement`; `body` trägt `overflow-x:hidden`, also kann
dieser Vergleich in dieser App **nie** zutreffen. Ein 3000 px breites Kind
ließ `scrollWidth` bei 390 stehen. Zu breiter Inhalt wird hier nicht gerollt,
sondern still **abgeschnitten**. Gemessen wird jetzt über die Rechtecke *und*
über jeden Behälter mit `overflow-x:auto`.

Dazu zwei kleinere:

* Der Emoji-Melder zählte eine **aufgezählte Liste von Codepoint-Bereichen**;
  der Block „Geometrische Formen" (▲ ▼ ◀ ▶) fehlte darin. Ersetzt durch die
  umgekehrte Vorschrift („trägt die Beschriftung einen Buchstaben oder eine
  Ziffer?"), plus ein **zweiter Köder** mit `▲`. Die Zahlen änderten sich
  dadurch nicht — der alte Melder hatte Glück, nicht recht.
* Der Quelltext-Größenzähler kannte nur `fontSize:9`, nicht
  `fontSize:isMob?7:9`. **Genau in dieser Form steht der kleinste Wert der
  ganzen App.** Die ersten Zahlen (47/53/61/54 Stellen) waren untergezählt;
  richtig sind **52/58/71/63**.

### Die acht Köder, alle in allen acht Läufen angeschlagen

| Köder | Fall | Nachweis |
|---|---|---|
| K1 Schrift | Textknoten mit `font-size:9px !important` | als 9 px gemessen und gemeldet |
| K2 Tippziel | Knopf 30×20 px, `!important` gegen die Hausregel | Melder fand genau 1 |
| K3 Emoji | zwei Knöpfe: nur `🔧`, nur `▲` | beide gemeldet |
| K4 Beschnitt | 240 Zeichen in 80 px `overflow:hidden` | gemeldet |
| K5 Querrollen | 3000 px breites Kind | als 3000 px Rechteck gemeldet, abschneidender Vorfahr benannt |
| K6 Saat | 6 Scheine, 6 Werkzeuge, 3 Monteure, 2 Projekte, 5 Zeiteinträge | zurückgelesen **und** in der Ansicht gefunden (7 bzw. 8 Treffer) |
| K7 Tabelle | 3000 px breite Tabelle | gemeldet — ohne ihn wäre „keine Tabelle zu breit" bei 390 px wertlos, dort gibt es nämlich gar keine Tabelle |
| K8 Verdeckung | Knopf `position:fixed` über der Leiste | gemeldet; bei 1440 px **entfällt** er, weil `.bottom-nav` in `@media(max-width:600px)` lebt |

Für den neuen Querroll-Melder gibt es eine **Positivkontrolle aus derselben
Messreihe**: auf Home bei 390 px meldet er `.main-pad` mit 460/390. „Kein
Roller" in den anderen Ansichten ist damit ein Messwert, kein blinder Fleck.

---

## 1. Messwerte, alle acht Läufe

| Ansicht | Breite | Schrift < 12 px | Tippziel < 44 px | nur Symbol, ohne title/aria | quer (Wortlaut) | quer (tatsächlich) | Beschnitt | verdeckt | Tabelle > Schirm |
|---|---|---|---|---|---|---|---|---|---|
| Werkzeuge | 390 | **60** von 101 | **4** | **5** | nein | keiner | 1 | 0 | – (keine Tabelle) |
| Werkzeuge | 1440 | 32 von 163 | 29 (Zeiger fein) | **6** | nein | keiner | 1 | entfällt | 0 (1398/1440) |
| Planung | 390 | **50** von 133 | 0 | **2** | nein | keiner | 1 | 0 | – (keine Tabelle) |
| Planung | 1440 | 43 von 234 | 31 (Zeiger fein) | **2** | nein | keiner | 1 | entfällt | 0 (1398/1440) |
| Home | 390 | **78** von 182 | 0 | 0 | nein | **`.main-pad` 460/390** | **5** | 0 | – |
| Home | 1440 | **120** von 237 | 9 (Zeiger fein) | 0 | nein | keiner | 1 | entfällt | – |
| Arbeitsschein bearb. | 390 | **45** von 140 | **1** | **2** | nein | keiner | 1 | 0 | – |
| Arbeitsschein bearb. | 1440 | 43 von 156 | 15 (Zeiger fein) | **2** | nein | keiner | 1 | entfällt | – |

„Tippziel < 44 px" bei **1440 px** ist **kein Regelbruch**: die Hausregel gilt
`@media (pointer: coarse), (max-width: 768px)`, und bei 1440 px mit feinem
Zeiger greift sie nicht. Die Spalte steht trotzdem da, weil dieselben
Elemente auf einem **Touch-Notebook oder Tablet bei 1440 px quer** grobe
Zeiger bekommen und die Regel dann nicht greift — das ist ein eigener,
unentschiedener Fall und steht unten unter „nicht gemessen".

---

## 2. Bestandsschutz — Mengengerüst IST gegen `GRUNDSTAND_UI_v3.9.930.md`

### Vorbemerkung, die für alle vier Ansichten gilt

Die **rohen Knopf-/Feldzahlen** des Grundstands sind mit dieser Messung
**nicht vergleichbar**, und zwar aus zwei benennbaren Gründen:

1. Die Zählvorschrift des Grundstands ist nicht dokumentiert (was zählt als
   „Eingabefeld"? Zählen `[role=button]`-Kacheln als Knöpfe? unsichtbare
   mit?).
2. Die Zahlen hängen am **Datenbestand**. Der Grundstand wurde an 296 echten
   Werkzeugen und 185 echten Scheinen aufgenommen, diese Messung an 6 und 6.
   Der Grundstand sagt das für die 228 Arbeitsschein-Knöpfe selbst.

Deshalb wird hier gegen die **benannten Stücke** geprüft — die sind
datenunabhängig und stehen im Grundstand ausgeschrieben. **Ergebnis vorweg:
in allen vier Ansichten ist jedes benannte Stück vorhanden. Kein
Regressionsfehler.**

### Werkzeuge

| Grundstand nennt | IST 390 | IST 1440 |
|---|---|---|
| + Neues Gerät · Labels · Excel · PDF | alle 4 ✔ | alle 4 ✔ |
| fünf Icon-Reiter 📷 📋 📤 🔧 ✏️ | 5 ✔, **0 mit Text** | 5 ✔, **5 mit Text** (`📷 QR Scan`, `📋 Liste`, `📤 Check-In/Out`, `🔧 Service`, `✏️ Neu`) |
| Filter-Chips Alle · Verfügbar · Ausgegeben · Kalibrierung fällig · Defekt | 5 ✔ mit Zählern `(6) (2) (1) (1) (1)` | 5 ✔, gleiche Zähler |
| Suchfeld „Name, Seriennr, Inventar…" | ✔ (`🔍 Name, Seriennr, Inventar...`) | ✔ |
| Auswahlfeld Status, 6 Werte | 7 Optionen (Alle + 6) ✔ | 7 ✔ |
| Auswahlfeld Kategorie, 9 Werte | 10 Optionen (Alle + 9) ✔ | 10 ✔ |
| Ausleihen je Gerät | 2 Knöpfe (`📦 Ausleihen` ×2, `✅ Zurückgeben` ×1) ✔ | ✔ |
| Grundstand: 3 Auswahlfelder | **3** ✔ | **2** |

Rohzahlen: 28 Knöpfe / 1 Feld / 3 Auswahlfelder (390) · 48 / 1 / 2 (1440).

Die **Differenz 3 gegen 2 Auswahlfelder** ist erklärt und **keine Regression**:
bei 390 px gibt es ein zusätzliches, **nur mobiles Sortier-Auswahlfeld**
(`Inventar · Bezeichnung · Standort · Status · Letzte Wartung`), das am
Rechner durch die klickbaren Tabellenköpfe ersetzt ist. Der Grundstand hat bei
390 px gemessen und nennt darum 3.

### Planung / Wochenplanung

| Grundstand nennt | IST 390 | IST 1440 |
|---|---|---|
| Woche zurück / vor | `◀` `▶` ✔ | ✔ |
| Nächste Woche | `📅 Nächste Woche ▶` ✔ | ✔ |
| + Zeile | ✔ (zweimal: Kopf und `+ Zeile hinzufügen`) | ✔ |
| Vorlage | – **siehe unten** | – **siehe unten** |
| Vorwoche | `📋 Vorwoche` ✔ | ✔ |
| Tageszahlen „N MA" | `Mo 3 MA · Di 2 MA · Mi 4 MA · Do 4 MA · Fr 4 MA · Sa —` ✔ | ✔ |
| KW-Sprungmarken | entfallen — **laut Grundstand gewollt**; jede KW bleibt über `◀`/`▶`/`Nächste Woche` erreichbar ✔ | ✔ |

Rohzahlen: 41 Knöpfe (390) · 54 (1440), zusätzlich `📅 Planung` /
`👷 MA-Übersicht` (Unterreiter), `📊 Excel`, `🖨️ PDF` und je Zeile
`▲ ▼ ✕` (390) bzw. `▲ ▼ 🗑 ✕` (1440).

> **Offen, nicht als Regression gemeldet:** Der Knopf **„Vorlage"** aus dem
> Grundstand erscheint in keiner der beiden Breiten. Im Quelltext von
> `WeekPlan` steht die Zeichenkette `"Vorlage"` **genau einmal**, sie ist also
> nicht entfernt. Wahrscheinlichste Erklärung: der Knopf hängt an einer
> Bedingung, die mit leerer `wpHistory` (die Saat füllt `meta` nicht) nicht
> erfüllt ist. **Das ist nicht gemessen** — es ist die einzige Stelle des
> Bestandsschutzes, die offen bleibt, und sie gehört vor dem Umbau geklärt.

### Home / Startseite

Nach der Korrektur K-4 gemessen (vorher war es das Chef-Dashboard).
**Vollständig, bei 390 px und bei 1440 px identisch:**

| Grundstand nennt | IST |
|---|---|
| Kopf: Sync, Theme, Benachrichtigungen, Abmelden, Neu laden, Einstellungen | ✔ (`🔄 Jetzt sync`, `Offline/Server`, `🅰️`, `🔔`, `🚪`, `🔄`, `⚙️`) |
| Schnellzugriff, 7 Stück | ✔ alle 7: `🏗️ Neues Projekt · 📋 Arbeitsscheine · 📅 Wochenplanung · 🏖️ Urlaub beantragen · 🚐 Fahrzeuge · 📊 Auswertungen · ⛽ Tanken` |
| Kacheln, 8 Stück | ✔ alle 8 als `[role=button][aria-label]`: `Projekte aktiv · Scheine offen · Fahrzeuge · Werkzeugwert · Abwesenheiten · Monatsabrechnung · Material — zur Bestellung · Bautagebuch` |
| Baustellen-Karten + „Alle →" | ✔ (2 Karten aus der Saat, `Alle →` zweimal) |
| Bottom-Bar: Home · Baustelle · Zeit · Fuhrpark · Mehr | ✔ genau diese fünf |

Rohzahlen: 37 Knöpfe (390) · 52 (1440), 0 Felder, 0 Auswahlfelder.
Werkzeugwert `€4 985 / 6 Geräte` statt `16 490 € / 296 Geräte` — das ist die
Saat, nicht die App.

### Arbeitsschein bearbeiten

**Der Grundstand kennt diese Ansicht nicht.** Er führt die Seite
*Arbeitsscheine* (Liste), nicht das Bearbeitungsformular. Die folgende
Aufnahme ist deshalb ein **neuer Grundstand für diese Ansicht** und muss in
`GRUNDSTAND_UI_v3.9.930.md` nachgetragen werden, sonst hat der Umbau hier
keine Abnahmegrundlage.

Erreicht über den Deep-Link `window.__asOpenId` (v3.9.489, derselbe Weg, den
das Chef-Portal benutzt), belegt über `.as-form-grid` **und** einen
Speichern-Knopf.

Mitgemessen, weil oberhalb des Formulars sichtbar, und **deckungsgleich mit
dem Grundstand der Liste**:

* **11 Statuskacheln**: Gesamt · Offen (alle) · aufgenommen · freigegeben ·
  in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt ·
  storniert · Fertig (alle) — **alle 11 ✔**
* **4 Unterreiter**: Liste · QR Scan · Kalender · Dispo ✔
* `📊 OFFA Excel` ✔

Das Formular selbst, in **beiden** Breiten gleich:

* **22 Eingabefelder / Textbereiche.** Platzhalter: `Uhrzeit`, `z.B. 03:00`,
  `z.B. 01:30` (2×), `Was wurde erledigt?`,
  `Interne Notizen, Anmerkungen...`, `Neuer Punkt… (Enter)`,
  `Kommentar… (@Name = Mention, Ctrl+Enter = Senden)`; dazu `date`/`time`-Felder.
* **4 Auswahlfelder** mit zusammen **21 Optionen**:
  Monteur (3) · Priorität (6: aufgeschoben, niedrig, normal, hoch, sehr hoch,
  FIXTERMIN) · Scheinstatus (8) · Verrechnung (4: —, verrechenbar, nicht
  verrechenbar, Garantiefall).
* **Aktionsknöpfe**: `✕ Abbrechen` · `Verschieben` · `−`/`+` (Fahrzeit) ·
  `−`/`+` (Arbeitszeit) · `🎤` (3×) · `+ Material` · `💾 Aktualisieren` ·
  `📄 PDF` · `⊘ Storno` · `🗑️` · `✅ Speichern & PDF erstellen` ·
  `📄 Vorschau` · `+` (Checkliste) · `Senden` (Kommentar).
* **22 Feldbeschriftungen**: Kunden-Nr. · Kundenname \* · Straße · PLZ · Ort ·
  Bestätigt · Vorschlag · Dauer (hh:mm) · Monteur · Fahrzeit (hh:mm) ·
  Arbeitszeit (hh:mm) · Gesamtzeit · Störungsmelder · Durchzuführen \* 🎤 ·
  Kontakt · Notizen 🎤 · Projektnr. · Priorität · Scheinstatus ·
  Auftragstyp (OFFA) · Verrechnung · Sachbearbeiter.

Rohzahlen: 44 Knöpfe / 22 Felder / 4 Auswahlfelder (390) · 59 / 22 / 4 (1440).

---

## 3. Die Befunde, mit Vorschlag

Reihenfolge nach Wirkung. Jeder Anker ist **aus der Datei geschnitten**, nicht
abgetippt; `\r\n` steht für die CRLF-Zeilenenden. Zu jedem Anker ist die Zahl
der Vorkommen im **ganzen** Dokument angegeben — steht dort 1, ist
`grep -F` eindeutig.

---

### B1 — Sieben Pixel. Die Wetterzeile auf Home. *(beide Breiten betroffen, 7 px nur bei 390)*

**Messwert.** Home 390 px: acht Textstellen bei **7 px** — der kleinste Wert
der ganzen Messreihe. `Bedeckt`, `Heiter`, `Klar`, `Bewölkt`, `💨6 💧50%`.
Bei 1440 px sind dieselben Stellen 8 bzw. 9 px — also **auch dort unter 12**.

**Ursache.** Vier bedingte Größenangaben in `HomeView`, je zweimal (Live-Block
und Zwischenspeicher-Block):

| Anker (`grep -F`, je **1×** im Dokument) | Länge |
|---|---|
| `fontSize:isMob?7:9,color:V.dm,marginTop:1}}, WMO_D[wcode]||""` | 61 |
| `fontSize:isMob?7:9,color:V.dm,marginTop:1}}, WMO_D[w.c]||""` | 59 |
| `fontSize:isMob?7:8,color:V.dm,marginTop:2}}, "💨"` | 48 |
| `fontSize:isMob?7:8,color:(_dark?COLORS.WARNING_DARK:COLORS.WARNING),marginTop:2,fontWeight` | 90 |

**Vorschlag.** In allen vier `isMob?7:…` und `isMob?9:…` der Wetterkarte auf
`UI.fMeta` (12) gehen, also z. B.
`fontSize:isMob?7:9` → `fontSize:UI.fMeta`.
**Risiko:** die Wetterkarte ist eine 7-Tage-Reihe in einer Zeile; 12 px statt
7 px macht die Spalten breiter. Deshalb **zusammen** mit B4 anfassen — dort
liegt der Grund, warum diese Karte überhaupt so gequetscht ist. Wenn die
Reihe bei 12 px nicht in 374 px passt, ist der richtige Weg **weniger Tage am
Telefon** (heute + 3) statt kleinerer Schrift, nicht beides.

---

### B2 — Vier Kopfknöpfe sind 40 px hoch und 10 px beschriftet, *weil zwei CSS-Regeln die 44-px-Hausregel schlagen*. *(nur bei 390 px; die Regeln greifen bis 600 bzw. 414 px)*

**Messwert.** Werkzeuge 390 px: `+ Neues Gerät`, `🏷️ Labels`, `📊 Excel`,
`🖨️ PDF` — je **40 px hoch** (computed `min-height: 40px`) und **10 px
Schrift**. Arbeitsschein bearbeiten 390 px: `📊 OFFA Excel`, ebenfalls 40 px.
Das sind **alle** Knopf-Tippziele unter 44 px, die bei 390 px überhaupt
gefunden wurden (4 + 1).

**Ursache — und das ist der eigentliche Befund.** Es gibt die Hausregel

```
@media (pointer: coarse), (max-width: 768px) { button, [role="button"], … { min-height: 44px !important } }
```

Sie verliert hier, obwohl sie `!important` trägt: zwei spätere Regeln haben
**höhere Spezifität** (`.header-row .mob-stack button` = 0,2,1 gegen
`button` = 0,0,1) und ebenfalls `!important`.

Anker A — **1×** im Dokument, 134 Zeichen (im `@media (max-width: 600px)`-Block):

```
.header-row .mob-stack button {\r\n    font-size: 11px !important;\r\n    padding: 8px 10px !important;\r\n    min-height: 40px !important;\r
```

Anker B — **1×** im Dokument, 174 Zeichen (im `@media (max-width: 414px)`-Block):

```
.header-row .mob-stack button {\r\n    font-size: 10px !important;\r\n    padding: 7px 8px !important;\r\n    min-height: 40px !important;\r\n    line-height: 1.15 !important;\r\n  }\r\n
```

**Vorschlag.** In **beiden** Blöcken `min-height: 40px` → `min-height: 44px`
und `font-size: 11px`/`10px` → `font-size: 12px`. Die Regeln bleiben sonst
unberührt (Padding, Zeilenhöhe).
**Risiko:** gering und benennbar. Die Knöpfe sind bei 390 px durch
`.mob-stack{flex-direction:column}` **374 px breit** und stehen
untereinander — 4 px mehr Höhe und 1–2 px mehr Schrift kosten je Knopf
4 px Höhe, bei vier Knöpfen 16 px Seitenlänge. Kein Umbruchrisiko, weil die
Breite von der Spalte kommt, nicht vom Text. **Gegenmessung:** dieselbe Sonde
noch einmal; „Tippziele (Knöpfe) < 44 px" muss in Werkzeuge 390 von 4 auf 0
und in Arbeitsschein bearbeiten 390 von 1 auf 0 gehen.

---

### B3 — Die fünf Icon-Reiter in Werkzeuge: bestätigt, und der billigste Fix kostet kein Pixel. *(390 px: keine Beschriftung; 1440 px: Beschriftung da, title/aria fehlt in beiden)*

**Messwert.** Bei 390 px tragen **0 von 5** Reitern Text; bei 1440 px **5 von
5**. `title` und `aria-label` fehlen in **beiden** Breiten. Genau der Stand aus
`docs/WERKZEUG_REITER_VORARBEIT.md` §5, jetzt unabhängig nachgemessen. Höhe
44 px, die Reiterzeile rollt nicht quer.

**Ursache.** `, t.i, " " , isMob?"":t.l)` — **Achtung, dieser Text kommt
2× im Dokument vor**, einmal in der Zeiterfassung, einmal in Werkzeuge. Der
eindeutige Anker für Werkzeuge ist die Farbe: `color:sub===t.id?"#d97706":V.dm`
(**1×**, 31 Zeichen) — `#d97706` ist die Werkzeug-Farbe aus `_allTabs`.

**Vorschlag.** Dem Reiterknopf `title: t.l` und `'aria-label': t.l`
mitgeben. Die Beschriftung **existiert schon** im Objekt (`l`), es wird kein
Wort erfunden und nichts umbenannt — damit bleibt der Bestandsschutz-Zusatz
(„nicht angefasst, nicht umbenannt, nicht entfernt, bis der Zweck geklärt
ist") gewahrt, denn der Zweck ist in der Vorarbeit geklärt.
**Risiko: null sichtbare Änderung.** Kein Pixel bewegt sich, die
Bedeutung ist nur nicht mehr allein im Emoji.
**Gegenmessung:** „nur Symbol, ohne title/aria" muss in Werkzeuge von 5 (390)
bzw. 6 (1440) auf 0 bzw. 1 fallen — die verbleibende 1 ist B5.

---

### B4 — Home rollt bei 390 px quer, 70 px. Die Regel im Wortlaut kann das nicht sehen. *(nur bei 390 px; bei 1440 px kein Roller)*

**Messwert.** `div#root > div.app-shell > div.app-col > div.main-pad`:
**scrollWidth 460 gegen clientWidth 390** — 70 px waagrecht zu viel.
`document.scrollingElement.scrollWidth` ist dabei **390**, also genau der
Fensterwert: die Regel, wie sie formuliert ist, bleibt grün.
Dieselbe Stelle erzeugt zwei der fünf Beschnittbefunde: zwei `div` mit
**374 px Kasten und 452 px Inhalt** (78 px fehlen, `text-overflow: clip`).
Auf **allen anderen sieben Läufen** gibt es keinen waagrechten Roller.

**Ursache, gemessen und nicht geraten.**

* Verfügbar im Inhalt: **374 px** (390 − 8 − 8 `.main-pad`-Padding).
* Der Abschnittsrahmen `display:grid; grid-template-columns:1fr; gap:14px`
  ist **452 px** breit — ein `1fr`-Track ist `minmax(auto, 1fr)`, und das
  `auto`-Minimum ist die **min-content-Breite des Kindes**. Der Track wächst
  also über den Behälter hinaus.
* Das breiteste Kind ist die Karte **„👷 Team"** mit 452 px
  (`min-width: auto`). Darin eine Reihe
  `display:flex; flex-wrap:wrap; gap:8px` mit drei Kacheln je
  `flex: 1 1 130px; min-width: 120px` → gemessen 3 × 133 px + 2 × 8 px
  = 415 px, plus 2 × 18 px Kartenpolster und Rahmen = **452 px**. Die drei
  Kacheln **wrappen nicht**, weil der Track ihnen den Platz gibt.
* `body{overflow-x:hidden}` verhindert, dass das Dokument quer rollt; darum
  ist der Überschuss **teils gerollt (in `.main-pad`), teils abgeschnitten**.

**Im Bild zu sehen, nicht nur in der Zahl:** `screenshots/b3_home_390.png`
zeigt die dritte Team-Kachel rechts angeschnitten —
„Bernade… Wieshof… Prandtn… Monteu…". Dieselbe Kante schneidet in der Liste
darüber die Datumsspalte ab („21.9.2…"). Das ist der sichtbare Teil derselben
70 px.

Anker:

| Zweck | Anker (`grep -F`) | Vorkommen | Länge |
|---|---|---|---|
| der Grid-Rahmen | `gridTemplateColumns:isMob?"1fr":"1fr 1fr",gap:14}}\r\n\r\n        /* ═══ ACTIVE PROJECTS ═══ */` | **1×** | 91 |
| die Team-Kachel | `flex:"1 1 130px",minWidth:120,padding:12,borderRadius:10` | **1×** | 56 |

*Ohne den Kommentar ist `gridTemplateColumns:isMob?"1fr":"1fr 1fr",gap:14}}`
**4×** im Dokument — nicht als Anker benutzen.*

**Vorschlag, zwei Schritte, der erste genügt vermutlich schon.**

1. `gridTemplateColumns: isMob?"1fr":"1fr 1fr"` →
   `isMob?"minmax(0,1fr)":"minmax(0,1fr) minmax(0,1fr)"`.
   Das ist der Standardgriff für genau diesen Fall: `minmax(0,1fr)` nimmt dem
   Track das `auto`-Minimum, der Rahmen bleibt bei 374 px, und die drei
   Team-Kacheln wrappen, wie ihr `flex-wrap:wrap` es vorsieht.
2. Falls danach noch etwas übersteht: `minWidth:120` in der Team-Kachel auf
   `minWidth:isMob?104:120`. Drei Kacheln à 104 px + 2 × 8 px = 328 px passen
   in 338 px Innenmaß.

**Risiko.** Schritt 1 ist rein einschränkend und kann nichts breiter machen;
das Schlimmste, was passiert, ist ein früherer Umbruch. Schritt 2 macht die
Kachel schmaler und kann `Bernadette Wieshofer-Prandtner` abschneiden — das
ist bei 12 px Schrift ohnehin schon so und gehört zu B6.
**Gegenmessung:** dieselbe Sonde; die Zeile „quer, TATSÄCHLICH" muss auf Home
390 „kein waagrechter Roller" melden, und „Beschnitt ungewollt" muss von 5 auf
3 fallen.

---

### B5 — Symbol-Knöpfe ohne jede Beschriftung: sieben Stellen in drei Ansichten. *(je in beiden Breiten, außer wo vermerkt)*

Alle mit Köder gemessen (K3, zwei Fälle). Höhe überall ≥ 44 px bei 390 px,
das Tippziel ist also in Ordnung — es fehlt die **Bedeutung**.

| # | Ansicht / Breite | Knopf | Anker (`grep -F`) | × | Vorschlag |
|---|---|---|---|---|---|
| a | Planung, **390 und 1440** | `◀` | `()=>switchKw(Math.max(1,kw-1))` | 1 | `title`/`aria-label`: „Woche zurück" |
| b | Planung, **390 und 1440** | `▶` | `()=>switchKw(Math.min(_getMaxKW(yr),kw+1))` | 1 | „Woche vor" |
| c | Werkzeuge, **nur 1440** (6×, je Geräte­zeile) | `✏️` | `style: {...bsS(),padding:"3px 8px",fontSize:10}}, "✏️"` | 1 | `title: "Bearbeiten"` — die Tabelle hat dafür schon ein Muster: derselbe Stift in der Arbeitsschein-Liste trägt `title: "Bearbeiten"`. Zugleich `fontSize:10` → 12 |
| d | Arbeitsschein bearb., **390 und 1440** | `🗑️` | `onClick: ()=>deleteAs(editId), style: {...bdS,fontSize:11}}, "🗑️"` | 1 | `title: "Arbeitsschein löschen"`, `fontSize:11` → `UI.fKlein` (13) |
| e | Arbeitsschein bearb., **390 und 1440** | `+` (Checkliste) | `React.createElement('button',{onClick:add,style:{...bpS,padding:'7px 13px'}},'+')` in `ASChecklistPanel` | 1 | `title: "Punkt hinzufügen"` |

**Risiko: null sichtbare Änderung** bei a, b, e; bei c und d wird die Ikone
2 px größer.
**Was ausdrücklich kein Befund ist:** die Zeilenknöpfe `▲ ▼ ✕` (390) und
`▲ ▼ 🗑 ✕` (1440) in der Planungstabelle **tragen** `aria-label`
(„Zeile nach oben / nach unten / leeren / löschen") — gemessen, nicht
angenommen. Ebenso `🅰️`, `🔔`, `🚪`, `📷`, `🔄`, `⚙️`, `🎤`, `−`/`+`
(Fahrzeit/Arbeitszeit, `title: "+15 Min"`): alle mit `title`.

---

### B6 — Schrift unter 12 px ist der Regelfall, nicht die Ausnahme

**Messwert.** Anteil der sichtbaren Textstellen unter 12 px:

| Ansicht | 390 px | 1440 px | kleinster Wert |
|---|---|---|---|
| Home | **78 von 182 (43 %)** | **120 von 237 (51 %)** | 7 px (390) / 8 px (1440) |
| Werkzeuge | 60 von 101 (59 %) | 32 von 163 | 8 px |
| Planung | 50 von 133 | 43 von 234 | 8 px |
| Arbeitsschein bearb. | 45 von 140 | 43 von 156 | 8 px |

Verteilung beispielhaft Werkzeuge 390 px: 8 px ×1, 10 px ×10, **11 px ×49**,
12 px ×20, 13 px ×7, darüber 14. Der Schwerpunkt liegt also auf **11 px** —
einen Pixel unter der Grenze.

Aus dem Quelltext (`scripts/b3_bestand_quelltext.py`, Köder K1–K3 bestanden),
Stellen mit einem Wert unter 12, die nachweislich im **Code** stehen und
nicht in Kommentar oder Zeichenkette:

| Komponente | Stellen < 12 | davon bedingt (`isMob?a:b`) |
|---|---|---|
| `HomeView` | **71** | 9, darunter die vier aus B1 |
| `ArbeitsscheinView` | **63** | 3 |
| `WeekPlan` | **58** | 2 |
| `WerkzeugView` | **52** | 0 |

**Vorschlag — und hier bewusst kein Rundumschlag.** Eine CSS-Untergrenze
(`#root *{font-size:max(12px, …)}`) wäre in einer Datei mit 244 Inline-Werten
nicht abzuschätzen; sie würde Kachelzahlen und Tabellenzellen mitverschieben.
Stattdessen in drei Stufen, jede einzeln gegenmessbar:

1. **Alles unter 10 px zuerst** — das sind die Stellen, die man nicht mehr
   liest, nicht nur schwer: B1 (Wetter, 7 px), der Zähler am Sync-Knopf
   (`top:-2,right:-4,background:"#f97316",color:"#fff",fontSize:8` — **1×**,
   60 Zeichen; er steht in **allen vier** Ansichten und **beiden** Breiten im
   Bild), `fontSize:8` in `WeekPlan` (2×: „+N" hinter der dritten
   Mitarbeiter-Kachel und die Kennzeichenzeile) und in
   `ArbeitsscheinView` (1× `push_pending`-Pfeil).
   → auf `UI.fMeta` (12); beim Zähler am Sync-Knopf ist das ein Kreis mit
   einer Ziffer, 12 px kosten dort 4 px Durchmesser.
2. **Die Fußleiste, weil sie überall ist.** Ihre fünf Beschriftungen
   (`Home · Baustelle · Zeit · Fuhrpark · Mehr`) sind **10 px**, ebenso das
   Sync-/Offline-Band darüber. Anker (**1×**, 79 Zeichen):
   `React.createElement('span', { style: {fontSize:10,fontWeight:isActive?700:400}}`
   → `fontSize:UI.fMeta`. Die Leiste ist 55 px hoch bei 20 px Ikone + 10 px
   Text + 12 px Polster; 12 px Text passen in `--epk-bar-h:58px`, aber **das
   ist zu messen, nicht zu glauben** — `scripts/bottom_reserve_messen.py` ist
   dafür da, und `--epk-bar-h`/`--epk-bar-warn` müssen mitwandern, wenn die
   Leiste wächst (die Endreserve hängt an ihnen, v3.9.932).
3. **Die 11er zuletzt**, ansichtsweise, weil sie die Masse sind (49 Stellen
   allein in Werkzeuge 390) und jede davon in einer Kachel oder Tabellenzelle
   steht, deren Höhe sich mitbewegt.

**Risiko.** Stufe 1 und 2 sind eng begrenzt und je für sich messbar. Stufe 3
ist die einzige, die Layout in der Breite bewegt; sie gehört **nach** B4,
damit ein neuer Überstand nicht zwei Ursachen hat.

---

### B7 — Der Sync-/Offline-Knopf im Kopf schneidet seine eigene Beschriftung ab. *(beide Breiten, alle vier Ansichten)*

**Messwert.** In **allen acht Läufen** genau eine Beschnittstelle, immer
dieselbe: `header > div > button`, Inhalt `Offline4` bei 390 px
(**scrollWidth 48, clientWidth 44**, 4 px fehlen) und
`Offline4Server ❌` bei 1440 px (**85 / 81**), `text-overflow: clip`, also
**ohne Auslassungspunkte** — es wird stumm abgeschnitten. Die Ursache ist die
44-px-Mindestbreite aus der Hausregel gegen einen Inhalt, der 48 px braucht.

**Vorschlag.** Dem Knopf `flex-wrap` oder ein `gap:2` weniger geben, oder —
sauberer — den Inhalt bei 390 px auf die Ikone reduzieren und den Text in
`title` legen; `title` trägt er schon (`Letzter Sync …`). Es gibt dafür sogar
bereits eine Regel in derselben Datei:
`@media (max-width: 340px) { header button[title*="Letzter Sync"] { display: none !important } }`
— dieselbe Idee, nur 50 px zu spät.
**Risiko:** gering, betrifft einen Kopfknopf. **Zu klären ist, was
abgeschnitten wird** — bei 390 px sind es 4 px, das kann die Ziffer `4` des
Ausstehend-Zählers sein. Dann ist es kein Schönheitsfehler, sondern eine
verschwundene Zahl.

---

### B8 — Was gemessen wurde und in Ordnung ist (mit dem Köder, der es belegt)

Diese Punkte sind **keine** Befunde, und sie sind es nachweislich, nicht
mangels Suche:

| Regel | Ergebnis | der Köder, der angeschlagen hat |
|---|---|---|
| Verdeckung durch die Fußleiste | **0** verdeckte Bedienelemente in allen vier Ansichten bei 390 px, am **Ende** jedes Rollers gemessen (belegt: `.main-pad` 1234/1878 · 657/1301 · 2251/2895 · 3628/4272, jeweils „am Ende") | K8: ein Knopf `position:fixed` über der Leiste wurde gemeldet. Die Leiste wird gefunden (`bottom-nav`, 55 px) und ihr **Überstand von 22 px** durch das Sync-Band wird mitgerechnet — das Rechteck der Leiste allein enthält es nicht |
| Tabelle breiter als der Schirm | bei **390 px gibt es in keiner der vier Ansichten eine Tabelle** (Kartenansicht); bei 1440 px sind die zwei vorhandenen Tabellen **1398 px in 1440 px** und rollen nicht | K7: eine eingehängte 3000-px-Tabelle wurde gemeldet. Ohne ihn wäre „keine Tabelle zu breit" bei 390 px die Aussage eines Melders, der nichts zu messen hatte |
| Querrollen, 7 andere Läufe | kein waagrechter Roller | Positivkontrolle aus derselben Reihe: Home 390 px meldet `.main-pad` 460/390 (B4) |
| Emoji ohne Beschriftung auf **Home** | **0** in beiden Breiten; alle Symbolknöpfe tragen `title` | K3, zwei Fälle (`🔧` und `▲`), beide gemeldet |
| Seitenfehler | **0** in allen acht Läufen (nach Abzug der erwarteten REST-/Auth-Abbrüche) | – |

---

## 4. Was NICHT gemessen wurde — das sind keine bestandenen Fälle

1. **Der Knopf „Vorlage" in Planung.** Nicht im Bild, im Quelltext vorhanden.
   Vermutlich an `wpHistory` gebunden, das die Saat nicht füllt (`meta` wird
   nicht gesät). Die einzige offene Stelle des Bestandsschutzes.
2. **Die Rollen-Gatter.** Gefahren wurde nur `admin`. Ein Monteur sieht in
   Werkzeuge **drei** statt fünf Reiter (`checkout` an `canDo("wz_edit")`,
   `form` an `isAdmin`); `Labels` hängt an `_isVAdminWz`. Alle Befunde oben
   gelten für die Admin-Sicht.
3. **1440 px mit grobem Zeiger.** Die 29/31/9/15 Tippziele unter 44 px bei
   1440 px sind unter der Hausregel *kein* Bruch, weil sie
   `pointer: coarse` oder `max-width: 768px` verlangt. Auf einem
   Touch-Notebook oder einem Tablet im Querformat bei 1440 px trifft
   `coarse` aber zu und `max-width:768px` nicht — ob die Regel dort greift,
   ist **nicht gemessen**. Die kleinsten Werte dort wären ernst: die
   Zeilenknöpfe in der Planungstabelle sind **10 × 9,8 px** und
   `🗑` ist **10 × 8,3 px**.
4. **Das „letzte bedienbare Element".** Die Sonde nimmt es in
   **DOM-Reihenfolge**, nicht als das visuell unterste; bei Home 390 px lieferte
   das `Alle →` mit `bottom = −53`, also ein Element **oberhalb** des
   Bildschirms. Die Verdeckungsaussage selbst hängt nicht daran (sie prüft
   **alle** sichtbaren Bedienelemente gegen die Leistenzone), aber die Zeile
   „letztes Bedienelement" im JSON ist so nicht zu gebrauchen.
5. **Ob der abgeschnittene Text wichtig ist.** Bei B7 sind es 4 px, die die
   Ziffer eines Zählers sein können; bei den zwei Kundennamen auf Home
   (`GEDESAG Gemeinnuetzige Donau-Ennstaler Siedlungs-AG` 329/299 und
   `Pfarre Sankt Michael Oberoesterreich` 206/192) ist es ein bewusstes
   `text-overflow: ellipsis`. Das ist eine Entscheidung, keine Messung.
6. **Farbkontrast und Hellmodus.** Dafür ist
   `scripts/hellmodus_messen.py` da.
7. **Ob 12 px Schrift die Layouts hält.** Jeder Vorschlag in B1 und B6 ist ein
   Vorschlag **mit Gegenmessung**, nicht eine Behauptung. Die Zahlen nach der
   Änderung sind von derselben Sonde zu holen.

---

## 5. Reihenfolge, die ich vorschlagen würde

1. **B3** und **B5** — `title`/`aria-label`. Kein Pixel bewegt sich, sieben
   plus fünf Stellen, sofort gegenmessbar.
2. **B4** — `minmax(0,1fr)`. Nimmt Home das Querrollen und zwei
   Beschnittstellen; rein einschränkend.
3. **B2** — die zwei CSS-Blöcke auf 44 px / 12 px. Danach ist die Spalte
   „Tippziel < 44 px" bei 390 px in allen vier Ansichten **0**.
4. **B7** — der Kopfknopf, mit der Frage, was da abgeschnitten wird.
5. **B1** und **B6 Stufe 1** — alles unter 10 px.
6. **B6 Stufe 2** (Fußleiste, zusammen mit `--epk-bar-h`) und **Stufe 3**
   (die 11er, ansichtsweise) — erst nachdem B4 die Breite beruhigt hat.

Vor Punkt 1: **den Nachtrag „Arbeitsschein bearbeiten" in
`GRUNDSTAND_UI_v3.9.930.md` eintragen** (Abschnitt 2 dieses Berichts). Ohne
ihn hat der Umbau in dieser Ansicht keine Abnahmegrundlage — und sie ist mit
22 Feldern, 4 Auswahlfeldern und 21 Optionen die inhaltsreichste der vier.

---

### Läufe und Rohdaten

Alle acht Läufe endeten mit
`Alle Koeder haben angeschlagen - die Zahlen oben sind Messwerte.`
und Rückgabewert 0; die Rückgabewerte wurden getrennt von der Ausgabe
gelesen (keine Pipe).

```
set EPK_INDEX=_mess_stand_939.html
python scripts/b3_vier_ansichten_messen.py --json b3.json
python scripts/b3_bestand_quelltext.py --json b3_quelltext.json
python scripts/b3_home390_beschnitt.py
```

Bildschirmfotos je Ansicht und Breite: `screenshots/b3_<ansicht>_<breite>.png`.
md5 der gemessenen Datei bei Beginn und Ende:
**`f750cdcb888a46b85f8b8504abec39ea`**.
