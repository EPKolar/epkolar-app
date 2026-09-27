# Die fünfzehn reinen Leser — was davon in eine Kette gehört

**Stand:** 27.09.2026 · `HEAD = a26e2b0` · v3.9.961
**Vorlage:** `docs/befunde/WAS_LAEUFT_WIRKLICH.md`, Messung (3) und (4)
**Messskripte (neu angelegt):**
`scripts/befund_leser.py` · `scripts/befund_leser_lauf.py` · `scripts/befund_leser_urteil.py`
**Rohdaten:** `docs/befunde/_leser_lauf.log` — die Datei ist per
`.gitignore:27` (`*.log`) **nicht mitversioniert**. Sie entsteht neu mit
`python scripts/befund_leser_lauf.py`; jede Zahl dieses Berichts ist damit
nachfahrbar, aber keine ist im Repo hinterlegt.

> `index.html` wurde nicht angefasst (`git diff --stat -- index.html` ist leer).
> Es wurde kein Prüfer gefahren, der schreibt oder migriert. Jede
> Mutationsprobe lief auf einer **Kopie** in einem Wegwerfbaum.

---

## Kurzfassung

| | Zahl |
|---|---|
| **einhängen** | **3** |
| **als Test umschreiben** | **5** |
| **abschreiben und kennzeichnen** | **1** (+1 heute früh bereits erledigt) |
| **liegenlassen mit Grund** | **6** |
| **heute ROT** | **1** (`paare_v931_ausgetretene.py`, rc 1) |
| **Kosten der Einhängung** | **+1,0 s** auf 283 s Kette = **+0,35 %** |

Die drei Einhängkandidaten sind **an einer Kopie mutationsgeprüft**: sie werden
rot, wenn man ihren Gegenstand kaputt macht. Die Empfehlung steht nicht auf
„läuft durch".

Der teuerste Einzelbefund steht nicht in der Tabelle, sondern hier:
**`scripts/md5_geschuetzt.py` ist der einzige Ort im Repo, der die
Byte-Identität von sieben lohn- und eskalationsnahen Funktionen festhält — und
er läuft in keiner Kette.** Zwei Testdateien verweisen ausdrücklich auf ihn
(„das hält `scripts/md5_geschuetzt.py` fest"), und keine der sieben Prüfsummen
steht in irgendeiner Testdatei. Die Zusicherung wird also delegiert an etwas,
das nie gefahren wird.

---

## Vorab: die Grundgesamtheit hat sich verschoben

Die Vorlage nennt 15 reine Leser. Die Zahl stimmt, **die Namensliste nicht** —
und zwar aus einem Fehler in der Vormessung, nicht aus Änderungen am Baum.

`scripts/befund_kette.py` und `scripts/befund_verweise.py` widersprechen sich:
12 erreichte Prüfer gegen 14. Nachgemessen am 27.09.:

| Fehler in `befund_kette.py` | Wirkung |
|---|---|
| gleicht Verweise über den **Basisnamen** ab (`if b in txt`) | `"bracket_check.py"` ist eine **Teilzeichenkette** von `"_bracket_check.py"`. Weil `tests/test_klammertor_blindheit_v956.py` den Streicher `_bracket_check.py` nennt, galt ihm auch `scripts/bracket_check.py` als gefahren. **Eine erfundene Kette.** |
| kennt die **Import-Form** nicht | `from code_scan import ist_code` nennt `"code_scan.py"` nirgends. Also galten `code_scan.py`, `safe_edit.py` und `mob_ansicht_messen.py` als verwaist — `code_scan.py` wird von **19 Testdateien** importiert. **Drei falsche Waisen.** |

`befund_verweise.py` trennt Form S (Zeichenkette) von Form M (Import) und trifft
beide Fälle richtig. Meine Messung nimmt deshalb **dessen** Liste.

**Folge für diese Untersuchung:** `scripts/code_scan.py` ist **kein** Waise und
fällt aus den 15 heraus; `scripts/icons_erzeugen.py` kommt hinein. Die Zahl
bleibt zufällig bei 15.

> Das ist derselbe Fehlertyp, den `befund_verweise.py` in seinem eigenen
> Docstring als „Fehler 3 der Vorfassungen" beschreibt. Er ist dort ausgebaut
> und in `befund_kette.py` stehengeblieben — zwei Messgeräte, ein Repo,
> verschiedene Stände.

---

## Die Tabelle

Laufzeit = Mittel aus zwei **warmen** Läufen (der erste Lauf trägt den
Dateizwischenspeicher für die 3,6 MB `index.html` und ist nicht die Zahl, die
die Kette kosten würde). Rückgabewert getrennt von der Ausgabe gelesen, ohne
Pipe, Urteil aus `docs/befunde/_leser_lauf.log`.

| # | Prüfer | Gegenstand | rc | Laufzeit | Überschneidung | Empfehlung |
|---|---|---|---|---|---|---|
| 1 | `scripts/md5_geschuetzt.py` | md5 der 7 geschützten Funktionen (`_ezEffTage`, `_asEskalierbar`, `_dispoPlan`, `_maIstEhemalig`, `_maWaehlbar`, `_juprowaPush`, `_juprowaSanitize`) | **0** | **0,06 s** | **keine** — keine der 7 Summen steht in einem Test | **einhängen** |
| 2 | `scripts/bestand.py` | 118 Bedienbegriffe in 17 Gruppen müssen in `index.html` vorkommen | **0** | **0,10 s** | teilweise — „Termin (best.)", „Kein Monteur", „Leiter/Geruest" stehen in **keinem** Test | **einhängen** |
| 3 | `scripts/icons_erzeugen.py --pruefen` | die 4 PWA-PNG im Repo stimmen mit dem Erzeuger überein | **0** | **0,82 s** | keine | **einhängen** (nur `--pruefen`) |
| 4 | `scripts/freivar/selbsttest.js` | misst `freivar.js` an 23 Sprachkonstrukten, je gebunden **und** frei | **0** | 4,16 s | `tests/test_freie_variablen.py` fährt `freivar.js`, hat aber 5 **eigene** Fälle, nicht diese 23 | **als Test umschreiben** |
| 5 | `scripts/freivar/mutation.js` | Köder: benennt echte Referenzen in `index.html` um, prüft ob der Scanner sie meldet | nicht gefahren | — | keine | **als Test umschreiben** |
| 6 | `scripts/a2_dryrun.mjs` | JUPROWA-Status-Roundtrip | **0** | 0,06 s | **ATTRAPPE** — siehe unten | **als Test umschreiben** |
| 7 | `scripts/verify_sync_behavior.cjs` | `doSync`-Schleife, 403-Wedge + PhotoQ | **0** | 0,06 s | **ATTRAPPE** — siehe unten | **als Test umschreiben** |
| 8 | `scripts/b3_12_15_quelltext.py` | `fontSize` je Komponente, Untergrenze 12 px | **0** | 0,90 s | keine | **als Test umschreiben** — siehe unten |
| 9 | `scripts/paare_v931_ausgetretene.py` | Anker/Ersatz-Paare aus v3.9.931 | **1** | 0,11 s | — | **abschreiben und kennzeichnen** |
| 10 | `sql/_check_brackets.js` | Klammerbilanz über Rohtext | **0** | 0,67 s | fährt `_bracket_check.py` ein **zweites** Mal | **erledigt** (27.09. abgelöst) |
| 11 | `scripts/anker_schneiden.py` | schneidet einen Anker aus der Datei | 2 (Aufrufhinweis) | 0,05 s | — | **liegenlassen** |
| 12 | `scripts/ansicht_inventar.py` | Inventar **einer** Ansicht | nicht gefahren | — | — | **liegenlassen** |
| 13 | `scripts/b3_bestand_quelltext.py` | B3-Mengengerüst der vier Ansichten | nicht gefahren | — | — | **liegenlassen** |
| 14 | `scripts/bughunt-state-update.ps1` | schreibt einen Schlüssel in eine Zustandsdatei | nicht gefahren | — | — | **liegenlassen** |
| 15 | `scripts/torkette.py` | — | 0 | 3,0 s | — | **liegenlassen** (Messartefakt) |

**Nicht gefahren, je mit Grund** (ein Messlauf, der nebenbei das Repo ändert,
ist keine Messung):

| Prüfer | Grund |
|---|---|
| `ansicht_inventar.py` | schreibt eine Inventardatei, braucht `--ansicht` |
| `b3_bestand_quelltext.py` | schreibt einen Vergleichsstand nach `docs/` |
| `bughunt-state-update.ps1` | schreibt per `Set-Content` in die übergebene Datei |
| `freivar/mutation.js` | legt `scripts/freivar/_mut.html` im **Repo** an |
| `icons_erzeugen.py` (ohne `--pruefen`) | schreibt PNG in die Repo-Wurzel |
| `torkette.py` (voll) | ist die Kette selbst |

---

## Die Wirkungsproben

`python scripts/befund_leser_lauf.py --wirkung` — jede Probe auf einer **Kopie**
von `index.html` in einem Wegwerfbaum, nie am Original. Der Läufer bricht ab,
wenn eine Mutation die Datei nicht verändert hat („KÖDER GRIFF NICHT"): ein
Köder, der seinen Gegenstand verfehlt, ist eine leere Grundgesamtheit und
belegt nichts.

| Prüfer | unverändert | Gegenstand kaputt | soll | Ergebnis |
|---|---|---|---|---|
| `md5_geschuetzt.py` | rc 0 | rc **1** | wirkt | ✅ |
| `bestand.py` | rc 0 | rc **1** | wirkt | ✅ |
| `icons_erzeugen.py --pruefen` | rc 0 | rc **1** | wirkt | ✅ |
| `b3_12_15_quelltext.py` | rc 0 | rc **0** | wirkt **nicht** | ✅ (Befund) |
| `a2_dryrun.mjs` | rc 0 | rc **0** | wirkt **nicht** | ✅ (Befund) |
| `verify_sync_behavior.cjs` | rc 0 | rc **0** | wirkt **nicht** | ✅ (Befund) |

Alle sechs mit **einem** Aufruf nachfahrbar (`--wirkung`, rc 0): 6 von 6 wie erwartet — in **beide** Richtungen. Eine Probe, die nur „muss rot
werden" kennt, kann nicht zwischen *wirkt nicht* und *soll nicht wirken*
unterscheiden; die Soll-Richtung steht deshalb je Probe im Code.

### Ein Köder, der zweimal danebenlag

Die erste Fassung der `bestand.py`-Probe meldete **WIRKT NICHT** — für einen
Riegel, der einwandfrei wirkt. Sie entfernte den Begriff mit
`replace(b, ..., 1)`, also **einmal**. `bestand.py` prüft aber
`if not any(k in quelle ...)`: solange der Begriff irgendwo sonst noch steht,
ist er gefunden. Der Köder traf seinen Gegenstand nicht und belegte damit nicht
das Gegenteil, sondern **nichts**. Die zweite Fassung entfernt den Begriff
überall und nimmt einen ohne Umlaute (`Bautagebuch`, 29 Vorkommen) — denn
`bestand.py` sucht auch die Umlaut- und Entity-Schreibweisen, und eine
ASCII-Ersetzung hätte die ä-Variante stehenlassen.

---

## Die drei Einhängkandidaten — wo, und was es kostet

### Wo

**Ein eigenes fünftes Tor, vor `pytest`.** Nicht ins vierte (`pytest tests/`)
hinein und nicht als Testdatei:

* Alle drei urteilen über **Dateien neben `index.html`** (Prüfsummen, PNG-Bytes,
  Begriffsliste), nicht über eine Funktion. Als pytest-Fall würden sie dieselbe
  3,6-MB-Datei ein weiteres Mal einlesen, die 466 Testdateien ohnehin schon
  lesen.
* Sie sollen **vor** den 280 s pytest urteilen. Ein verschobener Lohnrumpf soll
  nach einer Sekunde auffallen, nicht nach fünf Minuten.
* Sie tragen je eine **Selbstprobe gegen die leere Grundgesamtheit**, die in
  einem pytest-Fall verlorenginge — `bestand.py` bricht ab, wenn seine
  Begriffsliste leer ist **oder** `index.html` unter 1 MB fällt („Das ist
  Datenverlust, kein grünes Ergebnis"). Das ist genau das Lebenszeichen, das
  `sql/_check_brackets.js` fehlte.

Vorschlag für `TORE` in `scripts/torkette.py`, eingefügt **vor** dem
pytest-Eintrag:

```
("Geschuetzte Rümpfe", [sys.executable, "scripts/md5_geschuetzt.py"], False),
("Bestand",            [sys.executable, "scripts/bestand.py"], False),
("PWA-Icons",          [sys.executable, "scripts/icons_erzeugen.py",
                        "--pruefen"], False),
```

🔴 **`--pruefen` ist nicht optional.** Ohne das Argument schreibt
`icons_erzeugen.py` vier PNG in die Repo-Wurzel. Ein Tor, das schreibt, ist
kein Tor.

### Was es kostet

| | heute | mit dem 5. Tor |
|---|---|---|
| schnelle Tore (`--schnell`) | 3,0 s | **4,0 s** (+33 %) |
| ganze Kette (mit pytest ~280 s) | 283 s | **284 s** (**+0,35 %**) |

Die Einzelbeiträge: 0,06 + 0,10 + 0,82 = **0,98 s**. Der Löwenanteil sind die
PWA-Icons (0,82 s), weil sie viermal ein PNG neu zeichnen. Wer die schnelle
Kette schlank halten will, hängt nur die ersten beiden ein (**+0,16 s**) und
die Icons in ein Tor, das nur vor einer Auslieferung läuft.

**Für den PostToolUse-Hook (K2)** taugen `md5_geschuetzt.py` und `bestand.py`
mit zusammen 0,16 s ohne weiteres; die Icons mit 0,82 s würden den Hook nach
jedem `Edit` spürbar verlangsamen — und ein Hook, der nervt, wird abgeschaltet.

---

## Die Befunde im Einzelnen

### 1 · Zwei Attrappen: `a2_dryrun.mjs` und `verify_sync_behavior.cjs`

Beide bezeichnen sich als Prüfer von `index.html`:

* `a2_dryrun.mjs`: „repliziert die exakten Maps + die GEFIXTE
  `_juprowaReversMap`-Status-Logik (**index.html:3307**)"
* `verify_sync_behavior.cjs`: „Repliziert die ECHTE Loop-Logik **VERBATIM**
  (index.html:5139-5164)"

Kommentarblind über den Syntaxbaum gemessen:

| Prüfer | „index.html" im **Rohtext** | im **Code** |
|---|---|---|
| `a2_dryrun.mjs` | 2 | **0** |
| `verify_sync_behavior.cjs` | 4 | **0** |

**Sie öffnen `index.html` nie.** Die Statustabelle und die `doSync`-Schleife
stehen **abgeschrieben** in ihrem eigenen Quelltext. Belegt an der Kopie: mit
verdrehtem `JUPROWA_STATUS_MAP` und zerstörtem `syncQueueFailed` in
`index.html` bleiben beide auf rc 0.

Als Tor wären sie schlimmer als nichts: sie melden grün, während ihr Gegenstand
rot ist, und tragen dabei einen Namen, der Deckung verspricht. **Ein Riegel auf
einer Kopie schützt die Kopie.**

Der Gegenstand existiert noch (`_juprowaReversMap` 3×, `syncQueueFailed` 14×,
`doSync` 48× in `index.html`) — die Eigenschaft ist also richtig, nur das
Verfahren nicht. Deshalb **umschreiben**, nicht abschreiben: die Tabelle bzw.
die Schleife aus `index.html` schneiden (dafür gibt es `scripts/code_scan.py`,
das bereits in der Kette hängt) statt sie abzutippen.

> Nebenbei: die beiden sind der Grund, warum eine Prüfung auf „nennt das
> Skript `index.html`?" hier nichts taugt. Beide nennen es — im Kommentar.

### 2 · `b3_12_15_quelltext.py` berichtet 113 Fundstellen und gibt 0 zurück

Ausgabe vom 27.09.:

```
FahrzeugView          13   165kB  113 Stellen   9px x29 - 10px x40 - 11px x44
FlotteView            13    34kB    8 Stellen   10px x1 - 11px x7
BauprovisorienView    15    40kB    3 Stellen   10.5px x1 - 11.5px x2
```

Rückgabewert: **0**. Der Prüfer kann rot werden, aber nur über
`raise SystemExit("ABBRUCH (K-Q1) …")` in Zeile 115 — wenn **seine eigene
Eichung** scheitert. Über seinen Gegenstand urteilt er nie.

Das ist auch ein Befund **an den beiden Vormessungen**: sie nennen einen Prüfer
„urteilsfähig", wenn das Wort `exit` in seinem Code vorkommt. Das ist
Anwesenheit, nicht Wirkung. `scripts/befund_leser_urteil.py` misst stattdessen,
ob es einen Ausstieg mit einem Wert ≠ 0 gibt, und löst `sys.exit(main(…))` in
die aufgerufene Funktion auf.

🔴 **Vor dem Umschreiben ist zu entscheiden**, ob die 124 Fundstellen ein
Fehler oder der gewollte Stand sind. Ein Tor daraus wäre heute sofort rot. Der
saubere Weg ist eine **Grundlinie** wie bei der Klammerbilanz
(`FahrzeugView 113 / FlotteView 8 / BauprovisorienView 3`, alles darüber ist rot) — dann fällt jede
**neue** Unterschreitung auf, ohne dass der Altbestand die Kette blockiert.
Das ist eine Entscheidung, keine Messung.

> Zwei eigene Irrtümer an dieser Stelle, beide in dieselbe Richtung: Ich hatte
> für `b3_12_15_quelltext.py` **und** für `icons_erzeugen.py` „kann nie rot
> werden" erwartet; beide Male hatte die Messung recht und meine Erwartung
> unrecht. Der Grund war beide Male derselbe: ich hatte mit `grep` nach
> `sys.exit` gesucht, und `sys.exit` ist **kein Teil von** `SystemExit`. Die
> Köderprobe hat es beide Male gefangen — die Richtung „NIE ROT" ist deshalb
> nur an den synthetischen Ködern belegt, deren Ausstiege ich Zeile für Zeile
> gelesen habe. **Keine** der fünfzehn echten Dateien ist „nie rot".

### 3 · `paare_v931_ausgetretene.py` ist rot — und verbraucht

Rückgabewert **1**, Laufzeit 0,11 s. **7 von 9 Ankern treffen nicht mehr**
(„0 Treffer"), zwei noch genau einmal. Das ist die gewollte Schutzabschaltung:
„ABBRUCH — 9 Anker nicht eindeutig, es wurde NICHTS geschrieben."

Der Gegenstand existiert nicht mehr in der Form, die das Werkzeug erwartet. Es
ist ein **Einmal-Anwender aus v3.9.931**, dessen Ziel-Code seither umgebaut
wurde. Es ist damit **genau der Fall `sql/_check_brackets.js`**: ein Werkzeug,
das rot steht, weil sein Verfahren überholt ist, nicht weil etwas kaputt ist.

**Empfehlung: abschreiben und kennzeichnen** — Kopfkommentar „ANGEWENDET in
v3.9.931, Anker seither überholt, nicht mehr fahren", und den Ausstieg auf 0
mit einem sprechenden Satz setzen, damit niemand die 1 für einen Befund hält.
Datei liegen lassen (Hausregel „parken, nicht löschen").

### 4 · `sql/_check_brackets.js` ist erledigt — und darf **nicht** eingehängt werden

Er ist heute früh abgelöst worden und leitet auf `scripts/_bracket_check.py`
weiter; rc 0, 0,67 s. Das ist richtig so.

Er gehört trotzdem **nicht** in die Kette: der Weiterleitungsaufruf fährt
`_bracket_check.py` ein **zweites** Mal — ein Tor, das Tor 2 schon fährt, für
0,67 s. Die Weiterleitung existiert für die Zeile im RUNBOOK, nicht für die
Kette.

### 5 · Die vier Einmal-Messgeräte und das Messartefakt

`anker_schneiden.py` (Bedienwerkzeug: schneidet einen Anker aus der Datei,
hat keinen festen Gegenstand, rc 2 ist der Aufrufhinweis) ·
`ansicht_inventar.py` und `b3_bestand_quelltext.py` (Bestandsschutz-Sonden
**einer** Umbaustufe, schreiben Vergleichsstände) ·
`bughunt-state-update.ps1` (schreibt eine Zustandsdatei — Infrastruktur, kein
Prüfer). Alle vier sind zu Recht nicht verdrahtet.

`torkette.py` ist ein **Messartefakt**: sie taucht in der Waisenliste auf, weil
niemand *sie* aufruft. Eine Kette kann nicht in sich selbst hängen.

---

## Köder-Nachweise

Eine zählende Messung, die ausfällt, meldet „0 gefunden" — und das sieht wie
ein Ergebnis aus. Beide neuen Messskripte tragen deshalb eine Selbstprobe.

### `scripts/befund_leser.py --koeder` — 7 von 7 richtig

| Probe | erwartet | Ergebnis |
|---|---|---|
| Skript mit `sync_playwright` | BROWSER | ok |
| Skript mit `SUPABASE_URL` | DB | ok |
| Skript mit `urllib.request` | NETZ | ok |
| Skript, das nur eine Datei liest | LESER | ok |
| **Merkmale nur im Docstring** | **LESER** | **ok** |
| Skript mit `open(…, 'w')` | schreibt = True | ok |
| Grundgesamtheit nicht leer | >20 Waisen, >5 Browser | ok |

Die fünfte Probe ist die tragende: ein Skript, dessen Docstring erklärt „braucht
KEIN playwright", darf nicht als Browser-Skript gelten. Ohne sie misst die
Einteilung Kommentare mit.

**Ein echter Fehler, den die Messung selbst hatte:** die erste Fassung führte
`webkit` als Browser-Merkmal. Damit galt `scripts/schrift_holen.py` als
Browser-Skript — es lädt Schriften und nennt dabei das CSS-Präfix `-webkit-`.
Ein Merkmal, das auch außerhalb seines Gegenstands vorkommt, ordnet falsch zu.
Die Browser-Merkmale sind jetzt alle an einen **Aufruf** gebunden
(`.launch`, `new_page(`, `sync_playwright`), und `schrift_holen.py` steht
wieder richtig unter NETZ — wie in der Vorlage.

### `scripts/befund_leser_urteil.py --koeder` — 8 von 8 richtig

Gegenprobe in beide Richtungen, synthetisch (`sys.exit(main())` mit nur
`return 0` → NIE ROT; `return 1` → KANN ROT; `process.exit(0)` / `(1)`) und an
echtem Code (`bestand.py`, `b3_12_15_quelltext.py`, `icons_erzeugen.py`).

---

## Was ich NICHT gemessen habe

* **`freivar/mutation.js` nicht gefahren** — es legt `_mut.html` (3,6 MB) im
  Repo an. Seine Laufzeit ist damit **unbekannt**; sie ist die offene Frage bei
  Empfehlung 5. Anhaltspunkt: `tests/test_freie_variablen.py` kostet heute
  **8,1 s**, und `mutation.js` fährt `freivar.js` **25-mal**.
* **Keine Mutationsprobe für `freivar/selbsttest.js`** — es liest `index.html`
  nicht; sein Gegenstand ist `freivar.js`. Eine Probe daran hätte ein
  Kettenglied verändert.
* **Kein vollständiger pytest-Lauf.** Drei andere Agenten arbeiten gerade in
  `tests/` (5 geänderte Dateien im Arbeitsbaum). Die 280 s stammen aus der
  Vorlage, nicht aus einem eigenen Lauf; die Prozentzahl oben ist gegen diese
  übernommene Zahl gerechnet.
* **Die Überschneidungsprüfung ist stichprobenartig.** Für `md5_geschuetzt.py`
  ist sie vollständig (alle 7 Prüfsummen gegen alle Testdateien gesucht, keine
  gefunden). Für `bestand.py` habe ich 6 der 118 Begriffe geprüft — 3 davon
  stehen in keinem Test, das genügt für „deckt Boden ab, den kein Test deckt",
  aber **nicht** für eine Aussage über die anderen 112.
* **Die Einteilung von `.js`/`.ps1` ist nicht syntaxbaumfest.** Python wird über
  `ast` gelesen, die anderen über einen Abtaster, der Zeichenketten stehen lässt
  und Kommentare streicht. Reguläre Ausdrücke als Literale kennt er nicht; für
  die fünf betroffenen Dateien ist das von Hand gegengelesen.
