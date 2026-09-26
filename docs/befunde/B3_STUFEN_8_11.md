# B3, Stufen 8–11 — vier Ansichten gemessen, je bei 390 px UND 1440 px

Gemessen am **26.09.2026** an der eingefrorenen Kopie
`_mess_stand_942.html`, md5 **`420fb60986ede332b7fe08f66214c4c5`**
(zu Beginn und am Ende der Sitzung derselbe Wert; `index.html` wurde nicht
angefasst und nicht geschrieben).

Ansichten:

| Stufe | Ansicht | erreicht über |
|---|---|---|
| 8 | **Projektakte / Berichte** (Wochenbericht) | `.proj-shell .sidebar button[title="Berichte"]` |
| 8b | **Projektakte / Bautagebuch** | `…button[title="Bautagebuch"]` |
| 9 | **Projektakte / Material** | `…button[title="Material"]` |
| 10 | **Projektakte / Pläne** | `…button[title="Pläne"]` |
| 11 | **Arbeitsscheine / LISTE** | Fußleiste bzw. `.top-tabs`, danach Unterreiter „Liste" |

Je Ansicht **390×844** (`is_mobile`, `has_touch`, also `pointer: coarse`) und
**1440×900** (`pointer: fine`), dazu je ein eigener Lauf im **Hellmodus**
(`epk_theme='light'` bei `color_scheme: dark` im Betriebssystem — die App-Wahl
muss die OS-Wahl schlagen, v3.9.711). Rolle `admin`, `monteurId=M1`,
REST und Auth abgeklemmt. **Die orangen und Amber-Warnbänder im Bild sind
Aufbau-Artefakt und kein Befund** („4 Änderungen warten auf Sync",
„Anforderungen konnten nicht geladen werden").

Sonden:

| Datei | was sie tut |
|---|---|
| `scripts/b3_stufen_8_11_messen.py` | **neu.** Die sieben Regeln aus Stufe 4–7 (unverändert importiert) auf die fünf Ansichten, plus Beschnitt-**Einordnung**, Flächenfarbe im Hellmodus, Bestandsschutz der AS-Liste und der OFFA-Hinweis. 13 Köder. |
| `scripts/b3_vier_ansichten_messen.py` | als **Modul** benutzt: `SCHRIFT_JS`, `TIPP_JS`, `EMOJI_JS`, `QUER_JS`, `BESCHNITT_JS`, `TABELLE_JS`, `MENGEN_JS`, `VERDECKUNG_JS`, `BIS_UNTEN_JS`, `_koeder()` (K1–K8) |
| `scripts/anker_schneiden.py` | **neu.** Schneidet Anker AUS der Datei und meldet die Vorkommenzahl im ganzen Dokument. Kein abgetippter Anker in diesem Bericht. |

Alle Läufe endeten mit `Alle Koeder haben angeschlagen` und **Rückgabewert 0**;
der Rückgabewert wurde getrennt von der Ausgabe gelesen (keine Pipe).

---

## 0. Zuerst: fünf eigene Messfehler, hier behoben

Die fünf aus `B3_STUFEN_4_7.md` sind **nicht** wiederholt worden — der
Verdeckungsmelder fährt jeden Roller bis ans Ende, Tippziel und Beschriftung
liegen in zwei Töpfen, der Querroll-Melder sieht auf jeden Behälter statt auf
`document.scrollingElement`, der Ansichtsnachweis ist **inhaltlich** und nicht
der Klick, und der Größenzähler kennt `isMob?a:b`. Dazu **fünf neue**, jeder
hat in einem Zwischenlauf eine saubere, falsche Zahl geliefert:

**N-1 · Neun von elf Statuskacheln galten als verschwunden.**
Der erste Bestandsschutz-Zähler verglich den Kacheltext auf **Gleichheit** mit
dem Wort aus dem Grundstand. Neun der elf Kacheln tragen ihre Beschriftung
aber als `v.i+" "+v.l`, also **Emoji plus Wort** („📋 aufgenommen"). Gemeldet
wurden **4 von 11** — und damit **sieben Regressionsfehler, die keine sind**.
Jetzt wird nach Abzug aller Nicht-Buchstaben verglichen. Ergebnis: **11/11**.

**N-2 · Dieselbe Zählung fand die Wörter auch dort, wo keine Kachel ist.**
„storniert" steht auch in den Optionen des Status-Auswahlfelds und im
OFFA-Excel-Menü. Nach der Reparatur von N-1 wäre eine **fehlende** Kachel
durch eine Option „vorhanden" gewesen. Gesucht wird jetzt **im `.kpi-grid`**.

**N-3 · Sieben Sortierkriterien fehlten bei 1440 px — angeblich.**
Der Zähler kannte nur das `<select>` „Sortieren:". Das gibt es nur auf dem
Telefon; am Rechner wird über die **klickbaren Tabellenköpfe** sortiert
(`toggleSort`). Gemeldet wurde **0 von 7**, also die ganze Prüfliste als
Regression. Jetzt zählt die Sonde beide Wege und schreibt die Gleichsetzung
aus (`Termin (best.) = Bestätigt`, `Termin (vorg.) = Vorgeschl.`,
`Kunde = Kundenname`). Ergebnis: **7/7 bei beiden Breiten**
(390: 7 über das Auswahlfeld, 0 über die Kopfzeile; 1440: 0 / 7).

**N-4 · Die VPlan-Unterreiter wurden nie besucht — gemessen wurden die
Status-Chips.** Der erste Sucher nahm „die flachste Reihe aus 3–6
Geschwister-Knöpfen" und traf damit `Alle 2 · 🟢 Offen 1 · 🟢 Erledigt 1`.
Drei Zustände wurden gemessen, die keine Unterzustände sind, und
`📁 Planverwaltung` — der einzige Zustand mit der fest eingetragenen Farbe
`#0a0c14` — blieb **unbesucht**. Gesucht wird jetzt über ein Merkmal, das nur
diese Reihe hat (die Karten-Ikone U+1F5FA im ersten Eintrag).

**N-5 · Die Saat kam an, aber der Wochenbericht blieb leer.**
Die Saat aus Stufe 4–7 führt Zeiteinträge mit `project_id`. Der ODB-Mapper der
App liest `x.pid||x.p`. `VBer` filtert `e.p===pid||e.pid===pid` — und fand
nichts. Ein Wochenbericht über eine leere Menge sieht wie ein Ist-Zustand aus
und ist keiner. Die Saat führt jetzt `pid`, `p`, `w`, `date`, `stunden`, `gw`.

### Die dreizehn Köder, alle in allen Läufen angeschlagen

| Köder | Fall | Nachweis |
|---|---|---|
| K1–K8 | unverändert aus Stufe 4–7 | siehe `B3_STUFEN_4_7.md` §0. K8 **entfällt** bei 1440 px (die Fußleiste lebt in `@media(max-width:600px)`) |
| **K9 Beschnitt-Einordnung** | **zwei** Baits: (a) 80 px `overflow:hidden` mit 240 Zeichen, (b) 60 px `overflow:visible` mit langem Text | (a) als „wirklich gekürzt" (1636/80), (b) als „nur Kastenüberlauf" (305/60), **0 falsch eingeordnet**. Ein Melder, der beide „abgeschnitten" nennt, hätte recht ohne zu messen |
| **K10 OFFA-Hinweis** | die Saat setzt **genau zwei** verwaiste Scheine (S1, S2: `juprowa_id` + `juprowa_sync_at` 30 Tage alt + Status in `AS_GRP_OFFEN` + `epk_last_juprowa_pull` neuer) **und einen dritten juprowa-gebundenen, aber frischen** (S3, 1 Tag) | das Band erschien und nannte die **2**. Ohne S3 hätte ein Melder, der einfach alle juprowa-Scheine zählt, dieselbe 2 geliefert |
| **K11 Projektakte** | `.proj-shell` muss nach jedem Schritt noch stehen; die Ansicht wird **inhaltlich** belegt | in allen 20 Läufen `shell: True`, `sidebarKnoepfe: 13` |
| **K12 Flächenfarbe** | derselbe Lauf im **Dunkelmodus** muss tragende dunkle Flächen melden | 6–25 dunkle Flächen, 2–5 tragend, Hülle `rgb(15, 17, 23)`. Ohne ihn wäre „im Hellmodus nichts dunkel" die Aussage eines Melders, der keine Farbe sieht |
| **K13 nur Symbol + Zahl** | ein Knopf, dessen ganze Beschriftung `🔩7` ist | der **alte** Melder lässt ihn durch (Ziffer = Text), der **neue** fängt ihn. Genau diese Lücke trifft drei der vier Plan-Unterreiter |

---

## 1. Messwerte, alle zehn Läufe (Dunkelmodus, die sieben Regeln)

| Ansicht | Breite | Schrift < 12 px | Tippziel < 44 px | nur Symbol ohne title/aria | **ohne BUCHSTABEN** ohne title/aria | quer (Wortlaut) | quer (tatsächlich) | wirklich gekürzt | nur Kastenüberlauf | verdeckt | Tabelle > Schirm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Berichte | 390 | **29** von 82 | **0** | 3 | 3 | nein | **3 Roller** | 0 | 0 | 0 | **1** (720/390) |
| Berichte | 1440 | 29 von 100 | 30 (Zeiger fein) | 2 | 2 | nein | 1 Roller | 0 | 0 | entfällt | 0 (1164/1440) |
| Bautagebuch | 390 | **13** von 51 | **0** | 1 | 1 | nein | 2 Roller | 0 | 0 | 0 | – |
| Bautagebuch | 1440 | 14 von 69 | 28 (Zeiger fein) | 0 | 0 | nein | 1 Roller | 0 | 0 | entfällt | – |
| Material | 390 | **14** von 57 | **0** | 1 | 1 | nein | **3 Roller** | 0 | 0 | 0 | – |
| Material | 1440 | 15 von 75 | 36 (Zeiger fein) | 0 | 0 | nein | 1 Roller | 0 | 0 | entfällt | – |
| Pläne | 390 | **39** von 108 | **0** | 2 | **5** | nein | 2 Roller | 0 | 1 | 0 | – |
| Pläne | 1440 | **56** von 130 | 52 (Zeiger fein) | 0 | 0 | nein | 1 Roller | 0 | 1 | entfällt | – |
| AS-Liste | 390 | **81** von 160 | **0** | 0 | 0 | nein | **keiner** | 0 | 1 | 0 | – (keine Tabelle) |
| AS-Liste | 1440 | 74 von 170 | 39 (Zeiger fein) | 0 | 0 | nein | 1 Roller | **6** | 1 | entfällt | **1** (1507/1440) |

Zweiter Zustand, getrennt gemessen (siehe §4 „leere Grundgesamtheit"):

| Ansicht | Breite | Schrift < 12 | Tippziel < 44 | Symbol | gekürzt | Mengen |
|---|---|---|---|---|---|---|
| Material / **Warenkorb** | 390 | 27 von 107 | **0** | 1 | 0 | 46 Knöpfe, 2 Felder |
| Material / **Warenkorb** | 1440 | 35 von 125 | 40 (Zeiger fein) | 0 | 0 | 52 Knöpfe, 2 Felder |

„Tippziel < 44 px" bei **1440 px ist kein Regelbruch**: die Hausregel gilt
`@media (pointer: coarse), (max-width: 768px)`. Bei 390 px, wo sie gilt, ist
die Zahl in **allen fünf Ansichten 0** — und das ist ein Messwert, kein
blinder Fleck: K2 (Knopf 30×20 px mit `!important` gegen die Hausregel) wurde
in jedem Lauf gefunden. Der Fall „1440 px mit grobem Zeiger" bleibt offen,
siehe §6.

**Seitenfehler: 0 in allen zwanzig Läufen** (nach Abzug der erwarteten
REST-/Auth-Abbrüche).

Kleinste gemessene Werte je Ansicht:

| Ansicht | kleinster Wert | wo |
|---|---|---|
| Pläne | **9 px** (14 Stellen, beide Breiten) | Zähler-Abzeichen der Unterreiter und Ebenen, Plan-Name in der Geschoss-Pille |
| AS-Liste | **8 px** (1 Stelle, beide Breiten) | Zähler am Sync-Knopf — **bereits als B6/Stufe 1 gemeldet**, steht in allen Ansichten |
| AS-Liste | **9 px** (4 Stellen, nur 390) | die Unterreiter `Liste · QR Scan · Kalender · Dispo` |
| Berichte | **10 px** (7 Stellen, beide Breiten) | die sieben Datumszeilen im Tabellenkopf |
| Material | **10 px** (1 Stelle) | Zähler im Chip `Offen 0` |
| Bautagebuch | **11 px** | Beschriftungen der Fußleiste |

---

## 2. Bestandsschutz

### 2.1 Arbeitsscheine-Liste — die harte Prüfliste. **Bestanden, 390 und 1440.**

`docs/GRUNDSTAND_UI_v3.9.930.md` nennt für diese Seite ausdrücklich:
*„Die elf Statuswerte und die sieben Sortierkriterien sind die harte
Prüfliste dieser Seite."*

| Grundstand nennt | IST 390 | IST 1440 |
|---|---|---|
| **11 Statuskacheln** (Gesamt · Offen (alle) · aufgenommen · freigegeben · in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt · storniert · Fertig (alle)) | **11/11 ✔** | **11/11 ✔** |
| **7 Sortierkriterien** (Nummer · Erf.-Datum · Termin (best.) · Termin (vorg.) · Status · Kunde · Monteur) | **7/7 ✔** über das Auswahlfeld „Sortieren:" | **7/7 ✔** über die klickbaren Tabellenköpfe (`Nummer · Erf.-Datum · Bestätigt · Vorgeschl. · Status · Kundenname · Monteur`), zusätzlich sortierbar: `Durchzuführende Arbeiten · Priorität · Auftragstyp · SB · Projektnr.` |
| **8 Schnellfilter-Chips** (Alle · Offen · In Arbeit · Erledigt · Meine · Heute · Überfällig · Kein Monteur) | **8/8 ✔** | **8/8 ✔** |
| Suchfeld „Suche Nr, Kunde, Arbeit…" | ✔ | ✔ |
| 4 Unterreiter (Liste · QR Scan · Kalender · Dispo) | ✔ alle vier | ✔ alle vier |
| `📊 OFFA Excel` | ✔ | ✔ |

**Kein Regressionsfehler.** Rohzahlen zur Einordnung, **nicht** als
Prüfgröße (der Grundstand nennt 228 Knöpfe an 185 echten Scheinen, hier sind
es 6): 66 Knöpfe / 1 Feld / 1 Auswahlfeld (390) · 73 / 13 / 28 (1440). Die
Differenz ist die Kartenansicht gegen die Tabelle: am Rechner trägt **jede
Zeile** ein Datumsfeld und vier Inline-Auswahlfelder.

### 2.2 Die drei Projektakte-Unterseiten — **NEUER Grundstand, noch nicht abgenommen**

`GRUNDSTAND_UI_v3.9.930.md` kennt die Projektakte **überhaupt nicht** — weder
Berichte noch Material noch Pläne noch Bautagebuch. Die folgende Aufnahme ist
deshalb ein **neuer Grundstand**, und **niemand hat ihn abgenommen.** Er
gehört vor dem Umbau in `GRUNDSTAND_UI_v3.9.930.md` nachgetragen, sonst hat
der Umbau in diesen Ansichten keine Abnahmegrundlage.

**Hülle, in allen drei Unterseiten gleich (Rolle admin):**

* Sidebar (1440) bzw. Reiterzeile + „Mehr" (390): **13 Ziele** —
  `📊 Dashboard · 🗺️ Pläne · ⚠️ Mängel · 📷 Fotos · ⏱️ Zeiterfassung ·
  📄 Berichte · 📝 Formulare · ✅ Checklisten · 📋 Bautagebuch ·
  🔩 Material · 📁 Dokumente · 🔗 OFFA · 📦 Export`
* Kopf: `◀` (zurück) · PA-Nummer · Projektname · Kunde · Ort ·
  Monteur-Auswahlfeld (3 Optionen) · `📷` Schnellfoto
* nur 390: Projektkopf Zeile 2 (Name 20 px/700, Status-Pille, Kunde · Ort,
  Fortschrittsbalken mit Prozentwert), `☰` Menü
* Fußleiste 390: `.tab-bar.pf-hauptnav`, **13 App-Reiter**, 58 px hoch

**Berichte (Wochenbericht)**

* Überschrift `📄 Wochenbericht`, Untertitel `KW <n>/<jahr> — <Projekt> —
  Stunden pro Mitarbeiter & Gewerk im Wochenüberblick.`
* **2 Knöpfe**: `◀` / `▶` (Kalenderwoche zurück / vor)
* **1 Tabelle**: Spalte `Gewerk` + 7 Tagesspalten (`Mo` bis `So` mit Datum)
  + Summenspalte; Fußzeile mit Tagessummen und der Wochen-Σ
* 0 Eingabefelder, 0 eigene Auswahlfelder
* Rohzahlen: 24 Knöpfe (390) · 30 (1440) — davon 22 bzw. 28 aus der Hülle

**Bautagebuch**

* **1 Handlung**: `➕ Neuer Eintrag` (zweimal im Bild: Kopf und Leerzustand)
* Leerzustand mit Hinweistext
* 0 Eingabefelder, 0 eigene Auswahlfelder
* Rohzahlen: 24 Knöpfe (390) · 30 (1440) — **alle** aus der Hülle plus die
  zwei `➕`
* **Die Zeilen kommen vom SERVER.** In diesem Aufbau ist die Liste leer —
  siehe §4.

**Material**

* Überschrift `🔩 Material-Anforderung`, Zähler `N Anforderungen`
* **5 Unterreiter**: `🛒 Warenkorb · 📋 Verlauf · 📦 Lager · 🏪 Bestellungen ·
  ⚙ Katalog` (Voreinstellung für admin: **Lager**)
* **3 Statuschips**: `Offen N · Erledigt · Alle`
* **1 Suchfeld**: `🔍 Bestellungen suchen (z.B. "hansgrohe 32")`
* Warenkorb (zweiter Zustand): Katalog mit Kategoriekacheln, Mengenfeldern,
  Freitextfeld — 46 Knöpfe / 2 Felder (390), 52 / 2 (1440)
* Rohzahlen Lager-Reiter: 30 Knöpfe / 1 Feld (390) · 36 / 1 (1440)
* **Die Anforderungen kommen vom SERVER.** In diesem Aufbau leer — siehe §4.

**Pläne**

* **2 Kopfknöpfe**: `📤 Plan hochladen` · `📥 Export`
* **4 Unterzustände**: `🗺️ Plan-Viewer · 🎫 Alle Tickets (N) ·
  📐 Ebenen (N) · 📁 Planverwaltung (N)` — bei **390 px ohne Beschriftung**
* **Plan-Pillen** je Geschoss (`🏢 Erdgeschoss · Erdgeschoss Elektro Rev. B ·
  <Ticketzahl>`)
* **7 Ebenen-Pillen** mit Farbpunkt, Zähler und Auge:
  `⚡ Elektro · 🔥 Heizung · 🚿 Sanitär · ❄️ Klima/Lüftung · 🔧 Allgemein ·
  🧯 Brandschutz · 🧱 Baumeister`
* **3 Handlungen**: `📌 Ticket platzieren` · `🎫 Ticket-Liste` ·
  `📄 Plan-Report`
* **3 Statuschips**: `Alle N · 🟢 Offen N · 🟢 Erledigt N`
* **1 Suchfeld**: `🔍 Pin-Nr oder Titel suchen…`
* **Viewer-Werkzeugleiste, 9 Knöpfe**: `− · + · ⊡ · ↔ · ⬚ · ⛶ · 📥 · 📍 · 📌`
  (alle mit `title` — gemessen, nicht angenommen)
* Rohzahlen: 52 Knöpfe / 1 Feld (390) · 57 / 1 (1440)
* Checkbox „Alte Versionen (archiviert) anzeigen" erscheint nur, wenn es
  archivierte Pläne gibt — in dieser Saat gibt es keine, also **nicht
  gemessen**.

---

## 3. Die Befunde, mit Vorschlag

Reihenfolge nach Wirkung. Jeder Anker ist **aus der Datei geschnitten**
(`scripts/anker_schneiden.py`), nicht abgetippt; zu jedem steht die Zahl der
Vorkommen im **ganzen** Dokument — steht dort 1, ist `grep -F` eindeutig.

---

### C1 — Die Plan-Unterreiter sind bei 390 px vier Ikonen ohne jedes Wort. Drei davon rutschen am Emoji-Melder vorbei, weil ihr Zähler eine Ziffer ist. *(nur 390 px; bei 1440 px tragen alle vier Text)*

**Messwert.** Pläne bei 390 px: die vier Unterzustände stehen als
`🗺️` · `🎫3` · `📐7` · `📁2` da. **Kein `title`, kein `aria-label`, keine
Beschriftung** — gemessen, nicht gelesen: `{'text': '🗺️', 'title': None,
'aria': None, 'h': 44, 'w': 44}`. Bei 1440 px heißen dieselben Knöpfe
`🗺️ Plan-Viewer`, `🎫 Alle Tickets 3`, `📐 Ebenen 7`,
`📁 Planverwaltung 2`.

**Warum das der alte Melder nicht sieht — und das ist der zweite Teil des
Befunds.** `EMOJI_JS` fragt: *steht in der Beschriftung ein Buchstabe **oder
eine Ziffer**?* Damit gilt `🎫3` als beschriftet. Der Melder meldete für
Pläne 390 px **2**; der Melder nach BUCHSTABEN meldet **5**. Die Differenz
sind genau die drei Unterreiter mit Zähler-Abzeichen. **Eine Zahl ist keine
Bedeutung:** `🎫3` sagt „drei wovon?" und beantwortet es nicht.
Belegt durch K13 (Köder `🔩7`: alter Melder fängt ihn **nicht**, neuer
**schon**).

**Anker** (`grep -F`, **1×**, 63 Zeichen):

```
!isMob&&React.createElement('span', null, t.l), t.c!==""&&t.c>0
```

**Vorschlag.** Dem Reiterknopf `title: t.l` und `'aria-label': t.l`
mitgeben — die Beschriftung **existiert schon** im Objekt (`l`), es wird kein
Wort erfunden. Das ist derselbe Griff, mit dem v3.9.942 die fünf
Werkzeug-Reiter behoben hat (B3 aus Stufe 4–7); dort steht er jetzt im Code
und kann abgeschrieben werden.
Zusätzlich zu erwägen, aber **nicht** in einem Schritt: die Beschriftung bei
390 px stehenzulassen statt auszublenden (`!isMob&&` entfernen). Vier Pillen
mit Text passen bei 390 px nicht nebeneinander; die Reihe rollt bereits quer.
Deshalb **erst** `title`/`aria-label`, das kostet kein Pixel.
**Risiko: null sichtbare Änderung.**
**Gegenmessung:** `python scripts/b3_stufen_8_11_messen.py --nur plaene`.
Die Zeile „OHNE BUCHSTABEN ohne title/aria" muss in Pläne 390 von **5 auf 1**
fallen (die verbleibende 1 ist C2), und „nur-Symbol ohne title/aria" von
**2 auf 1**.

---

### C2 — Der Zurück-Knopf aus der Projektakte trägt kein Wort und keinen Hinweis. *(nur 390 px, alle vier Projekt-Unterseiten)*

**Messwert.** In **jeder** der vier Projekt-Unterseiten bei 390 px genau ein
Bedienelement ohne Buchstaben, ohne `title`, ohne `aria-label`: `◀` im
Projektkopf, 44×44 px. Bei 1440 px heißt derselbe Knopf in der Sidebar
`◀ Alle Projekte` — die Beschriftung existiert also, sie wird am Telefon nur
nicht gezeigt.

**Anker** (`grep -F`, **1×**, 73 Zeichen):

```
display:isMob?"flex":"none",alignItems:"center",justifyContent:"center"}}
```

**Vorschlag.** `title: "Alle Projekte"` und `'aria-label': "Alle Projekte"`.
Der Wortlaut ist **schon da** (v3.9.937 hat „Zurück" auf „Alle Projekte"
geändert, weil „Zurück" nicht sagt, wohin). 44×44 px bleiben unangetastet.
**Risiko: null sichtbare Änderung.**
**Gegenmessung:** dieselbe Sonde; „OHNE BUCHSTABEN ohne title/aria" muss in
Bautagebuch 390 und Material 390 von **1 auf 0** gehen.

---

### C3 — Der Wochenbericht ist bei 390 px eine fest 720 px breite Tabelle in einem 374 px breiten Kasten. *(nur 390 px)*

**Messwert.** Berichte 390 px: **eine** Tabelle, **720 px breit bei
innerWidth 390**. Der Behälter trägt `overflow-x: auto` und rollt
(374 sichtbar von 720) — es geht also **nichts verloren**, aber **346 px der
Tabelle sind nur über eine waagrechte Wischbewegung erreichbar**, und
„Sa/So/Summe" stehen darin. Breiteste Spalte: `Gewerk` mit 70 px, die sieben
Tagesspalten je 42 px.
Bei **1440 px** ist dieselbe Tabelle 1164 px breit und rollt nicht.

**Ursache, gemessen und nicht geraten.** Die Breite ist eine **feste Zahl**,
keine Folge des Inhalts:

Anker (`grep -F`, **1×**, 41 Zeichen):

```
width:window.innerWidth<BP_MOB?720:"100%"
```

**Der Zusammenhang, der das zu mehr als einem Schönheitsfehler macht:**
`v3.9.930` hat **zwei** quer rollende Bereiche beseitigt, weil ein quer
rollbarer Kasten die waagrechte Wischgeste **selbst verbraucht** — der
Browser rollt ihn, statt sie nach oben durchzureichen. Genau das ist hier
wieder da, in einem 374 px breiten Streifen mitten im Inhalt.

**Vorschlag, zwei Wege, der erste ist der kleinere.**

1. `720` → `"100%"` und den sieben Tagesspalten am Telefon **nur den
   Wochentag** geben statt `Mo` + Datum (das Datum steht bereits im
   Untertitel als KW). Dann passt die Tabelle in 374 px und der Roller
   verschwindet.
2. Falls die sieben Tage bei 374 px nicht lesbar bleiben: am Telefon
   **weniger Tage** zeigen (Mo–Fr, Sa/So nur wenn dort Stunden stehen) —
   das ist der gleiche Griff wie der Vorschlag zu B1 in Stufe 4–7
   („weniger Tage am Telefon statt kleinerer Schrift").

**Risiko.** Weg 1 ist rein einschränkend. Er kann Zellen enger machen; die
Gefahr ist **nicht** Verlust, sondern Umbruch — die Zellen tragen kein
`overflow:hidden` (in diesem Lauf **0 wirklich gekürzte Stellen** in
Berichte, gemessen mit K9).
**Gegenmessung:** `--nur berichte`. „Tabellen: 1, davon breiter als der
Schirm" muss bei 390 von **1 auf 0**, und in „quer, TATSAECHLICH" muss der
Roller `div.fade-in > div  374/720` **verschwinden** (die beiden übrigen
Roller sind C4 und C5).

---

### C4 — In der Projektakte ist die Fußleiste eine andere als im Rest der App, und 7 ihrer 13 Ziele liegen hinter einer waagrechten Wischbewegung. *(nur 390 px, alle vier Projekt-Unterseiten)*

**Messwert.** In jeder Projekt-Unterseite bei 390 px:
`div.tab-bar.pf-hauptnav`, **scrollWidth 976 gegen clientWidth 390** — also
**586 px waagrecht zu viel**. Darin liegen **13 App-Reiter**:
`🏠 Home · 👑 Chef · 🏗️ Projekte · 📋 Arbeitsscheine · 📅 Planung ·
⏱️ Zeiterfassung · 🏖️ Abwesenheiten · 📄 Monatsabrechnung · 🚐 Fahrzeuge ·
🛰️ Flotte · 🔧 Werkzeuge · 🚧 Bauprovisorien · ☣️ Gefahrenstoffe`.
Im Bild sind **sechs** zu sehen.

Zum Vergleich, aus **derselben Messreihe**: in der Arbeitsschein-Liste bei
390 px heißt die Leiste `.bottom-nav`, ist 55 px hoch, hat **22 px
Überstand** (das Sync-Band) und trägt **fünf** Gruppen, die **alle** sichtbar
sind (`Home · Baustelle · Zeit · Fuhrpark · Mehr`, Stufe 4–7 §2).
Dieselbe App, dieselbe Breite, **zwei verschiedene Hauptnavigationen**.

**Was ausdrücklich KEIN Befund ist:** Die Leiste **verdeckt nichts**.
Gemessen am Ende jedes Rollers: `0` Bedienelemente in der Leistenzone, Höhe
58 px, Überstand 0 px, `.proj-main` bis ans Ende gefahren und das Ankommen
belegt. K8 (ein Knopf `position:fixed` über der Leiste) wurde in jedem Lauf
gemeldet. Und die Wischgeste ist bedacht: `shellNavSwipe` hängt an der
Leiste, `touchAction: "pan-y"`.

**Anker** (`grep -F`, **1×**, 48 Zeichen) — die Stelle, an der Größe und
Bauform der Einträge stehen:

```
fontSize:isMob?8:11,fontWeight:_isActive?700:500
```

*(Der inline stehende Wert **8** kommt im Bild nie an: `.tab-bar button
{ font-size: 11px !important }` aus dem `@media (max-width: 414px)`-Block
schlägt ihn. Gemessen wurden **11 px** — trotzdem unter 12, siehe C7.)*

**Vorschlag.** Hier **keine** Reparatur vorschlagen, sondern eine
**Entscheidung einholen**, und zwar vor dem Umbau: Soll die Projektakte
dieselbe Fünf-Gruppen-Leiste bekommen wie der Rest der App? Der Kommentar
an Ort und Stelle nennt den Grund, warum sie es **nicht** tut („die hängt an
`kat`, `setKat`, `moreOpen`, `setMoreOpen` und `safeKat` — Zustand, der in
`App` lebt … sie zu verdoppeln heißt zwei Wahrheiten, die driften"). Das ist
ein guter Grund gegen das **Kopieren**, aber kein Grund für **zwei
Navigationen**. Die dritte Möglichkeit — die Leiste einmal bauen und beiden
Hüllen als Bauteil geben — ist im Kommentar nicht betrachtet.
**Risiko:** hoch, das ist ein Umbau an der Navigation. Deshalb **nicht** in
diesem Durchgang.
**Gegenmessung, falls es gemacht wird:** in „quer, TATSAECHLICH" muss
`div.tab-bar.pf-hauptnav 390/976` verschwinden, und die Zahl der erreichbaren
Ziele muss **vorher und nachher gleich 13** sein (`scripts/projektakte_nav_probe.py`
fährt genau das ab).

---

### C5 — Die Material-Unterreiter rollen quer, und der fünfte ist bei 390 px nicht zu sehen. *(nur 390 px)*

**Messwert.** Material 390 px: `div.proj-main > div > div`,
**scrollWidth 467 gegen clientWidth 354** — 113 px zu viel. Es sind die fünf
Reiter `🛒 Warenkorb · 📋 Verlauf · 📦 Lager · 🏪 Bestellungen · ⚙ Katalog`;
im Bild endet die Zeile mitten in „Bestellung…", `⚙ Katalog` ist gar nicht da.
Der dritte Roller in dieser Ansicht (nach C4 und der Projekt-Reiterzeile).

Dazu die Projekt-Reiterzeile selbst, in **allen vier** Projekt-Unterseiten
bei 390 px: `scrollWidth 421/422 gegen clientWidth 390` — 31 px, breitestes
Kind 89 px (`Mängel 1`). Das ist der kleinste der drei und der einzige, der
mit einem Handgriff verschwindet.

**Vorschlag.** Beide Reihen **umbrechen statt rollen** lassen
(`flexWrap: "wrap"` statt `overflowX: "auto"`) — genau der Griff, mit dem
v3.9.930 die Chip-Leiste der Arbeitsscheine und die Kachelreihe behoben hat,
mit derselben Begründung (tote Wischzone). Kosten: eine zweite Zeile.
**Risiko:** gering; bei der Projekt-Reiterzeile ist es **ein** zusätzlicher
Umbruch von 31 px, bei den Material-Reitern zwei Zeilen statt einer.
Zu bedenken: `scripts/projektakte_nav_probe.py` prüft heute ausdrücklich
`overflowX in (auto, scroll)` und `flexWrap === 'nowrap'` für die
Reiterzeile und würde **rot** — das ist dann kein Fehler, sondern eine
Prüfung, die dem Umbau nachgezogen werden muss, **mit Begründung im Riegel**.
**Gegenmessung:** `--nur material` und `--nur berichte`; in „quer,
TATSAECHLICH" dürfen nur noch die Roller stehen, die man behalten will.

---

### C6 — In der Arbeitsschein-Tabelle bei 1440 px gehen bis zu 494 px Text verloren — mit Auslassungspunkten, also sichtbar. *(nur 1440 px; bei 390 px gibt es keine Tabelle)*

**Messwert.** AS-Liste 1440 px: **6 Zellen wirklich gekürzt**, alle in der
Spalte `Durchzuführende Arbeiten`, alle mit `overflow: hidden` und
`text-overflow: ellipsis`:

| verloren | Inhalt |
|---|---|
| **493,6 px** | „Zaehlerkasten tauschen, Hauptleitung neu zie…" |
| 349,2 px | „Stoerung Aussenbeleuchtung Stiegenhaus 2 - B…" |
| 262,3 px | „Wartung Notlichtanlage, 24 Leuchten, Batteri…" |
| 240,7 px | „Neuinstallation Weinkeller: 14 Steckdosen, 6…" |
| 173,8 px | „Blitzschutz Pruefung nach OeVE/OeNORM E 8049…" |
| 144,6 px | „Netzwerkverkabelung Schalterhalle, 18 Datend…" |

Die Tabelle ist dabei **1507 px breit in 1440 px** und rollt in einem
`overflow-x: auto`-Behälter um 109 px. Die Spalte selbst hat `minWidth: 180`
und ist gemessen 220 px breit — die breiteste von 13.

**Das ist eine Entscheidung, kein Versehen** — `ellipsis` ist gesetzt, die
Kürzung ist also sichtbar und die Zeile ist anklickbar. Gemeldet wird sie
trotzdem, weil die Spalte **das Einzige** ist, was in einer Zeile sagt,
worum es geht, und weil **alle sechs** Zeilen gekürzt sind, nicht einzelne.

Anker (`grep -F`, **1×**, 95 Zeichen):

```
minWidth:180,cursor:"pointer",userSelect:"none"}, onClick: ()=>toggleSort("arbeitsanweisungen")
```

**Vorschlag.** Der Tabelle 109 px Platz verschaffen, statt die eine
aussagekräftige Spalte zu kürzen: die Spalten `SB` und `Auftragstyp` am
Rechner unter 1600 px einklappen (beide sind read-only und stehen im
Formular), oder der Zelle `title={a.arbeitsanweisungen}` geben, damit der
ganze Text wenigstens beim Zeigen erscheint. Das Zweite kostet **kein
Pixel** und ist der Schritt für diesen Durchgang.
**Risiko:** bei `title` null. Beim Einklappen von Spalten ist zu prüfen, ob
der Bestandsschutz sie nennt — **er tut es nicht** (der Grundstand nennt für
diese Seite Statuswerte, Sortierkriterien, Filter, Suchfeld; die
Spaltenauswahl der Tabelle ist dort nicht aufgeführt). Trotzdem wäre das
Einklappen einer Spalte eine **sichtbare Handlungsänderung** (die Spalte ist
ein Sortierkriterium) und gehört Sebastian vorgelegt.
**Gegenmessung:** `--nur as_liste`. „Beschnitt: N WIRKLICH gekürzt" muss bei
1440 von **6 auf 0** gehen — und die Zeile „nur Kastenüberlauf" darf dabei
**nicht** steigen, sonst ist der Text nur woanders hin gewandert.

---

### C7 — Schrift unter 12 px: die AS-Liste ist der dichteste Fall der ganzen Messreihe, Pläne der tiefste

**Messwert.** Anteil der sichtbaren Textstellen unter 12 px:

| Ansicht | 390 px | 1440 px | kleinster Wert |
|---|---|---|---|
| **AS-Liste** | **81 von 160 (51 %)** | 74 von 170 (44 %) | **8 px** (390 und 1440) |
| **Pläne** | 39 von 108 (36 %) | **56 von 130 (43 %)** | **9 px** (14 Stellen, beide Breiten) |
| Berichte | 29 von 82 (35 %) | 29 von 100 | 10 px |
| Material (Lager) | 14 von 57 | 15 von 75 | 10 px |
| Material (Warenkorb) | 27 von 107 | 35 von 125 | 11 px |
| Bautagebuch | 13 von 51 | 14 von 69 | 11 px |

Verteilung AS-Liste 390 px: **8 px ×1**, 9 px ×4, 10 px ×23, **11 px ×53**,
12 px ×41, 13 px ×7. Der Schwerpunkt liegt wie in Stufe 4–7 auf **11 px** —
einen Pixel unter der Grenze.

**Die Stellen, die neu sind** (die 8 px am Sync-Knopf und die 11er-Masse
stehen bereits in B6 aus Stufe 4–7):

| # | Stellen | Wert | Anker (`grep -F`) | × | Länge |
|---|---|---|---|---|---|
| a | die vier Unterreiter der AS-Liste (`Liste · QR Scan · Kalender · Dispo`), **nur 390 px** | **9** | `fontSize:isMob?9:13` | **1** | 19 |
| b | Zähler-Abzeichen der Plan-Unterreiter | **9** | `!isMob&&React.createElement('span', null, t.l), t.c!==""&&t.c>0` (dieselbe Zeile wie C1) | **1** | 63 |
| c | Plan-Name in der Geschoss-Pille | **9** | `fontSize:9,opacity:.55,marginLeft:3,fontWeight:400}}, pl.name` | **1** | 61 |
| d | Ticketzahl in der Geschoss-Pille | **9** | `background:sel?V.ac:V.bd,color:sel?"#fff":V.dm,fontSize:9,fontWeight:700,fontFamily:mono}}, ptc` | **1** | 95 |
| e | Zähler in der Ebenen-Pille | **9** | `fontSize:9,fontFamily:mono,fontWeight:700}}, cnt)` | **1** | 49 |
| f | Auge in der Ebenen-Pille | **9** | `fontSize:9,opacity:.65,marginLeft:2}}, l.visible` | **1** | 48 |
| g | die sieben Datumszeilen im Wochenbericht-Tabellenkopf | **10** | `fontSize:10,fontWeight:400}}, d.toLocaleDateString` | **1** | 50 |

**Vorschlag — dieselbe Dreistufigkeit wie in Stufe 4–7, hier die passenden
Stufen:**

1. **Alles unter 10 px zuerst.** Das sind a–f, also **sechs Anker, alle
   9 px**, alle in Pläne und der AS-Liste. → `UI.fMeta` (12). Bei a ist das
   `fontSize:isMob?9:13` → `fontSize:UI.fMeta` bei 390 und 13 bleibt; die
   Reiter sind 44 px hoch und stehen in einer Zeile mit vier Einträgen —
   **das ist zu messen, nicht zu glauben**, ob 12 px dort noch in eine Zeile
   passen. Bei b–f sind es Abzeichen in Pillen: 12 px kosten dort je
   3 px Höhe.
2. **Die 10er.** Das ist g (sieben Datumszeilen) — und **g fällt mit C3
   zusammen**: wenn die Wochenbericht-Tabelle bei 390 px nicht mehr 720 px
   breit sein soll, ist das Datum im Kopf ohnehin die erste Stelle, die
   wegkann. **Beides in EINEM Schritt**, sonst hat ein neuer Überstand zwei
   Ursachen.
3. **Die 11er zuletzt**, ansichtsweise — 53 Stellen allein in der AS-Liste
   bei 390 px, dazu die Fußleiste (B6/Stufe 2 aus Stufe 4–7, und die
   `.tab-bar button { font-size: 11px !important }`-Regel aus dem
   414er-Block, die in der Projektakte greift).

**Risiko.** Stufe 1 ist eng begrenzt und je Anker gegenmessbar. Stufe 3 ist
die einzige, die Layout in der Breite bewegt; sie gehört **nach** C3 und C5.
**Gegenmessung:** dieselbe Sonde, die Spalte „Schrift < 12 px" je Ansicht und
Breite, und die Zeile „kleinste 6" im JSON.

---

### C8 — Eine fest eingetragene dunkle Fläche in Pläne, aber sie trägt den Schirm NICHT. *(beide Breiten, nur im Unterzustand „Planverwaltung")*

**Messwert, Hellmodus.** In **keiner** der fünf Ansichten gibt es im
Startzustand eine fest eingetragene dunkle Farbe im Bild — gemessen oben
**und** nach dem Rollen an jedes Rollerende, mit K12 als Positivkontrolle
(derselbe Lauf im Dunkelmodus meldet 2 bis 5 tragende dunkle Flächen).

**Im Unterzustand `📁 Planverwaltung`** der Plan-Ansicht: **zwei** Flächen
`rgb(10, 12, 20)` (= `#0a0c14`, Helligkeit **0,004**), je 372×140 px bei
390 px = **15,8 % des Schirms je Kachel**, und 377×140 px bei 1440 px =
**4,1 %**. Es sind die Vorschaubilder der Plan-Kacheln; sie skalieren mit der
Zahl der Pläne (hier zwei).

**Urteil nach der Regel aus `scripts/hellmodus_messen.py`:** geurteilt wird
nach **Anteil am Schirm ab 25 %**, nicht nach Farbe. **15,8 % je Kachel
liegt darunter** — bei zwei Kacheln übereinander sind es 31,6 %, aber das ist
eine Summe über getrennte Kästen und nicht dieselbe Aussage. **Das ist also
kein Befund nach der geltenden Schwelle, aber es ist eine feste dunkle Farbe
in einer der vier Ansichten, und der Auftrag verlangt, sie zu nennen.**

Anker (`grep -F`, **1×**, 31 Zeichen):

```
height:140,background:"#0a0c14"
```

`#0a0c14` steht **viermal** im Dokument: hier, in `PlanViewer` (Zeile mit
`flex:1,overflow:"hidden",position:"relative",background:"#0a0c14"`) und
zweimal in `VFotos`. `VFotos` ist **nicht** Gegenstand dieser vier Ansichten.
Zu `PlanViewer`: dieser Bestandteil kam in **keinem** der zwanzig Läufe ins
Bild — gerendert wird `PlanViewerCanvas`, und **genau dort ist v3.9.942 der
Nutzerbefund behoben worden** (`background: _dark?"#1a1a1a":V.bd`). Ob
`PlanViewer` überhaupt noch erreichbar ist, ist **nicht gemessen** (siehe §6).

**Vorschlag.** Dieselbe Form wie der Fix in v3.9.942:
`background:"#0a0c14"` → `background: _dark?"#0a0c14":V.bd`. Der Dunkelmodus
bleibt **bytegleich**, der Hellmodus bekommt ein vorhandenes Token statt
einer neuen Farbe, und die Kante des Vorschaubilds bleibt sichtbar.
**Risiko:** gering und eng; es betrifft die Vorschaukachel, nicht das Bild
darin.
**Gegenmessung:** `--nur plaene --hell`. In der Zeile
„Reiter 3 `📁2` … feste dunkle Farben" darf `rgb(10, 12, 20)` nicht mehr
auftauchen, und K12 muss weiter anschlagen (sonst hat die Messung aufgehört
zu messen, statt dass sich etwas geändert hat).

---

### C9 — Die `◀`/`▶` im Wochenbericht tragen keinen Hinweis. *(beide Breiten)*

**Messwert.** Berichte, beide Breiten: `◀` und `▶` (Kalenderwoche zurück /
vor), je 44 px hoch, **ohne `title`, ohne `aria-label`**. Derselbe Fall wie
B5 a/b aus Stufe 4–7 (Planung), nur in einer anderen Ansicht.

Anker (`grep -F`, **1×**, 24 Zeichen):

```
setKw(k=>Math.max(1,k-1)
```

Der Zwilling steht in derselben Zeile: `setKw(k=>Math.min(_getMaxKW(yr),k+1)`.

**Vorschlag.** `title` / `aria-label`: „Kalenderwoche zurück" bzw.
„Kalenderwoche vor".
**Risiko: null sichtbare Änderung.**
**Gegenmessung:** `--nur berichte`; „nur-Symbol ohne title/aria" muss bei
390 von **3 auf 1** (die verbleibende 1 ist C2) und bei 1440 von **2 auf 0**.

---

### C10 — Was gemessen wurde und in Ordnung ist (mit dem Köder, der es belegt)

Diese Punkte sind **keine** Befunde, und sie sind es nachweislich, nicht
mangels Suche:

| Regel | Ergebnis | der Köder, der angeschlagen hat |
|---|---|---|
| Tippziel < 44 px bei **390 px** | **0 in allen fünf Ansichten** und im Warenkorb | K2: ein Knopf 30×20 px mit `!important` gegen die Hausregel wurde in jedem Lauf gefunden (genau 1). Die drei CSS-Regeln, die die Hausregel in v3.9.942 geschlagen haben, greifen in **keiner** dieser Ansichten |
| Verdeckung durch die Fußleiste | **0** verdeckte Bedienelemente in allen fünf Ansichten bei 390 px, am **Ende** jedes Rollers gemessen (`.proj-main 953/1496 am Ende`, `.main-pad 1714/2358 am Ende`, Hülle 58 px bzw. 55 px + 22 px Überstand) | K8: ein Knopf `position:fixed` über der Leiste wurde gemeldet. Die Sonde findet **beide** Leistenformen: `.bottom-nav` (AS-Liste) und `.tab-bar.pf-hauptnav` (Projektakte) |
| Querrollen nach dem **Wortlaut** der Regel | in allen zehn Läufen „rollt nicht" — und das sagt **nichts**, weil `body{overflow-x:hidden}` diesen Vergleich in dieser App nie rot werden lässt | K5: ein 3000 px breites Kind ließ `scrollWidth` bei 390 stehen und wurde vom Rechteck-Melder als 3000 px gemeldet, abschneidender Vorfahr `html > body overflow-x:hidden`. Die echten Roller stehen unter C3/C4/C5 |
| **Beschnitt-Einordnung** | in vier der fünf Ansichten **0 wirklich gekürzte** Stellen; die einzigen Kürzungen sind die 6 Tabellenzellen aus C6 | K9, **zwei** Baits, 0 falsch eingeordnet |
| Der Sync-Knopf im Kopf (**B7 aus Stufe 4–7**) | **Die offene Frage ist beantwortet: es geht NICHTS verloren.** `Offline4` bei 390 px (48/44) und `Offline4Server ❌` bei 1440 px (85/81) laufen bei `overflow: visible` über ihren Kasten **hinaus** und werden **gezeichnet**. Die Ziffer `4` des Ausstehend-Zählers ist zu sehen | K9, Bait (b) — genau dieser Fall |
| Bestandsschutz AS-Liste | 11/11 Statuskacheln, 7/7 Sortierkriterien, 8/8 Chips, Suchfeld, 4 Unterreiter, OFFA-Excel — **bei beiden Breiten** | N-1/N-2/N-3 oben: drei Fassungen dieses Zählers haben vorher insgesamt **16 Regressionsfehler gemeldet, die keine waren** |
| Seitenfehler | **0** in allen zwanzig Läufen | – |

---

## 4. Leere Grundgesamtheit — was in diesem Aufbau NICHTS zu messen hatte

Drei Zustände haben ihre Zeilen vom **Server**, und REST wird in dieser Sonde
abgebrochen. Sie sind **gemessen, aber leer** — das ist kein Bestehen:

| Zustand | was fehlt | Folge |
|---|---|---|
| **Bautagebuch** | `btEntries` (Server) | die ganze Ansicht ist der Leerzustand: `➕ Neuer Eintrag` und ein Hinweistext. **Die Liste, die Einträge, das Bearbeitungsformular und der Druck sind NICHT gemessen.** Die Zahlen in §1 für Bautagebuch sind die Zahlen eines leeren Blatts |
| **Material / Lager** (Startreiter für admin) | `orders` (Server) | „Keine offenen Anforderungen." Deshalb wurde der Reiter **Warenkorb** zusätzlich gefahren (§1) — der nimmt seinen Inhalt aus einem eingebauten Katalog. **Verlauf, Bestellungen und Katalog sind NICHT gemessen** |
| **Pläne / archivierte Revisionen** | keine archivierten Pläne in der Saat | die Checkbox „Alte Versionen (archiviert) anzeigen" erscheint nicht und ist **nicht gemessen** |

---

## 5. Der OFFA-Hinweis in der Arbeitsschein-Liste

### 5.1 IST-Stand, gemessen

**Wo er steht.** Ganz oben im Unterreiter „Liste", **über** den
Schnellfilter-Chips, als erstes Kind von `div.epk-tab-fade[key="as-liste"]`.
Bei 390 px: `y = 675`, 374×72 px (drei Zeilen). Bei 1440 px: `y = 561`,
1400×36 px (eine Zeile).

**Was er wörtlich sagt** (gemessen, nicht abgeschrieben):

> ⚠ 2 offene(r) Schein(e) evtl. in OFFA abgeschlossen — bitte in OFFA prüfen
> (kein Feed-Update seit >7 Tagen trotz Pull; die App ändert den Status NICHT
> selbst).

Schriftgröße **12 px** (`UI.fMeta`, also am Boden, aber nicht darunter),
Rahmen `1px solid #f59e0b`, Hintergrund `rgba(245,158,11,.10)` in **beiden**
Themen gleich, Textfarbe `#fbbf24` (dunkel) / `#92400e` (hell).

**Wie er zustande kommt.** Der Zähler ist

```
const _verwaisteN=(arbeitsscheine||[]).filter(_isVerwaist).length;
```

mit `_isVerwaist(a) = window._isOffaVerwaist(a, _lastJupPull, Date.now())`
und `_lastJupPull = window.__lastJuprowaPull || localStorage
"epk_last_juprowa_pull"`. Die **reine** Funktion (v3.9.728, `#18a`,
Register-Punkt, eigener Riegel `test_offa_verwaist_v728`) verlangt **fünf**
Bedingungen, alle fünf gleichzeitig:

1. `s.juprowa_id` ist gesetzt,
2. `s.juprowa_sync_at` ist gesetzt,
3. `s.scheinstatus` liegt in `AS_GRP_OFFEN` =
   `["aufgenommen","freigegeben","in_bearbeitung","aufgeschoben"]`,
4. `now − juprowa_sync_at > OFFA_VERWAIST_TAGE·86 400 000` mit
   `OFFA_VERWAIST_TAGE = 7`,
5. `lastPullMs > syncMs` — **nach** dem letzten Sync dieses Scheins hat ein
   Pull stattgefunden, der ihn **nicht** mehr gebracht hat.

Gezeigt wird das Band nur, wenn zusätzlich `canSync` gilt
(`role ∈ {admin, projektleiter, buero}`).

**Zweite Anzeigestelle, mitgemessen:** im **Formular** eines betroffenen
Scheins steht das Abzeichen `⚠ in OFFA prüfen`, `fontSize: 10`,
Farbe `#b45309`.

**Kann man von ihm aus zu den betroffenen Scheinen gelangen? NEIN.**
Gemessen am Band selbst, alle sechs Wege geprüft:

| Frage | Messwert |
|---|---|
| `role` | `None` |
| `tabindex` | `None` |
| `cursor` | `auto` |
| `onclick`-Attribut | `nein` |
| React-`onClick`/`onKeyDown` am Knoten (`__reactProps`) | **`False`** |
| Knöpfe oder Verweise **im** Band | **`[]`** |
| Band liegt in einem Knopf | `False` |

Das Band **nennt eine Zahl und keinen Namen**, und es ist **kein Tippziel**.
Der einzige Weg zu den betroffenen Scheinen führt über **Raten**: alle
offenen Scheine durchgehen und in jedem Formular nachsehen, ob dort
`⚠ in OFFA prüfen` steht. Bei 37 offenen Scheinen (Grundstand) sind das 37
Formulare für 2 Treffer.

**Abhaken gibt es nicht.** Es gibt keinen Zustand, der „ich habe das in OFFA
geprüft" festhält. Das Band verschwindet erst, wenn OFFA von sich aus wieder
liefert oder jemand den Status von Hand ändert — und Letzteres ist genau das,
was der Satz im Band ausschließt („die App ändert den Status NICHT selbst").
**Solange nichts passiert, steht dasselbe Band jeden Tag da.** Das ist die
Form von Warnung, die man nach einer Woche nicht mehr liest.

### 5.2 Vorschlag

**Zweck:** aus „N Scheine sind vielleicht betroffen" wird „**diese** Scheine
sind es, und ich kann einzeln festhalten, dass ich sie geprüft habe".

**Drei Teile, aufeinander aufbauend. Teil 1 allein ist schon die halbe Miete.**

**Teil 1 — ein Schnellfilter-Chip `⚠ OFFA prüfen (N)`.** Damit ist der Weg
von der Warnung zu den Scheinen **ein Tipp**, und die Liste zeigt genau die
betroffenen. Zwei Anker, beide **1×** im Dokument:

*Anker 1a* — die Chip-Liste, 55 Zeichen (`\r\n` sind die CRLF-Zeilenenden):

```
{key:"keinmonteur",label:"⚠️ Kein Monteur"}\r\n          
```

→ dahinter, in derselben Aufzählung, ein neunter Eintrag
`{key:"offa",label:"⚠ OFFA prüfen"}`. Der Chip soll nur erscheinen, wenn
`_verwaisteN > 0 && canSync` — sonst steht am Telefon ein neunter Chip, der
nie etwas tut.

*Anker 1b* — die Filterbedingung in `filtered`, 56 Zeichen:

```
if(quickFilter==="keinmonteur"&&a.monteur) return false;
```

→ dahinter `if(quickFilter==="offa"&&!_isVerwaist(a)) return false;`.
`_isVerwaist` ist an dieser Stelle **im Geltungsbereich** und **vorher**
deklariert (Deklaration bei Offset 1 397 333, Verwendung bei 1 420 411) —
das ist gemessen, nicht angenommen; die ESM-/TDZ-Falle aus v3.9.142 greift
hier nicht.

**Risiko, benennbar.** Die `filtered`-`useMemo` führt `_isVerwaist` **nicht**
in ihrer Abhängigkeitsliste, und `_lastJupPull` wird bei jedem Render neu
gelesen. Folge: zwischen zwei Pulls kann die gefilterte Liste einen Takt
hinterherhängen, bis sich eine der bestehenden Abhängigkeiten ändert. Das ist
tolerierbar (dasselbe gilt heute schon für `_verwaisteN`, das **außerhalb**
jeder Memo steht), aber es gehört in den Kommentar, sonst sucht es in einem
halben Jahr jemand als Fehler.

**Teil 2 — das Band wird zum Tippziel und nennt die Nummern.**
*Anker 2* — der Anfang des Bandes, **1×**, 45 Zeichen:

```
(_verwaisteN>0&&canSync)&&React.createElement
```

Der ganze Block ist von dort an 470 Zeichen lang und endet mit
`die App ändert den Status NICHT selbst)." )`.

→ aus dem `div` wird ein Bedienelement mit
`role: "button"`, `tabIndex: 0`, `cursor: "pointer"`,
`onClick: ()=>{setQuickFilter("offa");setSub("liste");}` und dem
dazugehörigen `onKeyDown` (Enter/Space) — **genau das Muster**, das die
Statuskacheln schon benutzen (`_scrollToScheinListe(status)` setzt
`filterStatus`, setzt `sub` auf „liste" und rollt zur Liste). Es wird also
kein neues Verhalten erfunden, sondern ein vorhandenes angewandt.
Dazu im Text die **Nummern** statt nur der Zahl, gekappt bei dreien:
`AS-2401, AS-2402 und 3 weitere`. Die Nummern stehen in `a.nummer` und sind
bereits gefiltert (`(arbeitsscheine||[]).filter(_isVerwaist)`) — es braucht
nur noch, dass diese Liste **behalten** statt sofort gezählt wird:
`const _verwaiste=(arbeitsscheine||[]).filter(_isVerwaist);
const _verwaisteN=_verwaiste.length;`.

**Teil 3 — abhakbar, ohne Status und ohne DDL.**
Je genanntem Schein ein `☐`, und ein angehakter fällt aus dem Band (nicht aus
der Liste, nicht aus dem Status). Gespeichert wird **im Browser**, nach dem
Muster, das diese Seite schon hat:

```
const _asFilterSave=(k,v)=>{try{localStorage.setItem("epk_as_"+k,v||"");}catch(e){...}};
```

Also ein `epk_offa_geprueft` mit den `juprowa_sync_at`-Werten der abgehakten
Scheine (**nicht** nur der Id: kommt der Schein später doch noch einmal aus
OFFA, ändert sich `juprowa_sync_at`, und dann soll er **wieder** warnen — ein
Haken auf die reine Id würde ihn für immer stumm schalten).
`_isVerwaist` selbst bleibt **unberührt**; das Abhaken ist eine Anzeigesache
und gehört nicht in die reine Funktion, gegen die
`tests/test_offa_verwaist_v728` läuft.

**Was dieser Vorschlag ausdrücklich NICHT tut**, weil der Code es an drei
Stellen ausschließt: er ändert **keinen** Scheinstatus, er löst **keinen**
Push aus, er legt **keine** Tabelle an, und er fasst `_juprowaPush` /
`_juprowaSanitize` nicht an.

**Risiko.** Teil 1 ist ein Chip und eine Zeile Filter — rein additiv. Teil 2
macht ein `div` zum Knopf; die Höhe wächst bei 390 px um die Zeile mit den
Nummern (heute 72 px, dann ~90 px). Teil 3 bringt `localStorage` ins Spiel;
in einem privaten Fenster oder nach „Websitedaten löschen" sind die Haken
weg und das Band ist wieder voll — das ist **richtig so** und gehört in den
Kommentar.

**Gegenmessung** (`python scripts/b3_stufen_8_11_messen.py --nur as_liste`,
die Sonde misst diese Felder heute schon):

| heute | nach der Änderung |
|---|---|
| `role=None tabindex=None cursor=auto react-onClick=False` | `role=button tabindex=0 cursor=pointer react-onClick=True` |
| `Knoepfe im Band=[]` | mindestens ein Eintrag, und bei Teil 3 je Schein ein `☐` |
| Wortlaut enthält nur `2 offene(r) Schein(e)` | Wortlaut enthält **`AS-2401`** und **`AS-2402`** — die Saat setzt genau diese beiden (K10) |
| Chips 8/8 | Chips **9/9**, und ein Klick auf den neuen Chip lässt in der Liste **genau 2** Scheine übrig (Saat: S1 und S2 verwaist, S3 juprowa-gebunden aber frisch — **S3 darf NICHT auftauchen**) |
| Band steht nach Neuladen wieder da | nach dem Abhaken beider und **Neuladen** ist das Band **weg**; nach `localStorage.removeItem('epk_offa_geprueft')` und Neuladen ist es **wieder da** |

Die letzte Zeile ist die wichtigste: ein Haken, der einen Neustart nicht
überlebt, ist kein Haken, und ein Haken, der sich nicht zurücknehmen lässt,
ist eine Falle.

---

## 6. WAS NICHT GEMESSEN WURDE — das sind keine bestandenen Fälle

1. **Die drei Server-Zustände aus §4.** Bautagebuch (Liste, Formular,
   Druck), Material (Verlauf, Bestellungen, Katalog), die archivierten
   Plan-Revisionen. Alles, was diese Sonde über Bautagebuch sagt, ist über
   ein **leeres Blatt** gesagt.
2. **Die Rollen-Gatter.** Gefahren wurde nur `admin`. `_allNav` trägt
   `pm`-Rechte an 8 der 13 Projekt-Unterseiten (`plaene`, `maengel`,
   `zeiterfassung`, `formulare`, `checklisten`, `bautagebuch`, `material`,
   `offa`, `export`); ein Monteur sieht weniger. In `VPlan` sieht ein
   Monteur **nur eigene Tickets** (`_vpIsField`), in `VMaterial` hängen die
   Aktionsknöpfe an `isLager`/`_moOwner`, in `VBautag` an `_vbIsMineBt`.
   **Alle Befunde oben gelten für die Admin-Sicht.**
3. **1440 px mit grobem Zeiger.** Die 30/28/36/52/39 Tippziele unter 44 px
   bei 1440 px sind unter der Hausregel **kein** Bruch. Auf einem
   Touch-Notebook oder einem Tablet im Querformat bei 1440 px trifft
   `pointer: coarse` aber zu und `max-width: 768px` nicht. Derselbe offene
   Punkt wie in Stufe 4–7 — **in Pläne wäre er der ernsteste**: dort sind es
   52 Elemente, darunter die neun Knöpfe der Viewer-Werkzeugleiste.
4. **Ob `PlanViewer` (mit `#0a0c14`) überhaupt noch erreichbar ist.**
   In zwanzig Läufen kam er nicht ins Bild; gerendert wird
   `PlanViewerCanvas`. Ob er toter Code ist oder auf einem ungemessenen Weg
   (PDF-Pläne, Mängel-Platzierung) doch erscheint, ist **nicht gemessen**.
   Das gehört vor dem Anfassen von C8 geklärt — sonst ändert man eine Farbe
   an der falschen der beiden Stellen.
5. **Ob 12 px die Layouts halten.** Jeder Vorschlag in C7 ist ein Vorschlag
   **mit Gegenmessung**, keine Behauptung. Besonders C7/a: vier Reiter mit
   12 px in einer Zeile bei 390 px ist eine Vermutung, bis die Sonde sie
   bestätigt.
6. **Farbkontrast von TEXT.** Gemessen wurde nur die **Fläche**
   (Helligkeit der Hintergrundfarbe, gegen den Untergrund gemischt, ab
   8000 px², geurteilt ab 25 % Schirmanteil). Ob die 9-px- und
   11-px-Schriften ihren Kontrast halten, sagt diese Messung nicht.
7. **Das „letzte bedienbare Element".** Die Sonde nimmt es weiterhin in
   **DOM-Reihenfolge**, nicht als das visuell unterste. Die
   Verdeckungsaussage hängt nicht daran (sie prüft **alle** sichtbaren
   Bedienelemente gegen die Leistenzone), aber die Zeile
   „letztes Bedienelement" im JSON ist so nicht zu gebrauchen. Unverändert
   aus Stufe 4–7.
8. **Die Tastaturbedienung** und die Reihenfolge des Fokus — in keiner der
   fünf Ansichten.
9. **Der OFFA-Hinweis für die Rollen `projektleiter` und `buero`.**
   `canSync` schließt sie ein, gemessen wurde nur `admin`.

---

## 7. Reihenfolge, die ich vorschlagen würde

1. **C1, C2, C9** — `title` / `aria-label` an sechs Stellen. Kein Pixel
   bewegt sich, sofort gegenmessbar.
2. **C6, zweiter Teil** — `title` an der Zelle `Durchzuführende Arbeiten`.
   Ebenfalls kein Pixel.
3. **C8** — die feste Farbe in der Plan-Kachel, **nachdem** Punkt 4 aus §6
   geklärt ist.
4. **Der OFFA-Hinweis, Teil 1 und 2** (§5.2). Der Chip und das Tippziel sind
   das, was den Hinweis von einer Warnung zu einer Handlung macht.
5. **C5** — die zwei Reiterzeilen umbrechen statt rollen (und
   `projektakte_nav_probe.py` mit Begründung nachziehen).
6. **C3 zusammen mit C7 Stufe 2** — die Wochenbericht-Tabelle und die sieben
   Datumszeilen in **einem** Schritt.
7. **C7 Stufe 1** — die sechs 9-px-Anker.
8. **Der OFFA-Hinweis, Teil 3** (abhaken) — zuletzt, weil er als Einziger
   einen Zustand einführt.
9. **C4** — nicht anfassen, sondern Sebastian vorlegen: eine App, zwei
   Hauptnavigationen.
10. **C7 Stufe 3** — die 11er, ansichtsweise, **nach** C3 und C5.

**Vor Punkt 1:** den Nachtrag aus §2.2 (Berichte · Bautagebuch · Material ·
Pläne) in `GRUNDSTAND_UI_v3.9.930.md` eintragen **und als noch nicht
abgenommen kennzeichnen**. Ohne ihn hat der Umbau in der ganzen Projektakte
keine Abnahmegrundlage — und das sind 13 Unterseiten, von denen hier vier
gemessen sind.

---

### Läufe und Rohdaten

```
set EPK_INDEX=_mess_stand_942.html
set EPK_BREITEN=390,1440
python scripts/b3_stufen_8_11_messen.py --json b3_8_11.json
python scripts/b3_stufen_8_11_messen.py --nur plaene --hell
python scripts/anker_schneiden.py --suche "<anker>" 
```

Alle Läufe: `Alle Koeder haben angeschlagen - die Zahlen oben sind
Messwerte.`, Rückgabewert **0**, getrennt von der Ausgabe gelesen.
Bildschirmfotos: `screenshots/b3_<ansicht>_<breite>.png` (Dunkelmodus) und
`screenshots/b3_<ansicht>_<breite>_hell.png` (Hellmodus).
md5 der gemessenen Datei bei Beginn und Ende:
**`420fb60986ede332b7fe08f66214c4c5`**.
