# HANDOFF — A-2: Juprowa Status-Roundtrip 4→1 / 15→11

**Status:** DOKUMENTIERT, **nicht gefixt** (Sebastian-Entscheidung 2026-06-29). Kein Commit, kein OFFA-Write.
**Stand Codebasis:** v3.9.569 (HEAD `d065111`, origin/main in sync). Zeilennummern gelten für diesen Stand (nach dem Kiosk-PII-Lockdown-Shift; bei weiteren Edits neu greppen).

---

## Der Bug (verifiziert)

**Nicht-injektive Forward-Map** `JUPROWA_STATUS_MAP` (`index.html:3017`):
```
{'0':'aufgenommen','1':'freigegeben','2':'aufgeschoben','3':'in_bearbeitung',
 '4':'freigegeben','5':'erledigt','10':'abgerechnet','11':'bar_bezahlt',
 '15':'bar_bezahlt','20':'storniert'}
```
→ **4 und 1** → beide `'freigegeben'`; **15 und 11** → beide `'bar_bezahlt'`.

**Reverse-Map** `JUPROWA_STATUS_REV` (`:3244`): `{… freigegeben:'1', bar_bezahlt:'11' …}` (kein 4, kein 15).

**Push-Site ohne Dirty-Check** (`:3307`, in Funktion `_juprowaReversMap`):
```js
if(schein.scheinstatus&&JUPROWA_STATUS_REV[schein.scheinstatus]!=null)
  json.AK_AUFSTATUS=JUPROWA_STATUS_REV[schein.scheinstatus];
```
→ Ein aus OFFA gezogener Status **4** (`→'freigegeben'`) wird bei JEDEM Push als **AK_AUFSTATUS=1** zurückgeschrieben (15→11 analog) — **auch ohne echte Status-Änderung** (jeder Push wegen `durchgefuehrte`/`notizen`/Termin/etc. löst es aus). Stille, OFFA-seitig irreversible Status-Verfälschung.

---

## Welche Felder / Zeilen / welches Mapping falsch ist

| Element | Zeile | Problem |
|---|---|---|
| `JUPROWA_STATUS_MAP` | 3017 | nicht-injektiv: `4→freigegeben` (==1), `15→bar_bezahlt` (==11) |
| `JUPROWA_STATUS_REV` | 3244 | kollabiert: `freigegeben→1`, `bar_bezahlt→11` (4/15 unerreichbar) |
| `json.AK_AUFSTATUS` Push | **3307** | sendet bedingungslos den Reverse, kein Vergleich gegen den gepullten Roh-Status |
| betroffenes OFFA-Feld | — | **AK_AUFSTATUS** (Auftragsstatus) |

---

## PULL-seitig oder PUSH-seitig? Und Phase-2-Tabu-Klärung

- Der korrekte Fix ist **PUSH-seitig**: er muss das ausgehende Payload (`json.AK_AUFSTATUS`) korrigieren. Die Korruption entsteht beim Senden an OFFA (wir schicken 1 statt 4) — **eine PULL-seitige `push_pending`-Schutzmaßnahme würde das NICHT lösen**, weil `push_pending` nur steuert, ob ein Pull lokale Edits überschreibt, nicht WAS gepusht wird.
- **Fix-Ort:** Funktion **`_juprowaReversMap(schein)`** (Start `:3287`, Bug-Zeile `:3307`) — der Push-Payload-**Builder**.
- **Phase-2-Tabu (`_juprowaPush`):** `_juprowaPush` (`:3350`) wird **NICHT editiert**. ABER: `_juprowaPush` ruft den Builder an **`:3359`** auf (`const pushJson=_juprowaReversMap(schein)`), d.h. das Push-VERHALTEN ändert sich über die Abhängigkeit.
  - Wenn „Tabu" = *die Funktion `_juprowaPush` nicht anfassen* → **eingehalten** ✓ (Edit liegt im Builder).
  - Wenn „Tabu" = *den Push-Pfad inhaltlich gar nicht verändern* → ⚠️ **dieser Fix fällt darunter** und braucht ausdrückliche Freigabe, weil er das ausgehende OFFA-Payload ändert.
  - → Nächste Session: vor Umsetzung diese Tabu-Auslegung mit Sebastian klären.

---

## Vorgeschlagener Fix (NICHT umgesetzt — Referenz für nächste Session)

Ersetzt `:3307` in `_juprowaReversMap`. Muster = der bestehende konservative `juprowa_raw`-Echo (RE_ADR_* `:3332+`):
```js
// Dirty-Check gegen zuletzt gepullten Roh-Status: bildet er auf DENSELBEN App-Status ab
// (Roundtrip-stabil = keine echte Aenderung), Roh-Wert echoen statt kanonischen Reverse erzwingen.
if(schein.scheinstatus&&JUPROWA_STATUS_REV[schein.scheinstatus]!=null){
  const _rawSt=(schein.juprowa_raw&&typeof schein.juprowa_raw==='object'&&schein.juprowa_raw.AK_AUFSTATUS!=null)?String(schein.juprowa_raw.AK_AUFSTATUS):null;
  json.AK_AUFSTATUS=(_rawSt!=null&&JUPROWA_STATUS_MAP[_rawSt]===schein.scheinstatus)?_rawSt:JUPROWA_STATUS_REV[schein.scheinstatus];
}
```
Verhalten: Pull 4 unverändert → bleibt 4; Pull 15 unverändert → bleibt 15; echte Änderung `freigegeben→erledigt` → 5; kein `juprowa_raw` → Reverse (wie bisher).

---

## Nebennotiz — AK_PRIOR (NICHT fixen)

`json.AK_PRIOR` (`:3305`) hat dasselbe nicht-injektive Muster:
- `JUPROWA_PRIO_MAP` (`:3018`): `0→'keine'`, `1→'keine'`.
- `JUPROWA_PRIO_REV` (`:3243`): `keine→'1'`.
→ Pull-Prio **0** wird beim Push zu **1**. **Folgenlos** (beide semantisch „keine") — bewusst NICHT fixen. Nur falls man denselben Dirty-Check aus Konsistenzgründen mitnimmt.

---

## Gate-Plan (für die eigentliche Umsetzung, nächste Session)
index.html-Change → v3.9.569 → v3.9.570 (Triple-Bump SW_VER + APP_VERSION + sw.js CACHE_NAME) · `python scripts/node_check.py index.html` · `python scripts/_bracket_check.py index.html` (Baseline `() -1, {} 0, [] 0`) · `node sql/_check_version.js` · `python -m pytest tests/ -q` (998) · eigener Commit + Push (main sauber bei d065111, kein Stacking). **OFFA-Push outward-facing** → vor Commit Tabu-Auslegung bestätigen.
