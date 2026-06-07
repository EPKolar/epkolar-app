# Overnight-Agenten-Bug-Hunt — Welle 2 Funde (2026-06-07, So abends)

Read-only Audit-Agenten. Konservativ: nur eindeutige, eng begrenzte Frontend-Bugs werden gefixt (mit Triade +
Verhaltens-Test, eigener Commit); nuancierte/strukturelle/sensible Themen werden für Sebastian dokumentiert.

## Urlaub / Kontingent / Carry-Over — DOKUMENTIERT (nicht über Nacht gefixt)
Kernformel `resturlaub` (Z.14307, v3.8.64) ist **korrekt** (Anspruch + Vorjahr − genehmigt − ausstehend, abgelehnt
ignoriert; Beispiel Günther 192,5+0−90−0 = 102,5h ✓). **Begründung Nicht-Fix:** Urlaubssaldo-Logik ist sensibel
(Mitarbeiter-Ansprüche), und die Funde sind Anzeige-Semantik / strukturell / mehrstellig — kein sauberer Single-Site-Fix.

1. **[MITTEL-HOCH] Anzeige-Inkonsistenz abgelehnte Tage** `index.html:14302/14513`: Spalte „Urlaub" zeigt `ys.urlaubStd`
   (inkl. abgelehnt), `resturlaub` zieht nur genehmigt+ausstehend ab → „Urlaub + Rest ≠ Gesamt" bei abgelehnten Tagen.
   **Entscheidung Sebastian:** Soll die „Urlaub"-Spalte Verbrauchtes (gen+ausstehend, konsistent mit Rest) oder ALLE
   Anträge (inkl. abgelehnt) zeigen? Fix dann: 14513 `ys.urlaubStd` → `(ys.urlaubStdGen+ys.urlaubStdAusstehend)` ODER
   separate „abgelehnt"-Spalte. (Anzeige-Semantik-Entscheidung, kein blinder Fix.)
2. **[MITTEL] Anspruch `0h` nicht speicherbar** `index.html:14510` (+ resturlaub 14307, total 14506): `parseFloat(...)||192.5`
   überschreibt ein bewusst eingegebenes `0` (z.B. Ganzjahres-Karenz) auf 192,5. Korrekter Fix bräuchte `||192.5`→nullish
   (`?? ` / explizit `isNaN`) KONSISTENT an allen ~4 Stellen (Input-onChange, Input-value, resturlaub, total) — sonst
   speichert man 0, aber resturlaub rechnet wieder mit 192,5. `woche||38.5` NICHT ändern (0-Std-Woche bricht Tages-Skalierung).
   Mehrstellige Änderung auf sensibler Logik → Sebastian-Freigabe + dedizierter Test.
3. **[MITTEL] Zwei getrennte Urlaubs-Systeme** `index.html:15955` (UrlaubsantragPanel/`urlaubsantraege`-Tabelle, Datumsbereich)
   vs `14307` (Kalender `abs`/`absApprovals`, Tages-Toggle). `entscheiden()` (Antrags-Panel-Genehmigung) schreibt NICHT in
   `abs` → über das Antrags-Panel genehmigter Urlaub taucht NIE im Resturlaub auf. **Strukturell** (zwei Quellen) — Design-
   Entscheidung: Antrags-Bereich bei Genehmigung in Werktags-`abs` expandieren ODER resturlaub zusätzlich aus
   `urlaubsantraege` speisen. Kein Quick-Fix.
4. **[NIEDRIG-MITTEL] Keine Halbtage** `index.html:14280/14286`: `stdVonTag` nur ganze Tage; ein halber Urlaubstag wird als
   voller (8,5h) abgezogen. Feature, falls fachlich gefordert (AT üblich).
5. **[NIEDRIG] Carry-Over rein manuell** `index.html:14267/14511`: kein automatischer Jahres-Übertrag von `resturlaub(yr-1)`
   nach `vorjahr` in `yr` → bei Jahreswechsel default 0 bis Admin nachträgt. Evtl. gewollt (manuelle Kontrolle), als Risiko notiert.
6. **[NIEDRIG/latent] `tage` ohne woche-Arg** `index.html:14289`: `tage:(stdVonTag(d)>0?1:0)` — aktuell korrekt (nur >0-Check),
   latent falsch bei künftiger skalierter Nutzung. Kosmetik.

## Arbeitsscheine / OFFA-Import
- **[MITTEL] AS#1 OFFA In-Batch-Duplikat → ✅ GEFIXT v3.9.161**: `commitImport` (14.6206) ohne Batch-internes Dedupe →
  dieselbe Scheinnummer in einem Import zweimal = doppelter Insert. Fix: `seen`-Set, erste Anlage gewinnt, weitere übersprungen.
- **[NIEDRIG] AS#3 saveAs-Guard-Reset → ✅ GEFIXT v3.9.161**: Monteur-Bail (6158) machte `return` ohne `_saveAsInFlightRef=0`
  (anders als 6152/6157) → 800ms-Lockout des nächsten legitimen Saves. Reset ergänzt.
- **[MITTEL] AS#2 Re-Import überschreibt manuell zugewiesenen Monteur — DOKUMENTIERT (Disposition-Entscheidung)**: `commitImport`
  (6212) schützt scheinstatus/termine/notizen, aber `monteur` wird bei `r._monteurId` gesetzt → ein im Büro geänderter Monteur
  wird vom OFFA-Re-Import überschrieben. Fix wäre `monteur` in die Schutz-Liste, ABER: ändert Disposition-Verhalten →
  Sebastian-Entscheidung (soll OFFA den Monteur führen oder das Büro?).
- **[NIEDRIG] AS#4 AS_TRANSITIONS all→all = toter Guard — DOKUMENTIERT**: `_isLegalAsTransition` immer true (freie Übergänge
  vermutlich gewollt, Sebastian-Vorgabe „alle Wechsel frei" v3.9.122). Guard+Toast sind Dead Code. Optional: entfernen+kommentieren.

## Mängel / PlanRadar
- **[HOCH] Mängel#1 Layer-Sichtbarkeits-Toggle (👁️/⊘) wirkungslos → ✅ GEFIXT v3.9.161**: `ticketsOnPage` filterte nur auf das
  `filterLayer`-Dropdown, nie auf `layers[].visible` → Auge ein/aus hatte keinen Effekt auf die Pins. Fix: explizit ausgeblendete
  Ebenen (`l.visible===false`) aus `ticketsOnPage` filtern (unbekannte Ebenen bleiben sichtbar = konservativ).
- **[HOCH] Mängel#2 Plan-Ticket(„mangel") desynct mit gespiegeltem defect — DOKUMENTIERT (Multi-Flow)**: `createTicket` (11184)
  pusht bei type=mangel zusätzlich `/api/defects` mit gleicher id; `updateTicket`/`deleteTicket` (11184/11185) fassen nur tickets
  an → Status-Änderung lässt Mangel veralten, Löschen hinterlässt verwaisten defect (zählt in KPIs). Fix: update/delete den
  gespiegelten defect mitführen. Multi-Flow + Daten-Integrität → eigener getesteter Fix (nächste Charge).
- **[MITTEL] Mängel#3 Pin-Nummer Plan ≠ XLS ≠ PNG — DOKUMENTIERT**: drei verschiedene Nummerierungs-Quellen (ticketsOnPage-Index
  vs allTickets-Index). Querverweis Plan↔Liste bricht. Fix: eine kanonische Nummer (z.B. stabile t.nr). Entscheidung nötig.
- **[MITTEL] Mängel#5 Pin-Klick vor PDF-Render verzerrt — DOKUMENTIERT/Kandidat**: `handleCanvasClick` ohne `if(!pageDims)return;`
  → Klick vor erstem Render liefert verzerrte %-Werte. Contained-Fix möglich (Guard) — nächste Charge.
- **[MITTEL] Mängel#4 Status-Sort `||0` maskiert valid/fehlend — DOKUMENTIERT**: `ord[ks]||0` — gültiger `gemeldet`(0) und
  unbekannter Status kollabieren. Fix: `ord[ks]??99`. Klein.
- **[NIEDRIG] Mängel#6 Foto-Dedup Thumb/Full — DOKUMENTIERT**: Dedup über Roh-URL statt Foto-id → lokaler Thumb + Server-URL
  derselben Datei doppelt. Kosmetisch.
- **Sauber bestätigt:** Koordinaten durchgängig Prozent 0-100 (Pixel-Kommentare veraltet, Mathe korrekt), Zoom/Pan 0.4-6,
  Pin-scale(1/zoom), TDZ-Render-Fix stabil, Monteur-Permission-Gates vorhanden.
