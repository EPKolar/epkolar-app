# CSS-Regeln mit `!important`, die eine Schriftgroesse erzwingen

Messung vom 28.09.2026. Reiner Mess-Bericht — an `index.html` und an `tests/` wurde
nichts geaendert.

---

## 0. UMFANG DIESER MESSUNG

| Was | Wert |
| --- | --- |
| Gemessene Datei | `C:\repos\epkolar-app\index.html` |
| Stand NACHHER | Arbeitskopie, `APP_VERSION="3.9.967-supabase"` (Kopf `a438b5a`) |
| Stand VORHER | `git show 4526b70:index.html` — v3.9.965, der Vorgaenger von `4304110` |
| Der hebende Commit | `4304110` „v3.9.966: Arbeitsscheine - Lesbarkeit. Der Boden war CSS, nicht der Quelltext" |
| Gemessener Bereich | AUSSCHLIESSLICH der Inhalt der `<style>`-Bloecke, plus — getrennt ausgewiesen — der zur Laufzeit eingehaengte Stilblock `GCSS()` (Zeilen 6289–6454) |
| NICHT gemessen | der laufende Browser. Alle Aussagen sind Quelltext-Aussagen ueber die STILREGELN, keine `getComputedStyle`-Messung. |

Der Vorgaenger ist selbst ermittelt (`git log --oneline`, dann `git rev-parse 4304110^`
→ `4526b708ee4e5dcbbe99130c745329341743013d`), nicht uebernommen.

### Warum NICHT im rohen Dateitext gezaehlt wird

`index.html` fuehrt lange deutsche Kommentare, die CSS-Regeln **woertlich zitieren**.
Das ist keine Vermutung, das ist gemessen:

```
ROHTEXT (ganze Datei)          font-size + !important : 30
<style>-Bloecke, gehaertet     font-size + !important : 27
GCSS() (Laufzeit-Stilblock)    font-size + !important :  2
```

Die Differenz sitzt unter anderem bei Zeichen-Offset 234 305, mitten im
`APP_VERSION`-Kommentar:

> `… eine CSS-Regel mit !important macht daraus 10 px. `.kpi-grid.epk-leiste > div > div:nth-child(4) { font-size: 10px !important }` ist der Traeger der 'offen'/'fertig'/'storniert'-Unterzeilen …`

Ein Zaehler ueber den Rohtext misst hier seine **eigene Begruendung** mit: er wird gruen,
sobald jemand sie hinschreibt, und rot, wenn jemand sie loescht. Gezaehlt wird deshalb
nur innerhalb der Stilbloecke.

### 🔴 UND DIE BLOCKEXTRAKTION SELBST HAT DENSELBEN FEHLER

Das naheliegende Muster `<style[^>]*>(.*?)</style>` ist an **dieser** Datei falsch.
`index.html` fuehrt **21** oeffnende `<style>` und nur **20** schliessende `</style>`.
Der Ueberschuss steht in Zeile 9502 — **innerhalb eines deutschen JS-Kommentars**:

> `… diese Huelle setzt fontFamily INLINE, und inline schlaegt jede Regel im <style> …`

Das naive Muster paart dieses Kommentar-`<style>` mit dem naechsten echten `</style>`
in Zeile 11228 und liest damit rund **1 700 Zeilen JavaScript als CSS**. Gemessen:

```
naive Extraktion       : 291 511 Zeichen  (davon 244 061 = 84 % JavaScript)
gehaertete Extraktion  :  47 450 Zeichen
```

Die Regel, die hier hilft: **vor einem `</style>` gilt das LETZTE `<style>`.**
Heute aendert das am Zaehlergebnis nichts (beide finden 26 bzw. 27 Regeln), aber der
Fehler ist scharf. Mutationsprobe, in beide Richtungen belegt:

```
Zitat  /* die Regel .zitat{font-size: 9px !important;} war der Traeger … */
in den verschluckten JS-Bereich gesetzt:
   naive Extraktion meldet    : [('9', '/* Begruendung: die Regel .zitat')]   <- FALSCHER ALARM
   gehaertete Extraktion      : NICHTS
dieselbe Zeichenfolge als ECHTE Regel im Hauptstilblock:
   gehaertete Extraktion      : [('9', '.zitat')]                              <- richtig gemeldet
```

---

## 1. DIE ZEHN REGELN

Zeilennummern beziehen sich auf die heutige Arbeitskopie.

| # | Zeile | Wahlmuster | Kontext (`@media`) | alt | neu | Trifft welche Bauteile | Urteil |
| - | ----- | ---------- | ------------------ | --- | --- | ---------------------- | ------ |
| 1 | 172 | `.kpi-grid.epk-leiste > div > div:nth-child(2)` | **keiner** — alle Breiten | 11 px | **12 px** | Die Beschriftungen der Kennzahlleiste. Die Klassenkombination `kpi-grid epk-leiste` steht an **genau einer** Stelle der App: Zeile 11380, in `ArbeitsscheinView` (ab Zeile 10810). Ansicht: **Arbeitsscheine**. | **ALTLAST** |
| 2 | 174 | `.kpi-grid.epk-leiste > div > div:nth-child(4)` | **keiner** — alle Breiten | 10 px | **12 px** | Dasselbe Element wie #1: die Unterzeilen `offen` / `fertig` / `storniert` der Arbeitsschein-Kennzahlleiste. Das ist der im Commit benannte Traeger des Befunds (inline 12 px → berechnet 10 px). | **ALTLAST** |
| 3 | 274 | `th` | `max-width: 600px` | 11 px | **12 px** | Jeder Tabellenkopf der App im Telefonformat. Besonders auffaellig: **eine Zeile darueber** (273) steht `td, th { font-size: 12px !important }`. Die `th`-Regel hat den eigenen Zwilling um 1 px **unterboten** — Kopfzellen waren kleiner als ihre Datenzellen. | **ALTLAST** |
| 4 | 284 | `.ber-table` | `max-width: 600px` | 11 px | **12 px** | **Nichts.** Die Klasse `ber-table` kommt in der ganzen Datei nur in CSS vor (Zeilen 284/285 und `GCSS()` 6355/6356) — **null** Treffer als `className` oder `class=`. Ein Kommentar in Zeile 3085 sagt es selbst: „Diese Tabelle hat KEINE .ber-table-Klasse". | **ALTLAST, dazu wirkungslos** |
| 5 | 307 | `.badge` | `max-width: 600px` | 11 px | **12 px** | **Nichts im Hauptdokument.** `class="badge"` steht ausschliesslich in HTML-Zeichenketten fuer Druck-/Export-Fenster (Zeilen 16367, 16370, 16821, 16826). Das sind **eigene Dokumente** mit **eigenen** Stilbloecken (16381, 16829) — die `@media`-Regel des Hauptdokuments erreicht sie nicht. Die `badge:`-Vorkommen in Zeilen 9431 und 21172 ff. sind JS-Objektfelder, keine Klassennamen. | **ALTLAST, dazu wirkungslos** |
| 6 | 319 | `svg text` | `max-width: 600px` | 10 px | **10 px — unveraendert** | Die Achsen- und Wertbeschriftungen der Diagramme. 8 Stellen erzeugen `createElement('text', …)`. | **GEWOLLT** — Achsenschriften stehen dicht nebeneinander; 10 → 12 px kann sie zum Ueberlappen bringen. Eigener Schritt, eigene Messung. |
| 7 | 389 | `.tab-bar button` | `max-width: 414px` | 11 px | **12 px** | Die Reiterleisten. `className: "tab-bar"` an fuenf Stellen: 9757 (Hauptnavigation der Projektakte auf Mobil), 11386 (Arbeitsscheine), 15845, 22810, 29775. | **ALTLAST** |
| 8 | 419 | `.bottom-nav button > span:nth-child(2)` | `max-width: 380px` | **9 px** | **12 px** | Die Beschriftungen der fixen Fussnavigation: Home / Baustelle / Zeit / Fuhrpark / Mehr. Der Knopf (Zeile 9830) fuehrt zwei `span` — erstes = Emoji (20 px), zweites = Beschriftung (Zeile 9832). 9 px war der **kleinste Wert der ganzen App**. | **ALTLAST** — und die schaerfste: die Inline-Angabe steht seit v3.9.943 bewusst auf `UI.fMeta` = 12, die CSS-Regel hat sie auf 9 zurueckgerechnet. |
| 9 | 442 | `.header-row p` | `max-width: 340px` | 11 px | **12 px** | Die Unterzeilen unter den Ansichts-Ueberschriften, z. B. Zeile 10231 (`MitarbeiterView`) und 11372 (`ArbeitsscheinView`). `header-row` kommt 32-mal vor. | **ALTLAST** |
| 10 | 470/471 | `[style*="📤"][style*="Änderungen warten"],`<br>`div:has(> button[title*="Jetzt sync"])` | `max-width: 600px` | 11 px | **12 px** | **Nichts — beide Arme sind tot.** Arm A sucht die Zeichenfolge „Änderungen warten" im **`style`-Attribut**; sie steht aber im **Textinhalt** des Banners (Zeile 14712: `"📤 "+pendingCount+" Änderung…warten auf Sync"`). Ein `style`-Attribut enthaelt diesen Text nie. Arm B verlangt `button[title*="Jetzt sync"]`; **kein** Knopf der Datei traegt so ein `title` — der Knopf in Zeile 14713 fuehrt „🔄 Jetzt sync" als **Text**, ohne `title`. Die einzigen `title` mit „Sync" sind 9761 und 23867 und passen nicht. | **ALTLAST, dazu wirkungslos** |

### Zaehlung

* **9 von 10 = ALTLAST.** Einzige gewollte Ausnahme: `svg text` (#6).
* **3 der 9 Altlasten trafen ueberhaupt kein Bauteil** (#4 `.ber-table`, #5 `.badge`, #10 Sync-Banner). Ihr Heben war richtig, aber wirkungslos — der Befund liegt woanders, naemlich bei #1/#2/#3/#7/#8/#9.
* Ergebnis der Hebung, gemessen im Stilblock:

```
VORHER  (4526b70) : 10 Regeln unter 12 px
NACHHER (a438b5a) :  1 Regel  unter 12 px   -> svg text, 10px, @media (max-width: 600px)
```

### Eine Nebenwirkung, die schon gemessen ist und hier nicht verschwiegen wird

Der Kommentar in Zeile 9832 haelt fuer #8 fest: der Schlitz je Fussnavigations-Knopf ist
74 px breit. Bei 10 px war **ein** Name gekuerzt (Monatsabrechnung), bei 12 px sind es
**fuenf** (Monatsabrechnung 112 px, Abwesenheiten 89, Bauprovisorien 88, Gefahrenstoffe 86,
Zeiterfassung 80). Die 9-px-Regel hat diese Kuerzung nicht verhindert — sie hat sie
**verdeckt**. Das ist eine Textentscheidung (Kurznamen je Reiter) und liegt bei Sebastian.

---

## 2. ZUSATZMESSUNG A — ALLE `font-size` mit `!important`

**Umfang: die `<style>`-Bloecke der Datei, gehaertet extrahiert.**

| | VORHER | NACHHER |
| - | ------ | ------- |
| `font-size` + `!important`, gesamt | **27** | **27** |
| davon mit px-Wert | 26 | 26 |
| davon ohne px-Wert (`font-size: 0 !important`) | 1 | 1 |
| davon **unter** 12 px | **10** | **1** |
| genau 12 px | 7 | 16 |
| ueber 12 px (14/16/18/20/22 px) | 9 | 9 |

Dazu, **ausserhalb** der `<style>`-Bloecke und deshalb von jedem Blockzaehler unsichtbar:

| Ort | Regeln | Werte |
| --- | ------ | ----- |
| `GCSS()`, Zeilen 6289–6454 | **2** | `input,select,textarea` 16 px; dieselben bei `min-width:601px` 14 px |

`GCSS()` ist ein JS-Template-Literal, das an sechs Stellen (7145, 7885, 9457, 9495, 9497,
9503) als `React.createElement('style', {}, GCSS())` in den Baum gehaengt wird. Im
**laufenden** Dokument ist das ein vollwertiger Stilblock; im **Quelltext** steht kein
`<style>` davor. **Gesamt erreichen also 29 `font-size`-Regeln mit `!important` den
Browser, nicht 27.**

### Zwei Sonderfaelle, die kein px-Zaehler sieht

* **Zeile 433: `font-size: 0 !important`** auf `.header-row .mob-stack button` bei
  `max-width: 340px` („Text weg, Icon bleibt"). Das ist ein erzwungener Wert **unter**
  12 px, den jedes Muster mit `\d+px` uebersieht. Er ist allerdings **selbst tot**: Zeile
  438 setzt **dasselbe** Wahlmuster bei gleicher Spezifitaet auf `16px !important` und
  steht spaeter — 16 px gewinnt.
* Zeile 16829 (Export-Fenster) fuehrt `.badge{…font-size:10px…}` **ohne** `!important`.
  Ausserhalb der `!important`-Grundgesamtheit, aber unter 12 px.

---

## 3. ZUSATZMESSUNG B — erzwungene GROESSEN unter 44 px

**Umfang: dieselben `<style>`-Bloecke. Gemessen wurden `width`, `min-width`, `height`,
`min-height`, `padding` (und die vier Einzelrichtungen) — jeweils nur mit `!important`.**

```
Groessen-Deklarationen mit !important und px-Wert : 44
davon mit einem px-Wert UNTER 44                  : 24   (vorher wie nachher identisch)
davon HARTE Masse (width/min-width/height/min-height) : 3
davon padding                                     : 21
```

Die Hebung von v3.9.966 hat an dieser Eigenschaft **nichts** veraendert — die Zahlen sind
vorher und nachher gleich.

### Die drei harten Masse

| Eigenschaft | Wert | Wahlmuster | Kontext | Einordnung |
| --- | --- | --- | --- | --- |
| `height` | 24 px | `header img[alt="EP Kolar"]` | `max-width: 600px` | Firmenlogo, kein Tippziel — unkritisch |
| `height` | 24 px | `header img[alt="EP Kolar"]` | `max-width: 380px` | dito |
| `min-width` | 40 px | `.header-row .mob-stack button` | `max-width: 340px` | **Tippziel, 4 px unter der 44-px-Schwelle.** Die einzige der drei, die zaehlt. |

### Die auffaelligsten `padding`-Werte

| Wert | Wahlmuster | Kontext | Anmerkung |
| --- | --- | --- | --- |
| `4px 1px` | `.bottom-nav button` | `max-width: 380px` | **1 px seitlich** auf den fuenf Knoepfen der Fussnavigation — der schaerfste Wert der Messung |
| `3px 8px` | `.badge` | `max-width: 600px` | dazu `min-height: 24px` — **ohne** `!important` |
| `4px 6px` | `.ber-table th, .ber-table td` | `max-width: 600px` | trifft nichts (Klasse wird nie vergeben, s. #4) |
| `5px 6px` | `.header-row .mob-stack button` | `max-width: 380px` | Tippziel |
| `6px 6px` | `td, th` | `max-width: 600px` | |
| `7px 8px` | `.header-row .mob-stack button` | `max-width: 414px` | Tippziel |
| `8px 10px` | `.kpi-grid.epk-leiste > div` | **keiner** | |

### 🔴 DER BEFUND IST HIER EIN ANDERER ALS BEI DER SCHRIFT

Die 1 952 Tippziele unter 44 px kommen **nicht** aus erzwungenen `!important`-Groessen —
es gibt davon genau **eine** (`min-width: 40px`). Die Krankheit ist an dieser Eigenschaft
**seitenverkehrt**:

* **Zeile 291: `button { min-height: 44px; font-size: 12px !important; }`** — die Schrift
  ist erzwungen, der **44-px-Boden nicht**. Ebenso Zeile 247 (`[role="button"]`) und
  `GCSS()` 6358 (`.form-tabs button{min-height:44px}`).
* Ein nicht erzwungener Wert **verliert gegen jede Inline-Angabe**. Beispiel, nachgesehen:
  der Knopf in Zeile 14713 traegt inline `minHeight:32` — 32 px gewinnen gegen die
  44-px-Regel der Zeile 291.
* Erzwungen wird der Boden nur an **sechs** Stellen: Zeilen 337 und 369
  (`.header-row .mob-stack button`), 402, 520 (`input[type=checkbox|radio|submit|button]`),
  536 (`table button`, `[class*="list"] button`, `[style*="display:flex"] > button`) und
  544/545 (Schliessen-Knoepfe, dort auch `min-width`). Ueberall sonst ist der Boden
  ein **Vorschlag**, kein Boden.

Fuer einen Riegel heisst das: bei der Schrift muss man nach `!important` **suchen**, bei
der Groesse muss man sein **Fehlen** suchen.

---

## 4. EMPFEHLUNG FUER DEN RIEGEL

Gemeint ist `tests/test_css_boden_12px_v966.py`. Er ist deutlich besser als sein Vorgaenger
`test_fahrzeuge_schriftgroesse_v965.py` (der nur den Quelltext las) und er hat bereits eine
Grundgesamtheits-Gegenprobe und einen Kommentar-Koeder. Er hat trotzdem **drei belegte
Luecken**, und die erste ist nicht theoretisch.

### 🔴 Luecke 1 — `GCSS()` wird NICHT gemessen. Mutationsprobe gefahren, Riegel schweigt.

`stilbloecke()` liest `<style[^>]*>(.*?)</style>`. `GCSS()` ist ein Template-Literal ohne
`<style>` im Quelltext und faellt vollstaendig heraus — 18 767 Zeichen echtes,
ausgeliefertes CSS. Gemessen, nicht vermutet:

```
REGEL-Treffer in GCSS(), vom Riegel NICHT gesehen : 2   (16px / 14px, input,select,textarea)
MUTATION  input,select,textarea{font-size:16px !important}  ->  9px !important
   Riegel meldet: NICHTS
```

**Eine 9-px-Regel im ausgelieferten Stilblock, und der Riegel bleibt gruen.** Das ist
genau die Krankheit, gegen die er gebaut wurde, eine Ebene hoeher.

Der bestehende Koeder deckt das nicht ab und **kann** es nicht: er baut sein Pruefstueck als
`'<html><head><style>…</style></head>'` — er benutzt dieselbe Schreibweise, die der Riegel
kennt, und **teilt damit genau dessen Luecke**. „Selbstprobe vorhanden" belegt hier nichts.

**Zu tun:** die Grundgesamtheit aus **beiden** Quellen bilden —
(a) den `<style>`-Bloecken und (b) jedem JS-Template-Literal, das als Stilblock in den Baum
geht (heute `GCSS()`, Zeilen 6289–6454; auffindbar ueber `createElement('style'`).
Ein **eigener Koeder je Quelle**: eine 9-px-Regel in einem `<style>`-Block **und** eine in
einem Laufzeit-Literal muessen **beide** gemeldet werden. Dazu eine Zaehlprobe: findet der
Riegel in `GCSS()` **null** Regeln, ist die Quelle nicht angeschlossen — das ist rot, nicht
gruen.

### 🔴 Luecke 2 — die Blockextraktion liest 84 % JavaScript

Belegt oben in Abschnitt 0: 244 061 der 291 511 gelesenen Zeichen sind JavaScript, weil ein
`<style>` in einem deutschen Kommentar (Zeile 9502) die Paarung verschiebt. Die
Mutationsprobe erzeugt daraus einen **falschen Alarm** aus einem blossen Zitat — dieselbe
Fehlerform, die der Riegel bei sich selbst schon einmal gefunden hat.

**Zu tun:** vor einem `</style>` gilt das **letzte** `<style>`. Zusaetzlich eine Zaehlprobe
auf die Groesse der Grundgesamtheit (heute ~47 KB CSS) — springt sie auf 290 KB, liest der
Riegel Programmtext. Und: **CSS-Kommentare innerhalb der Bloecke zuerst entfernen** und das
belegen. Heute gibt es dort kein Zitat (27 mit Kommentaren = 27 ohne), morgen schreibt
jemand eins hin.

### 🔴 Luecke 3 — der Riegel misst die ANWESENHEIT einer Regel, nicht ihre WIRKUNG

Drei der neun gehobenen Regeln (#4, #5, #10) treffen **kein einziges Bauteil**. Der Riegel
ist an ihnen gruen und war es auch, als sie noch 11 px erzwangen — er haette dasselbe
gesagt. Umgekehrt kann eine Schrift auf dem Schirm unter 12 px landen, **ohne** dass
irgendwo `!important` steht:

* durch eine **Inline**-Angabe unter 12 px (die Fussnavigation hatte genau das, bevor
  v3.9.943 sie hob);
* durch ein Kind mit **eigenem** Inline-Wert — der Commit nennt es selbst: sieben `span`
  **innerhalb** von `th` mit inline 10 px, die der gehobene `th`-Wert nicht erreicht;
* durch `font-size: 0`, `em`/`rem`/`%`/`pt` oder die `font`-Kurzform — das heutige Muster
  verlangt `\d+px` und sieht Zeile 433 nicht;
* durch eine Regel, die hoeher gewinnt als die gehobene (Zeile 438 schlaegt Zeile 433 —
  hier sogar zugunsten der Lesbarkeit, aber das Prinzip traegt in beide Richtungen).

**Woran der Riegel scheitert, wenn er nur im Quelltext liest:** an allem, was erst aus dem
**Zusammenspiel** entsteht — Kaskade, Spezifitaet, Reihenfolge, Vererbung, Inline gegen
Regel, und ob das Wahlmuster ueberhaupt ein Element erreicht. Der Quelltext kann diese
Frage **prinzipiell nicht beantworten**; er ist die falsche Grundgesamtheit fuer sie.

**Zu tun — die drei Proben, nach Wert geordnet:**

1. **Die Wirkungsprobe.** Die einzige Messung, die die Frage wirklich beantwortet, ist
   `getComputedStyle(el).fontSize` am **gerenderten** Baum, bei 390 px und 1440 px, ueber
   die Ansichten. Der Pruefstand des Hauses kann das bereits — der Commit berichtet genau
   solche Vorher/Nachher-Zahlen (`as_liste 24 → 2`, `berichte 29 → 7`). Diese Zahlen
   gehoeren **in einen Riegel**, nicht nur in eine Commit-Nachricht. Alles andere ist
   Vorfilter.
2. **Die Erreichbarkeitsprobe.** Fuer jedes Wahlmuster der Ausnahme- **und** der
   Boden-Liste pruefen, ob es im gerenderten Baum ueberhaupt ein Element trifft
   (`document.querySelectorAll(sel).length`). Trifft es nichts, ist die Regel tot und
   gehoert benannt — sonst pflegt man neun Jahre lang Regeln fuer Bauteile, die es nicht
   gibt (`.ber-table`, `.badge`, Sync-Banner).
3. **Die Quelltextprobe** (die heutige) bleibt — als **schneller Vorfilter**, mit den
   Korrekturen aus Luecke 1 und 2, und mit einem Muster, das auch `font-size: 0` und
   nicht-px-Einheiten meldet statt sie stumm zu ueberspringen.

### Zwei Kleinigkeiten am bestehenden Riegel

* `REGEL` begrenzt das Wahlmuster auf 120 Zeichen (`[^{};]{1,120}`) und den
  Deklarationsblock auf 300 (`[^{}]{0,300}?`). Das Sync-Banner-Wahlmuster (#10) ist mit
  ~105 Zeichen schon nah dran; ein weiterer Arm laesst die Regel unsichtbar werden. Eine
  Laengenschranke ohne Koeder ist eine stille Kappung.
* `test_die_ausnahme_ist_noch_die_ausnahme` prueft `len(AUSNAHMEN) == 1`. Richtig — aber
  die Ausnahme sollte zusaetzlich ihre **Wirkung** belegen muessen (Probe 2 oben: `svg text`
  trifft die 8 Diagramm-Beschriftungen). Eine Ausnahme, deren Wahlmuster nichts mehr
  trifft, ist eine Attrappe mit Begruendung.

---

## 5. WAS DIESE MESSUNG NICHT ABDECKT

1. **Den laufenden Browser.** Es wurde kein `getComputedStyle` gefahren, keine Ansicht
   geoeffnet, keine Breite gerendert. Alle Aussagen sind Aussagen ueber **Stilregeln im
   Quelltext**. Ob nach der Hebung am Schirm tatsaechlich nirgends mehr unter 12 px steht,
   sagt diese Messung **nicht** — die 24 → 2 und 29 → 7 des Commits sind fremde Zahlen,
   hier nicht nachgemessen.
2. **Inline-Schriftgroessen.** Kein einziger `style={{fontSize:…}}`-Wert wurde gezaehlt.
   Der Commit nennt selbst sieben `span` in `th` mit inline 10 px in der Berichte-Ansicht,
   die stehen geblieben sind. Diese Grundgesamtheit ist hier gar nicht angefasst.
3. **Schriftgroessen ohne `!important`.** Gemessen wurde ausschliesslich die
   `!important`-Grundgesamtheit. Eine gewoehnliche Regel `font-size: 10px` ohne `!important`
   taucht in **keiner** Zahl dieses Berichts auf — einschliesslich der gefundenen
   `.badge{font-size:10px}` in Zeile 16829.
4. **Die Kaskade.** Ueberdeckungen wurden nur dort geprueft, wo sie ins Auge sprangen
   (Zeile 433 gegen 438, Zeile 273 gegen 274). Es gab **keine** systematische
   Spezifitaets-Aufloesung. Zwei Regeln koennen einander ueberdecken, ohne dass dieser
   Bericht es bemerkt.
5. **Die Erreichbarkeit ist am Quelltext geprueft, nicht am Baum.** Fuer `.ber-table`,
   `.badge` und das Sync-Banner wurde nach `className`, `class=` und `title` gesucht und
   nichts gefunden. Ein zur **Laufzeit** zusammengesetzter Klassenname (etwa
   `"ber-" + x + "-table"`) waere dieser Suche entgangen. Das ist eine **starke**, aber
   keine erschoepfende Aussage.
6. **Druck- und Export-Dokumente.** Die Stilbloecke in den Zeilen 16265 ff. (`printForm`),
   16381 und 16829 gehoeren zu **eigenen** Dokumenten. Sie sind in den Zahlen des
   Abschnitts 2 enthalten (sie sind `<style>`-Bloecke), aber sie beschreiben **Papier**,
   nicht den Schirm. Fuer sie gilt die 12-px-Schwelle nicht in derselben Weise.
7. **Andere Ausgabewege.** `style.cssText`-Zuweisungen aus JavaScript (z. B. Zeile 6176:
   `note.style.cssText='font-size:11px;color:'+dm+…`) sind **Inline**-Angaben und hier
   nicht gezaehlt. Es gibt davon mehr als eine.
8. **Die Nebenwirkung der Hebung.** Ob die neun gehobenen Regeln irgendwo Ueberlauf oder
   Textverlust erzeugen, ist hier **nicht** gemessen. Der Commit behauptet „kein Ueberlauf
   ist gestiegen"; fuer die Fussnavigation nennt er zugleich fuenf gekuerzte Namen statt
   einem. Beides ist uebernommen, nicht nachgeprueft.
9. **`sw.js`.** Der Commit aendert auch `sw.js`; diese Datei wurde nicht gemessen.
