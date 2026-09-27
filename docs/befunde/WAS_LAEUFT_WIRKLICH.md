# Was läuft wirklich — Messung der Prüfungen in `epkolar-app`

Gemessen 27.09.2026, 11:18–11:55. Stand des Baums: `git HEAD = ce397e9`.

> **Der Baum bewegte sich während der Messung.** Ein parallel arbeitender
> Vorgang hat um 11:24, 11:27 und 11:28 `tests/test_code_scan_elemente_v959.py`,
> `tests/test_d9_seitenueberschriften_v956.py`,
> `tests/test_jede_komponente_wird_gerendert_v959.py` und `scripts/code_scan.py`
> geändert und drei Commits gesetzt (`e6202e5`, `aa4a091`, `ce397e9`). Meine
> erste Sammelmessung (11:21) sah deshalb 3189 Fälle, der Lauf (11:40) 3196.
> Aufgefallen ist das erst beim Abgleich der **Fall-Mengen**, nicht der Zahlen —
> die Zahlen allein hätte man als Rundungsrauschen abtun können. Alle Zahlen
> unten sind gegen den Stand ab 11:40 neu erhoben und untereinander konsistent.

Alle Messskripte liegen unter `scripts/befund_*.py` und
`scripts/riegel_wirkung_plugin.py`. Jede Messung hat eine `--koeder`-Selbstprobe.
Rückgabewerte wurden ausnahmslos aus Logdateien gelesen, nie hinter einer Pipe.

---

## Kurzfassung

| Frage | Zahl |
|---|---|
| Testdateien auf der Platte / mit eingesammeltem Fall | 466 / 462 |
| Eingesammelte Fälle | 3196 (Rückgabewert 0, **0** Sammelfehler) |
| Prüfungen, die **nie laufen** | **1** echte (`test_nichtgemessen_v909.py`, 18 Fälle) + 1 leerer Platzhalter |
| Fälle, die **nie rot werden können** | **6** belegt, **1** tote Zusicherung, 31 ungeprüfte Verdachte |
| Pruefer unter `scripts/`+`sql/` in **keiner** Kette | **62 von 76** — abzüglich meiner 5 neuen: **57 vorbestehende**, davon **53 urteilsfähig** |
| Davon **jetzt rot** | **1** — `sql/_check_brackets.js` |
| Torkette | sauber, 5/5 Köderproben richtig |

Es gibt **keine `package.json`** (laut git-Historie nie eine gegeben) und
**keine CI** (`.github/workflows/` existiert nicht). `npm test` gibt es hier
nicht. Die Ketten sind `scripts/torkette.py` und zwei Claude-Code-Hooks.

---

## (1) Wird jede Testdatei eingesammelt?

**Messung:** `pytest tests/ --collect-only -q` in eine Logdatei, Rückgabewert
als eigene Zeile angehängt, Urteil aus der Datei. Danach Vergleich der Dateien
auf der Platte gegen die Dateien, die im Protokoll mindestens einen Fall tragen
(`scripts/befund_einsammeln.py`).

```
pytest-Rueckgabewert aus der Logdatei: 0
Zeilen mit ERROR im Protokoll: 0
Dateien auf der Platte (.py, ohne __pycache__): 466
Dateien mit mindestens einem eingesammelten Fall: 462
Summe eingesammelter Faelle: 3196
```

`Rückgabewert 0` und `0 ERROR-Zeilen` zusammen heißen: **kein Importfehler,
kein `conftest`-Problem, keine unsammelbare Datei**. Gegenprobe zur Aussagekraft
dieses Kriteriums: im Köderlauf mit einem Importbruch meldete pytest
**Rückgabewert 2** — das Kriterium ist also nicht blind für diesen Fall.

Zusätzlich die Fall-Mengen (nicht nur die Summen) zwischen `--collect-only` und
dem echten Lauf verglichen: **0 Fälle nur im Protokoll, 0 Fälle nur im Lauf.**
Nichts wird eingesammelt und dann übersprungen.

### Die 4 Dateien ohne eingesammelten Fall

| Datei | Befund |
|---|---|
| `tests/_hilfen.py` | Hilfsmodul ohne `def test*` — erwartet |
| `tests/conftest.py` | Fixtures — erwartet |
| `tests/test_dispo_resched_push_v737.py` | 2-Zeilen-Platzhalter, laut Docstring durch `..._v738.py` ersetzt („Datei-Rename war gesperrt; leer belassen"). Harmlos, aber irreführender Name. |
| **`tests/test_nichtgemessen_v909.py`** | **Befund.** Siehe unten. |

### Befund: ein vollständiger Riegel, der in keiner Kette läuft

`tests/test_nichtgemessen_v909.py` ist keine Leiche. Es sind **73 Zeilen mit 18
Prüffällen** gegen `index.html` (Kacheln, die bei ausgebliebener Messung `null`
statt `0` zeigen müssen — genau der Fehler, den der Riegel verhindert). Die
Datei heißt `test_*.py` und liegt in `tests/`, enthält aber **kein `def test_*`**:
sie ist als eigenständiges Programm mit `main(pfad)` geschrieben.

**pytest sammelt daraus null Fälle ein.** Gefahren wird sie nur von Hand:

```
python tests/test_nichtgemessen_v909.py index.html
```

**Wirkung belegt, nicht Anwesenheit:**

| Probe | Ergebnis |
|---|---|
| gegen den heutigen Bestand | `GRUEN 18/18`, Rückgabewert **0** |
| gegen eine Kopie, in der **ein** Anker mutiert wurde (`setMatOpen(null)` → `setMatOpen(0)`) | `ROT 2 Befunde`, Rückgabewert **1** |

Der Riegel ist also **funktionsfähig und grün — und wirkungslos**, weil ihn
nichts fährt. Das ist genau die Form aus dem Schwesterprojekt. Er ist heute
grün, es fehlt also kein Fund; was fehlt, ist der Schutz ab morgen.

> Die Mutation lief auf einer **Kopie** in meinem Ablagebereich. `index.html`
> wurde nicht angefasst.

### Köder-Nachweis für Messung (1)

Miniaturbaum mit vier bekannt unsammelbaren Dateien, echter pytest-Lauf darauf
(`scripts/befund_einsammeln.py --koeder`):

| Köder | gefunden? |
|---|---|
| `test_leer.py` — Name passt, kein Fall drin | GEFUNDEN |
| `pruefe_etwas.py` — Fälle drin, Name passt auf kein Sammelmuster | GEFUNDEN |
| `test_importbruch.py` — Importfehler | GEFUNDEN |
| `test_falsche_klasse.py` — Klasse ohne `Test`-Präfix | GEFUNDEN |
| `test_echt.py` — **Gegenprobe**, muss sammelbar sein | korrekt **nicht** gemeldet |

Alle vier Ausfallarten werden erkannt, die Gegenprobe erzeugt keinen
Fehlalarm. Grundgesamtheit der echten Messung: 466 Dateien, nicht leer.

---

## (2) Fälle, die niemals rot werden können

**Nicht statisch geraten, sondern zur Laufzeit gemessen.**
`scripts/riegel_wirkung_plugin.py` hängt sich vor pytests eigene
assert-Umschreibung und ergänzt den Syntaxbaum jedes Testmoduls:

* vor **jedes** `assert` einen Zähler → wie viele Zusicherungen hat der Fall
  wirklich ausgeführt;
* um die Grundgesamtheit **jeder** Kurzschreibung und **jeder** `for`-Schleife
  einen Zähler → war die geprüfte Menge leer.

Zugeschrieben wird dem laufenden Fall, also auch bei Zusicherungen in
Hilfsfunktionen. Der pyc-Zwischenspeicher wird nicht gelesen (sonst käme eine
Fassung ohne Zähler von der Platte und das Gerät meldete überall 0).

```
Faelle im Lauf: 3196     Ausgaenge: 3177 passed, 11 skipped, 8 xfailed
Ausgefuehrte Zusicherungen: 9867
Aufgezeichnete Grundgesamtheiten: 38653 (davon leer: 31495) in 653 Faellen
```

> **Meine erste Fassung war für den wichtigsten Fall blind.** Sie klammerte nur
> Kurzschreibungen, die *direkt im Pruefausdruck* eines `assert` stehen. Die
> vorherrschende Schreibweise ist aber `treffer = [...]` und erst danach
> `assert not treffer`. Ergebnis: **63** aufgezeichnete Grundgesamtheiten statt
> 38653, und **0** leere — ein Messgerät, das sauber misst, nur eine andere
> Grundgesamtheit. Eine Abwesenheit darin hätte nichts belegt. Aufgefallen ist
> es nur, weil 63 Mengen auf 3177 Fälle unplausibel wenig sind.

### A) Grün, aber **0** Zusicherungen ausgeführt — 4 Fälle

**A1 `tests/test_autopush_hook.py::test_save_hook_uses_no_await_before_juprowapush`**

```python
for i, line in enumerate(index_html.splitlines()):
    if "_juprowaPush(" in line and "AUTOPUSH" in line:
        assert ".then(" in line, ...
```

Beleg: `_juprowaPush(` steht in **7** Zeilen, `AUTOPUSH` in **2** — in **0**
Zeilen beides. Die beiden `AUTOPUSH`-Marken sitzen auf der
`.then()`/`.catch()`-Fortsetzungszeile, nie auf der Aufrufzeile. Die Bedingung
kann in diesem Bündel **strukturell nie** zutreffen. Der Fall prüft nichts.

**A2 `tests/test_hook_order_static.py::test_no_hook_after_early_return_general`**

Enthält **kein einzelnes `assert`**. Am Ende steht ein `print("[soft-flag] …")`.
Der Docstring sagt das offen („nur Warning via stdout fuer Rest"). Also
Absicht — aber als Riegel kann er nicht rot werden, und eine Warnung in
stdout sieht in einem `-q`-Lauf niemand.

**A3 `tests/test_pdf_bautagebuch_v882.py::test_10_toter_print_stz_selektor_hat_ein_ziel_oder_ist_weg`**

`if not styled: return`. Gemessen: die CSS-Regel `#print-stz…{` ist **nicht**
mehr vorhanden → früher Ausstieg ist **richtig**, die Regel wurde entfernt.
Kein Mangel, aber der Fall prüft heute nichts mehr.

**A4 `tests/test_pdf_bautagebuch_v882.py::test_umkehrprobe_anker_des_alten_knopfes_ist_echt`**

`if "_genBautagPdf" in index_html: return`. Gemessen: `_genBautagPdf` ist
vorhanden → die Umkehrprobe steigt korrekt aus.

Die Folge ist trotzdem ein blinder Fleck: diese Umkehrprobe war der Beleg,
dass der Anker von Riegel 1 (`assert _PDF_KNOPF_ALT not in index_html`)
überhaupt trifft. Sie ist jetzt still. Riegel 1 behauptet eine **Abwesenheit**
ohne lebenden Beleg, dass sein Anker eine Rückkehr noch erkennen würde.

### B) Grün, 0 Zusicherungen, Schleife über **leerer** Menge — 2 Fälle

Das ist die vom Auftrag benannte häufigste und wichtigste Form.

* `tests/test_db_schema_assumptions.py::test_no_xPct_yPct_in_tickets_patch`
* `tests/test_tickets_xy_schema.py::test_no_xPct_yPct_write_to_tickets`

Beide identisch:

```python
matches = re.findall(r"_sbPatch\(\s*['\"]tickets['\"][^)]+\{([^}]+)\}", text)
for m in matches:
    assert 'xPct' not in m, ...
    assert 'yPct' not in m, ...
```

Laufzeitmessung: `matches` ist **leer**, die Schleife läuft **nie**, beide
Fälle führen **null** Zusicherungen aus und melden grün.

Beleg für die Ursache — `_sbPatch` wird 21-mal aufgerufen, **nie** mit `tickets`:

```
7 _sbPatch("fahrzeuge"      3 _sbPatch('workers'        3 _sbPatch('arbeitsscheine'
2 _sbPatch("users"          1 _sbPatch('fahrzeuge'      1 _sbPatch("werkzeuge"
1 _sbPatch("time_entries"   1 _sbPatch("arbeitsscheine"
```

Die Grundgesamtheit ist leer, weil `tickets` über `_sbPatch` gar nicht
geschrieben wird. **Eine leere Grundgesamtheit besteht keine Probe.**

**Köder auf das Muster** — würde es eine echte Rückkehr fangen?

| Fall | Treffer | Urteil |
|---|---|---|
| heutiger Bestand | 0 | ok (richtig leer) |
| `_sbPatch('tickets', id, {xPct:1,yPct:2})` | 1 | ok |
| `_sbPatch('tickets', t.id, {xPct: pct(e.x), yPct: 2})` | 1 | ok |
| `_sbPatch("tickets", String(t.id), {xPct:1})` | **0** | **Muster greift nicht** |
| Aufruf über zwei Zeilen | 1 | ok |

Also nicht nur wirkungslos, sondern zusätzlich **brüchig**: `[^)]+` kann die
schließende Klammer eines Aufrufs im Argument nicht überqueren.

### C) Grün, **alle** Grundgesamtheiten leer — 3 Fälle, alle drei berechtigt

| Fall | leere Menge | Urteil |
|---|---|---|
| `test_security.py::test_no_eval_calls` | `_EVAL.finditer(text)` | **berechtigt** — 0 `eval(` ist die richtige Antwort |
| `test_eine_mobilschwelle_v955.py::test_keine_zweite_mobilschwelle` | `code_scan.nur_code_stellen(...)` | **berechtigt** |
| `test_worker_projects_einzelzeile_v940.py::test_koeder_ohne_adminrecht_passiert_nichts` | `protokoll` | **berechtigt** — ist selbst ein Köder |

Entscheidend: **jede dieser drei Dateien trägt ihre eigene Selbstprobe**, die
belegt, dass der Sucher noch trifft —
`test_security.py` drei `test_umkehrprobe_*`,
`test_eine_mobilschwelle_v955.py` ein `test_der_riegel_wird_bei_einer_neuen_mobilschwelle_rot`
plus `test_der_abtaster_hat_sich_geeicht`,
`test_worker_projects_einzelzeile_v940.py` vier `test_koeder_*`.
Eine leere Menge **mit** Köder daneben ist kein Befund.

### Der Zusammenhang, der die Befunde erklärt

| Datei | Fälle | Nennungen von Umkehrprobe/Köder/Gegenprobe |
|---|---|---|
| `test_autopush_hook.py` (A1) | 11 | **0** |
| `test_hook_order_static.py` (A2) | 2 | **0** |
| `test_db_schema_assumptions.py` (B1) | 10 | **0** |
| `test_tickets_xy_schema.py` (B2) | 2 | **0** |

**Alle sechs belegten Befunde liegen in Dateien ohne jede Selbstprobe. Alle
drei berechtigten Leermengen liegen in Dateien mit Selbstprobe.** Im ganzen
Bestand tragen **124 von 464** Testdateien einen solchen Begriff.

### Eine tote Zusicherung

`tests/test_as_zeile_flaechen_v920.py::test_der_wolkenknopf_bleibt_die_ausnahme`,
Zeile 271:

```python
assert "canSync&&a.juprowa_id&&a.push_pending&&React.createElement("
```

Ein nichtleeres Zeichenketten-Literal als Prüfausdruck ist **immer wahr** —
hier fehlt sichtbar das `in index_html`. Die folgende Zeile prüft mit
`index_html.count(kette) == 1` wirklich, der Fall als Ganzes ist also nicht
wirkungslos. Die Zeile selbst ist tot.

### Tautologien, verschluckende `try/except`, späte Ausstiege

`assert True` / `assert 1` / `x == x` / `len(x) >= 0` als **einzige**
Zusicherung: **0 Fälle**.
`try/except`, das eine Zusicherung schluckt: **0 Fälle** im echten Bestand
(im Köder gefunden — die Probe ist nicht leer).
Früher Ausstieg, bei dem der Rumpf dennoch lief: **0 Fälle**.

### Ungeprüft — 31 Verdachte

31 Fälle führten Zusicherungen aus, hatten aber **mindestens eine** leere
Grundgesamtheit neben gefüllten. Eine leere Teilmenge ist dort meist die
richtige Antwort (ein Regex, der eine Verletzung sucht und keine findet). Ich
habe diese 31 **nicht** einzeln belegt; sie gehören in die Verdachtsliste, nicht
in die Befundliste. Die vollständige Liste steht in der Ausgabe von
`python scripts/befund_wirkung.py <wirkung.json>`. Die auffälligsten:

* `test_freie_variablen.py::test_5_keine_neuen_freien_variablen` — 4 von 5
  Mengen leer, darunter `BASISLINIE.items()`
* `test_hotfix_sync_v3131.py::test_antwortzweige_tragen_den_status` — 53 von 79
  Mengen leer bei 156 Zusicherungen
* `test_d9_seitenueberschriften_v956.py` — 4 von 13 Mengen leer

### Köder-Nachweis für Messung (2)

13 bekannte Fälle in einem Wegwerfbaum, echter pytest-Lauf, alle 13 grün:

| Köder | erwartet | Ergebnis |
|---|---|---|
| kein `assert` | A | GEFUNDEN |
| früher Ausstieg `if True: return` | A | GEFUNDEN |
| `for x in []: assert …` | B | GEFUNDEN |
| `assert not [x for x in LEER …]` | C | GEFUNDEN |
| `assert all(… for x in LEER)` | C | GEFUNDEN |
| `assert len([x for x in LEER]) == 0` | C | GEFUNDEN |
| **`treffer = [x for x in LEER …]; assert not treffer`** | C | GEFUNDEN |
| `assert True` | E | GEFUNDEN |
| `try: assert 1==2 except: pass` | statisch | GEFUNDEN |
| Grundgesamtheit **n=5**, Ergebnis leer | — | korrekt **nicht** gemeldet |
| zwei echte Zusicherungen | — | korrekt **nicht** gemeldet |
| `assert` in einer **Hilfsfunktion** | — | korrekt gezählt, nicht gemeldet |
| Grundgesamtheit n=5 nach Zuweisung | — | korrekt **nicht** gemeldet |

Acht bekannte Ausfälle gefunden, vier Gegenproben ohne Fehlalarm.

**Bekannte Grenze des Messgeräts:** ein `assert`, dessen Ausnahme von einem
`except` geschluckt wird, zählt als *ausgeführt*. Der Laufzeitzähler ist dafür
blind; abgedeckt wird der Fall vom statischen Teil (im Köder gefunden, im
Bestand 0-mal).

---

## (3) Was ist verdrahtet, und was nicht?

### Es gibt keine `package.json` und keine CI

```
package.json im Repo: NEIN - und laut git-Historie hat es nie eine gegeben
  (git log --all -- package.json ist leer)
.github/workflows/: NEIN - es gibt keine CI
```

Die Frage „was läuft bei `npm test` mit" hat hier also keinen Gegenstand.
`npm` spielt in diesem Repo keine Rolle; `node` wird nur als Programm
aufgerufen. Es gibt genau drei Ketten:

| Kette | Auslöser | Tore |
|---|---|---|
| **K1** `scripts/torkette.py` | von Hand | `node_check.py`, `_bracket_check.py`, `sql/_check_version.js`, `pytest tests/` |
| **K2** `.claude/settings.json` `PostToolUse` | nach jedem `Edit`/`Write` | `scripts/hook_index_riegel.py` (fährt node_check + Klammerbilanz) |
| **K3** `.claude/settings.json` `PreToolUse` | vor jedem `Bash` | `scripts/hook_git_add_riegel.py` |

Das vierte Tor der Torkette ist `pytest tests/` — **alle 466 Testdateien sind
damit Teil der Kette**, und über sie mittelbar jedes Skript, das ein Test als
Unterprozess startet oder als Modul importiert.

### Erreichbarkeit, gemessen

`scripts/befund_verweise.py`, kommentar- und docstringblind, mit `tests/` als
Startpunkt, transitiv. Von **76** Skriptdateien unter `scripts/` + `sql/` sind
**14** von einer Kette erreichbar:

| Datei | erreicht über |
|---|---|
| `scripts/node_check.py` | direktes Tor / `hook_index_riegel.py` |
| `scripts/_bracket_check.py` | direktes Tor |
| `sql/_check_version.js` | direktes Tor |
| `scripts/hook_index_riegel.py`, `scripts/hook_git_add_riegel.py` | direktes Tor |
| `scripts/code_scan.py` | `import` aus `tests/test_d9_seitenueberschriften_v956.py` |
| `scripts/messen.py` | `import` aus `tests/test_messen_v931.py` |
| `scripts/safe_edit.py` | `import` aus `tests/test_safe_edit_diagnose_v931.py` |
| `scripts/tab_sweep.py` | `import` über `scripts/mob_ansicht_messen.py` |
| `scripts/mob_ansicht_messen.py` | `import` aus `scripts/b7_syncknopf_messen.py` |
| `scripts/b7_syncknopf_messen.py` | Zeichenkette in `tests/test_b3_stufen_4_7_v942.py` |
| `scripts/bracket_check.py` | `tests/test_v3913_bracket_baseline.py` |
| `scripts/freivar/freivar.js` | `tests/test_freie_variablen.py` |
| `scripts/riegel_zeitfenster.js` | `tests/test_zeitfenster_v909.py` |
| `sql/_check_syntax.js` | `tests/test_docs.py` |

**62 hängen in keiner Kette, davon 57 urteilsfähig** (können mit einem
Rückgabewert ≠ 0 enden).

> **Eigene Zahl abgezogen.** Fünf dieser 62 sind die Messskripte, die ich für
> diesen Bericht angelegt habe (`befund_einsammeln.py`, `befund_kette.py`,
> `befund_verweise.py`, `befund_wirkung.py`, `riegel_wirkung_plugin.py`), vier
> davon urteilsfähig. **Vorbestehend sind 57 in keiner Kette, davon 53
> urteilsfähig.** Eine Messung, die ihre eigenen Dateien mitzählt, misst sich
> selbst.

### Aber: die meisten davon *können* nicht in eine Kette

Eine Empfehlung „häng sie ein" ist nur dann harmlos, wenn das Skript nichts
verändert. Gemessen über den Syntaxbaum, kommentarblind:

Die 53 vorbestehenden urteilsfähigen Verwaisten zerfallen in:

| Art | Zahl |
|---|---|
| braucht einen **Browser** (Playwright) | **32** |
| braucht die **DB** | **5** (`audit_v3_9_95.ps1`, `create_kiener_v3960.ps1`, `db_migrate_all.ps1`, `version_bump.py`, `sql/sql-runner.mjs`) |
| braucht das **Netz** | **1** (`schrift_holen.py`) |
| **reine Leser** | **15** |

(`grundstand_erheben.py` braucht beides, gezählt beim Browser.)

Die 38 Browser-/DB-/Netz-Skripte sind keine vergessenen Riegel, sondern
**Einmal-Messgeräte für je einen Befund** (`hellmodus_*`, `b3_stufen_*`,
`projliste_*` …). Dass sie in keiner Kette hängen, ist richtig.

### Befund: ein Riegel, der in keiner Kette hängt — und **jetzt rot ist**

Von den 15 vorbestehenden reinen Lesern habe ich die gefahren, die ohne
Argumente laufen:

| Skript | Rückgabewert | Ausgabe |
|---|---|---|
| **`sql/_check_brackets.js`** | **1** | `brackets () -6 {} 0 [] 0` · `BRACKET BASELINE BROKEN` |
| `scripts/freivar/selbsttest.js` | 0 | `OK` |
| `scripts/verify_sync_behavior.cjs` | 0 | alle Testfälle grün |
| `scripts/md5_geschuetzt.py` | 0 | „Die 7 geschuetzten Funktionen sind unveraendert." |
| `scripts/bestand.py` | 0 | `BESTAND GRUEN - 118 Begriffe in 17 Gruppen` |
| `scripts/paare_v931_ausgetretene.py` | 1 | siehe unten — **kein** Riegel |
| `scripts/ansicht_inventar.py`, `scripts/anker_schneiden.py` | 1 / 2 | nur Aufrufhinweis, brauchen Argumente |

**`sql/_check_brackets.js` steht rot und niemand sieht es**, weil kein Skript,
kein Test und keine Kette ihn aufruft. Die Ursache ist allerdings nicht ein
Fehler in `index.html`, sondern ein **überholtes Messverfahren**:

| | `scripts/_bracket_check.py` (in der Kette) | `sql/_check_brackets.js` (verwaist) |
|---|---|---|
| Verfahren | entfernt **zuerst** Zeichenketten, Template-Literale und Kommentare | zählt über den **rohen** Dateitext |
| Grundlinie | `() -1 / {} 0 / [] 0` | `() -2 / {} 0 / [] 0` |
| zusätzlich | Lebenszeichen: bricht ab, wenn `index.html < 1 MB` | — |
| Stand heute | **grün** (Torkette, 0,6 s) | **rot**, `() -6` |

Eine Rohtext-Bilanz verschiebt sich bei jedem neuen String, der eine
unbalancierte Klammer enthält — die Grundlinie `-2` ist deshalb nicht zu
halten. Die richtige Antwort ist hier **nicht** „in die Kette hängen", sondern
**abschreiben**: das Verfahren der Kettenfassung ist strikt besser, inklusive
Lebenszeichen gegen die 0-Byte-Falle.

`scripts/paare_v931_ausgetretene.py` ist **kein** Riegel, sondern ein
Anker/Ersatz-Anwender aus v3.9.931. Sein Rückgabewert 1 bedeutet „9 Anker nicht
mehr eindeutig, es wurde NICHTS geschrieben" — das ist die gewollte
Schutzabschaltung eines längst verbrauchten Einmalwerkzeugs, kein Befund.

### Köder-Nachweis für Messung (3)

Wegwerfbaum, im Repo wird nichts angelegt:

| Probe | erwartet | Ergebnis |
|---|---|---|
| Skript per `import` benutzt → erreichbar | ja | ok |
| Skript als Zeichenkette in `subprocess.run` → erreichbar | ja | ok |
| Skript **nur im Kommentar/Docstring** genannt → **nicht** erreichbar | nein | ok |
| echtes Tor der Torkette → erreichbar | ja | ok |

Die dritte Probe ist die wichtige: ohne sie zählt eine Erwähnung in Prosa als
Kette. Meine erste Fassung hatte genau diesen Fehler.

---

## (4) Die Torkette selbst

`scripts/torkette.py`, geprüft über den Syntaxbaum (**kommentarblind** — siehe
Warnung unten):

| Frage | Antwort |
|---|---|
| Jedes Tor ein eigener Prozess? | **ja** — `subprocess.run(befehl, …)`, Liste statt Zeile |
| `shell=True`? | **nein** |
| Pipe im Befehl? | **nein** |
| Rückgabewert einzeln gelesen? | **ja** — `r.returncode == 0` je Tor, Ergebnis in `rot`-Liste gesammelt |
| `and`/`or`-Verknüpfung über `returncode`? | **nein** |
| Ausgabe erst **nach** dem Lesen gekürzt? | **ja** — `capture_output=True`, `ausgabe[-3000:]` erst im Bericht |
| Tor, das nicht startet? | **rot** — `FileNotFoundError` wird gefangen und als `False` gewertet |
| Hängendes Tor? | **rot** — `timeout=1800`, `TimeoutExpired` → `False` |
| Rückgabewert der Kette | `0` nur, wenn **alle** gefahrenen Tore grün waren |

**Kein Befund.** Die Kette macht genau das, was ihr Docstring behauptet.

> **Warnung aus eigenem Schaden:** meine erste Fassung suchte im **rohen**
> Dateitext und meldete zwei Befunde — `shell=True gefunden` und
> `Pipe im Befehl gefunden`. Beide standen im **Docstring** von `torkette.py`,
> in der Begründung, *warum* es dort keine Pipe gibt („`npm run verify | tail`
> meldete den Code von `tail`", „Kein `shell=True`, keine Pipe"). Ein Riegel,
> der rohen Dateitext durchsucht, misst seine eigene Begründung mit. Ebenso
> meldete er später fälschlich `capture_output fehlt`, weil mein
> Code-Auszug Schlüsselwort-**Namen** nicht mitnahm. Beide Fehler sind
> ausgebaut und mit der Kommentar-Probe des Köders abgesichert.

### Köder-Nachweis: macht ein rotes Tor die Kette rot?

`torkette.fahre()` direkt gefahren, ohne die Datei anzufassen:

| Probe | grün? | erwartet |
|---|---|---|
| Tor endet mit 1 | False | False ✓ |
| Tor endet mit 0 | True | True ✓ |
| Tor gibt 50 000 Zeichen aus **und** endet mit 1 | False | False ✓ |
| Tor existiert nicht | False | False ✓ |
| Tor schreibt auf stderr, endet mit 0 | True | True ✓ |

5 von 5 richtig. Der dritte Fall ist der wichtige: viel Ausgabe verdeckt den
Rückgabewert nicht.

### Vollständigkeit der Torliste

Gegen `package.json` **nicht prüfbar — es gibt keine.** Gegen die Hooks:

| Tor | Torkette | PostToolUse-Hook |
|---|---|---|
| `node_check.py` | ja | ja |
| `_bracket_check.py` | ja | ja |
| `sql/_check_version.js` | ja | **nein** |
| `pytest tests/` | ja | **nein** |

Das ist plausibel (der Hook muss nach jedem Schreiben schnell sein), heißt aber:
**der Versionsabgleich und die 3196 Fälle laufen ausschließlich, wenn jemand
`python scripts/torkette.py` von Hand tippt.** Es gibt keinen Automatismus —
keine CI, kein pre-commit-Hook — der das erzwingt.

Zwei Randbefunde:

* `python scripts/torkette.py --schnell` überspringt pytest, gibt `0` zurück und
  **warnt ausdrücklich** („kein Auslieferungsurteil"). Ehrlich gebaut; wer nur
  den Rückgabewert liest, sieht die Warnung trotzdem nicht.
* `sql/_check_brackets.js` ist ein Torkandidat, der **nicht** in der Liste steht
  — siehe (3): zu Recht, sein Verfahren ist überholt.

### Ist die Kette heute grün?

```
Torkette - schnell (ohne pytest)
node_check         gruen    0.8 s
Klammerbilanz      gruen    0.6 s
Versionsabgleich   gruen    0.1 s
ALLE 3 TORE GRUEN
```

Und der vollständige pytest-Lauf, gemessen aus der Logdatei, nicht hinter einer
Pipe: `3177 passed, 11 skipped, 8 xfailed in 280,72 s`, **Rückgabewert 0**.
**Kein Fall ist rot.**

---

## Was ich NICHT gemessen habe

* **Keine Mutationsprobe an `index.html`.** Das Schreiben dort war untersagt.
  Für die 3177 grünen Fälle ist damit **nicht** belegt, dass sie rot werden,
  wenn man den Code kaputt macht. Die einzige echte Mutationsprobe lief gegen
  `test_nichtgemessen_v909.py` auf einer **Kopie**. Für die Wirkung der übrigen
  Riegel stützt sich dieser Bericht auf Laufzeitzähler (wurde geprüft?
  war die Menge leer?), nicht auf Mutation.
* **Die 31 Verdachte aus Klasse D sind ungeprüft.** Jeder braucht einen Blick
  auf die Absicht des Falls; das ist mit dem Laufzeitzähler nicht entscheidbar.
* **Die 53 verwaisten urteilsfähigen Skripte habe ich nicht alle gefahren** —
  nur die reinen Leser ohne Argumentzwang (8 von 15). Von **38** Skripten
  (Browser/DB/Netz) und den restlichen 7 weiß ich **nicht**, ob sie heute grün
  oder rot wären. Ich habe sie bewusst nicht gestartet: `version_bump.py`,
  `db_migrate_all.ps1`, `create_kiener_v3960.ps1`, `sql/sql-runner.mjs` und
  `schrift_holen.py` würden schreiben, migrieren oder herunterladen.
* **Verschluckte Zusicherungen** erkennt der Laufzeitzähler nicht (siehe
  Grenze in (2)); dort gilt nur der statische Befund.
* **Die 11 übersprungenen und 8 xfailed-Fälle** habe ich nicht danach
  untersucht, *warum* sie übersprungen werden. Ein dauerhaft übersprungener
  Fall ist dieselbe Krankheit in anderer Form.
* **`tests/_hilfen.py` wurde nicht instrumentiert.** pytest schreibt nur
  Testmodule um; Zusicherungen, die in `_hilfen.py` stehen, zählt der Zähler
  nicht. (Zusicherungen in Hilfsfunktionen *innerhalb* der Testmodule zählt er
  — im Köder belegt.)
* **Kein DB-, Browser- oder Netzzugriff**, keine Prüfung der SQL-Funktionen
  gegen die laufende Datenbank.
* **Ein Stand, nicht ein Zeitraum.** Der Baum wurde während der Messung dreimal
  committet. Alle Zahlen gelten für `HEAD = ce397e9` ab 11:40.

---

## Angelegte Dateien

Nur Messskripte und dieser Bericht — `index.html` und keine bestehende Prüfung
wurde angefasst, es wurde nichts committet.

| Datei | Zweck |
|---|---|
| `scripts/befund_einsammeln.py` | Messung (1), `--koeder` |
| `scripts/riegel_wirkung_plugin.py` | pytest-Plugin, Laufzeitzähler für (2) |
| `scripts/befund_wirkung.py` | Urteil für (2) |
| `scripts/befund_verweise.py` | Messung (3), `--koeder` |
| `scripts/befund_kette.py` | Messung (3)+(4), `--koeder` |
| `docs/befunde/WAS_LAEUFT_WIRKLICH.md` | dieser Bericht |

Nachvollziehen:

```
python scripts/befund_einsammeln.py --koeder
python -m pytest tests/ --collect-only -q > collect.log 2>&1 ; echo "PYTEST_RC=$?" >> collect.log
python scripts/befund_einsammeln.py collect.log

set EPK_WIRKUNG_OUT=wirkung.json
python -m pytest tests/ -p scripts.riegel_wirkung_plugin -q
python scripts/befund_wirkung.py wirkung.json

python scripts/befund_verweise.py --koeder
python scripts/befund_verweise.py
python scripts/befund_kette.py
```
