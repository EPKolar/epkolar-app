# Werkzeug-Ansicht: die fuenf unbeschrifteten Reiter — Vorarbeit

Stand 26.09.2026 · gemessen am Quelltext von `index.html` (`function WerkzeugView(`),
nicht am Bild. Zeilennummern stehen hier absichtlich nirgends: die Datei bewegt
sich taeglich. Jede Aussage haengt an einem **String-Anker**, der sich mit
`grep -F` wiederfinden laesst.

---

## 0. Der wichtigste Befund zuerst: die Beschriftungen SIND da

Die Reiterleiste ist eine einzige Liste von Objekten mit `id`, `i` (Ikone) und
`l` (Beschriftung). Die Beschriftung existiert also im Code. Sie wird nur beim
Rendern **weggelassen**, sobald das Fenster schmaler als 600 px ist:

Anker (Ende der Reiterzeile):

```
, t.i, " " , isMob?"":t.l)
```

mit `const isMob=ww<BP_MOB;` in `WerkzeugView` und `const BP_MOB=600`.

Daraus folgt praezise:

* **ab 600 px** tragen alle fuenf Reiter sichtbaren Text (Ikone + Wort),
* **unter 600 px** bleibt nur die Ikone — und `title`/`aria-label` traegt der
  Reiterknopf in **keinem** der beiden Faelle.

Der Grundstand "fuenf Reiter ohne Text, ohne `title`, ohne `aria-label`" gilt
also fuer das Telefon. Die Bedeutung ist trotzdem **zweifelsfrei** bestimmbar,
weil sie im Objekt daneben steht und weil jeder Reiter einen eigenen
Renderzweig `sub==="<kennung>"` hat.

---

## 1. Die Tabelle

Vollstaendiger Anker der Reiterliste (eine Zeile im Quelltext):

```
[{id:"scan",i:"📷",l:"QR Scan"},{id:"liste",i:"📋",l:"Liste"},...(canDo("wz_edit",curUser)?[{id:"checkout",i:"📤",l:"Check-In/Out"}]:[]),{id:"kalib",i:"🔧",l:"Service"},...(isAdmin?[{id:"form",i:"✏️",l:editId?"Bearbeiten":"Neu"}]:[])]
```

Der Klickweg fuer alle fuenf:

```
onClick: ()=>{if(t.id==="scan")switchToScan();else{stopScan();setSub(t.id);}}
```

| # | Kennung | Emoji | Was der Reiter rendert | Anker (`grep -F`) | Vorschlag |
|---|---------|-------|------------------------|-------------------|-----------|
| 1 | `scan` | 📷 | Kamera-Panel "QR-Code scannen" mit Knopf "Kamera starten", manueller Code-Eingabe und — nach einem Treffer — der Geraetekarte samt Schnellaktionen (Ausgeben an Monteur, Zuruecknehmen, In Reparatur, Bearbeiten, Label drucken). Eigener Einstieg `switchToScan()`, der Scanner und alten Treffer zuruecksetzt. | `const switchToScan=()=>{stopScan();setScannedWz(null);setScanMsg("");setManualCode("");setSub("scan");};` und `"📷 QR-Code scannen"` | **QR-Scan** |
| 2 | `liste` | 📋 | Die Inventarliste: fuenf Filter-Chips mit Zaehlern, Suchfeld, Status- und Kategorie-Auswahl, darunter Desktop-Tabelle bzw. Mobil-Karten je Geraet mit dem Schnellknopf "Ausleihen"/"Zurueckgeben". Das ist der Startreiter (`useState("liste")`). | `{key:'kalib_faellig',label:'⚠️ Kalibrierung fällig'}` | **Liste** |
| 3 | `checkout` | 📤 | Zwei Karten nebeneinander: "Werkzeug ausgeben" (Auswahl verfuegbarer Geraete + Monteur, Knopf "Ausgeben") und "Werkzeug zuruecknehmen" (alle ausgegebenen Geraete mit "Zuruecknehmen"). Nur sichtbar mit `canDo("wz_edit",curUser)`. | `"📤 Werkzeug ausgeben"` und `"📥 Werkzeug zurücknehmen"` | **Aus-/Rueckgabe** |
| 4 | `kalib` | 🔧 | Das "Geraete-Serviceheft": ein Auswahlfeld ueber alle Geraete, danach die Service-Eintraege des gewaehlten Geraets mit "+ Service-Eintrag". Der Kommentar nennt den Block KALIBRIERUNG, die Ueberschrift auf dem Schirm ist "Geraete-Serviceheft". | `"🔧 Geräte-Serviceheft"` | **Service** |
| 5 | `form` | ✏️ | Das Erfassungs-/Bearbeitungsformular eines Geraets: Name, **Kategorie** (neun Werte), Seriennummer, Inventar-Nr. mit QR-Scan-Knopf, **Status** (sechs Werte), Zuweisung, Kalibrierdaten, Wert, Notizen, Zustandsbewertung und der Fotoblock. Ueberschrift wechselt je `editId`. Nur sichtbar mit `isAdmin`. | `editId?"✏️ Gerät bearbeiten":"🔧 Neues Gerät anlegen"` | **Geraet bearbeiten** (bzw. **Neues Geraet**, wie `l` es heute schon macht) |

Kein Reiter blieb unbestimmt. Alle fuenf haben eine Kennung, eine
Beschriftung im Code, einen eigenen Renderzweig `sub==="<kennung>"` und eine
eindeutige Ueberschrift in diesem Zweig.

---

## 2. Begruendung je Reiter — woher der Vorschlag kommt

**1 `scan` → QR-Scan.** Nicht wegen der Kamera-Ikone: der Zweig hat einen
eigenen Einstiegsweg (`switchToScan`), der sich von allen anderen Reitern
unterscheidet — er raeumt Scanner, letzten Treffer, Meldung und manuellen Code
auf. Gerendert wird ein Kamerabild mit QR-Erkennung *und* ein Feld fuer
manuelle Code-Eingabe; die Kamera ist nur ein Weg von zwei. "Scan" beschreibt
also die Sache, "Kamera" nur das Mittel. Der bestehende `l`-Wert lautet bereits
"QR Scan" — ich schlage nichts Neues vor, sondern das, was im Code steht.

**2 `liste` → Liste.** Der Zweig ist der Startwert (`useState("liste")`) und
traegt alles, was nach Bestandsuebersicht aussieht: Chips mit Zaehlern, Suche,
zwei Filter-Auswahlfelder, Tabelle bzw. Karten. Er ist der einzige Zweig, der
ueber `filtered` alle Geraete zeigt. "Liste" ist die kuerzeste richtige
Beschreibung; "Inventar" waere ebenfalls richtig, weicht aber vom bestehenden
`l` ab und wuerde den Riegel und die Nutzergewohnheit zugleich verschieben.

**3 `checkout` → Aus-/Rueckgabe.** Der Zweig enthaelt genau zwei Karten, und
beide Richtungen sind gleich gewichtet: ausgeben (`checkout`) und zuruecknehmen
(`checkin`). Der bestehende `l`-Wert "Check-In/Out" ist Englisch und dreht die
Reihenfolge gegenueber dem Schirm (dort steht Ausgeben oben). Eine deutsche
Beschriftung in Schirmreihenfolge ist naeher am Gerenderten. Wer die
bestehende Schreibweise behalten will, hat damit ebenfalls recht — das ist eine
Geschmacksfrage, keine Sachfrage.

**4 `kalib` → Service.** Hier weichen Kennung, Kommentar und Schirm
auseinander: die Kennung heisst `kalib`, der Kommentar `═══ KALIBRIERUNG ═══`,
die Ueberschrift "Geraete-Serviceheft", der `l`-Wert "Service". Gerendert wird
ein Serviceheft (Eintraege mit Datum, Art, Text), nicht die Kalibrierung
allein — Kalibrierung ist nur eine Eintragsart und wird ausserdem in den Chips
und in der KPI-Zeile separat gezaehlt. Die Beschriftung muss deshalb "Service"
heissen und nicht "Kalibrierung": sie folgt dem Gerenderten, nicht der Kennung.

**5 `form` → Geraet bearbeiten / Neues Geraet.** Der Zweig rendert das einzige
Schreibformular der Ansicht, und seine Ueberschrift wechselt schon heute mit
`editId`. Genau das macht der `l`-Wert auch (`editId?"Bearbeiten":"Neu"`). Die
Beschriftung sollte diesen Wechsel behalten — ein fester Text wie "Formular"
waere in einem der beiden Faelle irrefuehrend.

---

## 3. Was ausserdem gemessen wurde (Bestand, der nicht verletzt werden darf)

**Sechs Statuswerte**, Anker `const WZ_STATUS={verfuegbar:`:

| Schluessel | Beschriftung | Ikone |
|---|---|---|
| `verfuegbar` | Verfügbar | ✅ |
| `ausgegeben` | Ausgegeben | 📤 |
| `reparatur` | In Reparatur | 🔧 |
| `kalibrierung` | Kalibrierung fällig | 📏 |
| `verloren` | Verloren/Defekt | ❌ |
| `stillgelegt` | Stillgelegt | ⏸️ |

Sie speisen **zwei** Auswahlfelder in `WerkzeugView`: den Listenfilter
(`value: filtSt`) und das Statusfeld im Formular (`value: form.status`), beide
ueber `Object.entries(WZ_STATUS).map(([k,v])=>(React.createElement('option'`.

**Neun Kategorien**, Anker `const WZ_KAT={elektro:`: Elektrowerkzeug ⚡,
Messgeräte 📏, Handwerkzeug 🔨, Maschinen ⚙️, Sicherheit/PSA 🦺,
Verbrauchsmaterial 📦, Kabelwerkzeug 🔌, Leiter/Gerüst 🪜, Sonstiges 📎.
Ebenfalls zwei Auswahlfelder: Listenfilter (`value: filtKat`) und Formular
(`value: form.kat`).

**Fuenf Filter-Chips mit Zaehlern.** Anker `{key:'alle',label:'Alle'}`; die
Zaehler kommen aus `const cnt={alle:_wzPool.length,verfuegbar:0,ausgegeben:0,kalib_faellig:0,verloren:0};`
und werden als `chip.label+" ("+cnt+")"` gerendert. `kalib_faellig` zaehlt
ueber `_wzKalibFaellig(w)`, nicht ueber den Status — ein Geraet kann
"verfuegbar" und gleichzeitig faellig sein.

**"Ausleihen" je Geraet.** Anker `const _wzQuickBtn=(w)=>{if(!w)return null;`
mit `"📦 Ausleihen"`. Aufgerufen an **zwei** Stellen: in der Mobil-Karte
(`const _qb=_wzQuickBtn(w);`) und in der letzten Zelle der Desktop-Tabelle.
Verfuegbar + eigene Monteur-Id ⇒ "Ausleihen"; ausgegeben an mich selbst ⇒
"Zurueckgeben"; sonst `null`.

**Vier Kopfknoepfe — ihre Handler, nicht ihr Aussehen:**

| Knopf | Handler (Anker) | Wirkung |
|---|---|---|
| Neues Gerät | `onClick: openNew, style: bpS}, "+ Neues Gerät"` → `const openNew=()=>{setForm(defWz());setEditId(null);setSub("form");};` | leeres Formular, `editId=null`, Reiter `form` |
| Labels | `printLabels(_list.map(w=>({name:w.name,code:w.inventarnr,inventarnr:w.inventarnr})),"Werkzeug-Labels")` | Etikettendruck; ohne Haken `stillgelegt`/`verloren` gefiltert |
| Excel | `onClick: exportWz` → `const exportWz=()=>{` mit `genXls(` | Tabellenausgabe ueber `sorted`, nicht ueber die rohe Prop |
| PDF | `onClick: ()=>window.print(), style: xBtn("pdf")` | Druckdialog des Browsers |

Nur zwei der vier sind fuer alle sichtbar: "Neues Gerät" haengt an `isAdmin`,
"Labels" an `_isVAdminWz` (admin/PL/buero/lagerleitung).

---

## 4. Wer welche Reiter sieht

| Reiter | Bedingung |
|---|---|
| `scan`, `liste`, `kalib` | immer |
| `checkout` | `canDo("wz_edit",curUser)` — admin, projektleiter, buero, lagerleitung |
| `form` | `isAdmin` — admin, projektleiter |

Ein Monteur sieht also **drei** Reiter, ein Admin **fuenf**. Eine Messung, die
nur mit der Admin-Rolle faehrt, kann die Gatter nicht sehen; die Riegel in
`tests/test_werkzeuge_vorbereitet_v940.py` fahren die Reiterliste deshalb
zweimal durch Node — einmal mit beiden Rechten, einmal ohne.

---

## 5. Der Ist-Zustand am Schirm (`scripts/werkzeuge_probe.py`, 26.09.2026)

Gemessen mit Admin-Rolle und `monteurId=M1`, sechs gesaeten Geraeten
(zwei verfuegbar, eines ausgegeben, eines verloren, eines in Reparatur, eines
stillgelegt, eines mit ueberfaelliger Kalibrierung), REST abgeklemmt.

| | 390 x 860 | 1440 x 900 |
|---|---|---|
| Reiter | 5, **0 davon mit Text**, je 44 x 44 px, nicht querrollend | 5, **5 mit Text**, 81–135 x 44 px |
| `title` / `aria-label` | bei allen fuenf `None` | bei allen fuenf `None` |
| Reitertexte | `📷` `📋` `📤` `🔧` `✏️` | `📷 QR Scan`, `📋 Liste`, `📤 Check-In/Out`, `🔧 Service`, `✏️ Neu` |
| Statusfilter | 7 Optionen (Alle + 6) | 7 |
| Kategoriefilter | 10 Optionen (Alle + 9) | 10 |
| Formular Status / Kategorie | 6 / 9 | 6 / 9 |
| Filter-Chips | 5, Zaehler `Alle (6)`, `Verfügbar (2)`, `Ausgegeben (1)`, `Kalibrierung fällig (1)`, `Defekt (1)` | gleich |
| Ausleih-Knoepfe | 2 (ein verfuegbares Geraet = ein Knopf), 44 px | 2, 25 px |
| Abgeschnittener Text | keiner | keiner |

Damit ist der Grundstand **am Schirm belegt**: unter 600 px trägt kein Reiter
Text, und auch `title`/`aria-label` fehlen in beiden Breiten. Die Zahl der
Reiter, die Statuswerte, die Kategorien, die Chips und der Ausleih-Knopf sind
vollstaendig.

Drei Melder der Probe tragen einen Koeder und haben ihn gefangen: der
Beschnittmelder (240 Zeichen in 80 px), die Chipzahl (ein entnommener Chip
wurde als 4 statt 5 gemeldet) und die Optionszaehlung (eine entnommene Option
fiel als fehlendes „Stillgelegt" auf). Die Ausleih-Messung ist der Fall, der
beim ersten Lauf **nicht** gemessen wurde: ohne `monteurId` gibt
`_wzQuickBtn` nie einen Knopf zurueck, und „0 Knoepfe" haette wie ein
Ist-Zustand ausgesehen.

Am Rechner ist die Chip-Hoehe 27 px, am Telefon 44 px — das Tippziel gilt nur
mobil. Kein Reiter ist unter 44 px hoch.

---

## 6. Grenzen dieser Vorarbeit

* Gemessen ist der **Quelltext**. Dass ein Zweig gerendert *wird*, misst
  `scripts/werkzeuge_probe.py` am Schirm.
* Die Reihenfolge der Reiter am Schirm haengt an den Rechten: faellt
  `checkout` weg, folgt `kalib` direkt auf `liste`. Eine Beschriftung darf
  sich nicht auf die Position verlassen.
* Ob eine deutsche Beschriftung ("Aus-/Rueckgabe") der bestehenden
  englischen ("Check-In/Out") vorzuziehen ist, ist **nicht** aus dem Code
  herleitbar. Das ist die einzige offene Frage in dieser Tabelle, und sie
  betrifft die Wortwahl, nicht die Bedeutung.
