# Die drei Kiosk-Anzeigen — `#planung`, `#monteure`, `#stempel`

**Was zeigen sie an, wenn die Daten fehlen, veraltet sind oder die Verbindung
weg ist — und merkt das jemand?**

Diese Anzeigen hängen an der Wand und werden von niemandem bedient. Was dort
falsch steht, fällt keinem Nutzer auf, der es melden könnte. Gemessen wurde
deshalb nicht, ob sie *funktionieren*, sondern ob sie **lügen, wenn sie
ausfallen**.

---

## 0. UMFANG DIESER MESSUNG — und was sie NICHT abdeckt

| Was | Wert |
| --- | --- |
| Gemessene Datei | `C:\repos\epkolar-app\index.html`, Arbeitsbaum |
| Stand | `APP_VERSION="3.9.997-supabase"`, `origin/main = 44d52bf`, 30 430 Zeilen |
| Gemessene Ansichten | **alle drei**: `#planung` (`WochenplanTafel`), `#monteure` (`MonteurTafel`), `#stempel` (`StempelTafel`) |
| Gemessene Rollen | `admin` (Vorschau), `lager_display` (Wandpanel), `stempel_terminal` (Panel am Werkstor) |
| Gemessene Netzlagen | `aus` (Abruf abgebrochen), `leer` (HTTP 200 + `[]`), `403` (Rechte fehlen) |
| Gemessene Größen | 1920×1080 (TV), 1280×800 (EDATEC-Panel), 1920×380 (Streckungsprobe) |
| Aufnahmen gesamt | **30** Läufe am Schirm (19 `admin`, 8 `lager_display`, 3 `stempel_terminal`) + 1 Zeitreise über 40 Minuten |
| Werkzeuge | `scripts/kiosk_tafeln_quelltext.py`, `scripts/kiosk_tafeln_live.py`, `scripts/kiosk_tafeln_mutationsprobe.py` |
| Rohdaten | `docs/befunde/KIOSK_QUELLTEXT.json`, `docs/befunde/KIOSK_LIVE.json` |

### 🔴 ZEILENNUMMERN SIND HINWEISE, KEINE ADRESSEN

Alle Zeilennummern in diesem Papier gelten für den gemessenen Stand:
`origin/main = 44d52bf`, **30 430 Zeilen**, `md5(index.html) =
3538f7ec726ce22053e5649d00adf2d1`.

**Die Datei hat sich noch während der Niederschrift bewegt.** Ein anderer
Vorgang hat für v3.9.998 bei Zeile 2656 einen Block eingefügt (`_sqDropName`,
20 Zeilen ein, 1 aus). Damit ist **alles unterhalb von 2656 um +19 Zeilen
verschoben**: `WochenplanTafel` steht jetzt bei 7373 statt bei 7354, die
Datei hat 30 449 Zeilen. An `index.html` wurde von mir dabei nichts geändert
— der Nachweis steht in Abschnitt 9.

Damit die Befunde auch morgen noch auffindbar sind, trägt jeder einen
**Suchbegriff**. `grep -n` findet die Stelle unabhängig von der Nummer:

| Befund | Suchbegriff (`grep -n -F … index.html`) |
| --- | --- |
| B1 Leerzweig `#planung` | `Keine Wochenplan-Zeilen` |
| B1 Lieferant kehrt stumm um | `_rlsLeer(wprs)` |
| B2 Abwesenheiten-Auffangzweig | `[wp-abs]` |
| B3 hartkodierte Belegschaft | `const [monteure,setMonteure]` bzw. `const MONT=` |
| B3/B7 Startabruf | `_kioskFieldWorkers().catch(()=>null)` |
| B4 der Uhr-Takt | `setInterval(()=>setStand(new Date()),60000)` |
| B4 die Anzeige | `Stand '+_pad(stand.getHours` |
| B5 die `!important`-Regel | `input,select,textarea{font-size:14px !important}` |
| B5 das UID-Feld | `UID (Test ohne Reader)` |
| B5 die Datumsfelder | `type:'date',value:aVon` |
| B6 das Kiosk-Tor | `const _canKiosk=` |
| B8 die drei Fehlertexte | `Keine Verbindung — Mitarbeiterliste` |
| B9 das Terminal lädt nichts | `if(props.terminal){return` |
| B9 der SQL-Fehlertext | `stempel_log — SQL` |
| B10 die Altersangabe | `Daten von "+_pad` |
| B11 die Fußzeile | `read-only · aktualisiert` |

Beide Messwerkzeuge finden ihre Bereiche über
`re.search(r"function\s+<Name>\s*\(props\)\s*\{")` und rechnen die
Zeilennummern jedes Mal neu aus — sie gehen also nicht kaputt, wenn die
Datei wächst. Ein erneuter Lauf nennt die dann gültigen Nummern.

**Zwischenstand-Hinweis:** Die Werkzeuge liefen zuerst gegen v3.9.996; der
Arbeitsbaum ist während des Laufs auf v3.9.997 gewechselt. **Beide Werkzeuge
wurden danach vollständig neu gefahren**; alle Zahlen in diesem Papier
stammen aus dem Lauf gegen v3.9.997. Der Quelltext-Lauf ergab dabei **exakt
dieselben Zahlen** wie gegen v3.9.996 — v3.9.997 hat keine der drei Tafeln
berührt.

### 🔴 Was LEERZUSTAND.json NICHT erfasst hat — die Antwort auf die Vorfrage

`docs/befunde/LEERZUSTAND.json` deckt **15 Ansichten** ab (`home`, `as_liste`,
`werkzeuge`, `fahrzeuge`, `mitarbeiter`, `zeit`, `planung`, `auswertungen`,
`monatsabr`, `chef`, `einstell`, `abwesend`, `flotte`, `buero`, `gefahr`) —
**und KEINE davon ist eine Kiosk-Ansicht.**

Das ist belegbar und nicht vermutet:

* Der Lauf setzt `u.role='admin'` (`scripts/b3_vier_ansichten_messen.py:1095`)
  und navigiert über die **Navigationsknöpfe** (`_navigieren` →
  `NAV_TOP_JS`/`NAV_MEHR_JS`) — ohne `?screen=`, ohne `#hash`.
* Das Kiosk-Tor lautet
  `const _canKiosk=_isLagerDisplay||_isStempelTerminal||(curUser.role==='admin'&&!!_kioskScreen);`
  (`index.html:9602`). Ohne `?screen=` und ohne Kiosk-Rolle ist `_canKiosk`
  **falsch** — die drei Tafeln werden in jenem Lauf nie erzeugt.
* Der Eintrag `planung` in LEERZUSTAND.json ist folglich die **normale**
  Wochenplanung (`WeekPlan`, `index.html:21402`), **nicht** die
  `WochenplanTafel` (`index.html:7354`).

Dasselbe gilt für die Schriftmessung: `docs/befunde/WIRKUNG_SCHRIFT.json`
enthält genau **vier** Kürzel (`as_liste`, `fahrzeuge`, `home`, `planung`) —
wieder die normale Ansicht. **Der Schriftboden ist für die Kiosk-Ansichten
nie gemessen worden.** Dieses Papier ist die erste Messung an ihnen.

### Was ich NICHT messen konnte

1. **Die echte Datenbank.** Keine DB-Zugriffe (Nicht-Ziel). Ob
   `lager_display` die Tabelle `weekplan_rows` überhaupt lesen *darf*, ist
   hier **nicht** geprüft. Der 403-Modus stellt diesen Fall nach, er belegt
   ihn nicht.
2. **Eine echte Anmeldung.** Die Rollen wurden über `localStorage`
   (`epkolar_user.role`) gesetzt — das ist der Weg, den auch `_canKiosk`
   liest (`public.users.role`, ausdrücklich **nicht** ein JWT-Anspruch,
   Kommentar bei `index.html:9596`). Serverseitige RLS-Wirkung ist damit
   **nicht** mitgemessen.
3. **Die Antrags-Schirme des Stempel-Terminals** (Urlaub/Zeitausgleich,
   `amode='typ'/'datum'/'confirm'`). Sie sind erst nach einem gültigen
   Chip-Scan erreichbar; ohne Worker-Datensatz mit `nfc_uid` führt kein Weg
   dorthin. Die Datumsfelder dort sind darum nur **über die CSS-Regel**
   beurteilt, nicht am gerenderten Feld (siehe B5).
4. **Ein VOLLES Brett.** Alle Aufnahmen zeigen die Tafeln mit **null**
   Datenzeilen. Die Auto-Streckung (`transform:scale`) läuft damit an ihre
   **obere** Klemme; bei vollem Brett läuft sie an die untere. Ersatzweise
   gemessen über eine kleinere Fensterhöhe — im Bruch `wh/ch` dieselbe
   Rechnung (siehe Abschnitt 5). Das ist ein **Ersatz**, keine Aufnahme
   einer vollen Woche.
5. **Farbsehschwäche, Blickwinkel, Entfernung.** Gemessen sind
   WCAG-Kontrastverhältnisse und Pixelgrößen, nicht die Lesbarkeit aus 6 m.

---

## 1. Wie die drei Ansichten überhaupt erreicht werden

`_kioskScreenPick(hash, query, session)` (`index.html:3271`) löst die Ansicht
in der Reihenfolge **Hash → Query → sessionStorage** auf und schreibt das
Ergebnis nach `window.__kioskScreen` (`3291`). Das Tor daneben tut das
**nicht**:

```js
// index.html:9593
const _kioskScreen=(()=>{try{return new URLSearchParams(location.search).get('screen');}catch(_){return null;}})();
// index.html:9602
const _canKiosk=_isLagerDisplay||_isStempelTerminal||(curUser.role==='admin'&&!!_kioskScreen);
```

`_canKiosk` liest **nur `location.search`**. Der Hash, den `_kioskScreenPick`
zwei Absätze weiter oben sauber aufgelöst hat, kommt im Tor nicht vor.

**Gemessen** (`kiosk_tafeln_live.py`, Lauf `admin / planung / leer / nur hash`):

| Weg | Rolle | Was erscheint | Textlänge |
| --- | --- | --- | --- |
| `?screen=planung#planung` | admin | die Wochenplan-Tafel | 346 Zeichen |
| `#planung` allein | admin | **die ganze normale App** mit Kopfzeile, 17 Reitern und Offline-Banner | 2 610 Zeichen |
| `#planung` allein | lager_display | die Wochenplan-Tafel | 346 Zeichen |

> **B6 🟡 — `#planung` allein öffnet für einen Admin den Kiosk nicht.**
> **Stelle:** `index.html:9593` und `9602`.
> **Auslöser:** Ein Admin ruft die im Auftrag genannte Adresse `…/#planung`
> auf, statt `…?screen=planung`.
> **Folge:** Er sieht die normale App und hält den Kiosk für kaputt — oder,
> schlimmer, er prüft den Kiosk „nachgesehen, sieht normal aus" und hat in
> Wahrheit nie hingesehen. Am Wandpanel (`lager_display`) wirkt der Hash,
> dort ist der Fehler unsichtbar.
> **Wie gemessen:** derselbe Schirm, derselbe Netzmodus, nur der Weg
> geändert — zwei Aufnahmen, 346 gegen 2 610 Zeichen Text.

**Und eine Rollen-Besonderheit, die jede Messung verfälscht, die sie
übersieht:** Unter `admin` laufen die Daten über `API.getWorkers()` /
`API.request(...)`; die Kiosk-Marken `window.__kioskAsErr` und
`window.__kioskFzErr` werden dabei **nie gesetzt** (gemessen: `(nie gesetzt)`
in allen 18 Admin-Läufen). Erst unter `lager_display` gehen dieselben
Ansichten über die `kiosk_*`-RPCs, und erst dort tragen die Marken einen
Wert. **Wer nur die Admin-Vorschau misst, misst die Fehlermeldung an einem
Pfad, auf dem es sie gar nicht gibt.**

---

## 2. Die Datenwege je Ansicht — und was bei einem Fehlschlag passiert

Gemessen mit `scripts/kiosk_tafeln_quelltext.py` (Codetrennung über das
geeichte `code_scan.ist_code`, Eichung an index.html: **21 von 21**).

| | `#planung` WochenplanTafel | `#monteure` MonteurTafel | `#stempel` StempelTafel |
| --- | --- | --- | --- |
| Zeilen | 7354–7451 (14 305 B) | 7858–8015 (19 494 B) | 7462–7856 (31 349 B) |
| Abrufe im Rumpf | 1 (`fetch` Z.7366) | 1 (Z.7872) | 3 `fetch` + `_stLoadPauseRules` + `_sbPatch` |
| RPC im Rumpf | `kiosk_week_absences` | — | `stempel_terminal_workers`, `stempel_terminal_stempel` |
| `catch` gesamt | 5 | 5 | 9 |
| davon **leerer Rumpf** | **3** (Z.7365, 7368, 7368 — Auto-Streckung und WakeLock, ohne Anzeigefolge) | **3** (Z.7866, 7884, 7888) | **5** (Z.7534, 7534, 7538, **7573**, 7652) |
| `_rlsLeer` / `__rlsFehler` / `__EP_RLS` | **0** | **0** | **0** |
| Stand-Takt | Z.7367, **ohne** Erfolgsprüfung | Z.7872, **mit** (`Array.isArray`) | keiner |

> Ein leerer `catch` ist ein **Verdacht, kein Urteil** — nachgelesen wurde
> jeder. Drei der fünf in der StempelTafel (7534, 7534, 7538) sind
> WakeLock-/Timer-Aufräumer ohne Anzeigefolge, und 7652 (`/* Netz/RPC weg */`)
> wird direkt danach von `if(!_rpcOk||!_res){_showFb({kind:'error'})}`
> abgefangen — das ist kein Schlucken. **7573 ist einer:**
> `try{const rl=await _stLoadPauseRules();…}catch(_e){}` — schlägt das
> Laden der Pausenregeln fehl, gilt still `STEMPEL_PAUSE_FALLBACK`, ohne
> ein Wort.

### Die Daten kommen überwiegend gar nicht aus den Tafeln

Der eigentliche Inhalt von `#planung` und `#monteure` kommt als **Prop** aus
der App (`index.html:9609`):

```js
React.createElement(WochenplanTafel,{wpHistory:wpHistory,monteure:monteure,fahrzeuge:fahrzeuge,abs:abs,onLogout:logout})
```

Und dort gilt, im Code nachgezählt:

| Feld | Woher | Wie oft nachgeladen | Bei Fehlschlag |
| --- | --- | --- | --- |
| `wpHistory` (die Wochenzeilen) | `_loadWeekplansFromRows` (8079) | **alle 30 s**, nur wenn sichtbar (9367) | `if(!Array.isArray(wprs))return;` und `if(_rlsLeer(wprs))return;` → alter Stand bleibt, **stumm** |
| `monteure` (die Namen) | Boot-`Promise.all` (8507) | **nie wieder** — genau ein Aufrufer von `_kioskFieldWorkers(` in der ganzen Datei | `.catch(()=>null)` → `setMonteure` wird nie gerufen |
| `fahrzeuge` | Boot (8515) | **nie wieder** — ein Aufrufer von `_loadKioskFahrzeuge(` | `__kioskFzErr` gesetzt, Liste bleibt leer |
| `absRows` (Kranken-/Urlaub-/ZA-Zeilen) | eigener Takt im Bauteil (7366) | alle 60 s | `catch → console.warn`, **stumm** |
| `arbeitsscheine` (`#monteure`) | eigener Takt (7872) | alle 60 s | `__kioskAsErr` gesetzt **und gezeigt** |

`props.abs` wird übergeben (`9609`) und im Rumpf von `WochenplanTafel`
**nirgends gelesen** — die Tafel holt ihre Abwesenheiten selbst. Ein toter
Durchgang, ohne Folge (⚪).

> **B3 🔴 — Fällt der Start-Abruf aus, zeigt die Wand eine hartkodierte
> Belegschaft von 2018.**
> **Stelle:** `index.html:8150` (`const [monteure,setMonteure]=_react.useState.call(void 0, MONT)`),
> Konstante `MONT` bei `index.html:3721`, Ladeweg `index.html:8507`
> (`_kioskFieldWorkers().catch(()=>null)`).
> **Auslöser:** Netz weg **oder** 403 beim Start des Panels — und das Panel
> startet nach jedem Versionswechsel und täglich um 03:00 Wien neu
> (`_kioskDailyTick`, `index.html:3355`, aufgerufen im Poll bei `8373`).
> **Folge:** `setMonteure` wird nie gerufen, der Anfangswert bleibt stehen.
> Die Monteur-Tafel zeigt dann **„Barger · Cracana · Paschinger · Schmid"**
> mitsamt Rollen — vier Namen aus einer Konstanten mit Eintrittsdaten von
> 2018, ohne jeden Hinweis, dass das kein Ist-Stand ist. Wer heute ein- oder
> ausgetreten ist, steht nicht drin bzw. steht noch drin.
> Nebenbei umgeht das die DSGVO-Vorkehrung: die RPC `kiosk_field_workers`
> gibt bewusst nur Minimalfelder zurück, `MONT` trägt `gebDat`, `fsNr`,
> `eintritt`.
> **Wie gemessen:** 6 Aufnahmen (`lager_display`/`admin` × `aus`/`leer`/`403`)
> — in **allen sechs** stehen dieselben vier Namen im gerenderten Text
> (`KIOSK_LIVE.json`, Feld `text`).

> **B7 🟡 — Namen und Fahrzeuge werden nach dem Start nie wieder geholt.**
> **Stelle:** je genau ein Aufrufer, `index.html:8507` und `8515`; die
> 60-s-Umfrage `pollForChanges` (`9274`) holt ausschließlich `defects` und
> `absences` und ruft weder `setMonteure` noch `setFahrzeuge`.
> **Folge:** Ein neuer Mitarbeiter oder ein umgemeldetes Fahrzeug erscheint
> auf der Wandtafel erst beim nächsten Neuladen — also beim nächsten
> Versionssprung oder um 03:00. Bis zu **24 Stunden** Versatz, ohne Hinweis.
> **Wie gemessen:** Zählung der Aufrufstellen im Code (nicht im Rohtext) mit
> `code_scan`; `scripts/kiosk_tafeln_quelltext.py` weist die Leseaufrufe je
> Bauteil aus, die App-Stellen sind einzeln nachgeschlagen.

---

## 3. Leerzustand gegen Fehlerzustand — die Kernfrage

In diesem Haus kommt ein abgewiesener Lesezugriff als **HTTP 200 mit leerem
Array** beim Aufrufer an. Dafür gibt es `window.__EP_RLS` (`index.html:1643`)
und das Array-Merkmal `__rlsFehler` (`1647`, `2197`, `2206`, `2337`).
**Keine der drei Tafeln sieht eine dieser Marken an — gemessen: 0 Vorkommen
in allen drei Rümpfen.**

Am Schirm, Rolle `lager_display`, 1920×1080 — was tatsächlich im Kopf steht:

| Ansicht | `leer` (200 + `[]`) | `403` (abgewiesen) | `aus` (kein Netz) |
| --- | --- | --- | --- |
| `#planung` | `Stand HH:MM` · `v3.9.997 · FZ:0 · Spez:0` | `Stand HH:MM` · `v… · FZ:Fehler(other)` | `Stand HH:MM` · `v… · FZ:Fehler(net)` |
| Textlänge | 346 | **349** | **347** |
| `window.__EP_RLS` | 0 Einträge | **11 Einträge** | 0 |
| `#monteure` | `Daten von HH:MM` | `Daten von …` · `⚠️ AS:Fehler(HTTP403)` | `… ⚠️ AS:Fehler(net)` |
| Textlänge | 245 | 267 | 263 |
| `#stempel` (Rolle `stempel_terminal`) | kein Hinweis | kein Hinweis | kein Hinweis |
| Textlänge | 113 | 113 | 113 |
| `#stempel` (Rolle `admin`, Vorschau) | kein Hinweis | `⚠ Mitarbeiterliste konnte nicht geladen werden` | `⚠ Keine Verbindung — Mitarbeiterliste konnte nicht geladen werden` |

> **B1 🔴🔴 — `#planung` sagt bei einem abgewiesenen Lesezugriff auf den
> Wochenplan NICHTS, obwohl die App es weiß.**
> **Stelle:** `index.html:7438` — der Leerzweig lautet
> `:h('tr',{},h('td',{colSpan:8,…},"Keine Wochenplan-Zeilen für KW "+kw))`.
> Der Lieferant `_loadWeekplansFromRows` (`8079`) fragt bei `8095`
> ausdrücklich `if(_rlsLeer(wprs))return;` — er **kennt** den Rechtefehler
> und kehrt stumm um, ohne den Zustand zu ändern und ohne ihn zu melden.
> **Auslöser:** eine Policy auf `weekplan_rows`, die `lager_display` nicht
> durchlässt — oder ein ausgelaufenes Token.
> **Folge:** Auf dem Schirm steht **„Keine Wochenplan-Zeilen für KW 40"** —
> **wortgleich** mit dem Fall, dass für diese Woche wirklich nichts geplant
> ist. Gemessen sind die beiden Texte bis auf drei Zeichen identisch (346
> gegen 349); die drei Zeichen stecken in der Fahrzeug-Diagnose, also in
> einer Aussage über **Fahrzeuge**, nicht über den Wochenplan. Zugleich
> liegen in `window.__EP_RLS` **11 Einträge** — die Kenntnis ist im Browser
> vorhanden und wird nicht angezeigt. Die halbe Firma liest an der Wand ab,
> heute sei nichts zu tun.
> **Wie gemessen:** `scripts/kiosk_tafeln_live.py`, 3 Netzmodi × 2 Rollen,
> gerenderter `innerText` des `#root` plus `window.__EP_RLS.length`; der
> Hinweis-Melder kennt vier Formen (`⚠`, `Fehler`, `nicht aktualisiert`,
> `Keine Verbindung`) und hat alle vier an einem eingesetzten Köder
> angeschlagen.

> **B2 🔴 — Die Zeilen Krankenstand / Urlaub / Zeitausgleich sind bei
> Ausfall leer und behaupten damit „niemand fehlt".**
> **Stelle:** `index.html:7366` — der Abruf `kiosk_week_absences` endet in
> `catch(e){console.warn('[wp-abs]',e&&e.message||e);}`. `absRows` bleibt auf
> seinem alten Wert (beim Start: `[]`).
> **Auslöser:** derselbe wie B1, zusätzlich jeder 60-s-Takt, der scheitert.
> **Folge:** Die drei Zeilen `🤒 Krankenstand`, `🏖️ Urlaub`,
> `⏰ Zeitausgleich` bleiben leer. Eine leere Krankenstandszeile liest sich
> als Aussage („heute ist niemand krank"), nicht als Lücke. Die Einteilung
> am nächsten Morgen hängt daran.
> **Wie gemessen:** in **allen 9** `#planung`-Aufnahmen stehen die drei
> Zeilen ohne einen einzigen Namen, in `leer` wie in `403` wie in `aus` —
> und ohne jeden Hinweis daneben.

> **B8 ✅ — `#stempel` unterscheidet sauber, und zwar in beide Richtungen.**
>
> 🔴 **NACHTRAG 01.10.2026 — ich habe diesen Befund am 30.09.
> abends WIEDER AUFGEMACHT, und das war falsch.** Mein Beleg: unter der
> echten Rolle `stempel_terminal` lieferten alle drei Netzlagen denselben
> Text mit 113 Zeichen — kein Unterschied zwischen „keine
> Verbindung“, „leer“ und „abgewiesen“. Daraus habe ich
> geschlossen, die Unterscheidung gelte nur in der Vorschau-Rolle `admin`.
>
> **Die Messung stimmt, die Schlussfolgerung nicht.** Das ECHTE Terminal
> (`props.terminal`) laedt beim Start bauartbedingt KEINE Liste —
> `if(props.terminal){return ...}`, begruendet bei v3.9.769: der Stempelweg
> schickt die rohe `nfc_uid` an eine DEFINER-RPC, die den Mitarbeiter selbst
> nachschlaegt. Ein anon-Panel am Werkstor duerfte die Liste gar nicht lesen
> und soll keine Sozialversicherungsnummern im Speicher halten.
>
> Mein Pruefstand hat also die ANTWORTEN AUF LESEZUGRIFFE veraendert, und
> das echte Terminal macht beim Start keine. **Es gab dort nichts zu
> unterscheiden** — die drei gleichen Texte sind richtig, nicht blind.
> Die Lehre ist nicht „die Rolle ist ein anderer Datenweg“ (das bleibt
> wahr), sondern: **eine Messung an einem Weg, den es nicht gibt, belegt
> nichts.** Ich habe aus einer leeren Grundgesamtheit geschlossen.
>
> Der Weg, der hier wirklich zaehlt, ist der SCAN — und der ist seit
> v3.9.699 ausdruecklich gegen genau diese Krankheit gehaertet: der
> Richtungs-Leser WIRFT bei 401/403, statt ein leeres Array zu liefern.
> Sonst saehe eine Abweisung aus wie „heute kein Stempel“, jeder Scan
> wuerde als „kommen“ gebucht, und der ganze Tag zaehlte null Stunden
> — mit gruenem Haekchen. Der Abbruch meldet getrennt nach Netz, Trigger
> und Sonstigem, je mit eigenem Text. **B8 bleibt erledigt.**
> Kein Befund, steht hier, damit niemand zweimal sucht. `StempelTafel` führt
> einen eigenen Zustand `tblErr` (`7469`) mit drei getrennten Texten nach
> `_stErrKind` (`7569`–`7571`): `missing` → „RPC … fehlt", `net` → „Keine
> Verbindung — Mitarbeiterliste konnte nicht geladen werden", sonst
> „Mitarbeiterliste konnte nicht geladen werden". Gemessen: drei
> **verschiedene** Texte in drei Netzmodi (195 / 176 / 129 Zeichen). Der
> Buchungsweg quittiert ebenfalls ehrlich — `if(!_rpcOk||!_res){_showFb({kind:'error'});return;}`
> (`7656`), ausdrücklich kein grünes Häkchen ohne RPC-Erfolg.

> **B9 🟡 — aber am ECHTEN Terminal erscheint dieser Hinweis nie.**
> **Stelle:** `index.html:7559` — `if(props.terminal){return ()=>{alive=false;};}`
> steigt vor dem Laden aus, also wird `tblErr` dort nie gesetzt.
> **Gemessen:** Rolle `stempel_terminal`, alle drei Netzmodi, Textlänge
> **113 Zeichen, dreimal identisch**, kein Hinweis. Das ist so **gewollt**
> (das Terminal lädt bewusst nichts und scheitert erst beim Scan, dann aber
> laut) — es heißt nur: am Werkstor sieht man einem ruhenden Panel nicht an,
> ob es Netz hat. Der erste, der es merkt, ist der Mitarbeiter mit dem Chip
> in der Hand.
> **Und die eine Fehlermeldung, die er dann sieht, ist falsch adressiert:**
> `index.html:7746` setzt für den allgemeinen Fehlerfall
> `lines=["stempel_log — SQL ausführen?"]`. Der häufigste Auslöser ist ein
> Netzausfall; der Text schickt den Mitarbeiter in den SQL-Editor. Er steht
> 3 Sekunden (`_showFb`, `7601`), dann ist er weg.

---

## 4. Das Alter der Anzeige — die Zeitreise

Der Anker der Fragestellung lautete: *keine der Ansichten zeigt an, wie alt
die angezeigten Daten sind.* **Das ist für `#monteure` widerlegt und für
`#planung` schlimmer als vermutet.**

`MonteurTafel` führt seit v3.9.939 **zwei** Merker (`index.html:7871`):
`stand` = Zeitpunkt des letzten **erfolgreichen** Abrufs, `jetzt` = die Uhr.
`setStand` steht innerhalb von `if(Array.isArray(raw)){…}` (`7872`) — vom
Quelltext-Melder als „mit Erfolgsprüfung" erkannt.

`WochenplanTafel` hat denselben Kopf **ohne** diese Kur (`index.html:7367`):

```js
_react.useEffect.call(void 0, ()=>{const iv=setInterval(()=>setStand(new Date()),60000);return ()=>clearInterval(iv);},[]);
```

Kein Abruf, keine Prüfung, kein Bezug zu irgendwelchen Daten — eine **Uhr**.
Angezeigt wird sie als `… · Stand HH:MM`.

**Zeitreise, 40 Minuten ohne Netz, Rolle `lager_display`**
(`kiosk_tafeln_live.py`, Funktion `uhrprobe`, Playwright-`clock`):

```
monteure  t+0   : … | Daten von 14:18 | ⚠️ AS:Fehler(net) | …
monteure  t+40m : … | Daten von 14:18 · seit 40 min nicht aktualisiert | ⚠️ AS:Fehler(net) | …
planung   t+0   : 📋 Wochenplan · KW 40 | 28.09.–03.10. · Stand 14:18 · v3.9.997 · FZ:Fehler(net) …
planung   t+40m : 📋 Wochenplan · KW 40 | 28.09.–03.10. · Stand 14:58 · v3.9.997 · FZ:Fehler(net) …
```

Die MonteurTafel hält ihren Stempel bei `14:18` fest und schreibt das Alter
dazu. Die WochenplanTafel schiebt ihren auf `14:58` — 40 Minuten weiter,
ohne dass ein einziger Abruf gelungen wäre.

> **B4 🔴🔴 — Der „Stand" auf der Wochenplan-Tafel ist die Uhr, nicht das
> Datenalter. Er behauptet Frische, die nie geprüft wurde.**
> **Stelle:** `index.html:7367` (der Takt), `index.html:7416` (die Anzeige
> `… · Stand '+_pad(stand.getHours())+':'+_pad(stand.getMinutes())`).
> **Auslöser:** jeder Ausfall, der länger als eine Minute dauert.
> **Folge:** Nach 40 Minuten ohne jede Verbindung steht im Kopf **`Stand
> 14:58`** — eine taufrische Uhrzeit über 40 Minuten alten (hier: gar nicht
> vorhandenen) Daten. Wer die Tafel fotografiert oder im Vorbeigehen abliest,
> hat keine Möglichkeit, das zu bemerken. Der Zwilling nebenan zeigt im
> selben Augenblick korrekt **„seit 40 min nicht aktualisiert"**.
> Das ist **wortwörtlich der Fehler, der in v3.9.939 für die MonteurTafel
> kuriert wurde** — der Kommentar dort beschreibt ihn bis in die Formulierung
> („Wer die Tafel fotografiert, sah eine frische Uhrzeit ueber moeglicherweise
> stundenalten Daten"). Die zweite Tafel wurde nicht mitgenommen.
> **Wie gemessen:** Quelltext-Melder (`setInterval` mit `setStand`, mit/ohne
> Erfolgsprüfung — Selbstprobe mit je einem Köder für beide Formen) **und**
> am Schirm mit vorgestellter Uhr.
> **🔴 Der Köder dieser Probe ist der Zwilling selbst:** erscheint bei
> `#monteure` nach 40 Minuten **kein** Alterstext, hat die vorgestellte Uhr
> nicht gewirkt, und „`#planung` zeigt kein Alter" wäre eine Aussage über
> mein Werkzeug statt über die Tafel. Das Skript bricht in diesem Fall mit
> `return 2` ab, **bevor** es eine Zahl nennt.

**Und die Fußzeile verspricht etwas, das so nicht stimmt.** `index.html:7448`
schreibt `"read-only · aktualisiert alle 60s"`. Gemessen sind drei
verschiedene Takte: Abwesenheiten 60 s (`7366`), die Uhr 60 s (`7367`), die
Wochenzeilen **30 s** und nur bei sichtbarem Tab (`9367`) — und Namen sowie
Fahrzeuge **nie** (B7). Die Fußzeile ist die einzige Aussage über Aktualität,
die auf der Tafel steht, und sie gilt für keinen der Inhalte vollständig.

### Wie oft würde eine Meldung feuern? (Frage des Koordinators)

Eine Meldung, die zu oft kommt, wird weggeklickt — an einer Wandtafel wird
sie nicht einmal weggeklickt, sie wird schlicht Teil des Bildes. Für die
vier denkbaren Melder, mit den gemessenen Takten gerechnet:

| Melder | Feuert im Normalbetrieb | Begründung, gemessen |
| --- | --- | --- |
| Alterstext auf `#planung` (Schwelle wie `KIOSK_STAND_WARN_MS` = 15 min) | **0×/Tag** | Der Wochenplan-Takt ist 30 s; 15 Minuten sind **30 ausgefallene Umläufe in Folge**. Ein einzelner Aussetzer wird vollständig geschluckt. Im gemessenen `leer`-Modus (HTTP 200 + `[]`, also Normalbetrieb ohne Zeilen) feuert er **nie**. |
| Rechte-Hinweis aus `__EP_RLS` | **0×/Tag**, solange die Policies stimmen | Gemessen: `leer` → `__EP_RLS` = 0 Einträge, `403` → 11. Die Marke entsteht ausschließlich bei 401/403, nicht bei leeren Ergebnissen. Ein Treffer ist **immer** ein echter Befund. |
| Hinweis auf leere Abwesenheits-Antwort | **täglich mehrfach** — **darum nicht empfohlen** | Eine leere Abwesenheitsliste ist der Normalfall (an den meisten Tagen fehlt niemand). Unterschieden gehört nur „Abruf gescheitert" (aus dem `catch` bei `7366`) von „Abruf leer" — das feuert wieder 0×/Tag. |
| Alterstext auf Namen/Fahrzeugen | **dauernd**, also wertlos | Sie werden nach dem Start nie nachgeladen (B7); ein Altersmelder stünde ab Minute 15 permanent im Bild. Der richtige Weg ist dort **nachladen**, nicht warnen. |

---

## 5. Lesbarkeit an der Wand

### 🔴 Drei Fallen, und alle drei sind eingetreten

1. **`getComputedStyle().fontSize` ist nicht die Größe am Schirm.** Beide
   Tafeln legen ihren Inhalt in einen Knoten mit
   `transform:scale(_fitScale)`, Klemmbereich **0,6 bis 1,25**
   (`index.html:7412` bzw. `7998`; die Klemme rechnet `_fit` bei `7365` bzw. `7863`). Eine Transformation ändert `fontSize`
   nicht. Der Melder rechnet die Streckung darum aus
   `rect.height / offsetHeight` zurück und weist **beide** Zahlen aus.
2. **Eine CSS-Regel mit `!important` übersteuert jede Inline-Angabe.**
3. **CSS lebt in dieser App an mehreren Orten.** Gemessen wurden die
   `<style>`-Blöcke (gehärtet: *vor einem `</style>` gilt das LETZTE
   `<style>`* — das naive Muster liest an dieser Datei rund 1 700 Zeilen
   JavaScript als CSS) **und** der Laufzeit-Stilblock `GCSS()`
   (`index.html:6402`, ein Vorlagenliteral).

### Gemessen, Rolle `lager_display`, leeres Brett

| | `#planung` | `#monteure` | `#stempel` |
| --- | --- | --- | --- |
| Textknoten mit eigenem Text | 27 | 31 | 7 |
| kleinste `fontSize` | 12 px | 12 px | 14 px |
| kleinste **wirksame** Größe (1920×1080, leer) | 15,0 px | 15,0 px | 14 px |
| Streckung dort | 1,25 (obere Klemme, alle 27 Knoten) | 1,25–1,26 | 1,0 (keine) |
| Knoten unter 24 px (wirksam) | 25 von 27 | 26 von 31 | 6 von 7 |
| kleinste wirksame Größe bei gedrängtem Brett (1920×380) | **13,8 px** | **12,7 px** | — |
| Kontrast-Rügen (WCAG AA) | **3** (2 bei Ladefehler) | **18** (19 bei Ladefehler) | 1 |

Die Streckung läuft am **leeren** Brett an die obere Klemme — aus 12 px
werden 15. Das ist die freundliche Richtung. Bei einer vollen Woche wächst
die Inhaltshöhe, und `sc = min(1.25, max(0.6, wh/ch))` fällt; an der unteren
Klemme würden aus 12 px **7,2 px**. Ersatzweise gemessen über eine kleinere
Fensterhöhe (im Bruch `wh/ch` dieselbe Rechnung): bei 1920×380 stehen die
kleinsten Texte schon bei 12,7 px. **Eine Aufnahme mit einer echten vollen
Woche fehlt** (siehe Umfang, Punkt 4).

> **B10 🟡 — `#monteure` hat 18 Texte unter dem AA-Kontrast, darunter genau
> die Alterswarnung.**
> **Stelle:** die Kopfzeile, `index.html:8004`
> **Gemessen** (am gerenderten Knoten, Vordergrund aus `getComputedStyle`,
> Hintergrund nach oben gesucht bis zur ersten deckenden Farbe):
> `„Daten von 14:17"` = **4,31 : 1** bei 14 px (Soll 4,5),
> `„Woche"` = 3,86 : 1, `„Mi"` (Spaltenkopf, 18 px fett) = 3,44 : 1,
> `„Mitarbeiter"` = 4,31 : 1.
> **Folge:** Der einzige Hinweis, der sagt, wie alt die Zahlen sind, ist der
> kontrastschwächste Text auf der Tafel — und mit 14 px auch der kleinste
> im Kopf. Auf `#planung` steht die Fußzeile `„read-only · aktualisiert alle
> 60s"` bei **2,45 : 1** und 13 px, die Diagnosezeile mit der einzigen
> Fehleranzeige bei **3,73 : 1**.
> Auf `#stempel` ist es genau eine Rüge, und sie trifft den Buchungsknopf:
> `„▶ Buchen"` = **3,86 : 1** bei 14 px.
> **Einschränkung:** gezählt sind nur Knoten, für die ein deckender
> Hintergrund auffindbar war (`ohne_hintergrund` = **0** in allen 30
> Aufnahmen — die Zählung ist also vollständig und keine Untergrenze).
> Halbdurchsichtige Überlagerungen sind nicht mitgerechnet.

> **B5 🔴 — Am Stempel-Terminal drückt eine `!important`-Regel jedes
> Eingabefeld auf 14 px, egal was im Quelltext steht.**
> **Stelle:** `index.html:6414` in `GCSS()`:
> `@media(min-width:601px){input,select,textarea{font-size:14px !important}}`
> (daneben `6413`: dieselbe Regel mit 16 px ohne Media-Bedingung).
> **Auslöser:** jede Kioskbreite ≥ 601 px — also **jedes** Wandpanel.
> **Folge, gemessen:** Ein eingesetztes `<input style="font-size:30px">`
> kommt in **allen 30 Aufnahmen** mit **14 px** zurück. Das UID-Feld der
> Stempeluhr deklariert `fontSize:15` (`index.html:7852`) und misst 14 px.
> Die Datumsfelder des Urlaubsantrags deklarieren
> `fontSize:"clamp(20px,2.4vw,30px)"` (`index.html:7791`, Stilobjekt `dIn` bei `7785`) — bei 1280 px
> wären das 30 px; sie fallen unter denselben Selektor. Ein Mitarbeiter, der
> am Wandpanel im Stehen sein Urlaubsdatum eintippt, liest es in 14 px.
> **Wie gemessen:** eingesetzter Köder am gerenderten Knoten, **mit
> Gegenprobe**: ein `<div style="font-size:30px">` im selben Einsatz **bleibt
> bei 30 px** — der Selektor nennt nur `input,select,textarea`. Ohne diese
> Gegenprobe wäre „14 gemessen" auch mit einer Regel vereinbar, die alles
> kleinmacht, und die Aussage über die Eingabefelder wäre leer.
> **Nicht gemessen:** die Datumsfelder selbst — sie sind erst nach einem
> gültigen Chip-Scan erreichbar (Umfang, Punkt 3). Die Aussage über sie ist
> aus der Regel abgeleitet, nicht am Feld abgelesen.

Zur Einordnung: von **26** `font-size`-Regeln mit `!important` greifen bei
Kioskbreite nur **5** — drei davon auf `.kpi-grid.epk-leiste`, eine Klasse,
die auf keiner der drei Tafeln vorkommt. Die restlichen 21 hängen an
`@media (max-width: 600px)` und sind für die Wand ohne Belang. **Der
Schriftboden aus `docs/befunde/UNTER24.md` ist eine Mobil-Regel** —
`@media (pointer: coarse), (max-width: 768px)` — und greift auf einem
1280- oder 1920-px-Panel **nicht**. Für die Kiosk-Ansichten gilt er also
nicht, und gemessen wurde er dort bis heute auch nie.

---

## 6. Der Plausibilitätsanker — was hielt, was fiel

Die Vorgabe lautete, und sie war ausdrücklich als Behauptung markiert:

| Behauptung | Ergebnis | Beleg |
| --- | --- | --- |
| „Die drei Ansichten unterscheiden NICHT zwischen ‚es gibt heute nichts' und ‚ich konnte nichts laden'." | **Für zwei bestätigt, für eine widerlegt.** `#planung` und `#monteure` sehen keine einzige RLS-Marke an (0 Vorkommen in beiden Rümpfen); bei 403 liegen 11 Einträge in `__EP_RLS` und die Wochenplan-Zeile bleibt wortgleich. **`#stempel` unterscheidet sauber** — drei Netzmodi, drei verschiedene Texte. | Abschnitt 3, B1/B8 |
| „Mindestens eine zeigt bei einem Fehler eine leere oder gestrige Liste, ohne das zu sagen." | **Bestätigt, und schärfer:** nicht eine gestrige Liste, sondern eine **hartkodierte von 2018** (B3), plus drei leere Abwesenheitszeilen, die als Aussage gelesen werden (B2). | B2, B3 |
| „Keine zeigt an, WIE ALT die angezeigten Daten sind." | **Widerlegt für `#monteure`** — sie zeigt es seit v3.9.939 korrekt und in Klartext („seit 40 min nicht aktualisiert"), gemessen in der Zeitreise. **Für `#planung` ist es schlimmer als behauptet:** sie zeigt nicht *nichts*, sondern eine **falsche** Frische — nach 40 Minuten Ausfall steht dort `Stand 13:09`. Eine fehlende Angabe ist eine Lücke; eine falsche ist eine Zusage. | Abschnitt 4, B4 |

**Die Abweichung ist der eigentliche Befund:** Die Kur, die diesen Fehler
beseitigt, ist seit v3.9.939 im Haus, ausführlich begründet, mit einer
funktionierenden Textform — und steht **nur in einer der beiden Tafeln**.
Es fehlt nicht die Einsicht, es fehlt die Übertragung auf den Zwilling.
Dieselbe Form ist in `docs/befunde/BUGHUNT_2026-09-30.md` mehrfach
verzeichnet („zwei gleichlautende Stellen", „vier Stellen, nicht drei").

---

## 7. Die Befunde auf einen Blick

| | Befund | Stelle | Einstufung |
| --- | --- | --- | --- |
| B1 | `#planung` zeigt bei abgewiesenem Lesezugriff denselben Text wie bei leerem Plan — `__EP_RLS` hat 11 Einträge, die Tafel sieht keinen an | `7438`, Lieferant `8095` | 🔴🔴 |
| B4 | „Stand HH:MM" auf `#planung` ist die Uhr, nicht das Datenalter — nach 40 min Ausfall steht dort eine taufrische Uhrzeit | `7367`, Anzeige `7416` | 🔴🔴 |
| B3 | Fällt der Start-Abruf aus, zeigt die Wand vier hartkodierte Namen von 2018 | `8150`, `3721`, `8507` | 🔴 |
| B2 | Kranken-/Urlaubs-/ZA-Zeilen bleiben bei Ladefehler leer und lesen sich als „niemand fehlt" | `7366` | 🔴 |
| B5 | `!important` drückt jedes Eingabefeld am Kiosk auf 14 px, auch die als `clamp(20px…30px)` deklarierten Datumsfelder | `6414` (GCSS) | 🔴 |
| B6 | `#planung` allein öffnet für einen Admin den Kiosk nicht — das Tor liest nur `location.search` | `9593`, `9602` | 🟡 |
| B7 | Namen und Fahrzeuge werden nach dem Start nie wieder geholt (bis 24 h Versatz) | `8507`, `8515` | 🟡 |
| B9 | Am echten Stempel-Terminal erscheint nie ein Verbindungshinweis; der allgemeine Fehlertext schickt in den SQL-Editor | `7559`, `7746` | 🟡 |
| B10 | 18 Texte auf `#monteure` unter AA-Kontrast, darunter die Altersangabe selbst (4,31 : 1 bei 14 px) | `8004` | 🟡 |
| B11 | Fußzeile verspricht „aktualisiert alle 60s" — gemessen sind 30 s, 60 s und *nie*, je nach Inhalt | `7448` | 🟡 |
| B12 | `props.abs` wird an `WochenplanTafel` übergeben und nie gelesen | `9609` | ⚪ |
| B8 | `#stempel` unterscheidet leer / abgewiesen / ohne Netz korrekt — **kein Fehler**, damit niemand zweimal sucht | `7469`, `7569`–`7571`, `7657` | ✅ |

---

## 8. Wie gemessen wurde — und wie die Werkzeuge sich selbst widerlegen

### `scripts/kiosk_tafeln_quelltext.py`

Trennt Code von Kommentar mit dem geeichten `code_scan.ist_code` (Eichung an
index.html: **21 von 21** `isMob`-Deklarationen als Code erkannt; scheitert
die Eichung, nennt das Modul keine Zahl). Nötig, weil `index.html` lange
deutsche Kommentare führt, die genau die gesuchten Marken **wörtlich
zitieren** — wer den Rohtext durchsucht, misst seine eigene Begründung mit.

Selbstprobe an einem **selbstgebauten** Text (nicht an index.html: eine
Probe, die auf Bauteilnamen zeigt, fällt aus, sobald jemand umbenennt — und
dann fällt ein Werkzeug aus, das damit nichts zu tun hat). **Ein Köder je
Schreibweise, plus Gegenprobe:**

```
RLS-Marken (Koeder je Form)        2    soll 2    OK
Lesewege (4 Formen)                4    soll 4    OK
RPC-Name aus Zeichenkette      ['probe_eins']     OK
catch gesamt                       2    soll 2    OK
catch davon leer                   1    soll 1    OK
setInterval mit setStand           2    soll 2    OK
davon OHNE Erfolgspruefung         1    soll 1    OK
fontSize beide Schreibweisen   [9, 13]  soll [9, 13]  OK
Farbpaare (beide Zitatformen)      2    soll 2    OK
Kontrast #777777 auf #888888 < 3 True   soll True OK
CSS-Regel ohne @media gilt      [True]  soll [True]   OK
CSS-Regel max-width:600 gilt nicht [False] soll [False] OK
Blindprobe (blinder Melder = 0)              OK
```

Die **Gegenproben** stecken im Probetext: dieselben Marken stehen dort noch
einmal in einem Block- und in einem Zeilenkommentar und dürfen nicht
mitzählen (`RLS-Marken` = 2, nicht 6; `fontSize` = `[9,13]`, nicht
`[9,13,98,99]`). Die **Blindprobe** ist die Umkehrung: einem Melder, dem man
das Codefeld wegnimmt, **muss** die Zahl auf 0 fallen — täte sie das nicht,
wäre „alle Proben grün" auch dann wahr, wenn die Proben nichts messen.
Scheitert eine Probe, endet das Skript mit `return 2` und **nennt keine
Zahl**.

**Eine eigene Falle, gemessen und behoben:** Die erste Fassung suchte
`lager_display` im Codefeld und fand **0** — der Begriff steht in
`curUser.role==='lager_display'` in einer **Zeichenkette**. Ein Melder, der
das nicht bedenkt, meldet „kommt nicht vor", und das sieht aus wie ein
Befund. Die RPC-Namen werden darum ausdrücklich an der Position des `/rpc/`
gesucht, nicht im Codefeld — die Selbstprobe `RPC-Name aus Zeichenkette`
hält genau das fest.

### `scripts/kiosk_tafeln_live.py`

30 Aufnahmen: 18 in der Admin-Vorschau (3 Ansichten × 3 Netzlagen × 2
Größen), 9 unter den echten Kiosk-Rollen, 1 Wegprobe, 2 Streckungsproben —
dazu die Zeitreise mit ihren beiden eigenen Aufnahmen.
Selbstprobe **in derselben Seite**, vor der ersten Zahl:

```
Hinweis: alle vier Formen gefunden  [Fehler, Keine Verbindung, nicht aktualisiert, ⚠]  OK
Schrift: 9-px-Koeder gefunden       9        soll 9      OK
Schrift: nur der SICHTBARE 9-px-Knoten  1    soll 1      OK
Kontrast: grau auf grau geruegt     1        soll 1      OK
!important-Probe: div bleibt 30 px  30       soll 30     OK
!important-Probe restlos entfernt   True     soll True   OK
Koeder restlos entfernt             True     soll True   OK
Hinweis zurueck auf Stand VORHER    []       soll []     OK
Schrift zurueck auf Stand VORHER    0        soll 0      OK
Kontrast zurueck auf Stand VORHER   3        soll 3      OK
```

**Ein Köder je Form** — die vier Hinweisformen werden einzeln eingesetzt und
müssen einzeln gefunden werden. **Vier Gegenproben in die andere Richtung:**
dieselben Hinweise in einem `display:none`-Knoten und in einem
HTML-Kommentar dürfen **nicht** gefunden werden; eine 9-px-Schrift mit
`visibility:hidden` darf **nicht** mitzählen (ohne diese Frage hätte der
unsichtbare Zwilling mitgezählt und die Probe wäre grün geworden, obwohl der
Melder unsichtbaren Text misst); `#000000` auf `#ffffff` darf **nicht**
gerügt werden; und nach dem Entfernen müssen **alle** Zahlen auf den Stand
von vorher zurückfallen. Die `!important`-Probe trägt ihre Gegenprobe in
sich: das `div` **muss** bei 30 px bleiben.

Die **Zeitreise** hat als Köder den Zwilling: schlägt bei `#monteure` der
Alterstext nicht an, bricht das Skript mit `return 2` ab, **bevor** es etwas
über `#planung` sagt.

### `scripts/kiosk_tafeln_mutationsprobe.py` — misst der Riegel WIRKUNG?

Dass eine Selbstprobe **da ist**, belegt nichts. Geprüft wird darum ihr
**Ausfall**: nimmt man dem Werkzeug genau eine Fähigkeit, muss es rot werden
**und danach keine Zahl mehr nennen**. Die zweite Hälfte ist die wichtigere —
ein Werkzeug, das zwar `2` zurückgibt, aber trotzdem seine Tabelle druckt,
ist gefährlicher als eines, das schweigt: die Tabelle wird gelesen, der
Rückgabewert nicht.

```
GRUNDLINIE (unveraendert)
  Rueckgabe 0, nennt Zahlen: True

MUTATIONEN
  RLS-Melder kennt nur EINE Schreibweise      Rueckgabe 2  Zahlen False  ROT wie gewollt
  Erfolgspruefung erkennt Array.isArray nicht Rueckgabe 2  Zahlen False  ROT wie gewollt

GEGENPROBE: nach dem Zuruecksetzen wieder gruen?
  Rueckgabe 0, nennt Zahlen: True
```

Die beiden Mutationen sind mit Bedacht gewählt: der Verlust **sieht in
beiden Fällen wie ein Befund aus**. Ein Melder, der nur noch eine
Schreibweise kennt, meldet für die anderen „kommt nicht vor"; eine
Erfolgsprüfung, die ihr Muster verloren hat, erklärt einen richtig gebauten
Takt fälschlich zur bloßen Uhr — und hätte damit **B4 auch für die
MonteurTafel gemeldet**, wo er nicht gilt.

Die **Grundlinie ist Teil der Probe**: wäre das Werkzeug schon unverändert
rot, würden zwei grüne Haken darunter nichts messen. Die **Gegenprobe am
Ende** fängt den Fall ab, dass die Probe das Werkzeug beschädigt zurücklässt.

### Fallen, die hier vermieden wurden — und warum sie hier standen

* **Ein Melder, der nur `fontSize` liest, misst eine Zahl, die es am Schirm
  nicht gibt.** Beide Tafeln strecken ihren Inhalt mit `transform:scale`
  zwischen 0,6 und 1,25. Die erste Fassung meldete „min 12 px"; wirksam
  waren 15. In beide Richtungen falsch.
* **Nur die Admin-Vorschau zu messen** hätte ergeben: `__kioskAsErr` und
  `__kioskFzErr` sind **nie gesetzt** — in allen 18 Admin-Aufnahmen. Das
  hätte als Befund „die Marken feuern nicht" ausgesehen. Sie feuern; nur
  nicht auf dem Admin-Pfad. Die Rolle ist kein Beiwerk, sie ist ein anderer
  Datenweg.
* **Das naive `<style[^>]*>(.*?)</style>`** liest an dieser Datei rund 1 700
  Zeilen JavaScript als CSS, weil ein `<style>` in einem deutschen Kommentar
  steht. Verwendet wird: *vor einem `</style>` gilt das LETZTE `<style>`*,
  plus der Vorlagenliteral-Block `GCSS()` getrennt.
* **`$?` nach einer Pipe** ist der Code des letzten Glieds. Beide Skripte
  schreiben ihr Urteil in die Ausgabe **und** geben es als Rückgabewert; das
  Urteil in diesem Papier stammt aus der Logdatei, nicht aus einem Exit-Code
  hinter einer Pipe.
* **`sys.stdout.reconfigure(encoding="utf-8")`** steht in beiden Skripten
  ganz oben. Die Konsole hier ist cp1252; ohne das stirbt ein Skript an
  seiner eigenen Ausgabe, und ein Absturz ist am Rückgabewert von einem
  Befund nicht zu unterscheiden.

---

## 9. Was an `index.html` geändert wurde

**Nichts.** Kein `Edit`, kein `Write`, kein `sed -i`. Die Kiosk-Hash-Wege
(`_kioskScreenPick`, `_canKiosk`, `window.__kioskScreen`) sind unberührt.

`git status` zeigt `index.html` am Ende dieser Arbeit dennoch als geändert.
**Das ist nicht meine Änderung**, und das ist nachgesehen, nicht behauptet:
`git diff index.html` enthält genau einen Block — `function _sqDropName(…)`
bei Zeile 2656, mit einem v3.9.998-Kommentar über verworfene
Warteschlangen-Einträge. Das ist der andere Vorgang, der an dieser Datei
arbeitet; mit den Kiosk-Tafeln (ab 7373) hat er keine Berührung. Der Stand,
gegen den hier gemessen wurde, ist über `md5 = 3538f7ec726ce22053e5649d00adf2d1`
und 30 430 Zeilen festgehalten.
Neu geschrieben wurden ausschließlich:

```
scripts/kiosk_tafeln_quelltext.py
scripts/kiosk_tafeln_live.py
scripts/kiosk_tafeln_mutationsprobe.py
docs/befunde/KIOSK_QUELLTEXT.json
docs/befunde/KIOSK_LIVE.json
docs/befunde/bughunt/kiosk_anzeigen.md   (dieses Papier)
```

Nichts davon ist committet, nichts ist zum Index hinzugefügt.

---

## 10. Nachfahren

```bash
cd C:\repos\epkolar-app
python scripts/kiosk_tafeln_quelltext.py --json docs/befunde/KIOSK_QUELLTEXT.json
python scripts/kiosk_tafeln_live.py      --json docs/befunde/KIOSK_LIVE.json
python scripts/kiosk_tafeln_mutationsprobe.py
```

Beide enden mit `2`, wenn eine Selbstprobe scheitert — dann steht in der
Ausgabe, **welche**, und es steht **keine Zahl** darunter.
