# KV-Proposals — vier offene Näherungen (Stand 15.07.2026)

**Zweck:** Die vier bei der Bug-Hunt-Welle v3.9.664 dokumentierten KV-Näherungen einzeln
entscheidbar machen — je Punkt: Ist-Verhalten im Code, die zu treffende Entscheidung, ein
durchgerechnetes Zahlenbeispiel und der €-Delta pro Monat/MA. **Reines Entscheidungs-Dokument,
keine Code-Änderung.** Der Lohnverrechner bleibt maßgeblich; die App bildet nur ab, was Sebastian
hier entscheidet.

**Verwendete KV-Sätze (aus `KV_RULES_FALLBACK`, index.html):** Montagezulage 1,155 €/h (2026);
Taggeld ab 6 h 11,94 € · ab 11 h 30,00 € · Nächtigung 62,04 €; Zuschläge Mehrarbeit/Ü50 = 50 %,
Ü100 = 100 %; Tagesnorm Mo–Do 8,5 h / Fr 4,5 h. Beispiel-MA: 160 Arbeitsstunden/Monat.

---

## 1. Montagezulage — nur Baustellen-Stunden vs. alle Stunden

**Ist (Code):** `_kvMontagezulage(baustellenStd, rules)` = `baustellenStd × 1,155`. Die Zulage
zählt **nur Stunden auf der Baustelle** — Werkstatt- und Fahrtstunden sind ausgenommen.

**Entscheidung:** Soll die Montagezulage auf **alle** Arbeitsstunden (inkl. Werkstatt + Fahrt)
laufen, oder bei Baustellen-Stunden bleiben?

**Beispiel** (MA-Monat 160 h: 120 Baustelle, 25 Werkstatt, 15 Fahrt):
| Variante | Rechnung | €/Monat |
|---|---|---|
| Ist (nur Baustelle) | 120 × 1,155 | **138,60 €** |
| Alle Stunden | 160 × 1,155 | **184,80 €** |
| **Delta** | 40 × 1,155 | **+46,20 €/Monat/MA** |

Bei 15 Monteuren betrieblich ≈ **+693 €/Monat**. Je nach Baustellen-Anteil skaliert das linear.

**Hinweis:** Rechtsfrage (KV Metallgewerbe Abschn. VIII) — gilt die Montagezulage tatbestandlich
für die Montagetätigkeit oder pauschal je Anwesenheitsstunde? Lohnverrechner bestätigen.

---

## 2. 100 %-Zuschlag — Tages-Flag vs. Zeitfenster-Overlap

**Ist (Code):** `_kvTagZuschlag(...)` bekommt ein **Tages-Flag** `hundert`. Ist es gesetzt
(`_kvIst100`: Sonntag/Feiertag, bzw. Tag mit Nachtanteil), werden **alle** Überstunden dieses
Tages mit 100 % gewertet (`ue100=hundert?restUe:0`), sonst alle mit 50 %.

**Entscheidung:** Bei einem gemischten Tag (teils im 100 %-Fenster, teils nicht) — sollen **nur
die Stunden im Fenster** (z. B. 20–6 Uhr) 100 % bekommen und der Rest 50 % (Overlap-Berechnung),
oder bleibt die tagesweite Alles-oder-nichts-Näherung?

**Beispiel** (Samstag 08:00–22:00, 5,5 Überstunden über Tagesnorm; Nachtfenster ab 20:00):
| Variante | Aufteilung | Zuschlags-Äquiv.-Std |
|---|---|---|
| Ist (Tages-Flag 100 %) | 5,5 × 100 % | **5,50 Std** |
| Fenster-Overlap | 2,0 h (20–22) × 100 % + 3,5 h × 50 % | **3,75 Std** |
| **Delta** | | **1,75 Zuschlags-Std** zugunsten Ist |

Bei einem MA-Stundensatz von z. B. 20 €: **+35 €** pro solchem Tag. Richtung des Delta hängt am
konkreten Tag — die Tages-Näherung ist mal großzügiger (Beispiel), mal knapper (wenn der
Nachtanteil größer ist als der 100 %-Anteil der Näherung).

**Hinweis:** Overlap ist genauer, braucht aber verlässliche von/bis-Zeiten (bei Einträgen ohne
Uhrzeit nicht berechenbar — dort bliebe die Tages-Näherung ohnehin).

---

## 3. „3. Überstunde nach 19 Uhr" → 100 % (eigenes Band)

**Ist (Code):** Der KV-Text ist im Kommentar hinterlegt (`ue100Regeln`: „… ab 3. ÜeStd nach 19 Uhr
— nur höchster Zuschlag (Kumulationssperre)"), die **Umsetzung** kippt aber pauschal über das
Tages-Flag `hundert` (Punkt 2), nicht über ein eigenes „ab der 3. Überstunde nach 19:00"-Band.

**Entscheidung:** Soll dieses Band exakt umgesetzt werden (ab der 3. Überstunde, die nach 19:00
geleistet wird, 100 % — unter Kumulationssperre mit den übrigen 100 %-Tatbeständen)?

**Beispiel** (Werktag, Arbeitsende spät, 4 Überstunden, davon 3 nach 19:00):
| Variante | Wertung | Zuschlags-Äquiv.-Std |
|---|---|---|
| Ist (kein Band, 50 %) | 4 × 50 % | **2,00 Std** |
| Mit Band (3. Üe-Std nach 19 h → ab da 100 %) | 2 × 50 % + 2 × 100 % | **3,00 Std** |
| **Delta** | | **+1,00 Zuschlags-Std/Tag** |

Bei 20 € Stundensatz **+20 €** pro betroffenem Abend. Tritt nur an Tagen mit ≥ 3 Überstunden nach
19:00 auf — vermutlich selten, aber lohnrelevant.

**Hinweis:** Braucht von/bis-Zeiten (welche Überstunde fällt nach 19:00). Kumulationssperre
beachten: an Sonntag/Feiertag ist ohnehin schon 100 % — dann kein zusätzliches Band.

---

## 4. Toter `taggeldNacht`-Knopf (Nächtigungsgeld 62,04 €)

**Ist (Code):** `taggeldNacht: 62.04` steht in `KV_RULES_FALLBACK`, aber `_kvTaggeldTag(...)`
wertet **nur** `taggeldAb6h`/`taggeldAb11h` aus — das Nächtigungsgeld ist **nirgends verdrahtet**
(kein Button, kein Flag, keine Auswertung). Der Wert ist totes Kapital.

**Entscheidung:** Wann gebührt Nächtigungsgeld (auswärtige Übernachtung) und wie soll es erfasst
werden — z. B. ein „Übernachtung"-Häkchen je Tag/Auswärtstag, das 62,04 € auslöst?

**Beispiel** (MA mit 4 Auswärts-Übernachtungen/Monat):
| Variante | Rechnung | €/Monat |
|---|---|---|
| Ist (nicht ausgezahlt über App) | 0 | **0,00 €** |
| Mit Erfassung | 4 × 62,04 | **248,16 €/Monat/MA** |

Das ist der größte Einzel-Delta der vier Punkte — solange es Auswärts-Übernachtungen gibt, fehlt
dieser Betrag aktuell in der App-Auswertung komplett.

**Hinweis:** Klären, ob Nächtigungsgeld überhaupt über die App laufen soll oder rein über den
Lohnverrechner. Falls App: braucht ein Erfassungs-UI (Tag-Flag) + Auswertung in den KV-Reports.

---

## Zusammenfassung der €-Deltas (Beispiel-Annahmen)

| # | Punkt | Delta-Richtung | Beispiel-Delta |
|---|---|---|---|
| 1 | Montagezulage auf alle Std | mehr Auszahlung | +46,20 €/Monat/MA |
| 2 | 100 % Fenster statt Tages-Flag | tagesabhängig | ±~35 €/betroffener Tag |
| 3 | „3. Üe nach 19 h"-Band | mehr Auszahlung | +20 €/betroffener Abend |
| 4 | Nächtigungsgeld verdrahten | mehr Auszahlung | +248 €/Monat/MA (4 Nächte) |

**Alle vier sind lohnrelevant und Rechts-/Produktentscheidungen — nichts davon wird ohne
Sebastians Einzelfreigabe gebaut.** Der Lohnverrechner ist maßgeblich.
