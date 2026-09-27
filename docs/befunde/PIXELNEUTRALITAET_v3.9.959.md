# Pixelneutralität v3.9.959 — drei Behauptungen am gerenderten Schirm

Stand: 27.09.2026 · gemessene Datei `index.html`, md5 `14b5ccf7caff920d60c77107d132b63f`
(v3.9.959, `origin/main = e6202e5`) · Sonde `scripts/pixelneutralitaet_959_messen.py`

An `index.html` wurde nichts geändert. Angelegt wurden nur die Sonde und dieser
Bericht; die Vergleichsstände liegen als git-ignorierte `_mess_pn_*.html` im
Wurzelverzeichnis.

---

## 0. Zuerst: der im Auftrag genannte Vergleichsstand ist der falsche

Der Auftrag nennt `84b8e72` als „Stand VOR dem Umbau (dort ist es noch ein div)".
Das ist nicht so, und zwar nachprüfbar:

```
$ git show --stat --oneline 84b8e72
84b8e72 Doku: S-1 berichtigt (33 statt 2, gebaut statt offen) und der Zusagen-Wortlaut
 docs/ABSCHLUSSBERICHT_UI_UMBAU.md   | 89 ++++++---
 docs/handoffs/HANDOFF_2026-09-26.md | 27 +++--
 2 files changed, 92 insertions(+), 24 deletions(-)
```

`84b8e72` ist ein **Doku-Commit**; `index.html` ist dort unverändert und trägt
`APP_VERSION="3.9.957-supabase"`. Der Titel steht dort schon als `h2`
(Zeile 29446), und die beiden Umschalter tragen schon `title`/`aria-label`
(Zeilen 19184, 28238). Gegen diesen Stand gemessen wäre bei **beiden**
Behauptungen 1 und 2 „null Unterschied" herausgekommen — und das hätte
**nichts belegt**, weil beide Stände dieselbe Änderung tragen. Das ist genau
die Form „leere Grundgesamtheit besteht keine Probe".

Gemessen wurde deshalb gegen den Commit **direkt vor** der jeweiligen Änderung:

| Behauptung | Änderung in | Vergleichsstand VOR der Änderung | Kopie |
|---|---|---|---|
| 1 (D9, div→h2) | `a4b50e5` v3.9.956 | `11e365a` v3.9.955 | `_mess_pn_v955_11e365a.html` md5 `76bb4c4e49…` |
| 2 (S-1, title/aria) | `09d0153` v3.9.957 + `cd3ea13` v3.9.958 | `a4b50e5` v3.9.956 | `_mess_pn_v956_a4b50e5.html` md5 `d646cb4c73…` |
| 3 (VBautag BP_MOB) | `11e365a` v3.9.955 | `a34d535` v3.9.954 | `_mess_pn_v954_a34d535.html` md5 `359be14440…` |

Dass die Stände sich unterscheiden, ist je Lauf am md5 belegt und die Sonde
sagt ausdrücklich „BEIDE STAENDE SIND BYTEIDENTISCH", falls nicht.
Die Gegenprobe im Quelltext:

* v3.9.955 Zeile 29446: `h('div',{style:{fontSize:20,fontWeight:800,color:V.tx}},"🚧 Bauprovisorien")` — **div, ohne `margin:0`**
* v3.9.956 Zeilen 19184/28238: die Umschalter-Knöpfe **ohne** `title`/`aria-label`
* v3.9.954 Zeile 19640: `const isMob=ww<768;` statt `ww<BP_MOB`

---

## 1. Wie gemessen wird

Die Sonde benutzt die vorhandenen Sonden (`mob_ansicht_messen`,
`b3_vier_ansichten_messen`, `b3_stufen_8_11_messen`, `b3_stufen_12_15_messen`)
für Server, Saat, Navigation und den Schriftzähler und legt drei Messgeräte
darauf:

* **RASTER_JS** — für **jedes** Element der Ansicht mit sichtbarem Kasten und
  Text bis 90 Zeichen eine Zeile. Schlüssel = normierter Text + `#` + laufende
  Nummer dieses Textes in Dokumentordnung; Wert = `tag, x, y, w, h`. Der
  Schlüssel überlebt `div`→`h2` (der Text bleibt, die Stelle in der Ordnung
  bleibt), das **Tag steht im Wert**, nicht im Schlüssel — sonst wäre gerade der
  zu messende Fall unvergleichbar. Damit fällt jede Verschiebung der **ganzen
  Ansicht** auf, nicht nur die des Titels.
* **TITEL_JS** — Feinmessung am Titelelement selbst (tiefstes Element mit genau
  diesem Text): Tag, Kasten, berechnete Schriftgröße/-dicke, Zeilenhöhe,
  Außenabstand — plus Kopfzeile und das Element **darunter**.
* **NAMEN_JS** — zugänglicher Name je Knopf, am **gerenderten** Element:
  `aria-label`, sonst `title`, sonst Text mit mindestens einem Buchstaben.

Umgebung je Lauf: Chromium (Playwright, headless), `color_scheme=dark`,
`is_mobile` und `has_touch` unter 600 px, Rolle `admin`, `monteurId=M1`,
`**/rest/v1/**` und `**/auth/v1/**` abgebrochen, Saat in die IndexedDB
`epkolar_offline` (plus `projektCache`-Schlüssel `bt_P1` für die
Bautagebuch-Einträge, weil `ODB.loadProj("bt_"+p.id)` dort liest und die
vorhandene Saatfunktion nur unter dem Schlüssel `data` schreibt).

### Die Köder

| Köder | was er prüft | Ergebnis |
|---|---|---|
| K-A | Saat sichtbar (`SAATWORT` in der Ansicht) | angeschlagen in allen Läufen (5–6 Treffer) |
| K-B | Ansichtsnachweis: ein Merkmal, das NUR diese Ansicht trägt, plus Abwesenheit des Nachbarmerkmals | angeschlagen in allen Läufen |
| K-C | der Titeltext MUSS in beiden Ständen gefunden werden | angeschlagen |
| K-D | `Kalibrierungsintervallpruefung` darf NICHT gefunden werden | angeschlagen (nicht gefunden) |
| K-E | 340 px: Klasse `header-row` anhängen → Schriftgröße MUSS auf 16px fallen | siehe §2 |
| K-F | Kunstknopf mit nur `⊗`, ohne title → der Namenszähler MUSS ihn zählen | siehe §3 |
| K-G | Kunst-`div` mit `font-size:9px` → der 12-px-Zähler MUSS um genau 1 steigen | siehe §4 |
| K-H | Formular offen: Datumsfeld UND „speichern" UND „Abbrechen" im DOM, dazu ≥1 Eintragskarte | siehe §4 |

---

## 2. Behauptung 1 — „der Umbau von div auf h2 kostet kein Pixel"

**STIMMT.** Gemessen bei 340, 375, 390 und 1440 px, in der LISTE und im
FORMULAR, jeweils `index.html` (v3.9.959) gegen `11e365a` (v3.9.955).

### Die Feinmessung am Titel

| Breite | Ort | alt (v955) | neu (v959) | Δ |
|---|---|---|---|---|
| 340 | Liste | `DIV` 20px h=30 y=227 m=0px/0px | `H2` 20px h=30 y=227 m=0px/0px | 0 |
| 340 | Formular | `DIV` 18px h=27 y=235.5 m=0/0 | `H2` 18px h=27 y=235.5 m=0/0 | 0 |
| 375 | Liste | `DIV` 20px h=30 y=210 | `H2` 20px h=30 y=210 | 0 |
| 375 | Formular | `DIV` 18px h=27 y=218.5 | `H2` 18px h=27 y=218.5 | 0 |
| 390 | Liste | `DIV` 20px h=30 y=210 | `H2` 20px h=30 y=210 | 0 |
| 390 | Formular | `DIV` 18px h=27 y=218.5 | `H2` 18px h=27 y=218.5 | 0 |
| 1440 | Liste | `DIV` 20px h=30 y=266.5 | `H2` 20px h=30 y=266.5 | 0 |
| 1440 | Formular | `DIV` 18px h=27 y=265 | `H2` 18px h=27 y=265 | 0 |

Das Element **darunter** (Liste: der Knopf „📷 Kasten-QR scannen & öffnen";
Formular: der erste `_sec`-Block) steht in beiden Ständen auf derselben Höhe:
Liste 340→y=323, 375/390→y=306, 1440→y=312; Formular 340→y=285,
375/390→y=268, 1440→y=308. **dy = +0 in allen acht Fällen.**

### Die ganze Ansicht, nicht nur der Titel

| Breite | Ort | gemeinsame Stellen | max \|Δ\| x / y / w / h | Stellen > 1 px |
|---|---|---|---|---|
| 340 | Liste | 7 | 0.0 / 0 / 0.0 / 0 | **0** |
| 340 | Formular | 68 | 0 / 0.0 / 0 / 0.0 | **0** |
| 375 | Liste | 7 | 0.0 / 0 / 0.0 / 0 | **0** |
| 375 | Formular | 68 | 0 / 0.0 / 0 / 0.0 | **0** |
| 390 | Liste | 7 | 0.0 / 0 / 0.0 / 0 | **0** |
| 390 | Formular | 68 | 0 / 0.0 / 0 / 0.0 | **0** |
| 1440 | Liste | 7 | 0.0 / 0 / 0.0 / 0 | **0** |
| 1440 | Formular | 68 | 0 / 0.0 / 0 / 0.0 | **0** |

Keine Stelle nur in einem Stand, kein Größenunterschied. Der **einzige**
Unterschied, den das Raster findet, ist in beiden Orten genau einer und genau
der gewollte:

```
Tagwechsel: [{'schluessel': '🚧 Bauprovisorien#0',   'neu': 'H2', 'alt': 'DIV'}]
Tagwechsel: [{'schluessel': 'Neues Bauprovisorium#0','neu': 'H2', 'alt': 'DIV'}]
```

### Der interessante Fall: 340 px und die `!important`-Regel

`index.html:441` in `@media (max-width: 340px)`:
`.header-row h2 { font-size: 16px !important; }`

Eine Messung, die bei 340 px nur „20px, alles gut" meldet, wäre auch dann grün,
wenn sie die Regel prinzipiell nicht sehen könnte. Köder **K-E** hängt dem
Kopfbehälter darum vorübergehend die Klasse `header-row` an (nur im lebenden
DOM, die Datei bleibt unberührt) und liest die berechnete Schriftgröße vorher /
mit / wieder-ohne:

```
340 px, Liste,    v3.9.959: tag=H2  20px -> 16px -> 20px   Höhe 30 -> 24
340 px, Formular, v3.9.959: tag=H2  18px -> 16px -> 18px   Höhe 27 -> 24
                  medienregel_greift = True (matchMedia('(max-width:340px)'))
```

Die Regel ist bei 340 px **wirksam** und die Messung **sieht** sie — sie greift
nur am echten Baum nicht, weil dieser Kopf kein `header-row` trägt. Damit ist
„die Regel greift hier nicht" gemessen und nicht bloß behauptet.

Gegenprobe in die andere Richtung, im Altstand:

```
340 px, Liste,    v3.9.955: tag=DIV 20px -> 20px -> 20px   Höhe 30 -> 30
340 px, Formular, v3.9.955: tag=DIV 18px -> 18px -> 18px   Höhe 27 -> 27
```

Am `div` schlägt K-E **nicht** an — richtig, denn `.header-row h2` kann auf ein
`div` nicht passen. Die Sonde meldet diesen Lauf als „NICHT gemessen"; das ist
für den Altstand der **erwartete** Ausgang und kein Mangel. Beide Richtungen
zusammen belegen: der Zähler zählt, was er behauptet.

### Einschränkung dieses Falls

Die **Liste** ist ohne Server leer: nur 7 Rasterzeilen (Kopfzeile, `h2`, die
zwei Kopfknöpfe, der QR-Knopf, der Leertext). Die Kartenliste der Bauprovisorien
ist in diesem Aufbau eine **leere Grundgesamtheit** und nicht gemessen. Der
Titel, die Kopfzeile und das Element darunter sind davon unabhängig, das
Formular mit 68 Stellen ebenfalls.

---

## 3. Behauptung 2 — „title und aria-label kosten kein Pixel"

**STIMMT.** Gemessen bei 390 und 1440 px in **Fahrzeugverwaltung**
(Hauptreiter „Fahrzeuge") und in **Projektakte/Fotos**, `index.html` gegen
`a4b50e5` (v3.9.956).

### Die Umschalter ☰ / ⊞ und ihre Leiste

| Breite | Ansicht | Knopf | alt (v956) | neu (v959) | Δw / Δh | title alt → neu |
|---|---|---|---|---|---|---|
| 390 | Fahrzeuge | ☰ | 44 × 44 | 44 × 44 | +0 / +0 | `None` → `Listenansicht` |
| 390 | Fahrzeuge | ⊞ | 44 × 44 | 44 × 44 | +0 / +0 | `None` → `Kachelansicht` |
| 390 | Fahrzeuge | **Leiste** | 90 × 46 | 90 × 46 | +0 / +0 | — |
| 390 | Fotos | ☰ | 44 × 44 | 44 × 44 | +0 / +0 | `None` → `Listenansicht` |
| 390 | Fotos | ⊞ | 44 × 44 | 44 × 44 | +0 / +0 | `None` → `Kachelansicht` |
| 390 | Fotos | **Leiste** | 90 × 46 | 90 × 46 | +0 / +0 | — |
| 1440 | Fahrzeuge | ☰ | 32.58 × 42 | 32.58 × 42 | +0 / +0 | `None` → `Listenansicht` |
| 1440 | Fahrzeuge | ⊞ | 34.67 × 42 | 34.67 × 42 | +0 / +0 | `None` → `Kachelansicht` |
| 1440 | Fahrzeuge | **Leiste** | 69.25 × 44 | 69.25 × 44 | +0 / +0 | — |
| 1440 | Fotos | ☰ | 33.58 × 29 | 33.58 × 29 | +0 / +0 | `None` → `Listenansicht` |
| 1440 | Fotos | ⊞ | 33.67 × 29 | 33.67 × 29 | +0 / +0 | `None` → `Kachelansicht` |
| 1440 | Fotos | **Leiste** | 69.25 × 31 | 69.25 × 31 | +0 / +0 | — |

`aria-label` trägt in allen vier Fällen denselben Wortlaut wie `title`.

Dazu das Raster der ganzen Ansicht:

| Breite | Ansicht | gemeinsame Stellen | max \|Δ\| x / y / w / h | Stellen > 1 px |
|---|---|---|---|---|
| 390 | Fahrzeuge | 50 | 0.0 / 0 / 0.0 / 0 | **0** |
| 390 | Fotos | 24 | 0.0 / 0.0 / 0.0 / 0 | **0** |
| 1440 | Fahrzeuge | 50 | 0.0 / 0 / 0.0 / 0 | **0** |
| 1440 | Fotos | 24 | 0.0 / 0.0 / 0.0 / 0 | **0** |

Kein Tagwechsel, keine Stelle nur in einem Stand.

### Hat jetzt jeder dieser Knöpfe einen zugänglichen Namen?

Abgelesen am gerenderten Element (`aria-label`, sonst `title`, sonst Text mit
Buchstaben), nicht am Quelltext:

| Breite | Ansicht | Knöpfe gerendert | ohne Namen alt (v956) | ohne Namen neu (v959) |
|---|---|---|---|---|
| 390 | Fahrzeuge | 10 | **2** (`☰`, `⊞`) | **0** |
| 390 | Fotos | 3 | **2** (`⊞`, `☰`) | **0** |
| 1440 | Fahrzeuge | 10 | **2** (`☰`, `⊞`) | **0** |
| 1440 | Fotos | 3 | **2** (`⊞`, `☰`) | **0** |

**Köder K-F:** eine 0 ist ohne Selbstprobe wertlos — ein ausgefallener Zähler
meldet ebenfalls 0. Vor jeder Zählung wurde ein Kunstknopf mit ausschließlich
`⊗` und ohne `title`/`aria-label` eingehängt; der Zähler fand ihn in **allen
vier** Läufen des neuen Standes (`namenlos 0 → 1`), danach wurde er entfernt.
Der Zähler war also nicht blind, als er 0 meldete.

### Einschränkung dieses Falls

* **Fotos** ist ohne Server bildleer: nur 3 Knöpfe gerendert (die zwei
  Umschalter und einer weiterer). Die Kategorie-Chips (`_visibleCats`) und die
  Foto-Kacheln sind eine **leere Grundgesamtheit** und nicht gemessen. Die
  Leiste selbst trägt `marginLeft:auto` — ihre **x-Position** hängt an den
  fehlenden Chips, ihre **Größe** nicht. Für den Vergleich ist das
  unschädlich, weil beide Stände gleich leer sind; als Aussage über die
  bestückte Fotoansicht taugt die x-Position nicht.
* Gemessen sind die Knöpfe **dieser zwei Ansichten**, nicht alle 33 + 32 aus
  S-1. Der Umfang ist in §5 erweitert.

---

## 4. Behauptung 3 — „die Verhaltensänderung im Bautagebuch ist noch da"

**STIMMT.** Gemessen bei 390, 640, 767 und 1440 px in `Projektakte/Bautagebuch`,
`index.html` (v3.9.959) gegen `a34d535` (v3.9.954, dort `const isMob=ww<768`).

### Zuerst: die Falle, die die frühere Messung wertlos gemacht hat

Alle `isMob`-Stellen in `VBautag` liegen im **Bearbeitungsformular** oder in einer
**Eintragskarte**. Beide Zustände brauchen Daten bzw. einen Klick; bei leerem
Server und geschlossenem Formular kann sich nichts unterscheiden. Köder **K-H**
verlangt darum **beides** und belegt es je Lauf:

```
Eintragskarten:      {'erstellt_von': 3, 'zeilen': 3}          ← 3 Karten im DOM
K-H Formular offen:  1 Datumsfelder,
                     Speichern=['💾 Eintrag speichern'],
                     Abbrechen=['Abbrechen'],
                     Ueberschriften=['📋 Neuer Tagesbericht']
```

Die drei Einträge liegen als Saat im IndexedDB-Store `projektCache` unter dem
Schlüssel `bt_P1` — das ist die Stelle, aus der `VBautag` ohne Server liest
(`ODB.loadProj("bt_"+p.id)`). Ohne diese zweite Saat wäre die Ansicht leer
gewesen, und die Kartenzahlen wären eine leere Grundgesamtheit.

🔴 **Beim ersten Lauf hat K-H genau zugeschlagen und mich vor der Falschmeldung
bewahrt:** die Sonde suchte `/Speichern/` und der Knopf heißt
`💾 Eintrag speichern` — klein geschrieben. Vier Läufe wurden als „NICHT
gemessen" abgebrochen, obwohl das Formular offen war. Erst mit `/[Ss]peichern/`
lief es durch. Hätte K-H nur nach dem Datumsfeld gefragt, wäre die Messung
„grün" gewesen, ohne dass die Prüfung vollständig war.

`VBautag` rendert bei offenem Formular **nur** das Formular (`if(editing!==null)
return …`). Die Kartenstellen und die Formularstellen sind deshalb in
**getrennten** Aufnahmen gemessen: `liste_*` im Listenzustand mit drei Karten,
`form_*` nach dem Klick auf „➕ Neuer Eintrag".

### Die gemessenen isMob-Stellen

| Breite | Stelle | v3.9.954 (alt) | v3.9.959 (neu) | Fassung neu |
|---|---|---|---|---|
| **390** | Formularraster 3-spaltig | `374px` | `374px` | mobil (gleich) |
| **390** | Speichern/Abbrechen | `column` [374, 374] | `column` [374, 374] | mobil (gleich) |
| **390** | Chips-Innenabstand | `4px 8px` | `4px 8px` | mobil (gleich) |
| **390** | Kartenkopf | `column` / `flex-start` | `column` / `flex-start` | mobil (gleich) |
| **640** | Formularraster 3-spaltig | `544px` (1 Spalte) | `173.328px 173.328px 173.328px` | **DESKTOP** |
| **640** | Speichern/Abbrechen | `column` [544, 544] | `row` [161.83, 104.08] | **DESKTOP** |
| **640** | Chips-Innenabstand | `4px 8px` | `5px 10px` | **DESKTOP** |
| **640** | Kartenkopf | `column` / `flex-start` | `row` / `center` | **DESKTOP** |
| **767** | Formularraster 3-spaltig | `671px` (1 Spalte) | `215.656px 215.672px 215.672px` | **DESKTOP** |
| **767** | Speichern/Abbrechen | `column` [671, 671] | `row` [161.83, 104.08] | **DESKTOP** |
| **767** | Chips-Innenabstand | `4px 8px` | `5px 10px` | **DESKTOP** |
| **767** | Kartenkopf | `column` / `flex-start` | `row` / `center` | **DESKTOP** |
| **1440** | alle vier | Desktop | Desktop | Desktop (gleich) |

Bei 640 px erscheint die Desktop-Fassung. **Die Behauptung gilt an v3.9.959
weiterhin.**

### Die Textstellen unter 12 px — 33 auf 15 reproduziert

Gezählt mit `SCHRIFT_JS` aus `b3_vier_ansichten_messen` im **Formularzustand**:

| Breite | v3.9.954 | v3.9.959 |
|---|---|---|
| 390 | 13 von 83 | 13 von 83 |
| **640** | **33 von 87** | **15 von 87** |
| **767** | **33 von 87** | **15 von 87** |
| 1440 | 15 von 101 | 15 von 101 |

Das ist genau die frühere Messung („bei 640/767 px fallen die Textstellen unter
12 px von 33 auf 15"), auf die Stelle bestätigt.

Im **Listenzustand** ändert sich die Zahl nicht (23 von 84 in beiden Ständen bei
640 px) — die `isMob`-Stellen der Karte bewegen Richtung, Abstand und Beschriftung,
aber keine Schriftgröße unter 12 px. Das ist keine Abweichung, sondern eine
Präzisierung: die 33→15 gehören dem **Formular**.

**Köder K-G:** vor jeder Zählung wurde ein Kunst-`div` mit `font-size:9px`
eingehängt; die Zahl stieg in **allen acht** Läufen um genau 1 (13→14, 33→34,
15→16), danach wurde es entfernt. Der Zähler war nicht blind.

### Das ganze Raster, als Gegenprobe zur Größe der Änderung

| Breite | Ort | gemeinsame Stellen | Stellen > 1 px | nur in einem Stand |
|---|---|---|---|---|
| 390 | Liste | 50 | **0** | 0 / 0 |
| 390 | Formular | 54 | **0** | 0 / 0 |
| **640** | Liste | 38 | **49** | 12 / 12 |
| **640** | Formular | 54 | **100** | 0 / 0 |
| **767** | Liste | 38 | **49** | 12 / 12 |
| **767** | Formular | 54 | **100** | 0 / 0 |
| 1440 | Liste | 50 | **0** | 0 / 0 |
| 1440 | Formular | 54 | **0** | 0 / 0 |

Die zwölf Stellen, die es nur in einem Stand gibt, sind der Beschriftungswechsel
der Kartenknöpfe — ein Text-Beleg des Zweigwechsels, der keine Koordinate braucht:

```
nur alt (v954, 640 px):  ✏️ Bearbeiten#0..2   🗑️ Löschen#0..2
nur neu (v959, 640 px):  ✏️#0..2              🗑️#0..2
```

Größte Einzelverschiebungen im Formular bei 640 px: `Abbrechen` von
544 px auf 104.08 px Breite und von x=76 auf x=245.83; `Beleuchtung`-Chip von
x=532 auf x=76. Bei 390 und 1440 px ist der Baum **bitgleich positioniert** —
die Änderung wirkt genau im Fenster 600–767 px und nirgends sonst.

### 🟡 Nebenbefund: ein Knopf verliert im Fenster 600–767 px seinen Namen

Der Zweigwechsel hat eine Nebenwirkung, die S-1 nicht erfasst hat. In der
Eintragskarte lautet der Löschknopf `"🗑️ " + (isMob ? "Löschen" : "")`
(`index.html:19889`) und trägt **weder `title` noch `aria-label`** — anders als
der Bearbeiten-Knopf daneben (`title: "Bearbeiten"`, `index.html:19888`).

Solange `isMob` bei 640 px wahr war (v3.9.954), hieß der Knopf „🗑️ Löschen" und
hatte damit einen Namen. Seit v3.9.955 ist er dort „🗑️" — ein Knopf, dessen
ganzer Inhalt ein Symbol ist. Am gerenderten Baum gemessen, nicht am Quelltext:

```
Bautagebuch-Liste, 3 Eintragskarten, 9 Knöpfe
   640 px  v3.9.954: 0 ohne Namen      v3.9.959: 3 ohne Namen  ['🗑️','🗑️','🗑️']
  1440 px  v3.9.954: 3 ohne Namen      v3.9.959: 3 ohne Namen  ['🗑️','🗑️','🗑️']
```

Bei 1440 px ist der Mangel **nicht neu** — er stand in v3.9.954 genauso da und
hat S-1 überlebt. Neu ist allein, dass er sich seit v3.9.955 auch auf das
Fenster **600–767 px** erstreckt. Weitere Zahlen in §5.

Das ist **kein Widerspruch** zu Behauptung 3 — die Behauptung sagt „die
Verhaltensänderung ist noch da", und sie ist da. Es ist eine Folge davon, die
niemand gemessen hatte.

---

## 5. Umfangserweiterung zu Behauptung 2: namenlose Knöpfe über elf Ansichten

Behauptung 2 fragt auch: „hat jetzt jeder dieser Knöpfe im DOM einen
zugänglichen Namen?" Zwei Leisten sind dafür ein schmaler Umfang. Derselbe
Zähler wurde deshalb über elf Hauptansichten bei 1440 px geführt, jeweils mit
K-F davor:

| Ansicht | Knöpfe gerendert | ohne Namen v3.9.956 | ohne Namen v3.9.959 | K-F |
|---|---|---|---|---|
| Projekte | 9 | 0 | 0 | ok |
| Arbeitsscheine | 56 | 0 | 0 | ok |
| Zeiterfassung | 29 | 0 | 0 | ok |
| Abwesenheiten | 25 | 0 | 0 | ok |
| Fahrzeuge | 10 | **2** (`☰`,`⊞`) | **0** | ok |
| Werkzeuge | 23 | 0 | 0 | ok |
| Mitarbeiter | 5 | 0 | 0 | ok |
| Auswertungen | 101 | 0 | 0 | ok |
| Einstellungen | 12 | 0 | 0 | ok |
| Gefahrenstoffe | 2 | 0 | 0 | ok |
| Bauprovisorien | 3 | 0 | 0 | ok |
| **Summe** | **275** | **2** | **0** | 11/11 |

In allen elf Ansichten hat der Kunstknopf-Köder angeschlagen — die Nullen sind
Messwerte und nicht das Schweigen eines ausgefallenen Zählers.

Dazu die Bautagebuch-Liste (Projektakte, nicht Hauptreiter), mit drei
Eintragskarten im DOM — hier in **beiden** Ständen, weil das der Nebenbefund aus
§4 ist:

| Breite | Knöpfe gerendert | ohne Namen v3.9.954 | ohne Namen v3.9.959 | K-F |
|---|---|---|---|---|
| 390 | 9 | — (nicht gemessen) | **0** | ok |
| **640** | 9 | **0** | **3** (`🗑️`, dreimal) | ok |
| 1440 | 9 | **3** (`🗑️`, dreimal) | **3** (`🗑️`, dreimal) | ok |

Damit ist der Nebenbefund eingegrenzt: die drei namenlosen `🗑️` bei **1440 px
sind nicht neu** — sie stehen in v3.9.954 genauso da. Neu ist allein das
**Fenster 600–767 px**: dort hatte der Knopf vorher die Beschriftung „Löschen"
und damit einen Namen, seit v3.9.955 nicht mehr.

Die Zahl wächst mit der Anzahl der Einträge: es ist **ein** Knopf je
Eintragskarte, drei Karten in der Saat.

🔴 Das heißt auch: der Löschknopf der Bautagebuch-Karte war bei Desktopbreiten
**schon vor S-1 namenlos und ist es nach S-1 noch**. Der Sweep in der Tabelle
oben hätte ihn nie gefunden — er sitzt in einer Projektakte-Unterseite, nicht in
einem Hauptreiter. Ein Beispiel dafür, wie schmal der Umfang von elf
Hauptansichten ist.

**Diese Zahlen sind eine Aussage über 275 + 3·n Knöpfe in zwölf Ansichts­zuständen
bei einer Breite — nicht über die 33 + 32 Knöpfe aus S-1.** Der größte Teil
jener 65 liegt in Zuständen hinter einem Klick (Modale, Unterreiter,
Projektakte-Unterseiten, Formulare), und die sind hier nicht angefahren. Dass
v3.9.956 in zehn von elf Ansichten schon 0 namenlose Knöpfe hatte, heißt
deshalb **nicht**, dass S-1 wenig zu tun hatte — es heißt, dass dieser Aufbau
den Ort der 33 nicht sieht.

---

## 6. Was ich NICHT gemessen habe

**Zum Aufbau**

* **Echte Serverdaten.** `**/rest/v1/**` und `**/auth/v1/**` werden abgebrochen;
  gesät wird in die IndexedDB. Jede Zeile, die nur vom Server kommt, fehlt.
* **Rollen.** Gefahren wurde ausschließlich `role=admin`, `monteurId=M1`,
  `rolle=Geschäftsführer`. Ein Monteur, ein Büro oder ein Projektleiter sieht
  andere Knöpfe und andere Reiter; für die ist keine dieser Zahlen gültig.
* **Nur Dunkelmodus.** Alle Läufe mit `epk_theme=dark` und
  `color_scheme=dark`. Ein Hellmodus-Lauf würde andere Farben, aber dieselbe
  Geometrie liefern — gemessen ist er nicht.
* **Ein Browser.** Chromium via Playwright, headless. Kein WebKit, kein Firefox,
  kein echtes Gerät. Die `h2`-Frage ist eine Frage an die UA-Vorgaben des
  Browsers; eine andere Engine könnte andere Vorgabeabstände mitbringen (hier
  sind sie durch `* { margin: 0 }` in `index.html:78` **und** das inline
  `margin:0` doppelt abgeräumt, aber gemessen ist nur Chromium).

**Leere Grundgesamtheiten — ausdrücklich keine Nullen**

* Die **Kartenliste der Bauprovisorien** (Behauptung 1) ist ohne Server leer:
  7 Rasterzeilen, davon eine der Leertext. Über die bestückte Liste sagt dieser
  Bericht nichts.
* Die **Fotoansicht** (Behauptung 2) ist bildleer: 3 Knöpfe, keine
  Kategorie-Chips (`_visibleCats` ist leer), keine Kacheln. Die **x-Position**
  der Umschalter-Leiste hängt an den fehlenden Chips (`marginLeft:auto`); ihre
  Größe nicht. Als Aussage über die bestückte Fotoansicht taugt die Position
  nicht.
* **Fahrzeuge** wurde mit der Saat aus `b3_stufen_12_15` bestückt; die Liste ist
  nicht leer, aber sie ist auch nicht der Produktionsbestand.

**Zu den Behauptungen selbst**

* **Behauptung 1:** gemessen sind die zwei Titel in `BauprovisorienView`. Die
  übrigen `div`→`h2`-Umbauten aus v3.9.956 (D9 hat mehrere Ansichten
  angefasst) sind **nicht** gemessen. „Kein Pixel" gilt hier für diese zwei
  Stellen an diesen vier Breiten.
* **Behauptung 1, die 340er-Regel:** geprüft ist, dass `.header-row h2` bei
  340 px wirkt und dass dieser Kopf sie nicht bekommt. **Nicht** geprüft ist, ob
  irgendein anderer der D9-`h2` unter einem `header-row` sitzt.
* **Behauptung 2:** gemessen sind die **zwei** Umschalterpaare, die der Auftrag
  nennt, bei zwei Breiten. Von den 33 + 32 Knöpfen aus S-1 ist der größte Teil
  nicht angefahren (§5). Auch nicht gemessen: ob der **Tooltip selbst** irgendwo
  etwas verdeckt — er entsteht erst beim Verweilen, liegt in der
  Browser-Oberfläche und nicht im Baum, und eine Playwright-Messung sieht ihn
  gar nicht.
* **Behauptung 2, Qualität der Namen:** gezählt ist, **ob** ein Name da ist,
  nicht ob er **gut** ist. „Kachelansicht"/„Listenansicht" sind aus dem
  `onClick` abgelesene Namen; ob eine Vorlesehilfe damit die
  Umschalter-Beziehung („gedrückt"/„nicht gedrückt", `aria-pressed`) vermittelt,
  ist eine andere Frage und hier **nicht** gestellt. Ein Knopf mit Namen ist
  nicht automatisch ein bedienbarer Umschalter.
* **Behauptung 3:** gemessen sind der Listenzustand mit drei Karten und der
  Zustand „neuer Eintrag". Der Zustand „Eintrag **bearbeiten**"
  (`editing===<id>`, Titel „✏️ Tagesbericht bearbeiten") ist **nicht**
  angefahren; er teilt denselben Formularbaum, ist aber nicht gemessen.
  Ebenfalls nicht: die PDF-/Excel-Ausgabe, der Wetter-Abruf (`autoFillWeather`
  läuft gegen eine externe Adresse und wurde nicht abgeschaltet — ob er in
  diesen Läufen geantwortet hat, ist nicht protokolliert) und die Breiten
  599/600/601, also die Schwelle selbst.
* **Der Nebenbefund in §4/§5** ist am Zustand „Liste mit drei Karten" gemessen.
  Ob dieselbe Stelle in anderen Karten-Listen der App denselben Mangel hat, ist
  nicht gemessen.

**Was nicht in diesen Bericht gehört**

Die Sonde hat `index.html` nicht angefasst; alle Köder (K-E, K-F, K-G) wirken im
lebenden DOM und werden im selben Aufruf wieder entfernt, was jeweils
mitprotokolliert ist (`zurueck: True`, `entfernt: {'weg': True}`).

---

## 7. Zusammenfassung

| # | Behauptung | Urteil |
|---|---|---|
| 1 | v3.9.956 D9: „der Umbau von div auf h2 kostet kein Pixel" | **STIMMT** — 0 Abweichungen > 1 px an 7 + 68 Stellen je Breite, bei 340/375/390/1440 px; max \|Δ\| = 0.0 in x/y/w/h; der einzige Unterschied ist der gewollte Tagwechsel |
| 2 | v3.9.957/958 S-1: „title und aria-label kosten kein Pixel" | **STIMMT** — Umschalter und Leiste bei 390 und 1440 px auf 0.00 px gleich, 0 Abweichungen an 50 + 24 Stellen; namenlose Knöpfe 2 → 0 in beiden Ansichten |
| 3 | v3.9.955: die Verhaltensänderung im Bautagebuch ist noch da | **STIMMT** — bei 640 und 767 px erscheint die Desktop-Fassung (3-spaltiges Raster, `row`-Knopfzeile, `5px 10px`-Chips, `row/center`-Kartenkopf); Schrift unter 12 px 33 → 15, auf die Stelle wie früher gemessen; bei 390 und 1440 px kein Unterschied |

Dazu ein Nebenbefund (🟡, §4/§5) und eine Berichtigung am Auftrag (§0).

---

## 8. Wie die Läufe wiederholt werden

```
cd C:\repos\epkolar-app

:: Vergleichsstaende herstellen (git-ignoriert, CRLF wie das Original)
git cat-file -p 11e365a:index.html | sed 's/$/\r/' > _mess_pn_v955_11e365a.html
git cat-file -p a4b50e5:index.html | sed 's/$/\r/' > _mess_pn_v956_a4b50e5.html
git cat-file -p a34d535:index.html | sed 's/$/\r/' > _mess_pn_v954_a34d535.html

:: Behauptung 1
python scripts/pixelneutralitaet_959_messen.py --fall 1 --json f1_neu.json
set EPK_INDEX=_mess_pn_v955_11e365a.html
python scripts/pixelneutralitaet_959_messen.py --fall 1 --json f1_alt.json
python scripts/pixelneutralitaet_959_messen.py --vergleich f1_neu.json f1_alt.json

:: Behauptung 2 (--fall 2) gegen _mess_pn_v956_a4b50e5.html
:: Behauptung 3 (--fall 3) gegen _mess_pn_v954_a34d535.html
:: Umfang     (--fall 4) gegen _mess_pn_v956_a4b50e5.html
```

Rückgabewert der Sonde: `0` nur dann, wenn **alle** Köder des Laufs angeschlagen
haben; `1`, sobald einer stumm bleibt — und dann steht unter „NICHT GEMESSEN",
welcher. Die Ausgabe wird in eine Datei geschrieben und **aus der Datei**
geurteilt, nicht aus einem gepipten Rückgabewert.

Dass der K-E-Köder im **Altstand** von Behauptung 1 stumm bleibt, ist der
erwartete Ausgang (dort ist der Titel ein `div`, und `.header-row h2` kann auf
ein `div` nicht passen) — dieser eine Lauf endet deshalb planmäßig mit `1`.

Prozesse: die Sonde schließt Browser und Kontext selbst. Nach den Läufen dieses
Berichts liefen vier `chrome-headless-shell.exe` — sie gehören über
`node.exe`/`workerProcessEntry.js` zu einem **fremden** Playwright-Lauf aus
`C:\dev\mlg-hafen-0922` und wurden **nicht** abgeräumt. Alter oder Name eines
Prozesses macht ihn nicht zur Waise.
