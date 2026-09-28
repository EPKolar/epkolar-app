# MEMORY.md — Risiko "mehrere Schreiber, keine Sperre"

Messdatum: 2026-09-28, ca. 07:00 MESZ.
Messobjekt: `C:\Users\technik\.claude\projects\C--Users-technik\memory\` und die Sitzungsablage daneben.
Diese Analyse hat NICHTS geaendert. Kein Schreibvorgang wurde ausgeloest, der Verlustfall wurde nur gedanklich durchkonstruiert.

---

## Kurzfassung der Zahlen

| Groesse | Wert | Herkunft |
|---|---|---|
| `MEMORY.md` Byte | **17 634** | `wc -c MEMORY.md` |
| `MEMORY.md` Zeilen | **84** | `wc -l MEMORY.md` |
| Zeilenenden | reines LF, **0** CR | `grep -c $'\r'` → 0 |
| Zeiger der Form `](name.md)` | **78** Vorkommen, **74** eindeutige Ziele | `grep -o` + `sort -u` |
| davon ins Leere | **0** | Schleife `test -f` ueber alle 74 |
| Zeiger der Form `[[name]]` in `MEMORY.md` | **1** (`[[epkolar-session-2026-09-27]]`) | `grep -o '\[\[[^]]*\]\]'` |
| `.md`-Dateien im Ordner | **133** (inkl. `MEMORY.md`) | `ls -1 *.md \| wc -l` |
| davon mit `node_type: memory`-Frontmatter | **99** | `grep -l 'node_type: memory'` |
| davon ohne jedes Frontmatter | **1** — nur `MEMORY.md` selbst | Schleife ueber `head -1` |
| Dateien ohne Zeiger aus `MEMORY.md` | **58** | `comm -13` |
| Dateien ohne Zeiger aus `MEMORY.md` **und** `archiv_aeltere_etappen.md` | **1** | `comm -13` gegen die Vereinigung |
| Dateien, die **keine** `.md`-Datei im Ordner erreicht (beide Schreibweisen) | **1** | siehe unten |

Die 58 sind eine irrefuehrende Zahl, solange man die zweite Ebene nicht mitmisst: `archiv_aeltere_etappen.md` fuehrt **57** Zeiger, und genau diese 57 decken 57 der 58 ab. Die Verdichtung ins Archiv hat also gehalten, was die Zeile im Index verspricht ("kein Zeiger ist dabei weggefallen").

**Die eine uebrig bleibende Datei — der eigentliche Befund dieses Abschnitts:**

### `mlg_regel_agenten_bei_freier_last.md`

- 3 026 Byte, mtime 2026-09-27 15:40:17, `originSessionId: 199947c7-31eb-4040-9203-32fe75670dea`.
- Inhalt: Sebastians Dauervorgabe "agenten immer benutzen wenn die last es erlaubt, fuer immer merken" (27.09.2026).
- `MEMORY.md` nennt sie **nicht** — weder als `](…)` noch als `[[…]]`.
- Sie wird von genau einer anderen Datei erwaehnt: `mlg_regel_auftrag_ist_eine_behauptung.md`, Zeile 22, und zwar nur als `[[mlg_regel_agenten_bei_freier_last]]` in einer "Verwandt:"-Aufzaehlung — nicht als Indexeintrag.
- In **keiner** der 31 aufgezeichneten `MEMORY.md`-Fassungen (siehe c) kommt ihr Name vor: `grep` ueber alle 31 Fassungen ergab 0 Treffer.

Damit ist sie fuer eine Sitzung, die nur `MEMORY.md` liest, unsichtbar. Ob sie je im Index stand und herausfiel, oder ob sie nie eingetragen wurde, ist **nicht feststellbar** — die Historie reicht zurueck bis 18.09. und enthaelt den Namen nie. Die Wirkung ist in beiden Faellen dieselbe: eine Dauervorgabe des Nutzers liegt ausserhalb des Index.

---

## a) Wie wird `MEMORY.md` geschrieben?

**Gemessen, nicht vermutet.** Ich habe die Sitzungsprotokolle (`*.jsonl`) nach Werkzeugaufrufen auf den Pfad durchsucht.

1. **Ueber das `Write`-Werkzeug:** genau **1** Aufruf in `199947c7….jsonl`, **0** in `a0610c25….jsonl`.
   Messung: `grep -o '"name":"Write","input":{"file_path":"[^"]*MEMORY.md"'`.
2. **Ueber `Edit`/`MultiEdit`/`NotebookEdit`:** **0** in beiden Protokollen.
3. **Ueber Bash + Python-Heredoc:** **15** Protokollzeilen in `199947c7….jsonl` nennen den `MEMORY.md`-Pfad in einem Python-Schnipsel, **7** davon eindeutig. In `a0610c25….jsonl`: 0.

Der tatsaechliche Schreibweg sieht so aus (woertlich aus dem Protokoll entnommen, Zeilenumbrueche der Lesbarkeit halber):

```
import io
p = r'C:\Users\technik\.claude\projects\C--Users-technik\memory\MEMORY.md'
s = io.open(p, encoding='utf-8', newline='').read()      # (1) GANZE Datei lesen
alt = '**`3e66c818`, v2.21.240, …**'
assert s.count(alt) == 1, s.count(alt)                   # (2) schwache Vorpruefung
neu = ('**`8c9b49f7`, v2.21.242, …**')
io.open(p, 'w', encoding='utf-8', newline='').write(s.replace(alt, neu))   # (3) GANZE Datei zurueckschreiben
```

Eine zweite Auspraegung arbeitet zeilenweise, aber mit demselben Muster:

```
zeilen = s.split(nl)
i = next(k for k, z in enumerate(zeilen) if z.startswith('- [MLG/YachtLog CC-Session 2026-08-27/28]'))
zeilen[i] = ( … )
```

**Antwort auf a):**

- **Die ganze Datei wird ersetzt.** Es wird nicht angehaengt und es wird keine Zeile "eingefuegt" im Sinne eines Teilschreibvorgangs. Jeder Schreibvorgang ist ein `open(p,'w')` mit dem vollstaendigen neuen Text.
- **Ja, der Schreiber liest vorher** — aber er liest in Schritt (1), und zwischen (1) und (3) liegt die gesamte Denk- und Werkzeugzeit einer Sitzung. Die Lueckenbreite ist damit nicht Millisekunden, sondern Minuten bis Stunden. Belegt: `MEMORY.md` wurde laut Historie am 27.09. um 13:24, 14:48, 16:06, 16:54, 17:15, 18:15, 19:39 und 23:20 jeweils vollstaendig neu geschrieben.
- **Keine Sperre.** Im Ordner liegt keine `.lock`-Datei, kein `.bak`, kein Sicherungsstand (`ls -1a | grep -E '\.(bak|orig|tmp|old|save)$|~$'` → leer). Auch `settings.json` und `settings.local.json` enthalten keinen Hook, der vor oder nach einem Schreibvorgang auf diesen Pfad greift (geprueft: `settings.json`, 3 901 Byte, keine `hooks`-Sektion mit Bezug auf `memory`).
- Zusatz: `newline=''` ist in den gesehenen Schnipseln gesetzt, und die Datei hat **0** CR-Zeichen. Die CRLF-Falle hat hier also nicht zugeschlagen.
- **Nicht feststellbar:** die 99 Dateien mit `node_type: memory`-Frontmatter tragen `originSessionId` und `modified`. Sie werden offenkundig von einem Speicher-Teilsystem geschrieben, nicht von einem Python-Schnipsel. Ob dieses Teilsystem `MEMORY.md` ebenfalls anfasst, konnte ich nicht belegen — `MEMORY.md` ist die **einzige** `.md`-Datei im Ordner **ohne** Frontmatter, was eher dagegen spricht.

---

## b) Kann ein Schreibvorgang fremde Zeilen verlieren?

**Ja. Vollstaendig und geraeuschlos.** Durchkonstruiert, nicht ausprobiert:

| Zeit | Sitzung A (`199947c7`) | Sitzung B (`a0610c25`) | Datei auf Platte |
|---|---|---|---|
| T0 | — | — | Stand S0, 84 Zeilen |
| T1 | `s = open(p).read()` → haelt S0 im Arbeitsspeicher | — | S0 |
| T2 | arbeitet (Agenten, Messungen, Minuten bis Stunden) | `s = open(p).read()` → haelt **ebenfalls S0** | S0 |
| T3 | — | ersetzt Zeile 7, schreibt `open(p,'w').write(S0')` | **S0'** (= S0 + Lektion β) |
| T4 | ersetzt Zeile 42 **in ihrem S0**, schreibt `open(p,'w').write(S0'')` | — | **S0''** (= S0 + Lektion α) |
| T5 | meldet "Gedaechtnis aktualisiert" | meldet "Gedaechtnis aktualisiert" | S0'' |

Ergebnis bei T5: **Lektion β ist weg.** Die Datei enthaelt α, nicht β. Beide Sitzungen haben eine Erfolgsmeldung ausgegeben. Niemand hat einen Fehler gesehen.

Warum die Vorpruefung nicht rettet:

- Das `assert s.count(alt) == 1` prueft **nur den Textbaustein, den A selbst ersetzen will**. Es prueft NICHT, ob sich die uebrige Datei seit dem Lesen geaendert hat. Bs Zeile 7 ist fuer As `assert` unsichtbar.
- Das `next(k for k, z in enumerate(zeilen) if z.startswith(…))` in der zeilenweisen Auspraegung hat dieselbe Blindheit: es findet seine Zeile, unabhaengig davon, was sonst dazugekommen ist.
- Der Riegel, den es hier gaebe — "hat sich die Datei seit meinem Lesen geaendert?" — existiert im gemessenen Schreibweg **nicht**. Das `Edit`-Werkzeug haette ihn (es verlangt ein vorheriges `Read` und bricht bei Abweichung ab). Aber `Edit` wurde laut Messung **0**-mal auf `MEMORY.md` angewandt.

Das ist die Bauform "letzter Schreiber gewinnt", und sie verliert genau die Menge, die zwischen fremdem Lesen und fremdem Schreiben entsteht.

**Eine Praezisierung, die die Messung nahelegt:** verloren gehen nicht nur ganze Zeilen. Der haeufigere Fall ist der **ueberschriebene Zusammenfassungstext einer Zeile, deren Zeiger stehen bleibt**. Siehe d) — dort ist belegt, dass der Zeigerbestand nie schrumpfte, waehrend die Zeilentexte laufend ersetzt wurden. Ein Verlust der zweiten Art laesst den Index vollstaendig aussehen.

---

## c) Ist ein Verlust bemerkbar?

**Versionskontrolle: nein.**
`git -C <ordner> rev-parse` → `fatal: not a git repository (or any of the parent directories): .git`, Exit 128. Auch kein uebergeordnetes Repository. Der Ordner ist **nicht** versioniert.

**Sicherungskopien im Ordner: nein.**
Keine `.bak`, `.orig`, `.tmp`, `.old`, `.save`, keine Tilde-Dateien. Gemessen mit `ls -1a | grep -E '\.(bak|orig|tmp|old|save)$|~$'` → leer.

**Papierkorb: leer bzw. nicht einsehbar.**
`C:\$Recycle.Bin` enthaelt fuer diesen Zugriff keine Eintraege (nur `.` und `..`).

**`~/.claude/backups`: nein.**
Enthaelt ausschliesslich 5 Kopien von `.claude.json` (je 69 486 Byte, vom 28.09. 06:51–06:56). Kein `MEMORY.md`.

**ABER — es gibt doch eine Historie, und sie ist gut:**
`C:\Users\technik\.claude\file-history\` fuehrt pro Sitzung einen Versionsspeicher. Fuer `MEMORY.md` (Pfadschluessel `e78bd3190dee4ce7`):

- in `199947c7-31eb-4040-9203-32fe75670dea\`: **43** Fassungen, `@v1` bis `@v52`
- in `a0610c25-8e86-4c8e-8376-74a93ef9dae6\`: **8** Fassungen, `@v1` bis `@v8`
- zusaetzlich eine aeltere Fassung unter anderem Pfadschluessel: `8cfd56108eebf468@v3` vom 03.09.
- Davon tragen **31** die heutige Kopfzeile `## REGELN`; die uebrigen sind aeltere Formate derselben Datei.

Diese Historie ist **belastbar, aber nicht vollstaendig**. Drei gemessene Luecken:

1. **Numerierungsluecken.** In der Reihe `v1…v52` fehlen neun Nummern: `v2 v5 v6 v7 v8 v9 v17 v18 v19`. Ob geloescht oder nie angelegt, ist nicht feststellbar.
2. **Reichweite.** Die aelteste `MEMORY.md`-Fassung in diesem Speicher ist `@v1` vom **18.09.2026 13:04** (27 099 Byte). Alles davor ist nicht rekonstruierbar. Der Ordner selbst enthaelt Dateien seit Mai.
3. **Der entscheidende blinde Fleck.** Die Historie schnappt nur zu, **wenn die jeweilige Sitzung die Datei selbst anfasst**. Der vom Auftraggeber beobachtete Stand von **18 286 Byte** taucht unter allen 31 Fassungen **nicht auf**: die Groessen um diese Zeit sind 17 441 (27.09. 19:39:34) und 17 634 (27.09. 23:20:35). Ein Zwischenstand, den keine Sitzung im Moment seines Bestehens beruehrt hat, hinterlaesst dort **keine Spur**.

**Antwort auf c):** Ein Verlust ist **nachtraeglich rekonstruierbar, aber nicht bemerkbar.** Nichts meldet ihn. Es gibt keinen Vergleich, keinen Riegel, keine Pruefsumme. Man muss den Verdacht schon haben und dann von Hand in `file-history` nachsehen — und selbst dort fehlt genau der Zustand, der den Verdacht ausgeloest hat.

---

## d) Ist es schon passiert?

Drei getrennte Messungen, zwei negative Befunde und ein positiver.

### d1) Zeigerbestand — kein Verlust nachweisbar

Vereinigungsmenge aller `](name.md)`-Ziele ueber **alle 31** aufgezeichneten Fassungen: **131** eindeutige Namen.
Heute erreichbar ueber `MEMORY.md` + `archiv_aeltere_etappen.md`: dieselben 131 sind darin enthalten.
Differenz "je referenziert, heute nirgends": **0**.

Kein einziger Zeiger ist ueber die aufgezeichnete Strecke (18.09.–27.09.) verschwunden. Die Verdichtung ins Archiv hat sauber gearbeitet.

### d2) Zeilenbestand — Schrumpfungen ja, Verluste nein

Groessenverlauf der Kette in `199947c7\` (Byte / Zeilen):

```
v31 12993/68  v32 13462/69  v33 13944/69  v34 15117/71  v35 15566/72  v36 15889/72
v37 15889/72  v38 16171/72  v39 18120/73  v40 19039/74  v41 16857/75  v42 18205/76
v43 19286/76  v44 17479/77  v45 17429/78  v46 17784/79  v47 17447/80  v48 18161/82
v49 16266/80  v50 16351/80  v51 17441/83  v52 17634/84
```

Es gibt **sieben** Uebergaenge, in denen die Datei schrumpft, die groessten:

| Uebergang | Zeit | Byte | Delta |
|---|---|---|---|
| v40 → v41 | 26.09. 21:46 → 23:19 | 19 039 → 16 857 | **−2 182** |
| v48 → v49 | 27.09. 16:54 → 17:15 | 18 161 → 16 266 | **−1 895** |
| v43 → v44 | 27.09. 10:57 → 11:14 | 19 286 → 17 479 | **−1 807** |
| v47-Vorlauf | 27.09. 16:06 | 17 784 → 17 447 | −337 |

Ich habe fuer jeden Uebergang gezaehlt, wie viele Zeilen verschwinden, **die heute weder in `MEMORY.md` noch im Archiv stehen**: zusammen 38 ueber die ganze Kette, maximal 6 an einem Uebergang (v43→v44).

**Diese 38 sind aber ueberwiegend Fehlalarme des Messverfahrens.** Ich habe drei Uebergaenge im Volltext nachgelesen: in jedem Fall handelt es sich um **dieselbe Zeile in neuer Fassung** — der Zeiger bleibt, die Zusammenfassung wird umgeschrieben, also verschwindet der alte Zeilentext exakt. Beispiel v44→v45:

- alt: `- 🔴 [Jede Messung nennt ihren UMFANG](mlg_regel_umfang_der_messung.md) — … Belegt: „nicht nachst…`
- heute: dieselbe Zeile mit anderer Zusammenfassung, Zeiger unveraendert.

**Gegenprobe, ob dabei Substanz verlorenging:** Ich habe einen kondensierten Detailwert verfolgt. In der Fassung vom 26.09. 23:13 stand in `MEMORY.md` noch `anchor_watch_stop … 7 229 ms … 24,45 ms … groesste Spur 2 161 Punkte`. In der heutigen Zeile steht nur noch `7 229 ms gemessen, 24 ms gerechnet`. In der **Zieldatei** `mlg_regel_zeit_ist_nicht_arbeit.md` sind `anchor_watch_stop` (1 Treffer), `24,45` (2 Treffer) und `2 161 Punkte (47 Wachen, Mittel 106,5)` weiterhin vorhanden. Die Verdichtung hat also verschoben, nicht geloescht.

### d3) Die eine Spur, die bleibt

Der direkte Beleg fuer **gleichzeitige** Schreiber:

- Am 26.09. hat Sitzung `a0610c25` um **23:13:20** einen Stand von **19 832** Byte gesichert. Sitzung `199947c7` kennt diesen Stand nicht: ihre Nachbarfassungen sind 19 039 (21:46) und 16 857 (23:19).
- Umgekehrt hat `199947c7` Fassungen (v43 10:57, v47 16:06, v48 16:54, v50 18:15, v51 19:39), die in `a0610c25` fehlen.
- Zwischen den 4 Zeilen, in denen sich die beiden Fassungen vom 26.09. 23:13 und 23:19 unterscheiden, ist **keine** verloren — alle 4 Zeiger existieren heute. Es waren Umschreibungen, keine Loeschungen.

**Was tatsaechlich auffaellig bleibt:** `mlg_regel_agenten_bei_freier_last.md` (siehe oben) — erstellt 27.09. 15:40, in keiner der 31 Fassungen je im Index. **Und** die eine tote Verweisung `[[epkolar-cockpit-arch-notes]]` aus `epkolar_cockpit_session_2026-05-13.md`: eine Datei dieses Namens existiert nicht und kommt auch in `file-history` nicht vor. Beide Faelle liegen ausserhalb bzw. am Rand der aufgezeichneten Strecke.

**Antwort auf d):** Fuer die Strecke **18.09.–27.09.**, die die Historie abdeckt, ist **kein Verlust eines Zeigers und kein Verlust einer Lektion nachweisbar**. Fuer alles davor gibt es **keine Historie**, und damit ist die ehrliche Antwort: **nicht feststellbar — und diese Nicht-Feststellbarkeit ist selbst der Befund.** Ein Verlust waere geraeuschlos, und die einzige Historie, die es gibt, ist neun Tage alt, hat neun Numerierungsluecken und enthaelt genau den Zwischenstand nicht, der den Verdacht ausgeloest hat.

---

## e) Wie viele Sitzungen und Agenten schreiben real hinein?

**Sitzungsdateien im Projektordner** `C:\Users\technik\.claude\projects\C--Users-technik\`:
**9** `*.jsonl`, gemessen mit `ls -1 *.jsonl | wc -l`.

| mtime | Byte | Sitzung |
|---|---|---|
| 2026-09-28 06:59:39 | 702 644 031 | `199947c7-31eb-4040-9203-32fe75670dea` |
| 2026-09-28 06:59:39 | 61 678 274 | `a0610c25-8e86-4c8e-8376-74a93ef9dae6` |
| 2026-09-21 13:09 | 569 | `38a1f7cc-…` |
| 2026-09-03 16:14 | 569 | `a4565d53-…` |
| 2026-09-01 14:09 | 569 | `45361bef-…` |
| 2026-09-01 10:26 | 1 795 855 | `25c89a4c-…` |
| 2026-09-01 10:26 | 267 | `c44b1d49-…` |
| 2026-08-30 18:40 | 4 782 477 | `b59aa4c3-…` |
| 2026-08-30 18:40 | 534 | `3ae01445-…` |

**Zwei Sitzungen sind in derselben Sekunde aktiv** (28.09. 06:59:39). Das ist kein Indiz, das ist der Zustand: `199947c7` und `a0610c25` laufen **gleichzeitig**, und beide fuehren einen eigenen `MEMORY.md`-Versionszaehler in `file-history` (v52 bzw. v8 fuer dieselbe Datei). Zwei getrennte Zaehler fuer eine Datei ist die Bauform des Problems in Reinform.

**Schreiber ueber die gesamte Lebensdauer des Ordners:**
Die 99 Speicherdateien mit Frontmatter tragen `originSessionId`. Verteilung (`grep -h 'originSessionId:' *.md | sort | uniq -c`):

```
64  199947c7-…   11  a0610c25-…   10  c8ce60f0-…    9  e8d8fd56-…    7  eef37456-…
 4  c7b43c9e-…    4  c338d1db-…    4  22a7d2b7-…    3  f9450b9e-…    2  caea2a07-…
 1  b59aa4c3-…    1  73edd745-…    1  5c90bd7f-…    1  5b67a792-…    1  4d3ca76c-…
 1  3e197b28-…    1  1dd762ff-…    1  1207c609-…
```

**18 verschiedene Sitzungs-IDs** haben in diesen Ordner geschrieben; Summe 126 Eintraege (mehrere Dateien tragen mehr als eine Zeile mit `originSessionId`).

**Zaehlung, Herkunft je Zahl:**

- **9** Sitzungsprotokolle im Projektordner → `ls *.jsonl`.
- **2** davon jetzt gleichzeitig aktiv → identische mtime 28.09. 06:59:39.
- **3** Sitzungen mit eigenem `file-history`-Speicher → `ls -d */` in `.claude\file-history` (2 057, 576 und 33 Eintraege).
- **2** Sitzungen haben `MEMORY.md`-Fassungen dort → Pfadschluessel `e78bd3190dee4ce7`.
- **18** verschiedene Sitzungs-IDs haben je eine Speicherdatei erzeugt → `originSessionId`-Auszaehlung.

**Agenten: nicht gemessen — und nicht messbar auf dieser Ebene.** Ein Unteragent schreibt in dasselbe Sitzungsprotokoll und traegt dieselbe Sitzungs-ID. Aus Dateien und Frontmatter laesst sich nicht trennen, ob ein Schreibvorgang vom Hauptlauf oder von einem Agenten kam. Anmerkung ohne Beleg aus dieser Messung: die Indexzeile selbst behauptet, Unteragenten saehen das Gedaechtnis nie — das wuerde die Zahl der Schreiber auf die Hauptlaeufe begrenzen, ist hier aber **nicht nachgemessen**.

---

## f) Drei Wege, je mit Kosten und mit dem, was er NICHT loest

### Weg 1 — Sperrdatei

Vor dem Lesen `memory/.lock` anlegen (`O_CREAT|O_EXCL`), nach dem Schreiben entfernen. Wer sie vorfindet, wartet oder bricht ab.

**Kosten:** klein im Code, gross im Betrieb. Jeder Schreibweg muss sie beachten — und es gibt hier nicht *einen* Schreibweg, sondern beliebige ad-hoc-Python-Schnipsel, die eine Sitzung sich gerade ausdenkt. Eine Sperre, die 7 von 8 Schnipseln kennen, ist keine Sperre. Dazu die klassische Nebenwirkung: eine Sitzung, die abstuerzt oder vom Nutzer abgebrochen wird, laesst die Sperre liegen und blockiert alle folgenden, bis jemand sie von Hand loescht. Eine Zeitgrenze ("Sperre aelter als 10 min = Waise") bringt genau die Regel zurueck, dass Alter kein Todesnachweis ist.

**Loest nicht:** das Hauptproblem hier ist nicht die Gleichzeitigkeit auf Millisekundenebene, sondern die **Lueckenbreite zwischen Lesen und Schreiben**, die Minuten bis Stunden betraegt. Eine Sperre ueber diese ganze Zeit zu halten heisst, die zweite Sitzung fuer Stunden auszusperren. Eine Sperre nur waehrend des `write()` zu halten verhindert eine zerrissene Datei, aber **kein einziges** der unter b) beschriebenen verlorenen Updates. Genau das ist "Anwesenheit statt Wirkung".

### Weg 2 — je Sitzung eine eigene Datei plus Zusammenfuehrung

`MEMORY.199947c7.md`, `MEMORY.a0610c25.md`, …; der Leser liest alle und fuegt zusammen, oder ein Lauf verdichtet sie regelmaessig in `MEMORY.md`.

**Kosten:** Schreiben wird konfliktfrei — jede Sitzung besitzt ihre Datei allein. Dafuer wandert die Arbeit ins Lesen: der Index ist nicht mehr *eine* Datei, die man oben ins Fenster legt, sondern n Dateien in ungeklaerter Reihenfolge. Die Reihenfolge ist hier nicht kosmetisch: `MEMORY.md` ist nach Wichtigkeit sortiert (🔴🔴 zuerst), und diese Sortierung ueberlebt eine mechanische Zusammenfuehrung nicht. Die Zusammenfuehrung selbst braucht dann doch wieder einen Schreiber auf eine gemeinsame Datei — und der hat exakt das alte Problem, nur seltener.

**Loest nicht:** Widersprueche. Wenn zwei Sitzungen **dieselbe** Lektion unterschiedlich formulieren (belegt am 26.09.: dieselbe Regelzeile, zwei Fassungen), erzeugt die Zusammenfuehrung entweder ein Duplikat oder muss entscheiden — und beim Entscheiden faellt wieder eine Fassung weg. Auch der Befund aus d3 bliebe: eine neue Regeldatei, die niemand in den Index eintraegt, ist in n Dateien genauso unsichtbar wie in einer.

### Weg 3 — nur anhaengen, nie umschreiben, und getrennt verdichten

`MEMORY.md` wird nie ersetzt. Neue Lektionen werden mit `open(p,'a')` **angehaengt**. Die Verdichtung (Sortieren, Kuerzen, Archivieren) ist ein eigener, seltener, bewusst einzeln gefahrener Lauf.

**Kosten:** Ein Anhaengen mit einem einzigen `write()` unterhalb der Blockgroesse ist unter Windows praktisch unteilbar — zwei Sitzungen, die gleichzeitig anhaengen, bekommen beide ihre Zeile, in irgendeiner Reihenfolge. Der Preis ist, dass die Datei nur noch waechst und ihre Ordnung verliert: heute stehen 84 Zeilen nach Wichtigkeit sortiert da, beim Anhaengen entsteht ein Protokoll in Zeitreihenfolge. Die Sortierung, die den Index brauchbar macht, muss der Verdichtungslauf wiederherstellen — und der ist wieder ein Voll-Ueberschreiber. Zusaetzlich: das Korrigieren einer bestehenden Zeile ("`origin/main` ist jetzt ein anderer") geht nicht mehr durch Ersetzen, sondern nur durch eine Nachtragszeile.

**Loest nicht:** die Verdichtung selbst. Genau dort — v40→v41, −2 182 Byte; v48→v49, −1 895 Byte — passiert das riskante Schreiben, und dort waere es unveraendert riskant. Der Weg verschiebt das Risiko von "jedem Schreibvorgang" auf "dem Verdichtungslauf", er beseitigt es nicht. Er loest auch nicht, dass niemand merkt, wenn dabei etwas herausfaellt.

### Empfehlung

**Weg 3, aber mit einer Ergaenzung, und die Ergaenzung ist der eigentliche Punkt: eine Historie mit Riegel.**

Begruendung aus den Messungen, nicht aus Geschmack:

1. **Der gemessene Schreibweg ist Voll-Ueberschreiben ohne Aenderungspruefung** (a). Weg 3 beseitigt fuer den haeufigen Fall — eine Lektion dazuschreiben — das Lesen-Denken-Schreiben-Fenster vollstaendig. Das ist der einzige der drei Wege, der die Ursache trifft und nicht die Gelegenheit.
2. **Weg 1 misst Anwesenheit, nicht Wirkung.** Eine Sperre waehrend `write()` verhindert keinen der unter b) konstruierten Verluste. Sie wuerde gruen melden und nichts ausrichten.
3. **Weg 2 verlagert die Kosten dorthin, wo sie am teuersten sind** — ins Lesen, das bei jedem Sitzungsstart stattfindet, gegen ein Schreiben, das ein paarmal am Tag stattfindet.
4. **Die fehlende Ergaenzung ist der Nachweis.** Alles, was ich unter d) belegen konnte, konnte ich nur belegen, weil `file-history` zufaellig existiert — ein Nebenprodukt, das neun Numerierungsluecken hat, neun Tage zurueckreicht und ausgerechnet den beobachteten 18 286-Byte-Stand nicht enthaelt. Solange der Ordner nicht versioniert ist, bleibt jeder Verlust unbemerkbar. Konkret und billig: **`git init` im Speicherordner** und ein Commit nach jedem Verdichtungslauf. Kosten: ein Ordner mehr unter Versionskontrolle, ein `git add`/`git commit` je Verdichtung. Nutzen: aus "nicht feststellbar" wird "in zwei Befehlen feststellbar", rueckwirkend und ohne Luecken.
5. **Der Riegel darauf** misst Wirkung, nicht Anwesenheit: nach jedem Schreibvorgang zaehlen, wie viele `.md`-Dateien im Ordner von **keiner** anderen `.md`-Datei erreicht werden — **in beiden Schreibweisen**, `](name.md)` **und** `[[name]]`, und mit normalisierten Trennzeichen, sonst meldet er 72 Fehlalarme statt 1 (gemessen). Heute waere dieser Riegel bei **1** — `mlg_regel_agenten_bei_freier_last.md` — und haette damit genau den Fall gefunden, den fuenf andere Messungen nicht sahen. Als Koeder gehoert eine angelegte Wegwerfdatei dazu, sonst wird der Riegel bei eigenem Ausfall gruen.

Die Reihenfolge, falls nur eines davon kommt: **zuerst `git init`.** Ein Verlust, den man nachher sehen kann, ist ein anderes Problem als ein Verlust, den niemand je sieht.

---

## Was diese Analyse NICHT abdeckt

- **Zeitlicher Umfang.** Alle Aussagen ueber Verluste (d) gelten **nur** fuer 18.09.2026 bis 27.09.2026 — so weit reicht `file-history` fuer `MEMORY.md` zurueck (aelteste Fassung `@v1`, 18.09. 13:04). Der Ordner enthaelt Dateien seit **Mai 2026**. Fuer 4½ Monate gibt es **keine** Historie und damit keine Aussage. Was dort verlorenging, ist nicht feststellbar.
- **Numerierungsluecken.** Neun Versionsnummern (`v2 v5 v6 v7 v8 v9 v17 v18 v19`) fehlen. Die Kette ist also auch innerhalb der neun Tage nicht lueckenlos.
- **Der ausloesende Zustand fehlt.** Der beobachtete 18 286-Byte-Stand kommt in keiner der 31 Fassungen vor. Was zwischen 17 441 (19:39) und 17 634 (23:20) genau geschah, konnte ich **nicht** messen.
- **Zeilenweise Verlustmessung ist ungenau.** Mein Verfahren ("Zeile war da, ist weg, steht heute nirgends") zaehlt jede **Umformulierung** als Verlust. Ich habe drei Uebergaenge stichprobenartig im Volltext nachgelesen und dort nur Umformulierungen gefunden — die uebrigen 19 Uebergaenge habe ich **nicht** einzeln nachgelesen. Die Aussage "kein Verlust" ist auf Zeigerebene vollstaendig gemessen, auf Textebene nur stichprobenartig.
- **Zielinhalte nicht gegengelesen.** Ich habe fuer **einen** kondensierten Detailwert geprueft, ob er in der Zieldatei ueberlebt hat. Fuer die uebrigen Verdichtungen nicht.
- **Agentenzahl nicht ermittelt.** Ein Unteragent ist im Dateisystem nicht von seinem Hauptlauf unterscheidbar. Die Zahl unter e) ist eine Zahl **von Sitzungen**, nicht von Schreibern.
- **Andere Schreibwege nicht ausgeschlossen.** Ich habe zwei Sitzungsprotokolle nach `Write`/`Edit`/Python durchsucht. Die sieben kleineren Protokolle und alle Schreibvorgaenge eines Speicher-Teilsystems (das die 99 Frontmatter-Dateien anlegt) sind **nicht** ausgewertet. Ein Schreibweg, der dort sitzt, waere mir entgangen.
- **Keine Aussage ueber andere Maschinen.** Das Gedaechtnis wird laut Index zwischen zwei Anthropic-Konten geteilt. Ob es auf einem zweiten Rechner eine weitere Kopie mit eigenen Schreibern gibt, habe ich **nicht** gemessen und kann es von hier aus nicht.
- **Kein Schreibversuch.** Der Verlustfall unter b) ist **konstruiert**, nicht ausgeloest. Es gibt dafuer keinen experimentellen Beleg, nur den gemessenen Schreibweg und seinen fehlenden Riegel.
