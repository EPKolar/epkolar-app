# Die 31 Verdachte — beurteilt

Gemessen 27.09.2026, 14:50–16:10. Stand: `git HEAD = a26e2b0` (v3.9.961),
`3210 passed, 11 skipped, 8 xfailed in 306,96 s`, **Rückgabewert 0**, aus der
Logdatei gelesen. HEAD war vor und nach dem Lauf derselbe (`head_vor.txt` /
`head_nach.txt`).

Grundlage ist `docs/befunde/WAS_LAEUFT_WIRKLICH.md` §2, „Ungeprüft — 31
Verdachte": Fälle, die Zusicherungen ausführten, aber **mindestens eine** leere
Grundgesamtheit neben gefüllten hatten (Klasse D).

`index.html` wurde **nicht angefasst** (`git diff -- index.html` ist leer).
Keine bestehende Prüfung wurde geändert. Neu sind nur
`scripts/befund_31_muster.py`, `scripts/befund_31_mutation.py` und dieser
Bericht.

---

## 0. Zuerst: die Zahl 31 ist nicht nachvollziehbar

Der Vorbericht nennt **31**. Sein eigenes Werkzeug auf seiner eigenen Messdatei
nennt **28**.

```
python scripts/befund_wirkung.py wirkung2.json
  A) 4     B) 2     C) 3     E) 0     F) 0
  D) VERDACHT: einzelne leere Grundgesamtheit, andere Zusicherungen liefen: 28
```

Die Messdatei ist zweifelsfrei die des Vorberichts — alle übrigen Kennzahlen
stimmen aufs Stück: 38653 Grundgesamtheiten, davon 31495 leer, in 653 Fällen,
9867 ausgeführte Zusicherungen, 3177 passed / 19 skipped+xfailed, A=4 B=2 C=3.

**Kann 31 aus einem anderen Zustand von `tests/` entstanden sein?** Nein. Die
Klassengrenze D hängt nur an einer Stelle von der Statik ab. Gemessen,
statikunabhängig (`empfindlich.py`):

```
Faelle mit TEILWEISE leerer Grundgesamtheit, unabhaengig von Statik: 29
davon mit asserts==0 (Statik entscheidet A/B vs D):                   1
   tests/test_hook_order_static.py::test_no_hook_after_early_return_general
=> D kann bei KEINEM Zustand von tests/ ueber 29 steigen.
```

Die Obergrenze in jener Messung ist **29**, und der 29. ist der Fall, den der
Vorbericht bereits als Befund **A2** führt. Die **31** ist also eine
Verschreibung — am ehesten aus `31495`.

**Was ich stattdessen beurteile:** die 28 aus dem Stand `ce397e9` **und** den
Stand von heute. Bei `HEAD = a26e2b0` sind es **33**: dieselben 28 plus fünf
Fälle aus `tests/test_zusammengesetzte_knopfnamen_v960.py`, einer Datei, die es
am `ce397e9` noch nicht gab. Kein einziger der 28 ist weggefallen.

```
nur ce397e9 (0):   —
nur a26e2b0 (5):   test_zusammengesetzte_knopfnamen_v960.py  (5 Faelle)
beide:            28
```

Damit deckt die Beurteilung jede Lesart von „die 31" ab. Die Nummern D01–D28
sind die des Standes `ce397e9`, D29–D33 die fünf neuen.

---

## 1. Wie geurteilt wird

Der Auftrag gibt die Regel vor: eine leere Menge ist **berechtigt**, wenn die
Prüfung eine Abwesenheit behauptet, die Abwesenheit echt ist, **und** ein Köder
belegt, dass die Prüfung etwas finden *könnte*.

Daraus die Entscheidungsregel, die hier auf jeden der 33 angewandt wird:

| | |
|---|---|
| **berechtigt** | Die leere Menge ist entweder eine einzelne Runde einer Schleife, deren Stelle im selben Lauf auch gefüllt war (dann ist der Sucher zur Laufzeit nachweislich lebendig), oder eine echte Abwesenheit, für die ein Köder **je Form** belegt, dass der Sucher zuschlägt. |
| **Ausfall** | Die Prüfung behauptet eine Abwesenheit, und eine **Mutationsprobe** zeigt: eine Form dieser Verletzung lässt sie **grün**. Die Grundgesamtheit kann den Fall nicht enthalten, den die Prüfung ausschließt. |
| **nicht entscheidbar** | Weder das eine noch das andere messbar. |

### Das Messgerät für „war die Stelle jemals gefüllt?"

Das Plugin `scripts/riegel_wirkung_plugin.py` schreibt **je Ausführung** einer
Kurzschreibung oder `for`-Schleife einen Eintrag. Ein Fall mit 27301 Einträgen
hat nicht 27301 Grundgesamtheiten, sondern **eine Stelle, die 27300-mal lief**.
Entscheidend ist deshalb nicht „wie viele Mengen waren leer", sondern:

> War **diese Stelle** im selben Lauf jemals gefüllt?

Ist sie es, war der Sucher lebendig und die leere Runde ist eine Runde.
War sie es nie, ist es ein echter Verdacht. `sites.py` rechnet das je Stelle
aus, im Fall **und** über die ganze Datei. Ergebnis: von den 28 haben **19**
nur Stellen mit gefüllten Geschwistern; **9** tragen mindestens eine Stelle,
die im ganzen Lauf nie gefüllt war — das sind die, die einzeln belegt werden
mussten.

---

## 2. Die Tabelle

Spalte **Stelle**: `**` = im ganzen Lauf nie gefüllt (echter Verdacht),
`+` = im Fall nie, in einem anderen Fall derselben Datei schon,
`·` = dieselbe Stelle war im selben Fall auch gefüllt.

| Nr | Datei · Fall | erwartete Grundgesamtheit | tatsächlich | Stelle | Urteil | Beleg |
|---|---|---|---|---|---|---|
| D01 | `test_ausgetretene_live_v931` · `test_00_der_aufbau_sieht_den_ausgetretenen` | Rümpfe, die ins Node-Programm gehängt werden | **0 — absichtlich**: `_lauf(quelle, tmp, "koeder.js", [], [])` | + | **berechtigt** | Der Fall IST der Köder der Datei. 9 Zusicherungen liefen auf gefüllten Mengen (`satz.items()` 27×, `aus['praedikat']`). Datei: 3 `test_5x_gegenprobe_*`. |
| D02 | `test_b3_stufen_4_7_v942` · `…unter_12_px_schrift` | `font-size:…px` je Header-Regelblock | 5 Blöcke, 4 mit Fund, **1 ohne** | · | **berechtigt** | Stelle 4× gefüllt. In-Fall-Schranke `assert len(stellen) >= 3` mit der Meldung „KOEDER STUMM". |
| D03 | `test_b3_stufen_4_7_v942` · `…unter_44_px` | `min-height:…px` je Header-Regelblock | 5 Blöcke, 3 mit Fund, **2 ohne** | · | **berechtigt** | Stelle 3× gefüllt. **Mutationsprobe:** `.header-row .mob-stack button{min-height:20px}` → **rot**; dieselbe Regel unter anderem Selektor → **grün**. |
| D04 | `test_b6_schrift_und_medien_v943` · `…unter_zehn_px_im_code` | Treffer je Schriftgrößen-Muster | 3 Muster, 2 mit Fund, **1 ohne** | · | **berechtigt** | Stelle 2× gefüllt; der Fall führt zusätzlich ein `koeder`-Wörterbuch (`koeder.values()`, gefüllt). |
| D05 | `test_d9_seitenueberschriften_v956` · `…keine_erfundene_ueberschrift` | h1/h2/h3-Elemente in 4 Ansichten | **0** in allen vier — das ist die Behauptung | + | **berechtigt** | Muster kennt **beide** Erzeuger und **beide** Anführungszeichen: 4/4 Köder treffen, 2/2 Gegenproben (`search('h2')`, `obj.h('h2')`) schweigen. 32 Überschriften im Gesamttext. Datei: `test_der_riegel_wird_bei_einer_erfundenen_ueberschrift_rot`. |
| D06 | `test_finkzeit_kommentar_stimmt_v959` · `…bei_einer_neuen_behauptung_rot` | Anführungszeichen je Kommentar / Phrasenfunde | 12 Kommentare, **2 ohne** Anführungszeichen; 7 Phrasen, **1** ohne Fund | · | **berechtigt** | Beide Stellen 10× bzw. 6× gefüllt. Datei: 2 Selbstproben. |
| D07 | `test_finkzeit_kommentar_stimmt_v959` · `…ein_zitat_macht_den_riegel_NICHT_rot` | Phrasenfunde | 14, **2 ohne** | · | **berechtigt** | Stelle 12× gefüllt. Der Fall ist selbst eine Gegenprobe. |
| D08 | `test_finkzeit_kommentar_stimmt_v959` · `…kein_kommentar_widerspricht_der_fahne` | Phrasenfunde | 7, **1 ohne** | · | **berechtigt** | Stelle 6× gefüllt. |
| D09 | `test_freie_variablen` · `test_5_keine_neuen_freien_variablen` | freie Variablen in `index.html`; `BASISLINIE` | **0 Funde**, `BASISLINIE = {}` (Z60, absichtlich leer) | ** | **berechtigt** | Im selben Fall wird die **Messmenge** zugesichert: `assert bloecke >= 1` und `assert zeichen >= 1_000_000` — „0 Treffer" ist ohne sie wertlos, und genau das steht dort. Datei: `test_3_gegenprobe_riegel_kann_rot_werden` (baut einen freien Bezeichner in den ECHTEN `index.html` ein) und `test_4_kaputte_datei_ist_nicht_sauber` (rc muss 3 sein). Beide grün im Lauf. |
| D10 | `test_hook_order_static` · `test_no_hook_after_early_return_in_App` | Hooks zwischen erstem und letztem `return` im App-Rumpf | **0** — die Behauptung. `violations[:5]` ist nur die Meldungskürzung | ** | **berechtigt** | Die *entscheidende* Menge `hooks` war **gefüllt**, `returns` ≥ 2. **Mutationsprobe:** `  _react.useState(0);` hinter den ersten `return` im App-Rumpf → **rot** (rc=1). |
| D11 | `test_hotfix_sync_v3131` · `test_antwortzweige_tragen_den_status` | Antwortzweige ohne Status | `_luecken()` = **0** — die Behauptung | ** (Z224) | **berechtigt** | Im selben Fall: `assert len(antwort) >= 30` („Ein Scanner, der nichts mehr findet, ist grün und nutzlos"). Datei: `test_umkehrprobe_verlorener_status_wird_rot` baut den Status zurück und fordert **genau eine Lücke mehr** — grün im Lauf. |
| D12 | `test_hotfix_sync_v3131` · `test_benannte_antwortzweige_werden_erkannt` | `.status===NNN`-Zahlen je Zweig | 38 Zweige, **26 ohne** Zahl | · | **berechtigt** | Stelle 12× gefüllt; nachgelagerte Mengen (`alle`, `treffer`) je 7× gefüllt. |
| D13 | `test_hotfix_sync_v3131` · `test_nicht_antwortwuerfe_bleiben_draussen` | dito | 38, **26 ohne** | · | **berechtigt** | Stelle 12× gefüllt. |
| D14 | `test_hotfix_sync_v3131` · `test_offene_luecken_laufen_ab` | Einträge in `_OFFENE_LUECKEN` | `_OFFENE_LUECKEN = []` (Z84) → Schleife läuft **nie** | ** | **berechtigt** | Eine leere Ausnahmeliste ist der gewollte Zustand; es gibt nichts Abgelaufenes zu finden. **Hinweis:** der Fall führt heute **keine eigene** Zusicherung aus — die 77 gezählten stammen aus dem Helfer `_wuerfe`. Er ist harmlos, aber leer. |
| D15 | `test_hotfix_sync_v3131` · `test_umkehrprobe_verlorener_status_wird_rot` | dito | 116, **80 ohne** | · | **berechtigt** | Stelle 36× gefüllt; der Fall ist selbst die Umkehrprobe. |
| D16 | `test_keine_denkmaeler` · `test_fliesstext_in_docstrings_zaehlt_nicht` | Dekoratoren je Funktion | 1 Funktion **ohne** Dekorator | + | **berechtigt** | Stelle im Lauf **69×** gefüllt. Eine Funktion ohne Dekorator ist der Regelfall. |
| D17 | `test_keine_denkmaeler` · `test_kein_pin_sichert_eine_ungelesene_groesse` | Dekoratoren / Knotenlisten / Pins je Testdatei | 5074 Runden, **3927 leer** | · | **berechtigt** | Alle drei Stellen auch gefüllt (68 / 463 / 151). 464 Dateien abgetastet. |
| D18 | `test_keine_denkmaeler` · `test_not_in_zusicherungen_werden_nicht_bemaengelt` | Dekoratoren | 1 ohne | + | **berechtigt** | wie D16. |
| D19 | `test_keine_denkmaeler` · `test_stillgelegte_pins_zaehlen_nicht` | Dekoratoren / Knoten | je 1 ohne, je 1 mit | · | **berechtigt** | beide Stellen im Fall gefüllt. |
| D20 | `test_keine_denkmaeler` · `test_umkehrprobe_der_riegel_kann_rot_werden` | Dekoratoren | 1 ohne | + | **berechtigt** | wie D16; der Fall ist die Umkehrprobe der Datei. |
| D21 | `test_projekt_cache_v927` · `…gehen_ueber_saveProj_und_loadProj` | `ODB.save/load/get/set("docs_…` u. 3 weitere Präfixe | **0 in BEIDEN Anführungszeichen** (gemessen, nicht geschlossen) | ** | **berechtigt** | Gegenzähler im selben Fall: `ODB.saveProj/loadProj` = **3 je Präfix**, gefordert `== 3`. **Mutationsprobe:** `ODB.save("docs_koeder31",1)` → **rot**; `ODB.save("andere_…")` → **grün**. 🟡 **Nebenbefund:** `ODB.save('docs_…')` mit EINFACHEN Anführungszeichen bleibt **grün**. Heute ohne Fundstelle (0 in beiden Schreibweisen), also Sprödigkeit, kein Loch. |
| **D22** | `test_schrift_und_tokens_v933` · `…kommt_aus_dem_repo_und_nicht_von_google` | „von Google geladen": `url(http…)` im `<head>` | **0** — aber der Kopf führt **8** absolute Quellen (7 `<script src>`, 1 `<link href>`, alle cdnjs) | ** | 🔴 **AUSFALL** | **Mutationsprobe:** `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto">` in den Kopf → Fall bleibt **GRÜN** (rc=0). Nur `url(…)` → rot. Die geprüfte Menge kann die übliche Form der behaupteten Verletzung nicht enthalten. Datei: **0** Selbstproben. |
| D23 | `test_security` · `test_umkehrprobe_kommentar_bleibt_gruen` | `eval(`-Funde in zwei Texten | 1 Text **0**, 1 Text **1** | · | **berechtigt** | Der Fall ist selbst die Umkehrprobe; die leere Seite ist die Gegenprobe. |
| D24 | `test_symbolknoepfe_haben_namen_v957` · `…bei_einem_namenlosen_knopf_rot` | 9 Symbole × Vorkommen | 9 Symbole, **4 ohne** Vorkommen | · | **berechtigt** | Stelle 5× gefüllt. 🔴 **Nebenbefund:** dieser Köder prüft nur die Schreibweise `createElement('button'` — er kann die Lücke aus D25 nicht aufdecken. |
| **D25** | `test_symbolknoepfe_haben_namen_v957` · `test_kein_symbolknopf_ohne_namen` | Symbolknöpfe in `index.html` | Riegel sieht **74**, geeicht sind es **79** | · | 🔴 **AUSFALL** | **Mutationsprobe:** namenloser `✕`-Knopf als `createElement('button'` → **rot**; **derselbe Knopf** als `h('button'` → **GRÜN**. Anker ist `vor.rfind("createElement('button'")` — 1 von 4 Schreibweisen. 5 echte Symbolknöpfe (4× `h('button'`, 1× `createElement("button"`) werden nie angesehen; zusätzlich 6 Symbolvorkommen in einfachen Anführungszeichen. **Heute verdeckt das keinen Mangel** — alle 5 tragen `title`/`aria-label`. |
| D26 | `test_werkzeuge_vorbereitet_v940` · `test_koeder_ein_toter_handler_wird_gefunden` | Mustertreffer in zwei Texten | 1× **0**, 1× gefüllt | · | **berechtigt** | Der Fall ist ein Köder; die leere Seite ist die reparierte Fassung. |
| D27 | `test_worker_projects_einzelzeile_v940` · `test_koeder_der_lueckensucher_findet_eine_luecke` | Zeilen je Prüfstand | 6 Stände, **1 leer** | · | **berechtigt** | Stelle 5× gefüllt; der Fall ist ein Köder. |
| D28 | `test_zulagen_saetze_v768` · `test_keine_taggeld_anzeige_mehr` | Anzeige-Zeichenketten mit „Taggeld" | **30256 Zeilen, 27300 geprüft, 0 Treffer.** „Taggeld" steht 15× im Text: 4× als Bezeichner (`_kvTaggeldTag`), 11× in Kommentaren | ** | **berechtigt** | **Mutationsprobe:** `'Taggeld alt'` → **rot**, `"Taggeld alt"` → **rot**, Kommentar `// Taggeld …` → **grün** (richtig). Beide Anführungszeichen abgedeckt. 🟡 **Nebenbefund:** `` `Taggeld alt` `` (Vorlagenliteral) bleibt grün. Heute ohne Fundstelle: die 3 Vorlagenliterale mit „Taggeld" liegen alle in Kommentaren. |
| D29 | `test_zusammengesetzte_knopfnamen_v960` · `…erkennt_auch_den_versteckbaren_text` | `className:"…"` je Knopf-Rest | 28 Runden, **26 leer** | · | **berechtigt** | Stelle 2× gefüllt. 🔴 **Nebenbefund** siehe D33; das `className`-Muster kennt nur doppelte Anführungszeichen (11 Stellen im Code schreiben einfach). |
| D30 | `test_zusammengesetzte_knopfnamen_v960` · `…bei_einem_leeren_ast_rot` | dito, auf einem gebauten Text | 15 Runden, **14 leer** | · | **berechtigt** | Stelle 1× gefüllt; der Fall ist der Köder. 🔴 Er benutzt nur `createElement('button'` — deshalb ist die Lücke aus D33 an ihm vorbeigelaufen. |
| D31 | `test_zusammengesetzte_knopfnamen_v960` · `…die_zwei_behobenen_stellen_bleiben_benannt` | dito | 28 Runden, **26 leer** | · | **berechtigt** | Stelle 2× gefüllt; beide Stellen werden namentlich zugesichert. |
| D32 | `test_zusammengesetzte_knopfnamen_v960` · `…wer_immer_text_traegt_braucht_keinen` | dito | 14 Runden, **13 leer** | · | **berechtigt** | Stelle 1× gefüllt; der Fall ist die Gegenseite, nicht die Behauptung. |
| **D33** | `test_zusammengesetzte_knopfnamen_v960` · `test_wer_seinen_text_verlieren_kann_hat_einen_namen` | Knöpfe der Klasse „Text kann wegfallen" | Riegel sieht **698** von **797** Knöpfen im Code (87,6 %); Klassenmitglieder **14** statt **16** | · | 🔴 **AUSFALL** | **Mutationsprobe:** namenloser Knopf als `React.createElement('button'` → **rot**; **derselbe Knopf** als `h('button'` → **GRÜN**. 101 Knöpfe liegen außerhalb der Grundgesamtheit, fast alle `h('button',`. **Heute verdeckt das keinen Mangel** — von den 2 zusätzlichen Klassenmitgliedern ist **0** namenlos. |

**Summe: 30 berechtigt · 3 Ausfälle (D22, D25, D33) · 0 nicht entscheidbar.**

---

## 3. Der Zusammenhang „Selbstprobe ⇒ berechtigt" trägt hier NICHT

Der Vorbericht hat gemessen: alle sechs echten Befunde lagen in Dateien mit
**0** Selbstproben, alle drei berechtigten Leermengen in Dateien **mit** einer.
Über diese 33 bricht der Zusammenhang **in beide Richtungen**.

Gemessen (`selbstproben.py`, Selbstprobe = `def test_*`-Name mit
Umkehrprobe/Köder/Gegenprobe/Eichung **oder** `…wird_…_rot` / `bleibt_gruen`):

| Datei | Selbstproben | Urteil der Fälle darin |
|---|---|---|
| `test_zulagen_saetze_v768.py` | **0** | **berechtigt** (D28) — Mutationsprobe bestanden |
| `test_b3_stufen_4_7_v942.py` | **0** (Namen) | **berechtigt** (D02, D03) — In-Fall-Schranke „KOEDER STUMM" |
| `test_schrift_und_tokens_v933.py` | **0** | 🔴 **Ausfall** (D22) |
| `test_symbolknoepfe_haben_namen_v957.py` | **1** | 🔴 **Ausfall** (D25) |
| `test_zusammengesetzte_knopfnamen_v960.py` | **2** | 🔴 **Ausfall** (D33) |
| `test_projekt_cache_v927.py` | **7** | berechtigt, aber mit Schreibweisen-Lücke (D21) |
| `test_hook_order_static.py` | 0 → heute **4** | **berechtigt** (D10) — war auch mit 0 berechtigt |

* **„keine Selbstprobe ⇒ Ausfall" ist falsch.** D28 und D10 stehen in Dateien
  ohne (bzw. damals ohne) Selbstprobe und bestehen die Mutationsprobe.
* **„Selbstprobe ⇒ berechtigt" ist falsch, und zwar gefährlich falsch.** D25 und
  D33 liegen in Dateien **mit** Köder. Der Köder ist da — er prüft nur
  **dieselbe Schreibweise**, die der Riegel kennt. Ein Köder, der die Lücke des
  Riegels teilt, ist kein Beleg; er bestätigt die Blindheit.

**Was stattdessen trägt:** nicht „gibt es einen Köder", sondern **„gibt es einen
Köder JE FORM"**. Alle drei Ausfälle sind genau daran gescheitert, alle 30
berechtigten bestehen ihn. Das ist die Regel aus dem Auftrag, an diesen 33
bestätigt.

### Das gilt auch für die Messung der Selbstproben selbst

Meine erste Wortliste (`umkehrprobe|koeder|gegenprobe|selbstprobe|eich`) führte
`test_zusammengesetzte_knopfnamen_v960.py` mit **0** Selbstproben. Die Datei hat
**zwei** — sie heißen `test_der_riegel_wird_bei_einem_leeren_ast_rot` und
`test_der_riegel_erkennt_auch_den_versteckbaren_text`. Ein Köder heißt nicht
immer „Köder". Dieselbe Fehlerform wie ein Muster, das eine Schreibweise nicht
kennt — nur eine Ebene höher, im **Messgerät**. Korrigiert und im Skript
vermerkt.

---

## 4. Was die Ausfälle tun müssten (beschrieben, nicht gebaut)

Ein anderer Vorgang repariert gerade `test_hook_order_static.py`,
`test_db_schema_assumptions.py`, `test_tickets_xy_schema.py`,
`test_autopush_hook.py` und `test_pdf_bautagebuch_v882.py`. Keine der drei
Ausfall-Dateien ist darunter; trotzdem wurde hier **nichts** geändert.

**D22 — `test_schrift_und_tokens_v933.py::test_die_schrift_kommt_aus_dem_repo_und_nicht_von_google`**
Die Behauptung ist „über die CSP kommt nichts von Google herein". Gemessen wird
nur `url(…)`. Zu messen wären **alle Wege, auf denen der Kopf lädt**:
`url(…)`, `@import '…'`, `<link … href="…">`, `<script … src="…">`. Heute
stehen dort 8 absolute Quellen, alle `cdnjs.cloudflare.com` — die Grundgesamtheit
ist also **nicht** leer, nur die Teilmenge „Google" ist es, und das wäre dann
eine echte Aussage. Dazu ein Köder je Form (vier Stück) und eine Gegenprobe,
die eine cdnjs-Quelle **nicht** melden darf. Die Prosa-Nennungen von
`fonts.gstatic.com` im Kommentar müssen weiter schweigen — der bestehende
Kommentar erklärt richtig, warum eine reine Wortsuche hier ein Dauer-Fehlalarm
wäre.

**D25 — `test_symbolknoepfe_haben_namen_v957.py::test_kein_symbolknopf_ohne_namen`**
Den eigenen Knopf-Abtaster (`vor.rfind("createElement('button'")`) durch
`code_scan.knopf_stellen(text)` ersetzen. Der kennt alle vier Schreibweisen und
**belegt** das mit `eichen_knoepfe()` (4/4, geprüft). Die Symbolsuche
`re.finditer('"' + sym + '"')` muss zusätzlich einfache Anführungszeichen
kennen (6 Stellen im Bestand). Erwartete Grundgesamtheit danach: 79 statt 74.
Die `AUSNAHMEN`-Liste bleibt, wie sie ist.

**D33 — `test_zusammengesetzte_knopfnamen_v960.py::test_wer_seinen_text_verlieren_kann_hat_einen_namen`**
Dasselbe: `_klasse()` läuft über `re.finditer(r"createElement\('button'\s*,")`.
Die Datei **importiert `code_scan` bereits** (für `ist_code`), benutzt aber
`knopf_stellen` nicht. Umgestellt liefert `_klasse` 16 statt 14 Mitglieder
(nachgerechnet, Selbstprobe: auf der Schnittmenge **0** Abweichung). Dazu:
`className:\s*"…"` → beide Anführungszeichen, und das Symbol-Literal
`"…"\s*,` ebenfalls. Der vorhandene Köder
`test_der_riegel_wird_bei_einem_leeren_ast_rot` muss **je Schreibweise einen
Fall** bekommen — sonst bleibt er grün, während der Riegel blind ist. Genau das
ist heute der Zustand.

🔴 Bei keinem der drei verdeckt die Lücke **heute** einen Mangel. Gemessen,
nicht vermutet: D25 → 5 zusätzliche Knöpfe, alle mit `title`/`aria-label`;
D33 → 2 zusätzliche Klassenmitglieder, **0** namenlos; D22 → 0 Google-Quellen in
jeder geprüften Form. Was fehlt, ist der Schutz ab morgen.

---

## 5. Köder- und Gegenproben-Nachweis dieser Messung

### 5.1 Musterproben (`scripts/befund_31_muster.py`, gegen Zeichenketten im Speicher)

```
Koeder/Gegenproben gesamt: 29, davon richtig: 24, LUECKEN: 5
```

Die fünf „Lücken" sind **Befunde, keine Fehler des Messgeräts** — sie benennen
Schreibweisen, die ein Riegel nicht kennt:
`ODB.save('docs_…')` (D21), `React.createElement("button",` / `h('button',` /
`h("button",` (D33), `className:'…'` (D29–D33).

Selbstprobe des Messgeräts vorab, aus `code_scan`:
`eichen_elemente` OK (4/4 Formen), `eichen_knoepfe` OK (4/4),
`eichen` (Zeichenketten) am Bestand OK (21/21).

### 5.2 Mutationsproben (`scripts/befund_31_mutation.py`, echter pytest-Lauf)

Gefahren in einem Wegwerfbaum (`git archive a26e2b0`), der eine **eigene**
`index.html`, `tests/` und `scripts/` hat. Die Vorrichtung `index_html` liest
`repo_root`, und `repo_root` ist das Elternverzeichnis von `tests/` — deshalb
greift die Mutation, **ohne dass eine Testdatei geändert wird**. Die
`index.html` des Repos wurde nie angefasst; der Wegwerfbaum wird nach jeder
Probe zurückgesetzt und das am Ende nachgemessen.

**Grundstand zuerst:** alle 7 geprüften Fälle sind ohne Mutation grün. Ohne das
belegt ein späteres Rot nichts.

| Fall | Probe | erwartet | Ergebnis |
|---|---|---|---|
| D03 | `min-height:20px` in einer Header-Regel | rot | **rot** ✓ |
| D03 | Gegenprobe: dieselbe Regel, anderer Selektor | grün | **grün** ✓ |
| D10 | `  _react.useState(0);` zwischen zwei `return` | rot | **rot** ✓ |
| D21 | `ODB.save("docs_koeder31",1)` | rot | **rot** ✓ |
| D21 | `ODB.save('docs_koeder31',1)` | rot | grün — **Lücke** |
| D21 | Gegenprobe `ODB.save("andere_…")` | grün | **grün** ✓ |
| D22 | `url('https://fonts.gstatic.com/…')` im Kopf | rot | **rot** ✓ |
| D22 | `<link href="https://fonts.googleapis.com/…">` | rot | grün — **AUSFALL** |
| D22 | Gegenprobe `url('./fonts/…')` | grün | **grün** ✓ |
| D25 | namenloser `✕`-Knopf als `createElement('button'` | rot | **rot** ✓ |
| D25 | derselbe als `h('button'` | rot | grün — **AUSFALL** |
| D25 | Gegenprobe: derselbe Knopf **mit** `title` | grün | **grün** ✓ |
| D28 | `'Taggeld alt'` | rot | **rot** ✓ |
| D28 | `"Taggeld alt"` | rot | **rot** ✓ |
| D28 | `` `Taggeld alt` `` | rot | grün — **Lücke** |
| D28 | Gegenprobe `// Taggeld` im Kommentar | grün | **grün** ✓ |
| D33 | namenloser Knopf als `createElement('button'` | rot | **rot** ✓ |
| D33 | derselbe als `h('button'` | rot | grün — **AUSFALL** |

Vier Gegenproben, keine davon ein Fehlalarm.

### 5.3 🔴 Zweimal war MEIN Köder falsch, nicht der Riegel

Beide Male hätte ich einen funktionierenden Riegel für blind erklärt.

1. **D10.** Erster Köder: `  const [x,setX]=React.useState(0);` → grün. Der
   Riegel sucht aber `^  _react\.useState` — die Datei ist kompiliert, dort
   steht `_react.`. Mein Köder traf das Muster nicht. Zweiter Anlauf: die
   Muster des Riegels selbst importiert (`HOOK_RE`, `RETURN_RE`,
   `APP_OPEN_RE`, `_function_span`) und den Köder **gegen `HOOK_RE` geprüft,
   bevor** er eingebaut wird → **rot**.
2. **D25.** Erster Köder: ein `✏️`-Knopf → grün. `✏️` steht nicht in der Liste
   `SYMBOLE` des Riegels (9 Zeichen, `✕` ist dabei). Mit `✕` → **rot**.

Daraus die Regel, die in beiden Skripten als Kommentar steht: **ein Köder, der
die Definition des Riegels nicht kennt, misst den eigenen Irrtum.** Jeder
Köder, der grün bleibt, braucht eine Gegenprobe in die andere Richtung, bevor
daraus ein Befund wird.

---

## Was ich NICHT gemessen habe

* **Die Zahl 31 habe ich nicht erklärt, nur widerlegt.** Ich habe belegt, dass
  sie aus der Messdatei des Vorberichts nicht entstehen kann (Obergrenze 29),
  aber nicht, woher sie stammt.
* **Keine Mutationsprobe für 26 der 33.** Für die 19 Fälle mit gefüllter
  Geschwisterstelle stützt sich das Urteil auf den **Laufzeitzähler**
  („dieselbe Stelle war im selben Lauf gefüllt"), nicht auf Mutation. Das
  belegt, dass der Sucher lebt — es belegt **nicht**, dass der Fall bei jeder
  denkbaren Verletzung rot wird. Gefahren wurden 18 Mutationsproben auf 7
  Fällen.
* **Kein vollständiger Schreibweisen-Abgleich über alle 33.** Geprüft wurden
  die Muster der neun Fälle mit nie gefüllter Stelle und der beiden
  Knopf-Dateien. Für die übrigen ist **nicht gemessen**, ob ihre Muster alle
  Formen kennen.
* **`_OFFENE_LUECKEN` (D14) und `BASISLINIE` (D09) habe ich als „absichtlich
  leer" gewertet**, weil Kommentar und Fehlermeldung das so sagen. Dass sie
  einmal gefüllt waren und richtig geleert wurden, habe ich **nicht** aus der
  git-Historie belegt.
* **Die 3 Ausfälle habe ich nicht repariert** — der Auftrag untersagt es, und
  zwei Reparateure in derselben Datei zerreißen sie.
* **Nichts an `index.html`, keine DB, kein Browser, kein Netz.** Die
  Mutationsproben liefen ausschließlich im Wegwerfbaum.
* **Der Baum bewegte sich nicht während meiner Messung** (`HEAD` vor und nach
  dem 5-Minuten-Lauf identisch), aber der **Arbeitsbaum** trug durchgehend
  fremde Änderungen an fünf Testdateien (`git status`: `M
  test_autopush_hook.py`, `M test_db_schema_assumptions.py`, `M
  test_hook_order_static.py`, `M test_pdf_bautagebuch_v882.py`, `M
  test_tickets_xy_schema.py`). Alle Zahlen oben gelten für den **Commit**
  `a26e2b0`, nicht für den Arbeitsbaum. Für D10 heißt das: gemessen wurde die
  bereits eingecheckte v3.9.961-Fassung, nicht die gerade entstehende.
* **Die 11 übersprungenen und 8 xfailed-Fälle** sind wie im Vorbericht
  ungeprüft geblieben.

---

## Angelegte Dateien

| Datei | Zweck |
|---|---|
| `scripts/befund_31_muster.py` | Musterproben je Schreibweise, `--selbstprobe` |
| `scripts/befund_31_mutation.py` | Mutationsproben im Wegwerfbaum, `--baum`, `--nur` |
| `docs/befunde/DIE_31_VERDACHTE.md` | dieser Bericht |

Nachvollziehen:

```
python scripts/befund_31_muster.py --selbstprobe
python scripts/befund_31_muster.py

git archive HEAD | tar -x -C <wegwerfbaum>
python scripts/befund_31_mutation.py --baum <wegwerfbaum>

set EPK_WIRKUNG_OUT=wirkung.json
python -m pytest tests/ -p scripts.riegel_wirkung_plugin -q > lauf.log 2>&1
echo PYTEST_RC=%errorlevel% >> lauf.log
python scripts/befund_wirkung.py wirkung.json
```
