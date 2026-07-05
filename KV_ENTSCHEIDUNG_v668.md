# KV-Metallgewerbe — offene Rechen-Entscheidungen (Stand v668/670)

**Was dieses Dokument ist:** Entscheidungsvorlage zu den offenen Berechnungsfragen der KV-Metallgewerbe-Auswertung in der EPKolar-App. Pro Punkt: KV-Grundlage (soweit im Repo belegbar), was der Code **heute tatsächlich rechnet** (mit Funktion + `index.html:<Zeile>`), empfohlene Rechenregel als Pseudocode, durchgerechnete Zahlenbeispiele (IST vs. Vorschlag, mit €-Delta/Tag) und Empfehlung.

**Rahmenbedingungen:**
1. **Reine Anspruchs-/Info-Auswertung, keine Lohnverrechnung.** Beide Report-Komponenten (`KVZuschlagReport`, `KVZulagenReport`) tragen „Lohnverrechner maßgeblich — KEINE automatische Verbuchung".
2. **Werte-Quelle:** `KV_RULES_FALLBACK` (`index.html:2078–2088`), `stand:'KV Metallgewerbe 1.1.2026'`. Editierbar über `system_config.kv_rules`.
3. **Kein Ort-/Tätigkeitsfeld in `time_entries`.** Felder: `id, p/pid, w/worker, date, hours/stunden, task/taetigkeit` (Freitext), `gw/gewerk` (konstant `"elektro"`), `von, bis, pause, bemerkung, arbeitsschein_id` (`index.html:6327`). **Kein** Feld Baustelle/Werkstatt/Fahrt; `project.type` = Gewerk, nicht Ort; `fahrzeit` liegt auf `arbeitsscheine`, nicht auf `time_entries`.
4. **Der Zuschlag-Report gibt keine €, nur Zuschlags-Äquivalent-Stunden aus** (kein Stundenlohn im Repo). Für die €-Illustration in Punkt 2/3 wird **20,00 €/h angenommen (NICHT aus dem Repo)**; die harte Zahl ist die Zuschlag-Äquivalent-Stunden-Differenz.

**Kanon-Beispiel:** Monteur, **Montag**, gestempelt 07:00–19:30, Pause 0,5 h → gespeicherte `hours` = 12,0. Tagesnorm Mo = 8,5 → über Norm 3,5 h; Mehrarbeit 1,5 h; Rest-Ü 2,0 h.

---

## ✅ UPDATE — Sebastian-Entscheidungen (05.07.2026)

- **Punkt 1 (Montagezulage): ENTSCHIEDEN → manuelle Vergabe durch das Büro.** Keine Auto-Erkennung Baustelle/Werkstatt/Fahrt (das Datenmodell kann es nicht, siehe Analyse unten). Umsetzungs-Spezifikation + offene DB-Frage im Abschnitt **„Umsetzung Montagezulage (manuell)"** am Ende.
- **Punkt 2/3/4:** noch offen — Freigabe pro Punkt erbeten (Format „2A, 3 wie vorgeschlagen, 4 raus"). Punkte 2 & 3 ändern **lohnrelevante** Zuschlagsstunden und sind **nicht** eindeutig aus dem Repo/KV_RULES ableitbar (Quelle fehlt) → **kein autonomer Code-Change**, erst nach Freigabe/KV-Original.

---

### Punkt 1 — Montagezulage (1,155 €/h): auf welche Stunden?

- **KV-Text (Quelle):** **Quelle fehlt** — vollständiger KV-Paragraphentext nicht im Repo. Belegbar nur `montagezulageStd:1.155` (`index.html:2086`), Stand „KV Metallgewerbe 1.1.2026" (2027-Wert Kommentar 1,178).
- **Was der Code AKTUELL rechnet:** `_kvMontagezulage(baustellenStd, rules) = baustellenStd × 1,155` (`index.html:2157`). `baustellenStd` = **Summe ALLER** gebuchten Stunden des Monats (`byW[wid].baustelle += hrs` je Eintrag, ohne Ortsfilter, `index.html:8931–8933`). Die Spalte heißt „Baustellen-Std", enthält faktisch **alle** Logstunden. Varianten A/B/C sind heute **nicht unterscheidbar** (kein Ortsfeld).
- **Beispiel (Kanon Mo, hours 12,0; Annahme real 10,0 Baustelle + 2,0 Werkstatt):** IST (alle Std) = 12,0×1,155 = **13,86 €** · Vorschlag A (nur Baustelle) = 10,0×1,155 = **11,55 €** → **Delta −2,31 €/Tag** (nur mit neuem Ortsfeld/manueller Vergabe realisierbar).
- **Empfehlung / Entscheidung:** → **manuelle Vergabe** (Sebastian, s. u.). Bis Umsetzung: Spalte ehrlich „Log-Std (alle)" nennen.

### Punkt 2 — 100%-Zuschlag: Tages-Flag vs. Fenster-Overlap

- **KV-Text (Quelle):** **Quelle fehlt.** Belegbar nur `ue100Regeln:'Nacht 20-6, Sonntag, Feiertag, ab 3.UeStd nach 19 Uhr — nur hoechster Zuschlag (Kumulationssperre)'` (`index.html:2083`).
- **Was der Code AKTUELL rechnet:** `_kvHundert100(dow,feiertag,von,bis,ueberStd)` liefert ein **Tages-Flag** (`index.html:2132`). `von`/`bis` = früheste `von`/späteste `bis` des Tages; `nacht = (von<06:00) || (bis>20:00) || (bis<von)`. Ist das Flag true, werden **alle** Rest-Überstunden 100 % — unabhängig davon, wie viel tatsächlich im 20–06-Fenster lag.
- **Empfohlene Rechenregel (Pseudocode):** je Rest-Ü-Stunde prüfen, ob ihr Zeitfenster in 20:00–06:00 (bzw. So/Feiertag) liegt → 100 %, sonst 50 %. (Braucht echte Zeitscheiben; mit nur einem `von/bis` pro Tag als Rand-Overlap näherbar.)
- **Beispiel A — Ende nach 20:00 (Mo 08:00–21:00, Pause 0,5 → hours 12,5):** über Norm 4,0; Mehr 1,5; Rest-Ü 2,5; physisch im Nachtfenster nur 20:00–21:00 = 1,0 h.
  - IST (Tages-Flag): Ü50 0,0 / Ü100 2,5 → Zuschlag-Äq. = 1,5·0,5 + 2,5·1,0 = **3,25 h**
  - Vorschlag (Overlap): Ü50 1,5 / Ü100 1,0 → Zuschlag-Äq. = 0,75 + 0,75 + 1,0 = **2,50 h**
  - **Delta: 0,75 Äq.-h/Tag ≈ 15,00 €/Tag zu viel im IST (@20 €/h).**
- **Beispiel B — Frühstart flaggt den ganzen Tag (Mo 04:00–16:00, Pause 0,5 → hours 11,5):** `von 04:00<06:00` → Flag true, obwohl die Rest-Ü mittags (≈14:30–16:00) liegen. IST Zuschlag-Äq. **2,25 h** vs. Vorschlag **1,50 h** → **≈ 15,00 €/Tag zu viel im IST.**
- **Empfehlung:** Fenster-Overlap ist inhaltlich korrekt; das Tages-Flag überzeichnet. Aber sauber nur mit Zeitscheiben → Näherung labeln. **Freigabe + KV-Bestätigung nötig.**

### Punkt 3 — „3. Überstunde nach 19 Uhr": Verhältnis zum Mehrarbeits-Band (38,5→40 h)

- **KV-Text (Quelle):** **Quelle fehlt.** Belegbar nur Teilstring `'… ab 3.UeStd nach 19 Uhr …'` (`index.html:2083`). Ob die „3. Überstunde" das Mehrarbeits-Band (38,5→40) mitzählt, ist **nicht** ableitbar.
- **Was der Code AKTUELL rechnet:** `if(bis>19:00 && ueberStd>=3) return true` mit `ueberStd = hours − Tagesnorm` (`index.html:2139/20402`) — also **inkl.** des 1,5-h-Mehrarbeits-Bandes. Trigger schon ab `hours ≥ 11,5`.
- **Empfohlene Rechenregel:** `restUe = max(0, hours − Tagesnorm − 1,5)` (echte Ü ohne Mehrarbeit); Trigger `bis>19:00 && restUe>=3` → erst ab `hours ≥ 13,0`.
- **Beispiel A — Kanon (Mo hours 12,0, Ende 19:30):** IST triggert (3,5≥3) → Ü100 2,0 → Zuschlag-Äq. **2,75 h**. Vorschlag triggert nicht (2,0<3) → Ü50 2,0 → **1,75 h**. **Delta ≈ 1,0 Äq.-h/Tag ≈ 20,00 €/Tag.**
- **Beispiel B — genug echte Ü (Mo 06:00–19:50, Pause 0:20 → hours 13,5):** beide triggern → identisch **4,25 h** → **Delta 0**. Differenz nur im Band `hours ∈ [11,5; 13,0)`.
- **Empfehlung:** arbeitsrechtlich ist Mehrarbeit keine Überstunde → `restUe≥3` konsistenter; **Entscheidung nur mit KV-Original.**

### Punkt 4 — `taggeldNacht` (62,04 €): toter Konfig-Knopf

- **KV-Text (Quelle):** **Quelle fehlt.** Belegbar nur `taggeldNacht:62.04` (`index.html:2085`).
- **Was der Code AKTUELL rechnet:** **Nichts.** Von keiner Rechenfunktion gelesen; `_kvTaggeldTag` nutzt nur `taggeldAb6h`/`taggeldAb11h` (`index.html:2148`). Einzige weitere Fundstelle: das Konfig-UI-Feld (`index.html:7607`). Anbindung bräuchte Nächtigungs-Info, die `time_entries` nicht hat.
- **Empfehlung:** **Entfernen/deaktivieren** (bzw. „ohne Funktion — erfordert Nächtigungsdaten" labeln). Ein editierbarer Wert, der nirgends einfließt, suggeriert eine nicht existente Berechnung.

---

## Kompakt-Tabelle

| Punkt | Ist rechnet | Vorschlag rechnet | Delta €/Tag | Empfehlung |
|---|---|---|---|---|
| 1 Montagezulage | 1,155 € × **alle** Log-Std | manuelle Vergabe je MA-Tag × Satz | Bsp −2,31 € | **ENTSCHIEDEN: manuell** (s. u.) |
| 2 100% Nacht | Tages-Flag → alle Rest-Ü 100 % | nur Rest-Ü im 20–6-Fenster 100 % | ≈ +15 €/Tag zu viel im Ist | Overlap (Freigabe+KV nötig) |
| 3 3.Ü nach 19h | `ueber≥3` inkl. Mehrarbeit (ab 11,5 h) | `restUe≥3` echte Ü (ab 13,0 h) | Bsp A ≈ +20 €/Tag; sonst 0 | KV-Original nötig; `restUe≥3` konsistenter |
| 4 taggeldNacht | **nichts** (toter Knopf) | entfernen / anbinden | +32,04 €/Nacht *falls* angebunden | Entfernen/deaktivieren |

---

## Umsetzung Montagezulage (manuell) — Spezifikation + offene DB-Frage

**Sebastian-Entscheid:** Büro vergibt die Montagezulage **manuell pro Mitarbeiter-Tag**. App rechnet: `zulagefähige Tages-Std (ohne Pause) × Satz(Jahr des Tages)`.

**Storage-frei umsetzbar (kein DDL) — kann sofort gebaut werden:**
1. **KV_RULES-Erweiterung:** `montagezulage: { 2026: 1.155, 2027: 1.178 }`, Satz-Auswahl nach **Jahr des Eintrags-Datums** (nicht heutiges Datum). Pure Function `_kvMontagezulageSatz(datum, rules)` + Test (Jahreswechsel 2026/2027).
2. **Editierbare Sätze:** Konfig-UI analog Pausen-Konfiguration (`system_config`, Gate `isWAdm`). Overrides schlagen KV_RULES-Defaults.
3. **Berechnung:** Pure Function `_kvMontagezulageTag(stundenOhnePause, datum, satzQuelle, flag)` → `flag ? std × satz(jahr) : 0`. Tests: Jahreswechsel, Flag an/aus, 0h-Tag.

**⛔ STOPP — braucht deine DB-Entscheidung (dieser Lauf ist TABU für DB-Writes/DDL):**
- **Speicherort des Tages-Flags** „Montagezulage ja/nein je Mitarbeiter-Tag": existiert **nicht** in der DB. Optionen:
  - **(B, empfohlen) Neue Tabelle** `montagezulage_tage(worker_id text, datum date, aktiv bool, PRIMARY KEY(worker_id,datum))` + RLS `is_staff()` (Büro/PL schreiben, Monteur read-only). Sauber pro Tag, kollidiert nicht mit `time_entries`-Mehrfachbuchungen.
  - (A) Neue Spalte `montagezulage bool` auf `time_entries` — **nicht empfohlen** (Flag ist per **Tag**, nicht per Eintrag; ein Tag hat oft mehrere Einträge → Mehrdeutigkeit).
  - (C) `system_config`-JSON-Blob — hackig, nicht empfohlen (kein sauberes Query pro Tag).
- **Gültigkeitsdatum der Satz-Overrides (nicht rückwirkend):** Es gibt im Repo **kein** bestehendes „effective-date"-Muster (Taggeld-Werte sind flach in KV_RULES, keine Historisierung). → **neues Muster nötig**; Vorschlag: Override-Objekt `{satz, gueltig_ab}` in `system_config`, Berechnung wählt den Satz mit größtem `gueltig_ab ≤ Eintrags-Datum`, sonst KV_RULES-Jahreswert. Bitte bestätigen.

**Rollen-Gate (per Grep bestätigt):** Kiosk/Rollen nutzen `curUser.role` als **Display-String** (`"Backoffice"`, „Geschäftsführer", „Monteur"), nicht Kurzcode. Vergabe-UI sichtbar/setzbar für Büro/PL, Monteur read-only in der Tagesansicht.

**Anzeige:** dort wo Taggeld heute erscheint (`KVZulagenReport` + CSV-Export für den Lohnverrechner) — gleiche Stellen, per Grep verifiziert.

**→ Sobald du (B) + das Gültigkeitsdatum-Muster freigibst, baue ich das Storage-freie (KV_RULES-Jahr + Satz-Konfig + Pure-Function + Tests) und liefere das DDL als Migrations-Vorschlag (kein Auto-Apply).**
