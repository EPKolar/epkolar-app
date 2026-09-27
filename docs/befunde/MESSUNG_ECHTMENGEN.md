# Die Oberfläche an ECHTMENGEN gemessen — 22 Ansichten × 390 und 1440 px

**Auftrag dieses Laufs: messen. Gebaut wurde nichts.** `index.html` ist nicht
angefasst — kein Edit, kein Write, kein `sed`. Kein Fix. Keine bestehende
Prüfung unter `tests/` geändert. Kein `git add/commit/push/checkout/stash/
reset`. Keine DB-Schreibzugriffe, kein DDL, `.github/workflows/` nicht berührt.

---

## 🔴 Stufe 0a ist offen.

Der git-add-Riegel feuert seit über zwanzig Commits nicht (der
Einstellungswächter beobachtet `.claude/` erst, wenn dort beim Sitzungsstart
schon eine Datei lag). **Sebastian muss einmal `/hooks` öffnen.** Solange das
offen ist, liegen mehrere MB große Messkopien im Baum und ein versehentliches
`git add -A` nähme sie mit.

Dieser Lauf hat **keine** `_mess_*.html`-Kopie angelegt (gemessen wurde direkt
an `index.html` über einen lokalen HTTP-Server, und die Datei ist vorher wie
nachher bytegleich). Er hat aber **drei Rohdatendateien** unter `scripts/`
hinterlassen, und **zwei davon sind nicht git-ignoriert** — siehe §10.

---

## 1. Messgrundlage

| Was | Wert |
|---|---|
| `HEAD` | `8d53ad7` — „Doku: v3.9.962 nachgezogen" |
| `index.html` **vor** dem Lauf | 3 712 738 Bytes, md5 **`e5f245b76f1f23d5e9864c5d1344eda0`** |
| `index.html` **nach** dem Lauf | 3 712 738 Bytes, md5 **`e5f245b76f1f23d5e9864c5d1344eda0`** |
| `git diff --numstat index.html` | **leer**, vor und nach jedem Lauf |
| `APP_VERSION` im Bild | `3.9.962` (aus der Kopfzeile der Ansicht abgelesen, nicht aus dem Repo) |
| Rolle im Messaufbau | `admin`, `rolle=Geschäftsführer`, `monteurId=M1` |
| Netz | REST **und** Auth abgeklemmt (`ctx.route(...).abort()`) — die Amber-Bänder „18 Änderungen warten auf Sync" / „Server nicht erreichbar" sind Aufbau-Artefakt und **kein Befund** |
| Breiten | **390×880** (`is_mobile`, `has_touch` → `pointer: coarse`) und **1440×880** (`pointer: fine`) |
| Thema | dunkel |
| Läufe | **2 × 44 Aufnahmen** (22 Ansichten × 2 Breiten), 843 s bzw. 837 s |

Angelegte Skripte:

| Datei | Zweck |
|---|---|
| `scripts/echtmengen_saat.py` | die Saat in Echtmengen **plus** `mindestmenge_pruefen()` mit eigener Selbstprobe (`python scripts/echtmengen_saat.py`) |
| `scripts/echtmengen_messen.py` | der Lauf über alle 22 Ansichten, beide Tore, alle Köder |
| `scripts/echtmengen_tabellen.py` | erzeugt die Tabellen dieses Berichts aus den Rohdaten |
| `scripts/echtmengen_planung_probe.py` | eine einzige Frage: was zeigt die Wochenplanung überhaupt (§7.3) |

**Nichts davon ist neu erfunden.** Die Melder sind die vorhandenen:
`B.SCHRIFT_JS`, `B.TIPP_JS`, `B.QUER_JS`, `B.EMOJI_JS`, `B.KOEDER_*` aus
`b3_vier_ansichten_messen.py`, der Saat-Rückleser `S.SEED2_JS` aus
`b3_stufen_8_11_messen.py`, die Navigatoren `_navigieren` / `_navigieren8` /
`_navigieren12` aus allen drei Sondengruppen, die Gruppentabelle aus
`grundstand_erheben.py`. Neu gebaut ist genau **ein** Melder (`PIKTO_JS`,
Emoji *im* Knopftext) — weil `EMOJI_JS` per Vorschrift eine andere
Grundgesamtheit misst (siehe §4.4).

---

## 2. Die Saat

### 2.1 Mengen

| Speicher | alte Saat (v3.9.954-Stand) | **neue Saat** | Mindestmenge | Sebastians Bestand |
|---|---|---|---|---|
| Mitarbeiter gesamt | 5 | **11** | 11 | — |
| davon aktiv | 3 | **9** | 9 | 9 |
| davon ausgetreten | 2 | **2** | 2 | — |
| Fahrzeuge | 3 | **21** | 21 | 21 |
| Werkzeuge | 6 | **300** | 290 | 296 |
| Arbeitsscheine | 8 | **185** | 180 | 185 |
| Projekte | 2 | **3** | 3 | 3 |

Zurückgelesen wurde jeweils aus der IndexedDB **nach** dem Neuladen, nicht das,
was hineingeschrieben werden sollte. Tor A hat in **allen 44** Aufnahmen der
neuen Saat **keine** Verletzung gemeldet — die Saat kommt überall an.

### 2.2 Die Namen — erfunden, mit Absicht gebaut

🔴 **Keine echten Personendaten.** Fünf Namen sind unverändert aus
`b3_stufen_12_15_messen.MONTEURE` übernommen (sie tragen den Köder K14:
ausgetreten *mit* Beitrag = M4, ausgetreten *ohne* Beitrag = M5), sechs sind neu:

| Forderung | eingelöst mit |
|---|---|
| **zwei Nachnamen mit gleichem Anfang** | `Steinbichler` / `Stein**berger**` → beide `Steinb` · `Hinterleitner` / `Hinter**huber**` → beide `Hinter` |
| **zwei ungewöhnlich lange** | `Pfeiffenberger-Dollinger` (24) · `Brandstetter-Hollenstein` (24), dazu der vorhandene `Wieshofer-Prandtner` (19) |

Die Kürzungspaare sind **nicht Zierde**: sie sind das Messmittel für §7.3. Hätte
eine Ansicht die Namen auf sechs Zeichen gekürzt, wäre mein Tor-B-Melder für
genau diese Ansicht blind gewesen — die Probe darauf steht dort.

### 2.3 🔴 Eine Abweichung vom Auftrag, gemessen statt angenommen

Der Auftrag nannte „**rund 185 Arbeitsscheine über alle elf Status verteilt**".
**`AS_STATUS` in `index.html` führt ACHT Scheinstatus, nicht elf:**

    aufgenommen · freigegeben · in_bearbeitung · aufgeschoben     (Gruppe offen)
    erledigt · abgerechnet · bar_bezahlt                          (Gruppe fertig)
    storniert                                                     (Gruppe storniert)

Geschnitten aus der Datei, nicht abgetippt. Verteilt wurde über alle acht.
`WZ_STATUS` führt sechs (`verfuegbar`, `ausgegeben`, `reparatur`,
`kalibrierung`, `verloren`, `stillgelegt`), `FZ_STATUS_LABEL` sechs
(`faehrt`, `steht`, `aktiv`, `inaktiv`, `wartet`, `kein_tracker`) — **keine
dieser Listen hat elf Einträge.** Woher die Elf stammt, ist **nicht gemessen**.

---

## 3. Die zwei Tore: eine zu dünne Grundgesamtheit besteht keine Probe

Beide Tore können eine Aufnahme als **NICHT AUSSAGEKRÄFTIG** stempeln. Sie
können sie **niemals** als bestanden stempeln.

| Tor | prüft | Quelle |
|---|---|---|
| **A** (je Lauf) | die aus der DB **zurückgelesenen** Mengen gegen `MINDEST` | `echtmengen_saat.mindestmenge_pruefen` |
| **B** (je Aufnahme) | mindestens **3 verschiedene** Saatmarken im Text *dieser* Ansicht | `echtmengen_saat.marken_im_text` |

### 3.1 Die Köder der Tore — einer je Form

🔴 **Ein Köder, der die Lücke teilt, bestätigt die Blindheit.** Tor A hat
deshalb **zwei**:

| Köder | was er prüft | Ergebnis |
|---|---|---|
| **leere Saat** | schlägt der Melder überhaupt an? | **7 von 7** Mindestmengen gemeldet |
| **die ALTE, dünne Saat aus v3.9.954** | prüft er auf *genug* Daten oder nur auf *überhaupt* Daten? | **6 von 7** gemeldet: `arbeitsscheine 8/180 · fahrzeuge 3/21 · monteure 5/11 · monteure_aktiv 3/9 · projects 2/3 · werkzeuge 6/290` |
| **Gegenprobe: volle Saat** | darf **nicht** gemeldet werden | **0 Verletzungen** |

Der zweite Köder ist der wichtigere. Ohne ihn hätte Tor A auf „überhaupt
Daten" geprüft und wäre bei drei Monteuren grün gewesen — also genau bei der
Konfiguration, die dieser Auftrag verdächtigt.

**Tor B**, derselbe Aufbau in derselben Ansicht (`fahrzeuge` @ 1440 px):

| | Ergebnis |
|---|---|
| leere Saat | **1** von mindestens 3 Marken → gemeldet. Die eine Marke ist `Steinbichler` — der **angemeldete Benutzer aus dem localStorage**, nicht der Bestand. Genau dafür fordert Tor B *drei verschiedene* Marken und nicht *eine* |
| volle Saat (Gegenprobe) | **7** Marken → nichts gemeldet, richtig |

### 3.2 Was die Tore über die alte Messanordnung sagen

**Der Vergleichslauf mit der alten Saat ist in allen 44 Aufnahmen
„nicht aussagekräftig".** Das ist kein Nebenergebnis, das ist das Ergebnis:
die Messanordnung, mit der v3.9.954 abgenommen wurde, würde heute keine
einzige Aufnahme bestehen.

---

## 4. Die Köder der fünf Messungen

Gefahren in `fahrzeuge @ 1440 px`, vor jedem Lauf (`--koeder`). **16 von 16
angeschlagen, in beiden Läufen.** Am Ende belegt, dass alle Köder restlos
entfernt sind (`pikto=True icon=True rest=[]`).

### 4.1 Elemente unter 12 px
`M1` — ein Textknoten mit `font-size: 9px !important`, gemessen als **9 px**
und gemeldet.

### 4.2 Tippziele unter 44 px
`M2` — ein Knopf **30×20 px**, der die Hausregel
(`@media (pointer:coarse),(max-width:768px) { min-height:44px !important }`)
mit eigenem `!important` übersteuert. Melder fand genau **1**. Ohne das
Übersteuern wäre der Köder selbst 44 px hoch und der Melder fände zu Recht
nichts — eine Selbstprobe, die den eigenen Fall wegmisst.

### 4.3 Horizontaler Überlauf
`M3` — ein 3000 px breites Kind. **`scrollWidth` wächst nicht** (1440 → 3000
nur am Rechteck des Köders); der Inhalt wird abgeschnitten. Genau deshalb wird
über die **Rechtecke** gemessen und nicht über `document.scrollingElement`.

### 4.4 Emoji in Knopftexten — vier Formen, vier Köder, vier Gegenproben

`EMOJI_JS` fängt **nur** Bedienelemente, deren *ganzer* Text zeichenlos ist. Ein
Knopf `🔧 Werkzeug ausgeben` trägt Buchstaben und fällt dort per Vorschrift
heraus. Punkt 4 des Auftrags fragt nach etwas anderem, also braucht er einen
eigenen Melder — und der bekommt **einen Köder je Form**, jeder **mit** einem
Wort daneben (ein Köder, der nur aus dem Zeichen besteht, würde auch von
`EMOJI_JS` gefangen und bewiese nichts):

| Form | Köder | Unicode | warum genau diese |
|---|---|---|---|
| F1 | `🔧 Werkzeug ausgeben` | U+1F527, `So`, astral | der Regelfall |
| F2 | `▲ Sortierung aufsteigend` | U+25B2, `So`, BMP | **genau die Form, an der die erste Fassung des Emoji-Melders blind war** (Geometrische Formen standen in keiner Bereichsliste) |
| F3 | `✏️ Schein bearbeiten` | U+270F U+FE0F | Piktogramm **mit Variantenselektor** |
| F4 | `Weiter → Schritt 2` | U+2192, **`Sm`, nicht `So`** | eine Regel „nur `So`" wäre hier blind |

**Alle vier angeschlagen.** Gegenproben, die **nicht** gemeldet werden dürfen
und es auch nicht wurden:

| Gegenprobe | warum sie kein Befund ist |
|---|---|
| `Summe 1.250,00 € übernehmen` | `€` ist `Sc` (Währung) |
| `Preis + Zuschlag = Endsumme` | ASCII-Symbole |
| `Fläche 12 m² erfassen` | `²` ist `No` (Zahl), kein Symbol |
| `Speichern` | reines Wort |

🔴 **Keine aufgezählte Zeichenliste.** Die Vorschrift lautet: *Unicode-Kategorie
`S`, nicht `Sc`, nicht ASCII.* Was sie **zu viel** meldet und was das kostet:
nicht-ASCII-Mathezeichen wie `×  ±  ≥  ÷`. Ein Knopf `5 × 3` wäre ein Befund.
Diese Unschärfe ist nicht wegmessbar — sie fällt zur **sicheren** Seite, weil
sie zu viel meldet und nicht zu wenig.

### 4.5 Icon-Knöpfe ohne `aria-label` **und** ohne `title`

| Köder | Erwartung | Ergebnis |
|---|---|---|
| Knopf nur `🗑`, ohne beides | **muss** Befund sein | angeschlagen |
| Knopf nur `▼`, ohne beides | **muss** Befund sein (die BMP-Form) | angeschlagen |
| Knopf `⚙` **mit** `title` | darf **nicht** Befund sein, gehört nach `mit_hilfe` | angeschlagen |

### 4.6 Kreuzprobe zwischen 4.4 und 4.5

Messen die beiden Melder dieselbe Menge, ist einer überflüssig. Geprüft: der
reine Icon-Knopf steht **nicht** in `mit_text`, der Knopf mit Wort **nicht** im
Icon-Befund. **Angeschlagen** — sie messen zwei verschiedene Grundgesamtheiten.

---

## 5. Alle 44 Aufnahmen mit der neuen Saat

„Tippziel < 44 px" bei **1440 px ist kein Regelbruch**: die Hausregel gilt
`@media (pointer: coarse), (max-width: 768px)`; bei 1440 px mit feinem Zeiger
greift sie nicht. Die Spalte steht trotzdem da, weil dieselben Elemente auf
einem Touch-Notebook bei 1440 px grobe Zeiger bekommen — ein eigener,
**nicht gemessener** Fall (§8).

| Ansicht | Gruppe | Breite | Urteil | <12 px | Tippziel <44 px | Überlauf verloren | Überlauf rollt | Emoji im Knopftext | Icon ohne Namen | Zeilen | Knöpfe |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Werkzeuge | 4-7 | 390 | gemessen | 15 | 0 | 0 | 1 | 114 | 0 | 0 | 126 |
| Werkzeuge | 4-7 | 1440 | gemessen | 15 | 715 | 0 | 0 | 134 | 0 | 300 | 440 |
| Planung / Wochenplanung | 4-7 | 390 | **nicht aussagekräftig** | 44 | 0 | 0 | 0 | 12 | 0 | 0 | 26 |
| Planung / Wochenplanung | 4-7 | 1440 | **nicht aussagekräftig** | 42 | 31 | 0 | 0 | 27 | 0 | 15 | 34 |
| Home / Startseite | 4-7 | 390 | gemessen | 2 | 0 | 0 | 0 | 26 | 0 | 0 | 30 |
| Home / Startseite | 4-7 | 1440 | gemessen | 26 | 9 | 0 | 0 | 41 | 0 | 0 | 45 |
| Arbeitsschein bearbeiten | 4-7 | 390 | gemessen | 24 | 0 | 0 | 0 | 25 | 0 | 0 | 33 |
| Arbeitsschein bearbeiten | 4-7 | 1440 | gemessen | 29 | 15 | 0 | 0 | 40 | 0 | 0 | 48 |
| Projektakte / Berichte | 8-11 | 390 | gemessen | 29 | 0 | 0 | 3 | 14 | 0 | 1 | 24 |
| Projektakte / Berichte | 8-11 | 1440 | gemessen | 26 | 30 | 0 | 1 | 28 | 0 | 1 | 30 |
| Projektakte / Bautagebuch | 8-11 | 390 | gemessen | 13 | 0 | 0 | 2 | 16 | 0 | 0 | 24 |
| Projektakte / Bautagebuch | 8-11 | 1440 | gemessen | 14 | 28 | 0 | 1 | 30 | 0 | 0 | 30 |
| Projektakte / Material | 8-11 | 390 | gemessen | 14 | 0 | 0 | 2 | 19 | 0 | 0 | 30 |
| Projektakte / Material | 8-11 | 1440 | gemessen | 15 | 36 | 0 | 1 | 33 | 0 | 0 | 36 |
| Projektakte / Pläne | 8-11 | 390 | gemessen | 25 | 0 | 0 | 2 | 33 | 0 | 0 | 52 |
| Projektakte / Pläne | 8-11 | 1440 | gemessen | 42 | 52 | 0 | 1 | 48 | 0 | 0 | 57 |
| **Arbeitsscheine / LISTE** | 8-11 | 390 | gemessen | 24 | 0 | 0 | 0 | **212** | 0 | 0 | **743** |
| **Arbeitsscheine / LISTE** | 8-11 | 1440 | gemessen | 29 | **733** | 0 | 1 | 41 | 0 | **185** | **756** |
| Chef-Dashboard | 12-15 | 390 | **nicht aussagekräftig** | 12 | 0 | 0 | 0 | 17 | 0 | 0 | 15 |
| Chef-Dashboard | 12-15 | 1440 | **nicht aussagekräftig** | 17 | 16 | 0 | 0 | 32 | 0 | 0 | 30 |
| Zeiterfassung | 12-15 | 390 | gemessen | 2 | 0 | 0 | 0 | 12 | 0 | 0 | 30 |
| Zeiterfassung | 12-15 | 1440 | gemessen | 7 | 43 | 0 | 0 | 27 | 0 | 0 | 45 |
| Abwesenheiten | 12-15 | 390 | gemessen | 14 | 0 | 0 | 0 | 20 | 0 | 0 | 40 |
| Abwesenheiten | 12-15 | 1440 | gemessen | 15 | 17 | 0 | 0 | 39 | 0 | 0 | 55 |
| Monatsabrechnung | 12-15 | 390 | gemessen | 2 | 0 | 0 | 0 | 7 | 0 | 0 | 13 |
| Monatsabrechnung | 12-15 | 1440 | gemessen | 7 | 9 | 0 | 0 | 22 | 0 | 0 | 28 |
| **Fahrzeuge** | 12-15 | 390 | gemessen | **39** | 0 | 0 | 0 | 11 | 0 | 0 | 36 |
| **Fahrzeuge** | 12-15 | 1440 | gemessen | **44** | 27 | 0 | 0 | 26 | 0 | 0 | 51 |
| Flotte / Fuhrpark-GPS | 12-15 | 390 | **nicht aussagekräftig** | 2 | 1 | 0 | 0 | 7 | 0 | 0 | 19 |
| Flotte / Fuhrpark-GPS | 12-15 | 1440 | **nicht aussagekräftig** | 13 | 19 | 2 | 0 | 22 | 0 | 0 | 34 |
| Mitarbeiter | 12-15 | 390 | gemessen | 16 | 0 | 0 | 0 | 9 | 0 | 0 | 15 |
| Mitarbeiter | 12-15 | 1440 | gemessen | 21 | 9 | 0 | 0 | 24 | 0 | 0 | 30 |
| **Auswertungen** | 12-15 | 390 | **nicht aussagekräftig** | **276** | 0 | 0 | 0 | 15 | 0 | 0 | 105 |
| **Auswertungen** | 12-15 | 1440 | **nicht aussagekräftig** | **350** | 99 | 0 | 0 | 30 | 0 | 0 | 120 |
| Büro-Portal | 12-15 | 390 | gemessen | 10 | 0 | 0 | 0 | 18 | 0 | 0 | 22 |
| Büro-Portal | 12-15 | 1440 | gemessen | 15 | 12 | 0 | 0 | 33 | 0 | 0 | 37 |
| Admin | 12-15 | 390 | gemessen | 10 | 0 | 0 | 0 | 29 | 0 | 0 | 35 |
| Admin | 12-15 | 1440 | gemessen | 15 | 22 | 0 | 0 | 44 | 0 | 0 | 50 |
| Einstellungen | 12-15 | 390 | **nicht aussagekräftig** | 8 | 0 | 0 | 0 | 15 | 0 | 0 | 22 |
| Einstellungen | 12-15 | 1440 | **nicht aussagekräftig** | 13 | 10 | 0 | 0 | 30 | 0 | 0 | 37 |
| Gefahrenstoffe | 12-15 | 390 | **nicht aussagekräftig** | 2 | 0 | 0 | 0 | 8 | 0 | 0 | 12 |
| Gefahrenstoffe | 12-15 | 1440 | **nicht aussagekräftig** | 7 | 9 | 0 | 0 | 23 | 0 | 0 | 27 |
| Bauprovisorien | 12-15 | 390 | **nicht aussagekräftig** | 2 | 0 | 0 | 0 | 8 | 0 | 0 | 13 |
| Bauprovisorien | 12-15 | 1440 | **nicht aussagekräftig** | 7 | 10 | 0 | 0 | 23 | 0 | 0 | 28 |

**Bilanz:** 44 Aufnahmen · Tor A verletzt **0** · Tor B verletzt **14** ·
nicht erreicht / abgebrochen **0**.

### 5.1 Die Überlauf-Funde, je einzeln: rollt er, oder geht etwas verloren?

**„Verloren" = Rechteck ragt über `innerWidth` hinaus UND kein rollbarer
Vorfahr.** Es gibt in allen 44 Aufnahmen genau **zwei** — beide in derselben
Ansicht, und beide sind **kein Befund**:

* **Flotte @ 1440 px:** zwei `img.leaflet-tile` à 256 px, rechts bei 1642 px.
  Das sind **Kartenkacheln von Leaflet**, die über den sichtbaren Bereich
  hinausreichen — das ist die Bauart einer Schiebekarte, nicht ein
  abgeschnittener Inhalt.

**Rollende Behälter** (Inhalt erreichbar, nichts verloren):

| Ansicht | Breite | Behälter | Überschuss | breitestes Kind |
|---|---|---|---|---|
| **Werkzeuge** | **390** | `div.main-pad` | **+23 px** | **405 px — `⚙️ Bosch GBH 18V-26 F Akku-Bohrhammer…`** |
| Berichte | 390 | `div.tab-bar.pf-hauptnav` | +586 px | 113 px `📄Monatsabrechnung` |
| Berichte | 390 | Tabellenbehälter | +346 px | 720 px `GewerkMo21.09.…` |
| Berichte | 390 | Projekt-Reiterzeile | +31 px | 89 px `Mängel1` |
| Berichte / Bautagebuch / Material / Pläne | 1440 | `div.tab-bar` | +158 px | 142 px `📄Monatsabrechnung` |
| Bautagebuch / Material / Pläne | 390 | `div.tab-bar.pf-hauptnav` | +586 px | 113 px `📄Monatsabrechnung` |
| Arbeitsscheine / LISTE | 1440 | `div.epk-tab-fade > div > div` | +139 px | 1537 px `AS-2401Zaehlerkasten tauschen…` |

🔴 **Der Werkzeuge-Roller bei 390 px ist NEU und ein Saat-Befund**: unter der
alten Saat rollt dort nichts (0 → 1). Er entsteht an einem **realistisch langen
Werkzeugnamen**. Sechs Kurznamen zeigen das nicht.

Die Projekt-Reiterzeile (+586 / +158 px) ist die im Abschlussbericht
ausdrücklich getroffene Entscheidung („bleibt rollbar", 13 Reiter) und
**unverändert zwischen beiden Saaten** — kein Saat-Befund.

### 5.2 Icon-Knöpfe ohne `aria-label` und ohne `title`

**0 in allen 44 Aufnahmen — und in allen 44 Aufnahmen der alten Saat.**

Das ist eine **gemessene** Null, keine blinde: der Köder aus §4.5 hat in jedem
Lauf angeschlagen, in **beiden** Formen (astral und BMP). Die Arbeit aus
v3.9.960/961 hält auch bei 3 513 sichtbaren Knöpfen statt 1 583.

---

## 6. Der Unterschied zur Saatmessung von v3.9.954

**Methodisch:** verglichen wird **nicht** gegen die Zahlen der alten Berichte,
sondern gegen einen **zweiten Lauf desselben Skripts an derselben
`index.html`** mit der alten, dünnen Saat (`B12._saat12()`). Ein Vergleich
gegen ein anderes Messskript würde zwei Dinge auf einmal vergleichen.

### 6.1 Summen über alle 44 Aufnahmen

| Größe | alte Saat | neue Saat | Unterschied |
|---|---|---|---|
| Elemente unter 12 px | 1 036 | **1 354** | **+318** |
| Tippziele unter 44 px | 550 | **1 952** | **+1 402** |
| Überlauf, Inhalt verloren | 2 | 2 | 0 |
| Überlauf, Behälter rollt | 14 | 15 | +1 |
| Emoji in Knopftexten | 1 049 | **1 444** | **+395** |
| **Icon-Knöpfe ohne Namen** | **0** | **0** | **0** |
| Tabellenzeilen | 31 | **502** | **+471** |
| sichtbare Knöpfe | 1 583 | **3 513** | **+1 930** |

### 6.2 Wo die neue Saat mehr findet — der blinde Fleck der alten Messung

🔴 **Das ist kein Fehler der alten Messung, sondern ihr blinder Fleck.** Die
alten Zahlen waren an ihrer Grundgesamtheit richtig; die Grundgesamtheit
enthielt den Fall nicht.

| Ansicht | Breite | Größe | alt → neu |
|---|---|---|---|
| **Werkzeuge** | 1440 | Tippziele < 44 px | **29 → 715** (+686) |
| **Werkzeuge** | 1440 | Tabellenzeilen | **6 → 300** (+294) |
| **Werkzeuge** | 390/1440 | Emoji im Knopftext | **16 → 114 / 36 → 134** (+98) |
| **Werkzeuge** | 390 | rollende Behälter | **0 → 1** (der lange Werkzeugname) |
| **Arbeitsscheine / LISTE** | 1440 | Tippziele < 44 px | **47 → 733** (+686) |
| **Arbeitsscheine / LISTE** | 1440 | Tabellenzeilen | **8 → 185** (+177) |
| **Arbeitsscheine / LISTE** | 390 | Emoji im Knopftext | **35 → 212** (+177) |
| **Fahrzeuge** | 390 | Elemente < 12 px | **12 → 39** (+27) |
| **Fahrzeuge** | 1440 | Elemente < 12 px | **17 → 44** (+27) |
| **Fahrzeuge** | 1440 | Tippziele < 44 px | **11 → 27** (+16) |
| **Auswertungen** | 390 | Elemente < 12 px | **142 → 276** (+134) |
| **Auswertungen** | 1440 | Elemente < 12 px | **217 → 350** (+133) |
| Zeiterfassung | 1440 | Tippziele < 44 px | 30 → 43 (+13) |
| Admin / Büro-Portal / Home | beide | Emoji im Knopftext | +6 / +2 / +3 |

### 6.3 Wo sie **nicht** mehr findet — dort lag die Ursache nicht an der Saat

**Byte-identisch zwischen beiden Saaten, in jeder gemessenen Größe:**

* **Planung / Wochenplanung** (390 **und** 1440) — siehe §7.3, der Kern dieses
  Berichts
* Arbeitsschein **bearbeiten** (Formular, eine einzelne Karteikarte)
* Projektakte: Bautagebuch · Material · Pläne · Berichte (bis auf −3 bei 1440)
* Abwesenheiten · Monatsabrechnung · Mitarbeiter · Chef-Dashboard ·
  Einstellungen · Gefahrenstoffe · Bauprovisorien · Flotte

Besonders bemerkenswert: **Abwesenheiten und Mitarbeiter zeigen nachweislich
alle neun aktiven plus die ausgetretenen Namen** (Tor B: 9 bzw. 10 verschiedene
Saatmarken) — und ihre Zahlen bewegen sich trotzdem nicht. Ihre
Mitarbeiterzeilen verwenden also **keine** Schrift unter 12 px und keine
Tippziele unter 44 px. Für diese Ansichten ist „die Saat war zu dünn" **widerlegt**.

**Eine einzige Größe wird kleiner:** Projektakte / Berichte @ 1440,
Elemente < 12 px **29 → 26**. Ursache **nicht gemessen**.

### 6.4 Einordnung gegen die veröffentlichten Vorher-Zahlen

Die dokumentierten Vorher-Stände (`docs/befunde/B3_STUFEN_4_7.md`,
`B3_STUFEN_8_11.md`, `B3_STUFEN_12_15.md`, gemessen an `_mess_stand_944.html`)
nennen z. B. Fahrzeuge 390 = **12**, Fahrzeuge 1440 = **17** — **exakt** die
Werte, die mein Lauf mit der alten Saat reproduziert. Die Vergleichsbasis
stimmt also. Die im Auftrag genannten Zahlen (Home 106, Planung 120,
Fahrzeuge 97 …) stammen aus einer **anderen** Aggregation als diese Berichte;
welche, ist **nicht gemessen** — dieser Bericht vergleicht deshalb
ausschließlich die beiden eigenen, gleich gemessenen Läufe.

---

## 7. Die drei offenen Ansichten — die Antwort

### 7.1 Fahrzeuge — **die Vermutung trägt**

| | 390 px | 1440 px |
|---|---|---|
| Elemente < 12 px | **12 → 39** | **17 → 44** |
| Tippziele < 44 px | 0 → 0 | **11 → 27** |
| Saatmarken in der Ansicht | 7 | 7 |

Die zusätzlichen Stellen sind die **Kennzeichnungs-Chips je Fahrzeugkarte**:
`⛽ 1 Tankungen` und `⚠️ 1 Schaden`, beide bei **10 px**. Unter der alten Saat
steht im Befund je einer bzw. zwei davon, unter der neuen füllen sie die Liste.
(Die Beispiellisten in den Rohdaten sind auf zwölf Einträge gekürzt, die
**Zahlen** 12/39 und 17/44 nicht.) Dazu die 9-px-Marke `MEIN` — die gibt es
genau **einmal**, am eigenen Fahrzeug, in beiden Saaten.

Bei drei Fahrzeugen fallen diese Chips kaum auf, bei 21 sind sie der Befund.
**Ein Prüfstand mit drei Fahrzeugen konnte das nicht finden.**

### 7.2 Arbeitsscheine — **die Vermutung trägt, aber bei einer anderen Größe**

| | 390 px | 1440 px |
|---|---|---|
| Elemente < 12 px | 24 → 24 (**unverändert**) | 29 → 29 (**unverändert**) |
| Tippziele < 44 px | 0 → 0 | **47 → 733** |
| Emoji im Knopftext | **35 → 212** | 41 → 41 |
| Tabellenzeilen | 0 → 0 | **8 → 185** |
| sichtbare Knöpfe | 57 → **743** | 70 → **756** |

Bei **1440 px** trägt die Tabelle **185 Zeilen** mit **733** Tippzielen unter
44 px — unter der alten Saat waren es 47. Bei **390 px** wird die Liste zu
Karten: **212 Knöpfe mit Emoji im Text** statt 35. Die Zahl „Elemente < 12 px"
bleibt dagegen **exakt gleich**: die kleinen Schriften der AS-Liste sitzen in
der **Kopfleiste** (`kpi-grid.epk-leiste`: `Arbeitsscheine`, `zu erledigen`,
`offen` bei 10 px), nicht in den Zeilen. **Für diese eine Größe war die Saat
nicht die Ursache.**

### 7.3 Planung — **die Vermutung trägt NICHT, und die Ursache ist eine andere**

**Alle gemessenen Größen sind zwischen dünner und voller Saat identisch:**

| | 390 px | 1440 px |
|---|---|---|
| Elemente < 12 px | 44 → **44** | 42 → **42** |
| Tippziele < 44 px | 0 → 0 | 31 → **31** |
| Emoji im Knopftext | 12 → **12** | 27 → **27** |
| Tabellenzeilen | 0 → 0 | 15 → **15** |

185 statt 8 Arbeitsscheinen, 9 statt 3 Monteuren, 21 statt 3 Fahrzeugen — und
**keine einzige Zahl bewegt sich.**

**Zwei Erklärungen wären möglich gewesen, und sie führen zu entgegengesetzten
Schlüssen.** Entweder zeigt die Ansicht den Bestand gar nicht — dann ist die
Saat nicht die Ursache. Oder sie zeigt ihn **gekürzt** (`Steinb` statt
`Steinbichler`) — dann wäre **mein Tor-B-Melder für genau diese Form blind**
und ich hätte mit einem blinden Messgerät gemessen. Der Unterschied ist nicht
erschließbar, er ist ablesbar. Dafür stehen die zwei Verwechslungspaare in der
Saat (§2.2). `scripts/echtmengen_planung_probe.py` liest den Text und sucht
zusätzlich nach den **auf sechs Zeichen gekürzten** Vor- und Nachnamen:

| Planung | volle Saatmarken | gekürzte Nachnamen (6) | Vornamen (6) |
|---|---|---|---|
| 390 px (880 Zeichen Text) | **keine** | **keine** | **keine** |
| 1440 px (1 610 Zeichen) | `Steinbichler` | `Steinb` | `Gerhar` |

Und die eine Marke bei 1440 px ist **nicht** der Bestand: sie steht in der
Kopfleiste („👑 Gerhard Steinbichler · Administrator · KW 39") — der
**angemeldete Benutzer**. Die Planungstabelle selbst zeigt in jeder Zelle `—`.

**Die Ursache, geschnitten aus `index.html`, nicht geraten:**

    // ═══════════ WOCHENPLANUNG — with History, Edit, Export ═══════════
    const DSHORT=["Mo","Di","Mi","Do","Fr","Sa"];
    const W0=[{id:1,bvh:"WHA Marktplatz 20",projId:"",bem:"Erdung",
               z:{Mo:{ma:["w3"],fz:[]}, …

`W0` ist ein **fest eingebauter Vorgabe-Wochenplan** von 902 Zeichen mit
**fünf** Zeilen — `WHA Marktplatz 20` · `FC Moser Medical` · `BVH Kaprun` ·
`Dr. Gschmeidlerstraße` · `öffentl. Beleuchtung Fels` — und Monteur-Kürzeln
`w1 · w2 · w3 · w5`, **nicht** `M1…M11`. Genau diese fünf Zeilen stehen in
beiden Läufen in der Ansicht. Die Wochenplanung wird von dieser Saat **nicht
gespeist**; eine Saatänderung kann ihre Zahlen nicht bewegen.

**Was das für Planung heißt:** die 44 bzw. 42 Elemente unter 12 px sind echt
(`3 MA` · `2 MA` · `4 MA` bei **9 px** in der MA-Übersicht; `Bedeckt` ·
`L. Regen` · `Schauer` bei **9 px** im Wetterband bei 1440 px), aber sie haben
mit der Bestandsgröße nichts zu tun. **Der Weg zu einer aussagekräftigen
Messung der Wochenplanung führt über den WeekPlan-Speicher, nicht über die
Saat** — welcher Speicher das ist und ob die Ansicht überhaupt aus
`monteure` liest, ist in diesem Lauf **nicht gemessen**.

---

## 8. 🔴 Ein eigener Widerruf: Tor B ist für Aggregat-Ansichten blind

Tor B hat **Chef-Dashboard** bei beiden Breiten als „nicht aussagekräftig"
gestempelt (0 bzw. 1 Saatmarke). **Das Urteil ist in der Sache falsch.** Die
Probe aus §7.3 hat denselben Text auch für Chef gelesen:

    AKTIVE PROJEKTE 3 · 3 gesamt │ OFFENE AS 95 · 185 gesamt │
    MONTEURE HEUTE 0/9 │ ÜBERFÄLLIG 65 │ AS ohne Monteur: 9

**3 Projekte, 185 Arbeitsscheine, 9 Monteure** — das Chef-Dashboard liest die
volle Grundgesamtheit und zeigt sie als **Zahl**, nicht als Namen. Mein Tor B
sucht **Namen**. Es misst einwandfrei, nur eine **andere** Grundgesamtheit als
die, über die es urteilt — und eine Abwesenheit darin belegt nichts.

**Was daraus folgt, ohne es zu beheben (kein Fix in diesem Block):**

* Für die Ansichten **Chef, Auswertungen** ist der Stempel „nicht
  aussagekräftig" **zu streng**; beide reagieren nachweislich auf die Saat
  (Auswertungen: 142 → 276 Elemente unter 12 px).
* Für **Planung, Flotte, Gefahrenstoffe, Bauprovisorien, Einstellungen** ist er
  durch den Vergleich der beiden Läufe **bestätigt**: dort bewegt sich nichts.
* Die belastbare zweite Vorschrift ist **nicht** „zeigt die Ansicht Namen?",
  sondern **„ändern sich ihre Zahlen, wenn sich der Bestand ändert?"** — und
  die lässt sich nur aus **zwei** Läufen mit verschiedener Saat beantworten,
  nicht aus einem. Genau das leistet §6.

---

## 9. Was ich NICHT gemessen habe

Ein „nicht gemessen" ist **kein** bestandener Fall.

1. **Unterzustände.** Je Ansicht ist der EINE Zustand aufgenommen, in den die
   Navigation führt. Chef hat fünf Reiter, Admin sechs, das Büro-Portal fünf
   (**aus `docs/GRUNDSTAND_UI_v3.9.954.md` übernommen, in diesem Lauf nicht
   nachgezählt**) — aufgenommen ist jeweils der erste. Allein diese drei
   Ansichten tragen also 16 Zustände statt drei; wie viele es insgesamt sind,
   ist **nicht gemessen**.
2. **Alle Rollen außer `admin`.** Monteur, Obermonteur, Büro sehen andere
   Ansichten und andere Knöpfe.
3. **Alles hinter einem Klick:** Dialoge, Menüs, Aufklapper, Bestätigungen.
4. **Nur zwei Breiten.** 375 px (iPhone SE), 640, 767, 768 und 1199 px sind
   nicht gemessen — und 640/767 sind genau die Breiten, bei denen der
   Abschlussbericht zu v955 einen Unterschied gefunden hat.
5. **Nur das dunkle Thema.** Der Hellmodus ist nicht gemessen.
6. **Tippziele bei 1440 px mit GROBEM Zeiger** (Touch-Notebook, Tablet quer).
   Dort greift die Hausregel nicht, und die Zahlen der 1440-px-Spalte wären
   echte Regelbrüche. Der Fall ist offen.
7. **Die Wirkung der Befunde auf einen Menschen.** „44 Elemente unter 12 px"
   sagt nicht, ob eines davon unlesbar ist.
8. **Der WeekPlan-Speicher** (§7.3) — welcher Speicher die Wochenplanung
   speist, ist nicht gemessen; gemessen ist nur, dass **diese** Saat sie nicht
   erreicht.
9. **Warum Projektakte / Berichte @ 1440 unter der vollen Saat DREI Stellen
   WENIGER unter 12 px hat.** Die Richtung ist gemessen, die Ursache nicht.
10. **Die Herkunft der „elf Status"** aus dem Auftrag (§2.3). Die App kennt
    acht.
11. **Ob der Server-Zustand etwas ändert.** REST und Auth sind abgeklemmt; mit
    erreichbarem Server sähen Flotte, Gefahrenstoffe, Bauprovisorien und die
    Lager-Reiter anders aus. Ihre Zahlen hier sind die eines leeren Blatts —
    und genau so stehen sie gestempelt da.
12. **Beschnitt** (`BESCHNITT_ECHT_JS`), **Verdeckung durch die Fußleiste**
    (`VERDECKUNG_JS`) und **Tabellen breiter als der Schirm** (`TABELLE_JS`).
    Der Auftrag nennt fünf Messungen; diese drei gehören nicht dazu und sind in
    diesem Lauf nicht gefahren.

---

## 10. Was dieser Lauf im Baum hinterlässt

| Datei | Größe | git-ignoriert? |
|---|---|---|
| `scripts/echtmengen_saat.py` | Quelltext | nein — **gehört ins Repo** |
| `scripts/echtmengen_messen.py` | Quelltext | nein — **gehört ins Repo** |
| `scripts/echtmengen_tabellen.py` | Quelltext | nein — **gehört ins Repo** |
| `scripts/echtmengen_planung_probe.py` | Quelltext | nein — **gehört ins Repo** |
| `docs/befunde/MESSUNG_ECHTMENGEN.md` | dieser Bericht | nein — **gehört ins Repo** |
| `scripts/_echtmengen_neu.log` · `_echtmengen_alt.log` | Protokolle | **ja** (`*.log`) |
| 🔴 `scripts/_echtmengen_rohdaten.json` | 398 917 B, Rohdaten neue Saat | **NEIN** |
| 🔴 `scripts/_echtmengen_rohdaten_alt.json` | 405 057 B, Rohdaten alte Saat | **NEIN** |
| 🔴 `scripts/_echtmengen_planung.txt` | 5 170 B, Text der Planung/Chef-Ansicht | **NEIN** |
| 🔴 `scripts/_echtmengen_tabellen.md` | 19 246 B, erzeugte Tabellen (Vorstufe dieses Berichts) | **NEIN** |

Die vier rot markierten Dateien sind **Messartefakte** und nähmen bei einem
`git add -A` teil. Solange **Stufe 0a offen** ist, gibt es keinen Riegel, der
das abfängt — sie sind einzeln zu behandeln.

**Keine `_mess_*.html`-Kopie angelegt.** Vor dem Lauf mit
`tasklist | findstr chrome` geprüft: kein Browser lief; die von Playwright
gestarteten Chromium-Instanzen sind am Ende jedes Laufs geschlossen
(`browser.close()`), der Baum am Ende chrome-frei.
