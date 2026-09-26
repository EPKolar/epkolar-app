# Grundstand nach dem UI-Umbau — v3.9.947

Aufgenommen am **26.09.2026** an `index.html` der Version **3.9.947**, nach
neun ausgelieferten Versionen (v3.9.939 bis v3.9.947).

**Zweck.** `GRUNDSTAND_UI_v3.9.930.md` hält fest, was *vor* dem Umbau da war.
Diese Datei hält fest, was *danach* da ist — damit der nächste Umbau eine
Abnahmegrundlage hat, die nicht ein Jahr alt ist.

---

## 🔴 Zuerst: was diese Datei ist und was nicht

**Sie ist keine Wunschliste und keine Beschreibung.** Jede Zahl darin ist an
der gerenderten Seite gemessen, mit benanntem Werkzeug und benanntem Köder.
Wo nicht gemessen wurde, steht das — und ein „nicht gemessen" ist **kein**
bestandener Fall.

**Sie deckt 22 von 31 Ansichten ab.** Die App führt 18 Hauptreiter (aus
`_allTabs`) und 13 Projekt-Unterseiten (aus `_allNav`) — aus dem Baum
aufgezählt, nicht aus dem Gedächtnis. Gemessen sind davon:

| Stufe | Ansichten | Werkzeug |
|---|---|---|
| 4–7 | Werkzeuge · Planung · Home · Arbeitsschein bearbeiten | `b3_vier_ansichten_messen.py`, 8 Köder |
| 8–11 | Berichte · Bautagebuch · Material · Pläne · Arbeitsscheine-Liste | `b3_stufen_8_11_messen.py`, 13 Köder |
| 12–15 | Chef · Zeiterfassung · Abwesenheiten · Monatsabrechnung · Fahrzeuge · Flotte · Mitarbeiter · Auswertungen · Büro · Admin · Einstellungen · Gefahrenstoffe · Bauprovisorien | `b3_stufen_12_15_messen.py`, 16 Köder |
| alle 31 | nur auf **feste dunkle Farben** im Hellmodus | `hellmodus_ansichten.py`, 248 Messpunkte |

**Nicht abgedeckt:** 19 Unterzustände (Chef 4 von 5, Abwesenheiten 3 von 4,
Admin 5 von 6, Büro-Portal 4 von 5, Flotte 2 von 3, Fahrzeuge-Kachelansicht
und -Detail) · alle Rollen außer `admin` · 1440 px mit **grobem** Zeiger ·
Textkontrast · Tastaturbedienung · Excel- und PDF-Export.
**Serverleer und deshalb ausdrücklich keine gemessenen Ist-Zustände:** Flotte,
Gefahrenstoffe, Bauprovisorien, vier Büro-Portal-Reiter, fünf Admin-Reiter,
die Monatszettel.

---

## Mengengerüst — gemessen an v3.9.947

| Ansicht | Breite | Knöpfe | Felder | Auswahlfelder |
|---|---|---|---|---|
| Werkzeuge | 390 | — | — | — |
| Planung | 390 | 37 | 0 | 0 |
| Planung | 1440 | 52 | 0 | 0 |
| Arbeitsschein bearbeiten | 390 | **44** | **22** | **4** |
| Arbeitsschein bearbeiten | 1440 | **59** | **22** | **4** |

Die **Knopfzahlen** sind nur eingeschränkt vergleichbar: die Zählvorschrift ist
nirgends festgelegt, und der Datenbestand der Messumgebung ist ein anderer als
der echte. **Hart sind die benannten Stücke** unten.

### Arbeitsscheine-Liste — die harte Prüfliste

Gemessen in **beiden** Breiten, bestanden:

* **11 Statuskacheln**: Gesamt · Offen (alle) · aufgenommen · freigegeben ·
  in Bearbeitung · aufgeschoben · erledigt · abgerechnet · bar bezahlt ·
  storniert · Fertig (alle)
* **7 Sortierkriterien**: Nummer · Erf.-Datum · Termin (best.) ·
  Termin (vorg.) · Status · Kunde · Monteur
  — bei 390 px über das Auswahlfeld „Sortieren:", bei 1440 px über die
  klickbaren Tabellenköpfe. **Beides zählt.** Eine Zählung, die nur das
  Auswahlfeld kennt, meldete bei 1440 px „7 von 7 verschwunden".
* **8 Schnellfilter-Chips**: Alle · Offen · In Arbeit · Erledigt · Meine ·
  Heute · Überfällig · Kein Monteur
* Suchfeld „Suche Nr, Kunde, Arbeit…" · **4 Unterreiter** (Liste · QR Scan ·
  Kalender · Dispo) · `OFFA Excel`

### Arbeitsschein bearbeiten

22 Eingabefelder · 4 Auswahlfelder mit zusammen **21 Optionen** (Monteur 3 ·
Priorität 6 · Scheinstatus 8 · Verrechnung 4) · **22 Feldbeschriftungen** ·
11 Statuskacheln und 4 Unterreiter oberhalb. Die vollständige Aufzählung steht
im Nachtrag von `GRUNDSTAND_UI_v3.9.930.md`.

### Mitarbeiter, Fahrzeuge, Abwesenheiten

**5/5 · 8/8 · 10/10** benannte Stücke, kein Regressionsfehler. Zwei davon nur
nach ausgeschriebener Gleichsetzung: „Listen-/Kachelumschalter" = `☰`/`⊞`,
„Favoritenstern" = `☆`, „vier Ansichtsreiter" = die vier Ikonen,
„Datei/Foto hochladen" = neuer Wortlaut.

---

## Regeln, die jetzt gelten und gemessen sind

| Regel | Stand an v3.9.947 |
|---|---|
| **Keine Schrift unter 12 px** | erfüllt in WerkzeugView, HomeView, ArbeitsscheinView; **offen** in WeekPlan (56 Stellen) und in den Ansichten der Stufen 12–15 (FahrzeugView 113 · AdminPanel 76 · AbsView 66 · …) |
| **Tippziele ≥ 44 px bei grobem Zeiger** | 0 Verstöße bei 375 und 390 px in allen gemessenen Ansichten außer Flotte (1, gezählt aber nicht benannt) |
| **Kein waagrechtes Rollen bei 390 px** | 1 echter Roller übrig (Admin, 374/562 — die sechs Unterreiter) |
| **Keine Bedeutung allein im Symbol** | 0 Bedienelemente ohne Buchstaben, ohne `title`, ohne `aria-label` in allen gemessenen Ansichten |
| **Keine feste dunkle Farbe, die der Hellmodus nicht erreicht** | 0 tragende Flächen in **allen 31** Ansichten; eine tote Stelle (`PlanViewer`) bleibt benannt statt gepflegt |
| **Nichts verdeckt hinter der Fußleiste** | 0 verdeckte Bedienelemente, am **Ende** jedes Rollers gemessen |

---

## 🔴 Offene Punkte, die jemand entscheiden muss

1. **Zwei Hauptnavigationen in einer App.** In der Projektakte hat die
   Fußleiste 13 Ziele, davon 586 px hinter einer Wischbewegung; im Rest der
   App sind es fünf Gruppen, alle sichtbar.
2. **Die Fußleisten-Beschriftung passt bei 12 px nicht.** Der Schlitz ist
   74 px, die Namen bis 112 px. Fünf sind gekürzt. Der volle Name steht im
   `title`. Ein Kurzname je Reiter würde es lösen — **das erfindet Wörter**.
3. **Die Arbeitsschein-Tabelle am Rechner** verliert bis zu 494 px in
   „Durchzuführende Arbeiten". Der ganze Text steht im `title`; wirklich
   abgeschnitten wird weiter. Platz gäbe es nur durch Einklappen von `SB` und
   `Auftragstyp` — beides Sortierkriterien.
4. **Der OFFA-Hinweis nennt die Scheine nicht** und ist kein Tippziel.
5. **`VBautag` heißt `isMob = ww < 768`** — die einzige Stelle, an der
   Tabletbreite „mobil" heißt. **Nicht angefasst**, wie beauftragt.
6. **`ChefDashboard` benutzt eine dritte Datumslogik** für den Austritt
   (`!String(m.austritt||'').trim()` statt `austritt < heute`). Für einen
   Austritt in der **Zukunft** widersprechen sich die beiden.
   🔴 Nur im Quelltext gelesen, **nicht gemessen**.
7. **Planung, Knopf „Vorlage"** erscheint in keiner gemessenen Breite, steht
   aber im Quelltext. Vermutlich an leerer `wpHistory`. 🔴 **Nicht gemessen,
   nicht bestanden.**

---

## Die Werkzeuge, mit denen das nachzumessen ist

```
python scripts/b3_vier_ansichten_messen.py     # EPK_BREITEN="375,390,1440"
python scripts/b3_stufen_8_11_messen.py        # --nur <ansicht>
python scripts/b3_stufen_12_15_messen.py       # --nur <ansicht>
python scripts/hellmodus_ansichten.py          # alle 31, beide Themen
python scripts/hellmodus_messen.py             # Startansicht, mit Köder
python scripts/b3_fussleiste_beschnitt.py      # die 74-px-Frage
python scripts/b7_syncknopf_messen.py          # Kastenüberlauf vs. Textverlust
python scripts/b3_bestand_quelltext.py         # Mengengerüst aus dem Quelltext
python scripts/innerwidth_reaktion_messen.py   # reagiert die Breite auf Drehung
```

Jede dieser Sonden hat einen **Köder** und einen Dateikopf, der sagt, was sie
**nicht** misst. Wo ein Köder nicht anschlägt, meldet sie „nicht gemessen" und
nicht „in Ordnung" — das ist der Unterschied, an dem in diesem Umbau ein
Dutzend Zahlen gehangen haben.
