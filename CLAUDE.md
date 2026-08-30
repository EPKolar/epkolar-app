# EPKolar-App — Claude-Code Hinweise

## Repo-Pfade — Arbeitsklon vs. Spiegel (seit 13.07.2026)

| Pfad | Rolle |
|---|---|
| **`C:\repos\epkolar-app`** | **Arbeitsklon — der einzige.** Alle Edits, Tests, Commits, Pushes laufen hier. **Achtung: auf PC `technik` existiert er nicht von selbst** — dort zuerst `git clone --depth 50 https://github.com/EPKolar/epkolar-app.git` nach `C:\repos\` (am 25.08.2026 so angelegt, Dauer ~1 min). |
| `\\srvdc02\Projekte\…\03_Repos\epkolar-app` (Z:/T:) | **Nur Ablage/Spiegel.** **Keine Edits, keine Commits, kein Push — und kein Pull durch Claude Code.** |

> **Claude Code führt KEINE git-Befehle mehr über Z:/SMB aus — auch keinen Abschluss-Pull.**
> Gemessen 13.07.2026: ein einziger `git pull` über das Share brauchte **74 Minuten**.
>
> **Der Spiegel aktualisiert sich seit 13.07.2026 selbst:** geplanter Task `EPKolar-Spiegel-Pull`
> auf srvdc02, täglich 05:00, läuft als SYSTEM mit portablem MinGit (`D:\tools\git`, kein Installer).
> Aktion: `git -C "D:\Projekte\…\epkolar-app" pull --ff-only origin main`
> (`--ff-only` als Schutz — der Spiegel darf **nie** mergen). Server-lokaler Pfad ist `D:\Projekte\…`,
> **nicht** der UNC-Pfad. Erster Lauf verifiziert: Exit 0, 127 s, Stashes unversehrt.
>
> Der Spiegel enthält seit 13.07. ohnehin keine Unikate mehr — beide Stashes liegen als Patch in
> `docs/wip/`. GitHub ist die Quelle der Wahrheit.

**Warum:** Das srvdc02-Share ist für git/pytest unbrauchbar langsam. Gemessen am 12.07.2026:
pytest 2h04 (lokal: 21 min) · `git push` 28–30 min (lokal: Sekunden) · `git commit`/`git status`
laufen regelmäßig in Minuten-Timeouts, ein gekillter Lauf hinterlässt eine stale
`.git/index.lock` · dazu ein SMB-Aussetzer mitten im git-Befehl
(»unable to open object pack directory: Function not implemented«).

> **Achtung Laufwerksbuchstaben (nur noch für den Spiegel relevant):** auf Sebastians Desktop liegt
> der Spiegel unter `T:`. **Auf PC `technik` gemessen am 25.08.2026: `T:` = `\\srvdc02\Projekte`,
> also SEHR WOHL der Spiegel; `W:` = `\\srvdc02\Technik`.** Die frühere Notiz hier (`Z:` = Repo,
> `T:` = ein anderer Share) stimmt auf diesem Rechner nicht mehr — im Zweifel `net use` fragen
> statt raten.

**Stashes leben nur auf dem srvdc02-Spiegel** (`stash@{0}` Flotte-GPS-WIP, `stash@{1}` Sebastian-WIP)
und bleiben dort unangetastet. Der Flotte-WIP ist zusätzlich als
`docs/wip/FLOTTE_GPS_WIP_2026-07.patch` versioniert und damit auch im Arbeitsklon vorhanden.

### Regeln für git / node / npm

- Im Arbeitsklon `C:\repos\epkolar-app` arbeiten. Nie den rohen UNC-Pfad `\\srvdc02\…` als
  Arbeitsverzeichnis — CMD/npm haben Bugs damit (»UNC paths are not supported«).
- Edge-Function-Deploys NUR aus `C:\temp\epkfn` (`supabase` CLI verträgt weder UNC noch Netzlaufwerk).
- Vor jedem Commit verifizieren:
  ```
  cd /d C:\repos\epkolar-app
  git rev-parse --show-toplevel
  # erwartet: C:/repos/epkolar-app
  ```

### Tests

Voller Lauf direkt im Arbeitsklon: `python -m pytest tests/ -q` (~21 min, ~1172 Tests).
Gate ist **voller Lauf grün** — keine fixe Testzahl. Auf dem Share NIE testen.

## Versionierung — 4 Stellen synchron halten

**Nimm das Skript, nicht die Hand:**

```
python scripts/version_bump.py 3.9.879 "Kurzbeschreibung OHNE Versionsprefix"
python scripts/version_bump.py --pruefen      # meldet doppelte Kopf-Prefixe
python scripts/version_bump.py --reparieren   # raeumt sie auf
node sql/_check_version.js                    # danach IMMER
```

Warum: am 28.08. ging der Handsprung an EINEM Tag **viermal** gleich daneben — der
sw.js-Kopf bekam die Version doppelt (`v3.9.878 - v3.9.878 - …`), weil die Vorlage das
Prefix schreibt und der uebergebene Text schon eines hatte. Folgenlos, aber vermeidbar.
Das Skript setzt das Prefix je Stelle **genau einmal** und prueft vor dem Schreiben, dass
es keine neue Doppelung erzeugt. `_check_version.js` bleibt bewusst ein **eigener** Riegel
und wird vom Bump-Skript NICHT aufgerufen.

Die vier Stellen (was das Skript anfasst):
1. `index.html` `var SW_VER='epkolar-vX.Y.Z'` (Z.15)
2. `index.html` `const APP_VERSION="X.Y.Z-supabase"` (Z.~2463) — Versions-Historie als trailing comment-Chain
3. `sw.js` Header-Kommentar Zeile 1
4. `sw.js` `const CACHE_NAME = "epkolar-vX.Y.Z"` (Z.2)

## Gates vor jedem Push

```
python scripts/node_check.py index.html     # exit 0
python scripts/_bracket_check.py index.html # () -1, {} 0, [] 0 (Baseline)
node sql/_check_version.js                  # ✓ versions synced
python -m pytest tests/ -q                  # voller Lauf grün (~40 s)
```

### …und danach der Browser-Check. NICHT optional.

```
python -m http.server 8899 --bind 127.0.0.1   # im Repo-Wurzelverzeichnis, im Hintergrund
# Seite laden (Playwright/Chrome), dann prüfen:
#   - Console: 0 errors
#   - typeof APP_VERSION !== 'undefined'   (sonst ist der Script-Body abgebrochen)
#   - document.querySelector('#root').children.length > 0   (React gemountet)
```

### …und bei Änderungen an Views: der Tab-Durchlauf

```
python scripts/tab_sweep.py                                    # gegen Live
python scripts/tab_sweep.py http://127.0.0.1:8899/index.html   # lokal
```

Der Browser-Check oben lädt nur die **Startseite**. Ein Prop, das auf einen nicht
existierenden Namen zeigt, wird wegen des `&&`-Kurzschlusses aber **nur beim Öffnen
genau seines Tabs** ausgewertet — und reißt dann die ganze App auf die Fehlerseite,
weil der ReferenceError im Render von `App` entsteht und keine `_ViewBoundary` ihn
fangen kann.

**Genau so stand „Monatsabrechnung" monatelang kaputt live** (25.08.2026,
`approvals` statt `absApprovals`) — und ein pytest-Test hatte den kaputten Wortlaut
sogar wortgleich festgeschrieben und war grün dabei. `node_check` parst nur, pytest
ist statisch, der Browser-Check sieht nur die Startseite. Der Tab-Durchlauf ist das
einzige Gate, das diese Fehlerklasse sehen kann. Kostet zwei Minuten.

Braucht einmalig `pip install playwright && playwright install chromium`.

**Seit 29.08.2026 tatsaechlich ausgefuehrt** — gegen die Live-App, v3.9.896:
**alle 18 Ansichten sauber**. Davor stand es drei Handoffs lang als „nie
ausgefuehrt“ im Repo.

> **Und der erste Lauf ist an der ERSTEN Ansicht gestorben — nicht an der App,
> an sich selbst.** Die Tab-Namen tragen Emoji („🏠 Home“), Windows-stdout
> ist cp1252, und `print("%-20s ok" % name)` warf `UnicodeEncodeError`. Der
> Fehler sass nicht im **Messen**, sondern im **Berichten**: Ansicht 1 war
> korrekt geprueft, das Gate fiel beim Ausgeben des Ergebnisses um. Es haette
> nie einen Befund melden koennen.
>
> Dieselbe Krankheit wie die geloeschte `index.html`, nur andersherum: dort
> meldete ein Gate **gruen**, wo alles weg war; hier konnte eines **gar nichts**
> melden. Beide Male war das Messgeraet das Problem, nicht das Gemessene.
> → **Die Transkription eines Laufs ist kein ausgefuehrter Lauf.** Ein Werkzeug
> gilt erst als vorhanden, wenn es einmal echt gelaufen ist.
> Abgesichert durch `tests/test_tab_sweep_v897.py` (mit Umkehrprobe: ohne die
> Reparatur stirbt derselbe `print` nachweislich).

**Warum das ein Pflicht-Gate ist — teuer gelernt am 14.07.2026:** v3.9.691 hinterließ
`window._stUuid=_stUuid;` in der Export-Zeile, obwohl `_stUuid` gelöscht war. Ergebnis:
`ReferenceError` auf **Top-Level** → der gesamte Script-Body danach (also die komplette App)
wurde nie definiert. **Die Live-App war über vier Versionen hinweg tot** und niemand hat es
gemerkt.

Keines der bestehenden Gates konnte das finden, und das ist kein Zufall:

| Gate | Warum es blind war |
|---|---|
| `node_check.py` | **parst** die Datei, **führt sie nicht aus**. Syntaktisch war alles korrekt. |
| `pytest` | statisch (String-/Regex-Asserts über den Quelltext). |
| Node-Eval-Tests | die Export-Zeile steht hinter `if(typeof window!=='undefined')` — **in Node gibt es kein `window`**. Der Zweig wurde übersprungen, der Fehler konnte dort gar nicht auftreten. |

**Kein Gate hat das Bundle je geladen.** Ein Browser hätte es in fünf Sekunden gefunden.
Zusätzlich fängt `tests/test_window_exports_defined.py` jetzt genau diese Fehlerklasse
statisch ab (mit Selbsttest: kaputte Zeile → rot, gesunde → grün).

## Push-Weg

`git push origin main`. KEIN `gh`. Remote-Verify per `curl raw.githubusercontent.com/EPKolar/epkolar-app/main/sw.js` nach jedem Push.

## Lektionen 29.08.2026 (v3.9.884-911, Details: `docs/handoffs/HANDOFF_2026-08-29.md`)

**Ein Gate, das auf NICHTS besteht, ist kein Gate.** Ein abgebrochener Schreibvorgang hat
`index.html` auf 0 Bytes gekürzt — und beide Gates meldeten grün: eine leere Datei parst
fehlerfrei und hat ausgeglichene Klammern, und `() 0` sieht sogar **besser** aus als die
erwartete Basislinie `-1`. Wer nur auf die Zahlen schaut, hält den Totalverlust für eine
Verbesserung. Beide haben jetzt eine Lebenszeichen-Prüfung.
→ **Für jede Änderung an `index.html` `scripts/safe_edit.py` benutzen** (Anker müssen genau
einmal treffen, Ergebnisgröße wird geprüft, Schreiben in eine Nebendatei mit Rücklese-
Vergleich, erst dann ersetzen). Die Zieldatei wird gar nicht angefasst, solange nicht
feststeht, dass der neue Inhalt vollständig ist.

**Drei Fehlerklassen, die fast jeden Befund dieser Sitzung erklären.** Wer in `index.html`
sucht, findet damit schneller etwas als über einen Feature-Namen:

1. *Eine Größe wird an zwei Stellen unterschiedlich gerechnet.* Erkennungsmerkmal: zwei
   Zahlen auf einem Bildschirm, die sich widersprechen — und jemand entscheidet nach einer
   davon. **Vor jedem Fix die anderen Verbraucher derselben Größe auflisten.**
2. *Etwas wird berechnet und nie gelesen.* Dreimal in einer Datei gefunden.
   **`grep` nach Variablen ohne Leser lohnt sich als eigener Durchgang** — vier Treffer.
3. *Ein Riegel, der nicht zumachen kann.* Gefährlicher als der offene Riegel ist das
   **Versprechen daneben**: ein Text, der eine Prüfung behauptet, die es nicht gibt.

**Ein Riegel, der auf Zeichenzahl, Zeilennummer oder Wortlaut prüft, misst früher oder
später den Kommentar mit.** Neunmal an zwei Tagen — zweimal davon in meinen eigenen neuen
Tests, und einmal hat ein Kommentar, der eine Muster-Kollision *erklärte*, sie damit
ausgelöst. Keinen abgeschwächt, alle auf die Eigenschaft gezogen.

**`git add -A` ist gefährlich, solange Agenten laufen** — zweimal landeten rote
Testdateien auf `main`. Nur explizite Dateilisten, und die Verfolgung an
`git ls-tree -r HEAD` prüfen, nie an `git status`.

**Ein Riegel darf die EIGENSCHAFT festhalten, nie die SCHREIBWEISE.** Die andere Hälfte
derselben Krankheit — v896 hat vier Fälle an einem Nachmittag gebracht. Der schlimmste:
ein Test verlangte die **Existenz** von `var _kapReal=…`, einer Zuweisung mit **null
Lesern**. Er hat damit keine Eigenschaft gesichert, sondern toten Code *beschützt* und
dessen Ausbau verhindert — kein Schutz, ein Denkmal; seine eigentliche Aussage stand in
der Zeile darunter. Die anderen drei wären **rot geworden, obwohl der Code besser ist
als gefordert**: ein Zeichenfenster `-1200/+400` um einen Namen, ein Variablenname statt
des strengeren echten, und `@media print` in einem Fenster, das ein *eigenständiges*
Druckdokument schreibt — dort wäre es wirkungslos.
→ **Prüffrage vor jedem neuen Riegel: welche Aussage wäre falsch, wenn er rot wird?**
Lässt sie sich nicht in einem Satz über das *Verhalten* sagen, misst der Riegel Form.

**Ein Bestandstest, den man nicht anfassen will, ist kein Grund, eine Lüge im Code
stehenzulassen.** `wocheKm` hieß km, enthielt Fahrminuten, summierte über den ganzen
Horizont statt eine Woche und ließ die fixen Termine aus. Ich hatte umbenannt und den
alten Namen als **Zwilling** danebenstehen lassen, um den einzigen Riegel für eine
andere Eigenschaft nicht kaputtzumachen. Das war Ausweichen: der irreführende Name
blieb Teil der Rückgabe und damit benutzbar, und eine Zahl mit zwei Namen ist dieselbe
Krankheit wie eine Größe mit zwei Rechnungen. Richtig ist, was mehr Arbeit macht:
ersatzlos wegnehmen und **die lesenden Tests mitziehen**.

**Ein leeres Ergebnis auf dem ERFOLGSPFAD ist die gefährlichste Form von Nichtwissen.**
`_sbGet` gab bei 401/403 ein leeres Array zurück — nicht als Fehler, sondern als Erfolg.
Für rund 150 Aufrufer ununterscheidbar von „die Tabelle ist leer“, und **kein
Auffangzweig kann es je sehen**: es kommt gar kein Fehler an. Alles, was an einem Tag
unter „eine Null, die ein Fehlschlag ist“ gefunden wurde (v898, v908, v909), waren die
AUSWIRKUNGEN dieser einen Stelle.
→ **Such die Quelle, nicht nur die Kachel.** Wenn dieselbe Krankheit dreimal an
verschiedenen Orten auftritt, liegt sie meistens in einem gemeinsamen Helfer.
→ Und der Umbau muss **additiv** sein: das Array trägt jetzt seinen Grund
(`__rlsFehler`), `.length` bleibt 0, `Array.isArray` bleibt wahr — **kein Aufrufer ändert
sein Verhalten**. Ein `return null` hätte hunderte mit `.filter is not a function`
zerrissen; genau deshalb blieb die Wurzel jahrelang liegen. Nachsehen: `window.__EP_RLS`.

**Eine Marke ohne Leser ändert nichts.** v910 markierte, v911 las — und erst dann stand
etwas anderes auf dem Schirm. Die drei Kacheln standen bei einem *Fehler* längst richtig
auf `null`; **ein 403 war für sie aber gar kein Fehler**. Wer eine Diagnose einbaut, muss
im selben Zug prüfen, ob irgendjemand sie liest — sonst ist sie ein Denkmal wie jedes
andere.

**Keine Gesamtzahl behaupten, wo benannte Stellen genügen.** An einem Tag lag ein
selbstgeschriebener Riegel **viermal** mit einer Fundstellen-Summe daneben — übersehen
wurden die `useMemo`-Abhängigkeit (v907), die Farbbedingung, die denselben Wert noch
einmal liest (v908), und der `window`-Export, der **keine Klammer trägt** (v911). Jedes
Mal wurde der Riegel zu Recht rot und zeigte seinen eigenen Fehler.
→ In v911 ist die Summe **ersatzlos entfallen**; geprüft werden die drei Stellen
namentlich. **Eine Zahl, die man beim Hinzufügen einer Zeile nachziehen muss, misst die
Buchhaltung und nicht die Eigenschaft.**

**Eine Null, die ein Fehlschlag ist, sieht aus wie ein Ergebnis.** Ein Auffangzweig mit
`catch(_){return 0;}` liefert eine Zahl, nach der jemand HANDELT: „niemand abwesend“ heisst,
die Woche wird mit voller Mannschaft geplant. „Die Rechnung ist fehlgeschlagen“ ist keine
Auskunft und gehoert auch nicht als Zahl auf den Schirm. Dritter Fall dieser Familie:
v3.9.898 („Alle bearbeitet“, ohne je gemessen zu haben), v3.9.892 (geschaetzte Dauer sah
aus wie vereinbarte), v3.9.908 (`absThisWeek`).
→ **Pruefe bei jedem Auffangzweig: landet der Wert vor einem Menschen?** Wenn ja, muss er
NICHT GEMESSEN sagen koennen. In diesem Repo kann die Anzeigefunktion `_metric` das
laengst (`null` → drei Punkte) — bei v908 war der Fix deshalb EINE Zeile. **Die
Faehigkeit war da, sie wurde nur nicht benutzt**; das ist der haeufigere Fall, nicht die
fehlende Faehigkeit.

**Zeitfenster: nachrechnen, nicht dem Namen glauben.** Die Klasse hat an einem Tag DREIMAL
zugeschlagen — `from + 32*TIME_DAY` als „Monat“ (Kilometergeld zweimal ausgewiesen,
v897), ein Fenster bei HEUTE abgeschnitten waehrend das Nachbarfenster voll war (v901),
und `+(14-day)` als „sieben Tage“ (der Sonntag fiel heraus, v907).
→ **Ein Fenster misst man, indem man den ersten und den letzten enthaltenen Tag ausgibt**
— gegen einen Montag, einen Sonntag, einen Monatsersten, ein Schaltjahr und eine
Zeitumstellung. Und: die Grenze bleibt HALBOFFEN, sonst gehoert ein Tag zwei Fenstern.

**Mein blinder Fleck bei Zaehl-Riegeln: die zweite Verwendung IM SELBEN AUSDRUCK.**
Dreimal an einem Tag hat ein selbstgeschriebener Zaehl-Riegel die falsche Zahl erwartet
— die `useMemo`-Abhaengigkeit (v907), die Farbbedingung, die denselben Wert noch einmal
liest (v908). Jedes Mal wurde er zu Recht rot und hat seinen eigenen Fehler gezeigt.
→ Vor jedem `count(...) == N`: alle Vorkommen einmal ausgeben lassen, nicht schaetzen.

**Zaehl ERST, raeum DANN.** Auf „die Liste ist zu mächtig“ war die Versuchung, sofort
aufzuräumen. Das Zählen hat die Antwort geliefert und zugleich die Priorität umgedreht:
6 Bedienelemente in der Kopfzeile, aber **6 Editoren je ZEILE** — bei dreißig Zeilen 180
aktive Bedienelemente. Die Kopfzeile war das kleinere Problem, und die Doppelung dort
(jeder Filter steht als Feldwert UND als Chip darunter) hätte ich nie geraten.

**Ein Auswahlfeld feuert `change` bei JEDEM Pfeiltasten-Schritt.** Gemessen: vier
Pfeiltasten → vier Ereignisse, vier Werte. In der Arbeitsschein-Liste hängt an jedem
Zeilen-Auswahlfeld ein sofortiges Schreiben.

🔴 **RICHTIGSTELLUNG (selbe Sitzung).** Ich hatte daraus geschlossen, der Schein werde
unterwegs an jeden Monteur dazwischen gehängt, mit einem Push je Schritt. **Das ist
falsch**, am Code nachgemessen:
* `updAs` aktualisiert den Zustand **sofort und lokal** — die Anzeige stimmt immer.
* `SQ.push` setzt bei jedem Schreiben den Sammel-Zeitgeber zurück; alle vier landen in
  **einem** Stapel, und der letzte Wert gewinnt.
* Der OFFA-Push läuft seit v3.9.756 über eine **per-Schein-Debounce-Klammer**, die
  ausdrücklich zusammenfasst (Kommentar dort: *10 Writes/1s = 1 Tick*).

Es bleibt: **vier PUTs an die eigene API statt einem** — Rauschen, kein Datenfehler.
→ Die Lehre ist nicht die Zahl, sondern der Reflex: **eine gemessene Ereigniszahl ist
noch keine gemessene Wirkung.** Ich hatte vier `change` gezählt und daraus vier Pushes
geschlossen, statt den Schreibpfad zu Ende zu lesen — dieselbe Lücke wie zwischen
ANKUNFT und WIRKUNG beim Datenmodus.
→ Der Fix ist NICHT trivial, und das gehört dazugesagt: Schreiben auf `blur` verschieben
scheitert daran, dass das Feld **kontrolliert** ist (die Anzeige springt zurück);
Pfeiltasten abfangen ist ein Rückschritt für die Tastaturbedienung; Entprellen braucht
ein Nachziehen beim Verlassen und beim Auskängen. **Lieber belegt offen lassen als
halb reparieren.**

**Ein widerlegter Verdacht spart einen Riegel.** Mausrad über einem Auswahlfeld ändert
den Wert nicht — in beide Richtungen gemessen, mit Gegenprobe, dass das Feld überhaupt
änderbar ist. Ohne die Messung hätte ich einen `onWheel`-Schutz an 131 Auswahlfelder
geschrieben, gegen ein Nicht-Problem.

**Ein Riegel misst ANKUNFT oder er misst WIRKUNG — das ist nicht dasselbe.** Beim Bau des
Datenmodus für `tab_sweep.py` hatte ich zwei Nachweise eingebaut: die Saat liegt in der
Datenbank (zurückgelesen), und die Saat erscheint in der Oberfläche (Text gefunden). Beide
waren grün. Der Lauf blieb trotzdem blind, weil die Saat `scheinstatus:"offen"` trug — **den
Status gibt es nicht**, die Dispo filtert über `AS_GRP_OFFEN`. `fixMap` blieb leer, die
fehlerhafte Schleife wurde nie betreten.
→ **Frag bei jedem Messaufbau: weise ich nach, dass die Daten ANGEKOMMEN sind, oder dass sie
GEWIRKT haben?** Der vierte Riegel rechnet `fixMap` jetzt mit `window._dispoBuildInput`
nach. Bewusst *gerechnet* statt im DOM gesucht: gegen eine kaputte Fassung stürzt genau
dieses Rendern ab, ein DOM-Riegel würde den Fund als eigenen Defekt ausgeben.

**`indexedDB.open` legt eine fehlende Datenbank wortlos neu an.** Ein Tippfehler im Namen
(`epkolar` statt `epkolar_offline`) erzeugt keinen Fehler, sondern eine leere Datenbank —
und jede folgende Prüfung ist grün und wertlos. Dieselbe Klasse wie `_ymd` gegen
`toISOString`: eine falsche Wahl, die sich nicht beschwert.

**Ein Messgerät darf nicht ausgeben, was man ihm gegeben hat.** Meine erste Saat meldete
„2 Monteure gesät" aus `mon.length` — aus der EINGABE. Sie hätte das bei jedem denkbaren
Fehler gesagt. Jetzt wird zurückgelesen und die tatsächlich gespeicherte Zahl gemeldet.

**Der einzige Riegel, der einen Syntaxfehler mitten im Render gefangen hat, war der, der
jeden `<script>`-Block EINZELN prüft** (`test_integration_smoke`). Ein Anwender-Skript zog
eine Trennzeile aus einer Paardatei (`# ==== OPTION B ====`) in eine Ersetzung — die App
wäre gar nicht gestartet. `node_check` blieb grün (es prüft die Datei anders), und die
Klammerbilanz blieb grün, **weil der Changelog-Text zufällig eine Klammer beisteuerte, die
die fehlende ausglich**. Zwei Tore grün, eines rot — und nur das rote hatte recht.
→ Merksatz: **ein Tor, das den ganzen Kessel prüft, kann von einem Fehler an anderer Stelle
ausgeglichen werden.** Deshalb bleibt die blockweise Prüfung Pflicht.

**Vier freie Namen sind noch in der Datei** (`ev`, `_built`, `_user`, `A` — Handoff 7j),
gefunden mit echtem Parser und einer Mutationsprobe: 40 verbogene Referenzen, 40 erkannt.
Zwei davon sind **stille Denkmäler** — ein `catch` fängt den ReferenceError, und der
Kommentar daneben verspricht eine Wirkung, die es seit der Einführung nie gab.

**Ein Riegel, der eine Schreibweise zählt, kann einen Fehler im Rumpf nicht sehen.** Am
29.08. stand ein Live-Absturz in der Dispo: ein Rückruf war als `tf` deklariert und als
`f` gelesen — unter `"use strict"` ein `ReferenceError` im Render, also Fehlerseite. Er
kam mit v3.9.894 herein, ausgerechnet mit dem Umbau, dessen Kommentar eine Zeile darüber
erklärt, *warum* der Parameter `tf` heißen muss; die Umbenennung wurde an **einer von vier**
Verwendungen vergessen. Alle drei Tore waren grün:

| Tor | Warum es blind war |
|---|---|
| `node_check.py` | **parst** nur — ein freier Name ist syntaktisch fehlerfrei |
| `tab_sweep.py` | meldet sich ohne echte Zugangsdaten an → alle Abrufe 401 → die datenabhängigen Renderpfade werden nie betreten |
| der Riegel daneben | prüfte die **Eindeutigkeit einer Schnittmarke** und konnte den falschen Namen im Rumpf prinzipiell nicht sehen |

→ **Für jeden Renderblock, der Daten braucht, gilt: schneiden und AUSFÜHREN, nicht
suchen.** Ein `assert "muster" in index_html` sichert die Schreibweise, nie das Verhalten.
Vorbild: `tests/test_dispo_tagesplan_freier_name_v899.py` — schneidet den echten Block aus
`index.html`, lässt ihn in Node gegen gestellte Daten laufen, und die Umkehrprobe baut den
alten Namen zurück und besteht darauf, dass es dann wirft.

**Der Tab-Durchlauf sieht nur, was ohne Anmeldung rendert.** Das steht seit v3.9.897 in
den Notizen — und hat noch am selben Tag etwas gekostet. Eine bekannte Grenze macht ein
Messgerät nicht harmlos: sie muss **bei jedem grünen Lauf mitgelesen** werden. „18/18
sauber" heißt „18 Ansichten starten leer", nicht „die App ist heil".

**Der Datenfall entscheidet, wann ein Fehler sichtbar wird — nicht die Ansicht.** Der
Absturz zeigte sich als „nächste Woche", weil `fixMap` nur Termine ab heute aufnimmt und
die Startwoche an einem Samstag komplett Vergangenheit war. Ab Montag hätte dieselbe Zelle
auch die laufende Woche zerrissen. **Wenn ein Nutzer einen Auslöser nennt, prüfe erst, ob
er die Ursache ist oder nur der heutige Kalender.**

**Ein Test, der die Existenz einer ungelesenen Größe fordert, konserviert sie.** Inzwischen
**fünf** belegte Fälle: `_kapReal` (v896), `Basis 38,5h` (v898), `_normFrei` und `_evCache`
(v900) — und bei `_evCache` besonders lehrreich: von drei Pins wurden die zwei mit echter
Aussage in v3.9.769 korrekt stillgelegt (*„dieser Pin testet toten Code"*), der dritte
sicherte nur die Existenz und blieb aktiv. Er hat die tote Referenz **samt ihrem lügenden
Kommentar** am Leben gehalten.
→ Bei `_normFrei` kam etwas hinzu, das die Klasse erweitert: die Funktion hieß „Rest-
Kapazität der **Hand-Wand**", aber die Hand-Wand rechnet an **drei anderen** Stellen. Der
Riegel war also nicht nur nutzlos — **er vermaß seit v3.9.790 einen Weg, den niemand geht.**

**Ein Messgerät, dessen Werte nicht auseinandergehen KÖNNEN, misst nichts.** Am 29.08.
ist `scripts/perf_live.py` **dreimal an sich selbst gescheitert**, bevor es zum ersten Mal
etwas gemessen hat — und jedes Mal sahen die Zahlen brauchbar aus:

| Was herauskam | Warum es Unsinn war |
|---|---|
| 18 Ansichten, 18× exakt `12.8 MB` Heap | Chromium rundet `performance.memory` grob, solange `--enable-precise-memory-info` fehlt |
| 18 Umschaltzeiten zwischen 460 und 468 ms | mein eigener `wait_for_timeout(450)` — **ich habe meinen Sleep gemessen, nicht die App** |
| danach 14× `-1` („nichts gerührt") | ab Runde 2 wurde auf den **bereits offenen** Tab geklickt |

Keiner der drei hätte einen Absturz erzeugt; alle drei hätten eine Tabelle geliefert, die
man in einen Handoff schreibt. Gefunden nur, weil eine Spalte ohne Streuung misstrauisch
macht. → **Prüffrage bei jeder neuen Messung: welcher Wert wäre auffällig, und kann er
überhaupt auftreten?** Streuen die Werte über sehr unterschiedliche Fälle kaum, misst man
den Aufbau. `perf_live.py` meldet solche Spalten seither **selbst als ungültig**.

**Die Transkription eines Laufs ist kein ausgeführter Lauf.** `scripts/tab_sweep.py` stand
drei Handoffs lang als „nie ausgeführt" im Repo. Beim ersten echten Start starb es an der
**ersten** Ansicht — nicht an der App, an sich selbst: Emoji-Tabnamen auf cp1252-stdout.
Der Fehler saß nicht im Messen, sondern im **Berichten**. Ein Werkzeug gilt erst als
vorhanden, wenn es einmal echt gelaufen ist.

**`scripts/safe_edit.py` gilt für JEDE Datei, nicht nur `index.html`.** Am 29.08. hat
dasselbe Surrogatpaar (ein Emoji als `📌` im Python-Quelltext) **zweimal** eine
Datei auf 0 Bytes geleert: erst `index.html`, später einen Handoff — beim zweiten Mal
genau deshalb, weil ich das Schutzmodul nur für `index.html` benutzt habe. Der Mechanismus
ist immer derselbe: `io.open(p,"w")` leert die Datei, und die Kodierausnahme fliegt erst
danach. → `ersetze(pfad, paare, min_bytes=5_000)` auch für Handoffs und Skripte. Das
Modul weist einzelne Surrogate jetzt **vor** dem Öffnen ab und nennt den Grund.

Im Kleinen ist das dieselbe Krankheit wie „eine Reparatur an einer von vier Stellen ist
keine": ein Schutz, der nur an einer Stelle angewandt wird, ist keiner.

**Backslashes in Bash-Heredocs: achtmal**, einmal mit zerstörtem Code. Die Regel stand
schon dreimal in den Notizen. Wenn sie achtmal nicht greift, ist das Werkzeug falsch —
`chr(92)`/`chr(10)`/`chr(34)` oder die Edit/Write-Werkzeuge. **Dazu neu: Python-Code
über stdin-Heredoc wird nach cp1252 dekodiert** — Umlaute zerbrechen dann die Quelle.
Skript in eine Datei schreiben und diese aufrufen.

---

## Lektionen 28.08.2026 (Details: `docs/handoffs/HANDOFF_2026-08-28.md`)

**Ein Riegel, der die Lücke des Geprüften teilt, misst nichts.** `test_feiertag_v3996`
listete die 2026-Feiertage **ohne den 26.10.** — genau den Tag, den auch `_isATFeiertag`
nicht kannte. Der Test war grün, während Urlaub und Zeiterfassung am Nationalfeiertag
volle 8,5 Sollstunden rechneten. Fünfter Beleg derselben Krankheit (vier Riegel am 23.08.,
der `approvals`-Test am 25.08., `tab_sweep` am 28.08.).
→ Beim Schreiben eines Tests immer fragen: *woher weiß ich, dass meine Erwartungsliste
vollständig ist?* Die Antwort darf nicht „aus derselben Quelle wie der Code" sein.

**Vor jedem Fix die anderen Verbraucher derselben Größe auflisten.** Den Status-Filter
einfach in `msF` zu ziehen wäre der naheliegende Fix gewesen — und hätte die Status-Zähler
auf 0 gesetzt, weil die aus `msF` zählen. Die fünf Minuten Prüfung haben den Folgeschaden
verhindert **und einen zweiten Fehler mitgefunden** (Prio-Zähler zählten aus einer bereits
nach Prio gefilterten Menge).

**Feste Zeichenfenster in Tests sind eine Schuld, kein Werkzeug.**
`test_juprowa_selfheal_v755` prüfte 2400 Zeichen ab `const updAs=`; die Funktion ist
inzwischen 3338 Zeichen lang. Der Riegel maß die **Kommentarlänge** mit und wurde rot,
obwohl der geprüfte Aufruf unverändert dastand — das Fenster war schon einmal nachgezogen
worden. Jetzt Abgrenzung bis zur nächsten Deklaration derselben Ebene: prüft mehr, nicht
weniger.

**Backslashes zerfallen in Bash-Heredocs — dreimal an einem Tag.** `"\n"` wird zum echten
Zeilenumbruch und hat eine Testdatei zerlegt (und früher schon einen Pfad im Memory).
→ Für alles mit Backslash `chr(92)`/`chr(10)` verwenden **oder die Edit/Write-Werkzeuge
statt der Shell**.

**Agenten-Befunde sind Hypothesen.** Jeder umgesetzte Befund wurde selbst am Code
nachgeprüft. Zwei waren dabei größer als gemeldet, einer anders gelagert. Ein widerlegter
Befund ist ein vollwertiges Ergebnis — Agenten ausdrücklich dazu ermächtigen.

---

## Lektionen 24./25.08.2026 — die Wisch-Jagd (Details: `docs/handoffs/HANDOFF_2026-08-25.md`)

Acht Versionen, bis der gemeldete Fehler gefunden war. Jede Messung war grün, während zwei
Nutzer unabhängig das Gegenteil berichteten. Was daraus zu lernen ist:

- **Widersprechen sich Messung und zwei Nutzerberichte, hat die MESSUNG unrecht.** Nicht genauer
  messen — anders messen. Der Unterschied liegt dort, wo die Messung die Wirklichkeit vereinfacht.
- **Synthetische und CDP-Touch-Gesten durchlaufen die Scroll-Arbitrierung des Browsers nicht wie
  ein echter Finger.** Der Standard-Playwright-Kontext hat sogar `hasTouch:false` — dann kann gar
  keine echte Geste entstehen. Für Gesten: `newContext({hasTouch:true,isMobile:true})` + CDP
  `Input.dispatchTouchEvent`.
- **Mit der ROLLE und den DATEN des Meldenden messen.** Als Admin mit vollen Daten war der Fehler
  unsichtbar; als `monteur` mit leerer Liste fiel er sofort auf.
- **Nach einem VERGLEICH fragen, statt blind weiterzumessen.** Die drei entscheidenden Hinweise
  kamen alle vom Nutzer: „quer geht, hoch nicht" · „nur in der Leiste" · „im Projekt geht's".
- **Wer scrollt, entscheidet, wem eine Geste gehört.** Scrollt die Seite, nimmt Chrome sie auf
  oberster Ebene. Scrollt ein Container, bleibt sie beim Element. Das war die Ursache.
- **Ein Test kann einen Absturz FESTSCHREIBEN.** `test_monatsabrechnung_v813` prüfte den Wortlaut
  einer Callsite (`approvals: approvals`) statt der Quelle — grün, während der Tab die ganze App
  umriss. Bei Props-Riegeln die QUELLE prüfen, nicht den Text.
- **Verdacht auf Selbstverschulden? Gegen die Vorversion messen:** `git show <alt>:index.html` auf
  eigenem Port servieren, identische Sequenz fahren. So war die Leaflet-Regression in Minuten belegt.
- **Ablesung an `aria-current`, nie am sichtbaren Text** — „Planung" und „Zeiterfassung" beginnen
  beide mit „◀ KW 35 / 2026". Und React rendert asynchron: 300–600 ms warten.
- **Ein Fix, den niemand antippt, kommt nie an.** Der Update-Banner funktionierte, verlangte aber
  einen Tipper. Seit v868 wendet die App ein Update selbst an, wenn nichts verloren gehen kann.

## Lektionen 14./15.07.2026 — Kurzindex (Details in den Abschnitten darunter)

- **Browser-Check ist Pflicht-Gate** (14.07.): `node_check` parst nur, lädt nie das Bundle. Ein
  `window._x=_y` ohne Deklaration killte die Live-App 4 Versionen lang. → Seite laden, 0 Console-Errors.
- **Kommentar-Behauptung braucht Test** (14.07.): „DST-sicher"/„stempelt NICHT"/„ERROR raus" waren alle
  drei falsch und standen als Fakt im Code. Behauptet ein Kommentar eine Eigenschaft, beweist ein Test sie.
- **Kein `CREATE OR REPLACE` aus Repo-Rekonstruktion** (14./15.07.): erst `pg_get_functiondef` aus der DB.
  `v3911` war für alle 5 guard-Trigger unvollständig (+793/+99/+69/+66/+19); ein Replace hätte Live-Logik
  gelöscht. Live-Bodies liegen als `docs/wip/*_LIVE_2026-07-14.sql`.
- **Jede Mess-Query trägt einen Kontrollwert** (15.07.): Cross-Engine-Normalisierung lügt (`\s` = nur ASCII
  in Postgres, auch Unicode in Python). Nur ein verfehlter Kontrollwert entlarvte die kaputte Messung.
- **Generierte Live-berührende Artefakte tragen einen Selbst-Nachweis** (15.07.): `TERMINAL_FINAL_v3` beweist
  per Test, dass v3-Body-minus-Zweig = Live-Body — der Replace fügt nur hinzu, löscht nichts.
- **SQL-Pakete PARSE-testen, nicht nur hashen** (15.07.): `TERMINAL_FINAL_v3` hatte den richtigen Inhalt,
  aber nach `$function$` fehlte ein `;` (`pg_get_functiondef` liefert keins) → `42601`, Batch lief gar nicht.
  Ein Hash prüft Inhalt, nicht Syntax. Vor dem Human-Run einen Parse-Smoke (sqlglot/EXPLAIN) laufen lassen.
- **`sql/` im main-Checkout ist eine geladene Waffe** (14.07.): Sebastian kopiert von dort in den SQL-Editor.
  Ungepushte/gefährliche Stände nie dort liegen lassen (WIP → `docs/wip/`), Gefährliches auskommentieren.
- **Fund außerhalb des Auftrags** (14.07.): erst melden, Beleg zeigen, Freigabe abwarten — nicht ungefragt
  committen (Ausnahme: akute Live-Störung, dann im Report ansagen).
- **DB-Body-Transfer via Datei, nicht Chat-Paste** (15.07.): `CREATE FUNCTION`+`$$`+`RAISE` triggert den
  Content-Filter (3× gescheitert). Datei ins Repo/Laufwerk, oder OAuth für den Supabase-MCP.

## Behauptet ein Kommentar eine Eigenschaft, muss ein Test sie beweisen

Ein Kommentar wie „DST-sicher", „stempelt NICHT", „COLORS.ERROR raus" ist eine **Absichts-
erklärung, kein Fakt** — bis ein Test ihn belegt. Am 14.07.2026 waren **alle drei** dieser
wörtlichen Commit-Behauptungen falsch, und alle drei standen als Tatsache im Code:

- *„Basis 12:00 → DST-sicher"* — die Schleife verlor im Frühjahr einen ganzen Tag aus der
  Lohnabrechnung.
- *„Im Antrags-Modus stempelt der Scan NICHT"* — er stempelte in jedem Zustand außer `ident`.
- *„v3.9.697: COLORS.ERROR raus"* — an einer von drei Stellen stand es noch drin.

**Regel:** Behauptet ein Kommentar eine nicht-triviale Eigenschaft, schreib den Test, der sie
beweist — im selben Commit. Das gilt besonders für alles Lohnrelevante und für jede „X passiert
NICHT"-Aussage (die sind am teuersten, weil sie ein Schweigen versprechen).

## `CREATE OR REPLACE` auf Live-Objekte — NIE aus einer Repo-Rekonstruktion

**Regel:** Bevor eine Live-Funktion/-View per `CREATE OR REPLACE` ersetzt wird, **immer zuerst den
Ist-Body aus der DB ziehen** und darauf aufbauen. Eine Datei im Repo, die behauptet, den Live-Stand
abzubilden, ist eine **Behauptung**, kein Beweis.

```sql
-- 1) Ist-Stand holen (das ist die einzige Wahrheit):
select pg_get_functiondef(oid) from pg_proc
 where pronamespace='public'::regnamespace and proname='<funktion>';

-- 2) Normalform-Hash des FUNKTIONSKÖRPERS (prosrc = nur der Text zwischen den
--    Dollar-Quotes; Whitespace-Läufe → ein Space, trimmen, dann MD5).
--    Das ist das Standard-Werkzeug: zwei Bodies sind identisch, wenn ihr Hash gleich ist.
select md5(btrim(regexp_replace(prosrc, '\s+', ' ', 'g')))   as body_md5,
       length(btrim(regexp_replace(prosrc, '\s+', ' ', 'g'))) as body_len
  from pg_proc
 where pronamespace='public'::regnamespace and proname='<funktion>';
```

Denselben Hash über den Body in der Repo-Datei rechnen. **Weichen Hash oder Länge ab, ist die
Repo-Datei keine Replace-Basis** — Punkt. Nicht „wahrscheinlich schon", nicht „nur Formatierung".

### Absolute Regel für die fünf Security-Trigger (unbefristet)

`sql/security_triggers_LIVE_v3911.sql` rekonstruiert fünf Trigger:
`guard_urlaub_edit` · `guard_kontingent` · `guard_users_privilege` · `guard_admin_only` ·
`guard_projects`.

> **KEIN `CREATE OR REPLACE` auf irgendeinen dieser fünf, dessen Live-Body nicht als
> `docs/wip/<name>_LIVE_<datum>.sql` gesichert UND hash-verifiziert ist.**

Gemessen wurde bisher nur `guard_urlaub_edit` — Live **1746** Zeichen normalisiert gegen **953** in
der Repo-Datei. **~800 Zeichen echter Logik fehlen dort.** Ein Replace hätte sie kommentarlos
gelöscht: kein Fehler, kein Rollback, keine Warnung. Die anderen vier stammen aus derselben
Rekonstruktion und sind bis zur Messung **unverifiziert** — darunter `guard_users_privilege`, der
Schutz gegen Rechte-Eskalation.

`sql/VERIFY_TRIGGER_BODIES_v2.sql` misst alle fünf auf einmal gegen die DB (read-only, gefahrlos).
**Vor jedem Eingriff ausführen.**

### Jede Mess-Query trägt einen Kontrollwert. Ohne getroffenen Kontrollwert ist der Lauf ungültig.

Eine Messung, deren Ergebnis „plausibel aussieht", ist kein Beweis — sie ist eine Vermutung mit
Nachkommastellen. **Jede Mess-Query braucht einen Wert, dessen Soll man unabhängig kennt.**

Am 14.07.2026 hat genau das den Fehler gefangen: Die Verify-Query lieferte für
`guard_urlaub_edit` ein Delta von **879** statt der erwarteten **~793**. Das Ergebnis der Query sah
für sich genommen völlig glaubwürdig aus („alle fünf Trigger weichen ab") — **nur der verfehlte
Kontrollwert verriet, dass die Messung selbst kaputt war.** Ohne ihn hätten wir vier Trigger
„saniert", die nie ein Problem hatten.

### Muster: Cross-Engine-Normalisierung (die Falle dahinter)

> **Niemals zwei Werte vergleichen, die von zwei verschiedenen Engines normalisiert wurden.**

Die kaputte Query verglich die **live-Seite (von Postgres normalisiert)** gegen die **repo-Seite
(von Python normalisiert)**. Beide benutzten `\s+` — aber `\s` bedeutet nicht dasselbe:

| Engine | `\s` matcht |
|---|---|
| Python | ASCII-Whitespace **und Unicode-Whitespace** (U+00A0 usw.) |
| Postgres | `[[:space:]]` — **nur ASCII** |

Enthält der Text ein geschütztes Leerzeichen, kollabiert Python es mit, Postgres nicht. **Gleicher
Text, andere Länge, anderer MD5.** Lokal reproduziert: derselbe 8-Zeilen-Body ergibt 120 Zeichen
(Python) vs. 132 (Postgres).

**Und das ist hier kein Laborfall:** Die Trigger wurden per **Copy-Paste aus dem Chat** in den
SQL-Editor deployed — genau dabei entstehen unsichtbare Unicode-Leerzeichen in der Einrückung.

**Regel:** Beide Seiten eines Vergleichs durch **dieselbe** Engine schicken. Geht das nicht,
die Zeichenklasse **explizit** ausschreiben (`[ \t\n\r\f\v]`) statt `\s` zu vertrauen — und im
Zweifel vorher zählen, ob überhaupt Nicht-ASCII-Whitespace im Text steckt.

### `sql/` im main-Checkout ist eine geladene Waffe

> **Niemals einen ungepushten Arbeitsstand in `sql/` liegen lassen.**
> Work in Progress gehört nach `docs/wip/` oder in einen Branch.

**Grund:** Sebastian kopiert SQL **direkt aus `C:\repos\epkolar-app\sql\`** in den Supabase-Editor
und führt es aus. Was dort liegt, ist damit potenziell **live** — auch ein Entwurf, auch ein
halbfertiger Stand, auch eine Datei, die „nur zum Draufschauen" gedacht war. Zwischen „ich lege das
mal ab" und „das läuft auf der Produktionsdatenbank" liegt kein Gate.

Konkret passiert am 14.07.2026: `STEMPEL_TERMINAL_v2.sql` lag zwischen zwei Commits mit einem
**aktiven** `CREATE OR REPLACE guard_urlaub_edit()` in `sql/` — aufgebaut auf der unvollständigen
Rekonstruktion. Wäre sie in diesem Fenster ausgeführt worden, hätte sie ~800 Zeichen Live-Logik
gelöscht. (Sie wurde es nachweislich nicht — kein Repo-Body passt zum Live-Stand.)

**Praktisch heißt das:** Gefährliche Abschnitte werden **auskommentiert**, nicht „später noch
scharf gemacht". Eine Datei in `sql/` muss zu jedem Zeitpunkt gefahrlos ausführbar sein.

**Warum das eine harte Regel ist — 14.07.2026, um Haaresbreite:**
`sql/security_triggers_LIVE_v3911.sql` gab sich als Live-Stand von `guard_urlaub_edit()` aus. Der
Vergleich ergab: **Live 1746 Zeichen normalisiert, Repo-Datei 953.** Es fehlten ~800 Zeichen echter
Logik. Ein `CREATE OR REPLACE` auf dieser Basis (in `STEMPEL_TERMINAL_v2.sql` bereits vorbereitet)
hätte sie **kommentarlos gelöscht** — kein Fehler, kein Rollback, keine Warnung. Die
Urlaubs-Absicherung wäre still um Logik ärmer gewesen, die niemand mehr kennt.

Der Unterschied zum Boot-Crash desselben Tages: Den hätte ein Browser in fünf Sekunden gefunden.
**Diesen hier hätte nie jemand gefunden.**

## Hart nicht anfassen

- `_juprowaPush` / `_juprowaPull` / Juprowa Phase-1+2
- `parseTankBeleg` / `addTank` / Tank-Kontroll-Dialog / km-Sperre
- `_RLS_SILENT_DENIAL_LABELS`
- DB-Writes: **das Supabase-Plugin funktioniert und zeigt auf die RICHTIGE Org** (EP Kolar & Sohn, Projekt `jiggujpruejkaomgxarp`) — die alte Warnung "falsche Org" ist ueberholt (25.08.2026 belegt: `list_projects` zeigt genau dieses eine Projekt). Schreiben nur auf ausdrueckliche Anweisung, und dann mit: project_id vorab pruefen, idempotent, Wiederherstellungs-SQL im Migrations-Kommentar, Selbsttest mit Kontrollwerten (Rollen simulieren, BEGIN/ROLLBACK) und Vorher/Nachher-Beweis. **Juprowa bleibt tabu** (Sebastian 25.08.: "juprowa machen wir nichts, das funktioniert"). **OAuth-Link IMMER vorher testen — 28.08. viermal ins Leere gelaufen, weil ich es nicht tat.** Die client_id verfaellt nach wenigen Minuten; der Link ist dann tot, BEVOR ihn jemand anklickt, und der Nutzer sieht nur eine nichtssagende Seite. Erkennungsmerkmal:

```
curl -s -o /dev/null -w '%{http_code}' '<autorisierungs-url>'
  422  + {"message":"Unrecognized client_id"}  -> TOT, neu erzeugen
  303  + 'Redirecting to .../dashboard/authorize' -> LEBT, jetzt losschicken
curl -s -m 3 -o /dev/null -w '%{http_code}' http://localhost:<port>/callback
  400  -> der lokale Empfaenger laeuft (erwartet, ihm fehlen nur die Parameter)
  kein Ergebnis -> Empfaenger ist weg, Link ist wertlos
```

Wiederholtes `authenticate` liefert manchmal DIESELBE (tote) client_id — dann nochmal aufrufen, bis eine neue kommt, und wieder testen. Am besten den Link nicht zum Kopieren anbieten (er ist >700 Zeichen und bricht ab), sondern als `! powershell -c "Start-Process '<url>'"` zum Selbstausfuehren. Bricht die Weiterleitung danach mit einer Fehlerseite ab, ist die URL aus der Adresszeile trotzdem gueltig -> `complete_authentication`. SQ.push-DELETE/POST/PUT durch die App ist OK (das ist die normale Offline-Queue).
- Diagnose-Aufträge sind strikt read-only. Keine selbst-initiierten Fixes.
