# Diagnose: Ticket-Datenverlust (BVH Sparkasse Ravelsbach)

**Stand:** 2026-06-13 · HEAD `64316e2` v3.9.347 · **Read-only Analyse · KEIN Code-Change**

## Befund (Chat-Claude forensisch, 12.06.2026)

Projekt „BVH Sparkasse Ravelsbach" (id `pmof9xiwk`) hatte laut Sebastian 3 Plan-Tickets, vor Wochen auf dem Laptop direkt am Plan angelegt + sichtbar. JETZT:

- Rohe DB-Abfrage `SELECT count(*) FROM tickets` = **1 Zeile** gesamt im System.
- IndexedDB `epkolar_offline` hat **KEINEN** `tickets`-Store (tickets leben innerhalb des Stores `planData`).
- `syncQueue` = 1 Eintrag (kein Ticket).
- `syncQueueFailed` = 0.
- `activity_log` via Client = leer.
- Tabellen-Schema `tickets`: `id, plan_id, project_id, title, …, x, y, page` — **KEIN** `xPct/yPct`, **KEIN** `deleted_at`/Soft-Delete.

Die 2 fehlenden Tickets sind unwiederbringlich verloren. Diese Analyse identifiziert die Ursache, damit es nicht wieder passiert.

## Speicher-/Sync-Pfad für Plan-Tickets

| Phase | Stelle | Mechanik |
|---|---|---|
| 1. Erstellung | `index.html` Z.12039–12045 `createTicket()` | erzeugt `ticket={...newTicket,id:uid(),...}` (Client-generierte ID); `setPlanData(prev=>({...prev,tickets:[...prev.tickets,ticket]}))`; `SQ.push({url:"/api/tickets",method:"POST",body:{…full payload incl. x,y,plan_id,project_id,…}})`. Beide Pfade in einer Anweisung. |
| 2. Lokale Persistenz | Z.5049 useState `planData={plans:[],tickets:[],layers:DEF_LAYERS}` + IndexedDB-Store `planData` (DB `epkolar_offline` v8, Z.2447) | `planData` lebt als kombiniertes Objekt im React-State; die IDB-Persistierung über `ODB.load/save("planData",…)` (Z.5239 Load, Save siehe Effekt-Pfade) lädt/speichert das gesamte Objekt en bloc. |
| 3. Sync-Queue | Z.2532–2544 (`SQ.push/getAll/clear/remove/count`) | SyncQueue selbst IST in IDB unter Store `syncQueue` persistiert (`ODB.save("syncQueue",q)`). Drain läuft on-startup / periodic / on online. |
| 4. Server-Pull | Z.5273 `API.getTickets()` via Z.2330 `_sbGet("tickets",…)`; Resultat-Apply Z.5304–5305 | Wenn `tkts && tkts.length` → `setPlanData(prev=>{const upd={...prev}; …; upd.tickets = tkts.map(t=>({…}));})`. **Ganzes tickets-Array wird durch Server-Antwort ERSETZT, NICHT gemerged.** |

## Schwachstelle(n) — wo Datenverlust entstehen KANN

### 🔴 Schwachstelle #1 — Server-Pull überschreibt lokal-pending Tickets (HIGH)

**Stelle:** `index.html` Z.5305

```js
if(plns?.length || tkts?.length){
  setPlanData(prev=>{
    const upd={...prev};
    if(plns&&plns.length) upd.plans = plns.map(_mapPlan);
    if(tkts&&tkts.length) upd.tickets = tkts.map(t=>({...}));  // ← OVERWRITE
    return upd;
  });
}
```

**Mechanik:**
1. User legt ein Ticket an → `createTicket` setzt `planData.tickets` lokal (sofort sichtbar) + `SQ.push` POST in SyncQueue (noch nicht gedrained).
2. Sync-Drain ist langsam / offline / pending. POST liegt in IDB-`syncQueue`.
3. App wird neu geladen / Tab-Switch / `loadAll` triggert → Z.5273 `API.getTickets()` läuft.
4. Server liefert nur die bereits-bestätigten Tickets (das eine alte Ticket, das schon in der DB ist). Die noch-pending Tickets sind serverseitig noch nicht da.
5. Z.5305 `upd.tickets = tkts.map(...)` **ERSETZT** das komplette tickets-Array → die lokal noch-pending Tickets sind aus dem State verschwunden.
6. Nächster `ODB.save("planData", …)` (in Effekt-Pfaden, oder bei Tab-Wechsel) schreibt das überschriebene Objekt in IDB → auch in der lokalen Persistenz weg.
7. Die SyncQueue-POSTs liegen noch in `syncQueue` und werden später gedrained — DB bekommt sie. ABER: wenn vor dem Drain ein **Cache-Clear / „Clear site data" / SW-Update mit DB-Wipe** passiert → `syncQueue`-Store weg, POSTs weg, Tickets endgültig weg.

**Trigger-Kombinationen die zum 2-of-3-Verlust passen:**
- 3 Tickets angelegt offline (z.B. Laptop ohne Netz) → SyncQueue hat 3 POSTs.
- Bei nächstem Online-Drain wird **1 erfolgreich**, dann fehlerhaft / interruption / oder einer war schon vorher mit anderer ID gepusht und schreibt nur eine Zeile.
- Reload triggert Z.5305 → lokale planData.tickets-Array auf Server-Stand (1) gesetzt → 2 lokale weg.
- ODER: Browser-Speicher gelöscht (Sebastian: „in den letzten Wochen oft den lokalen Speicher geleert für Versions-Updates") → IDB-`syncQueue` weg → 2 noch nicht gedrainte POSTs verloren.

**Risiko-Einstufung:** HIGH (datenverlustkritisch + reproduzierbar über Offline+Reload-Pattern).

### 🟠 Schwachstelle #2 — IndexedDB-Wipe bei Service-Worker-Update / „Clear site data" löscht pending SyncQueue (MID-HIGH)

**Stelle:** `index.html` Z.2447 `DB_NAME="epkolar_offline"; DB_VER=8`; SW-Update-Pfad in `sw.js`.

**Mechanik:** Wenn der User per DevTools „Clear site data" wählt, oder bei aggressivem SW-Skip-Waiting + Cache-Bust die IDB als Teil des Storage-Cleanup mitläuft → `syncQueue`-Store weg.

**Befund-Vereinbarkeit:** Sebastian sagt selbst: „in den letzten Wochen oft den lokalen Speicher geleert (für Versions-Updates)". Es gibt aktuell **keinen** Pre-Wipe-Drain-Check, der vor einem Cache-Clear sicherstellt dass die SyncQueue leer ist.

**Risiko-Einstufung:** MID (User-Aktion erforderlich, aber Sebastian macht sie regelmäßig).

### 🟡 Schwachstelle #3 — Kein activity_log clientseitig spiegeln (LOW-MID)

`activity_log` ist leer laut Befund → kein forensischer Hinweis, wann/wer die Tickets angelegt hat.

**Mechanik:** `createTicket` pusht nichts in `activity_log`. Es gibt kein Audit-Trail für DAS-Ticket-WURDE-LOKAL-ANGELEGT-EVENT.

**Risiko-Einstufung:** LOW (kein direkter Datenverlust, aber Forensik-Lücke — bei künftigen Verlusten wieder keine Spur).

### 🟡 Schwachstelle #4 — Mängel-Spiegel bricht bei Ticket-Verlust mit (LOW-MID)

**Stelle:** Z.12045 `if(ticket.type==="mangel"){…SQ.push("/api/defects",POST,…)}`

**Mechanik:** Wenn das Ticket im State verloren geht, aber der defects-POST schon erfolgreich war → Geister-Defect in DB ohne Ticket-Pin. Bei den 2 verlorenen Tickets: wenn sie `type==="mangel"` waren, könnte ein „toter Defect" in der DB liegen (zu prüfen via SQL: `SELECT * FROM defects WHERE plan_id IN (Sparkasse-Plan-IDs)`).

**Risiko-Einstufung:** LOW (kosmetischer Nebeneffekt, kein zusätzlicher Verlust).

## Fix-Vorschlag (noch NICHT umsetzen — separate v3.9.xxx nach Sebastians Freigabe)

### Fix-A (PFLICHT, behebt Schwachstelle #1)

**Server-Pull mit Merge statt Overwrite:**

```js
if(tkts && tkts.length){
  const serverIds = new Set(tkts.map(t=>t.id));
  upd.tickets = [
    ...tkts.map(t=>({...t,planId:t.planId||t.plan_id,…})),       // Server-Stand
    ...(prev.tickets||[]).filter(t=>!serverIds.has(t.id))          // lokal-pending behalten
  ];
}
```

Das behält ALLE lokalen Tickets, deren ID der Server (noch) nicht kennt. Der nächste SyncQueue-Drain pusht sie. Wenn der Server sie dann hat, gewinnt der Server-Stand im nächsten Pull.

Analog auch für `plans` empfehlenswert (Schwachstelle existiert dort spiegelbildlich).

### Fix-B (PFLICHT, behebt Schwachstelle #2)

**Pre-Wipe-Drain-Guard:** Vor dem SW-Update-Apply / „Update bereit"-Banner-Klick prüfen ob `SQ.count() > 0`; wenn ja → User-Modal „⚠️ N Änderungen sind noch nicht synchronisiert. Erst senden, dann aktualisieren." mit Button „Jetzt synchronisieren". Nur dann SW-Skip-Waiting freigeben.

Zusätzlich: IndexedDB-Wipe-Detection beim App-Start (z.B. via Heartbeat-Key in IDB der versions-tagged ist). Wenn der Heartbeat-Key bei einem Start fehlt aber `localStorage` noch da → Warnung „Lokaler Speicher wurde geleert. Möglicher Datenverlust prüfen."

### Fix-C (Empfehlung, behebt Schwachstelle #3)

**Client-seitiger activity_log-Spiegel:** Bei jedem `SQ.push` zusätzlich ein lightweight-Audit-Eintrag in einen lokalen `auditLog`-Store (mit Timestamp + User + Action + payload-Hash) — nie automatisch geleert. So ist im Verlust-Fall nachvollziehbar was angelegt wurde.

### Fix-D (Empfehlung, behebt Schwachstelle #4)

**defects-Spiegel idempotent + Anti-Geister:** Vor dem defects-POST prüfen ob das Ticket noch in `planData.tickets` existiert. Wenn nicht (Verlust) → defects-POST nicht abschicken. Periodischer Server-Sweep: defects ohne ticket-Pendant löschen.

## Was wir aus dem konkreten Verlust lernen

**Wahrscheinlichste Ursache:** Schwachstelle #1 + #2 in Kombination. Sebastian hat lokal Tickets angelegt (3), die SyncQueue hatte sie als POST in IDB. Bei einem SW-Update / „Clear site data" zur App-Aktualisierung wurde die IDB inklusive `syncQueue` geleert BEVOR die POSTs gedrained waren. Beim nächsten Load liefert der Server die 1 Ticket-Zeile, die VOR den 3 angelegt war (eines aus älterer Anlege-Session). Z.5305 hat dann den State auf Server-Stand reduziert.

**Präventiv MUSS:**
1. Z.5305 auf Merge umstellen (Fix-A).
2. Pre-Wipe-Drain-Guard (Fix-B).

**Präventiv KANN:**
3. Client-Audit-Log (Fix-C) → Forensik nächstes Mal.
4. defects-Anti-Geister (Fix-D) → Hygiene.

## Risiko-Status anderer Stores mit ähnlichem Pfad

| Store | Server-Pull-Stelle | Apply-Mechanik | Status |
|---|---|---|---|
| `time_entries` | Z.5278 setEntries(ent.map(...)) | OVERWRITE | **RISKY** — selbes Pattern, aber: time_entries hat höhere Drain-Frequenz weil VBueroExport seit v3.9.342 visibilitychange+focus reload triggert → Window kleiner |
| `forms` | Z.5279–5283 setForms | OVERWRITE (mit prev.spread, aber Top-Level-Keys überschrieben) | MID-RISKY — bei Form-Sub-Arrays könnte ähnlicher Verlust drohen |
| `defects` | Z.5284–5286 setForms(prev=>({...prev,maengel:def.map(...)})) | OVERWRITE auf maengel | RISKY — selber Mechanismus |
| `absences` | Z.5287–5293 absMap/apprMap | MERGE (prev wins über server in apprMap Z.5292) | **SAFE** — explizit als Lokal-gewinnt-Pattern dokumentiert v3.9.111 |
| `arbeitsscheine` | Z.5295 setArbeitsscheine(asch.map(_mapArbeitsschein)) | OVERWRITE | RISKY (aber seit v3.9.346 kein App-Anlegen mehr → reduziertes Risiko, weil POSTs nur noch aus OFFA-Import kommen, die robuster sind) |
| `werkzeuge`, `fahrzeuge`, `projects`, `monteure` | Z.5276–5298 setX(y.map(...)) | OVERWRITE | LOW — Anlage passiert seltener und mit explizitem Save-Pfad |
| `monteurProjekte` | Z.5299–5302 setMonteurProjekte | MERGE-with-prev | SAFER (aber phantom-default Z.5025 ist ein anderes UI-Problem, siehe v3.9.348) |

## Strikte Schutzliste

- Diese Diagnose ändert KEINEN Code. Fix kommt in einer separaten v3.9.xxx nach Sebastians expliziter Freigabe.
- `_juprowaPush` / Juprowa-Phase-1-Pull / Tank-Flow / RLS-Welle-1-Logik unberührt.
- Die identifizierten Schwachstellen #1+#2 existieren spiegelbildlich auch für `time_entries`, `forms`, `defects`, `arbeitsscheine` — der Fix sollte als generischer Merge-Helper gestaltet werden, der allen Store-Resolves gemeinsam zur Verfügung steht (nicht 7× duplizieren).

## DB-Direktive

`jiggujpruejkaomgxarp` HART. Keine DB-Writes ohne Sebastian-Freigabe. Bei späterem Fix-Apply: zuerst `SELECT COUNT(*)` auf `tickets` snapshot zur Beweissicherung, dann Fix-A einbauen + Smoke, dann Fix-B mit Drain-Modal-Vorlage.
