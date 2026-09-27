# Werden die 3210 Prüfungen rot, wenn der Code kaputt ist?

**Stand der Messung:** 27.09.2026, 15:05–15:40 · Testbaum = `a26e2b0` (v3.9.961)
**Gegenstand:** `index.html`, 3.711.031 Bytes, **md5 `20783957517acbdf18ae7e38729c3f54`**,
30.256 Zeilen, durchgehend CRLF
**Verfahren:** 14 Mutationen, je **genau eine geänderte Zeile**, jede auf einer
**Kopie** (`_mess_mut_<name>.html`, git-ignoriert über `.gitignore:90`).
`index.html` wurde von mir **nie zum Schreiben geöffnet**; nach jedem der
15 Läufe steht `git diff --numstat index.html` leer und die md5 unverändert im
Log.

> **Messwerkzeuge** (liegen im Sitzungs-Schmierzettel, nicht im Repo):
> `mutieren.py` (erzeugt die Kopien), `epk_mutplug.py` (pytest-Plugin, leitet
> das Lesen um), `lauf.sh`, `auswerten.py`. Rohdaten: 15 Logdateien.
> Das Urteil steht in jedem Fall aus der **Logdatei**, nie aus einem Exitcode
> hinter einer Pipe.

---

## Kurzfassung

| | Zahl |
|---|---|
| Mutationen gefahren | **14** (13 Schaden + 1 Gegenprobe) |
| davon **keine einzige Prüfung rot** | **3** auf dem gemessenen Baum → **2** nach `97cc02f` |
| Gegenprobe (nur Kommentartext) | **0 rot** — wie gefordert |
| Median rot je Schadensmutation | **2** Fälle |
| stärkste Reaktion | Austrittsfilter: **11** Fälle in 5 Dateien |
| Grundgesamtheit je Lauf | **3166** Fälle (3165 grün + 1 bekannt rot), 11 übersprungen, 8 xfail, **364 s** |

**Die drei blinden Klassen, beim Namen genannt:**

1. **Ein `catch`, der schluckt statt zu melden** — 0 rot.
2. **Ein entfernter Null-Schutz** — 0 rot.
3. **Die Byte-Identität der sieben plombierten Funktionen** — 0 rot auf dem
   gemessenen Baum; **seit `97cc02f` (während dieser Messung eingetroffen) 1 rot.**

---

## 🔴 Zwei Dinge haben sich während der Messung unter mir bewegt

Beides gehört in den Bericht, weil beides den Umfang der Aussage begrenzt.

### (a) `HEAD` ist gewandert: `a26e2b0` → `97cc02f`

Der Auftrag nannte `HEAD = a26e2b0`. Während Welle 2 lief, kam
`97cc02f "Torkette: drei Tore, die es schon gab und die NIRGENDS liefen"` dazu:

```
21   3   scripts/md5_geschuetzt.py
33   2   scripts/torkette.py
172  0   tests/test_geschuetzte_funktionen_v961.py     (neu, 5 Fälle)
index.html                                            unverändert
```

Alle 15 Läufe haben **dieselbe** Grundgesamtheit eingesammelt (3166 Fälle,
nachgelesen in jedem Log) — die neue Datei war in **keinem** davon dabei.
Die Haupttabelle ist damit in sich konsistent, aber sie beschreibt den
Testbaum von `a26e2b0`. Der Beitrag der neuen Datei ist unten einzeln
nachgemessen und betrifft **genau eine** Tabellenzeile (Nr. 8).

### (b) `index.html` ist um 15:40 auf v3.9.962 gewechselt — nicht durch mich

Nach dem letzten Lauf (15:38, md5 `20783957…`, `git diff` leer) steht die Datei
um **15:40:07** mit 3.712.738 Bytes und md5 `e5f245b7…` da, `4 4 index.html`:

```
-  var SW_VER='epkolar-v3.9.961';          +  var SW_VER='epkolar-v3.9.962';
-  const APP_VERSION="3.9.961-supabase";   +  const APP_VERSION="3.9.962-supabase";
   Z24005 ASChecklistPanel      + title/aria-label "Punkt entfernen"
   Z24921 FahrtenbuchPanel      + title/aria-label "Abbrechen"/"Fahrt hinzufügen"
```

Das ist ein Versions-Bump plus zwei Knopfnamen, also der Inhalt, den der
alleinige Schreiber der Datei anlegt — **keine meiner 14 Mutationen ändert mehr
als eine Zeile, und keine schreibt nach `index.html`.** Beleg in beide
Richtungen: `mutieren.py` druckt die md5 der Quelle **vor und nach** seinem
eigenen Lauf, beide Male `e5f245b7…` (also unverändert **durch mich**), und der
rekonstruierte Urstand aus der Kommentar-Mutation ergibt wieder exakt
`20783957…` (siehe Nachweis unten).

**Folge, und das ist die ehrliche Grenze dieses Berichts:** ich habe die
Messung an dieser Stelle **angehalten**. Drei bereits vorbereitete
Bestätigungsmutationen (zweiter schluckender `catch`, zweiter Null-Schutz,
echter Rechenfehler in `_ezEffTage`) wurden **aus dem neuen Stand erzeugt und
deshalb verworfen**, nicht gefahren. Eine Mutation aus v3.9.962 gegen eine
Grundlinie aus v3.9.961 zu stellen wäre eine Zahl über zwei verschiedene Bäume.

---

## Der Weg zur Kopie: es gibt keinen vorgesehenen

Die Vorrichtung in `tests/conftest.py` kennt **keine** Umlenkung:

```python
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(scope="session")
def index_html(repo_root):
    with open(os.path.join(repo_root, "index.html"), ...) as f:
        return f.read()
```

Kein `EPK_*`-Schlüssel (der einzige ist `EPK_TEST_TIMEOUT`), kein `--`-Schalter,
keine `pytest.ini`/`pyproject.toml` — es gibt im Repo überhaupt keine
pytest-Konfigurationsdatei. Ein eigenes conftest in einem Arbeitsverzeichnis
**außerhalb** von `tests/` hilft nicht: Vorrichtungen aus einem
Eltern-conftest oder einem Plugin verlieren gegen `tests/conftest.py`.

Und es sind **drei** Lesewege, nicht einer — wer nur den ersten umlenkt, misst
einen Teil des Prüfstands und hält das Ergebnis für das Ganze:

| Weg | Form | Dateien |
|---|---|---|
| 1 | Vorrichtung `index_html` (session-weit) | 329 Testdateien nennen sie |
| 2 | `io.open(str(WURZEL / "index.html"), …, newline="")` | 17 Dateien, 21 Stellen |
| 3 | `INDEX.read_text(encoding="utf-8")` | Modulebene in vielen älteren Dateien |
| 4 | der **Pfad** geht an einen Kindprozess (`scripts/riegel_zeitfenster.js`) | `test_zeitfenster_v909.py` |

**Gewählter Weg** (`epk_mutplug.py`, über `-p` geladen, aktiv nur bei gesetztem
`EPK_MUT_INDEX`): `builtins.open` **und** `io.open` werden ersetzt — in CPython
dasselbe Objekt, aber zwei Namensbindungen, und `pathlib.Path.read_text` geht
über `io.open`. Zusätzlich schreibt das Plugin die Argumentliste von
`subprocess.run`/`Popen` um. Umgeleitet wird ausschließlich ein **Lese**-Open,
dessen Pfad normalisiert auf `<repo>/index.html` zeigt.

### Die Selbstprobe des Messgeräts (Köder)

Ein Umlenker, der nichts umlenkt, macht **jede** Mutation zu „0 rot" — genau die
Zahl, die hier interessiert. Deshalb zuerst ein Köder: `index.html` auf die
ersten 500 Bytes gekürzt, gegen je einen Vertreter der vier Lesewege:

```
16 failed, 3 passed in 1.43s
EPK-UMLEITUNG: 12 Dateiöffnungen, 1 Kindprozess-Argument
```

Alle vier Wege rot, der Zähler für den Kindprozess-Weg > 0. Im vollen Lauf
meldet das Plugin **in allen 14 Läufen identisch 486 umgeleitete Öffnungen** —
die Umlenkung hat also jedes Mal dieselbe Menge erreicht.

---

## Die Tabelle

Gelesen aus den 15 Logdateien. „rot" = Fälle, die **zusätzlich** zum Grundlauf
umfallen. Der Grundlauf hat **einen** bekannten roten Fall, und der ist von mir
verursacht: `test_jede_datei_wird_eingesammelt_v961::test_jede_testdatei_hat_faelle_beigetragen`
fällt, weil fünf Dateien laut Auftrag per `--ignore` draußen bleiben
(`test_db_schema_assumptions`, `test_tickets_xy_schema`, `test_autopush_hook`,
`test_hook_order_static`, `test_pdf_bautagebuch_v882` — dort arbeiten zwei
andere Agenten). Er ist in allen 15 Läufen gleich und aus jeder Zeile
herausgerechnet.

| # | Mutation | Klasse des Schadens | Zeile | Δ Bytes | md5 der Kopie | **rot** | welche |
|---|---|---|---|---|---|---|---|
| **00** | Kommentartext ergänzt (`… kein neuer Fetch (Mutationsprobe).`) | **GEGENPROBE — soll 0 sein** | 7284 | +17 | `0ef12a79…` | **0** | — |
| 01 | `setMatOpen(null)` → `setMatOpen(0)` | Null verdeckt eine ausgebliebene Messung | 24544 | −3 | `f2762707…` | **2** | `test_nichtgemessen_v909.py` (2): `…[kachel_matOpen]`, `…zurueckgedrehten_kachel_rot` |
| 02 | `slice(0,10)<h` → `<=h` in `_maIstEhemalig` | Austrittstag selbst gilt als ausgetreten | 9988 | +1 | `6c6ac504…` | **11** | `test_ausgetretene_live_v931` (5) · `test_austritt_eine_regel_v950` (2) · `test_austritt_eine_regel_v952` (2) · `test_b3_stufen_12_15_v946` (1) · `test_ma_ehemalige_v866` (1) |
| 03 | `const isMob=ww<BP_MOB` → `ww<768` (1 von 26) | zweite Mobilschwelle | 8285 | −3 | `b89d7f54…` | **4** | `test_eine_mobilschwelle_v955` (2) · `test_mobil_fundament_v932` (2) |
| 04 | `canDo("material_delete",curUser)&&` vor dem Löschknopf entfernt | Rechteprüfung weg | 20958 | −34 | `081f2481…` | **2** | `test_bughunt_alt_2026_06_12` (2): `deleteSuppOrd_render_has_canDo_guard`, `die_gelockerten_rechtemuster_unterscheiden_noch` |
| 05 | `title` **und** `aria-label` eines Symbolknopfs entfernt („Portal öffnen") | zugänglicher Name weg | 6771 | −57 | `ad74e479…` | **2** | `test_emojiknoepfe_haben_namen_v958` (1) · `test_symbolknoepfe_vollstaendig_v961` (1) |
| 06 | `createElement('h2'` → `'div'` (Seitenüberschrift, 1 von 22) | Gliederung für die Vorlesehilfe weg | 10231 | +1 | `abb8e73e…` | **1** | `test_d9_seitenueberschriften_v956::test_die_gesamtzahl_der_seitenueberschriften` |
| 07 | `SW_VER='epkolar-v3.9.961'` → `…960` | Versionsdreiklang läuft auseinander | 16 | ±0 | `59e387d4…` | **1** | `test_version_triple_sync::test_version_triple_sync` |
| **08** | `_maWaehlbar`: **ein Leerzeichen** im Rumpf (`var h=` → `var h = `) | Plombe gebrochen, Verhalten unverändert | 9998 | +2 | `89c85551…` | **0** | — *(nach `97cc02f`: **1**, siehe Nachtrag)* |
| 09 | `_kurz(a.arbeitsanweisungen,60)` → `String(…).slice(0,60)` | Kürzung ohne Auslassungszeichen und ohne Zugang | 11660 | +14 | `6e0e1539…` | **2** | `test_stille_kappungen_v953` (2): `die_zwoelf_stellen_benutzen_den_helfer`, `keine_stille_kappung_von_anzeigetext` |
| 10 | `UI.fMeta: 12` → `10` | Schriftgröße unter 12 px im Token-Objekt | 3554 | ±0 | `093ccbbb…` | **1** | `test_schrift_und_tokens_v933::test_keine_schriftgroesse_unter_zwoelf_im_token_objekt` |
| 11 | `background: _dark?"#1a1a1a":V.bd` → `background:"#1a1a1a"` | feste dunkle Farbe im Hellmodus | 18064 | −11 | `a1153f79…` | **1** | `test_b3_stufen_4_7_v942::test_die_planflaeche_folgt_dem_thema` |
| **12** | `catch(e){setMsg(…);…__toast("❌ Speichern fehlgeschlagen…")}` → `catch(e){}` | `catch` schluckt statt zu melden | 9892 | −135 | `04f84649…` | **0** | — |
| **13** | `await window._ensureAuth?.();` → `await window._ensureAuth();` | Null-Schutz entfernt | 751 | −2 | `0d9138fa…` | **0** | — |

**Beleg, dass jede Mutation gegriffen hat** (eine leere Grundgesamtheit besteht
keine Probe): `mutieren.py` bricht ab, wenn der Anker nicht im Bestand steht
(„ANKER NICHT GETROFFEN … das ist NICHT GEMESSEN") oder wenn die Kopie gleich
der Quelle bleibt. Alle 14 Kopien haben **genau eine** abweichende Zeile
gegenüber dem Urstand, nachgerechnet Zeile für Zeile. Gegenprobe in die andere
Richtung: die Kommentar-Mutation rückwärts angewandt ergibt wieder
3.711.031 Bytes / md5 `20783957517acbdf18ae7e38729c3f54` — die 14 Kopien
stammen also nachweisbar aus dem gemessenen Stand und nicht aus v3.9.962.

**Zur CRLF-Falle:** gelesen **und** geschrieben mit `newline=""`. Ohne das
stellt Python auf Windows alle 30.255 Zeilen um, und „eine geänderte Zeile"
wäre eine Erfindung. Die Spalte „Δ Bytes" ist der Nachweis: sie liegt zwischen
−135 und +17, nicht bei fünfstelligen Zahlen.

---

## Nachtrag: was die während der Messung eingetroffene Datei ändert

`tests/test_geschuetzte_funktionen_v961.py` (aus `97cc02f`, 5 Fälle) importiert
`md5_geschuetzt.SOLL`/`summen` statt die sieben Summen abzuschreiben. Gegen
**alle 14 eingefrorenen Kopien** nachgefahren (die Datei liest nur `index.html`,
die Kopien sind unverändert — die Messung hängt also nicht am neuen Stand):

| Kopie | Ergebnis |
|---|---|
| 02_austritt_grenztag | **1 failed**, 4 passed (`_maIstEhemalig`) |
| 08_plombe_gebrochen | **1 failed**, 4 passed (`_maIstEhemalig` **und** `_maWaehlbar`) |
| die übrigen 12 | 5 passed |

Die Plombe wirkt also ab `97cc02f` **im Lauf** — und sie fasst weiter als ihr
Name sagt: das Messfenster ist 4000 Zeichen ab `function <name>`, deshalb
schlägt eine Änderung an `_maWaehlbar` zusätzlich bei `_maIstEhemalig` an. Das
freistehende `scripts/md5_geschuetzt.py` liefert für dieselben zwei Kopien
`rc 1` und für die übrigen `rc 0`.

Damit bleibt die Zahl der blinden Mutationen auf dem **heutigen** Baum bei
**zwei**: Nr. 12 und Nr. 13.

---

## Welche Schadensklassen KEINE Prüfung sieht

### 1. Ein `catch`, der schluckt statt zu melden — 0 von 3166

Geändert wurde der Fang eines **Speicher**-Wegs (Z9892): vorher `setMsg("❌ …")`
plus roter Toast mit 5 s Standzeit, nachher `catch(e){}`. Der Benutzer drückt
„Speichern", nichts passiert, nichts wird gemeldet, nichts wird gespeichert —
und der Prüfstand bleibt vollständig grün, 135 Bytes leiser.

Es gibt **keine** Prüfung der Form „kein schluckender `catch` im Baum". Das
Einzige in der Nähe ist `test_kiosk_fahrzeuge_v706::test_client_error_not_silently_swallowed`
— eine Prüfung über **einen namentlich genannten** Pfad (Kiosk-Fahrzeuge), die
für jeden anderen der 355 `catch(e){…}`-Blöcke prinzipiell grün ist. Eine
Klasse, die an einer Stelle geprüft und an 354 nicht geprüft ist, ist als
Klasse nicht geprüft.

> Das ist derselbe Bau wie die Befunde v3.9.908–914 („eine ausgebliebene
> Messung erscheint als Zahl"), nur eine Ebene davor: hier erscheint sie als
> **gar nichts**.

### 2. Ein entfernter Null-Schutz — 0 von 3166

`await window._ensureAuth?.();` im `API.get`-Vorlauf → `await window._ensureAuth();`.
Ist `window._ensureAuth` zu diesem Zeitpunkt nicht gesetzt, wirft der Aufruf
einen `TypeError`, und zwar im **ersten** Schritt jeder Leseanfrage. Keine
Prüfung nennt `_ensureAuth` überhaupt (vollständig gesucht in `tests/`), und
keine sucht im Baum nach entfernten Schutzformen.

Der Prüfstand ist hier grundsätzlich schwach: er liest Quelltext. Ein
entfernter Schutz sieht im Quelltext *aufgeräumter* aus als vorher — es ist
eine Mutation, die **Zeichen wegnimmt**, und „kommt nicht mehr vor" ist genau
die Form, die ein Anwesenheitsriegel nicht bemerkt.

### 3. (geschlossen) Byte-Identität der plombierten Funktionen

Auf `a26e2b0` konnte man `_maWaehlbar` — Lohn- und Auswahllogik, ausdrücklich
TABU — anfassen, ohne einen einzigen roten Fall zu erzeugen; die einzige
Zusicherung lag in einem Skript, das keine Kette fuhr (so steht es auch in
`docs/befunde/DIE_FUENFZEHN_LESER.md`, Zeile 1 der Tabelle). Seit `97cc02f`
ist das geschlossen. Es ist die einzige der drei Klassen, die während dieser
Messung von jemand anderem geschlossen wurde — ein Beleg dafür, dass die
Lücke echt war und nicht ein Messfehler.

---

## Was diese Messung nicht abdeckt

Der Umfang ist die halbe Aussage.

* **Der Baum.** 14 Mutationen an 14 einzeln benannten Stellen. Für die Klassen
  mit mehreren Vertretern (26 × `ww<BP_MOB`, 22 × `h2`, 355 × `catch`, 4 ×
  `canDo("material_delete")`) wurde **eine** Stelle gemessen. Eine Klasse, die
  an der gemessenen Stelle rot wird, kann an einer anderen still bleiben — die
  Riegel Nr. 3 und Nr. 5 nennen ihre erlaubten Stellen ausdrücklich einzeln,
  andere zählen nur.
* **Die zweiten Vertreter fehlen.** Für die beiden blinden Klassen waren
  Bestätigungsmutationen an einer *anderen* Stelle vorbereitet (zweiter
  schluckender `catch` in `[besch-print]`, zweiter Null-Schutz
  `(prev||[]).map`) — nicht gefahren, weil `index.html` gewechselt hat. „0 rot"
  steht damit je Klasse auf **einer** Stelle.
* **Fünf Testdateien waren draußen** (`--ignore`, siehe oben). Ihre Fälle
  können in keiner Zeile rot werden. Rund 44 Fälle der 3210.
* **Der Testbaum stand nicht still.** `tests/test_symbolknoepfe_haben_namen_v957.py`
  und `tests/test_zusammengesetzte_knopfnamen_v960.py` wurden um 15:34/15:36
  von einem anderen Agenten geändert, also während Welle 2. Die eingesammelte
  Fallzahl blieb in allen Läufen bei 3166; Mutation Nr. 5 (Knopfname) lief in
  Welle 1 und damit **vor** diesen Änderungen.
* **Kein Verhalten am Schirm.** Gemessen ist, was der Prüfstand aus Quelltext
  und aus in Node ausgeführten Schnitten sieht. Ob Mutation Nr. 11 im
  Hellmodus wirklich 57,5 % des Schirms dunkel färbt, steht nicht hier, sondern
  in `docs/befunde/HELLMODUS_ANSICHTEN.md`.
* **Kein Urteil über Richtigkeit.** Auch eine Mutation, die 11 Fälle rot macht,
  sagt nichts darüber, ob die 11 Fälle die *richtige* Sache prüfen.

---

## Nachfahren

```sh
# 1. Kopien erzeugen (schreibt nur _mess_mut_*.html, liest index.html)
python mutieren.py

# 2. Grundlauf und je eine Mutation, Urteil aus der Logdatei
sh lauf.sh grund
sh lauf.sh 12_catch_schluckt

# 3. Auswertung gegen den Grundlauf
python auswerten.py
```

Die 14 Kopien `_mess_mut_*.html` sind **stehengelassen**. Sie sind git-ignoriert,
aber sie sind seit 15:40 der einzige Träger des gemessenen Standes v3.9.961 auf
dieser Platte: `mutieren.py` kann sie aus dem heutigen `index.html` **nicht**
mehr erzeugen. Wer sie wegräumt, räumt die Grundgesamtheit dieses Berichts weg.

Voraussetzung ist der Stand `index.html` md5 `20783957517acbdf18ae7e38729c3f54`;
`mutieren.py` bricht sonst am Anker ab, statt still etwas anderes zu messen.
Die vier Skripte liegen **nicht** im Repo — sie sind Messwerkzeug einer Sitzung,
kein Bestandteil des Prüfstands. Wer die Probe wiederholbar haben will, muss
sie einhängen; dann gilt für sie dieselbe Frage wie für alles andere hier:
**wird sie rot, wenn sie kaputt ist?**
