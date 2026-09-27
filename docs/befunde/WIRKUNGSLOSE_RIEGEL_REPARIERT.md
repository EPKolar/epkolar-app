# Wirkungslose Riegel — repariert

Gearbeitet 27.09.2026, begonnen auf `HEAD = a26e2b0` (v3.9.961), abgeschlossen
auf `HEAD = 97cc02f` — **der Baum wurde von einem parallel arbeitenden Vorgang
weiterbewegt**, siehe „Vollständiger Lauf" am Ende.
Ausgangslage: `docs/befunde/WAS_LAEUFT_WIRKLICH.md`, Abschnitt (2) — die Fälle
sind dort **laufzeitgemessen** belegt, nicht geraten.

> **`index.html` wurde nicht angefasst.** Kein Edit, kein Write, kein sed.
> Alle Mutationsproben liefen auf **Kopien im Speicher**; am Ende jeder Probe
> steht der Byte-Vergleich gegen die Datei auf der Platte (`unverändert: True`).
> Es wurde nichts committet, nichts gepusht, nichts an der Datenbank gemacht.

Geändert wurden fünf Dateien, alle unter `tests/`, alle **strenger**:

| Datei | Fälle vorher | Fälle nachher |
|---|---|---|
| `tests/test_db_schema_assumptions.py` | 10 | 14 |
| `tests/test_tickets_xy_schema.py` | 2 | 4 |
| `tests/test_autopush_hook.py` | 11 | 15 |
| `tests/test_hook_order_static.py` | 2 | 6 |
| `tests/test_pdf_bautagebuch_v882.py` | 19 | 20 |

---

## Kurzfassung

| Fall | vorher | jetzt |
|---|---|---|
| (1) `_sbPatch tickets xPct/yPct`, zwei Dateien | **0** Zusicherungen, Schleife über leerer Menge, Muster brüchig | Grundgesamtheit belegt (20 Aufrufe), Klammern **gezählt**, 11 Köder + 10 Gegenproben je Datei |
| (2) `test_save_hook_uses_no_await_before_juprowapush` | **0** Zusicherungen, Bedingung strukturell nie erfüllbar | am Rumpf von `_juprowaSchedulePush` gemessen, leere Menge ist selbst ein Mangel, 7 Köder + 6 Gegenproben + Gegenprobe am echten Drain |
| (3) `test_no_hook_after_early_return_general` | **kein** `assert`, nur `print` | harte Zusicherung über 86 Komponenten + Selbstprobe gegen blind gewordene Anker, 5 Köder + 4 Gegenproben |
| (4) A4-Umkehrprobe `..._anker_des_alten_knopfes_ist_echt` | still (früher Ausstieg), und sie war der **einzige** Beleg für Riegel 1 | misst jetzt, ob der Anker noch zur Schreibweise der Datei passt; der fehlende Zweitschutz ist als Befund benannt |

**Alle vier Fälle sind jetzt wirksam.** Ein echter Mangel in `index.html` wurde
dabei **nicht** gefunden — die vier Riegel waren grün, weil sie nichts maßen,
nicht weil sie etwas verdeckten. Zwei Funde betreffen die Riegel selbst und
stehen unter „Befunde".

---

## (1) Zwei Schleifen über einer leeren Menge

`tests/test_db_schema_assumptions.py::test_no_xPct_yPct_in_tickets_patch`
`tests/test_tickets_xy_schema.py::test_no_xPct_yPct_write_to_tickets`

### Was wirkungslos war

```python
matches = re.findall(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}", text)
for m in matches:
    assert 'xPct' not in m, ...
    assert 'yPct' not in m, ...
```

Zwei Fehler, von denen jeder einzeln schon tödlich ist:

**(a) Das Muster ist brüchig.** `[^)]+` kann die schließende Klammer eines
Aufrufs *im Argument* nicht überqueren. Gemessen an der echten Datei mit
eingesetzter Regression:

| Mutation in `index.html` (Kopie) | altes Muster | neues Verfahren |
|---|---|---|
| `_sbPatch("tickets",t.id,{xPct:1,yPct:2});` | meldet | meldet |
| `_sbPatch("tickets",t.id,{xPct:pct(e.x),yPct:2});` | meldet | meldet |
| **`_sbPatch("tickets", String(t.id), {xPct:1});`** | **meldet NICHT** | **meldet** |
| Aufruf über zwei Zeilen | meldet | meldet |

**(b) Die Menge ist leer.** `tickets` wird über `_sbPatch` gar nicht
geschrieben; die Schleife lief nie, **null** Zusicherungen wurden ausgeführt,
beide Fälle meldeten grün. Damit sah der Zustand „alles in Ordnung" genau so
aus wie der Zustand „mein Regex ist kaputt" — und **das** ist der Grund, warum
Fehler (a) unbemerkt blieb. Eine leere Grundgesamtheit besteht keine Probe.

### Was jetzt geprüft wird

* **Klammern werden gezählt, nicht verboten**: `code_scan._klammer_zu`
  (dieselbe Zählung, die die Knopf-/Element-Abtaster seit v3.9.961 benutzen —
  sie überspringt Zeichenketten, sonst läuft die Bilanz an jeder Klammer in
  einem Text aus dem Tritt). Nicht nachgebaut.
* **Kommentare und Zeichenketten sind ausgenommen** (`code_scan.ist_code`).
  Ohne das erfüllt der Erklärkommentar zum Ausbau den Riegel selbst: von den
  **23** `_sbPatch`-Nennungen in `index.html` stehen **3 in Kommentaren**
  (Z3085 Changelog, Z29983, Z30001).
* **Die Grundgesamtheit wird zuerst belegt, dann die Abwesenheit behauptet.**
  Gemessen: **20** `_sbPatch`-Aufrufe im Code —
  `fahrzeuge` 7 · `arbeitsscheine` 4 · `workers` 3 · `users` 2 ·
  `werkzeuge` 1 · `time_entries` 1 · variabler Tabellenname 2 ·
  **`tickets` 0**. Der Riegel fordert ≥ 15 Aufrufe und mindestens die Tabelle
  `fahrzeuge`. Fällt der Auszieher aus, wird der Riegel **rot statt grün**
  (belegt: mit unkenntlich gemachtem `_sbPatch(` sinkt die Menge unter die
  Schranke).
* **Geprüft werden Schlüssel, nicht Vorkommen.** `{x: xPct*w}` liest `xPct`
  als Wert und schreibt keine `xPct`-Spalte — das darf nicht anschlagen.
  Erkannt werden `{a:1}`, `{"a":1}`, `{'a':1}` und die Kurzschreibung `{a}`.
* Der Auszieher liegt **einmal** in `test_db_schema_assumptions.py` und wird
  von `test_tickets_xy_schema.py` importiert. Zwei Kopien wären zwei
  Rechnungen — und die eine, die man beim Reparieren vergisst, ist genau die,
  die weiter nichts misst. Die **Zusicherungen** bleiben in beiden Dateien,
  damit jeder Fall sein eigenes Urteil fällt.

### Köder-Nachweis — einer je Form

Jede Zeile ist eine eigene Schreibweise, in der die Regression zurückkehren
könnte. Alle neun werden gefunden; die Liste läuft in **beiden** Dateien:

| # | Form | gefunden |
|---|---|---|
| A | `_sbPatch('tickets', id, {xPct:1,yPct:2})` | ja |
| B | `_sbPatch('tickets', t.id, {xPct: pct(e.x), yPct: 2})` | ja |
| C | `_sbPatch("tickets", String(t.id), {xPct:1})` — **hier lief das alte Muster vorbei** | ja |
| D | Aufruf über zwei Zeilen | ja |
| E | nur `yPct` | ja |
| F | verschachteltes Objekt davor: `{pos:{a:1}, xPct:1}` | ja |
| G | über `window._sbPatch(` | ja |
| H | Schlüssel in Anführungszeichen: `{"xPct":1}` | ja |
| I | Kurzschreibung: `{xPct}` | ja |
| J | Rumpf durch einen Abbilder gereicht: `_sbPatch('tickets', t.id, _mapBody({xPct:1}))` | ja |
| K | Rumpf in runden Klammern: `({yPct:1})` | ja |

> **Form J ist ein Fund an meinem eigenen Riegel.** Meine erste Fassung nahm
> nur Objektliterale auf der *obersten Argumentebene* und war damit für
> `_mapBody({…})` blind — einer Schreibweise, die im Bestand **vorhanden** ist:
> `_sbPatch("arbeitsscheine",existing.id,_mapBody(upd))` (`index.html:3950`).
> Ein Riegel, der eine im Repo vorhandene Schreibweise nicht kennt, ist
> dieselbe Krankheit, gegen die er gebaut wurde. Aufgefallen ist es nur, weil
> ich die echten Aufrufformen durchgesehen habe, statt mir die Köder
> auszudenken. Gefunden **bevor** der Riegel abgenommen war; die Form ist
> jetzt Köder J und in der Mutationsprobe an der echten Datei belegt.

### Gegenprobe — was **nicht** gemeldet werden darf

| Fall | gemeldet |
|---|---|
| andere Tabelle (`fahrzeuge`) | nein |
| richtige Spalten (`{x:1,y:2}`) | nein |
| Tabellenname als Präfix (`tickets_log`) | nein |
| Nennung nur im **Kommentar** | nein |
| Nennung nur in einer **Zeichenkette** | nein |
| ähnlicher Funktionsname (`_xsbPatch`) | nein |
| `xPct` nur als **Wert** gelesen (`{x: xPct*w}`) | nein |
| Lesen statt Schreiben (`_sbGet('tickets', …)`) | nein |
| `xPct` als Schlüssel eines **verschachtelten** Objekts (`{meta:{xPct:1}}`) | nein |
| Abbilder-Rumpf einer **anderen** Tabelle (`_sbPatch('fahrzeuge', id, _mapBody({xPct:1}))`) | nein |

Ein Zähler, der alles meldet, schlägt bei jedem Köder an und ist trotzdem
kaputt — deshalb zehn Gegenproben gegen elf Ködern. Die letzten beiden sind
die Gegenprobe zur Lockerung aus Form J: sie belegen, dass die Lockerung nicht
alles einsammelt.

### Mutationsprobe an der echten Datei

Sechs Regressionen wurden in eine **Kopie** der echten `index.html`
(3 676 134 Zeichen) eingesetzt (Formen A–D, J, K): neuer Riegel **6 von 6
rot**, unmutiert grün, Grundgesamtheit nicht leer. Das alte Muster war bei
Form **C grün**.

### Zusätzlich festgehalten

`test_das_alte_muster_war_bruechig_und_bleibt_es` hält den Grund fest, aus dem
das Muster ersetzt wurde. Kippt dieser Fall, hat jemand das alte `[^)]+`
reparieren können — dann gehört *der Fall* weg, nicht der Riegel.

---

## (2) Eine Bedingung, die strukturell nie zutreffen konnte

`tests/test_autopush_hook.py::test_save_hook_uses_no_await_before_juprowapush`

### Was wirkungslos war

```python
for i, line in enumerate(index_html.splitlines()):
    if "_juprowaPush(" in line and "AUTOPUSH" in line:
        assert ".then(" in line, ...
```

`_juprowaPush(` steht in 7 Zeilen, `AUTOPUSH` in 2 — in **0** Zeilen beides.
Die beiden `AUTOPUSH`-Marken sitzen auf der `.then()`/`.catch()`-Fortsetzungs­
zeile (`index.html:4285/4286`), nie auf der Aufrufzeile (`:4283`). **Null**
Zusicherungen, grün. Eine Zeile ist keine Struktur.

### Welche Eigenschaft gemeint war — und woran das festzumachen ist

Name und Docstring sagen es: im **Speicher-Haken** darf `_juprowaPush` nicht
`await`ed werden, sondern muss fire-and-forget laufen („`.then(…)` chains
instead of await"). Der Messort war falsch, nicht die Absicht.

Wo der Speicher-Haken steht, ist eindeutig bestimmbar: seit v3.9.756 ist es
die per-Schein-Debounce-Klammer `_juprowaSchedulePush` (`index.html:4273`).
Genau so benennt sie auch der Nachbarfall `test_save_hook_has_online_guard` im
selben Bündel, unabhängig von mir. Gemessen im Rumpf: **1** `_juprowaPush`-
Aufruf, kein `await` davor, `.then(` dahinter.

**Die Abgrenzung ist der Kern**: `await` ist an drei anderen Stellen richtig —
`_juprowaDrainPending` (`:4234`), `_juprowaPushAll` (`:4253`) und der
Einzel-Push auf Knopfdruck (`:10847`). Deshalb darf der Riegel nicht über die
ganze Datei laufen. `index.html` wurde nicht geändert; `_juprowaPush` ist dafür
ohnehin gesperrt.

### Was jetzt geprüft wird

* Gemessen wird über die **Funktionsgrenze** (`_extract_fn`), nicht über die
  Zeilengrenze.
* Je Aufruf: kein `await` unmittelbar davor, und `.then(` oder `.catch(`
  dahinter — hinter der **passenden** schließenden Klammer
  (`code_scan._klammer_zu`), damit `_juprowaPush(String(_id)).then(…)` nicht an
  der inneren Klammer abreißt. Der nackte Aufruf ohne Kette ist ein Mangel
  (unbehandelte Ablehnung).
* Kommentare und Zeichenketten sind über `code_scan.ist_code` ausgenommen.
* **Eine leere Grundgesamtheit ist selbst ein Mangel.** Findet sich im Haken
  kein Aufruf, ist der Riegel **rot**, nicht grün. Genau dieser Zustand galt
  hier zwei Jahre als grün.

### Köder-Nachweis — einer je Form

| # | Form | gefunden |
|---|---|---|
| A | `var r=await _juprowaPush(_id);` | ja |
| B | `await _juprowaPush(_id);` direkt | ja |
| C | `return await _juprowaPush(_id);` | ja |
| D | `await  _juprowaPush(_id).then(…)` — `await` **und** `.then` | ja |
| E | nackter Aufruf ohne Kette | ja |
| F | `await _juprowaPush(String(_id));` — innere Klammer | ja |
| G | **leerer Haken, gar kein Aufruf** | ja |

G ist der wichtigste: ohne ihn kehrt genau der alte Befund zurück.

### Gegenprobe

| Fall | gemeldet |
|---|---|
| die echte Form `.then(…).catch(…)` | nein |
| nur `.catch(` | nein |
| `await` nur im **Kommentar** | nein |
| `await` nur in einer **Zeichenkette** | nein |
| Umbruch vor `.then(` | nein |
| innere Klammer im Argument | nein |

Dazu eine Gegenprobe **am echten Code**, die kein Köder ist:
`test_gegenprobe_der_drain_darf_awaiten` wendet dieselbe Prüfung auf
`_juprowaDrainPending` an und verlangt, dass sie dort **anschlägt**. Schlägt
sie dort nicht an, kann sie `await` überhaupt nicht erkennen — und das Grün im
Speicher-Haken wäre wertlos.

### Mutationsprobe an der echten Datei

Drei Regressionen in den echten Haken eingesetzt plus der leere Haken:
neuer Riegel **4 von 4 rot**, unmutiert grün.
**Der alte Riegel war bei allen vier Mutationen grün** — auch bei einem
`await` direkt vor dem Push.

### Zusätzlich festgehalten

`test_das_alte_muster_konnte_nicht_zutreffen` hält den Befund fest: `_juprowaPush(`
und `AUTOPUSH` haben **null** gemeinsame Zeilen. Kippt das, hat jemand die
Marken auf die Aufrufzeile geholt — dann gehört *dieser Fall* weg.

---

## (3) Ein `print` statt einer Prüfung

`tests/test_hook_order_static.py::test_no_hook_after_early_return_general`

### War es Absicht?

Der Docstring sagte ja: „App-Pfad ist abgedeckt vom ersten Test, deshalb nur
Warning via stdout für Rest". **Die Begründung trägt nicht.** Der erste Test
deckt ausschließlich `App` ab; die anderen **86** Komponenten deckt er gar
nicht, und React-#310 entsteht in jeder Komponente gleich. Eine Warnung in
stdout sieht in einem `-q`-Lauf niemand.

Die Historie liefert keine zweite Begründung: `git log -- tests/test_hook_order_static.py`
zeigt **einen einzigen** Commit (`1eb4bfc`, „docs: PlanRadar ① als geliefert
markiert…"), ohne Hinweis auf eine gewollte Weichheit. Die Datei ist also nie
bewusst weich gestellt, sondern nur nie hart gestellt worden.

**Entscheidung: harte Zusicherung.** Gemessen **vor** dem Umbau gegen den
heutigen Bestand:

```
betrachtete Komponenten (ohne App):     86
davon mit Hook zwischen zwei returns:    0
Hook-Zeilen auf Einzug 2 im Bestand:   213
return-Zeilen auf Einzug 2 im Bestand: 486
```

Die Menge ist nicht leer und die Zusicherung ist heute grün — es wird also ein
**abgeschalteter Riegel eingeschaltet**, kein roter umgeschrieben.

### Was jetzt geprüft wird

* `komponenten(lines)` und `verdachte(lines)` sind aus dem Test
  herausgezogene **reine Funktionen** — nur dadurch kann der Köder sie mit
  selbstgebauten Zeilen füttern. Der Gang durch die Datei ist wörtlich der
  alte.
* Die Fundliste steht jetzt in der **Fehlermeldung** statt in stdout.
* Neu: `test_selbstprobe_die_anker_treffen_den_bestand`. `HOOK_RE` und
  `RETURN_RE` hängen an der Schreibweise des Bündels (`  _react.useState(`,
  Einzug 2). Ändert der Erzeuger diese Schreibweise, treffen beide Ausdrücke
  **null** Zeilen — und dann melden `test_no_hook_after_early_return_in_App`
  **und** der allgemeine Fall grün, ohne etwas gemessen zu haben. Das ist der
  stille Ausfall, gegen den beide Fälle dieser Datei vorher wehrlos waren.
  Belegt: mit unkenntlich gemachtem `_react.` fällt die Selbstprobe unter ihre
  Schranke.

Der Abtaster `_violations_in_span` selbst wurde **nicht** angefasst — beide
Fälle teilen ihn, eine Änderung dort hätte den App-Fall mitverschoben.

### Köder-Nachweis

| # | Form | gefunden |
|---|---|---|
| A | Hook zwischen zwei `return` | ja |
| B | `useEffect` statt `useState` | ja |
| C | nackter `return` als Grenze | ja |
| D | zwei Hooks in einer Komponente | ja |
| E | zweite Komponente nach einer heilen | ja |

### Gegenprobe

| Fall | gemeldet |
|---|---|
| Hooks **vor** dem ersten `return` | nein |
| `App` (hat seinen eigenen Fall) | nein |
| kleingeschriebene Hilfsfunktion | nein |
| Hook auf tieferem Einzug | nein |

Dazu `test_selbstprobe_eine_leere_menge_wird_als_leer_erkannt`: die
Grundgesamtheits-Wache muss eine ausgefallene Messung sehen können, sonst wäre
sie selbst die nächste stille Prüferin.

### Mutationsprobe an der echten Zeilenliste

Eine Komponente mit Hook zwischen zwei `return` in die echte Zeilenliste
eingesetzt → **rot**. Unmutiert grün, 86 Komponenten in der Menge.

---

## (4) Die stille A4-Umkehrprobe

`tests/test_pdf_bautagebuch_v882.py::test_umkehrprobe_anker_des_alten_knopfes_ist_echt`

### Was wirkungslos war

```python
treffer = index_html.count(_PDF_KNOPF_ALT)
if "_genBautagPdf" in index_html:
    return                       # Patch ist da
assert treffer == 1, ...
```

Der Ausstieg ist **richtig** — der Patch ist da, der alte Knopf ist weg. Die
Folge ist trotzdem ein blinder Fleck: diese Umkehrprobe war der Beleg, dass der
Anker von **Riegel 1** (`assert _PDF_KNOPF_ALT not in index_html`) überhaupt
trifft. Riegel 1 behauptet eine **Abwesenheit** — und eine Abwesenheitsaussage
ist nur so viel wert wie der Beleg, dass ihr Anker eine Rückkehr erkennen
würde.

### Gemessen: ist der Anker woanders geschützt? **Nein.**

| Geprüft | Ergebnis |
|---|---|
| `_PDF_KNOPF_ALT` in anderen Testdateien | kommt in **genau einer** Datei vor — dieser |
| `tests/test_company_footer_v3920.py` (prüft alle `xBtn('pdf')`-Knöpfe) | verlangt `window.print()` **oder** einen eigenen Erzeuger (`_wpPrintPlan`, `_genBautagPdf`). Ein Rückfall des Bautagebuch-Knopfes auf `window.print()` wäre dort **grün** |
| sonstige Riegel, die den Knopf nennen | keine |

**Das ist der Befund: Riegel 1 ist der einzige Schutz gegen die Rückkehr des
nackten `window.print()`-Knopfes im Bautagebuch — und er stand ohne lebenden
Beleg.**

### Was jetzt geprüft wird

Statt auszusteigen misst die Umkehrprobe, ob der Anker noch zur
**Schreibweise der Datei** passt. Der Anker ist ein wörtliches
Zeichenkettenstück; wird der Knopf künftig als `h('button',{onClick:…`
geschrieben oder das Leerzeichen hinter `{` entfernt, trifft er nie mehr — und
Riegel 1 wäre für immer grün, ohne dass sich etwas gebessert hätte.

Gemessen am Bestand (27.09.2026):

| Ankerteil | Vorkommen in `index.html` |
|---|---|
| `btEntries.length>0&&React.createElement('button', { onClick: ()=>` | 1× |
| `style: xBtn("pdf")` | 5× |
| `window.print()` | 18× |
| **ganzer Anker `_PDF_KNOPF_ALT`** | **0×** (Riegel 1 grün) |

Zuerst wird belegt, dass die Teile **aus dem Anker selbst** stammen (sonst
misst die Probe einen anderen Gegenstand als Riegel 1), dann, dass jeder Teil
in `index.html` noch vorkommt. Der Zweig für den Fall „Patch fehlt" bleibt
erhalten; **beide** Zweige tragen jetzt Zusicherungen, keiner ist still.

### Köder / Gegenprobe

* **Mutationsprobe:** Schreibweise des Knopfes in einer Kopie auf
  `h('button',{onClick:()=>` umgestellt → Umkehrprobe wird **rot** und
  verlangt, den Anker nachzuziehen.
* **Riegel 1 wird rot**, wenn der alte Knopf in eine Kopie zurückgebaut wird.
* **Neue Gegenprobe** `test_umkehrprobe_riegel_1_unterscheidet_alt_und_neu`:
  das Kriterium von Riegel 1 erkennt den alten Knopf in einem synthetischen
  Text **und** meldet den reparierten Knopf **nicht**. Ein Kriterium, das bei
  jedem Stand anschlägt, belegt nichts.

---

## Befunde

**Kein Mangel in `index.html`.** Die vier Riegel waren grün, weil sie nichts
maßen — nicht, weil sie etwas verdeckten. Jede Mutationsprobe bestätigt: der
heutige Bestand ist an allen vier Stellen in Ordnung.

Drei Funde betreffen die Riegel selbst:

1. **Riegel 1 des Bautagebuch-PDFs hat keinen Zweitschutz.** Siehe (4). Nicht
   gebaut, weil ein zweiter Riegel („der Knopf *ruft* `_genBautagPdf`") ein
   neuer Riegel wäre und nicht in den Auftrag gehört. **Empfehlung:** einen
   Riegel bauen, der den Bautagebuch-Knopf positiv prüft (`onClick` ruft
   `_genBautagPdf`), statt nur die Abwesenheit des alten zu behaupten — ein
   positiver Riegel kann nicht durch einen veraltenden Anker verstummen.

2. **`_violations_in_span` hat ein Loch**
   (`tests/test_hook_order_static.py`): bei `len(returns) < 2` gibt die
   Funktion leer zurück. Eine Komponente mit **genau einem** early-return, hinter
   dem ein Hook steht, wird nicht gemeldet — also genau die Form, die der
   Docstring als Ursache von v3.8.50 nennt. Nicht repariert, weil
   `test_no_hook_after_early_return_in_App` denselben Abtaster benutzt: eine
   Verschärfung wirkt dort mit und gehört einzeln gemessen und beurteilt, nicht
   im Vorbeigehen. Die Grenze steht jetzt als Kommentar an der Funktion.

3. **Beide Fälle in `test_hook_order_static.py` waren gegen den stillen
   Ausfall wehrlos**: hätte der Bündel-Erzeuger `  _react.useState(` anders
   geschrieben, hätten beide grün gemeldet, ohne etwas zu messen. Das ist mit
   `test_selbstprobe_die_anker_treffen_den_bestand` geschlossen.

---

## Was ich **nicht** reparieren konnte, und warum

* **`test_pdf_bautagebuch_v882.py::test_10_toter_print_stz_selektor_hat_ein_ziel_oder_ist_weg`**
  (Befund A3) steigt ebenfalls früh aus (`if not styled: return`) und prüft
  heute nichts mehr. Er stand **nicht** im Auftrag und ist unangetastet
  geblieben. Anders als bei A4 ist der Ausstieg hier auch harmlos: die
  CSS-Regel wurde entfernt, es gibt keinen zweiten Riegel, den dieser Fall
  belegen müsste. Er wäre trotzdem ehrlicher als Köder gegen seinen eigenen
  Sucher gebaut.

* **Das Loch in `_violations_in_span`** (Befund 2 oben) — begründet dort.

* **Die 31 ungeprüften Verdachte aus Klasse D** von
  `WAS_LAEUFT_WIRKLICH.md` sind nicht angefasst; jeder braucht einen Blick auf
  die Absicht des Falls.

* **`tests/test_nichtgemessen_v909.py`** (18 Prüffälle, in keiner Kette, weil
  ohne `def test_*`) stand nicht im Auftrag und ist unangetastet. Es wäre eine
  Änderung an einer nicht genannten Datei.

* **Keine Mutationsprobe für die drei neuen Selbstproben selbst.** Die Köder
  belegen, dass die Riegel anschlagen; dass sie es auch dann tun, wenn *pytest*
  sie gar nicht sammelt, belegt nur der Lauf — und der ist grün.

* **`index.html` ist im Baum als geändert vermerkt — nicht von mir.** Das
  kommt aus dem parallelen Vorgang. Mein Schlussurteil (Lauf 3) ist damit
  gegen eine `index.html` gemessen, die nicht mehr die vom Auftragsbeginn ist.
  Das ist gewollt vermerkt und nicht verschwiegen: es heißt, dass die
  Ankerzahlen oben (20 Aufrufe, 86 Komponenten, 1×/5×/18× Ankerteile) zum
  Stand von 27.09. gegen Mittag gehören, nicht zwangsläufig zum Stand nach dem
  nächsten Commit dieses Vorgangs. Die Riegel selbst bleiben davon unberührt —
  sie sind alle drei mit Untergrenzen statt festen Zahlen gebaut.

* **Keine Aussage über die restlichen ~3 200 Fälle.** Dieser Bericht spricht
  ausschließlich über die fünf geänderten Dateien. Was dieser Aufbau nicht
  abdeckt, ist kein Kleingedrucktes: alle anderen Riegel sind hier weder
  gemessen noch verbessert worden.

---

## Nachvollziehen

```
python -m pytest tests -q
python -m pytest tests/test_db_schema_assumptions.py tests/test_tickets_xy_schema.py \
                 tests/test_autopush_hook.py tests/test_hook_order_static.py \
                 tests/test_pdf_bautagebuch_v882.py -q
```

Die Mutationsproben liefen aus einem Wegwerfskript im Ablagebereich (nicht im
Repo angelegt): es liest `index.html`, mutiert **Kopien im Speicher**, ruft die
reinen Prüfkerne der fünf Dateien und vergleicht am Ende die Datei auf der
Platte byteweise gegen den Anfangsstand. Ergebnis: **26 von 26 Proben richtig,
0 Fehler, `index.html unverändert: True`** (plus zwei Nachzügler für die
Formen J und K, beide richtig).

### Vollständiger Lauf

```
3230 passed, 11 skipped, 8 xfailed in 419,73 s     Rückgabewert 0
```

Urteil aus der Logdatei gelesen, nicht hinter einer Pipe.
**Kein fremder Fall ist rot.** Die Zahl setzt sich zusammen aus
3210 (Ausgangsstand) + **15 von mir** + 5 aus einer parallel angelegten
fremden Datei (siehe unten).

Drei Läufe, und die beiden ersten sind lehrreich:

| Lauf | Ergebnis | Urteil |
|---|---|---|
| 1 | 3225 passed, 0 rot, **9:13** | grün, aber die Zeit ist wertlos: ich habe die Mutationsskripte auf derselben Maschine parallel laufen lassen, und die tasten `index.html` mehrfach zeichenweise ab. Eine Zeitmessung unter selbstgemachter Last misst die Maschine, nicht die Prüfung. |
| 2 | **1 failed**, 3224 passed | `test_jede_datei_wird_eingesammelt_v961.py::test_jede_testdatei_hat_faelle_beigetragen` — und zwar über `tests/test_geschuetzte_funktionen_v961.py`, eine Datei, die ich **nicht angelegt und nicht angefasst** habe. Sie entstand um **15:26:37 mitten im Lauf** durch einen parallel arbeitenden Vorgang. Nachgemessen: sie sammelt jetzt sauber **5** Fälle ein (`--collect-only`, Rückgabewert 0). Es war ein Wettlauf mit einer entstehenden Datei, kein Befund. |
| 3 | **3230 passed, 0 rot, 6:59** | das Urteil. |

> **Der Baum hat sich während der Arbeit bewegt.** `HEAD` wanderte von
> `a26e2b0` auf `97cc02f` („Torkette: drei Tore, die es schon gab und die
> NIRGENDS liefen"). Ein parallel arbeitender Vorgang hat zusätzlich
> `index.html`, `sw.js`, `docs/ENTSCHEIDUNGEN-OFFEN.md` und drei weitere
> Testdateien geändert und mehrere `scripts/befund_*.py` sowie
> `docs/befunde/DIE_31_VERDACHTE.md` / `DIE_FUENFZEHN_LESER.md` angelegt.
> **Keine dieser Änderungen kommt von mir** — meine fünf Dateien stehen
> unverändert als geändert im Baum. Aufgefallen ist es nicht an der Zahl
> (3225 → 3230 wäre als Rauschen abzutun gewesen), sondern am **Namen** der
> einen roten Prüfung.
