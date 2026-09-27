# Abschlussbericht — UI-Umbau, 25./26.09.2026

**Für Sebastian. Ohne Codelektüre lesbar.** Die Commit-Liste steht in
`LAUF_UI.md`; hier steht, was der Lauf *getan* hat.

---

## 🔴 Zuerst: eine Sache kann nur du erledigen

**Stufe 0a ist offen.** Der `git add`-Riegel feuert seit über zwanzig Commits
nicht. Er ist korrekt in `.claude/settings.json` eingetragen und wurde mit
`jq -e` geprüft — aber der Einstellungswächter beobachtet `.claude/` erst,
wenn dort beim Sitzungsstart schon eine Datei lag. **Einmal `/hooks` öffnen
oder Claude Code neu starten**, dann greift er. Ich kann das nicht selbst: das
Öffnen von `/hooks` beendet den Zug.

Was dabei ungeschützt blieb: ein versehentliches `git add -A` hätte in jedem
dieser Commits fremde Dateien mitgenommen. Es ist nicht passiert — jeder
Commit nennt seine Dateien einzeln, und die Dateizahl im Ergebnis wurde
gegengelesen. Aber das war Disziplin, nicht ein Riegel.

---

## Die Funde, die keine Optik waren

### 1. Der Austritt in der Kapazitätsliste — der teuerste

Der Austritt wurde an **22 Stellen in drei Schreibweisen** gelesen. Eine davon
(`!String(m.austritt||'').trim()`) schloss **jeden mit gesetztem
Austrittsdatum** aus — auch jemanden, der erst nächsten Monat geht. Sie stand
in `_kapMont`, der Kapazitätsliste des Chef-Dashboards, und die ist seit
v3.9.898 die **einzige** Quelle der Auslastung.

Wer am 20. zum Monatsletzten kündigt, verschwand **ab dem Tag der Eintragung**
aus der Dispositionsplanung — für die zehn Arbeitstage, die er noch arbeitet.
Dieselbe Schreibweise stand in der Spaltenquelle für Inline-Anzeige, Modal und
Excel im Stundenzettel.

**Seit wann:** der Fehler steht im **ältesten Stand, den die Historie dieses
Repositorys hergibt** — `1eb4bfc`, 21.08.2026, v3.9.828. Älter lässt er sich
hier nicht datieren; die Historie von `index.html` beginnt dort (115 Commits).
Behoben in v3.9.950, alle fünf Entscheid-Stellen vereinheitlicht in v3.9.952.

### 2. `worker_projects` — alles löschen, dann neu einfügen

Die Zuweisung „welcher Mitarbeiter arbeitet an welchen Projekten" wurde mit
**einem** Auftrag geschrieben: die ganze Liste im Rumpf. Serverseitig wurde
erst **alles** für diesen Mitarbeiter gelöscht und dann neu eingefügt.

Am **ausgeführten** Code gemessen, nicht abgeleitet: Projekt A liegt am Server,
der lokale Stand kennt es nicht, jemand setzt B → Endzustand `['B']`, **A ist
weg**. Und der Verlauf `['A'] → ['A'] → [] → ['A','B']` zeigt das leere
Fenster, in dem ein Leser gar nichts sieht.

**Seit wann:** ebenfalls im ältesten Stand vom 21.08.2026 vorhanden.
Behoben in v3.9.941 — ein Auftrag je Griff, mit einem Paar und der Richtung.

### 3. Resturlaub für Ausgetretene

Die Auswahl-Pille in den Abwesenheiten zeigte unter **jedem** Namen
`193h Rest · 0K` — auch unter den Ausgetretenen. v3.9.931 hatte die
Kompaktliste, die Detailtabelle und das Excel-Blatt versorgt; **die Pille
nicht.**

Der Kommentar von v3.9.931 sagt es selbst mit denselben Worten: *„Ein Anspruch
für jemanden, der nicht mehr da ist, ist keine Historie."*

**Seit wann:** im ältesten Stand vom 21.08.2026 vorhanden; v3.9.931 hat drei
von vier Stellen behoben und diese übersehen. Behoben in v3.9.948 — der Name
bleibt (die Pille ist die Auswahl für Kalender und Krankenstände), der
Krankenstand bleibt (Historie), der Anspruch ist weg.

### 4. Archivo war eingebaut und nie wirksam

Die Schrift lag im Repository, war im `<head>` verlinkt **und** im
Offline-Vorrat des Dienstarbeiters — und wurde nicht verwendet. Grund:
`.app-shell` setzt `fontFamily` **inline**, und inline schlägt CSS.

Gefunden nicht im Quelltext, sondern mit `getComputedStyle` an der
**gerenderten** Überschrift. Im Quelltext war alles richtig.

**Seit wann:** Archivo kam in diesem Lauf herein (v3.9.933, 25.09.) und war
vom ersten Moment an unwirksam — bis es am selben Tag gemessen wurde. Im
ältesten Stand vom 21.08. gibt es die Schrift nicht.

### 5. Die stille Kappung

Text wurde **in JavaScript** gekappt, bevor er ins DOM kam: kein `overflow`,
kein `ellipsis`, kein Kasten. Ein CSS-Prüfstand kann das **grundsätzlich**
nicht finden, weil CSS nicht beteiligt ist — der Beschnitt-Melder meldete für
die Auswertungen „0 wirklich gekürzt", korrekt nach seiner Vorschrift und
trotzdem die falsche Antwort.

Zwölf Stellen kürzten Anzeigetext **ohne** Auslassungszeichen **und ohne**
Zugang zum vollen Wert. Der schlimmste Fall: der **Monteursname im Wochenplan
auf sechs Zeichen** — zwei Kollegen mit gleichem Vornamen sind dort nicht
unterscheidbar. Dazu der Projektname, der **zweimal** gekappt wurde (erst in
den Daten auf 12, dann im Diagramm auf 8), weshalb mein erster `title` nur
`DR.-GSCHMEID` trug.

**Seit wann:** die einzelnen Stellen sind älter als die Historie; die
Diagramm-Kappung (`maxChars=14`) stammt aus der Zeit vor dem 21.08.2026.
Behoben in v3.9.949 und v3.9.953.

### 6. „mobil hell ist auch sehr dunkel" — dein Befund, und er war echt

Die Fläche des Plan-Betrachters war mit `#1a1a1a` **fest eingetragen**. Der
Hellmodus konnte sie gar nicht erreichen; sie war in beiden Themen gleich
schwarz. Gemessen nach dem, was man **sieht** (Rasterabtastung):
**57,5 % des Schirms bei 390 px, 72,7 % bei 1440 px.**

**Meine erste Antwort war zu früh.** Ich hatte die Startansicht gemessen und
gemeldet, der Befund sei nicht nachstellbar — sauber gemessen und als
„Startansicht" gekennzeichnet, und trotzdem fast wertlos. Der Befund lag in
**Ansicht 31 von 31**. Behoben in v3.9.942; der Dunkelmodus ist ziffergleich
geblieben.

---

## Was gebaut, was nicht gebaut wurde

### Gebaut (16 Versionen, v3.9.939 bis v3.9.954)

| | |
|---|---|
| **939** | Wandtafel: „Stand" war die Uhr, nicht das Datenalter. Der abgebrochene fetch setzte den Fehlermarker nie — genau im häufigsten Ausfall |
| **940** | Die Schwelle 600 an 38 weiteren Stellen benannt; 44 nackte Zahlen der Seitenüberschrift in zwei Token |
| **941** | Zuweisungen als Einzelzeilen — der Datenverlust |
| **942** | Der Hellmodus-Befund; drei CSS-Regeln, die die 44-px-Hausregel durch Spezifität schlugen; fünf Icon-Reiter und sieben Symbol-Knöpfe beschriftet; Home rollte 70 px quer |
| **943** | Alles unter 10 px; Wetterkarte vier statt sieben Tage am Telefon; drei Medienmulden folgen dem Thema |
| **944** | Die 9/10/11er in drei Ansichten — WeekPlan bewusst draußen |
| **945** | Projektakte: Bedeutung statt Symbol; die 9er in Pläne |
| **946** | Ausgetretene nur mit Beitrag in den Diagrammen; acht Pfeile beschriftet (dateiweit gesucht) |
| **947** | Die andere Hälfte der bedingten Angaben; erster neuer Grundstand |
| **948** | Kein Resturlaub für Ausgetretene; Admin- und Material-Reiter brechen um |
| **949** | Die dritte Form des Beschnitts in den Diagrammen |
| **950** | Eine Regel für den Austritt |
| **951** | Schrift unter 12 px in elf weiteren Komponenten (289 Stellen) |
| **952** | Jede Entscheid-Stelle des Austritts, Grenzfall gepinnt |
| **953** | Stille Kappungen sichtbar oder erreichbar |
| **954** | Grundstand neu erhoben, Bestandsprüfung nachgezogen |

### Bewusst nicht gebaut — mit Grund

* **Die Projekt-Reiterzeile bleibt rollbar.** Dort sind es **dreizehn**
  Reiter; ein Umbruch kostet drei Zeilen auf jeder Projektseite (~120 px). Bei
  sechs bzw. fünf Reitern (Admin, Material) kostet er eine — deshalb dort ja,
  hier nein. Ein Riegel hält die Ausnahme fest, damit sie niemand für
  Vergessen hält.
* **`WeekPlan` bleibt bei kleiner Schrift.** Mit gehobener Schrift rollte
  Planung bei 1440 px 7 px quer und der Beschnitt stieg von 1 auf **13**. Am
  Telefon wäre es der größte Einzelgewinn gewesen (49 → 2) — dreizehn
  abgeschnittene Texte am Schreibtisch sind kein Preis dafür. Die Tabelle
  führt feste Spaltenbreiten; wer sie hebt, muss dort zuerst Platz schaffen.
* **Der Wochenbericht bleibt eine 720-px-Tabelle in einem 374-px-Kasten.**
  Die 720 px stammen aus einer Messung (v3.9.937: bei neun Spalten blieben der
  Summe 55 px, und „18,0" erschien als „18."). Schmaler machen heißt die
  Summenspalte zurückbrechen.
* **`VBautag` bleibt `isMob = ww < 768`.** Nicht entschieden, siehe unten.
* **Die drei Ansichten ohne Überschrift** — Gestaltungsfrage, siehe unten.
* **Das eine Bedienelement unter 44 px** ist der Leaflet-Zuschreibungslink.
  Rechtlich nötig, kein Bedienelement der App. Und der Melder wurde
  ausdrücklich **nicht** um `.leaflet-control-attribution` erleichtert: das
  wäre Blindheit auf Bestellung.
* **Kein DDL ausgeführt.** Für `worker_projects` war keines nötig — belegt,
  nicht behauptet: die Filterspalten existieren live (gemessen), und dass
  `merge-duplicates` ohne `on_conflict` durchgeht, ist gemessen.

---

## Die drei OFFA-Scheine — 🔴 nicht geliefert

**Ich habe sie nicht.** Und das ist kein Versehen, sondern eine Grenze, die
mit Köder belegt ist:

* Die Bedingungsabfrage gibt HTTP 200 und `[]`.
* **Dieselbe Abfrage ohne jede Einschränkung** (`select=nummer&limit=5`) gibt
  **auch `[]`**.
* **Zehn weitere Tabellen** (projects, users, workers, tickets, …) geben alle
  `Content-Range: */0` — null Zeilen.
* Eine erfundene Spalte gibt `42703`, eine erfundene Tabelle `PGRST205` — der
  Messweg funktioniert und meldet Fehler sauber.

`anon` sieht wegen RLS **nirgends** eine Zeile. Das `[]` heißt „mein Messweg
liefert nichts", **nicht** „null Scheine". Eine Zahl daraus zu bilden wäre
erfunden.

**Was stattdessen vorliegt** (`docs/befunde/OFFA_SCHEINE.md`): die Bedingung
wörtlich, das Schema live gemessen, und die fertige Abfrage. Es sind übrigens
**drei verschiedene OFFA-Zahlen** in der App, nicht eine:

| | Anzeige | Bedingung | nennt Scheine? |
|---|---|---|---|
| **A** | Banner in der AS-Liste: „⚠ N offene(r) Schein(e) evtl. in OFFA abgeschlossen" | `_isOffaVerwaist` | **nein** — kein `onClick`, kein Filterwert |
| **B** | Chef-Kachel „Juprowa Push-Stau: N" | `push_pending` | ja, Klick filtert |
| **C** | KPI „Push ausstehend" | `push_pending && juprowa_id` | nein |

**Der Hinweis, der warnt ohne zu nennen, ist A.** Wörtlich „nicht übertragen"
wäre aber B/C — und A und B sind völlig verschiedene Mengen. Das gehört vor
dem Bauen geklärt.

**Wichtig für die Zahl:** die letzte Teilbedingung von A liest
`localStorage["epk_last_juprowa_pull"]` — sie ist **gerätelokal**. Die
Bannerzahl ist damit **pro Gerät verschieden**, und aus der Datenbank lässt
sich nur eine Obermenge messen.

**Der kürzeste Weg zur Zahl:** die Abfrage aus Abschnitt 2.6 von
`docs/befunde/OFFA_SCHEINE.md` im Supabase-SQL-Editor fahren. Sie ist rein
lesend.

---

## Die Entscheidungen, die auf dich warten

### 1. Die drei Ansichten ohne Überschrift — drei Zeilen genügen

| Ansicht | Kandidat | Was dafür spricht |
|---|---|---|
| **Bauprovisorien** | `🚧 Bauprovisorien` (20 px, Gewicht 800) | Eindeutig. Größte und fetteste Schrift der Ansicht, steht allein in seiner Zeile, trägt den Ansichtsnamen. Umwandlung in `h2` mit `margin:0` kostet **kein Pixel**. |
| **Zeiterfassung** | `KW 39 / 2026` (18 px, 700) | Der einzige Kandidat — aber ein **Zeitraum**, kein Titel. Ihn zur Überschrift zu machen heißt: die Seite heißt „KW 39 / 2026". |
| **Flotte** | **keiner** | Im oberen Drittel gibt es überhaupt keinen Überschriftstext. Eine Überschrift wäre **neuer Text**, und welches Wort — deine Entscheidung. |

### 2. `VBautag`: `isMob = ww < 768`

Die **einzige** Stelle, an der Tabletbreite „mobil" heißt; sechs andere
Stellen mit `ww<768` nennen die Variable `isTab`. **Was daran hängt:** auf
einem Tablet rendert das Bautagebuch die **Handy**-Fassung, während der Rest
der App die Desktop-Fassung zeigt. Bei einem Formular mit viel Text kann das
gewollt sein — deshalb nicht angefasst.

### 3. Der OFFA-Hinweis

A oder B/C (siehe oben)? Und soll das Banner die Scheine **nennen** und
abhakbar sein? Heute ist es **kein Tippziel**: kein `onClick`, kein
Filterwert „verwaist". Wer es sieht, kann die gemeinten Scheine in der App
nicht auflisten — bei 37 offenen Scheinen heißt das 37 Formulare für 2 Treffer.

### 4. Zwei Hauptnavigationen in einer App

In der Projektakte hat die Fußleiste **13 Ziele**, davon 586 px hinter einer
Wischbewegung; im Rest der App sind es **fünf Gruppen**, alle sichtbar. Das
ist eine Entscheidung und kein Fehler — aber es sind zwei Systeme, die
derselbe Mensch am selben Tag bedient.

### 5. Die Arbeitsschein-Tabelle am Schreibtisch

„Durchzuführende Arbeiten" verliert bis zu **494 px**. Der ganze Text steht
jetzt im `title`, **abgeschnitten wird weiter**. Platz gäbe es nur durch
Einklappen von `SB` und `Auftragstyp` — beides Sortierkriterien, also eine
sichtbare Handlungsänderung.

---

## Meine eigenen Fehlgriffe — und was der Prüfstand gefangen hat

Nicht aus Zerknirschung. Daraus geht hervor, **welche Fehlerklassen dieser
Bestand produziert**.

### Anker, die zu weit schneiden

* Ein Anker suchte die ganze Datei statt eine Komponente und löschte die
  **Überschrift der Mitarbeiter-Ansicht**. Gefangen von der Ankerlängenprüfung
  (312 statt 115 Zeichen), zurückgeholt aus `git show HEAD:index.html`.
* Eine **Klammerzählung lief davon** und meldete für `HomeView` einen „Rumpf"
  von **1 769 509 Zeichen**; der Griff änderte **1744 Stellen** quer durch die
  Datei. Gefangen von `node_check`, zurückgenommen mit
  `git checkout -- index.html`. Danach Abgrenzung an der nächsten
  Funktionsdeklaration — **mit Obergrenze**.
* Umgekehrt: ein fremder Prüfstand nahm ein **festes Fenster von 95 000
  Zeichen**, und mein Kommentar schob einen Abschnitt hinaus. Eine
  Längengrenze ist keine Abgrenzung.
* Ein zu weites Muster (`fontSize:[789]`) zerschnitt **`fontSize:9.5`** →
  „Unexpected number". Hinter die Zahl gehört `(?![\d.])`.

### Zähler, die zu wenig finden und grün melden

* **Dreimal an einem Tag** aus einer Menge geschlossen, die den Fall nicht
  enthält: `ww` gegen `window.innerWidth` (38 Stellen übersehen, zweimal
  „keine mehr" gemeldet) · die Leisten**höhe** gemessen statt der **Breite**
  (dadurch fünf gekürzte Reiternamen erzeugt) · die kleine Zahl **links** vom
  Doppelpunkt gesucht und die **rechts** nicht gesehen.
* Eine Sonde behauptete im Schlusstext einen Fall grün, der **nie gelaufen
  war** (kein Eingabefeld gefunden).
* Eine Sonde meldete „kein Ausgetretener in der Liste" — es war eine **leere
  Grundgesamtheit**: die Standardsaat führt keinen.
* Eine Sonde behauptete etwas über „die Kopfknöpfe", während die Liste **leer**
  war.
* `bestand.py` versprach im Dateikopf, bei leerer Begriffsliste rot zu
  melden — **und tat es nicht**. Gefunden, weil der Auftrag verlangte, den
  Fall einmal zu *belegen*.

### Quelltext stimmt, Bild zeigt anderes

* **TDZ**: `_kz` vor `hoursByProject` → `Cannot access before initialization`.
  `node_check` blieb grün (es parst, es führt nicht aus). Nur der Browserlauf
  fand es.
* **Klasse ohne Regel**: `pf-hauptnav` gesetzt, die CSS-Regel nicht
  geschrieben. Der Quelltext sah richtig aus, die Leiste stand weiter oben —
  gefunden über die gemessene Lage (Mitte y=187 von 860).
* **Durchsichtig ist nicht schwarz**: meine Helligkeitsformel las
  `rgba(0,0,0,0)` als Schwarz und erzeugte einen Befund, den es nicht gab.
  Eine Ebene tiefer dasselbe: `rgba(…, 0.067)` über Weiß ist nahezu weiß.
* **Fünfmal** löste ein erklärender Kommentar seinen **eigenen** Riegel aus.
  Einmal machte eine offene Klammer im Kommentar das Klammer-Tor rot, während
  `node_check` grün blieb.

---

## Was ein Quelltext-Prüfstand grundsätzlich nicht fangen kann

Alle vier waren in diesem Lauf da — **bei grünem `node_check`**.

| | Beleg aus diesem Lauf |
|---|---|
| **TDZ** | `_kz` vor `hoursByProject`. Der Code parst fehlerfrei und wirft beim Rendern. Nur Ausführen findet das. |
| **Schrift, die nicht wirkt** | Archivo war verlinkt, im Offline-Vorrat und unbenutzt, weil `.app-shell` `fontFamily` **inline** setzt. Im Quelltext steht alles richtig. |
| **CSS-Regel, die nicht greift** | Die 44-px-Hausregel trägt `!important` und **verlor** gegen `.header-row .mob-stack button` — Spezifität 0,2,1 gegen 0,0,1. Beide Regeln stehen korrekt da. |
| **In JavaScript gekappter Text** | Kein `overflow`, kein `ellipsis`, kein Kasten. Ein CSS-Prüfstand hat nichts zu prüfen, und der Beschnitt-Melder meldete korrekt „0 wirklich gekürzt". |

Dazu eine fünfte, die der Lauf gezeigt hat: **eine Prüfung, die Anwesenheit
statt Wirkung misst**, ist grün, während der Fehler ausliefert. Deshalb ist
jeder neue Riegel dieses Laufs entweder **ausführend** (der Code wird
geschnitten und unter Node gefahren) oder er misst **am gerenderten Schirm** —
und jeder zählende hat einen **Köder**, der beweist, dass er finden *kann*.

---

# Nachtrag 26.09.2026 — die drei Entscheidungen, umgesetzt

Der Lauf war beendet. Er wurde für **genau drei Punkte** wieder geöffnet und
danach wieder geschlossen. Was hier steht, ist alles, was seit
`docs/GRUNDSTAND_UI_v3.9.954.md` passiert ist.

## Punkt 1 — VBautag hängt an der einen Mobilschwelle (v3.9.955)

**Was falsch war.** `VBautag` war die einzige Stelle der App, an der eine
Variable namens `isMob` an die **Tabletbreite** gebunden war: `ww < 768`.
Überall sonst heißt die Mobilschwelle `BP_MOB` und ist 600. Die Folge war kein
Schönheitsfehler: zwischen 600 und 767 px — ein Tablet im Hochformat — zeigte
das Bautagebuch die **Handy**-Fassung, während jede andere Ansicht derselben
App die Desktop-Fassung zeigte. Und es war eine Falle mit Ansage: wer `BP_MOB`
anfasst, ändert 28 Stellen und diese eine nicht.

**Die sechs übrigen `ww<768` bleiben.** Sie heißen `isTab` oder vergleichen
absichtlich inline, und zwei davon — `VPlan` und `VFotos` — führen `isMob` und
`isTab` in **derselben Zeile**. Das ist der Beleg, dass die beiden Schwellen
dort absichtlich verschieden sind und 768 kein vergessenes 600 ist.

Der Riegel nennt sie **einzeln mit ihrer umschließenden Ansicht**, nicht als
Obergrenze: „höchstens sechs" wäre grün geblieben, wenn eine erlaubte Stelle
verschwindet und eine unerlaubte dazukommt.

> 🔴 **Eine Korrektur am Auftrag, sichtbar statt stillschweigend.** Der Auftrag
> nannte für die erste Ausnahme `HomeView`. Gemessen liegt sie in
> `ProjectShell` (Deklaration Z15748; HomeView endet bei ProjList@15562). Die
> Liste folgt der Messung.

### Die Vorher/Nachher-Messung — und warum der erste Durchgang verworfen wurde

Weil es eine **Verhaltensänderung** ist, wurde bei 390, 640, 767 und 1440 px
vorher **und** nachher am Schirm gemessen. Vorher-Stand: `_mess_stand_954.html`,
md5 `359be144407d9b033949cbeccd866892`.

🔴 **Der erste Durchgang meldete „null Unterschiede an allen vier Breiten" — und
war wertlos.** Die Köder bei 640 und 767 px blieben **stumm**, das Urteil war
deshalb *nicht gemessen*, nicht *kein Befund*. Der Grund, aus der Datei
gelesen: **alle 29 `isMob`-Stellen in VBautag liegen im Bearbeitungsformular
oder in einer Eintragskarte.** Ohne Server ist die Eintragsliste leer, und mit
geschlossenem Formular kann die Änderung überhaupt nicht sichtbar werden. Eine
leere Grundgesamtheit, die sich als sauberes Ergebnis ausgibt — die Fehlerform
dieses Laufs, diesmal in der Messung des Umbaus selbst.

Zweiter Durchgang mit **geöffnetem Formular**: alle vier Köder schlagen an.

**Drei Stände statt zwei, und das musste so sein.** Beim Messen trug
`index.html` bereits v3.9.956 (die D9-Überschriften). 954 gegen 956 hätte zwei
Änderungen in einen Topf geworfen und die Köder bei 390/1440 entwertet. Das
Beweispaar ist deshalb **954 (`359be144`) gegen 955 (`24d8565d`)** — sie
unterscheiden sich in genau drei Zeilen. v3.9.956 (`51f140dd`) ist zusätzlich
gemessen und in allen Größen mit 955 identisch.

| Größe | 390 | 640 · v954 → v955 | 767 · v954 → v955 | 1440 |
|---|---|---|---|---|
| Knöpfe | 50 = 50 | 56 → 56 | 56 → 56 | 56 = 56 |
| Felder / Auswahl / Optionen | 5/2/10 gleich | gleich | gleich | gleich |
| **Schrift < 12 px** | 13 = 13 | **33 → 15** | **33 → 15** | 15 = 15 |
| wirklich gekürzt | 0 = 0 | 1 → 1 | 1 → 1 | 0 = 0 |
| nur Kastenüberlauf | 0 | 0 → 0 | 0 → 0 | 0 |
| Tabellen > Schirm | 0 | 0 → 0 | 0 → 0 | 0 |
| Tippziele < 44 px | 0 | 0 → 0 | 0 → 0 | 0 |

**In Worten:** bei 640 und 767 px ändert sich genau **eine** Größe, und sie wird
**besser** — 18 Textstellen verlassen den Bereich unter 12 px, weil die
Formular-Chips `fontSize: isMob?11:12` tragen. **Nichts bricht um, nichts geht
verloren:** kein Knopf und kein Feld verschwindet, keine neue Kürzung, kein
neuer Roller, kein Tippziel unter 44 px. Bei 390 und 1440 px null Unterschiede
— das war der Köder, und er hält.

Die **eine** Kürzung bei 640/767 ist **nicht** VBautag: es ist der Projektname
in der Kopfzeile der Projekt-Hülle (202 px Text in 84 px),
`overflow:hidden`+`ellipsis` — in **beiden** Ständen mit denselben Zahlen.

Die drei Formen getrennt: (1) hidden+ellipsis → 1 Stelle, in beiden Ständen
dieselbe. (2) Kastenüberlauf ohne Verlust → **0** in allen acht Aufnahmen.
(3) **in JavaScript gekappter Text → kann diese Sonde nicht sehen**, der volle
Wert steht nie im Baum. Ergebnis dafür: *nicht gemessen*, nicht 0.

## Punkt 2 — D9: Seitenüberschriften (v3.9.956)

**Fünf Ansichten, nicht drei.** Der Befund D9 nannte drei ohne `h1`/`h2`/`h3`,
weil er die dreizehn Ansichten der Stufen 12–15 gemessen hatte. Der
Schluss-Grundstand über alle 22 findet zwei weitere: **Wochenplanung** und
**Startseite**. Wieder ein Schluss aus einer Menge, die den Fall nicht enthält —
die Leitkrankheit dieses Laufs.

**Gebaut: nur Fall (a).** Bauprovisorien, und zwar in **beiden**
Seitenzuständen — die Liste (20 px) und das **Formular** (18 px). Der zweite war
nie gemessen: die Sonde hat das Formular nie geöffnet, es liegt hinter einem
Klick. Beide jetzt `h2` mit `margin:0`, **pixelneutral** (`fontSize` und
`fontWeight` bleiben inline; die einzige `h2`-Regel der Hülle verlangt
`.header-row` und `@media max-width:340px`, die übrigen stehen in
Druck-Stylesheets, die als Zeichenkette gebaut werden). Ein bedingter Titel in
einem `h2` ist die Hausform — `VBautag` macht es so.

**Nicht gebaut, Fall (c):** Wochenplanung, Zeiterfassung, Flotte, Startseite.
Der Grund je Ansicht und die Frage an Sebastian stehen in
`docs/ENTSCHEIDUNGEN-OFFEN.md` als **Nummer 14**.

**Fall (b) — oberster Panel-Titel mit Text — hat keinen einzigen Vertreter.**
Das ist ein Messergebnis, kein Versäumnis.

## Punkt 3 — SM-02: nichts gebaut, nur aufgeschrieben (v3.9.954)

`docs/BERECHTIGUNG_AUSWERTUNGEN.md`. Vier von acht Rollen haben
`auswertungen` im Standard; die Übersteuerung je Benutzer ist **zweistufig**
und nur für Administratoren. Zwei Fallen: ein Rollenwechsel schreibt
`permsOverride: null` und **löscht damit stillschweigend alle
Übersteuerungen**, und `locked` verweigert alles. Und `_canSeeVolume` ist
**rollenfest, nicht übersteuerbar** — ein Obermonteur sieht den Reiter, aber
weder Auftragsvolumen noch KV-Zuschlagreport.

---

# Was in derselben Nacht dazu gefunden wurde, ohne gebaut zu werden

## 🔴 Das Klammertor beurteilt 28 % von `index.html`

Ausgelöst durch einen eigenen Fehler: zwei Backticks in einem Kommentar — die
übliche Zitierweise dieser Datei — ließen den Streicher in
`_bracket_check.py` **375.741 Zeichen echten Code** als Template-Literal
verschlucken. Beim Nachmessen: **72,1 % der Datei werden gestrichen**, und
40,0 % gehen auf 22 Backtick-Treffer, denen deutsche Kommentar-Prosa folgt. Die
Grundlinie `() -1` ist die Restsumme, keine Aussage über die Klammern des Codes.

Das Tor ist **nicht geändert**. Vollständig mit Zahlen in
`docs/ENTSCHEIDUNGEN-OFFEN.md` **Nummer 15**; `test_klammertor_blindheit_v956`
nagelt die Blindheit fest, damit sie nicht wächst.

## 🔴 S-1: nicht zwei Bedienelemente ohne Namen, sondern 33 — gebaut in v3.9.957

> **Dieser Abschnitt stand hier zuerst als „zwei Knöpfe, nicht gebaut".** Beides
> war falsch. Er ist am 27.09. berichtigt, nicht überschrieben: was daneben lag,
> steht dabei.

Gemeldet war: `FahrzeugView` führt `☰` und `⊞` (Listen-/Kachelumschalter), beide
44×44, **`title: null, aria: null`** — bei 375, 390 **und** 1440 px. Richtig,
aber zu klein. Über die ganze Datei gemessen sind es **33**:

| | Knöpfe |
|---|---|
| Ansichtsumschalter `☰`/`⊞` | **4** — Fahrzeugverwaltung **und** Fotos |
| Schließen/Entfernen `✕` | **27** — Fotos, Zeilen, Termine, Fenster |
| Abbrechen `✕` | **2** — Tank- und Schadensdialog |

Die Sonde hatte die Fotos-Ansicht in einer anderen Gruppe gemessen und dort
nicht gemeldet; v3.9.942 („sieben Symbol-Knöpfe beschriftet") und v3.9.946
(„acht Pfeile") hatten diese Menge nie erfasst. **Wieder ein Schluss aus einer
Menge, die den Fall nicht enthält** — zum vierten Mal in diesem Lauf.

**Jeder Name ist abgelesen, keiner formuliert:** aus dem `onClick`
(`delWzPhoto` → „Foto entfernen", `delTermin` → „Termin löschen",
`setShowTank(null)` neben „💾 Speichern" → „Abbrechen") oder aus dem Text, den
derselbe Knopf im anderen Zustand trägt.

🔴 **Sechs sind Umschalter, und dort wäre ein fester Name falsch:**

```
showUp        ? "✕" : "📤 Hochladen"
sa            ? "✕" : "+ Zeile"
showAdd       ? "✕" : "+ Fahrzeug"
showNewFolder ? "✕" : "+ Neu"
showAddTermin ? "✕" : "+ Termin"
isRemoved     ? "↩" : "✕"
```

Ein fester `title:"Abbrechen"` hätte im geschlossenen Zustand „Abbrechen"
angesagt, wo „Hochladen" steht. Der Name hängt deshalb an derselben Bedingung
wie der Inhalt. Sichtbar wurde das nur, weil der **Inhalt** jedes Knopfes
gemessen wurde und nicht bloß seine Anwesenheit.

🔴 **Eine Stelle ist gar kein Knopf.** `SmokeTestPanel` führt
`(x.pass||x.ok)?"✓":"✗"` — eine **Statusanzeige** in einer Ergebniszeile. Mein
erster Zähler hat sie einem benachbarten Knopf zugeschlagen und als 34. Fund
gemeldet. Sie steht namentlich als Ausnahme mit diesem Grund, und ein eigener
Riegel wird rot, wenn ihr **Anlass** verschwindet: eine Ausnahme ohne Prüfung
wird zur stillen Erlaubnis.

**Kein Pixel Änderung.** `tests/test_symbolknoepfe_haben_namen_v957.py`,
Mutationsprobe 4 von 4 erkannt.

### Und die zweite Hälfte: 32 Emoji-Knöpfe (v3.9.958)

v3.9.957 hatte die Knöpfe mit **Emoji**-Inhalt (🖨️ ✏️ 🗑️ ✅) ausdrücklich
ausgeschlossen — sie seien eine eigene Menge. Gemessen: **150** solche
Knöpfe, 118 trugen einen Namen, **32 nicht**. Jetzt alle 150.

Ein Schirmleser sagt bei einem Emoji den Namen des **Bildes** an,
„Papierkorb" — das sagt nicht, **was** gelöscht wird. Die Namen sind aus dem
`onClick` abgelesen, der Wortschatz von den 118 bereits benannten
übernommen; ein eigener Riegel wird rot, wenn ein zweites Wort für dieselbe
Handlung dazukommt.

🔴 **Mein erster Abtaster hat gelogen, und das ist der eigentliche Fund.** Er
suchte den Knopfinhalt mit `re.search` im Umfeld nach `}, "..."` — und fand
ein **späteres** Literal, wenn der Inhalt eine Variable ist. Drei Stellen
standen damit als „namenloser Emoji-Knopf" in der Liste, deren Inhalt Text
ist: `_navBtn` (Inhalt `text`) und zwei Reiterzeilen (Inhalt `f.l`,
„Offen"/„Erledigt"). Die Liste sah vollständig und glaubwürdig aus.
Aufgefallen ist es nur, weil ich **vor dem Bauen** die drei unklarsten
Stellen im Zusammenhang gelesen habe. Die Zahl fiel von 44 auf 32.

🔴 **Zwei Rechte-Riegel wurden rot, und sie hatten nicht recht.** Die
`canDo`-Riegel für `deleteSuppOrd` und `deleteCatalog` verlangten `{`
**unmittelbar** gefolgt von `onClick:`. Meine `title`-Eigenschaft steht davor
— sie haben also die **Reihenfolge der Eigenschaften** gemessen, nicht die
Rechteprüfung. Am Quelltext nachgemessen: `canDo("material_delete",curUser)&&`
steht unverändert vor beiden Knöpfen. Gelockert genau so weit, dass andere
Eigenschaften davorstehen dürfen — höchstens 300 Zeichen und **kein**
`createElement` dazwischen, sonst könnte das Muster die Prüfung des einen
Knopfes mit dem `onClick` eines **anderen** verbinden und wäre grün, während
der Löschknopf offensteht. Dazu eine Selbstprobe — und die Selbstprobe selbst
ist geprüft: mit dem zu weiten Muster wird sie rot, mit dem engen grün.


## 🔴 Sechzehn Kommentare behaupteten vierzehn Monate lang das Gegenteil (v3.9.959)

`FINKZEIT_ENABLED` schaltet den Reiter **Monatsabrechnung**. Am 04.06.2026
hat Sebastian ihn geparkt; in **v3.9.204** ist er reaktiviert worden, und die
Fahne steht seither auf `true`. Die Kommentare sind nie nachgezogen worden.

Bis v3.9.958 sagten **sechzehn** Stellen auf dreizehn Zeilen weiter
„FINKZEIT STANDBY", „Tab geparkt", „UI-ausgeblendet" — und direkt über
`StundenzettelView`: „komplette View geparkt: diese Komponente wird nicht
mehr gerendert."

Gemessen war zur gleichen Zeit: die Fahne `true`, `"stunden"` in `_navIds`
**und** in der Reiterliste, und der Aufruf der Komponente hängt nur noch an
`hasPerm(curUser,"stunden")`. **Der Weg ist offen, der Kommentar war falsch.**

Aufgefallen war es schon einmal: ein Kommentar aus v3.9.864 hält selbst fest
„und FINKZEIT_ENABLED=true, der Tab war für alle live". Nachgezogen wurde
damals nichts. Und in dieser Sitzung ist genau das passiert, wovor es
schützen soll: ein Befund wurde wegen dieses Satzes fast falsch einsortiert
— lebender Code galt als stillgelegt.

**Nur Kommentare geändert, kein Verhalten.** Und getrennt behandelt, weil
nicht alle sechzehn falsch waren:

| | |
|---|---|
| **sieben** Behauptungen über den **heutigen** Zustand | richtiggestellt; die Geschichte bleibt drin, gelöscht wird nichts |
| **sechs** Beschriftungen des `!FINKZEIT_ENABLED`-Zweigs | behalten — ihr Text ist **für diesen Zweig** richtig. Nur der Titel „STANDBY" liest sich als Zustandsaussage und heißt jetzt „FINKZEIT-SCHALTER" |

**Der Riegel misst ein Verhältnis, keine Wortliste.** Er liest den *Wert* der
Fahne aus der Deklaration und verlangt erst dann, dass kein Kommentar das
Gegenteil behauptet. Bei `false` schweigt er — wer den Reiter wieder parkt,
wird nicht behindert. Vier Proben, alle vier richtig; die entscheidende ist
die zweite: **dieselbe Behauptung bei Fahne `false` bleibt grün.**

Und: ein **Zitat** der alten Formulierung ist keine Behauptung. Ohne diese
Unterscheidung wäre die Richtigstellung selbst rot — und am Ende hätte man
die Erklärung gelöscht statt des Fehlers. Eine eigene Probe belegt es.

### Zwei eigene Fehler, beide von fremden Riegeln gefunden

1. **Mein Changelog-Text enthielt die Phrase wieder** — und nahm damit einem
   Riegel, der die Marken zählt, seine Vorbedingung (`assert 1 >= 6`).
2. **Mein neuer Riegel ließ das durch.** Sein Zitat-Test fragte, ob im
   umgebenden Kommentar *irgendwo* vor und *irgendwo* nach der Phrase ein
   Anführungszeichen steht — und der Changelog-Kommentar ist 256.000 Zeichen
   lang mit Tausenden davon. Dort galt **jede** Phrase als zitiert. Jetzt
   werden die Zitatbereiche paarweise ausgerechnet und gefragt, ob die Phrase
   **in** einem liegt. „Irgendwo im Umfeld" statt „innerhalb" ist dieselbe
   Fehlerform wie ein Anker, der zu weit schneidet.

### Und ein Riegel, der halb recht hatte

`test_finkzeit_standby_v3991` wurde rot. Seine geschützte Eigenschaft — **jede
FinkZeit-Fläche trägt ihre eigene Marke** — ist richtig und bleibt unberührt.
Nicht recht hatte er im Wortlaut: er pinnte „STANDBY" und schrieb damit einen
Widerspruch zu seinem **eigenen** ersten Riegel fest, der `FINKZEIT_ENABLED=`
`true` verlangt. Geändert wurde nur `_MARKE`; beide Umkehrproben laufen
unverändert, weil sie gegen `_MARKE` fahren und nicht gegen einen festen Text.

## Die Projekt-Reiterzeile rollt auch am Schreibtisch

Neu gegen den Stand dieses Berichts: die Reiterzeile der Projektakte rollt
**auch bei 1440 px** waagrecht (+158 px), nicht nur am Telefon (+586 bei 390).
Die Entscheidung „bleibt rollbar, 13 Reiter wären drei Zeilen auf jeder
Projektseite" war für das Telefon begründet — für den Schreibtisch war sie nie
gemessen.

## Drei Zusagen, die die eigenen Beschlüsse nicht hergeben

Die Schlussmessung hat die sieben Zusagen des Laufs geprüft. **Vier halten**
(Tippziele, Fußleisten-Verdeckung, feste dunkle Farben im Hellmodus,
waagrechter Roller außerhalb der Projekt-Hülle — jede mit angeschlagenem
Köder). **Drei nicht**, und zwei davon nur dem **Wortlaut** nach:

* **„Tabellen > Schirm bei 390: 0"** — Projektakte/Berichte führt 720 px gegen
  390. Das ist der bewusste Beschluss „bleibt eine 720-px-Tabelle", der
  Behälter rollt, der Inhalt ist erreichbar. Die **Zusage** ist trotzdem falsch.
* **„Wirklich gekürzt bei 1440: 0"** — die Arbeitsscheine-Liste kürzt 6 `<td>`
  der Spalte „Durchzuführende Arbeit" um bis zu **493,6 px**. Das ist wörtlich
  Entscheidung 5 dieses Berichts.
* **„Bedienelemente ohne Beschriftung: 0"** — war ein schlichtes Versehen und
  ist seit v3.9.957 **eingelöst**, mit einer namentlichen Ausnahme (siehe S-1
  oben). Diese Zusage ist damit keine mehr, die man umschreiben muss.

### Der Wortlaut, den die beiden übrigen Zusagen ab jetzt haben

Nicht „0", sondern 0 **außer diesen, namentlich** — sonst wird ein Riegel darauf
beim nächsten Lauf **grün gemacht** statt der Code repariert, und genau das ist
der schwerste Fehler, den dieser Lauf kennt:

> **Tabellen breiter als der Schirm bei 390 px: 0 — außer der
> Wochenbericht-Tabelle in Projektakte/Berichte (720 px).** Sie ist ein
> Beschluss, nicht ein Versehen: die 720 kamen aus einer Messung, der Behälter
> trägt `overflow-x:auto` und rollt +346 px, es geht nichts verloren. Eine neue
> zu breite Tabelle an einer anderen Stelle ist ein Fehler.

> **Wirklich gekürzte Textstellen bei 1440 px: 0 — außer den `<td>` der Spalte
> „Durchzuführende Arbeit" in der Arbeitsscheine-Liste** (6 Stellen, bis zu
> 493,6 px). Das ist Entscheidung 5: die Spalte bleibt 220 px breit, weil eine
> breitere Spalte die übrigen acht zusammenschiebt. Eine neue Kürzung an einer
> anderen Stelle ist ein Fehler.

Beide Ausnahmen nennen **wo** und **wie viel**. Eine Ausnahme ohne Zahl ist
keine Ausnahme, sondern eine Lücke — und sie wächst, weil niemand merkt, wenn
sie größer wird.

## Und ein Beleg, der gut ausgegangen ist

Der Grundstand `docs/GRUNDSTAND_UI_v3.9.954.md` wurde unabhängig neu erhoben:
44 Aufnahmen, 22 Ansichten × 2 Breiten, **`diff -u` gibt 0 Zeilen** — bytegleich,
nicht nur im Mengengerüst, sondern in jeder Überschrift, jedem Tabellenkopf,
jedem Platzhalter und jeder Auswahloption. Drei Köder haben dabei angeschlagen
(Knopfzahl verändert, Zeile entfernt, Wort in eine Überschrift eingefügt), sonst
wäre die Null wertlos.

---

# Nachtrag 27.09.2026 — v3.9.960 und v3.9.961: die Knöpfe, und drei Messungen

## Was drei parallele Messungen ergeben haben

**Alle drei Pixelneutralitäts-Behauptungen halten** (`docs/befunde/PIXELNEUTRALITAET_v3.9.959.md`).
Gemessen an 340, 375, 390 und 1440 px gegen den jeweils **richtigen** Vorgänger:

> 🔴 Der von mir genannte Vergleichsstand `84b8e72` war **falsch** — ein
> Doku-Commit, dessen `index.html` schon v3.9.957 trug. Dagegen gemessen wäre
> bei zwei von drei Behauptungen „null Unterschied" herausgekommen: **dieselbe
> Änderung auf beiden Seiten, eine leere Grundgesamtheit.** Gemessen wurde
> gegen `11e365a`, `a4b50e5` und `a34d535`.

Der 340-px-Fall ist mit Ködern in **beide** Richtungen belegt: die Regel
`.header-row h2{font-size:16px!important}` ist nachweislich wirksam (angehängtes
`header-row` lässt das `h2` von 20 auf 16 px fallen) und greift am echten Baum
nur nicht, weil dieser Kopf kein `header-row` trägt.

## 🔴 v3.9.961 — 18 namenlose Knöpfe, die **beide** alten Riegel nicht sehen konnten

Die Riegel aus v3.9.957 und v3.9.958 haben je einen **eigenen** Knopf-Abtaster
mitgebracht, und beide hatten dieselben drei Lücken:

| | |
|---|---|
| nur der lange Erzeuger | die **97** Stellen mit dem Kürzel `h` wurden nie angesehen |
| nur **doppelte** Anführungszeichen | sieben Stellen stehen in einfachen |
| nur **ein** Literal als Inhalt | jedes Ternär aus zwei Literalen fiel durch; die Zeichenklasse kennt weder `⊞` (0x229E) noch `×` (0x00D7) |

**Der Beleg ist die Eichung, nicht die Behauptung:** die Messung hat beide
Suchlogiken zeichengenau nachgebildet, und die nachgebildete v958-Logik findet
**genau 150** Knöpfe — dieselbe Zahl, die der Riegel nennt. Erst damit ist
„nicht gesehen" eine Aussage.

**Das bitterste daran:** die Regel dagegen ist **einen Tag vorher**
aufgeschrieben worden — *ein Zähler, der eine Schreibweise nicht kennt, meldet
„kommt nicht vor"*. Und am selben Abend sind zwei Riegel entstanden, die genau
daran vorbeilaufen. Eine Regel, die man kennt, ist keine Regel, die wirkt; erst
ein **gemeinsamer Abtaster mit Eichung** ist eine. Er liegt jetzt einmal in
`scripts/code_scan.py` (`knopf_stellen`, `hat_namen`, `eichen_knoepfe`) und
sieht alle **797** Knöpfe statt 174.

Vier Köder — **einer je Schreibweise**, nicht einer für den Zähler — plus vier
Gegenproben: ein Knopf *mit* Wort darf nicht gemeldet werden. Ein Zähler, der
alles meldet, schlägt bei jedem Köder an und ist trotzdem kaputt.

## v3.9.960 — zwei Knöpfe, deren Text wegfallen kann

Gefunden am gerenderten Baum, nicht von einem Zähler: der Löschknopf der
Bautagebuch-Karte ist `"🗑️ " + isMob?"Löschen":""` — ab 600 px bleibt nur das
Symbol. Und der Zurück-Knopf der Projektakte hat seinen Text in einem
`span.sb-text`, für das `display:none` in `@media(max-width:768px)` gilt: die
eingeklappte 56-px-Leiste liest nur „◀".

**Beide sind älter als dieser Lauf.** Am Schreibtisch war der Löschknopf schon
vor v3.9.955 namenlos; die Mobilschwellen-Umstellung hat den Mangel nur auf
600–767 px ausgeweitet. Ein Befund, der durch eine Änderung *sichtbarer* wird,
ist nicht durch sie entstanden.

## 🔴 Riegel-Hygiene: eine lief 29 Tage nie, eine war tot, eine war eine Falle

Aus `docs/befunde/WAS_LAEUFT_WIRKLICH.md`, behoben in `2449db2`:

* **`test_nichtgemessen_v909.py` hat 29 Tage und 75 Commits nichts gemessen.**
  Dateiname `test_*`, in `tests/`, fehlerfrei, meldet von Hand grün 18/18 — und
  enthielt keine einzige `def test_`. pytest sammelte **null** Fälle. Von innen
  sieht so eine Datei richtig aus; gefunden wurde sie nur von **außen**, durch
  den Vergleich von Platte gegen `--collect-only`. Ihre 18 Fälle prüfen eine
  echte Eigenschaft: eine ausgebliebene Messung darf nicht als **Zahl**
  erscheinen. Jetzt einzeln parametrisiert, mit Köder.
* Eine **tote Zusicherung** ohne `in index_html` — entfernt, nicht ergänzt: die
  Zeile darunter prüft strenger.
* **`sql/_check_brackets.js` war eine Falle**, nicht nur ungenutzt: RC 1, und
  README, RUNBOOK und ARCHITECTURE wiesen alle an, es zu fahren. Es zählt rohe
  Zeichen, seine Grundlinie wandert mit jedem Kommentar. Es bleibt liegen, sagt
  jetzt dass es abgelöst ist, und ruft das gültige Werkzeug auf.

Und der Fund verhindert sich künftig selbst:
`test_jede_datei_wird_eingesammelt_v961` fragt pytest **im Lauf**, aus welchen
Dateien Fälle gekommen sind. Bei einem **Teillauf** hält sie sich mit Begründung
zurück — eine Prüfung, die bei `-k` rot wird, wird abgeschaltet, und
abgeschaltet ist sie wieder nichts wert.

## 🔴 Eine Erkenntnis über die Tore selbst

Die Klammerbilanz gegen den Vorgänger habe ich in diesem ganzen Lauf **naiv**
gerechnet — über den rohen Text. In v3.9.961 wanderte sie um +2, weil mein
eigener Changelog `createElement(` mit offener Klammer nannte. Mit dem richtigen
Instrument (Zeichenketten und Kommentare zuerst gestrichen, wie in
`scripts/_bracket_check.py`) ist die Bilanz **identisch** bei `(0, -1, 0)`.

Der naive Vergleich ging bisher nur gut, solange meine Kommentare ausgeglichene
Klammern hatten — also **aus Glück, nicht aus Konstruktion**. Es ist dasselbe
Instrument, an dem `sql/_check_brackets.js` gescheitert ist.

## Zwei strukturelle Tatsachen, die Sebastian kennen sollte

1. **Es gibt keine `package.json` und keine CI** — und laut `git log --all` hat
   es nie eine gegeben. `.github/workflows/` existiert nicht. Die 3210 Fälle und
   der Versionsabgleich laufen **nur**, wenn jemand die Torkette von Hand tippt.
   Kein Automatismus erzwingt das.
2. **62 von 76 Prüfern hängen in keiner Kette.** Davon brauchen 32 einen
   Browser, 5 die Datenbank, 1 das Netz — das sind Einmal-Messgeräte und zu
   Recht nicht verdrahtet. Nur 15 sind reine Leser.

## Was gemessen ist und auf eine Entscheidung wartet

Aus `docs/befunde/BEDIENELEMENTE_OHNE_NAMEN.md`, mit Zeilennummer und
abgelesenem Vorschlag je Stelle — **nicht gebaut**, weil jeder Name dort eine
Wahl wäre:

* **133 Klickflächen** auf `div`, `th`, `span`, `img`, `td`, `tr`, `canvas` mit
  `onClick`, aber **ohne `role` und `tabIndex`** — für die Tastatur und für eine
  Vorlesehilfe sind das keine Bedienelemente. (29 reine Klick-Schlucker
  `e=>e.stopPropagation()` sind abgezogen; dort wäre ein `role` falsch.)
* **461 Eingabefelder ohne Namen** (315 `input`, 117 `select`, 29 `textarea`).
  161 haben nur einen `placeholder` — das ist kein Name. `htmlFor` kommt in der
  ganzen Datei 20 mal vor.
* **10 Bedienelemente, die mit `document.createElement` gebaut werden** statt
  über React — außerhalb jeder React-Messung: die PDF-Blätterknöpfe und acht
  Felder in Dialogen und Tabellenzellen.
