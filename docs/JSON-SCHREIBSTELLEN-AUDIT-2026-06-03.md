# JSON-Schreibstellen-Audit — Sprint 80 (2026-06-03)

**Folge-Audit zu** `docs/JSON-FELD-AUDIT-2026-06-03.md` (Whitelist-Befund).
**Scope:** Schreibstellen fuer `material` / `fotos` / `items` — fehlen in TEXT_JSON_FIELDS-Whitelist (Z1656).

## Recap: Whitelist + _mapBody

```js
// index.html Z1656
const TEXT_JSON_FIELDS=['perms_override','tank_log','km_log','tags','config','order_items'];

// Z1661 _mapBody
out[sk]=(v!==null&&typeof v==='object'&&TEXT_JSON_FIELDS.includes(sk))?JSON.stringify(v):v;
```

**Generischer CRUD-Pfad** (Z2105): `const mapped=_mapBody(body||{});` — JEDER `SQ.push({...,body})` der Generic-Route durchlaeuft `_mapBody`.

## Schreibstellen-Tabelle

| # | Zeile | Tabelle.Feld | Pfad | Typ vor _mapBody | Whitelist greift? | Risiko |
|---|---|---|---|---|---|---|
| 1 | **6003** | `arbeitsscheine.material` | `SQ.push({url:editId?"/api/arbeitsscheine/"+editId:"/api/arbeitsscheine",method:editId?"PUT":"POST",body:_finalForm})` | **Array** `[{name,stueck,artikelNr,bemerkung}]` (wenn UI Material-Tabelle befuellt) ODER **undefined** (defAs() hat kein material-Feld) | NEIN — `'material'` fehlt in Whitelist | **HIGH** wenn UI befuellt — Object durchlaeuft `JSON.stringify(data)` von _sbPost (Z1778) -> PostgREST mappt Array->Array-Literal in TEXT-Spalte ODER stringified-doppelt |
| 2 | **6003** | `arbeitsscheine.fotos` | wie #1 (`body:_finalForm`) | **Array** `[{file_path,...}]` ODER **undefined** | NEIN — `'fotos'` fehlt | **HIGH** wie #1 |
| 3 | **6055/6056** | `arbeitsscheine.material/fotos` (OFFA-Import) | `SQ.push({url:"/api/arbeitsscheine/"+r._existId,method:"PUT",body:as})` und POST `body:newAs` | **undefined** — OFFA-AS-Builder (Z6054) liefert KEIN material/fotos-Feld | N/A (Feld fehlt) | **LOW** — undef wird in _mapBody uebersprungen |
| 4 | **6005** | `arbeitsscheine` DELETE | `SQ.push({url:"/api/arbeitsscheine/"+id,method:"DELETE"})` | — | — | **OK** (kein body) |
| 5 | **6006/6007** | `arbeitsscheine` (verschieben/updAs) | `body:{termin_bestaetigt:d,...}` ODER `body:updates` | Updates enthalten i.d.R. **kein** material/fotos | N/A | **LOW** — falls Caller updAs(id,{material:[...]}) rufen wuerde -> Bug. Aktuell kein solcher Caller im Code. |
| 6 | **10056** | `checklists.items` | `SQ.push({url:"/api/checklists",method:"POST",body:{id:cl.id,project_id:p.id,name:cl.name}})` | **NICHT uebergeben** — body enthaelt nur `id/project_id/name` | N/A | **LOW (separat P2)** — items werden NIE per /api/checklists synchronisiert. **Konsequenz:** Items leben nur in `forms.checklisten` (lokaler State + ODB), Server-Spalte bleibt leer/null. **Datenverlust beim Logout/Cross-Device-Switch.** |
| 7 | **12176** | `bautagebuch.material` | `SQ.push({url:"/api/bautagebuch",method:"POST",body:{...,material:entry.material,...}})` | **String** (`form.material.trim()` aus `<textarea>`, defForm.material=`""`, Z12127/12173/12272) | N/A (kein Object) | **OK** — Bautagebuch.material ist plain-text (Sebastian-Befund) |
| 8 | **12179** | `bautagebuch.material` (PUT) | wie #7 | **String** | N/A | **OK** |
| 9 | **17968** | `werkzeuge.serviceheft` | `_pushWzSh` schreibt `{serviceheft:wz.serviceheft||[]}` (debounced PUT) | **Array** | NEIN — `'serviceheft'` fehlt in Whitelist ebenfalls | **HIGH** — siehe Zusatzbefund unten |
| 10 | **18072** | `werkzeuge.fotos` + `serviceheft` (PUT full form) | `SQ.push({url:"/api/werkzeuge/"+editId,method:"PUT",body:form})` mit `form={...,fotos:[...],serviceheft:[...]}` | **Array** fuer beide | NEIN — beide fehlen | **HIGH** |
| 11 | **18073** | `werkzeuge.fotos` + `serviceheft` (POST new) | `SQ.push({url:"/api/werkzeuge",method:"POST",body:form})` | Array | NEIN | **HIGH** wie #10 |
| 12 | **9949/9996** | `forms.data` (FRegie etc.) | `body:{id,form_type,project_id,data:entry}` mit `entry.material:[...]`, `entry.personal:[...]` | **Object/Array** im jsonb-Container `data` | OK (Annahme: `forms.data` ist jsonb) | **LOW (TBD Sebastian-Schema-Check)** — wenn `forms.data` jsonb -> PostgREST nimmt Object nativ; wenn TEXT -> benoetigt `'data'` in Whitelist. |

### Zusatzbefund: `werkzeuge.fotos` + `werkzeuge.serviceheft`

`_mapWerkzeug` (Z1687) liest mit `_jp(w.fotos)`, `_jp(w.serviceheft)` — Pattern wie bei AS: Spalten werden als JSON-strings vom Server erwartet. Die Schreibstellen Z18072/18073 senden aber **native Arrays**. Whitelist fehlt fuer `'fotos'` UND `'serviceheft'`.

## Lesestellen-Verifikation

| Ort | Funktion | Feld | Robust gegen jsonb? |
|---|---|---|---|
| Z1667 | `_jp(s)` | universal | **Ja** — `if(typeof s==='string'){try{parse}catch{return[]}}return s;` — passt String UND Array-Direct durch |
| Z1718 | `_mapArbeitsschein` | `material:_jp(a.material), fotos:_jp(a.fotos)` | **Ja** |
| Z1687 | `_mapWerkzeug` | `serviceheft:_jp, fotos:_jp` | **Ja** |
| Z4064/Z4736 | Checklist-Load | `items:_jp(c.items)` | **Ja** |
| Z12146 | Bautagebuch-Load | `material:d.material||""` | TEXT-pass-through (kein _jp) — **erwartet String** |

**Edge-Case bestaetigt:** Wenn DB-Spalte -> jsonb migriert -> Server liefert nativ Array -> `_jp` laesst es durch (kein Bug). Lesestellen sind also forward-kompatibel zur DB-Migration.

## DB-Schema-Check (Sebastian-Action)

```sql
-- Verifizieren ob TEXT oder jsonb fuer ALLE betroffenen Spalten:
SELECT table_name, column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_schema='public'
  AND (
    (table_name='arbeitsscheine' AND column_name IN ('material','fotos'))
    OR (table_name='checklists'    AND column_name='items')
    OR (table_name='werkzeuge'     AND column_name IN ('fotos','serviceheft'))
    OR (table_name='forms'         AND column_name='data')
  )
ORDER BY table_name, column_name;
```

**Erwartung Sebastian-Befund (aus JSON-FELD-AUDIT-2026-06-03):**
- arbeitsscheine.material/fotos = `text`
- checklists.items = `text`
- werkzeuge.fotos/serviceheft = (vermutlich text — _jp-Pattern identisch)
- forms.data = `jsonb` (Vermutung — neueres Feature)

## Empfehlung — 3 Optionen

### Option A) `TEXT_JSON_FIELDS` minimal ergaenzen (PREFERRED)

```js
const TEXT_JSON_FIELDS=[
  'perms_override','tank_log','km_log','tags','config','order_items',
  // v3.9.99 Sprint-80 Add — DB-Schema TEXT, Native-Array-Writes (siehe SCHREIBSTELLEN-AUDIT-2026-06-03):
  'material',    // arbeitsscheine.material (BAUTAGEBUCH bleibt String — kein Konflikt)
  'fotos',       // arbeitsscheine.fotos + werkzeuge.fotos
  'items',       // checklists.items (sofern Schreibpfad geschlossen wird)
  'serviceheft'  // werkzeuge.serviceheft
];
```

**Vorteil:** Additiv, minimal, kein UI-Touch, kein Migration-Risk.
**Cross-Table-Sicherheit:** Z1661-Guard `typeof v === 'object'` greift NUR fuer Objects/Arrays. Strings passieren durch -> `bautagebuch.material:"text"` bleibt unveraendert. **Kein Konflikt.**
**Caveat:** `_finalForm` von AS (`form`) hat AUCH Felder wie `personal:[...]` (kommt aber NUR im forms-Container vor — nicht direkt in arbeitsscheine-table). Cross-check fuer jeden _mapBody-Pfad empfohlen.

### Option B) DB-Migration TEXT -> jsonb (CLEAN)

3 Tabellen, 5 Spalten:
```sql
ALTER TABLE arbeitsscheine ALTER COLUMN material TYPE jsonb USING NULLIF(material,'')::jsonb;
ALTER TABLE arbeitsscheine ALTER COLUMN fotos    TYPE jsonb USING NULLIF(fotos,'')::jsonb;
ALTER TABLE checklists     ALTER COLUMN items    TYPE jsonb USING NULLIF(items,'')::jsonb;
ALTER TABLE werkzeuge      ALTER COLUMN fotos    TYPE jsonb USING NULLIF(fotos,'')::jsonb;
ALTER TABLE werkzeuge      ALTER COLUMN serviceheft TYPE jsonb USING NULLIF(serviceheft,'')::jsonb;
```
**Vorteil:** Sauber, Query-faehig (`->>`, `@>`), keine Whitelist mehr noetig (Lesestellen `_jp` bleibt fwd-kompatibel).
**Risiko:** Bei Bestand mit `""` oder kaputten Strings -> `USING`-Cast erfordert Sanitization. Sebastian-Dump pruefen. Plus RLS-Policy-Review.

### Option C) Manuelles `JSON.stringify` an Schreibstellen (DISTRIBUTED)

Pro Site: `material:JSON.stringify(_finalForm.material||[])` etc. — Touch in 6+ Sites.
**Nachteil:** Verteilt, fehleranfaellig, kein single-source. **NICHT empfohlen.**

## Sprint-80 Empfehlung

1. **Sebastian-DB-Check** (SQL oben) — bestaetigen Datentyp aller 5 Spalten + `forms.data`.
2. **Bei TEXT:** Option **A** anwenden (4 Strings in Whitelist). Patch ist 4-Lines, low-risk, additiv.
3. **Laengerfristig:** Option **B** als sauberer Endzustand. Migration in separatem Sprint.
4. **Separater P2-Befund:** Checklist-Items-Sync (Z10056) — items werden nie an Server geschickt. Eigenes Ticket.

## Schreibstellen-Count

- **arbeitsscheine.material/fotos:** 1 echte Schreibstelle (Z6003 `_finalForm`) + 2 sekundaere (Z6055/6056 OFFA-Import, dort undef) + 2 weitere Update-Pfade (Z6006/6007, dort selten betroffen).
- **checklists.items:** 0 Schreibstellen — items wird **nie** synchronisiert (Z10056 ohne items).
- **werkzeuge.fotos/serviceheft:** 3 Schreibstellen (Z17968 PUT-serviceheft, Z18072 PUT-form, Z18073 POST-form).
- **bautagebuch.material:** 2 Schreibstellen (Z12176/12179) — String, OK.
- **forms.data (Container fuer regie.material etc.):** N+ Schreibstellen via `useEditable.save` (Z9949/9996+).

**Sites-Count gesamt: 12 dokumentiert** — davon 5 HIGH (Z6003 x2, Z17968, Z18072, Z18073), 0 MED, 7 LOW/OK/N/A.

## Hard-Constraints respektiert

- Nur `docs/` editiert — `index.html`/`sw.js` **NICHT** angefasst.
- TEXT_JSON_FIELDS / `_mapBody` nur gelesen.
- Auth/Sync/Juprowa/OFFA-Code unveraendert.
- Doc-Commit als Sprint-80-Output.
