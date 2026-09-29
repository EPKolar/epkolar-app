# Stille Schreibfehler - wer wirft den Fehler weg?

Erzeugt von `scripts/stille_schreibfehler.py`.

Die Schreib-Helfer sind in Ordnung: `_sbPost`, `_sbPatch`, `_sbUpsert`,
`_sbDelete`, `_sbDeleteWhere`, `_sbInsertIfAbsent` pruefen **jeder** auf 401
und 403, rufen `_onAuthFail` und **werfen** mit Status im Text.
Gesucht wird deshalb nicht am Helfer, sondern beim **Aufrufer**: ein leeres
`catch`, dessen `try` einen Schreibvorgang enthaelt.

| Art | Anzahl | Bedeutung |
|---|---:|---|
| **schreiben** | **3** | der Nutzer glaubt, es sei gespeichert |
| lesen | 10 | zeigt die alten Daten weiter - oft gewollt |

Beurteilt wird je Aufruf das **innerste** ihn umschliessende `try/catch`.
Behandelt dieses den Fehler, ist der Fall erledigt - auch wenn ein
aeusseres ihn verwerfen wuerde. Der erste Entwurf urteilte ueber jedes
umschliessende `try` und meldete dadurch zu VIELE Faelle.

## 🔴 Schreibvorgaenge, deren Fehler verworfen wird

| Zeile | Ziel | catch | Urteil |
|---:|---|---|---|
| 5362 | `plz_geo` | nur Kommentar | **berechtigt** — Zwischenspeicher fuer eine Geokodierung. Die ARBEIT steht seit v3.9.987 vor dem Versuch - vorher riss der fehlgeschlagene Cache-Schreibvorgang den ganzen Lauf mit. Beleg: scripts/geo_nachzieh_wirkung.py |
| 5375 | `plz_distanz` | nur Kommentar | **berechtigt** — Zwischenspeicher fuer die Entfernungsmatrix. `distMatrix` und `matrixRows` stehen seit v3.9.987 vor dem Versuch. Beleg: scripts/geo_nachzieh_wirkung.py |
| 19687 | `plz_geo` | nur Kommentar | **berechtigt** — Zwischenspeicher fuer eine Geokodierung. Die ARBEIT steht seit v3.9.987 vor dem Versuch - vorher riss der fehlgeschlagene Cache-Schreibvorgang den ganzen Lauf mit. Beleg: scripts/geo_nachzieh_wirkung.py |

## Lesevorgaenge (zur Einordnung, kein Befund)

| Zeile | Ziel | catch | Urteil |
|---:|---|---|---|
| 2382 | `system_config` | nur Kommentar | **UNBEURTEILT** — noch niemand angesehen |
| 2502 | `system_config` | nur Kommentar | **UNBEURTEILT** — noch niemand angesehen |
| 9963 | `system_config` | nur Kommentar | **UNBEURTEILT** — noch niemand angesehen |
| 9967 | `workers` | leer | **UNBEURTEILT** — noch niemand angesehen |
| 10466 | `dispo_blocks` | nur Kommentar | **UNBEURTEILT** — noch niemand angesehen |
| 12390 | `workers` | leer | **UNBEURTEILT** — noch niemand angesehen |
| 12555 | `workers` | leer | **UNBEURTEILT** — noch niemand angesehen |
| 13817 | `activity_log` | nur Kommentar | **UNBEURTEILT** — noch niemand angesehen |
| 19676 | `plz_geo` | nur Kommentar | **berechtigt** — Zwischenspeicher fuer eine Geokodierung. Die ARBEIT steht seit v3.9.987 vor dem Versuch - vorher riss der fehlgeschlagene Cache-Schreibvorgang den ganzen Lauf mit. Beleg: scripts/geo_nachzieh_wirkung.py |
| 24191 | `workers` | leer | **UNBEURTEILT** — noch niemand angesehen |

