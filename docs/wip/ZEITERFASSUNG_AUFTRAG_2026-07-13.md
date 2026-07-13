# GEPARKT: Zeiterfassung — Sonntag bedingt rendern

**Status:** aufgehoben, nicht verworfen. Am 13.07.2026 beauftragt und noch am selben Tag
zurückgestellt (keine Zeit). **Keine einzige Code-Zeile dieses Auftrags wurde umgesetzt.**
Diese Datei ist der vollständige Auftragstext plus Kontext, damit die Wiederaufnahme nicht
bei null beginnt.

## Produktentscheid (Sebastian, 13.07.2026)

Sonntag ist kein Arbeitstag. Die Sonntags-Karte in der Zeiterfassung stört optisch — sie
bricht als einsame zweite Zeile um. Sie soll deshalb nur noch erscheinen, **wenn es für
diesen Sonntag tatsächlich Einträge gibt**.

**Die Einschränkung ist der wichtigste Teil des Auftrags:** Der Schutz aus **v3.9.546**
(Sonntags-Einträge dürfen NIE wieder unsichtbar werden) bleibt vollständig bestehen. Es geht
ausschließlich um die **Anzeige**, nicht um die Datenlogik. Wer das verwechselt, baut den Bug
von v3.9.546 wieder ein.

## Umsetzung (geplant, nicht gebaut)

Muster ist `exportWochenStz` aus **v3.9.661** — dort gibt es bereits genau diese Regel
("Sonntag-Block nur wenn Stunden"). Nicht neu erfinden, von dort übernehmen.

1. **Wochen-Karten in `ZeiterfassungView`:** Die So-Karte nur rendern, wenn für den
   ISO-Sonntag (`isoDate(6)`) Einträge existieren.
   - ohne Einträge → 6 Karten Mo–Sa, eine saubere Reihe
   - mit Einträgen → So-Karte erscheint mit **Warnakzent** (oranger Rand + Tooltip
     „Sonntags-Einträge vorhanden"). Sie soll als *Ausnahme* lesbar sein, nicht als Normalfall.
2. **Summen-Leiste unten:** So-Spalte analog bedingt rendern. **`Σ Woche` zählt den Sonntag
   IMMER mit** — der Datenpfad bleibt unangetastet, nur der Render ist bedingt.
3. **Tabu:** Timer und alle Schreibpfade nicht anfassen. `DAYS` bleibt intern **7-tägig**.
   Kein Rückbau der v3.9.546-Datenlogik — ausschließlich Anzeige.
4. **Regression-Test (Pflicht):**
   - (a) Woche ohne Sonntags-Einträge → 6 Karten
   - (b) Woche mit Sonntags-Eintrag → 7 Karten **und** der Eintrag steckt in der Summe
   - Die bestehenden v546- und v661-Tests dürfen nicht brechen.
5. **Gates wie üblich:** `node_check`, Bracket-Baseline `() -1`, `_check_version.js`, voller
   pytest-Lauf grün. Versions-Triple hochzählen.
6. **Commit-Message (vorgesehen):**
   `"Zeiterfassung — Sonntag nur bei vorhandenen Einträgen sichtbar (Optik Mo–Sa, v546-Schutz bleibt)"`

## Offene Punkte für die Wiederaufnahme

- **Warnakzent-Semantik klären:** Soll der orange Rand auch dann erscheinen, wenn der
  Sonntags-Eintrag legitim ist (bezahlter Sonntagsdienst)? Aktuell ist „Ausnahme" gemeint —
  das ist eine Anzeige-Entscheidung, die Sebastian bestätigen sollte.
- **Konsistenz-Frage:** Die Wochenplanung (Dispo-Grid + Kiosk) ist bis heute **6-tägig Mo–Sa**
  und kann Sonntag gar nicht planen, während Zeiterfassung/BWB 7-tägig sind. Dieser Auftrag
  macht die Zeiterfassung optisch 6-tägig — die Frage „ist Sonntag planbar oder nicht?"
  bleibt aber produktseitig offen und betrifft mehrere Views. Siehe den offenen Punkt aus der
  Bug-Hunt-Welle 3 (v3.9.666/667).

## Wiederaufnahme

Arbeitsklon `C:\repos\epkolar-app`. Einstieg über `grep -n "exportWochenStz" index.html` —
dort steht die fertige Regel, die hier gespiegelt werden soll.
