# Entfernungszulage Etappe 3 — €-Beispiel (Freigabe-Vorlage, NICHT gebaut)

**Stand 20.07.2026.** Etappe 3 = die **lohnrelevante** Umstellung: die Entfernungszulage-Rechnung
soll künftig die **manuell geflaggten Tage** (Kalender-Klick, Etappe 4 → Tabelle `entfernungszulage_tage`)
verrechnen, statt **automatisch alle Tage mit Anwesenheit > 6 h** (aus `time_entries`). Das ändert die
Menge im Lohnverrechner-CSV → **nicht autonom, Sebastian gibt frei.**

Satz unverändert: **11,71 €/Tag** (Lohnzettel LA 2740). Kein 4-Tage-Deckel (Freitag zählt, wenn > 6 h).

## Wie es HEUTE rechnet (automatisch)
`_kvZulagenMonat` zählt jeden Tag mit Tages-Anwesenheit (Summe `time_entries`) **> 6 h** automatisch als
Entfernungszulage-Tag. Keine Vergabe, kein Klick.

## Gegenrechnung — Riedmann, Juli 2026 (read-only, echte Daten)
- Tage mit Anwesenheit **> 6 h: 8** · Tage > 11 h: 0 · Monatsstunden: 80,8 h.

| Szenario | Tage | Rechnung | Summe |
|---|---|---|---|
| **Heute (automatisch > 6 h)** | 8 | 8 × 11,71 € | **93,68 €** |
| Nach Etappe 3, Büro flaggt **dieselben** 8 Tage | 8 | 8 × 11,71 € | 93,68 € (identisch) |
| Nach Etappe 3, Büro flaggt z. B. nur **6** echte Auswärtstage | 6 | 6 × 11,71 € | 70,26 € (**−23,42 €**) |
| Nach Etappe 3, Büro flaggt **10** Tage (inkl. < 6 h) | 10 | 10 × 11,71 € | 117,10 € (**+23,42 €**) |

## Der lohnrelevante Kern
Die **Kontrolle über die Menge** wechselt von „die App zählt automatisch **alle** > 6-h-Tage" zu „das Büro
entscheidet **pro Tag** per Klick". Effekt auf die abgerechnete Summe:
- **Identisch**, wenn das Büro exakt die automatischen > 6-h-Tage flaggt.
- **Niedriger**, wenn nicht jeder > 6-h-Tag als Auswärts-/Entfernungstag gilt (der wahrscheinliche Regelfall —
  ein langer Werkstatttag ist > 6 h, aber keine Entfernung).
- **Höher**, wenn das Büro Tage < 6 h flaggt.

**Frage an Sebastian:** Soll die Umstellung (a) so gebaut werden — **reine manuelle Menge** (Büro klickt,
keine automatische > 6-h-Vorbelegung)? Oder (b) mit **> 6-h-Vorbelegung** (App schlägt die > 6-h-Tage vor,
Büro korrigiert)? Und: greift die > 6-h-Schwelle beim manuellen Flaggen noch, oder darf das Büro jeden Tag
flaggen (dann ist „> 6 h" nur noch ein Vorschlag, keine harte Regel)?

**Bis zur Freigabe:** die Rechnung bleibt automatisch (> 6 h), `test_rechnung_unberuehrt` bleibt grün.
Der Kalender (Etappe 4) schreibt bereits Flags in `entfernungszulage_tage`, die aber **noch nicht verrechnet**
werden — er ist bis Etappe 3 reine Vergabe-Vorbereitung/Anzeige.
