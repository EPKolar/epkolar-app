# Bedienelemente ohne zugaenglichen Namen — die Menge, die v3.9.957 und v3.9.958 AUSGELASSEN haben

Gemessen an einer EINGEFRORENEN Abschrift von `index.html`:

* **3708615 Bytes**, SHA256 `254486fa2c4ad966344b3b56d4bce78ca364d9044602971140a40c6dd815c95d`
* Stand **v3.9.960**, `HEAD = ce397e9`, plus 4 noch nicht eingetragene Zeilen in `index.html`.

🔴 **Warum eine Abschrift.** Ich habe um 08:11 mit 3.671.906 Bytes (v3.9.959, `HEAD = e6202e5`) angefangen. Um 12:00 hatte die Datei 3.708.615 Bytes und v3.9.960. Zwei Laeufe derselben Messung gaben deshalb zwei verschiedene Zahlen (295/443/47/13 und 297/442/46/13 Knoepfe je Namensbefund). Eine Messung an einem Baum, an dem gearbeitet wird, ist keine Messung — und ZEILENNUMMERN aus dem ersten Lauf zeigen in der neuen Datei woandershin. Alles unten ist gegen die oben gehashte Abschrift gemessen, in EINEM Lauf. Nachmessen mit demselben Stand:

```
BEDIENELEMENTE_PFAD=<abschrift> python scripts/bedienelemente_scan.py
```
An `index.html` wurde NICHTS geaendert (`git diff --stat -- index.html` ist leer), keine bestehende Pruefung angefasst, kein aenderndes git-Kommando gelaufen, kein Schreibzugriff auf die Datenbank. Neu sind genau drei Dateien: dieser Bericht, `scripts/bedienelemente_scan.py` (das Messgeraet), `scripts/bedienelemente_gegenprobe_v957_958.py` (die Gegenprobe gegen die zwei alten Abtaster) und `scripts/bedienelemente_bericht.py` (der Erzeuger dieses Berichts).

## 0. Die Zahl

| Klasse | Gemessen | Befund |
| --- | --- | --- |
| (a) Knopf/Verweis, der NIE ein Wort zeigt und keinen Namen in den Props hat | 14 | 🔴 **14 Befunde** |
| (a) Name haengt an einer Variable oder einem Zweig, der leer sein kann | 53 | 🔴 **3 real** · 11 nur in einem Zustand · 1 unklar · 38 kein Befund |
| (b) Knopf mit Emoji PLUS Text | 273 | kein Urteil — schwaechere Klasse, getrennt gefuehrt |
| (c) `onClick` auf einem Element, das kein Bedienelement ist | 220 | 29 Klick-Schlucker abgezogen → 191 echte Flaechen, davon 🔴 **133 ohne `role`+`tabIndex`** |
| (c) `input`/`select`/`textarea` | 532 | 🔴 **461 ohne `label`, `aria-label`, `title` oder `htmlFor`-Verbindung** |
| (d) mit der rohen DOM-Schnittstelle gebaut — von JEDER React-Messung unerreicht | 27 | 🔴 **8 Befunde** (2 Knoepfe, 4 `input`, 2 `select`/`textarea`) |

### 🔴 Und zuerst: v3.9.957/958 sind NICHT vollstaendig

Beide Riegel behaupten, alle 150 Knoepfe mit reinem Symbol- oder Emoji-Inhalt tragen einen Namen. **14 Knoepfe bzw. Verweise zeigen NIE ein Wort und tragen keinen Namen**, und **alle 14 sind fuer beide Abtaster unsichtbar**.

🔴 Das ist GEMESSEN, nicht geschlossen. `scripts/bedienelemente_gegenprobe_v957_958.py` bildet die Suchlogik beider Abtaster zeichengenau nach und setzt sie auf denselben Text. Die Eichung dieser Gegenprobe: die nachgebildete v958-Logik findet **genau 150** Knoepfe, alle als benannt — dieselbe Zahl, die der Riegel behauptet. Die Nachbildung stimmt also mit dem Original ueberein, und erst dadurch heisst „nicht gesehen" etwas.

🔴 Und eine eigene Korrektur: die erste Fassung dieser Gegenprobe verglich ueber die ZEILENNUMMER. In einer Datei mit 1300 Zeichen pro Zeile stehen mehrere Knoepfe auf derselben Zeile — sie meldete daraufhin, v958 sehe Z18442 und halte sie fuer benannt, obwohl der Treffer zu einem ANDEREN Knopf derselben Zeile gehoerte. Verglichen wird jetzt ueber die Zeichenposition. Die Zeilennummer ist in dieser Datei kein eindeutiger Schluessel.

Die Ursachen, je Stelle ausgezaehlt (sie ueberschneiden sich):

| Ursache | Anzahl | Stellen |
| --- | --- | --- |
| **Die `h(`-Schreibweise**. Beide Abtaster suchen `createElement('button'`. Der lokale Kuerzel `h(` (`const h=React.createElement`, 13 mal vergeben) kommt **97 mal** in Knopfstellung vor und wurde NIE gemessen. | 5 | Z12273, Z12275, Z27736, Z27737, Z29511 |
| **Nur doppelte Anfuehrungszeichen.** v958 liest den Inhalt mit `re.match(r'"((?:[^"\\]\|\\.)*)"\s*\)')`. Ein einfach gesetzter Inhalt (`,'✕')`) faellt durch. | 7 | Z12273, Z12275, Z22143, Z24005, Z24358, Z24954, Z27737 |
| **Der Inhalt ist ein Ternaer, kein Literal.** Beide Abtaster suchen ein Zeichenketten-LITERAL. `isOn?"✓":"·"` ist keines — und BEIDE Zweige sind ein Zeichen ohne Wort. | 5 | Z14623, Z18442, Z18454, Z27736, Z28829 |
| **Gar kein `button`.** Ein `a` mit `href` und dem Inhalt `"🔗"`. Eine Vorlesehilfe sagt dort „Link" und sonst nichts. | 1 | Z20941 |

Zum Umfang, damit die Zahl nicht groesser klingt als sie ist: **174** Knoepfe haben als ganzen Inhalt EIN Symbol-/Emoji-Literal (das ist die Menge, die v957/v958 gemeint haben), und **8** davon tragen keinen Namen. Die restlichen 6 der 14 sind Ternaere und der eine `a` — die lagen auch nach dem Wortlaut der beiden Riegel nie in ihrem Umfang, wohl aber in ihrer Behauptung.

🟡 Eine Bauform, die in BEIDE Richtungen taeuscht: das `\s*\)` in v958 verlangt, dass der Inhalt das LETZTE Argument ist. Ein Knopf `,"🗑️ ",isMob?"Löschen":""` faellt deshalb durch — und war bis v3.9.960 ein echter Befund (siehe Abschnitt 2). Umgekehrt ist ein Knopf `,'🏖️',h('div',{},'Urlaub')` (Z7669) BENANNT, obwohl sein erstes Kind ein Emoji ist. Wer nur das erste Kind ansieht, irrt in beide Richtungen; dieser Abtaster liest alle Kinder und bei einem verschachtelten Element auch dessen Kinder.

Diese 14 gehoeren nach v3.9.957/958, nicht in diesen Auftrag. Sie stehen hier, weil ich sie beim Messen der Nachbarmenge gefunden habe.

| Zeile | Ansicht | Form | Tag | Inhalt | Was das onClick tut | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- | --- |
| 12273 | KVZulagenReport | h( | button | `'◀'` | `_shiftYm(-1)` - ein Monat zurueck | **Voriger Monat** |
| 12275 | KVZulagenReport | h( | button | `'▶'` | `_shiftYm(1)` - ein Monat vor | **Nächster Monat** |
| 14623 | AdminPanel | createElement | button | `isOn?"✓":"·"` | `isOn?"✓":"·"`, `upd[u.id][tk]=!isOn` - ein Schalter fuer eine Benachrichtigung. BEIDE Zustaende sind Zeichen ohne Wort. | **ENTSCHEIDUNG: der Name muss sagen, WELCHE Benachrichtigung (`tk`) fuer WELCHEN Benutzer (`u.id`) - beides steht im `onClick`, die Wortwahl nicht. ICH ENTSCHEIDE DAS NICHT.** |
| 18442 | VPlan | createElement | button | `l.visible?"👁️":"👁️‍🗨️"` | `l.visible?"👁️":"👁️‍🗨️"`, `toggleLayer(l.id)` - ein Umschalter, beide Zustaende ein Emoji. | **bedingt, wie die sechs Umschalter aus v3.9.957: `l.visible?"Ebene ausblenden":"Ebene einblenden"`** |
| 18454 | VPlan | createElement | button | `isPlanFreigegeben(pl.id)?"🔗":"📤"` | `isPlanFreigegeben(pl.id)?"🔗":"📤"`, `togglePlanFreigabe(pl)` | **bedingt: `isPlanFreigegeben(pl.id)?"Freigabe zurückziehen":"Plan freigeben"` - die Richtung steht im Namen der Funktion, die WORTE sind eine ENTSCHEIDUNG** |
| 20941 | VMaterial | createElement | a | `"🔗"` | KEIN `button`, sondern ein `a` mit `href:shopLink` und dem Inhalt `"🔗"`. Ein Verweis, dessen ganzer Text ein Emoji ist, hat fuer eine Vorlesehilfe keinen Namen - sie sagt „Link". | **abgelesen aus dem Zusammenhang (Artikelzeile, `shopLink`): „Artikel im Shop öffnen"** |
| 22143 | WeekPlan | createElement | button | `'✕'` | `setCellPick(null);setSelCells(null)` - schliesst die Zellenauswahl | **Auswahl schließen** |
| 24005 | ASChecklistPanel | createElement | button | `'×'` | `del(item.id)` in der Checklisten-Zeile | **Eintrag löschen** |
| 24358 | UrlaubsantragPanel | createElement | button | `'❌'` | `entscheiden(a.id,'abgelehnt')` | **Ablehnen** |
| 24954 | FahrtenbuchPanel | createElement | button | `'🗑'` | `del(e.id)` in der Fahrtenbuch-Zeile | **Eintrag löschen** |
| 27736 | load | h( | button | `imeiBusy?'…':'✓'` | `imeiBusy?'…':'✓'`, `_imeiSpeichern(row.f.id)` - BEIDE Zweige sind ein Zeichen ohne Wort. Kein Umschalter: der eine Zweig ist nur der Zustand WAEHREND des Speicherns. Der Knopf zeigt also nie ein Wort. | **IMEI speichern** |
| 27737 | load | h( | button | `'✕'` | `setImeiFid('');setImeiVal('')` - verwirft die IMEI-Eingabe | **Abbrechen** |
| 28829 | _kmFromBeleg | createElement | button | `t.erledigt?"✅":"⬜"` | `t.erledigt?"✅":"⬜"`, setzt `erledigt` um - ein Umschalter, beide Zustaende ein Emoji. | **bedingt: `t.erledigt?"Als offen markieren":"Als erledigt markieren"`** |
| 29511 | BauprovisorienView | h( | button | `"✕"` | `setVerrId(null);setVerrBetrag("");setVerrFile("")` | **Abbrechen** |

Von diesen 14 sind **drei ein Name, den ich NICHT entscheide** (Z14623, Z18454 teilweise, Z28829 teilweise): dort ist die Handlung aus dem `onClick` ablesbar, aber die WORTE waeren eine Wahl. Z18442/Z18454/Z28829/Z14623 sind ausserdem **Umschalter** — genau die Bauform, fuer die v3.9.957 sechs bedingte Namen gesetzt hat. Ein FESTER Name ist dort in einem der zwei Zustaende falsch.

## 1. Koeder-Nachweis

Jede Zahl unten sucht etwas und meldet gruen, wenn sie es nicht findet — die gefaehrlichste Bauform. Also wird je Klasse ein Fall EINGESETZT, der gefunden werden MUSS. Die vier **Gegenproben** messen die andere Richtung: ein Zaehler, der ALLES meldet, schlaegt bei jedem Koeder an und ist trotzdem kaputt.

| Koeder | Ergebnis |
| --- | --- |
| `Knopf, dessen Inhalt eine leere Variable sein kann` | ANGESCHLAGEN |
| `Knopf, der NIE Text zeigt (reines Symbol, ohne Namen)` | ANGESCHLAGEN |
| `Knopf mit Text UND leerem Zweig ("nur mobil benannt")` | ANGESCHLAGEN |
| `Knopf mit Emoji PLUS Text` | ANGESCHLAGEN |
| `div mit onClick, ohne role und tabIndex` | ANGESCHLAGEN |
| `input ohne jeden Namen` | ANGESCHLAGEN |
| GEGENPROBE die h(-Schreibweise wird ueberhaupt gesehen | ANGESCHLAGEN |
| GEGENPROBE ein EINFACH gesetzter Inhalt wird gesehen | ANGESCHLAGEN |
| GEGENPROBE ein BENANNTER Knopf wird NICHT gemeldet (Falschmeldung) | ANGESCHLAGEN |
| GEGENPROBE ein Knopf mit Text in einem KIND wird NICHT gemeldet | ANGESCHLAGEN |

Alle 10 angeschlagen. Zusaetzlich: `scripts/code_scan.py` hat seine EICHPROBE bestanden (der Abtaster verweigert sonst die Auskunft), und die Grundgesamtheit ist nicht leer: **7545** Elementstellen mit literalem Tag-Namen, davon **798** `button` (701 in der `createElement`-Form, 97 als `h(`).

### 🟡 Eine Gegenprobe, die ich fast weggelassen haette

Ich wollte in Abschnitt 6 schreiben: „ein leeres `title:""` kommt in der Datei nicht vor". Vor dem Hinschreiben gemessen — es kommt **4 mal** vor (Z3665, Z18364, Z18366, Z18476). Alle vier sind DATENFELDER (`{label:…,type:"mangel",title:"",…}` — der Titel eines Tickets), keine Eigenschaft eines Elements. Die Behauptung war also falsch und der Befund harmlos. Aber sie hat eine echte Schwaeche aufgedeckt:

`hat_namen()` sucht `title:` FLACH im Props-Text. Ein `title:` kann tiefer stehen — Z18476 hat eines in einem Datenobjekt INNERHALB des `onClick`. Dann meldet der flache Zaehler den Knopf als benannt, ohne dass er einen Namen hat. Das ist dieselbe Fehlerform, an der die erste v958-Messung dreimal gescheitert ist, nur eine Ebene hoeher.

Gemessen mit einer zweiten, strengen Pruefung (`hat_namen_streng()`, Schluessel nur auf Tiefe 1, mit eigenem Koeder und Gegenkoeder): von 819 `button`/`a` gelten **299** flach als benannt und **296** streng. Die Differenz ist **3** — Z14257, Z18476, Z23852. Alle drei tragen sichtbaren Text (`"📥 CSV"`, `"+ Vorlage hinzufügen"`, `"🗑️ Lokale Daten löschen"`), sind also auch streng gemessen benannt. **Kein neuer Befund, aber die Zahlen in diesem Bericht haengen nicht daran.**

🔴 Die Abtaster von v3.9.957 und v3.9.958 haben dieselbe Schwaeche, und v957 hat sie schlimmer: er nimmt einen 900-Zeichen-Schnitt RUECKWAERTS und sucht darin `title:`. Dieser Schnitt kann in einen ganz anderen Knopf hineinreichen.

Gegenprobe auf die Aufteilung: 297 `benannt-prop` + 442 `benannt-text` + 46 `manchmal-stumm` + 13 `immer-stumm` = 798. Die Summe geht auf; kein Knopf faellt zwischen die Klassen.

## 2. Klasse (a) — der Inhalt ist eine Variable, die leer sein kann

53 Stellen gemessen. Der Abtaster kann NICHT entscheiden, ob eine Variable leer wird — das ist je Stelle gelesen. Entscheidend war dabei ein Muster, das der Abtaster nicht sieht: **ein WAECHTER**. `p.telefon&&React.createElement('a',…,p.telefon)` rendert das Element gar nicht, wenn der Wert fehlt. Sieben Stellen, die nach einer leeren Variable aussehen, sind so bewacht.

🟢 **Eine vierte reale Stelle ist waehrend der Messung BEHOBEN worden.** Z19889 (`VBautag`) hatte die Kinder `"🗑️ "` und `isMob?"Löschen":""` — am Schreibtisch blieb dauerhaft nur der Papierkorb. In der Abschrift von 12:00 tragen dieselbe Zeile ein `title: "Eintrag löschen"` und ein `'aria-label': "Eintrag löschen"`, mit einem v3.9.960-Kommentar, der genau diesen Mechanismus beschreibt („Der Inhalt ist das Symbol plus `isMob?"Löschen":""` … hier sind es zwei Kinder"). Ich habe den Befund um 08:11 gemessen und um 12:00 nicht mehr — er stand also nicht in meinem Bericht, weil er weg ist, nicht weil ich ihn nicht gefunden hatte. Der Geschwisterknopf daneben (`editEntry`, `"✏️ ",isMob?"Bearbeiten":""`) traegt jetzt ebenfalls ein `title`.

### 🔴 REAL — die Stelle wird stumm — 3

| Zeile | Ansicht | Tag | Inhalt | Warum | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- |
| 13413 | VBueroExport | button | `isMob?_wn.split(" ").pop():_wn` | `const _wn=w.name\|\|""` - ein Vorgabewert, der die LEERE Zeichenkette ist. Ist `w.name` leer, ist der Knopf vollstaendig leer. Auf dem Telefon zusaetzlich `_wn.split(" ").pop()`, und `"".split(" ").pop()` ist wieder `""`. | **Mitarbeiter ein-/ausblenden** |
| 16439 | VForm | button | `t.i " " isMob?"":" "+t.l cnt>0?(" ("+cn…` | Die Kinder sind `t.i`, `" "`, `isMob?"":" "+t.l`. Auf dem TELEFON ist der Textzweig die leere Zeichenkette - dann bleibt nur das Emoji, dauerhaft, nicht nur waehrend einer Arbeit. | **der Reitername `t.l` - auf dem Telefon ist er im Bild weg, im Namen muss er bleiben** |
| 24921 | FahrtenbuchPanel | button | `showForm?'✕':'+ Fahrt'` | `showForm?'✕':'+ Fahrt'` - ein UMSCHALTER, genau die Bauform, fuer die v3.9.957 sechs bedingte Namen gesetzt hat. Dieser siebte wurde nicht erfasst. | **der Name muss an DERSELBEN Bedingung haengen: `showForm?"Abbrechen":"Fahrt hinzufügen"`** |

### 🟡 NICHT ENTSCHEIDBAR — ich entscheide das nicht — 1

| Zeile | Ansicht | Tag | Inhalt | Warum | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- |
| 19829 | VBautag | button | `w.vorname\|\|w.n` | `w.vorname\|\|w.n` aus `_maWaehlbar((monteure\|\|MONT))` - beide Felder kommen aus der Datenbank. Tragen alle Monteure einen `vorname` ODER ein `n`, ist der Knopf immer benannt. Das steht nicht im Code, und ich habe die Tabelle nicht gelesen - ICH ENTSCHEIDE DAS NICHT. | **der Mitarbeitername; ob er leer sein kann, sagt die Tabelle** |

### 🟡 Stumm nur, WAEHREND eine Arbeit laeuft (schwaechere Klasse) — 11

| Zeile | Ansicht | Tag | Inhalt | Warum | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- |
| 7168 | LoginScreen | button | `loading?React.createElement(_react.Frag…` | `loading?<Fragment><span/> "Wird angemeldet…"</>:"🔐 Anmelden"` - BEIDE Zweige tragen Text. Der Abtaster meldet die Stelle nur, weil `_react.Fragment` kein literaler Tag-Name ist; er kann nicht hineinsehen. FALSCHMELDUNG meines Abtasters, kein Befund. | **(kein Bedarf)** |
| 9917 | KVRulesConfig | button | `saving?'…':'💾 Speichern'` | `saving?'…':'💾 Speichern'` | **Speichern** |
| 9974 | StempelPauseConfig | button | `saving?"…":"💾 Speichern"` | `saving?"…":"💾 Speichern"` | **Speichern** |
| 10221 | MitarbeiterView | button | `pwBusy?"⏳ …":"Passwort ändern"` | `pwBusy?"⏳ …":"Passwort ändern"` | **Passwort ändern** |
| 23809 | VerbindungView | button | `pwBusy?React.createElement('span',{},Re…` | Spinner-`span` statt Text, waehrend `pwBusy` | **Passwort ändern** |
| 23889 | SmokeTestPanel | button | `busy&&kind==="smoke"?React.createElemen…` | Spinner-`span` waehrend `busy&&kind==="smoke"` | **Smoke-Tests** |
| 23890 | SmokeTestPanel | button | `busy&&kind==="integrity"?React.createEl…` | Spinner-`span` waehrend `busy&&kind==="integrity"` | **Integrität** |
| 24098 | ASKommentarePanel | button | `sending?'…':'Senden'` | `sending?'…':'Senden'` | **Senden** |
| 24191 | WorkerNfcPanel | button | `busy?'…':'💾 Chip zuordnen'` | `busy?'…':'💾 Chip zuordnen'` | **Chip zuordnen** |
| 24937 | FahrtenbuchPanel | button | `saving?'⏳ …':'💾 Speichern'` | `saving?'⏳ …':'💾 Speichern'` | **Speichern** |
| 29510 | BauprovisorienView | button | `busy?"…":"✓ Verrechnet"` | `busy?"…":"✓ Verrechnet"` | **Verrechnen** |

### 🟢 Bewacht — das Element rendert nur mit Wert — 8

| Zeile | Ansicht | Tag | Inhalt | Warum | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- |
| 6960 | KundenPortal | a | `"📞 " p.telefon` | `p.telefon&&React.createElement(...)` | — |
| 6961 | KundenPortal | a | `"✉️ " p.emailKunde\|\|p.email_kunde` | `(p.emailKunde\|\|p.email_kunde)&&...` | — |
| 7071 | KundenPortal | a | `p.telefon` | `p.telefon&&...` | — |
| 7072 | KundenPortal | a | `p.emailKunde\|\|p.email_kunde` | `(p.emailKunde\|\|p.email_kunde)&&...` | — |
| 11776 | sharePdf | a | `v` | `const v=String(_jr[k]\|\|"").trim(); if(!v)return;` | — |
| 11777 | sharePdf | a | `_em` | `const _em=...; if(_em){ ... }` | — |
| 14571 | AdminPanel | a | `_kurz(s.datanorm_url.replace(/https?:\/…` | `s.datanorm_url&&...`, Inhalt `_kurz(url,60)` | — |
| 20600 | VMaterial | button | `MAT_STATUS[nextStatus].i " " MAT_STATUS…` | `nextStatus&&...`, Inhalt `MAT_STATUS[nextStatus].l` | — |

### 🟢 Lokale Hilfsfunktion — alle Aufrufer uebergeben ein Literal — 4

| Zeile | Ansicht | Tag | Inhalt | Warum | Namensvorschlag (abgelesen) |
| --- | --- | --- | --- | --- | --- |
| 10180 | MitarbeiterView | button | `text` | `_navBtn(tab,text,color)`; 3 Aufrufer, alle mit einem Literal (Z10189, Z10204, Z10213) | — |
| 22684 | AbsView | button | `icon+" "+text` | `_btn(handler,color,bg,border,icon,text)`; 2 Aufrufer, beide mit einem Literal (Z22688, Z22689) | — |
| 24576 | ChefDashboard | button | `label+' →'` | `_drill(label,tab)`; 12 Aufrufer, alle mit einem Literal (Z24706-Z24845) | — |
| 27378 | FahrtenbuchView | button | `label` | `_tabBtn(k,label)`; 3 Aufrufer, alle mit einem Literal (Z27387, Z27388, Z27389) | — |

### 🟢 Wert aus einem Literal-Feld im Code — 26

Der Wert kommt aus einem Literal-Feld einer Aufzaehlung im Code (`.map` ueber ein Feld mit festen `l`/`label`-Werten). Er kann nicht leer werden, solange die Aufzaehlung im Code steht. Kein Befund - aber ein Vertrag, den nichts PRUEFT.

| Zeile | Ansicht | Tag | Inhalt |
| --- | --- | --- | --- |
| 6900 | KundenPortal | button | `t.i " " t.l` |
| 9544 | App | button | `c.i " " c.l` |
| 9553 | App | button | `s` |
| 11373 | sharePdf | button | `l` |
| 11389 | sharePdf | button | `React.createElement('span',{style:{fontSize:isMob?1…` |
| 11447 | sharePdf | button | `chip.label` |
| 13531 | VBueroExport | button | `_t[1]+" "+_t[2]` |
| 14019 | AdminPanel | button | `t.l` |
| 15130 | HomeView | button | `a.i " " a.l` |
| 15707 | ProjList | button | `t.l " " React.createElement('span', { style: {fontV…` |
| 15853 | ProjectShell | button | `React.createElement('span', { 'aria-hidden': "true"…` |
| 16034 | VExport | button | `x.primary?"📥 Exportieren":x.warn?"🔒 Archivieren":"📥…` |
| 18421 | VPlan | button | `t.l` |
| 19195 | VFotos | button | `c.i " " c.l` |
| 19836 | VBautag | button | `cat.l` |
| 19839 | VBautag | button | `chip` |
| 20322 | VMaterial | button | `o.l` |
| 20458 | VMaterial | button | `v.i " " v.l` |
| 21209 | VOffa | button | `"📥 " x.t` |
| 21951 | WeekPlan | button | `v.l` |
| 22013 | WeekPlan | button | `React.createElement('span',{style:{fontSize:13,font…` |
| 22147 | WeekPlan | button | `React.createElement('span',{style:{fontSize:13,font…` |
| 24637 | ChefDashboard | button | `_t[1]+' '+_t[2]` |
| 25844 | ZeiterfassungView | button | `t.l` |
| 26115 | ZeiterfassungView | button | `d " " dateFmt(i)` |
| 27406 | FahrtenbuchView | button | `pz[1]` |

**Zusammen mit den 14 aus Abschnitt 0** sind in Klasse (a) **17 Stellen ohne Namen** (14 nie benannt + 3 real) und **1 nicht entscheidbar**.

## 3. Klasse (b) — Emoji PLUS Text

**273 Knoepfe.** Diese Klasse ist SCHWAECHER, und ich urteile nicht: jeder dieser Knoepfe HAT einen Namen. Die Frage ist nur, ob der Text allein die Handlung benennt — „PDF" sagt nicht, was passiert. Das ist eine Wortwahl, keine Messung, und sie gehoert nicht mir.

Was ich stattdessen gemessen habe, weil es entscheidbar ist: welche dieser Knoepfe ein Wort tragen, das aus sich heraus keine Handlung nennt. Ein Substantiv ohne Verb. Die Liste ist eine VORLAGE zum Ansehen, kein Befund:

| Zeile | Ansicht | Sichtbar | onClick (die Handlung steht hier) |
| --- | --- | --- | --- |
| 7683 | _submitAntrag | `Weiter →` | ()=>{if(aBis<aVon){setAMsg('Das Bis-Datum liegt vor dem V… |
| 9765 | App | `⚙️ Mehr` | ()=>setMoreOpen(!moreOpen), style: {padding:"11px 16px",b… |
| 11424 | sharePdf | `📄 PDF` | ()=>genAsPdf(asScannedAs), style: {...bpS,background:"lin… |
| 11797 | sharePdf | `📄 PDF` | ()=>genAsPdf(form), style: {...beS,flex:1}} |
| 12646 | PZEView | `📊 Excel` | _xls,style:{...btnS,background:COLORS.SUCCESS,color:'#fff… |
| 12647 | PZEView | `📄 PDF` | _pdf,style:{...btnS,background:COLORS.INFO,color:'#fff',b… |
| 12969 | VBueroExport | `📥 Excel` | async(e)=>{e.stopPropagation();const _gd=getProjectData(p… |
| 14257 | AdminPanel | `📥 CSV` | ()=>{ const _cf=v=>{let s=String(v==null? |
| 14604 | AdminPanel | `Alle ⇆` | ()=>{const allOn=Object.values(notifPrefs).every(up=>Obje… |
| 15343 | HomeView | `Alle →` | ()=>onNav("projekte"), style: {...bsS(),padding:"4px 10px… |
| 15397 | HomeView | `Alle →` | ()=>onNav("arbeitsscheine"), style: {...bsS(),padding:"4p… |
| 15918 | VDash | `📷 + Foto` | ()=>setView("fotos"), style: {padding:"7px 12px",borderRa… |
| 15952 | VDash | `Alle →` | ()=>setView("fotos"), style: {...bsS(),padding:"4px 10px"… |
| 16682 | VCheck | `📄 PDF` | ()=>_genChecklistPdf(selCl,p,ww), title: "Checkliste als … |
| 16992 | VMang | `📥 Export` | ()=>{const hdrs=["Mangel","Ebene","Prio","Status","Verant… |
| 17615 | TicketDetail | `📄 PDF` | ()=>_genTicketPdf(ticket,plans,monteure,layers,proj), tit… |
| 18402 | VPlan | `📥 Export` | exportTickets, style: xBtn("xls")} |
| 19867 | VBautag | `📊 Excel` | exportXls, style: xBtn("xls")} |
| 21213 | VOffa | `📧 Mail` | (kein onClick) |
| 21954 | WeekPlan | `📥 Excel` | ()=>{ /* v3.9.676: bvh-Filter bleibt hier ABSICHT |
| 22326 | WeekPlan | `📊 Excel` | exportXls, style: {...xBtn("xls"),flex:1,justifyContent:'… |
| 22327 | WeekPlan | `🖨️ PDF` | _wpPrintPlan, style: {...xBtn("pdf"),flex:1,justifyConten… |
| 22329 | WeekPlan | `📊 Excel` | exportXls, style: xBtn("xls")} |
| 22330 | WeekPlan | `🖨️ PDF` | _wpPrintPlan, style: xBtn("pdf"), title: "Wochenplan als … |
| 22703 | AbsView | `🖨️ PDF` | ()=>window.print(), style: {...xBtn("pdf"),fontSize:12}, … |
| 22905 | AbsView | `✅ Alle` | ()=>approveAll(name), style: {...bgS,padding:"3px 8px",fo… |
| 22906 | AbsView | `❌ Alle` | ()=>rejectAll(name), style: {...bdS,padding:"3px 8px",fon… |
| 22983 | AbsView | `📊 Excel` | exportAbsCsv, style: xBtn("xls")} |
| 22984 | AbsView | `🖨️ PDF` | ()=>window.print(), style: xBtn("pdf"), title: "Drucken /… |
| 22985 | AbsView | `📤 Server` | exportToServer, style: xBtn("server")} |
| 23005 | AbsView | `◀ Zurück` | ()=>setTlWeekOff(p=>p-WEEKS), style: {...bsS(),padding:"5… |
| 24357 | UrlaubsantragPanel | `✅ OK` | ()=>entscheiden(a.id,'genehmigt'),style:{...bgS,padding:'… |
| 24922 | FahrtenbuchPanel | `📥 XLS` | exportCsv,style:{...xBtn("xls"),fontSize:11,padding:'4px … |
| 24923 | FahrtenbuchPanel | `🖨️ PDF` | ()=>window.print(),style:{...xBtn("pdf"),fontSize:11,padd… |
| 25147 | AuswertungView | `🖨️ PDF` | ()=>window.print(), style: {...xBtn("pdf"),fontSize:UI.fM… |
| 25965 | ZeiterfassungView | `📊 Excel` | exportAllXls,style:xBtn("xls")} |
| 25966 | ZeiterfassungView | `🖨️ PDF` | ()=>window.print(),style:xBtn("pdf"),title:"Drucken / als… |
| 26107 | ZeiterfassungView | `🖨️ PDF` | ()=>window.print(),style:xBtn("pdf"),title:"Drucken / als… |
| 26125 | ZeiterfassungView | `🖨️ PDF` | ()=>window.print(),style:xBtn("pdf"),title:"Drucken / als… |
| 27308 | FahrtenbuchView | `🗺 Karte` | function(){_zeigeAufKarte(s);},style:Object.assign({},bsS… |
| 27392 | FahrtenbuchView | `📥 Excel` | exportFahrten,title:'Excel-Export',style:Object.assign({}… |
| 27393 | FahrtenbuchView | `📄 PDF` | exportFahrtenPdf,title:'PDF-Export (A4 quer)',style:Objec… |
| 27776 | load | `⌖ Alle` | _fitAll,title:'Alle Fahrzeuge auf der Karte einpassen',st… |
| 28255 | _kmFromBeleg | `📊 Excel` | ()=>{const h=["Kennzeichen","Marke/Modell","Typ","Fahrer"… |
| 28256 | _kmFromBeleg | `🖨️ PDF` | ()=>window.print(), style: xBtn("pdf"), title: "Drucken /… |
| 28257 | _kmFromBeleg | `← Zurück` | ()=>setSel(null), style: bsS()} |
| 29162 | VGefahrstoff | `← Zurück` | goBack,style:{...bsS(),padding:isMob?"8px 12px":"5px 10px… |
| 29369 | BauprovisorienView | `← Zurück` | ()=>setSub("liste"),style:{border:"1px solid "+V.bd,backg… |
| 29764 | WerkzeugView | `📊 Excel` | exportWz, style: xBtn("xls")} |
| 29765 | WerkzeugView | `🖨️ PDF` | ()=>window.print(), style: xBtn("pdf"), title: "Drucken /… |

Die vollstaendige Liste aller 273 Stellen dieser Klasse steht nicht hier, sondern kommt auf Zuruf aus `python scripts/bedienelemente_scan.py json` (Schluessel `b`). Eine Liste mit 273 Zeilen in einem Bericht liest niemand, und ein Urteil steht mir hier nicht zu.

## 4. Klasse (c) — andere Bedienelemente als `button`

### 4a. `onClick` auf einem Element, das kein Bedienelement ist

**220 Stellen** tragen ein `onClick` auf einem Tag, das kein `button`/`a`/`input`/`select` ist.

🔴 Davon sind **29 gar keine Bedienelemente**, sondern KLICK-SCHLUCKER: `onClick: e=>e.stopPropagation()` verhindert nur, dass der Klick beim Elternelement ankommt. Ein `role`/`tabIndex` dort waere FALSCH — er baute einen Halt in der Tastaturreihenfolge, der nichts tut. Dieselbe Sorte Ausnahme wie die Statusanzeige in v3.9.957. Sie sind abgezogen.

Bleiben **191 echte Bedienflaechen**:

|  | Anzahl | Bedeutung |
| --- | --- | --- |
| mit `role` UND `tabIndex` | 58 | 🟢 bedienbar mit der Tastatur |
| ohne `role` und/oder `tabIndex` | 133 | 🔴 **fuer die Tastatur und fuer eine Vorlesehilfe gar kein Bedienelement** |
| mit `onKeyDown`/`onKeyPress`/`onKeyUp` | 58 | deckungsgleich mit der ersten Zeile — wer `role` setzt, hat hier auch die Taste verdrahtet |

Die 133 ohne Tastaturzugang nach Tag: `div` 80, `th` 15, `span` 15, `img` 10, `td` 7, `tr` 5, `canvas` 1.

Zwei Untergruppen darin sind eigene Faelle:

* **15 `th` mit `onClick`** (Spalten sortieren, alle in `sharePdf`, Z11511-Z11522). Der sichtbare Text (`"Nummer"`, `"Status"`, …) ist da, aber der Kopf ist kein Knopf: mit der Tastatur ist die Sortierung NICHT erreichbar. Der Name ist ABLESBAR — er steht als erstes Kind — der fehlende Teil ist `role`/`tabIndex` und ein `aria-sort`.
* **10 `img` mit `onClick`**. Ein Bild ist nie ein Bedienelement; hier braucht es zusaetzlich ein `alt`.

Vollstaendige Liste der 133 ohne Tastaturzugang:

| Zeile | Ansicht | Tag | Hat davon | onClick (der Name steht hier) |
| --- | --- | --- | --- | --- |
| 7014 | KundenPortal | `div` | — | e=>{e.stopPropagation();_openFileUrl(ph);}} |
| 9534 | App | `div` | — | e=>{if(e.target===e.currentTarget)onClose();}, onKeyDown: e=>{i… |
| 9561 | App | `div` | — | r.action, style: {display:"flex",alignItems:"center",gap:10,pad… |
| 9664 | App | `div` | — | ()=>{markRead(n.id);/* v3.9.144: Notification-Klick navigiert —… |
| 9701 | App | `img` | — | ()=>{/* v3.9.47 S32-1 F2: dataUrl-Guard — bei leerem/ungültigem… |
| 9771 | App | `div` | — | ()=>{refreshPendingDetail();setShowSyncPanel(true);}} |
| 9821 | App | `div` | — | ()=>{refreshPendingDetail();setShowSyncPanel(true);}} |
| 10287 | MitarbeiterView | `div` | — | ()=>setSel(m.id), className: "epk-card-hover", style: {...CC(),… |
| 10332 | MitarbeiterView | `div` | — | ()=>{if(isWAdm)toggleProj(selM.id,p.id);}} |
| 10525 | up | `div` | — | o.open, style:{position:"relative",display:"flex",alignItems:"s |
| 10683 | up | `div` | — | function(e){if(e&&e.stopPropagation)e.stopPropagation();},title… |
| 10804 | up | `div` | — | function(){/* v3.9.718 P1-b: Wartelisten-Eintrag oeffnet den Sc… |
| 11511 | sharePdf | `th` | — | ()=>toggleSort("nummer")} |
| 11512 | sharePdf | `th` | — | ()=>toggleSort("arbeitsanweisungen")} |
| 11513 | sharePdf | `th` | — | ()=>toggleSort("aufgenommen")} |
| 11514 | sharePdf | `th` | — | ()=>toggleSort("terminVorschlag")} |
| 11515 | sharePdf | `th` | — | ()=>toggleSort("terminBestaetigt")} |
| 11516 | sharePdf | `th` | — | ()=>toggleSort("scheinstatus")} |
| 11517 | sharePdf | `th` | — | ()=>toggleSort("prioritaet")} |
| 11518 | sharePdf | `th` | — | ()=>toggleSort("scheinart")} |
| 11519 | sharePdf | `th` | — | ()=>toggleSort("sachbearbeiter")} |
| 11520 | sharePdf | `th` | — | ()=>toggleSort("monteur")} |
| 11521 | sharePdf | `th` | — | ()=>toggleSort("kundName")} |
| 11522 | sharePdf | `th` | — | ()=>toggleSort("projektnr")} |
| 11527 | sharePdf | `td` | — | ()=>_openEditGuarded(a)} |
| 11528 | sharePdf | `td` | — | ()=>_openEditGuarded(a)} |
| 11537 | sharePdf | `td` | — | ()=>_openEditGuarded(a)} |
| 11551 | sharePdf | `div` | — | ()=>setAsShowQR(null), style: {position:"fixed",top:0,left:0,ri… |
| 11599 | sharePdf | `div` | — | ()=>{setCalDate(new Date(day));setCalView("tag");}, style: {pad… |
| 11601 | sharePdf | `div` | — | e=>{e.stopPropagation();openEdit(a);}, title: a.nummer+" — "+(a… |
| 11613 | sharePdf | `div` | — | ()=>{setCalDate(new Date(day));setCalView("tag");}, style: {pad… |
| 11627 | sharePdf | `div` | — | ()=>_openEditGuarded(a), title: a.nummer+" — "+(a.kundName\|\|"?"… |
| 11654 | sharePdf | `div` | — | ()=>_openEditGuarded(a), style: {padding:"8px 12px",borderRadiu… |
| 11747 | sharePdf | `img` | — | ()=>{try{window.open(_u,"_blank");}catch(_){}}, style:{width:64… |
| 12613 | PZEView | `div` | — | ()=>setKorr(null)} |
| 13375 | VBueroExport | `div` | tabIndex | (e)=>{if(e.target===e.currentTarget)setShowPreview(null);}, onK… |
| 13378 | VBueroExport | `div` | — | (e)=>e.stopPropagation()} |
| 13473 | VBueroExport | `td` | — | ()=>openMultiEntryEdit(w,ds,projId), title: "Mehrere Einträge —… |
| 13585 | VBueroExport | `div` | — | ()=>{setSelProj(ps.id);if(ps.cnt)_toggleBWB(ps.id);}/* v3.9.360… |
| 13644 | VBueroExport | `th` | — | ()=>_kTog(c[0]),style:{padding:"6px 8px",fontSize:UI.fMeta,font… |
| 13645 | VBueroExport | `tr` | — | function(){_setKrOpen(function(pp){var mm=Object.assign({},pp);… |
| 13677 | VBueroExport | `div` | — | ()=>_setTankFotoView(null),style:{position:"fixed",inset:0,back… |
| 14077 | AdminPanel | `div` | — | ()=>setSel(u.id), style: {...CC(),padding:12,marginBottom:6,cur… |
| 15208 | HomeView | `div` | — | ()=>onOpenP(pr)} |
| 15722 | ProjList | `div` | — | ()=>onOpen(p), onMouseEnter: e=>e.currentTarget.style.backgroun… |
| 15737 | ProjList | `div` | — | ()=>onOpen(p), onMouseEnter: e=>{e.currentTarget.style.boxShado… |
| 15817 | ProjectShell | `img` | — | onHome, style: {height:28,borderRadius:3,maxWidth:"100%",object… |
| 15955 | VDash | `div` | — | ()=>{if(setView)setView("fotos");}} |
| 16420 | VForm | `div` | — | ()=>{setFTab(t.id);setShowAll(false);setSearch("");}, style: {.… |
| 16429 | VForm | `div` | — | ()=>{setFTab(f._type);setShowAll(false);setSearch("");}} |
| 16661 | VCheck | `div` | — | ()=>setSel(c.id), style: {...CC(),cursor:"pointer",display:"fle… |
| 16941 | VMang | `div` | — | e=>{e.stopPropagation();setLightbox({src:ph,title:m.name+" — Fo… |
| 17025 | VMang | `div` | — | ()=>setLightbox({src:ph,title:m.name+" — Foto "+(i+1)}), style:… |
| 17173 | PlanViewer | `div` | — | handlePlanClick, onTouchEnd: onPlanClick?handlePlanTap:undefine… |
| 17173 | PlanViewer | `img` | — | handlePlanClick, onTouchEnd: onPlanClick?handlePlanTap:undefine… |
| 17686 | TicketListItem | `div` | — | ()=>onClick(ticket), style: {...CC(),padding:10,marginBottom:4,… |
| 18118 | PlanViewerCanvas | `canvas` | — | handleCanvasClick, style: {display: "block", maxWidth: "n |
| 18122 | PlanViewerCanvas | `img` | — | handleCanvasClick, style: {display: "block", boxShadow: " |
| 18141 | PlanViewerCanvas | `div` | — | (e)=>{e.stopPropagation();const _fx=pan.x+(_cx/100)*_pw*zoom, _… |
| 18183 | QuickEditPin | `div` | — | onClose, style:{position:"fixed", inset:0, background:"rgba(0,0… |
| 18432 | VPlan | `tr` | — | ()=>{setSelTicket(t);setSelPlan(plans.find(x=>x.id===t.planId)\|… |
| 18434 | VPlan | `div` | — | ()=>{setSelTicket(t);setSelPlan(plans.find(x=>x.id===t.planId)\|… |
| 18442 | VPlan | `div` | — | ()=>toggleLayer(l.id)} |
| 18452 | VPlan | `div` | — | ()=>_optionalChain([fileRef, 'access', _417 => _417.current, 'o… |
| 18454 | VPlan | `div` | — | ()=>{setSelPlan(pl);setSubView("viewer");}} |
| 18461 | VPlan | `div` | — | ()=>setSelTicket(null), style: {position:"fixed",inset:0,backgr… |
| 18461 | VPlan | `div` | — | ()=>setSelTicket(null), style: {display:"flex",justifyContent:"… |
| 18464 | VPlan | `div` | — | ()=>setTplEdit(null)} |
| 19435 | VDoku | `div` | — | e=>{e.stopPropagation();if(hasKids)toggleExpand(folder.id);}, s… |
| 19438 | VDoku | `div` | — | ()=>{setCurFolder(folder.id);if(isMob)setTreeOpen(false);}, sty… |
| 19563 | VDoku | `div` | — | ()=>setShowUp(true)} |
| 19578 | VDoku | `div` | — | ()=>openDoc(d)} |
| 20376 | VMaterial | `div` | — | e=>{if(e.target===e.currentTarget)setFlexPopup(null);}, style: … |
| 20500 | VMaterial | `div` | — | ()=>setOrderDetail(isDetail?null:ord.id)} |
| 21082 | VMaterial | `div` | — | ()=>setDnAutoEnabled(prev=>{const s=new Set(prev);if(s.has(g.id… |
| 21150 | VMaterial | `div` | — | ()=>{setDnSelected(prev=>{const s=new Set(prev);if(s.has(a.artN… |
| 21834 | WeekPlan | `span` | — | ()=>toggleMAMulti(r.id,pickDays,m.id), style: {width:18,height:… |
| 21835 | WeekPlan | `span` | — | ()=>toggleMAMulti(r.id,pickDays,m.id), style: {cursor:"pointer"… |
| 21836 | WeekPlan | `span` | — | (e)=>{e.stopPropagation();toggleMAWeek(r.id,m.id);}, style: {fo… |
| 21851 | WeekPlan | `span` | — | ()=>toggleFZMulti(r.id,pickDays,f.id), style: {width:18,height:… |
| 21852 | WeekPlan | `span` | — | ()=>toggleFZMulti(r.id,pickDays,f.id), style: {cursor:"pointer"… |
| 21853 | WeekPlan | `span` | — | (e)=>{e.stopPropagation();toggleFZWeek(r.id,f.id);}, style: {fo… |
| 21905 | WeekPlan | `td` | — | e=>{e.stopPropagation();if(isMob&&isAdmin){setCellPick(isPickCe… |
| 21922 | WeekPlan | `div` | — | ()=>{if(cellPick)setCellPick(null);setSelCells(null);}} |
| 22141 | WeekPlan | `div` | — | ()=>{setCellPick(null);setSelCells(null);},style:{position:'fix… |
| 22154 | WeekPlan | `div` | — | isAdmin?()=>setCellPick({rowId:r.id,days:[d],type:'ma'}):undefi… |
| 22154 | WeekPlan | `div` | — | isAdmin?()=>setCellPick({rowId:r.id,days:['_bem'],type:'bem'}):… |
| 22249 | WeekPlan | `th` | — | (isAdmin&&isTgt)?()=>_wpPasteDay(d):undefined, title: |
| 22260 | WeekPlan | `span` | — | (e)=>{e.stopPropagation();if(isTgt)_wpPasteDay(d);else if(isSrc… |
| 22283 | WeekPlan | `td` | — | ()=>{if(isAdmin&&isEmpty&&editRow!==r.id){setEditRow(r.id);setE… |
| 22746 | AbsView | `div` | — | ()=>{if(isAdmin){setSel(m);setSubView("kalender");}}, style: {d… |
| 22778 | AbsView | `td` | — | ()=>{if(isAdmin){setSel(m);setSubView("kalender");}}} |
| 22845 | AbsView | `div` | — | ()=>{if(inM&&!we)tog(day);}, style: {padding:"7px 3px",textAlig… |
| 22946 | AbsView | `div` | — | ()=>_openAttest(f), style: {width:56,height:56,borderRadius:6,o… |
| 22961 | AbsView | `div` | — | ()=>{setSel(m);setSubView("kalender");}} |
| 23043 | AbsView | `div` | — | ()=>{if(at2){setSel(m);setMo(d.getMonth());setSubView("kalender… |
| 23483 | StundenzettelView | `div` | — | ()=>setFinkStatusFilter(finkStatusFilter===k.f?"alle":k.f), sty… |
| 23608 | StundenzettelView | `span` | — | ()=>setFinkStunden(z.id,0), style: {cursor:"pointer",color:"#f9… |
| 23668 | StundenzettelView | `div` | — | ()=>{setSigZettel(null);setSigData(null);}} |
| 23685 | StundenzettelView | `div` | — | ()=>setViewPdf(null)} |
| 24091 | ASKommentarePanel | `div` | — | ()=>insertMention(w),style:{padding:'7px 10px',cursor:'pointer'… |
| 24232 | WorkerKompetenzenPanel | `span` | — | editable?e=>{e.stopPropagation();setLevel(key,lvl);}:null,style… |
| 24698 | ChefDashboard | `tr` | — | function(){if(onOpenP)onOpenP(p.p);},style:{borderTop:'1px soli… |
| 24767 | ChefDashboard | `div` | — | function(){window.__asFilter='alle';onNav('arbeitsscheine');},s… |
| 25827 | ZeiterfassungView | `div` | — | ()=>{setAddDay(null);setEditEntry(null);}/* v3.9.416: Tap-outsi… |
| 25828 | ZeiterfassungView | `div` | — | e=>e.stopPropagation()/* v3.9.416: Klicks im Panel schließen ni… |
| 25978 | ZeiterfassungView | `tr` | — | ()=>{setSelWorker(m.id);setViewAll(false);}} |
| 27331 | FahrtenbuchView | `div` | — | function(ev){try{ev.stopPropagation();}catch(_e){}}} |
| 27332 | FahrtenbuchView | `div` | — | function(){_waehleFahrt(s);}, style:{display:'grid',gridTemplat |
| 27701 | load | `div` | — | function(){if(row.hatTracker)_focus(row);setBuchFid(row.f.id);}, |
| 28596 | _kmFromBeleg | `div` | — | ()=>setSel(f.id)} |
| 28608 | _kmFromBeleg | `div` | — | ()=>setSel(f.id)} |
| 28770 | _kmFromBeleg | `div` | — | ()=>_openFileUrl(selFz.zulassungsschein,"Zulassungsschein")} |
| 28796 | _kmFromBeleg | `div` | — | ()=>{const m=monteure.find(x=>x.n===bh.fahrer);setBeschForm({fa… |
| 28873 | _kmFromBeleg | `img` | — | ()=>_openSvcDoc(d)} |
| 28877 | _kmFromBeleg | `span` | — | ()=>_delSvcDoc(i,d), title: "Entfernen", style: {position:"abso… |
| 28950 | _kmFromBeleg | `img` | — | ()=>_openFileUrl(s.foto,"Schaden"), alt: "Schaden"} |
| 28958 | _kmFromBeleg | `img` | — | ()=>_openFileUrl(t.foto,"Beleg"), style: {width:28,height:28,ob… |
| 29026 | PdfViewerModal | `div` | — | onClose,style:{position:"fixed",inset:0,background:"rgba(0,0,0,… |
| 29150 | VGefahrstoff | `div` | — | ()=>openFile(fi)} |
| 29163 | VGefahrstoff | `span` | — | ()=>jumpTo(-1),style:{cursor:"pointer",color:nav.length?V.ac:V.… |
| 29164 | VGefahrstoff | `span` | — | ()=>jumpTo(c.i),style:{cursor:"pointer",color:c.i===nav.length-… |
| 29168 | VGefahrstoff | `div` | — | ()=>goInto(fo.id)} |
| 29387 | BauprovisorienView | `div` | — | ()=>_kPick(hit),style:{padding:"8px 11px",cursor:"pointer",bord… |
| 29465 | BauprovisorienView | `div` | — | ()=>setQrShow(null),style:{position:"fixed",inset:0,zIndex:9999… |
| 29751 | WerkzeugView | `span` | — | onChange?()=>onChange(i):undefined, style: {cursor:onChange?"po… |
| 30020 | WerkzeugView | `div` | — | ()=>{if(isAdmin)openEdit(w);}, style: {...CC(),padding:"10px 12… |
| 30043 | WerkzeugView | `th` | — | h.c?()=>toggleSort(h.c):undefined, style: {...thS(),textAlign:i… |
| 30046 | WerkzeugView | `tr` | — | ()=>{if(isAdmin)openEdit(w);}, style: {borderBottom:"1px solid … |
| 30120 | WerkzeugView | `img` | — | ()=>_openFileUrl(s.befund,"Befund")} |
| 30120 | WerkzeugView | `span` | — | ()=>{setWerkzeuge(p=>p.map(w=>w.id===wzServiceSel?{...w,service… |
| 30121 | WerkzeugView | `img` | — | ()=>_openFileUrl(s.rechnung,"Rechnung")} |
| 30121 | WerkzeugView | `span` | — | ()=>{setWerkzeuge(p=>p.map(w=>w.id===wzServiceSel?{...w,service… |

### 4b. `input` / `select` / `textarea`

**532** gemessen, **461 ohne** `label`-Umschliessung, `aria-label`, `title`, `aria-labelledby` oder eine `htmlFor`/`id`-Verbindung.

| Tag | ohne Namen |
| --- | --- |
| `input` | 315 |
| `select` | 117 |
| `textarea` | 29 |

🔴 **161 davon tragen einen `placeholder` und sonst nichts.** Ein Platzhalter ist KEIN Name: er verschwindet, sobald jemand tippt, und mehrere Vorlesehilfen lesen ihn nicht als Namen. Er ist aber ein ABGELESENER Vorschlag — der Text steht schon da.

🟡 **141 davon haben ein `label`-ELEMENT in der Naehe** (bis 1400 Zeichen davor), dessen Text den Namen NENNT — nur ist er nicht VERBUNDEN. Die App benutzt `htmlFor` genau 20 mal in der ganzen Datei. Das ist der billigste Teil: der Name ist schon geschrieben, er braucht nur ein `htmlFor`+`id` oder ein `aria-label` mit demselben Wort.

Verteilung der 461 ohne Namen nach Ansicht (die 12 groessten):

| Ansicht (naechste `function` davor) | ohne Namen |
| --- | --- |
| _kmFromBeleg | 80 |
| WerkzeugView | 36 |
| sharePdf | 32 |
| AdminPanel | 28 |
| VPlan | 21 |
| BauprovisorienView | 21 |
| ProjList | 19 |
| VMaterial | 16 |
| MitarbeiterView | 13 |
| FRegie | 13 |
| VCheck | 12 |
| AbsView | 11 |

🔴 Die Spalte „Ansicht" ist die naechste `function NAME(` VOR der Stelle. Bei `_kmFromBeleg`, `sharePdf`, `load`, `_submitAntrag` und `up` ist das eine INNERE Hilfsfunktion, nicht die Ansicht — der Name ist dann falsch, die ZEILE stimmt. Dieselbe Schwaeche haben die Abtaster von v3.9.957 und v3.9.958.

Vollstaendige Liste, mit dem abgelesenen Namensvorschlag je Stelle. **Der Vorschlag ist ABGELESEN, nicht formuliert**: entweder aus dem `placeholder` oder aus dem Text des `label`-Elements daneben. Wo beide fehlen, steht „ENTSCHEIDUNG" — dort waere ein Name eine Wahl, und ich entscheide sie nicht.

| Zeile | Ansicht | Tag | type | Namensvorschlag (abgelesen) | Quelle |
| --- | --- | --- | --- | --- | --- |
| 6517 | PwInput | `input` | — | **ENTSCHEIDUNG** | — |
| 6770 | PortalEntry | `input` | — | `Code eingeben` | placeholder |
| 6977 | KundenPortal | `input` | — | `z.B. Steckdose in Küche defekt` | placeholder |
| 6978 | KundenPortal | `input` | — | `z.B. Erdgeschoss, Küche links` | placeholder |
| 6979 | KundenPortal | `textarea` | — | `Was genau ist das Problem?` | placeholder |
| 7179 | LoginScreen | `input` | — | `Benutzername` | placeholder |
| 7679 | _submitAntrag | `input` | date | **ENTSCHEIDUNG** | — |
| 7681 | _submitAntrag | `input` | date | **ENTSCHEIDUNG** | — |
| 7723 | _submitAntrag | `select` | — | **ENTSCHEIDUNG** | — |
| 7727 | _submitAntrag | `input` | — | `UID scannen oder tippen` | placeholder |
| 7740 | _submitAntrag | `input` | — | `UID (Test ohne Reader)` | placeholder |
| 9898 | KVRulesConfig | `input` | number | **ENTSCHEIDUNG** | — |
| 9905 | KVRulesConfig | `textarea` | — | **ENTSCHEIDUNG** | — |
| 9906 | KVRulesConfig | `input` | — | **ENTSCHEIDUNG** | — |
| 9959 | StempelPauseConfig | `input` | number | **ENTSCHEIDUNG** | — |
| 10274 | MitarbeiterView | `input` | — | `nachname` | placeholder |
| 10275 | MitarbeiterView | `input` | text | `min. 4 Zeichen` | placeholder |
| 10314 | MitarbeiterView | `input` | — | `Nachname` | placeholder |
| 10315 | MitarbeiterView | `input` | — | `Vorname` | placeholder |
| 10316 | MitarbeiterView | `select` | — | **ENTSCHEIDUNG** | — |
| 10317 | MitarbeiterView | `input` | — | `0664...` | placeholder |
| 10318 | MitarbeiterView | `input` | — | `name@ep-kolar.at` | placeholder |
| 10320 | MitarbeiterView | `input` | — | `z.B. 4491` | placeholder |
| 10321 | MitarbeiterView | `input` | — | `1234 010185` | placeholder |
| 10322 | MitarbeiterView | `input` | — | `P 1234567` | placeholder |
| 10323 | MitarbeiterView | `input` | date | **ENTSCHEIDUNG** | — |
| 10324 | MitarbeiterView | `input` | date | **ENTSCHEIDUNG** | — |
| 10325 | MitarbeiterView | `input` | date | **ENTSCHEIDUNG** | — |
| 10795 | up | `input` | — | `Suchen: Nummer, Kunde, Ort, Grund…` | placeholder |
| 11377 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11401 | sharePdf | `input` | — | `Scheinnummer z.B. S075270` | placeholder |
| 11458 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11459 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11460 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11461 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11471 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11530 | sharePdf | `input` | date | **ENTSCHEIDUNG** | — |
| 11531 | sharePdf | `input` | date | **ENTSCHEIDUNG** | — |
| 11532 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11533 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11535 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11588 | sharePdf | `select` | — | **ENTSCHEIDUNG** | — |
| 11705 | sharePdf | `input` | time | `Uhrzeit` | placeholder |
| 11706 | sharePdf | `input` | date | „Vorschlag" | label daneben |
| 11706 | sharePdf | `input` | time | „Vorschlag" | label daneben |
| 11712 | sharePdf | `input` | date | **ENTSCHEIDUNG** | — |
| 11712 | sharePdf | `input` | time | **ENTSCHEIDUNG** | — |
| 11717 | sharePdf | `input` | text | `z.B. 01:30` | placeholder |
| 11718 | sharePdf | `input` | text | `z.B. 01:30` | placeholder |
| 11727 | sharePdf | `input` | — | „Störungsmelder" | label daneben |
| 11728 | sharePdf | `textarea` | — | „Durchzuführen * 🎤" | label daneben |
| 11732 | sharePdf | `textarea` | — | `Was wurde erledigt?` | placeholder |
| 11738 | sharePdf | `input` | — | `Bezeichnung` | placeholder |
| 11739 | sharePdf | `input` | — | `Menge` | placeholder |
| 11740 | sharePdf | `input` | — | `Einh.` | placeholder |
| 11756 | sharePdf | `input` | — | „Kontakt" | label daneben |
| 11757 | sharePdf | `textarea` | — | `Interne Notizen, Anmerkungen...` | placeholder |
| 11763 | sharePdf | `input` | — | „Projektnr." | label daneben |
| 11764 | sharePdf | `select` | — | „Priorität" | label daneben |
| 11765 | sharePdf | `select` | — | „Scheinstatus" | label daneben |
| 11767 | sharePdf | `select` | — | „Verrechnung" | label daneben |
| 12243 | KVZulagenReport | `input` | number | **ENTSCHEIDUNG** | — |
| 12250 | KVZulagenReport | `select` | — | **ENTSCHEIDUNG** | — |
| 12621 | PZEView | `input` | time | **ENTSCHEIDUNG** | — |
| 12639 | PZEView | `select` | — | **ENTSCHEIDUNG** | — |
| 12643 | PZEView | `input` | date | **ENTSCHEIDUNG** | — |
| 12644 | PZEView | `input` | date | **ENTSCHEIDUNG** | — |
| 13481 | VBueroExport | `input` | text | **ENTSCHEIDUNG** | — |
| 13503 | VBueroExport | `textarea` | — | `T\u00e4tigkeit eingeben...` | placeholder |
| 13640 | VBueroExport | `input` | search | `🔍 Mitarbeiter suchen…` | placeholder |
| 13640 | VBueroExport | `select` | — | **ENTSCHEIDUNG** | — |
| 13640 | VBueroExport | `select` | — | **ENTSCHEIDUNG** | — |
| 13640 | VBueroExport | `select` | — | **ENTSCHEIDUNG** | — |
| 13678 | VBueroExport | `input` | date | **ENTSCHEIDUNG** | — |
| 13678 | VBueroExport | `input` | number | **ENTSCHEIDUNG** | — |
| 13678 | VBueroExport | `input` | number | **ENTSCHEIDUNG** | — |
| 13678 | VBueroExport | `input` | number | **ENTSCHEIDUNG** | — |
| 14035 | AdminPanel | `input` | — | `benutzername` | placeholder |
| 14037 | AdminPanel | `input` | — | `Vor- Nachname` | placeholder |
| 14038 | AdminPanel | `input` | — | `email@ep-kolar.at` | placeholder |
| 14041 | AdminPanel | `select` | — | „Rolle" | label daneben |
| 14042 | AdminPanel | `select` | — | „Monteur zuordnen" | label daneben |
| 14059 | AdminPanel | `select` | — | **ENTSCHEIDUNG** | — |
| 14138 | AdminPanel | `select` | — | „Rolle" | label daneben |
| 14175 | AdminPanel | `input` | date | **ENTSCHEIDUNG** | — |
| 14222 | AdminPanel | `select` | — | **ENTSCHEIDUNG** | — |
| 14226 | AdminPanel | `select` | — | **ENTSCHEIDUNG** | — |
| 14250 | AdminPanel | `select` | — | **ENTSCHEIDUNG** | — |
| 14428 | AdminPanel | `input` | — | `Neuen PASSPORT-Hash einfügen...` | placeholder |
| 14492 | AdminPanel | `input` | — | `z.B. Holter` | placeholder |
| 14493 | AdminPanel | `select` | — | „Gewerk" | label daneben |
| 14494 | AdminPanel | `select` | — | „Schnittstelle" | label daneben |
| 14497 | AdminPanel | `input` | — | „Kundennummer" | label daneben |
| 14498 | AdminPanel | `input` | — | „Benutzername" | label daneben |
| 14505 | AdminPanel | `input` | — | `z.B. HOLTER, OEAG, SHT` | placeholder |
| 14506 | AdminPanel | `input` | — | `DATANORM-Server des Händlers` | placeholder |
| 14509 | AdminPanel | `input` | — | `https://shop.holter.at/...` | placeholder |
| 14510 | AdminPanel | `select` | — | „Sync-Intervall" | label daneben |
| 14511 | AdminPanel | `input` | number | `28` | placeholder |
| 14512 | AdminPanel | `input` | — | `https://online.holter.at/HO/PREIWA/…` | placeholder |
| 14519 | AdminPanel | `input` | — | `z.B. 30 Tage netto` | placeholder |
| 14520 | AdminPanel | `input` | number | `z.B. 3` | placeholder |
| 14521 | AdminPanel | `input` | number | `z.B. 2` | placeholder |
| 14572 | AdminPanel | `input` | file | **ENTSCHEIDUNG** | — |
| 14637 | AdminPanel | `select` | — | „Standard-Sachbearbeiter:" | label daneben |
| 15662 | ProjList | `input` | — | `PA24xxxx` | placeholder |
| 15663 | ProjList | `input` | — | `BVH Muster` | placeholder |
| 15664 | ProjList | `input` | — | „Kunde" | label daneben |
| 15665 | ProjList | `input` | — | `Elektroinstallation` | placeholder |
| 15668 | ProjList | `input` | — | `Musterstraße 12` | placeholder |
| 15669 | ProjList | `input` | — | „PLZ" | label daneben |
| 15670 | ProjList | `input` | — | „Ort" | label daneben |
| 15671 | ProjList | `input` | number | „Auftragssumme" | label daneben |
| 15672 | ProjList | `input` | number | „Fortschritt %" | label daneben |
| 15676 | ProjList | `input` | number | `z.B. 150` | placeholder |
| 15677 | ProjList | `input` | number | `z.B. 25000` | placeholder |
| 15680 | ProjList | `input` | date | „Start" | label daneben |
| 15681 | ProjList | `input` | date | „Ende" | label daneben |
| 15682 | ProjList | `select` | — | „Status" | label daneben |
| 15683 | ProjList | `input` | — | „Kunden-Nr" | label daneben |
| 15687 | ProjList | `input` | — | `Hr. / Fr. ...` | placeholder |
| 15688 | ProjList | `input` | tel | `+43 ...` | placeholder |
| 15689 | ProjList | `input` | email | `kunde@firma.at` | placeholder |
| 15750 | ProjList | `input` | range | **ENTSCHEIDUNG** | — |
| 15838 | ProjectShell | `select` | — | **ENTSCHEIDUNG** | — |
| 16138 | VZeit | `select` | — | „Monteur" | label daneben |
| 16145 | VZeit | `input` | time | „Von" | label daneben |
| 16146 | VZeit | `input` | time | „Bis" | label daneben |
| 16147 | VZeit | `select` | — | „Pause" | label daneben |
| 16151 | VZeit | `textarea` | — | `z.B. Montage, Inbetriebnahme, Kabel…` | placeholder |
| 16152 | VZeit | `input` | — | `optional` | placeholder |
| 16478 | HeadFields | `input` | — | **ENTSCHEIDUNG** | — |
| 16478 | HeadFields | `input` | — | **ENTSCHEIDUNG** | — |
| 16478 | HeadFields | `input` | — | **ENTSCHEIDUNG** | — |
| 16478 | HeadFields | `input` | date | **ENTSCHEIDUNG** | — |
| 16485 | FSF | `input` | — | **ENTSCHEIDUNG** | — |
| 16485 | FSF | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 16485 | FSF | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 16485 | FSF | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 16485 | FSF | `input` | — | **ENTSCHEIDUNG** | — |
| 16491 | FDH | `select` | — | **ENTSCHEIDUNG** | — |
| 16491 | FDH | `input` | — | **ENTSCHEIDUNG** | — |
| 16491 | FDH | `input` | number | `bar` | placeholder |
| 16491 | FDH | `input` | number | `min` | placeholder |
| 16491 | FDH | `input` | — | **ENTSCHEIDUNG** | — |
| 16497 | FAH | `input` | date | **ENTSCHEIDUNG** | — |
| 16497 | FAH | `input` | number | **ENTSCHEIDUNG** | — |
| 16497 | FAH | `input` | number | **ENTSCHEIDUNG** | — |
| 16497 | FAH | `input` | number | **ENTSCHEIDUNG** | — |
| 16497 | FAH | `input` | — | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `input` | date | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `input` | — | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `input` | — | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `input` | — | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `select` | — | **ENTSCHEIDUNG** | — |
| 16503 | FAbn | `input` | — | **ENTSCHEIDUNG** | — |
| 16528 | FRegie | `input` | date | **ENTSCHEIDUNG** | — |
| 16528 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16528 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16528 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16529 | FRegie | `textarea` | — | **ENTSCHEIDUNG** | — |
| 16533 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16533 | FRegie | `input` | number | `0` | placeholder |
| 16533 | FRegie | `input` | number | `0` | placeholder |
| 16533 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16538 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16538 | FRegie | `input` | number | `0` | placeholder |
| 16538 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16538 | FRegie | `input` | — | **ENTSCHEIDUNG** | — |
| 16639 | VCheck | `input` | — | `Name der Checkliste` | placeholder |
| 16640 | VCheck | `textarea` | — | `Punkte (ein Punkt pro Zeile):\nPunk…` | placeholder |
| 16646 | VCheck | `input` | — | `Feld-Bezeichnung (z.B. Vorlaufdruck)` | placeholder |
| 16647 | VCheck | `select` | — | **ENTSCHEIDUNG** | — |
| 16648 | VCheck | `input` | — | `Einheit (bar, °C…)` | placeholder |
| 16649 | VCheck | `input` | — | `Optionen, mit Komma` | placeholder |
| 16688 | VCheck | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 16691 | VCheck | `input` | number | **ENTSCHEIDUNG** | — |
| 16692 | VCheck | `input` | text | `Eingabe…` | placeholder |
| 16693 | VCheck | `input` | date | **ENTSCHEIDUNG** | — |
| 16694 | VCheck | `select` | — | **ENTSCHEIDUNG** | — |
| 16695 | VCheck | `input` | — | `Anmerkung...` | placeholder |
| 16949 | VMang | `select` | — | **ENTSCHEIDUNG** | — |
| 16950 | VMang | `input` | — | `z.B. Wird nächste Woche behoben` | placeholder |
| 16969 | VMang | `input` | — | **ENTSCHEIDUNG** | — |
| 16970 | VMang | `input` | — | **ENTSCHEIDUNG** | — |
| 16972 | VMang | `input` | date | **ENTSCHEIDUNG** | — |
| 16973 | VMang | `select` | — | **ENTSCHEIDUNG** | — |
| 16989 | VMang | `input` | search | `🔍 Mangel/Ort/Ebene…` | placeholder |
| 16991 | VMang | `select` | — | „Alle" | label daneben |
| 17002 | VMang | `select` | — | **ENTSCHEIDUNG** | — |
| 17003 | VMang | `select` | — | **ENTSCHEIDUNG** | — |
| 17620 | TicketDetail | `textarea` | — | „Beschreibung 🎤" | label daneben |
| 17622 | TicketDetail | `select` | — | „Typ" | label daneben |
| 17623 | TicketDetail | `select` | — | „Status" | label daneben |
| 17624 | TicketDetail | `select` | — | „Priorität" | label daneben |
| 17626 | TicketDetail | `select` | — | „Ebene" | label daneben |
| 17627 | TicketDetail | `input` | date | „Frist" | label daneben |
| 17629 | TicketDetail | `input` | range | „%" | label daneben |
| 17659 | TicketDetail | `input` | — | `Kommentar...` | placeholder |
| 18199 | QuickEditPin | `select` | — | „Status" | label daneben |
| 18201 | QuickEditPin | `select` | — | „Zuständig" | label daneben |
| 18204 | QuickEditPin | `input` | date | „Erledigen bis" | label daneben |
| 18206 | QuickEditPin | `select` | — | „Priorität" | label daneben |
| 18219 | QuickEditPin | `input` | — | `Kommentar hinzufügen…` | placeholder |
| 18402 | VPlan | `input` | file | **ENTSCHEIDUNG** | — |
| 18413 | VPlan | `input` | search | `🔍 Pin-Nr oder Titel suchen…` | placeholder |
| 18422 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18422 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18424 | VPlan | `textarea` | — | „Beschreibung 🎤" | label daneben |
| 18424 | VPlan | `select` | — | „Typ" | label daneben |
| 18424 | VPlan | `select` | — | „Priorität" | label daneben |
| 18424 | VPlan | `select` | — | „Ebene" | label daneben |
| 18424 | VPlan | `input` | date | „Frist" | label daneben |
| 18430 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18430 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18430 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18442 | VPlan | `input` | — | **ENTSCHEIDUNG** | — |
| 18442 | VPlan | `input` | color | **ENTSCHEIDUNG** | — |
| 18450 | VPlan | `input` | file | **ENTSCHEIDUNG** | — |
| 18454 | VPlan | `input` | — | `🏢 Geschoss wählen/eingeben (Erdgesc…` | placeholder |
| 18469 | VPlan | `input` | — | `Chip-Text (z.B. 🔴 Steckdose defekt)` | placeholder |
| 18471 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18472 | VPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 18473 | VPlan | `input` | — | `Ebenen-Stichwort (optional)` | placeholder |
| 18474 | VPlan | `input` | — | `Beschreibung (optional)` | placeholder |
| 19179 | VFotos | `select` | — | **ENTSCHEIDUNG** | — |
| 19442 | VDoku | `input` | — | **ENTSCHEIDUNG** | — |
| 19459 | VDoku | `input` | — | `Unterordner...` | placeholder |
| 19486 | VDoku | `input` | — | `Neuer Ordner...` | placeholder |
| 19549 | VDoku | `input` | — | `z.B. Baubesprechung 12.02.` | placeholder |
| 19550 | VDoku | `select` | — | „Kategorie" | label daneben |
| 19551 | VDoku | `select` | — | „Ordner" | label daneben |
| 19552 | VDoku | `input` | — | `Optional` | placeholder |
| 19558 | VDoku | `input` | file | „Notiz" | label daneben |
| 19559 | VDoku | `input` | file | „Notiz" | label daneben |
| 19591 | VDoku | `select` | — | **ENTSCHEIDUNG** | — |
| 19822 | VBautag | `input` | date | „Datum *" | label daneben |
| 19823 | VBautag | `select` | — | „Wetter" | label daneben |
| 19824 | VBautag | `input` | number | `z.B. 18` | placeholder |
| 19841 | VBautag | `textarea` | — | `Beschreibung der durchgeführten Arb…` | placeholder |
| 19843 | VBautag | `textarea` | — | `Verwendetes Material, Lieferungen...` | placeholder |
| 19844 | VBautag | `textarea` | — | `Störungen, Verzögerungen, besondere…` | placeholder |
| 20314 | VMaterial | `input` | search | `🔍 Artikel suchen (z.B. \` | placeholder |
| 20386 | VMaterial | `input` | number | `0` | placeholder |
| 20400 | VMaterial | `input` | number | **ENTSCHEIDUNG** | — |
| 20415 | VMaterial | `input` | number | **ENTSCHEIDUNG** | — |
| 20425 | VMaterial | `input` | number | **ENTSCHEIDUNG** | — |
| 20445 | VMaterial | `input` | — | `Artikel / Bezeichnung` | placeholder |
| 20446 | VMaterial | `input` | number | `Menge` | placeholder |
| 20452 | VMaterial | `textarea` | — | `Notiz / Freitext (optional, z.B. Hi…` | placeholder |
| 20551 | VMaterial | `input` | search | `🔍 Bestellungen suchen (z.B. \` | placeholder |
| 20597 | VMaterial | `input` | — | `Kommentar (z.B. liegt im Bus, kommt…` | placeholder |
| 20722 | VMaterial | `input` | number | **ENTSCHEIDUNG** | — |
| 21062 | VMaterial | `input` | file | **ENTSCHEIDUNG** | — |
| 21064 | VMaterial | `select` | — | **ENTSCHEIDUNG** | — |
| 21162 | VMaterial | `input` | — | `System (z.B. Geberit Mepla)` | placeholder |
| 21163 | VMaterial | `input` | — | `Kategorie (z.B. Rohre)` | placeholder |
| 21164 | VMaterial | `select` | — | **ENTSCHEIDUNG** | — |
| 22154 | WeekPlan | `input` | — | `Was ist zu tun? (Bemerkung)` | placeholder |
| 22156 | WeekPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 22156 | WeekPlan | `input` | — | `oder Freitext...` | placeholder |
| 22231 | WeekPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 22235 | WeekPlan | `input` | — | `oder Freitext...` | placeholder |
| 22287 | WeekPlan | `select` | — | **ENTSCHEIDUNG** | — |
| 22291 | WeekPlan | `input` | — | `oder Freitext...` | placeholder |
| 22294 | WeekPlan | `input` | — | `BVH / Baustelle eingeben...` | placeholder |
| 22300 | WeekPlan | `input` | — | **ENTSCHEIDUNG** | — |
| 22668 | AbsView | `input` | file | **ENTSCHEIDUNG** | — |
| 22719 | AbsView | `input` | date | „Von" | label daneben |
| 22720 | AbsView | `input` | date | „Bis" | label daneben |
| 22722 | AbsView | `input` | — | `Hinweis ans Büro…` | placeholder |
| 22779 | AbsView | `input` | number | **ENTSCHEIDUNG** | — |
| 22780 | AbsView | `input` | number | **ENTSCHEIDUNG** | — |
| 22781 | AbsView | `input` | number | **ENTSCHEIDUNG** | — |
| 22789 | AbsView | `input` | number | **ENTSCHEIDUNG** | — |
| 22856 | AbsView | `select` | — | „Typ" | label daneben |
| 22856 | AbsView | `input` | number | „Stunden" | label daneben |
| 22856 | AbsView | `input` | text | `optional...` | placeholder |
| 23512 | StundenzettelView | `select` | — | „Mitarbeiter" | label daneben |
| 23519 | StundenzettelView | `select` | — | „Monat" | label daneben |
| 23525 | StundenzettelView | `select` | — | „Jahr" | label daneben |
| 23542 | StundenzettelView | `select` | — | „📎 Datei wählen" | label daneben |
| 23546 | StundenzettelView | `select` | — | „📎 Datei wählen" | label daneben |
| 23550 | StundenzettelView | `select` | — | **ENTSCHEIDUNG** | — |
| 23607 | StundenzettelView | `input` | number | `0.0` | placeholder |
| 23816 | VerbindungView | `input` | — | „Supabase URL" | label daneben |
| 23941 | SystemConfigPanel | `input` | — | **ENTSCHEIDUNG** | — |
| 24009 | ASChecklistPanel | `input` | — | `Neuer Punkt… (Enter)` | placeholder |
| 24097 | ASKommentarePanel | `textarea` | — | `Kommentar… (@Name = Mention, Ctrl+E…` | placeholder |
| 24181 | WorkerNfcPanel | `input` | — | `Chip-UID` | placeholder |
| 24335 | UrlaubsantragPanel | `input` | date | „Von" | label daneben |
| 24336 | UrlaubsantragPanel | `input` | date | „Bis" | label daneben |
| 24337 | UrlaubsantragPanel | `select` | — | „Art" | label daneben |
| 24339 | UrlaubsantragPanel | `textarea` | — | `Hinweis an Büro…` | placeholder |
| 24920 | FahrtenbuchPanel | `input` | month | **ENTSCHEIDUNG** | — |
| 24928 | FahrtenbuchPanel | `input` | date | „Datum" | label daneben |
| 24929 | FahrtenbuchPanel | `select` | — | „Fahrzeug *" | label daneben |
| 24930 | FahrtenbuchPanel | `select` | — | „Zweck" | label daneben |
| 24931 | FahrtenbuchPanel | `select` | — | „Projekt (opt.)" | label daneben |
| 24932 | FahrtenbuchPanel | `input` | number | „KM Start *" | label daneben |
| 24933 | FahrtenbuchPanel | `input` | number | „KM Ende *" | label daneben |
| 24934 | FahrtenbuchPanel | `input` | number | „Liter (opt.)" | label daneben |
| 24935 | FahrtenbuchPanel | `input` | number | „€/L (opt.)" | label daneben |
| 25852 | ZeiterfassungView | `select` | — | „Projekt wählen" | label daneben |
| 25859 | ZeiterfassungView | `select` | — | „Arbeitsschein / Störung wählen" | label daneben |
| 25866 | ZeiterfassungView | `input` | — | `z.B. Lager, Büro, Schulung, Störung…` | placeholder |
| 25872 | ZeiterfassungView | `input` | — | `z.B. Montage, Inbetriebnahme, Verka…` | placeholder |
| 25879 | ZeiterfassungView | `input` | time | „Von" | label daneben |
| 25883 | ZeiterfassungView | `input` | time | „Bis" | label daneben |
| 25887 | ZeiterfassungView | `select` | — | „Pause" | label daneben |
| 25903 | ZeiterfassungView | `input` | — | `Anmerkung...` | placeholder |
| 25950 | ZeiterfassungView | `select` | — | **ENTSCHEIDUNG** | — |
| 26053 | ZeiterfassungView | `input` | number | **ENTSCHEIDUNG** | — |
| 26120 | ZeiterfassungView | `select` | — | **ENTSCHEIDUNG** | — |
| 27292 | FahrtenbuchView | `select` | — | **ENTSCHEIDUNG** | — |
| 27399 | FahrtenbuchView | `select` | — | **ENTSCHEIDUNG** | — |
| 27402 | FahrtenbuchView | `input` | date | **ENTSCHEIDUNG** | — |
| 27404 | FahrtenbuchView | `input` | date | **ENTSCHEIDUNG** | — |
| 27732 | load | `input` | — | `IMEI` | placeholder |
| 27746 | load | `input` | — | `🔎 Kennzeichen, Marke, Fahrer …` | placeholder |
| 28279 | _kmFromBeleg | `input` | — | `Kennzeichen (z.B. TU-123AB)` | placeholder |
| 28293 | _kmFromBeleg | `input` | — | `Manuell...` | placeholder |
| 28361 | _kmFromBeleg | `input` | number | `45.0` | placeholder |
| 28362 | _kmFromBeleg | `input` | number | `72.50` | placeholder |
| 28363 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28364 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28381 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28386 | _kmFromBeleg | `input` | — | `z.B. Fahrt nach Wien` | placeholder |
| 28399 | _kmFromBeleg | `textarea` | — | `Was ist beschädigt? Z.B. Delle hint…` | placeholder |
| 28451 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28455 | _kmFromBeleg | `input` | number | `45.0` | placeholder |
| 28459 | _kmFromBeleg | `input` | number | `72.50` | placeholder |
| 28463 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28521 | _kmFromBeleg | `input` | — | `TU-123AB` | placeholder |
| 28522 | _kmFromBeleg | `input` | — | `VW` | placeholder |
| 28523 | _kmFromBeleg | `input` | — | `Crafter` | placeholder |
| 28524 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28525 | _kmFromBeleg | `input` | — | **ENTSCHEIDUNG** | — |
| 28526 | _kmFromBeleg | `input` | — | `2022` | placeholder |
| 28527 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28528 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28529 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28531 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28532 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28533 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28534 | _kmFromBeleg | `input` | — | **ENTSCHEIDUNG** | — |
| 28535 | _kmFromBeleg | `input` | — | `205/65/R16C` | placeholder |
| 28536 | _kmFromBeleg | `input` | — | `65/55` | placeholder |
| 28550 | _kmFromBeleg | `input` | — | `15 Ziffern` | placeholder |
| 28558 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28565 | _kmFromBeleg | `input` | — | `ICCID / Nummer` | placeholder |
| 28569 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28664 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28667 | _kmFromBeleg | `input` | — | **ENTSCHEIDUNG** | — |
| 28670 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28696 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28700 | _kmFromBeleg | `input` | — | `z.B. Fahrt nach Wien` | placeholder |
| 28713 | _kmFromBeleg | `input` | file | **ENTSCHEIDUNG** | — |
| 28719 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28720 | _kmFromBeleg | `input` | number | `z.B. 52.3` | placeholder |
| 28721 | _kmFromBeleg | `input` | number | `z.B. 89.50` | placeholder |
| 28722 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28731 | _kmFromBeleg | `textarea` | — | `Was ist passiert?` | placeholder |
| 28736 | _kmFromBeleg | `input` | file | **ENTSCHEIDUNG** | — |
| 28747 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28749 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28750 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28751 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28752 | _kmFromBeleg | `input` | — | **ENTSCHEIDUNG** | — |
| 28806 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28807 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28808 | _kmFromBeleg | `input` | — | `z.B. 4491` | placeholder |
| 28809 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28810 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28811 | _kmFromBeleg | `input` | text | `00:00` | placeholder |
| 28812 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28813 | _kmFromBeleg | `input` | text | `00:00` | placeholder |
| 28814 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28815 | _kmFromBeleg | `input` | — | **ENTSCHEIDUNG** | — |
| 28821 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28822 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28823 | _kmFromBeleg | `input` | — | `Beschreibung...` | placeholder |
| 28838 | _kmFromBeleg | `textarea` | — | `205/65/R16C` | placeholder |
| 28839 | _kmFromBeleg | `textarea` | — | `65/55` | placeholder |
| 28840 | _kmFromBeleg | `textarea` | — | `5W-30` | placeholder |
| 28841 | _kmFromBeleg | `textarea` | — | `Mann HU ...` | placeholder |
| 28842 | _kmFromBeleg | `textarea` | — | **ENTSCHEIDUNG** | — |
| 28843 | _kmFromBeleg | `textarea` | — | **ENTSCHEIDUNG** | — |
| 28844 | _kmFromBeleg | `textarea` | — | `DOT4` | placeholder |
| 28845 | _kmFromBeleg | `textarea` | — | **ENTSCHEIDUNG** | — |
| 28860 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28861 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28862 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28863 | _kmFromBeleg | `input` | number | **ENTSCHEIDUNG** | — |
| 28864 | _kmFromBeleg | `input` | — | `Was wurde gemacht?` | placeholder |
| 28865 | _kmFromBeleg | `input` | — | `z.B. Ford Tulln` | placeholder |
| 28903 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 28904 | _kmFromBeleg | `input` | date | **ENTSCHEIDUNG** | — |
| 28905 | _kmFromBeleg | `input` | — | `z.B. Ölwechsel, Bremsen prüfen...` | placeholder |
| 28946 | _kmFromBeleg | `select` | — | **ENTSCHEIDUNG** | — |
| 29070 | FahrbewSection | `input` | file | **ENTSCHEIDUNG** | — |
| 29091 | AnmeldungSection | `input` | file | **ENTSCHEIDUNG** | — |
| 29158 | VGefahrstoff | `input` | file | **ENTSCHEIDUNG** | — |
| 29160 | VGefahrstoff | `input` | search | `🔍 Suchen (Name, Lieferant, Notiz)…` | placeholder |
| 29373 | BauprovisorienView | `input` | — | `z.B. Bauzaun Baustelle Müller` | placeholder |
| 29375 | BauprovisorienView | `input` | — | `Typ wählen oder eingeben` | placeholder |
| 29376 | BauprovisorienView | `select` | — | „Status" | label daneben |
| 29384 | BauprovisorienView | `input` | — | `Name, Nummer oder Matchcode…` | placeholder |
| 29397 | BauprovisorienView | `input` | — | „Kundennummer" | label daneben |
| 29398 | BauprovisorienView | `input` | — | „Kundenname" | label daneben |
| 29401 | BauprovisorienView | `input` | — | `Straße + Nr.` | placeholder |
| 29402 | BauprovisorienView | `input` | — | „PLZ" | label daneben |
| 29403 | BauprovisorienView | `input` | — | „Ort" | label daneben |
| 29404 | BauprovisorienView | `select` | — | „Optional einem Projekt zuordnen" | label daneben |
| 29409 | BauprovisorienView | `input` | — | `Straße` | placeholder |
| 29410 | BauprovisorienView | `input` | — | `PLZ` | placeholder |
| 29411 | BauprovisorienView | `input` | — | `Ort` | placeholder |
| 29412 | BauprovisorienView | `input` | — | `Beschreibung (optional) — z.B. „hin…` | placeholder |
| 29415 | BauprovisorienView | `input` | date | „Errichtung *" | label daneben |
| 29416 | BauprovisorienView | `input` | date | „Abbau (optional)" | label daneben |
| 29417 | BauprovisorienView | `input` | number | „Miete/Jahr €" | label daneben |
| 29433 | BauprovisorienView | `input` | — | `Code scannen oder eingeben` | placeholder |
| 29449 | BauprovisorienView | `textarea` | — | `Notizen (optional)` | placeholder |
| 29508 | BauprovisorienView | `input` | number | `Betrag €` | placeholder |
| 29509 | BauprovisorienView | `input` | file | **ENTSCHEIDUNG** | — |
| 29789 | WerkzeugView | `input` | — | `Inventar-Nr. eingeben (z.B. EK-E001)` | placeholder |
| 29806 | WerkzeugView | `input` | — | `Manuell: EK-...` | placeholder |
| 29818 | WerkzeugView | `input` | — | `Code (vom Label)` | placeholder |
| 29819 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 29937 | WerkzeugView | `input` | — | `🔍 Name, Seriennr, Inventar...` | placeholder |
| 29938 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 29939 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 29955 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 29973 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 29995 | WerkzeugView | `input` | text | `z.B. Lager, Baustelle Mödling…` | placeholder |
| 30013 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30042 | WerkzeugView | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 30047 | WerkzeugView | `input` | checkbox | **ENTSCHEIDUNG** | — |
| 30074 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30100 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30114 | WerkzeugView | `input` | date | **ENTSCHEIDUNG** | — |
| 30115 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30116 | WerkzeugView | `input` | number | **ENTSCHEIDUNG** | — |
| 30117 | WerkzeugView | `input` | — | `z.B. Hilti Service` | placeholder |
| 30118 | WerkzeugView | `input` | — | `Was wurde gemacht?` | placeholder |
| 30120 | WerkzeugView | `input` | file | **ENTSCHEIDUNG** | — |
| 30121 | WerkzeugView | `input` | file | **ENTSCHEIDUNG** | — |
| 30144 | WerkzeugView | `input` | — | `z.B. Hilti TE 30-A36` | placeholder |
| 30145 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30146 | WerkzeugView | `input` | — | **ENTSCHEIDUNG** | — |
| 30149 | WerkzeugView | `input` | — | `EK-E001 oder bestehenden Code einge…` | placeholder |
| 30161 | WerkzeugView | `input` | date | **ENTSCHEIDUNG** | — |
| 30162 | WerkzeugView | `input` | number | **ENTSCHEIDUNG** | — |
| 30166 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30167 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30168 | WerkzeugView | `select` | — | **ENTSCHEIDUNG** | — |
| 30169 | WerkzeugView | `input` | — | `Lager, Baustelle, Service...` | placeholder |
| 30174 | WerkzeugView | `input` | date | **ENTSCHEIDUNG** | — |
| 30175 | WerkzeugView | `input` | date | **ENTSCHEIDUNG** | — |
| 30176 | WerkzeugView | `textarea` | — | **ENTSCHEIDUNG** | — |
| 30188 | WerkzeugView | `input` | file | **ENTSCHEIDUNG** | — |

## 5. Klasse (d) — mit der rohen DOM-Schnittstelle gebaut (ausserhalb jeder React-Messung)

Nicht bestellt, beim Messen gefunden, und deshalb hier: **27 Stellen bauen Bedienelemente mit `document.createElement(...)`** statt mit React. Kein Abtaster dieses Auftrags und keiner von v3.9.957/958 sieht sie — sie suchen alle `React.createElement`/`h(`. Ich habe sie alle 27 gelesen.

| Zeile | Element | Sichtbarer Inhalt | Befund |
| --- | --- | --- | --- |
| Z17237/Z17247 | `button` (`_btn`) | `"◀"` / `"▶"` | 🔴 **OHNE NAMEN.** `_btn(txt,on)` setzt nur `b.textContent=txt`, kein `title`. Aufgerufen mit `"◀"` und `"▶"` fuer das Blaettern in der PDF-Vorschau. Name abgelesen aus dem `onclick` (`page--` / `page++`): „Vorige Seite" / „Nächste Seite". |
| Z5946 (`mkField`) | `input` ×4 | – | 🔴 **OHNE NAMEN.** Die Beschriftung daneben ist ein `div` (Z5945), KEIN `label`, und der `input` hat kein `id`. Fuer eine Vorlesehilfe stehen die zwei in keiner Beziehung. Betrifft alle vier Felder des Tank-Dialogs: „📅 Datum", „🛢 Liter *", „💶 Gesamtpreis (€)", „🛣 km-Stand" (Z5952-Z5955) - die Namen sind ABLESBAR, sie sind nur nicht verbunden. |
| Z5906 | `select` | KW-Auswahl | 🔴 **OHNE NAMEN.** Kein `aria-label`, kein `label`-Element; die Optionen tragen `_fmtKw(k)`. Name ablesbar aus dem Zusammenhang: „Kalenderwoche wählen". |
| Z6126 | `select` | Projektspalte einer Tabelle | 🔴 **OHNE NAMEN.** Die leere Option `"— Projekt wählen —"` ist ein PLATZHALTER, kein Name. Ablesbar: „Projekt wählen". |
| Z6139 | `textarea` | Tabellenzelle | 🔴 **OHNE NAMEN.** Name waere `col.key`/`col.label` - das steht im Code daneben. |
| Z6146 | `input` | Tabellenzelle | 🔴 **OHNE NAMEN.** Wie Z6139. |
| Z5863/Z5866 | `button` ×2 | `opts.cancelLabel\|\|'Abbrechen'`, `opts.confirmLabel\|\|'Bestätigen'` | grün - Vorgabewert ist ein WORT. |
| Z5913/Z5914 | `button` ×2 | `'Abbrechen'`, `'📥 Exportieren'` | grün |
| Z5972/Z5974 | `button` ×2 | `'Zurück'`, `'✓ Speichern'` | grün |
| Z6163 | `button` | `'✕'` | grün - `delBtn.title='Zeile aus Export entfernen (nicht aus DB)'` |
| Z6178/Z6180 | `button` ×2 | `cancelLabel`, `confirmLabel` | grün (Aufrufer uebergeben Literale) |
| Z6079 | `button` | `addRow.label\|\|'➕ Buchung hinzufügen'` | grün - `title` gesetzt |
| Z17228/Z17229 | `button` ×2 | `"↗ Extern"`, `"✕"` | grün - beide mit `title` |
| Z30155 ff. | `button` | `"✕ Abbrechen"` | grün - Text im `textContent` |
| Z3288, Z4667, Z13115, Z18038 | `a` ×4 | – | keine Bedienelemente: unsichtbare `a`-Elemente mit `download`, sofort `click()` und entfernt. Ein Name dafuer waere ein Name fuer etwas, das niemand bedient. |
| Z11338, Z11566 | `textarea` ×2 | – | keine Bedienelemente: Zwischenablage-Behelf, `position:fixed;left:-9999px`, sofort entfernt. |


**8 Befunde**: 2 Knoepfe (Z17247), 4 `input` (Z5946 ueber `mkField`, 4 Aufrufe), 1 `select` (Z5906), 1 `select` + 1 `textarea` + 1 `input` in der Tabellenzelle (Z6126, Z6139, Z6146) — zusammen 2 + 4 + 1 + 3 = **10 Bedienelemente ohne Namen**, auf 8 Codestellen.

## 6. Was ich NICHT gemessen habe

* **Ob eine Vorlesehilfe den Namen wirklich ansagt.** Das kann nur ein Schirmleser. Alles hier ist am QUELLTEXT gemessen. Ein `aria-label` im Code ist eine Absicht, kein Beleg.
* **Den berechneten Namen nach der HTML-Regel.** Ein Browser bildet den Namen in einer festen Reihenfolge (`aria-labelledby` → `aria-label` → Inhalt → `title`). Ich habe die ANWESENHEIT von `title`/`aria-label` gemessen und den Inhalt gelesen; ich habe die Reihenfolge nicht nachgebaut.
* **Kein Browser.** Ich habe keinen gestartet, also ist nichts hier im laufenden Bild nachgemessen. Ein Befund haengt ausdruecklich an einer Bildschirmbreite: Z16439 (`VForm`) verliert auf dem TELEFON den Reiternamen (`isMob?"":" "+t.l`) und zeigt dann nur ein Emoji. Das habe ich am CODE gelesen, nicht gesehen — welcher Schwellwert `isMob` gerade ist, habe ich nicht nachgeschlagen, und in v3.9.955 hat er sich schon einmal geaendert (der v3.9.960-Kommentar an Z19889 sagt: von `ww<768` auf 600 px). Ein Befund, der an einer Schwelle haengt, ist nur so genau wie die Schwelle.
* **Ob ein Element ueberhaupt gerendert wird.** Eine unerreichbare Ansicht hat keine namenlosen Knoepfe, weil sie keine Knoepfe hat. Der Riegel von e6202e5 haelt fest, dass genau EINE Komponente nie gerendert wird; ob eine der Stellen hier darin liegt, habe ich nicht geprueft.
* **Die Dopplung.** Eine Stelle in einer `.map`-Schleife ist EINE Codestelle und im Bild N Knoepfe. Alle Zahlen hier sind CODESTELLEN. Die Zahl der Knoepfe auf dem Schirm ist groesser, und zwar um einen Faktor, den nur die Daten kennen.
* **`aria-hidden`, `disabled` und die Reihenfolge.** Ein Knopf, der `aria-hidden` traegt oder dauerhaft `disabled` ist, ist ein anderer Fall. Ich habe `disabled` gesehen (es steht bei den meisten „stumm waehrend der Arbeit"-Faellen) und nicht systematisch gezaehlt.
* **Alles, was nicht `button`/`a`/`input`/`select`/`textarea` und nicht `onClick` ist.** Kein `onChange` auf einem `div`, kein `onKeyDown` ohne `onClick`, keine Formulare, keine Ueberschriften-Ordnung, kein Farbkontrast, keine Reihenfolge beim Tabben, keine Fokusfalle in den Dialogen.
* **Die Namen in Klasse (b).** 273 Stellen haben einen Namen; ob das Wort gut ist, ist eine Wortwahl und kein Messwert. Ich habe eine Verdachtsliste gebaut und kein Urteil gesprochen.
* **Die Daten.** Bei Z19829 (`w.vorname||w.n`) haengt der Befund daran, ob in der Tabelle beide Felder leer sein koennen. Ich habe nicht in die Datenbank gesehen — auftragsgemaess — und entscheide es deshalb nicht.
* **Die 183 Symbol-/Emoji-Knoepfe erneut.** Abschnitt 0 nennt die 14, die durch die drei Blindstellen von v957/958 gefallen sind. Ich habe die uebrigen 169 nicht einzeln gegengelesen; dass sie einen `title` oder ein `aria-label` TRAGEN, ist gemessen, ob das Wort passt, nicht.

## 7. Wie das nachzumessen ist

```
python scripts/bedienelemente_scan.py          # die Zahlen
python scripts/bedienelemente_scan.py koeder   # die 10 Selbstproben
python scripts/bedienelemente_scan.py json     # jede Stelle einzeln
python scripts/bedienelemente_gegenprobe_v957_958.py  # was v957/v958
                                               #   wirklich sehen
python scripts/bedienelemente_bericht.py       # diesen Bericht neu
```

`scripts/bedienelemente_scan.py` ist ein MESSGERAET, kein Riegel. Es steht bewusst nicht unter `tests/`: ein Riegel behauptet, die Zahl sei null, und diese Zahl ist nicht null. Wer daraus einen Riegel macht, braucht je Klasse eine namentliche Ausnahmeliste MIT GRUND — und die Koeder muessen mit.

