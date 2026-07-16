# Register #31e — Schreibstellen-Inventar `arbeitsscheine` (Abrechnungs-Lebensader)

**Stand:** 16.07.2026, nach v3.9.755 (#31g). **Gate:** `tests/test_as_writers_whitelist.py` friert diese Whitelist ein.

## Grundsatz
Juprowa ist die reine **Maschinen-Brücke App↔OFFA**. Der Push ist die **Abrechnungs-Lebensader**.
Das **EINE Schreibgesetz** ist `onDrop/updAs → SQ.push` (Offline-Queue → `_translateAndExec` → PATCH).
Jeder **direkte** `_sbPatch/_sbPost("arbeitsscheine", …)` **umgeht** dieses Gesetz und ist deshalb
hoch-regressionskritisch. Ziel von #31e: den Bestand auditieren, per statischem Gate einfrieren, und den
einzigen redundanten Direkt-Writer für eine spätere **Live-Co-Verifikation** markieren.

## Inventar — 6 direkte Writer, alle in der Sync/Push-Maschinerie

| # | Zeile* | Funktion | Zweck | Klassifikation |
|---|--------|----------|-------|----------------|
| 1 | ~3541 | `_juprowaSync` | PULL: existierenden Schein mit OFFA-Daten patchen | **LEGITIM** — das IST die Brücke (App←OFFA) |
| 2 | ~3546 | `_juprowaSync` | PULL: neuen OFFA-Schein einfügen (`_sbPost`) | **LEGITIM** — Brücke (App←OFFA) |
| 3 | ~3780 | `_juprowaPush` | `push_error` bei RPC-non-ok setzen | **LEGITIM** — Fehler-Sichtbarkeit |
| 4 | ~3799 | `_juprowaPush` | **echo-gated Reset**: `push_pending=false`+`juprowa_raw` nach `respData.ID` | **LEGITIM** — *der* eine Drain-Reset (v616-gated) |
| 5 | ~3806 | `_juprowaPush` | `push_error` im catch (Exception) | **LEGITIM** — Fehler-Sichtbarkeit |
| 6 | ~3878 | `_juprowaMarkEdited` | direkter `push_pending=true` (`{local_updated_at,push_pending:true}`) | **REDUNDANT** — Migrations-Kandidat |

\* Zeilen driften bei Edits; das Gate prüft **Funktion + Anzahl**, nicht die Zeile.

## Befund (Korrektur der Handoff-Schätzung „1 Drain legit, 5 umziehen")
Tatsächlich sind **5 von 6 legitime Maschinen-Brücke-Writes** (Pull 2 + Push 3 — sie *sind* die Brücke, ein
Umzug auf `updAs`/SQ ergäbe keinen Sinn). Nur **#6 `_juprowaMarkEdited`** ist ein echter Konsolidierungs-
Kandidat.

### #6 `_juprowaMarkEdited` = W2 der 31g-Forensik
`updAs`/`storno`/`verschieben`/`saveAs` rufen bei einem Push-Feld-Diff **beides**:
- **W1** `SQ.push({PUT, body:{…,push_pending:true}})` (der Offline-Queue-Weg, gebounced) **und**
- **W2** `_juprowaMarkEdited → _sbPatch(push_pending:true)` (direkt, sofort).

W2 dupliziert W1s Effekt (`push_pending=true`). Da die 31g-Selbstheilung ohnehin an **W1** hängt (der
`doSync`-Hook erkennt `body.push_pending===true` aus dem SQ-Flush) und die Pull-Schutz-Logik (`isPending`,
~Z. 3517) nur das Flag liest, wäre **W2 entfernbar** — der SQ-Pfad trägt `push_pending` weiterhin.

## Empfehlung (NICHT autonom — Live-Co-Verifikation)
1. **W2 (`_juprowaMarkEdited`) stilllegen**, sodass `push_pending` **nur** über den SQ-Pfad (W1) läuft →
   ein einziger, geordneter Schreibweg für das Flag. Erwartet: identisches Verhalten, ein Direkt-Writer
   weniger auf der Lebensader. **Live-Beleg:** Statuswechsel → genau 1 `push_pending`-Setzung, Selbstheilung
   unverändert, kein Pull-Echo-Verlust.
2. **31g-Konsolidierung** (aus Live-Abnahme 31g, S075354): Sofort-Push (updAs W3) und Self-Heal-`doSync`-Tick
   pushen denselben Schein ~164ms auseinander (idempotent). Eine **gemeinsame Debounce-Klammer** würde den
   Doppel-Push sparen. Harmlos → beim nächsten Anfassen des Push-Pfads mitnehmen.

Beide Punkte berühren den Push-Trigger → gehören in die gemeinsame #31a/b/e-Session, nicht in einen Blind-Lauf.

## Was dieses Gate garantiert (jetzt aktiv)
- Genau **6** direkte `arbeitsscheine`-Writer; Verteilung `{_juprowaSync:2, _juprowaPush:3, _juprowaMarkEdited:1}`.
- **Kein** direkter Writer in `updAs`/`storno`/`verschieben` (User-Handler schreiben nur via `SQ.push`).
- Der Drain-Reset bleibt **echo-gated** (v616) — nie ein blinder `push_pending=false`.

Jeder neue/verschobene Direkt-Write bricht `test_as_writers_whitelist.py` und erzwingt ein Re-Audit.
