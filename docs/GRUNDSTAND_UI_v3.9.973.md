# Grundstand UI v3.9.973 — der Schriftboden gilt überall

**Erhoben am 28.09.2026.** 22 Ansichten, 44 Aufnahmen, je 390 **und** 1440 px,
echte Saat (9 aktive Monteure + 2 ausgetretene · 21 Fahrzeuge · 296 Werkzeuge ·
185 Arbeitsscheine · 3 Projekte). Keine Ansicht unerreicht, alle 16 Köder
angeschlagen, Köder restlos entfernt.

## Die Zahl, um die es ging

| | 27.09. (v3.9.962) | 28.09. mittags (v3.9.967) | **28.09. jetzt (v3.9.973)** |
|---|---|---|---|
| **Elemente < 12 px** | 1354 | 911 | **0** |
| Textverlust | 0 | 0 | 0 (nur `flotte`: 2 Leaflet-Kacheln) |
| Querlauf | — | 15 | **15 — kein Wert gestiegen** |
| Icon-Knöpfe ohne Namen | 0 | 0 | **0** |
| Tippziele < 44 px | 1952 | 1952 | 1939 |

**Null in allen 44 Aufnahmen.** Nicht eine Ansicht hält noch eine Stelle.

Und die Null ist **belegt**, nicht behauptet: die Wirkungsmessung
(`scripts/schriftgroesse_wirkung.py`) setzt je Aufnahme ein 9-px-Element ein,
muss es finden und danach restlos entfernen. Beide Flaggen stehen im Bericht,
in jeder Aufnahme „gefunden+weg".

## Wie es dahin kam — 513 Stellen in fünf Schreibweisen

v3.9.944 hatte den Rundumschlag **abgelehnt**, und die Begründung war richtig:
*„Alle auf einmal zu heben wäre eine Wette … messen kann ich mit den
vorhandenen Sonden VIER Ansichten von 22."* Die **Begründung** ist entfallen,
nicht die Vorsicht — der Prüfstand misst inzwischen 22 Ansichten mit Meldern
für Querlauf *und* Textverlust. Die Wette wurde nachgerechnet.

| | Form | Zahl | wie sie auffiel |
|---|---|---|---|
| 1 | `fontSize:9` | 480 | die nackte Zahl |
| 2 | `fontSize:isMob?9:14` | — | kleine Zahl **links** — das einzige Muster, das v3.9.943 hatte |
| 3 | `fontSize:isMob?12:10` | 27 | kleine Zahl **rechts**. Der Kommentar an der Tokenleiter nennt sie seit v3.9.947 **wörtlich** |
| 4 | `fontSize:isMob?UI.fMeta:8` | 4 | Token gegen Zahl. `home` hielt bei 1440 px noch 19 |
| 5 | `fontSize:h>0?13:11` | 2 | die Bedingung ist ein **Ausdruck**. `berichte` hielt noch 8 |

🔴 **Keine der vier Lücken ist durch Nachdenken aufgefallen.** Jede dadurch,
dass die Schirmmessung nach dem vermeintlich vollständigen Griff nicht auf null
ging und ich das laufende Element gefragt habe. Form 3 stand seit drei Wochen
wörtlich in einem Kommentar dieser Datei — *eine Regel zu kennen verhindert den
Fehler nicht.*

## Was dabei sonst gefunden wurde

* **Das Ringdiagramm verschluckte Einträge.** `SvgPie` zeichnete Legendenzeile
  *i* bei `y=i*18+16` in eine `viewBox` der Höhe 150 — sichtbar waren **acht**
  Zeilen. `absTyp` verlor 7 von 15, `asArt` 1 von 9. Das ist fehlende
  Information, nicht kleine, und niemand sieht sie fehlen.
* **Die `svg text`-Ausnahme nahm zurück.** Sie galt nur unter 600 px und
  drückte dort zwei bereits richtige Werte herunter (x-Achse 12→10, Ringsumme
  15→10). Entfernt statt gehoben.
* **`SvgLine` beschriftete jeden GPS-Punkt.** Bei 40–120 Punkten überlappten
  die Uhrzeiten schon bei 8 px. Jetzt höchstens acht Beschriftungen; die
  **Kurve** behält jeden Punkt.
* **24 CSS-Wahlmuster treffen nie** — sie suchen die JavaScript-Schreibweise im
  `style`-Attribut. Ergänzt (Tippziel-Familie), aufgeschoben
  (Überlagerungs-Familie). Messbare Wirkung: **null**, und warum, steht in
  `docs/befunde/TOTE_WAHLMUSTER.md`.

## 🔴 Was dieser Grundstand NICHT abdeckt

* **14 der 44 Aufnahmen sind „nicht aussagekräftig" gestempelt** — das Tor
  verweigert dort die Aussage, und es hat recht: diese Ansichten zeigen den
  Bestand als Zahl oder erreichen ihn gar nicht.
* **Die Wochenplanung erreicht die Saat prinzipiell nicht.** Der Wochenplan
  liegt in keinem der 21 Offline-Speicher.
* **1939 Tippziele unter 44 px, alle bei 1440 px.** Bei 390 px sind es 0 in 21
  von 22 Ansichten. Das ist ein **Schreibtisch**-Befund und war nie Gegenstand
  dieser Reihe — es ist jetzt die größte offene Zahl des Bestands.
* **Die `pt`-Größen im Druck- und Export-HTML** (8pt, 9pt). Sie betreffen
  Papier, nicht den Schirm, und sind von keiner Messung dieser Reihe erfasst.
* **Kein Melder für Überlappung.** Die Ausdünnung in `SvgLine` ist aus der
  `viewBox`-Arithmetik gerechnet, nicht am Schirm gemessen.
* **Keine geöffneten Dialoge.** Die Messreihe misst Ansichten im Ruhezustand;
  Modale, Schubladen und Detailfenster sind nie erfasst worden. Ein
  erheblicher Teil des Bestands ist damit ungemessen — das gilt für die Null
  oben genauso wie für alles andere.
