# SMOKE_KIOSK — Wandmonitor-Ansichten `?screen=monteure` und `?screen=planung`

**Datum:** 26.09.2026 · **Art:** reine Messung, NICHTS repariert, NICHTS ausser dieser Datei geschrieben.
**Stand der App waehrend der Messung:** `APP_VERSION` 3.9.934 → 3.9.935 (ein anderer Lauf hat
`index.html` waehrend meiner Messung bearbeitet).

**Messaufbau:** Playwright/Chromium, lokaler HTTP-Server auf dem Repo. `index.html` wurde je Runde
EINGEFROREN (Kopie im Scratchpad, wird statt der Repo-Datei ausgeliefert) — sonst haette ich ein
bewegliches Ziel gemessen. Die Pruefsummen je Runde:

| Runde | Inhalt | `index.html` sha256[:16] | Bytes |
|---|---|---|---|
| 1 | 36 Laeufe: 3 Rollen × 2 Ansichten × 2 Netzlagen × 3 Groessen, LEERE Tafel | `2fc0d9e555dd0b44` | 3 640 548 |
| 2 | 24 Laeufe mit GEFUELLTER Tafel (REST per `route.fulfill` gesetzt) | `ae72a8b9aeed9103` | 3 641 339 |
| 3 | Probe A (`__kioskAsErr`, 10 Faelle) + Probe B (Auto-Fit, 18 Faelle) | `ae72a8b9aeed9103` | 3 641 339 |
| 4 | „Stand"-Probe (80 s Laufzeit) | `6b9b97844a916c91` | — |
| 5 | Service-Worker-Gegenprobe + Bestaetigung (18 Laeufe, SW ERLAUBT) | `4a2d8c20dc42c720` | 3 644 101 |
| 6 | Schwingungs-Abtastung (6 Faelle × 60 Proben à 100 ms) | `90328e82dcc10245` | 3 644 672 |

Groessen: **1920×1080**, **3840×2160**, **1366×768**. Zeitzone Europe/Vienna, Sprache de-AT.
Messtag ist ein Samstag → die Tafeln zeigen per `kioskDisplayWeekOffset` die **Folgewoche KW 40
(Mo 28.09.–So 04.10.)**; die Saat liegt bewusst in dieser Woche, sonst filtert `inWeek()` sie weg.

---

## 0. Die wichtigste Korrektur vorweg

> Auftragstext: „Die Wandmonitor-Ansichten laufen **UNAUTHENTIFIZIERT** ueber `?screen=monteure`
> und `?screen=planung`."

**Das ist nicht so.** Beide Ansichten verlangen eine Sitzung. `?screen=` allein bewirkt nichts.
Beleg unten in §2 (12 von 12 Laeufen ohne `localStorage` landeten auf dem Anmeldeschirm).

Die Tafeln laufen am Wandpanel unter einer **angemeldeten Rolle `lager_display`**, deren Sitzung im
`localStorage` liegt. `?screen=` ist fuer diese Rolle nur die Auswahl zwischen zwei Tafeln; fuer
`admin` ist es die Vorschau. Gemessen habe ich deshalb alle drei Faelle: `anon`, `lager_display`
(die echte Wandpanel-Lage) und `admin` (Vorschau).

---

## 1. Je Ansicht und je Groesse: rendert sie, was steht drin, was ist abgeschnitten

Gemessen **pro ELEMENT**, nicht pro Container — ein Kind, das aus seinem Elter herausragt, zaehlt in
`getBoundingClientRect()` des Elters nicht mit. Drei Melder: (a) Rechteck ausserhalb des Sichtfelds,
(b) Rechteck ueber dem naechsten clippenden Elter, (c) `scrollWidth > clientWidth` bei
`overflow != visible`.

Runde 1 lief gegen eine **leere** Tafel (keine Arbeitsscheine, „Keine Wochenplan-Zeilen fuer KW 40")
und meldete 0 Beschnitte bei 27–32 gezaehlten Elementen. **Das ist kein Ergebnis, sondern eine
ausgefallene Messung** — null Funde auf einer leeren Tafel. Deshalb Runde 2 mit gesetzter Fuellung
(8 Feld-Mitarbeiter, 6 Bauvorhaben, 16–22 Arbeitsscheine, Abwesenheiten, 3 Fahrzeuge), Grundgesamtheit
dann 104–203 Elemente.

### `?screen=monteure` (MonteurTafel)

| Groesse | rendert | Massstab | ausserhalb | vom Elter abgeschnitten | Text gekuerzt |
|---|---|---|---|---|---|
| 1920×1080 | ja | 1.25 | 0 | 0 | 0 (normal) / 30 (lange Namen) |
| 3840×2160 | ja | 1.25 | 0 | 0 | 0 (normal) / 9 (lange Namen) |
| **1366×768** | ja | 1.25 | 0 | **16** | 2 |

Inhalt: Kopfzeile „📋 Monteur-Tafel · KW 40 · 28.09.–04.10. · nächste Woche · Stand HH:MM",
Knoepfe Woche/Tag, „🔄 Auto AN", Vollbild, Logout; darunter Mitarbeiterzeilen × Mo–So mit
Kacheln `HH:MM · AS-Nummer / Kundname / Arbeitsort`.

**Befund M1 — die Arbeitsschein-Nummer ist bei 1366×768 hart abgeschnitten (16 von 16 Kacheln).**
Die Nummer sitzt in einem `span` mit `flexShrink:0` in einem `overflow:hidden`-Elter. Weil sie nicht
schrumpfen darf, laeuft sie **31 px ueber den Elter hinaus und wird HART abgeschnitten — ohne
Auslassungspunkte**, obwohl `textOverflow:'ellipsis'` gesetzt ist (das greift nur, wenn der Text die
eigene Box sprengt, nicht wenn die Box den Elter sprengt). Am Schirm steht ueberall „AS–2026–4" und
dann nichts mehr. Reproduziert 3/3 mit erlaubtem Service Worker gegen die aktuelle Datei.
Screenshot: `s_lager_display_monteure_normal_1366x768.png` (Scratchpad).

**Befund M2 — lange, aber echte Kundennamen verlieren zwei Drittel.** Bei 1920×1080 ist die
Kachelspalte 162 px breit; „Wohnungsgenossenschaft Oberösterreich reg.Gen.m.b.H." braucht 486 px →
**ein Drittel sichtbar**. 30 solche Kuerzungen im Lauf. Bei 3840×2160 nur noch 9 (breitere Zellen).
Das ist gewollte Ellipsis, keine Kaputtheit — aber auf einer Wandtafel, die man aus 4 m Abstand liest,
ist „Wohnungsgenossenschaft Oberö…" nicht dasselbe wie ein Kundenname.

### `?screen=planung` (WochenplanTafel)

| Groesse | rendert | Massstab | Elemente unter der Bildkante | px abgeschnitten | erreichbar? |
|---|---|---|---|---|---|
| 1920×1080 | ja | 1.25 | 0 | 0 | — |
| 3840×2160 | ja | 1.25 | 0 | 0 | — |
| **1366×768** | ja | **schwingt 1.1261 ↔ 1.024** | **31** | **76** | **NEIN** |

Inhalt: „📋 Wochenplan · KW 40 ▶ nächste Woche · 28.09.–03.10. · Stand HH:MM · v3.9.935 · FZ:3 · Spez:2",
Tabelle Bauvorhaben × Mo–Sa + Bemerkung, Zeilen 🤒 Krankenstand / 🏖️ Urlaub / ⏰ Zeitausgleich,
Spezialfahrzeug-Zeilen, Fussleiste mit Farblegende und „read-only · aktualisiert alle 60s".

**Befund P1 — der Auto-Fit aus v3.9.634 SCHWINGT bei 1366×768 dauerhaft, und in einer der beiden
Lagen fehlen 76 px unwiederbringlich.**

6 s lang alle 100 ms abgetastet (60 Proben):

```
planung  1366x768   Massstaebe in 6 s: {1.1261: 26, 1.024: 34}
                    px UNTER der Kante: {76: 26, 0: 34}
planung  1920x1080  {1.25: 60}   px unter der Kante: {0: 60}
planung  3840x2160  {1.25: 60}   px unter der Kante: {0: 60}
monteure alle drei  {1.25: 60}   px unter der Kante: {0: 60}
```

Die Tafel wechselt also rund zwei- bis dreimal pro Sekunde ihr Layout. In 26 von 60 Proben liegen
**31 Elemente unter der Bildkante**, tiefstes Pixel 844 von 768. `overflow:hidden` am 100vh-Rahmen,
`scrollHeight - clientHeight = 0`, `document.scrollTopMax = 0` — **es ist nicht wegrollbar, es ist weg.**
Betroffen: die letzte Spezialfahrzeug-Zeile (LL-456CD, mitten im Text gekappt) und die **komplette
Fussleiste** samt Farblegende und „read-only · aktualisiert alle 60s".
Screenshot-Beleg: `beweis_planung_1366x768.png` (Scratchpad).

Mechanik, aus dem Code gelesen und mit den Zahlen gedeckt: `_fit` setzt
`sc = min(1.25, max(0.6, window.innerHeight / el.scrollHeight))` — und **dasselbe Element traegt
`width:(100/_fitScale)%`**. Ein anderer Massstab heisst also eine andere Breite, eine andere Breite
heisst anderer Umbruch, anderer Umbruch heisst eine andere `scrollHeight`. `wh/ch` hat bei 1366×768
keinen Fixpunkt:

* `scrollHeight 682` → `768/682 = 1.126` → Breite 88.8 % → mehr Umbruch → Inhalt waechst auf 750
* `scrollHeight 750` → `768/750 = 1.024` → Breite 97.7 % → weniger Umbruch → Inhalt faellt auf 682 → zurueck

Die Daempfung `Math.abs(prev-sc) > 0.01` hilft nicht: die beiden Lagen liegen 0.10 auseinander.
Der Effekt laeuft bei jedem Render, also endlos.

Nebenbefund: im schlechten Zustand sagt **das eigene Kriterium des Auto-Fits schon „passt nicht"**
(`scrollHeight * skala = 844 > 768`) — er misst es, zieht aber keine Folgerung, weil `_fit` pro
Ereignis genau einmal rechnet und nicht nachregelt.

**Befund P2/M3 — auf einem 4K-Wandmonitor liegen zwei Drittel des Schirms brach.** Der Massstab ist
bei `max 1.25` gedeckelt, der Inhalt hat eine natuerliche Hoehe:

| | 1366×768 | 1920×1080 | 3840×2160 |
|---|---|---|---|
| `planung` Inhaltshoehe | 844 px (110 %, s. P1) | 810 von 1080 (**75 %**) | 767 von 2160 (**36 %**) |
| `monteure` Inhaltshoehe | 757 von 768 (99 %) | 757 von 1080 (**70 %**) | 757 von 2160 (**35 %**) |

Bei 3840×2160 steht die Tafel also im oberen Drittel, darunter Leere. Kein Fehler im Sinne von
kaputt — aber die Groesse, fuer die ein Wandmonitor gekauft wird, wird nicht genutzt.

---

## 2. Verlangt eine der beiden einen Login? — JA, beide. Mit Beleg.

Statisch: `index.html:9427` `if(!curUser&&!portalProj) return React.createElement(LoginScreen,…)`
steht **vor** dem Kiosk-Tor in `:9441`
(`_canKiosk = _isLagerDisplay || _isStempelTerminal || (curUser.role==='admin' && !!_kioskScreen)`).
Ohne `curUser` wird das Tor nie erreicht.

Gemessen, 12 von 12 Laeufen (2 Ansichten × 2 Netzlagen × 3 Groessen), leerer `localStorage`:

```
anon  monteure netz=aus 1920x1080 -> login      anon  planung netz=aus 1920x1080 -> login
anon  monteure netz=aus 3840x2160 -> login      anon  planung netz=aus 3840x2160 -> login
anon  monteure netz=aus 1366x768  -> login      anon  planung netz=aus 1366x768  -> login
anon  monteure netz=401 …3× -> login            anon  planung netz=401 …3× -> login
```

Aufnahme des Falls `anon/monteure/1920×1080`:

```json
{"loginSichtbar": true, "pwFelder": 1, "monteurTafel": false, "wochenplanTafel": false,
 "kioskScreen": "monteure", "tabellenZeilen": 0,
 "text": "EP: Kolar & Sohn … Benutzername\nPasswort\n👁️\n🔐 Anmelden\n… v3.9.934-supabase"}
```

Bemerkenswert: `window.__kioskScreen` steht dabei korrekt auf `"monteure"` — die Ansichts-Anheftung
aus v3.9.784 arbeitet, das Tor sperrt trotzdem richtig.

Mit Rolle `lager_display` im `localStorage` rendern beide Tafeln in 12 von 12 Laeufen; mit `admin`
+ `?screen=` ebenfalls in 12 von 12.

---

## 3. `window.__kioskAsErr` aus v3.9.827 — wo, wann, und live gesehen?

**Wo im Code.** Gesetzt ausschliesslich in `_kioskWeekArbeitsscheine()` (`index.html:2178`):
`window.__kioskAsErr = "HTTP"+r.status` bei `!r.ok`, danach `= (json===null) ? 'parse' : null`.
Gelesen und angezeigt in **`MonteurTafel`** (`:7855`, v3.9.852) als
`⚠️ AS:Fehler(<art>)`. Aufgerufen wird `_kioskWeekArbeitsscheine` nur fuer `lager_display`
(`:8362`, `_isLD ? _kioskWeekArbeitsscheine() : API.request("GET","/api/arbeitsscheine")`).

**Wie geprueft.** Nicht durch Danebenstehen: die Arbeitsschein-RPC wurde einzeln abgefangen und je
Lauf **eine** Ausfallart erzwungen, Rolle `lager_display`, alles Uebrige normal gefuellt, beide
Ansichten. 10 Faelle, jeder Route-Treffer mitgezaehlt (`treffer=1` ueberall — die Probe hat also
wirklich gegriffen):

| erzwungene Ausfallart | `window.__kioskAsErr` | am Schirm `?screen=monteure` | am Schirm `?screen=planung` |
|---|---|---|---|
| **fetch abgebrochen (Netz weg)** | **`<undefined>` — nie gesetzt** | nein | nein |
| HTTP 500 | `HTTP500` | **`AS:Fehler(HTTP500)`** | nein |
| HTTP 401 (RLS/JWT) | `HTTP401` | **`AS:Fehler(HTTP401)`** | nein |
| Antwort ist kein JSON | `parse` | **`AS:Fehler(parse)`** | nein |
| alles in Ordnung (Gegenprobe) | `null` | nein (richtig) | nein (richtig) |

**Ja, live gesetzt UND live angezeigt gesehen** — dreimal (500/401/parse), und in der „Stand"-Probe
(§4) ist `AS:Fehler(HTTP500)` nach dem gescheiterten 60-s-Nachladen von selbst am Schirm erschienen,
also nicht nur beim Erststart.

**Befund A1 — der Netzausfall setzt den Marker NICHT.** `_kioskWeekArbeitsscheine` ruft
`_authRetry(…)`, und `_authRetry` macht `const r = await fn();`. Wirft `fetch` (Netz weg, DNS,
abgebrochen), wickelt sich die ganze Funktion ab, **bevor** `if(!r||!r.ok)` erreicht wird; der
Aufrufer faengt mit `.catch(()=>null)`. Der Kommentar an der Stelle verspricht „RLS/**Netz**" — die
Netz-Haelfte kommt nicht an. Der **Zwilling** `_loadKioskFahrzeuge` hat dafuer einen echten
`try/catch` und meldete im selben Lauf sauber `FZ:Fehler(net)`; die Wochenplan-Diagnosezeile zeigte
das auch an. Genau die Form, gegen die v3.9.827 geschrieben wurde, bleibt also fuer die
Arbeitsscheine offen — und Netz weg ist am Wandpanel der wahrscheinlichste Ausfall.

**Befund A2 — auf `?screen=planung` wird der Marker gesetzt, aber nie gezeigt.** Weil
`_kioskWeekArbeitsscheine()` im Boot fuer JEDE `lager_display`-Sitzung laeuft, steht `__kioskAsErr`
auch auf dem Planungs-Wandpanel korrekt auf `HTTP401`/`HTTP500`/`parse`. Die Anzeige aus v3.9.852
sitzt aber nur in `MonteurTafel`. Das Versprechen „per Foto des Screens diagnostizierbar" gilt fuer
eine der beiden Tafeln. (Die Wochenplan-Diagnosezeile zeigt Version, FZ-Anzahl, Spez-Treffer und
`FZ:Fehler(...)` — den AS-Zustand nicht.)

---

## 4. „Sind die Daten aktuell bzw. wird ein Alter angezeigt?" — nein, angezeigt wird die UHR

Beide Tafeln zeigen `Stand HH:MM`. Das ist **kein Datenalter**, sondern `new Date()` eines
60-s-Intervalls:

* `WochenplanTafel`: `setInterval(()=>setStand(new Date()),60000)` — vollstaendig unabhaengig davon,
  ob `wpHistory` sich geaendert hat.
* `MonteurTafel`: `setStand(new Date())` laeuft **vor** dem Nachladen und unbedingt; das Nachladen
  uebernimmt danach nur bei `Array.isArray(raw)`.

Gemessen (80 s, Rolle `lager_display`, `?screen=monteure`; erster RPC-Aufruf liefert Daten, jeder
weitere HTTP 500):

```
t=0s   {"stand":"09:42","kacheln":16,"asErr":null,      "asFehlerAmSchirm":null,              "as_route_aufrufe":1}
t=79s  {"stand":"09:43","kacheln":3, "asErr":"HTTP500", "asFehlerAmSchirm":"AS:Fehler(HTTP500)","as_route_aufrufe":2}
```

**„Stand" ist von 09:42 auf 09:43 gewandert, obwohl die Aktualisierung mit HTTP 500 gescheitert ist.**
Wer die Tafel fotografiert, sieht eine frische Uhrzeit ueber moeglicherweise stundenalten Daten.
Der einzige echte Aktualitaetshinweis ist das `⚠️ AS:Fehler(...)` daneben — und das gibt es nur auf
`?screen=monteure` und nur fuer Status-/Parse-Fehler (§3).

**Gegenprobe zum Rueckgang 16 → 3 Kacheln:** das war **kein** Datenverlust, sondern die
Auto-Rotation Woche→Tag (Default AN, v3.9.691). Belegt: der aktive Knopf wechselte von „Woche" auf
„Tag" (`bg rgb(0,150,64)`), der Titel von „KW 40 · 28.09.–04.10." auf „Sa 03.10.2026", und nach einem
Klick auf „Woche" waren **alle 16 Kacheln wieder da**. Die Offline-Faehigkeit aus dem v3.9.827-Kommentar
haelt also — ich haette hier beinahe einen Befund erfunden.

---

## 5. Der Unterschied „Netz abgeklemmt" gegen „Netz laeuft ins 401"

Gemessen in Runde 1 mit je 18 Laeufen. Beide Lagen rendern die Tafel; der Unterschied ist, **welche
Diagnose ankommt**:

| | Netz abgeklemmt (`route.abort`) | Netz laeuft ins 401 |
|---|---|---|
| REST-Aufrufe | 15–16 abgebrochen, 0 durch | 0 abgebrochen, 16 durch |
| `__kioskFzErr` | `net` | `other` |
| Wochenplan-Diagnosezeile | `v3.9.934 · FZ:Fehler(net)` | `v3.9.934 · FZ:Fehler(other)` |
| `__kioskAsErr` | **`<undefined>`, 12 von 12** | `HTTP401` — aber nur 1 von 6 im Zeitfenster |
| Tafel | rendert, leer | rendert, leer |

Zum 401-Fall: dort schiebt sich `_authRetry` mit `_sbAuthRefresh()` und einem zweiten Versuch
dazwischen (Auth-Endpunkt ging ans echte Supabase und scheiterte), deshalb war der Marker zum
Zeitpunkt meiner Aufnahme oft noch nicht gesetzt. In der gezielten, abgefangenen Probe (§3) steht der
401-Fall dagegen **deterministisch** auf `HTTP401`. Der belastbare Unterschied bleibt: **Statusfehler
hinterlassen eine Spur, ein Netzabbruch hinterlaesst bei den Arbeitsscheinen keine.**

Die im Auftrag genannte Falle — `_sbGet` gibt bei 401/403 ein leeres Array im **Erfolgspfad** zurueck,
der Auffangzweig greift nie — habe ich in den Kiosk-Pfaden **nicht** als Ursache gefunden: die
Kiosk-Tafeln lesen nicht ueber `_sbGet`, sondern ueber die `kiosk_*`-RPCs mit eigener Fehlerbehandlung.
Sie steht aber weiterhin im Weg des Wochenplans: `_loadWeekplansFromRows` liest ueber
`API.getWeekplanRows()` → `_sbGet` und faengt das mit `_rlsLeer(wprs)` ab (v3.9.928). Diese
Absicherung habe ich **nicht** gegengemessen (§7).

---

## 6. MEIN KOEDER — was ich absichtlich kaputt gemacht habe, und ob es gemeldet wurde

Ohne diesen Nachweis ist alles oben wertlos, denn ein zaehlender Melder wird beim eigenen Ausfall
gruen. Vier Proben, in JEDEM der 24 + 18 Messlaeufe gefahren:

1. **Koeder „ausserhalb"** — ein `div` mit rotem Text, `position:fixed`, `left = innerWidth - 20`,
   Breite 400 px, ragt also 380 px ueber den rechten Rand. **MUSS** als „ausserhalb des Sichtfelds"
   gemeldet werden. → in **allen** Laeufen gemeldet.
2. **Koeder „Beschnitt"** — ein 600 px breiter `nowrap`-Text in einer 60×24-px-Box mit
   `overflow:hidden`. **MUSS** als „vom Elter abgeschnitten" gemeldet werden. → in **allen** Laeufen gemeldet.
3. **Gegenprobe Stille** — nach dem Entfernen beider Proben darf **kein** `__koeder`-Fund mehr
   auftauchen (sonst meldet der Melder Gespenster). → in **allen** Laeufen stumm.
4. **Koeder der FUELLUNG** — eine Zeichenkette `ZZKOEDERSAAT`, die nur aus meiner Saat stammen kann,
   steckt in einem Mitarbeiternamen, einem Kundennamen, einem Bauvorhaben und einer Bemerkung. Sie
   **MUSS** im Tafeltext stehen, sonst ist die Fuellung nicht angekommen und jede Beschnittzahl waere
   erfunden. → in allen 12 „harten" Laeufen gefunden.

Zusaetzlich fuer Probe A (§3) zwei eigene Koeder: der HTTP-500-Fall **muss** `__kioskAsErr` setzen
(tat er, 2/2), und der Gutfall **muss** `null` liefern (tat er, 2/2) — sonst haette die Aussage
„Netzausfall setzt nichts" auch von einer kaputten Probe kommen koennen.

Alle Urteile liefen ueber `scripts/messen.py` (`urteil`/`koeder`), also mit Verweigerung bei leerer
Grundgesamtheit. Genau das hat in Runde 1 die leere Tafel auffliegen lassen.

### Ein Fehlalarm aus dem eigenen Werkzeug, der hier stehen bleibt

Ich hatte einen Widerspruch: ein Melder sagte „0 Elemente unter der Kante", der andere „31". Beide
hatten recht — sie massen Sekundenbruchteile auseinander, und die Tafel schwingt (P1). Haette ich
nur einen der beiden gefahren, haette ich entweder den Befund verpasst oder ihn falsch begruendet.

### Und ein Befund, den mein Messaufbau selbst erzeugt hat

Nach 60 s legte sich ein roter Fehlerbalken ueber die Tafel:
`Uncaught TypeError: Cannot read properties of undefined (reading 'update')`, `index.html:8119`.
**Gegenprobe:** derselbe Lauf mit ERLAUBTEM Service Worker → kein Balken, 0 Fehler; mit
`service_workers="block"` → Balken, reproduzierbar. **Also mein Werkzeug, nicht die App.**

Die Ursache ist trotzdem notierenswert, weil sie eine echte Luecke zeigt. Zeile 8119:

```js
swUpdateTimer.current=setInterval(()=>reg.update().catch(()=>{}),60000);
if(_isKioskPath){_kioskWaitTimer=setInterval(function(){try{reg.update()… }catch(_we){}},TIME_HOUR);}
```

Die Zeile **darunter** hat ein `try/catch`, die 60-s-Zeile hat keins. Loest
`navigator.serviceWorker.register()` je mit einem falsy Wert auf (Service Worker per Richtlinie aus,
privates Fenster, ein Kiosk-/TV-Browser ohne SW), dann wirft das Wandpanel **jede Minute** einen
unbehandelten Fehler, und `window.onerror` malt einen roten, 40vh hohen Balken mit einem
„Schließen"-Knopf ueber die Tafel — vor einem Schirm, den niemand bedient. **Nicht live belegt, nur
der Mechanismus ist belegt.**

---

## 7. Was ich NICHT messen konnte, und warum

1. **Die echten Daten.** Kein DB-Zugriff (Sperre). Alle Inhaltszahlen stammen aus einer gesetzten
   Saat. Ob die echten Bauvorhaben-Namen so lang sind wie meine „harte" Stufe, ist **nicht** gemessen —
   die Befunde M1 (AS-Nummer) und P1 (Auto-Fit) haengen aber **nicht** an der Textlaenge: M1 tritt
   schon bei kurzen Namen auf, P1 ist eine Geometrie des Rahmens.
2. **Das echte Wandpanel.** Gemessen wurde Chromium auf Windows bei
   `deviceScaleFactor=1`. Ein Samsung-TV-Browser, eine andere Schriftmetrik oder ein Browser-Zoom ≠ 100 %
   verschieben die Umbruchschwelle — und P1 haengt genau an einer Umbruchschwelle. Die Zahl „76 px"
   gilt fuer 1366×768 bei Faktor 1.
3. **Der Service-Worker-Pfad.** Runde 1–4 lief mit blockierten Service Workern (gegen Reload-Schleifen);
   Runde 5/6 mit erlaubten. Das Kiosk-Selbstupdate (`controllerchange` → Reload, stuendliches
   `SKIP_WAITING`) und der taegliche Hardreset um 03:00 Wien (`KIOSK_DAILY_RESET_HOUR`) wurden **nicht**
   gemessen.
4. **`?screen=stempel`.** Nicht im Auftrag, nicht angefasst. Ebenso wenig die Kiosk-Hash-Schreibpfade
   `#planung/#monteure/#stempel`.
5. **Die Rolle `lager_display` gegen die echte DB.** Meine Saat setzt die Rolle im `localStorage`;
   der Boot-Abgleich gegen `public.users` (`_sbGetUsersSafe`) lief ins Leere bzw. ins 401. Ob eine
   echte `lager_display`-Sitzung dieselbe Rolle behaelt, ist nicht gemessen.
6. **`_rlsLeer` / der Wochenplan-Waechter aus v3.9.928.** Nicht gegengemessen — meine Antworten trugen
   die RLS-Marke nicht.
7. **Die WakeLock-Pfade** (`navigator.wakeLock.request('screen')`) — headless ohne Bedeutung.
8. **Rundenuebergreifende Vergleichbarkeit.** `index.html` wurde waehrend meiner Messung von einem
   anderen Lauf bearbeitet (sechs verschiedene Pruefsummen, 3.9.934 → 3.9.935). Jede Runde ist in
   sich konsistent (eingefrorene Kopie), rundenuebergreifende Zahlenvergleiche sind es nicht.
   Die tragenden Befunde M1, P1, P2 und A1/A2 wurden gegen die **juengste** gemessene Fassung
   (`4a2d8c20…` / `90328e82…`, v3.9.935) bestaetigt.

---

## Kurzfassung der Befunde

| Nr. | Befund | Ansicht | belegt |
|---|---|---|---|
| — | `?screen=` laeuft **nicht** unauthentifiziert — beide Tafeln brauchen eine Sitzung | beide | 12/12 Laeufe → Anmeldeschirm |
| **P1** | Auto-Fit schwingt bei 1366×768; in 26 von 60 Proben fehlen 76 px (letzte FZ-Zeile + ganze Fussleiste), `overflow:hidden`, nicht wegrollbar | `planung` | 60 Proben à 100 ms + Screenshot |
| **M1** | AS-Nummer bei 1366×768 hart abgeschnitten (kein Ellipsis), 16 von 16 Kacheln, `flexShrink:0` | `monteure` | 3/3, SW erlaubt, v3.9.935 |
| **A1** | `__kioskAsErr` wird bei **Netzausfall nie gesetzt** — `_authRetry` wirft vor der Marker-Zeile; der Zwilling `__kioskFzErr` kann es | beide | Probe A, 2/2 |
| **A2** | `__kioskAsErr` wird auf `?screen=planung` gesetzt, aber nie angezeigt (Anzeige sitzt nur in `MonteurTafel`) | `planung` | Probe A, 4/4 |
| **S1** | `Stand HH:MM` ist die Uhr, kein Datenalter — laeuft weiter, waehrend das Nachladen scheitert | beide | 80-s-Probe |
| **M2** | Lange Kundennamen verlieren bei 1920×1080 zwei Drittel (486 px Text in 162 px Zelle) | `monteure` | 30 Funde |
| **P2** | Bei 3840×2160 nutzt die Tafel 35–36 % der Schirmhoehe (Massstab bei 1.25 gedeckelt) | beide | 6 Faelle |
| **(X)** | Roter Fehlerbalken alle 60 s, wenn `serviceWorker.register()` falsy aufloest (`:8119` ohne `try/catch`, Zeile darunter hat eins) — **durch meinen Messaufbau ausgeloest, nicht live belegt** | beide | Gegenprobe SW erlaubt/geblockt |

Messskripte und Rohdaten liegen im Scratchpad dieser Sitzung
(`kiosk_messen.py`, `kiosk_voll.py`, `kiosk_probe.py`, `kiosk_stand.py`, `kiosk_modus.py`,
`kiosk_sw.py`, `kiosk_bestaetigen.py`, `kiosk_widerspruch.py`, `kiosk_schwingung.py`,
zugehoerige `*.json` und die Screenshots). Nichts davon liegt im Repo.
