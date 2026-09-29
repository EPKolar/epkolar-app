# Container mit Tastenbehandler und `preventDefault()`

> Messlauf, keine Aenderung. Erzeugt von `scripts/keydown_container_audit.py`.


**113 Container** mit `onKeyDown` + `preventDefault()` im Code.


| | mit Waechter (heute) | ohne Waechter (vor v3.9.985) |
|---|---:|---:|
| 🔴 GEFAEHRLICH | 0 | 13 |
| 🟡 PRUEFEN | 0 | 3 |
| 🟢 OK | 113 | 97 |

🔴 **Die rechte Spalte ist der eigentliche Befund**: sie sagt, wie viele Container
vor v3.9.985 den Tastendruck eines inneren Bedienelements gefressen haetten.


## Die 13 Container mit interaktivem Kind

| Zeile | Tag | Zweck | innere Bedienelemente | heute |
|---|---|---|---|---|
| 7006 | `div` | ✅ Abnahme bestätigen — Mangel ist behoben | `button` | 🟢 geschuetzt |
| 9675 | `div` | Benachrichtigung löschen | `button` | 🟢 geschuetzt |
| 11519 | `div` | Bearbeiten | `button` | 🟢 geschuetzt |
| 15771 | `div` | Projekt  | `input` | 🟢 geschuetzt |
| 17068 | `div` | 📥 Download | `a`, `button` | 🟢 geschuetzt |
| 19255 | `div` | Foto löschen | `button` | 🟢 geschuetzt |
| 19271 | `div` | Vorheriges Bild | `a`, `button` | 🟢 geschuetzt |
| 20534 | `div` | 🗑 Löschen | `button` | 🟢 geschuetzt |
| 22881 | `div` | Bearbeiten | `button` | 🟢 geschuetzt |
| 27738 | `div` | — | `button` | 🟢 geschuetzt |
| 28645 | `div` | — | `button` | 🟢 geschuetzt |
| 29187 | `div` | Datei löschen | `button` | 🟢 geschuetzt |
| 29205 | `div` | Ordner umbenennen | `button` | 🟢 geschuetzt |

## 3 Faelle, die von hier aus nicht entscheidbar sind

Ein Kind ueber eine Variable, einen Spread oder eine Komponente ist im Quelltext
nicht aufloesbar. Diese Faelle stehen bewusst NICHT in einer der beiden anderen
Spalten - raten waere hier schlimmer als nicht wissen.

| Zeile | Tag | Zweck | heute |
|---|---|---|---|
| 10321 | `div` | — | 🟢 geschuetzt |
| 14111 | `div` | — | 🟢 geschuetzt |
| 30057 | `div` | — | 🟢 geschuetzt |
