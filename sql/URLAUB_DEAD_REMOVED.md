# Dead-Code Removal Log · Tag 5 · 2026-05-02

**Methodik pro Kandidat:** Triple-grep (`\bNAME\b`, `NAME.`, Import) — bei 0 externen Treffern → löschen.
**Verifikation:** Nach jeder Löschung syntax + brackets + pytest grün.

---

## Kandidat 1 · `SCHEINART_C` (L403)

**Code:** `const SCHEINART_C=Object.freeze({STOERUNG:'stoerung', ...});`

**Triple-Grep:**
- `\bSCHEINART_C\b`: 1 Treffer (Definition L403)
- `SCHEINART_C\.`: 0 Treffer
- Import/Export: nicht vorhanden (single-file App)

**Status:** Sicher löschbar. Frozen-Enum, nie konsumiert. Ersetzt durch direkten String-Zugriff (`'stoerung'` etc.) im gesamten Code.

**Aktion:** L403 (1 Zeile) wird entfernt.

---

## Kandidat 2 · `SCHEINSTATUS_C` (L402)

**Code:** `const SCHEINSTATUS_C=Object.freeze({AUFGENOMMEN:'aufgenommen', ...});`

**Triple-Grep:**
- `\bSCHEINSTATUS_C\b`: 1 Treffer (Definition L402)
- `SCHEINSTATUS_C\.`: 0 Treffer
- Import/Export: nicht vorhanden

**Status:** Sicher löschbar (analog SCHEINART_C).

**Aktion:** L402 (1 Zeile) wird entfernt.

---

## Kandidat 3 · `ESKALATION_RULES` (L2820-2823)

**Code:**
```js
const ESKALATION_RULES={
  as_new:{hours:24,urgentHours:4,targetRoles:["admin","projektleiter"],msg:"seit {h}h unbearbeitet"},
  material_order:{hours:8,urgentHours:2,targetRoles:["admin"],msg:"seit {h}h nicht bearbeitet"},
};
```

**Triple-Grep:**
- `\bESKALATION_RULES\b`: 1 Treffer (Definition L2820)
- `ESKALATION_RULES\.`: 0 Treffer

**Status:** Sicher löschbar. Stub für Auto-Escalation-Feature, das nie ausgeliefert wurde. NOTIF_TYPES (L2748+L2759) referenziert `as_eskalation`/`material_eskalation` als Notification-Type-Keys, ist aber unabhängig.

**Aktion:** L2819-2823 (Comment + 4 Zeilen Body) wird entfernt.

---

## Kandidat 4 · `MATERIAL_UNITS` (L9403-9406)

**Code:**
```js
const MATERIAL_UNITS=[
  {id:"stk",l:"Stück"},{id:"m",l:"Meter"},{id:"kg",l:"Kilogramm"},{id:"liter",l:"Liter"},
  {id:"rolle",l:"Rolle"},{id:"packung",l:"Packung"},{id:"pauschal",l:"Pauschal"}
];
```

**Triple-Grep:**
- `\bMATERIAL_UNITS\b`: 1 Treffer (Definition L9403)
- `MATERIAL_UNITS\.`: 0 Treffer

**Status:** Sicher löschbar. Units-Liste, nie in einem Dropdown verdrahtet. UI nutzt direkt freie Text-Eingabe für Einheiten.

**Aktion:** L9403-9406 (4 Zeilen) wird entfernt.

---

## Erwarteter Effekt

- **4 Konstanten weg** = ~10 Zeilen weniger im Code.
- **Test-Anpassung:** `tests/test_dead_code_candidates*.py` prüft auf "≥7" Kandidaten. Wir hatten in v3.8.37 bereits 3 gelöscht (INIT_AS, INIT_WZ, LazyImg), daher 4 verbleibend. Nach dieser Aktion: 0 Kandidaten.
- **Test-Anpassung Domain-Constants:** Falls `test_domain_constants.py` MATERIAL_UNITS testet → entfernen. (Check: enthält nur AS_PRIO/AS_ART/AS_VERRECH/JUPROWA_*/WZ_STATUS — kein MATERIAL_UNITS-Test, OK.)
- **Bracket-Baseline:** Sollte stabil bleiben (Object.freeze + const Array sind balanced).

## Risiko

Niedrig. Pure-Doku/Const-Removal. Keine Logic-Pfade berührt.
