# HANDOFF v3.5.11 — OFFA 1:1 Status + Auftragstyp + Fixes

## Version
- SW_VER: `epkolar-v3.5.11`
- APP_VERSION: `3.5.11-supabase`
- Zeilen: ~11311
- Bracket-Baseline: `() delta=-2`, `{} delta=0`, `[] delta=0` ✅

## Was in v3.5.11 neu ist

### 1. OFFA 1:1 Status-System (8 Status)
| OFFA ID | EPKolar Key | Label |
|---------|-------------|-------|
| 0 | aufgenommen | 📋 aufgenommen |
| 1 | freigegeben | ✅ freigegeben |
| 2 | aufgeschoben | ⏸️ aufgeschoben |
| 3 | in_bearbeitung | 🔧 in Bearbeitung |
| 5 | erledigt | 🔵 erledigt |
| 10 | abgerechnet | 💰 abgerechnet |
| 15 | bar_bezahlt | 💵 bar bezahlt |
| 20 | storniert | ❌ storniert |

WICHTIG: 2=aufgeschoben, 3=in_bearbeitung (bestätigt durch OFFA-Screenshots)

### 2. OFFA 1:1 Auftragstyp (7 Typen)
kein(0), stoerung(1), lieferung(2), reparatur(3), montage(4), mangelbehebung(5), garantie(6)

### 3. Auto-Sync (v3.5.10)
- Initial-Sync 3s nach Öffnen Arbeitsscheine
- Auto-Sync alle 5min (silent)
- Nur geänderte Scheine = PATCH (nicht alle 41)

### 4. Sachbearbeiter-Mapping
- TECHNIK → GÜNTHER
- WOLFGANG → SCHMID

### 5. KPI-Klick → Auto-Filter
- Dashboard "Scheine offen" → navigiert zu Arbeitsscheine mit Filter "offen_bearb"
- Arbeitsscheine KPIs → setzen Filter direkt
- window.__asFilter Mechanismus für Cross-View Filter
- Dropdown hat Gruppenoptionen: "Offen (alle)" + "Fertig (alle)"

### 6. Nummer-Farbe
- #8b5cf6 (violett) → #4ade80 (grün, gut lesbar)

### 7. Legacy-Migration
- _mapArbeitsschein: "offen"→"aufgenommen", "service"→"kein", "wartung"→"reparatur"
- AS_GRP_OFFEN / AS_GRP_FERTIG für Gruppenfilter
- JUPROWA_STATUS_REVERSE + JUPROWA_ART_REVERSE für Phase 2

## Supabase (AUF SUPABASE AUSGEFÜHRT ✅)
- scheinstatus: offen→aufgenommen (25 Zeilen)
- scheinstatus: aufgeschoben→in_bearbeitung (22 Zeilen — Fix wegen falschem 2↔3 Mapping)
- scheinart: service→kein (21 Zeilen)
- sachbearbeiter: TECHNIK→GÜNTHER
- sachbearbeiter: WOLFGANG→SCHMID

## DB-Stand
- 41 Arbeitsscheine: in_bearbeitung:22, abgerechnet:14, storniert:2, aufgenommen:2, freigegeben:1

## Bekannte Einschränkungen / Next Steps
- Juprowa API liefert KEIN Sachbearbeiter-Feld → SB nur über OFFA PDF-Import oder manuell
- PASSPORT kann ablaufen → Admin-UI zum Erneuern fehlt
- Phase 2 (EPKolar → Juprowa bidirektional) steht an
- Worker-Mapping: Nur 3 von 10+ Juprowa-Monteuren gemappt
