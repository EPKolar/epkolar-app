# JSON-Feld-Konsistenz-Audit (Sebastian-Spec 2026-06-03)

## TEXT_JSON_FIELDS Whitelist (index.html Z1656)

```js
const TEXT_JSON_FIELDS = [
  'perms_override',
  'tank_log',
  'km_log',
  'tags',
  'config',
  'order_items'
];
```

**_mapBody Z1661** (NO-GO Hard-Constraint — nur lesen):
```js
out[sk] = (v !== null && typeof v === 'object' && TEXT_JSON_FIELDS.includes(sk))
  ? JSON.stringify(v)
  : v;
```

## Sebastian's Live-Befund (Chat-Claude)

| Tabelle.Spalte | Speicherform | In Whitelist? | Risiko |
|---|---|---|---|
| `material_orders.positionen` | NATIVE jsonb | nicht nötig (jsonb) | OK |
| `bautagebuch.anwesende` | NATIVE jsonb | nicht nötig (jsonb) | OK |
| `bautagebuch.taetigkeiten` | plain TEXT | nicht nötig (kein Object) | OK |
| `bautagebuch.material` | plain TEXT | nicht nötig (kein Object) | OK |
| **`arbeitsscheine.material`** | STRING(stringified) | **❌ FEHLT** | **Stolperstein** |
| **`arbeitsscheine.fotos`** | STRING(stringified) | **❌ FEHLT** | **Stolperstein** |
| **`checklists.items`** | STRING(stringified) | **❌ FEHLT** | **Stolperstein** |

## Konsequenz

Wenn Code `arbeitsscheine.material` als JS-Array übergibt (`[{art:'...',menge:5}]`):
- `_mapBody`: `TEXT_JSON_FIELDS.includes('material')===false` → **NICHT stringified**
- PostgREST sendet native Array an Postgres
- Wenn DB-Spalte TEXT → Postgres lehnt ab ODER mappt als Array-Literal
- Wenn DB-Spalte jsonb → funktioniert (PostgREST mappt um)

**Sebastian-Befund:** Aktuell ist es "kein akuter Bug" wegen leerer `"[]"`-Defaults — diese sind als String aus früheren Schreibpfaden gespeichert. Bei BEFÜLLTEM Inhalt → Doppelt-Stringified ODER Object-in-Text-Spalte.

## DB-Schema-Frage (Sebastian-Action)

```sql
-- Verifizieren ob TEXT oder jsonb:
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema='public'
  AND (
    (table_name='arbeitsscheine' AND column_name IN ('material','fotos'))
    OR (table_name='checklists' AND column_name='items')
  );
```

**Erwartung Sebastian-Befund:** alle 3 als `text` (nicht `jsonb`) — daher Whitelist-Ergänzung nötig.

## Code-Fix (Sebastian-Freigabe nötig — TEXT_JSON_FIELDS ist Hard-Constraint NO-GO)

Wenn DB-Schema TEXT bestätigt:
```js
const TEXT_JSON_FIELDS = [
  'perms_override',
  'tank_log',
  'km_log',
  'tags',
  'config',
  'order_items',
  // v3.9.99 Sebastian-Spec Add (DB-Schema TEXT für arbeitsscheine.material/fotos + checklists.items):
  'material',  // arbeitsscheine.material — array of {art,menge,einheit,...}
  'fotos',     // arbeitsscheine.fotos — array of {file_path,thumb,uploaded_at}
  'items'      // checklists.items — array of {text,done,photo,note}
];
```

**Alternative:** DB-Migration TEXT → jsonb für die 3 Spalten (saubere Lösung, aber Schema-Change-Risiko).

## Schreibstellen — Grep aller Set-Sites

Pending Sprint 80 — Verifikation aller `material:`/`fotos:`/`items:`-Schreibstellen mit Native-Array vs. String.

## Empfehlung

**Sofort:**
1. Sebastian-DB-Check (SQL oben) — bestätigen ob TEXT oder jsonb
2. Bei TEXT: Code-Fix `TEXT_JSON_FIELDS`-Erweiterung (3 Strings) — minimal, additiv, sicher
3. Test: AS mit echtem material-Array speichern → reload → Array-Wert verifizieren

**Längerfristig:** DB-Migration TEXT → jsonb für die 3 Spalten + Code-Cleanup von `_jp`-Reverse-Mapping (parsing layer entfallen wenn jsonb).
