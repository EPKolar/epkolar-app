# DATENVERLUST_BEFUND — Projektzuweisungen (Mitarbeiter ↔ Projekt)

**Auftrag:** nur messen und berichten. Dieser Lauf hat **nichts** am Code geaendert und
**keine** Datenbank angefasst. Er hat genau diese eine Datei angelegt.

**Messgrundlage und warum sie belastbar ist.** Gemessen wurde an `index.html`. Die Datei wird
gerade von einem zweiten Lauf bearbeitet, deshalb ist jede Messstelle dreifach gegengelesen:
Arbeitsbaum, `HEAD` (`32bd632`, v3.9.937) und die **oeffentlich ausgelieferte Fassung**. Die
ausgelieferte Datei ist bytegleich mit `HEAD`:

| Fassung | Groesse | MD5 |
|---|---|---|
| `git show HEAD:index.html` | 3 624 799 B | `59f2531f05f486acf2d9ca743c67c570` |
| `https://epkolar.github.io/epkolar-app/index.html` | 3 624 799 B | `59f2531f05f486acf2d9ca743c67c570` |
| `https://raw.githubusercontent.com/.../main/index.html` | 3 624 799 B | `59f2531f05f486acf2d9ca743c67c570` |

Alle 17 Belegzeichenketten (Anhang A) kommen im Arbeitsbaum **genau so oft** vor wie in `HEAD`,
also auch genau so oft wie in der Fassung, die heute bei den Leuten laeuft. **Was unten steht,
beschreibt den laufenden Stand, nicht einen Zwischenzustand.** Ziel-Datenbank laut ausgeliefertem
Buendel: `jiggujpruejkaomgxarp.supabase.co` (EP Kolar Baumgmt).

**Kein DB-Zugriff.** Jede Aussage ist unten als **GEMESSEN** (im Code oder in einer Datei gelesen),
**SCHLUSS** (Folgerung) oder **OFFEN** (ohne Blick in die laufende Datenbank nicht entscheidbar)
gekennzeichnet.

---

## 0. Kurzfassung in sechs Zeilen

1. Die betroffene Tabelle heisst **`public.worker_projects`**; eine Zeile ist eine Zuweisung.
2. Es gibt **genau eine Benutzerhandlung**, die dort schreibt: der Schiebeschalter unter
   „🏗️ Projektzuweisungen" im Mitarbeiter-Detail. Nur Rolle `admin` kann ihn bedienen.
3. Auf der Leitung werden daraus **drei Stationen**: ein Eintrag in die lokale Warteschlange,
   dann **ein DELETE, das ALLE Zuweisungen dieses Mitarbeiters loescht**, dann ein Einfuegen der
   Liste, die das eigene Geraet fuer richtig haelt. Kein Vergleich, keine Bedingung, keine Meldung.
4. Die Annahme des Auftrags trifft zu, und die Lage ist **schlechter als dort beschrieben**: das
   Zeitfenster ist nicht der 1,5-Sekunden-Abfluss, sondern die **ganze Sitzung**, weil die
   Zuweisungen heute nur **einmal pro App-Start** vom Server gelesen werden.
5. Ein Einzel-DELETE auf eine Zuweisung ist mit dem heutigen Schema und den heutigen RLS-Regeln
   **mit sehr hoher Sicherheit moeglich** — die Begruendung steht in Abschnitt c und ist
   zwingend, aber aus dem Code gefolgert, nicht in der Datenbank nachgesehen.
6. Ein verschwundener Haken ist **nachtraeglich nicht mehr sichtbar**. Es gibt kein Protokoll,
   keine Historie und keinen brauchbaren Zeitstempel. Der einzige Weg zurueck ist das
   herunterladbare Supabase-Tagesbackup, und das hat **sieben Tage** Vorhaltezeit.

---

## a) Welche Tabelle genau

**Name (GEMESSEN):** `public.worker_projects`. Der Weg dorthin ist im Code fest eingetragen:
die App-interne Adresse `worker-projects` wird in der Routentabelle auf die Datenbanktabelle
`worker_projects` abgebildet (Anker **A16**).

**Spalten, die der Code schreibt und liest (GEMESSEN):** genau drei.

| Spalte | Inhalt | woher belegt |
|---|---|---|
| `id` | Text, zusammengesetzt als `<worker_id>_<project_id>` | wird beim Einfuegen berechnet (**A3**) |
| `worker_id` | Text, Mitarbeiterkennung (`w1`…`w9`-Form) | Einfuegen (**A3**), Loeschfilter (**A2**), Leser (**A7**) |
| `project_id` | Text, Projektkennung | Einfuegen (**A3**), Leser (**A7**) |

Dass `worker_id` live die `w…`-Form traegt, ist **fremdgemessen und im Bestand notiert**:
`docs/BUG-VERFOLGUNG-v3998.md` haelt aus einer Live-Messung fest „`worker_projects` 29/29 wX" —
also 29 Zeilen, alle mit gueltiger Mitarbeiterkennung. Das ist eine **zweite Hand**, kein eigener
Messwert dieses Laufs.

**Weitere Spalten:** **OFFEN.** Gelesen wird mit `select=*` (**A11**), die App nimmt also alles
mit, was da ist, benutzt aber nur die drei oben. Ob die Tabelle zusaetzlich `created_at`,
`updated_at` oder weitere Spalten fuehrt, ist aus dem Code **nicht** entscheidbar. Im Repo gibt es
**kein** `CREATE TABLE worker_projects` und **kein** Schema-Dokument, das die Tabelle auffuehrt
(geprueft: `sql/`, `_archiv/sql/`, `SCHEMA_LIVE_25_04_2026.md`, `SCHEMA_LIVE_26_04_2026.md`,
`docs/`). Ein Verzeichnis `supabase/migrations/` **existiert in diesem Repo nicht** — unter
`supabase/` liegt nur `functions/`. Es gibt also im Bestand ueberhaupt keine
Migrationsgeschichte, gegen die man das Schema lesen koennte.

**Primaerschluessel:** **OFFEN, mit einem starken Indiz.** Der Code schickt seine Zeilen als
Upsert mit dem Zusatz `resolution=merge-duplicates` (**A12**). PostgREST uebersetzt das in ein
`ON CONFLICT … DO UPDATE` und braucht dafuer einen eindeutigen Schluessel; ohne einen solchen
wuerde jeder Speichervorgang mit einem Datenbankfehler abbrechen. Da das Speichern
funktioniert, **SCHLUSS:** es gibt einen eindeutigen Schluessel. **Welche Spalten** er umfasst
(`id` allein, oder `worker_id`+`project_id`) ist aus dem Code nicht ableitbar. Fuer den
Reparaturvorschlag ist das folgenlos, siehe Abschnitt c.

---

## b) Die Schreibstellen

Hier ist eine Korrektur am Auftragstext noetig. Der Auftrag spricht von „drei Schreibstellen".
**GEMESSEN gibt es genau EINE Stelle, an der ein Mensch etwas ausloest**, und daraus werden auf
der Leitung **drei Stationen**. Die dritte Nennung aus der Vorlage (`MERGE_ANALYSE.md`, Tabelle
in 3a) war die Liste der Stellen, die man beim Umbau **anfassen** muesste — und eine davon ist
ein **Leser**, keine Schreibstelle. Belegt mit drei unabhaengigen Zaehlungen:

* die Zeichenkette `worker_projects` kommt in der Datei **6×** vor: 1× Routentabelle, 2× im
  Lesezweig, 1× im Loeschbefehl, 1× im Einfuegebefehl, 1× in einem Kommentar;
* die Zeichenkette `worker-projects` kommt **9×** vor, davon **1×** als Schreibauftrag;
* eine vollstaendige Aufstellung **aller 188 Warteschlangen-Auftraege** im Code (Verfahren in
  Anhang B) enthaelt `/api/worker-projects/` **genau einmal**, als `PUT`.

Alle drei Zaehlungen kommen auf dasselbe Ergebnis. Waeren sie auseinandergelaufen, waere das der
Befund gewesen.

### Station 1 — die Benutzerhandlung

| | |
|---|---|
| **Komponente** | `MitarbeiterView` |
| **Handlung** | Mitarbeiter auswaehlen → Abschnitt „🏗️ Projektzuweisungen" → auf eine Projektzeile bzw. deren Schiebeschalter tippen. Die Liste zeigt eine Zeile je **aktivem** Projekt. |
| **Wer darf** | nur Rolle `admin`. `isWAdm = curUser.role==="admin"` — Projektleiter und Buero sehen den Schalter, koennen ihn aber nicht bedienen (**A17**). |
| **Anker** | **A8** (der Klick), **A1** (der Auftrag) |
| **Was passiert** | Der Haken wird im Bildschirm sofort umgelegt, die neue **Gesamtliste** `nxt` des Mitarbeiters wird gebildet, und **ein** Auftrag wird in die lokale Warteschlange gelegt. |
| **Auf der Leitung** | noch nichts. Der Auftrag liegt in IndexedDB (`syncQueue`) und lautet: `PUT /api/worker-projects/<mitarbeiter-id>`, Rumpf `{"projects":["<projekt-id>", …]}` — die **ganze** Liste, nicht die Aenderung. |

Zwei Einzelheiten, die spaeter wichtig werden:

* **Keine Zusammenfassung.** Jeder Tipper legt einen **eigenen** Auftrag ab; die Warteschlange
  fasst nichts zusammen. Fuenf Haken hintereinander sind fuenf Auftraege, jeder mit der jeweils
  aktuellen Gesamtliste. Der Abfluss startet nach **1500 ms** Ruhe neu (**A13**), fuehrt dann
  aber alle fuenf **nacheinander** aus — also fuenfmal loeschen-und-neu-einfuegen.
* **Der eigene Zwischenspeicher wird mitgeschrieben.** Dieselbe (verkuerzte) Liste wandert in den
  lokalen Bestand `monteurProjekte` (**A10**). Das Geraet, das den Verlust verursacht hat,
  zeigt danach genau das an, was es glaubt — nicht, was in der Datenbank steht.

### Station 2 — das Loeschen ALLER Zuweisungen dieses Mitarbeiters

| | |
|---|---|
| **Wo** | im Uebersetzer `_translateAndExec`, Zweig `worker-projects` (**A6**) |
| **Ausgeloest durch** | den Abfluss der Warteschlange (`doSync`), also 1,5 s nach dem letzten Tipper, beim Wiederverbinden, beim Fensterwechsel |
| **Anker** | **A2** |
| **Auf der Leitung** | `DELETE https://jiggujpruejkaomgxarp.supabase.co/rest/v1/worker_projects?worker_id=eq.<mitarbeiter-id>` · Kopfzeilen `apikey` + `Authorization: Bearer <JWT des angemeldeten Admins>` · **kein Rumpf** |

Das ist der Kern des Schadens. Der Filter lautet **`worker_id=eq.<mitarbeiter>`** — nicht
„die Zuweisung, die der Admin gerade abgewaehlt hat". Es werden **alle** Zeilen dieses
Mitarbeiters entfernt, gleich wer sie angelegt hat und gleich wie alt sie sind.

Bemerkenswert: der Aufruf fragt nicht nach, **wie viele** Zeilen er entfernt hat (kein
`Prefer: count=…`). Selbst wenn man wollte, koennte der Code hinterher nicht sagen, ob er gerade
eine fremde Zuweisung mitgenommen hat.

Schlaegt dieses Loeschen fehl, bricht der Code bewusst ab, bevor er einfuegt, mit der Meldung
`worker-projects: Alte Zuweisungen konnten nicht entfernt werden — Upsert abgebrochen um
Duplikate zu vermeiden.` (**A4**). Der Auftrag bleibt in der Warteschlange und wird nach dem
fuenften Fehlversuch verworfen — **mit** einem sichtbaren Hinweis und einem Eintrag in
`syncQueueFailed`. **Ein Fehlschlag ist also sichtbar. Der Datenverlust im Erfolgsfall ist es
nicht.**

### Station 3 — das Neu-Einfuegen der eigenen Liste

| | |
|---|---|
| **Wo** | derselbe Zweig, unmittelbar danach |
| **Anker** | **A3**, **A12** |
| **Auf der Leitung** | `POST …/rest/v1/worker_projects` · Kopfzeilen zusaetzlich `Content-Type: application/json` und `Prefer: return=representation,resolution=merge-duplicates` · Rumpf: eine Liste von Objekten `{"id":"<w>_<p>","worker_id":"<w>","project_id":"<p>"}`, **eines je Haken, den das eigene Geraet kennt** |

Ist die Liste leer (der Admin hat den letzten Haken entfernt), wird dieser Schritt
**uebersprungen** — dann ist der Vorgang ein reines Alles-Loeschen.

**Die beiden Aufrufe sind zwei getrennte HTTP-Anfragen, keine Transaktion.** Bricht das Netz
zwischen ihnen ab, sind alle Zuweisungen dieses Mitarbeiters weg und keine ist wieder da; der
Auftrag steht dann allerdings noch in der Warteschlange und wird beim naechsten Abfluss von vorn
gefahren, was den Stand wiederherstellt — **den Stand des eigenen Geraets**, nicht den der
Datenbank.

### Warum das Fenster nicht 1,5 Sekunden ist, sondern die ganze Sitzung

Die 1500 ms aus **A13** sind die Verzoegerung bis zum Abfluss — sie sagen nur, wann A's Wille
abgeschickt wird. Entscheidend ist, **wann A ueberhaupt erfahren kann, was B getan hat**, und
das ist **GEMESSEN**: die Zuweisungen werden aus dem Server **genau an einer Stelle** gelesen,
im Startladeeffekt (**A5**), und dieser Effekt haengt in der ausgelieferten Fassung an
`},[curUser]);` — er laeuft also **einmal pro App-Start bzw. Benutzerwechsel**. Es gibt keinen
Umlauf, keinen zweiten Leser, kein Nachladen beim Oeffnen des Mitarbeiter-Reiters.

Solange A die App offen hat, kommt B's Haken bei A **nie** an. Setzt A danach irgendeinen
eigenen Haken bei demselben Mitarbeiter, ist B's Haken endgueltig weg.

Verschaerfend, ebenfalls **GEMESSEN**: die Verschmelzung beim Start ersetzt die Liste **je
Mitarbeiter** und ueberspringt den ganzen Schritt, wenn der Server eine **leere** Antwort
schickt (**A14**, **A7**). Folge: Hat ein Mitarbeiter serverseitig gar keine Zuweisung mehr,
bleibt auf dem Geraet die **alte, im Zwischenspeicher liegende** Liste stehen — auch nach einem
Neustart. Der Verlust ist damit nicht nur unangekuendigt, er ist auf dem verursachenden Geraet
**unsichtbar**.

**Nachtrag zum Arbeitsbaum, NICHT LIVE:** der parallele Lauf baut gerade (v3.9.938, noch nicht
eingecheckt) einen Auffrischer, der genau diesen Startladeeffekt beim Zurueckkehren in das
Fenster erneut ausloest, hoechstens einmal pro 60 s und nicht waehrend des Tippens. Das
**verkuerzt** das Fenster von „ganze Sitzung" auf „bis zum naechsten Fensterwechsel". Es
**behebt den Verlust nicht**: das Ersetzen-durch-die-eigene-Liste bleibt unveraendert, und der
Schutz fuer noch nicht abgeflossene Aenderungen aus v3.9.847/848 deckt Projekte, Mitarbeiter,
Fahrzeuge und Arbeitsscheine ab — `monteurProjekte` **nicht**.

### Was der Verlust praktisch bedeutet

Die Zuweisung ist keine Zierde. **GEMESSEN** steuert `monteurProjekte` unter anderem, welche
Projekte ein Monteur ueberhaupt in seiner Projektliste sieht (**A15**), welche Projekte auf
seinem Einstiegsschirm erscheinen und welche Mitarbeiter im Projekt als zugewiesen gelten. Ein
verlorener Haken nimmt dem Monteur also den Zugang zum Projekt in der Oberflaeche.

---

## c) Erlauben die heutigen RLS-Regeln ein Einzel-DELETE?

**Antwort in einem Satz: Ja — ein Einzel-DELETE kann von denselben Regeln nicht verboten sein,
die das heutige Alles-Loeschen erlauben. Das ist aus dem Code zwingend gefolgert, nicht in der
Datenbank nachgesehen.**

### Die Begruendung

**GEMESSEN:** Die App spricht **direkt** mit PostgREST; es gibt keinen eigenen Server, der etwas
abfangen koennte. Jeder Aufruf traegt das JWT des angemeldeten Benutzers. RLS wirkt also voll.

**GEMESSEN:** Was heute gefahren wird, ist bereits ein **gefiltertes DELETE** auf derselben
Tabelle: `DELETE /worker_projects?worker_id=eq.<w>` (**A2**). Das ist derselbe SQL-Befehl
(`DELETE`) auf derselben Tabelle unter derselben Regel.

**SCHLUSS, und der Schritt ist zwingend:** Eine RLS-Regel fuer `DELETE` wird **je Zeile**
ausgewertet. Der Filter in der Adresse verkleinert nur die Menge der betroffenen Zeilen, er
aendert die Regel nicht. Die Zeilenmenge eines Einzel-DELETE
(`?worker_id=eq.<w>&project_id=eq.<p>`) ist eine **Teilmenge** der Menge, die das heutige
Alles-Loeschen schon entfernt. Was fuer die groessere Menge erlaubt ist, ist fuer jede Teilmenge
davon erlaubt. Dasselbe gilt fuer die Einfuegeseite: ein Einfuegen **einer** Zeile ist eine
Teilmenge des heutigen Einfuegens aller Zeilen.

**Kein Schemawechsel noetig.** Der Einzelbefehl braucht **nicht einmal** den Primaerschluessel:
`?worker_id=eq.<w>&project_id=eq.<p>` filtert auf zwei gewoehnliche Spalten, deren Existenz
oben belegt ist. Damit ist die offene Frage aus `MERGE_ANALYSE.md` („fuehrt `worker_projects`
den PK auf `id`?") fuer den Umbau **entschaerft**: die Antwort darf unbekannt bleiben.

### Was von dieser Aussage aus dem Code stammt — und was nicht

| Aussage | Einordnung |
|---|---|
| Die App schreibt direkt gegen PostgREST mit dem Benutzer-JWT | **GEMESSEN** (Anker A2, A3, A12 und die Kopfzeilen-Erzeugung) |
| Heute laeuft ein gefiltertes DELETE auf `worker_projects` | **GEMESSEN** (A2) |
| Ein Einzel-DELETE ist eine Teilmenge davon und damit erlaubt | **SCHLUSS** aus der Arbeitsweise von RLS, nicht gemessen |
| Dass das heutige Alles-Loeschen in der laufenden Datenbank **tatsaechlich** durchgeht | **SCHLUSS**, kein Beleg. Ginge es nicht durch, wuerde bei jedem Haken die Meldung aus **A4** erscheinen und der Auftrag nach fuenf Versuchen sichtbar verworfen. Da Zuweisungen funktionieren (29 Zeilen live, fremdgemessen), gehe ich davon aus. **Gemessen habe ich es nicht.** |
| Der genaue Wortlaut der Policies auf `worker_projects` | **OFFEN** |
| Ob auf `worker_projects` ein Trigger haengt, der ein Einzel-DELETE anders behandelt | **OFFEN**, aber kein Hinweis darauf. Die einzige Aufstellung von Live-Triggerkoerpern im Bestand (`docs/wip/trigger_bodies_LIVE_2026-07-14.csv`, fuenf Funktionen) nennt `worker_projects` nicht; der Loeschschutz `trg_workers_block_delete` haengt an `workers`, nicht hier. |

### Welche Dateien ich als Belege geprueft habe — und warum keine davon ein Beleg ist

Der Auftrag warnt zu Recht: eine Datei unter `sql/` sagt nichts darueber, was in der laufenden
Datenbank steht. Fuer `worker_projects` ist die Lage sogar **duenner** als das:

* **Es gibt im ganzen Repo kein `CREATE POLICY` fuer `worker_projects`.** Alle Treffer auf
  `worker_projects` in `sql/`, `docs/` und `_archiv/` sind entweder Fremdverweise (andere
  Tabellen pruefen per Unterabfrage, ob eine Zuweisung besteht), Kommentare, Vorpruefungs-Notizen
  oder Tabellen in Berichten.
* `sql/RLS_RECONCILE_v3.8.md` fuehrt `worker_projects` mit dem **Rollenmuster** „staff RW" und
  dem Urteil „OK". Das Dokument datiert auf **19.04.2026**, nennt als Grundlage eine Messung
  gegen Supabase und schreibt selbst, die realen Policy-Zahlen seien noch **von Sebastian
  nachzutragen**. Die dafuer vorgesehene Ausgabedatei `sql/RLS_RECONCILE_v3.8_OUTPUT.md`
  **existiert nicht**. Das Dokument nennt also die **Absicht**, nicht den Regeltext, und
  unterscheidet nicht zwischen SELECT, INSERT, UPDATE und DELETE.
* `docs/db/policies-backup-2026-07-15.json` ist ein echter Abzug aus der laufenden Datenbank und
  enthaelt `worker_projects` — aber nur die 63 **Kiosk-Sperren**, die am 15.07. gedroppt wurden,
  und alle davon sind `SELECT`. Ueber die schreibenden Regeln sagt der Abzug nichts.
* `sql/CLEANUP_2026-07.sql` zeigt beilaeufig: Sperren der Bauart `…_no_delete` wurden nur fuer
  `arbeitsscheine`, `projects`, `weekplan_rows` und `workers` angelegt — **nicht** fuer
  `worker_projects`.
* `supabase/migrations/` **existiert nicht**. Es gibt keine versionierte Schemageschichte.

### Der starke Nebenbeleg: dieselbe Bauform laeuft direkt daneben schon

**GEMESSEN:** Im **selben Bildschirm**, ein Panel weiter, liegen die **Kompetenzen**. Sie sind
dieselbe Art Beziehung (Mitarbeiter ↔ Schluessel) und arbeiten **bereits** zeilenweise:

* Haken setzen → `POST worker_kompetenzen` mit **einer** Zeile,
* Haken entfernen → `DELETE worker_kompetenzen?id=eq.<zeile>` (**A9**),
* Stufe aendern → `PATCH` auf **eine** Zeile,
* gelesen wird frisch je Mitarbeiter, nicht einmal beim Start.

`sql/RLS_RECONCILE_v3.8.md` fuehrt `worker_kompetenzen` mit **demselben** Rollenmuster
„staff RW" wie `worker_projects`. Dass dieses Panel im Betrieb funktioniert, ist ein sehr
handfester Hinweis darauf, dass ein Einzel-DELETE auf eine Mitarbeiter-Kindtabelle unter den
heutigen Regeln durchgeht. **Ein Beweis fuer `worker_projects` ist es nicht** — es sind zwei
Tabellen, und dass zwei Zeilen in derselben Dokumentenspalte stehen, ist keine Messung. Der
Punkt ist ein anderer und wichtiger: **die Bauform, die Punkt 3 einfuehren will, ist in dieser
App keine Neuerung, sondern existiert schon als funktionierende Vorlage.**

### Was ein Blick in die Datenbank noch klaeren muesste

Drei Fragen, jede mit einer einzigen Abfrage:

1. Welche Policies traegt `public.worker_projects`, je Befehl (`pg_policies`)? — schliesst die
   Beweisluecke aus dem Teilmengen-Argument.
2. Welche Spalten und welchen Primaerschluessel hat die Tabelle? — nur noetig, wenn man beim
   Einfuegen weiter mit `merge-duplicates` arbeiten will.
3. Haengt ein Trigger an der Tabelle? — erwartet: nein.

---

## d) Kommt dieselbe Bauform noch woanders vor?

**Ergebnis: die Form „ganzes Array senden → serverseitig ALLES loeschen → neu einfuegen"
existiert in dieser Anwendung genau EINMAL, bei `worker_projects`.**

Belegt mit vier unabhaengigen Abtastungen (Verfahren in Anhang B):

| Abtastung | Grundgesamtheit | Treffer auf die Bauform |
|---|---|---|
| alle `method:"DELETE"`-Aufrufe im Code | **51** | 4 sind direkte gefilterte Loeschungen, davon **1** mit anschliessendem Neu-Einfuegen |
| alle `_sbUpsert(...)`-Aufrufstellen | **13** | **1** mit vorangehendem Alles-Loeschen |
| alle Warteschlangen-Auftraege (`SQ.push`) | **188** (aus 192 Textfunden, 4 in Kommentaren) | **1** Route `/api/worker-projects/` (PUT) |
| Zeichenkette `worker_projects` / `worker-projects` | 6 / 9 | 1 Loeschen, 1 Einfuegen |

Die vier gefilterten Loeschungen ohne `id=eq.` im Einzelnen:

| Anker / Stelle | Was es loescht | Urteil |
|---|---|---|
| `worker_projects?worker_id=eq.` (**A2**) | alle Zuweisungen eines Mitarbeiters, danach Neu-Einfuegen | **der Befund** |
| `notifications?user_id=eq.` | alle Hinweise eines Benutzers | in Ordnung — das **ist** die Handlung „Alle loeschen", kein Neu-Einfuegen |
| `weekplan_rows?row_id=eq.` | genau eine Dispo-Zeile | in Ordnung, Einzelzeile |
| `entfernungszulage_tage?worker_id=eq.&datum=eq.` | genau ein Tag | in Ordnung, Einzelzeile |

Dazu der Helfer `_sbDeleteWhere`, mit **zwei** Aufrufern: die Loeschkaskade beim Loeschen eines
**Projekts** (gewollt, elf Kindtabellen) und eine einzelne Dispo-Sperre. Keiner davon fuegt
danach neu ein.

### Zwei verwandte Bauformen — anderer Mechanismus, gleicher Ausgang fuer den Benutzer

Diese fallen **nicht** unter „loeschen und neu einfuegen", verlieren aber nach demselben Muster
Daten, wenn zwei Leute gleichzeitig arbeiten. Sie gehoeren in die Liste, damit sie nicht spaeter
als neue Entdeckung auftauchen. **Nur gemeldet, nichts geaendert.**

**Form 2 — ganzes Array in EINER JSON-Spalte (Fahrzeuge).** Jede Einzelaenderung schreibt die
komplette Sammlung zurueck. Die Spalte ist gegen unbeteiligte Spalten geschuetzt, aber nicht
gegen sich selbst: zwei Eintraege von zwei Geraeten kurz hintereinander, einer verschwindet.
Anker: `const _schSync=u=>({schaeden:u.schaeden});` und daneben `_svcSync` (`serviceheft`),
`_vmSync` (`verbrauchsmaterial`), `_zulSync` (`zulassungsschein`); ebenso `termine`, `tankLog`,
`kmLog`. Ein Umbau kostet hier eine Schemaaenderung und ist **nicht** Teil von Punkt 3.

**Form 3 — ein ganzes Einstellungsobjekt in einer Schluessel/Wert-Zeile.** `system_config` mit
den Schluesseln `kv_rules` (an **drei** Stellen geschrieben), `stempel_pause_rules` und
`ticket_templates`. Wer zuletzt speichert, bestimmt den ganzen Block. Betrifft wenige, seltene
Bearbeiter; Anker: `_sbUpsert("system_config",{key:"kv_rules"`.

### Eine Stelle, die harmlos aussieht und es auch ist

Der Uebersetzer enthaelt weiterhin einen Zweig `weekplans` (POST), der eine **ganze Woche** als
ein JSON-Klotz schreibt. **GEMESSEN: dieser Zweig ist unerreichbar.** Die Zeichenkette
`/api/weekplans` kommt in der ganzen Datei **genau einmal** vor — in einem Kommentar, der es
selbst festhaelt („bleibt fuer Backward-Compat, wird nicht mehr aufgerufen"). Die vollstaendige
Routenaufstellung bestaetigt es: es gibt nur `/api/weekplan-rows`. Die Dispo hat den Umbau, um
den es bei den Zuweisungen geht, **bereits hinter sich** — eine Zeile je Dispo-Zeile, Upsert
nach `row_id`, Loeschen einzeln.

---

## e) Ist ein verlorener Haken rekonstruierbar?

**Nein. Nicht in der App, nicht aus der Tabelle, und nach sieben Tagen ueberhaupt nicht mehr.**

**Kein Aktivitaetslog fuer diesen Vorgang — GEMESSEN.** Es gibt eine Tabelle `activity_log`,
und die App schreibt auch hinein. Aber sie schreibt **acht** Ereignisarten, und keine davon ist
eine Datenaenderung: `login`, `js_error`, `promise_rejection`, `react_error`, `view_boundary`,
`juprowa_pull`, `juprowa_push`, `juprowa_push_fail`. Gemessen wurde das, indem **alle**
Vorkommen von `action:` mit festem Text in der Datei aufgesammelt wurden — die Liste ist
vollstaendig, nicht gestichprobt. Eine geaenderte Projektzuweisung hinterlaesst dort **nichts**.

**Keine Historie, kein Papierkorb — GEMESSEN.** Es gibt fuer `worker_projects` kein
Gegenstueck zu einer Verlaufstabelle, keinen `aktiv`/`geloescht`-Merker, keinen Zweitspeicher.
Die Zeile wird tatsaechlich entfernt.

**Zeitstempel helfen nicht — teils GEMESSEN, teils OFFEN.** Ob die Tabelle `created_at` oder
`updated_at` fuehrt, ist OFFEN (Abschnitt a). **Aber es ist gleichgueltig:** GEMESSEN ist, dass
die Zeilen bei **jedem** Speichervorgang erst geloescht und dann neu eingefuegt werden. Ein
`created_at` mit Vorgabewert `now()` wuerde dabei fuer **alle** Zuweisungen dieses Mitarbeiters
auf „jetzt" zuruecksetzen. Es koennte also weder zeigen, wann eine Zuweisung entstand, noch
dass eine verschwunden ist. Der Code selbst schickt **keine** Zeitstempel mit (**A3**).

**Kein Nebenschauplatz, aus dem man es ableiten koennte — SCHLUSS.** Die Zuweisung erscheint
nicht in Zeiteintraegen, Arbeitsscheinen oder der Dispo als eigene Spur; sie ist die
Voraussetzung fuer Sichtbarkeit, nicht ihr Nebenprodukt. Rueckschluesse waeren allenfalls
indirekt („der Monteur hat auf dem Projekt Stunden erfasst, also war er zugewiesen") und decken
den Regelfall nicht ab.

**Der einzige Weg zurueck — aus dem Bestand belegt.** `docs/handoffs/HANDOFF_2026-07-23.md`
haelt aus einem echten Datenverlust-Vorfall fest, was der Weg ist: **das herunterladbare
logische Tagesbackup** (Supabase Pro, Database → Backups, **7 Tage** Vorhaltezeit), daraus die
Zeilen greifen, gezieltes UPDATE. Ausdruecklich **nicht** PITR, weil ein Restore das ganze
Projekt zurueckdreht. Caveat aus derselben Datei: ist das PITR-Add-on aktiv, gibt es statt der
herunterladbaren logischen nur *physische* Backups ohne Download. Ob das Add-on aktiv ist, ist
**OFFEN**.

**Die bittere Pointe.** Damit man ein Backup holt, muss man **wissen**, dass etwas fehlt. Und
genau das erfaehrt niemand: das verursachende Geraet zeigt weiter seine eigene Liste (**A10**),
und der Startleser ersetzt eine leere Serverantwort nicht (**A14**). Der Monteur merkt es
daran, dass ein Projekt aus seiner Liste verschwunden ist — und wird vermutlich annehmen, es
sei abgeschlossen worden.

---

## Empfehlung

`worker-projects` auf Einzel-Zuweisungen umstellen: Haken setzen = ein `POST` mit **einer**
Zeile, Haken entfernen = ein `DELETE` auf **diese eine** Zeile ueber
`?worker_id=eq.<w>&project_id=eq.<p>`; das Alles-Loeschen (**A2**) entfaellt vollstaendig. Das
ist keine Erfindung, sondern die Bauform, die im Nachbarpanel derselben Ansicht bei den
Kompetenzen (**A9**) und in der Dispo bei `weekplan_rows` schon laeuft — und sie braucht
**keine** Schemaaenderung, weil der Einzelbefehl nur auf `worker_id` und `project_id` filtert,
deren Existenz belegt ist. Weil dieselbe Ansicht die Zuweisungen heute nur **einmal pro
App-Start** liest (**A5**), sollte im gleichen Zug der Auffrischer, den der parallele Lauf
gerade baut, auch die Zuweisungen mitziehen — sonst bleibt die Anzeige eine ganze Sitzung alt,
auch wenn kein Serverwert mehr kaputtgeht. Vor dem Bauen bitte **eine** Abfrage in der
laufenden Datenbank: die Policies auf `public.worker_projects` je Befehl — nicht weil ich einen
Hinderungsgrund erwarte, sondern weil das Teilmengen-Argument aus Abschnitt c eine Folgerung ist
und keine Messung.

---

## Kann Punkt 3 mit dem HEUTIGEN Schema und den HEUTIGEN RLS-Regeln gebaut werden?

**JA — mit einer klar benannten Einschraenkung.**

* **Schema: ja, gemessen.** Der Einzelbefehl braucht nur `worker_id` und `project_id`, und dass
  es diese Spalten gibt, ist aus dem laufenden Code belegt (**A2**, **A3**, **A7**). Keine neue
  Tabelle, keine neue Spalte, kein Umzug von Altdaten. Selbst die offene Frage nach dem
  Primaerschluessel muss nicht beantwortet werden.
* **RLS: ja, gefolgert und zwingend, aber nicht gemessen.** Die Zeilenmenge eines Einzel-DELETE
  ist eine echte Teilmenge der Menge, die das heutige Alles-Loeschen bereits entfernt, und eine
  DELETE-Regel wird je Zeile ausgewertet. Was fuer die groessere Menge erlaubt ist, ist fuer die
  Teilmenge erlaubt. Es gibt keinen Mechanismus in RLS, der das eine erlaubt und das andere
  verbietet.
* **Worauf sich die Einschraenkung bezieht.** Ich habe **keinen** DB-Zugriff. Damit ist
  ungemessen: der Regeltext selbst, und ob an der Tabelle ein Trigger haengt, der einen
  einzeiligen Befehl anders behandelt (kein Hinweis darauf; die einzige Live-Triggeraufstellung
  im Bestand nennt `worker_projects` nicht). Ebenfalls ungemessen ist die **Voraussetzung**
  meines Arguments, naemlich dass das heutige Alles-Loeschen in der laufenden Datenbank
  wirklich durchgeht.
* **Nicht „nicht entscheidbar".** Die Frage lautete ja / nein / nicht entscheidbar. Die Antwort
  ist **ja**, weil das Teilmengen-Argument aus einer **gemessenen** Codestelle folgt und nicht
  aus einer Vermutung ueber den Regeltext. Eine Abfrage (`pg_policies` auf
  `public.worker_projects`) macht aus dem Schluss eine Messung; sie ist Vorsicht, nicht ein
  fehlendes Glied.

---

## Anhang A — Belegzeichenketten

Zum Greppen, keine Zeilennummern: die Datei bewegt sich. Spalten „Arbeit" und „HEAD" sind die
Fundzahlen; da die ausgelieferte Fassung bytegleich mit `HEAD` ist, gilt die HEAD-Spalte auch
fuer den Live-Stand.

| # | Zeichenkette | Arbeit | HEAD | Was es belegt |
|---|---|---|---|---|
| A1 | `SQ.push({url:"/api/worker-projects/"+mid,method:"PUT",body:{projects:nxt}})` | 1 | 1 | der einzige Schreibauftrag, mit ganzem Array |
| A2 | `SB_REST+"/worker_projects?worker_id=eq."+encodeURIComponent(idOrSub)` | 1 | 1 | das Loeschen ALLER Zuweisungen |
| A3 | `const rows=projects.map(pid=>({id:idOrSub+"_"+pid,worker_id:idOrSub,project_id:pid}));` | 1 | 1 | Neu-Einfuegen, Spalten, kein Zeitstempel |
| A4 | `worker-projects: Alte Zuweisungen konnten nicht entfernt werden` | 1 | 1 | Abbruch bei Loeschfehler |
| A5 | `API.request("GET","/api/worker-projects")` | 1 | 1 | der einzige Leser, im Startladeeffekt |
| A6 | `if(resource==="worker-projects"&&idOrSub&&(method==="PUT"||method==="POST")){` | 1 | 1 | der Uebersetzerzweig |
| A7 | `const mpObj={};wpMap.forEach(wp=>{const wid=wp.worker_id;` | 1 | 1 | Verschmelzung beim Start, je Mitarbeiter |
| A8 | `onClick: ()=>{if(isWAdm)toggleProj(selM.id,p.id);}` | 1 | 1 | die Benutzerhandlung |
| A9 | `_api.delete('worker_kompetenzen',existing.id)` | 1 | 1 | die Einzelzeilen-Vorlage daneben |
| A10 | `ODB.save("monteurProjekte",monteurProjekte)` | 1 | 1 | die eigene Liste wird lokal festgeschrieben |
| A11 | `if(idOrSub) return _sbGet("worker_projects","worker_id=eq."+encodeURIComponent(idOrSub));` | 1 | 1 | Lesen mit `select=*` |
| A12 | `resolution=merge-duplicates` | 7 | 7 | Upsert-Kopfzeile, braucht einen eindeutigen Schluessel |
| A13 | `_batchDelay:1500` | 2 | 2 | Verzoegerung bis zum Abfluss (1× Code, 1× Changelog) |
| A14 | `if(wpMap&&Array.isArray(wpMap)&&wpMap.length){` | 1 | 1 | leere Serverantwort ersetzt nichts |
| A15 | `const _myProjIds=curUser.monteurId?((monteurProjekte||{})[curUser.monteurId]||[]):[];` | 1 | 1 | die Zuweisung steuert die Projektsicht |
| A16 | `"worker-projects":["worker-projects","worker_projects"],` | 1 | 1 | Adresse → Tabelle |
| A17 | `const isWAdm=curUser.role==="admin";` | 1 | 1 | nur Admins koennen zuweisen |

---

## Anhang B — wie gezaehlt wurde, und warum den Zahlen zu trauen ist

Die Datei ist 3,6 MB gross und enthaelt Code, Kommentare und Zeichenketten durcheinander. Ein
naiver Zaehler verrechnet sich hier nachweislich: ein `/*` in der Zeichenkette
`accept:"application/pdf,image/*"` wird nie geschlossen, und alles dahinter gilt dann als
Kommentar. Deshalb wurde durchgehend `scripts/code_scan.py` benutzt, das Code von Kommentar und
Zeichenkette trennt und **eine Eichprobe bestehen muss**, sonst die Auskunft verweigert. Die
Eichung ist in jedem Lauf dieses Berichts **bestanden** (22 von 22 erwarteten Deklarationen als
Code erkannt); ohne bestandene Eichung haette das Modul geworfen statt zu zaehlen.

Wo eine Aussage der Form „es gibt nur N" gemacht wird, wurde sie mit **mehreren unabhaengigen
Mustern** gefahren und die Zahlen verglichen (Abschnitte b und d). Sie stimmten jeweils
ueberein. Waeren sie auseinandergelaufen, waere **das** der Befund gewesen und nicht ein
Mittelwert.

Zusaetzlich gegengelesen: dass `sw.js` (der Dienstarbeiter, 115 kB) **keinen** eigenen
`worker_projects`-Pfad enthaelt (0 Treffer) — es gibt also keine zweite, abweichende Fassung
derselben Logik. `sw.js` fuehrt `CACHE_NAME = "epkolar-v3.9.937"`, passend zu
`APP_VERSION="3.9.937-supabase"`.

---

## Anhang C — Messliste: GEMESSEN / SCHLUSS / OFFEN

**GEMESSEN (im Code oder in einer Datei gelesen, Anker im Text, Arbeitsbaum = HEAD = Live-Datei):**
* Tabelle `worker_projects`; geschriebene und gelesene Spalten `id`, `worker_id`, `project_id`.
* Genau eine Benutzerhandlung schreibt dort (Schalter „Projektzuweisungen"), nur fuer `admin`.
* Der Rumpf ist die **ganze** Liste; die Warteschlange fasst nichts zusammen.
* Serverseitig: gefiltertes DELETE auf `worker_id`, danach Upsert der eigenen Liste; zwei
  getrennte HTTP-Anfragen, keine Transaktion; das DELETE fragt keine Zeilenzahl ab.
* Ist die neue Liste leer, entfaellt das Einfuegen.
* Die Zuweisungen werden **nur** im Startladeeffekt vom Server gelesen (`},[curUser]);` in der
  ausgelieferten Fassung); kein Umlauf, kein zweiter Leser.
* Die Verschmelzung beim Start ersetzt je Mitarbeiter und ueberspringt eine leere Serverantwort.
* Die eigene (verkuerzte) Liste wird lokal festgeschrieben.
* Die Zuweisung steuert, welche Projekte ein Monteur sieht.
* `activity_log` kennt genau acht Ereignisarten, keine davon eine Datenaenderung.
* Der Code schickt fuer `worker_projects` keine Zeitstempel.
* Genau **eine** Stelle in der Anwendung hat die Form Alles-Loeschen-dann-Einfuegen
  (vier unabhaengige Abtastungen, siehe Abschnitt d).
* Der `weekplans`-Zweig mit dem ganzen JSON-Klotz ist unerreichbar.
* `worker_kompetenzen` arbeitet bereits zeilenweise, im selben Bildschirm.
* `supabase/migrations/` existiert nicht; kein `CREATE POLICY` fuer `worker_projects` im Repo.
* Ein Fehlschlag des Schreibens ist sichtbar (Meldung, Verwerfen nach 5 Versuchen, Archiv
  `syncQueueFailed`); der Verlust im Erfolgsfall ist es nicht.
* `sw.js` enthaelt keinen eigenen `worker_projects`-Pfad.

**FREMDGEMESSEN (Live-Zahlen, die andere gemessen und im Bestand notiert haben — zweite Hand):**
* `worker_projects` hatte am 23.07.2026 **29** Zeilen, alle mit `w…`-Mitarbeiterkennung
  (`docs/BUG-VERFOLGUNG-v3998.md`).
* Der Rueckholweg bei Datenverlust in diesem Projekt ist das herunterladbare logische
  Tagesbackup, 7 Tage (`docs/handoffs/HANDOFF_2026-07-23.md`).
* Rollenmuster „staff RW" fuer `worker_projects` und `worker_kompetenzen`, Stand 19.04.2026
  (`sql/RLS_RECONCILE_v3.8.md`) — eine Absicht, kein Regeltext.

**SCHLUSS (Folgerung, nicht selbst beobachtet):**
* Dass ein Einzel-DELETE von denselben Regeln erlaubt ist wie das heutige Alles-Loeschen
  (Teilmengen-Argument).
* Dass das heutige Alles-Loeschen in der laufenden Datenbank durchgeht (sonst waere jede
  Zuweisungsaenderung sichtbar gescheitert).
* Dass ein eindeutiger Schluessel auf der Tabelle existiert (weil `merge-duplicates` sonst
  fehlschlagen wuerde).
* Dass ein etwaiges `created_at` als Beweismittel unbrauchbar waere (weil bei jedem Speichern
  neu eingefuegt wird).
* Dass es keinen indirekten Fundort gibt, aus dem eine verschwundene Zuweisung ablesbar waere.

**OFFEN — ohne Blick in die laufende Datenbank nicht entscheidbar:**
* Der Wortlaut der RLS-Policies auf `public.worker_projects`, je Befehl.
* Die vollstaendige Spaltenliste und der Primaerschluessel der Tabelle.
* Ob an `worker_projects` ein Trigger haengt.
* Ob das PITR-Add-on aktiv ist (entscheidet, ob es herunterladbare logische Tagesbackups gibt).
* Wie viele Konten die Rolle `admin` tragen — also wie viele Personen ueberhaupt kollidieren
  koennen.

**Zum Schluss, weil es in diesem Bestand teuer erkauft ist:** dieser Bericht hat den Live-Stand
**des Codes** nachgemessen (bytegleich, MD5 oben) — aber **nicht** den Live-Stand der
**Datenbank**. Fuer alles, was in der Datenbank steht, gilt weiterhin: erst belegt, wenn dort
nachgemessen.
