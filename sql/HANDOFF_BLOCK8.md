# Block 8 deployed — v3.5.175

## Was gemacht wurde
AS-Signature-Close-Flow: Nach `saveAs` wird AS automatisch auf `scheinstatus='erledigt'` + `abschlussDatum=heute` gesetzt, wenn beide Unterschriften (sigMA + sigKunde) vorhanden sind und der Status noch in der 'offen'-Gruppe ist.

**Wichtige Schema-Anpassung gegenüber ursprünglichem Prompt**:
- Prompt nannte `status='abgeschlossen'` + `abgeschlossen_am` — beides existiert NICHT im Schema.
- Korrekt implementiert: `scheinstatus='erledigt'` + `abschlussDatum` (mappt auf DB-Column `abschluss_datum`).
- Signaturen sind keine separaten Storage-URLs sondern dataUrls im form-State → kein separater Upload-Hook nötig, Auto-Close läuft atomic in saveAs.

Commit: `8b55b33`

## Smoke-Test für Sebastian (3 min)

1. **T-149 · Neuer AS auto-close**:
   - AS anlegen, Status='aufgenommen', Kunde ausfüllen, Monteur-Unterschrift zeichnen, Kunden-Unterschrift zeichnen, "Speichern"
   - Erwartung: Toast "✓ AS automatisch abgeschlossen", Liste zeigt AS als "🔵 erledigt", `abschlussDatum`=heute.

2. **T-150 · Bereits-abgeschlossen bleibt**:
   - Vorhandenen AS mit `scheinstatus='erledigt'` öffnen, zweite Unterschrift neu zeichnen, speichern
   - Erwartung: KEIN "automatisch abgeschlossen"-Toast (da nicht mehr in 'offen'-Gruppe), `abschlussDatum` unverändert.

3. **T-151 · Nur eine Signatur**:
   - AS mit nur `sigMA` gezeichnet, `sigKunde` leer, speichern
   - Erwartung: kein auto-close, Status bleibt wie war.

4. **T-152 · Storniert wird nicht reaktiviert**:
   - AS auf `storniert` setzen (via Storno-Button), dann Signaturen zeichnen und speichern
   - Erwartung: Status bleibt `storniert`, kein auto-close (storniert ist nicht in AS_GRP_OFFEN).

5. **T-153 · Offline-Test**:
   - Flugzeug-Modus, AS mit Doppel-Signatur abschließen
   - Erwartung: sofort als "erledigt" sichtbar, SQ.push queued, Reconnect → DB synchronisiert.

## Regression-Risiko
**Niedrig** — Änderung ist lokal in `saveAs` (Zeilen ~4347-4350). Keine neuen useEffect/Handler/State, kein Refactor. Der einzige konzeptionelle Shift: `form` wird via Spread in ein `_finalForm` verpackt und das wird downstream verwendet.

Vor dem Patch: `SQ.push({..., body:form})`.
Nach dem Patch: `SQ.push({..., body:_finalForm})` — inhaltlich identisch, außer im Auto-Close-Fall.

## Test-Coverage
Session 14 T-149..T-153 (5 Testfälle).

## Bekannte Randbedingungen

### B-021 (Silent-Re-Auth im engeren Sinn nicht impl.) — P2 OPEN
Bei langen Sessions (>JWT-TTL, default ~1h) kann der Close-Patch mit 401 scheitern. Existierender `_sbAuthRefresh()` im doSync-Flow fängt das ab (Line 3420: `if(p2.exp*1000-Date.now()<60000)await _sbAuthRefresh()`). Fresh-Login schützt in allen Fällen.

### Nicht-atomar mit Signatur-Wischen selbst
Auto-close passiert bei `saveAs` (Button "Speichern" klicken). Wenn der User nur Unterschrift zeichnet ohne zu speichern, passiert nichts — wie vor dem Patch. Es gibt keinen "Signature-Save-Event" separat vom AS-Save.

### `sigMA.length>100` Heuristik
SignaturePad exportiert das Canvas als PNG-dataUrl. Eine "wirklich leere" Signatur exportiert als `""` (leer) oder sehr kurzen dataUrl. Eine echte Unterschrift hat immer >100 Zeichen. Bei Grenzfällen (z.B. ein einzelner Strich) könnte theoretisch der Threshold knapp sein — falls User beobachten dass Auto-Close bei minimalen Strichen NICHT feuert, Threshold auf 200+ anheben.

## Cross-Check gegen prev. Handoff
Aus `sql/HANDOFF_OVERNIGHT_v3.5.174.md`: "Block 8 — AS-Signature-Close-Flow — Schnell-Win (SignaturePad existiert) · 1-2h" ← jetzt erledigt ✓
