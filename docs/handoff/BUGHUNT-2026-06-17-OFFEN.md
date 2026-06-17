# Bug-Hunt-Marathon 2026-06-17 — OFFENE Punkte (Sebastian-Entscheidung / Backend)

Stand: main = origin = **v3.9.415**. 9 Fix-Batches autonom gepusht (v3.9.407–415), 931 pytest grün,
node_check 0. 4 Audit-Wellen (18 Read-only-Agenten) + adversariale Selbst-Review.

**Bereits behoben & live (v3.9.407–415):** FZ-/Pickerl-Timezone (4 Stellen), Material-FK-null,
CSV-Formel-Injektion, Storage-Waisen beim Löschen (privat-Buckets), **P1** Tages-Mehrstunden (Lohnbeleg),
Rechte-Härtung (Urlaub/Gefahrstoff/WZ/Projekt/Zeit — Handler-Guards), onOnline-countMine, **P2** QuickEditPin
Self-Assign-Klemme, **P2** OCR-Dezimalverlust, Stunden-24h-Cap, ChartBox-fmt (alle Chart-Typen), **P1**
Plan-Viewer-Touch-Pan, Timer-Leak-Cleanup, **P1** Notif-read-reconcile, TicketDetail-Badge-Status.

Die folgenden Punkte wurden bewusst **NICHT** autonom geändert — sie brauchen eine Geschäfts-/Backend-
Entscheidung oder berühren eingefrorene/lohnrelevante Bereiche.

---

## A) Backend / Edge Functions (Deploy nötig — nicht autonom)

1. **🔴 P1 `ocr_tankbeleg` ohne Aufrufer-Auth + ohne Bildgrößen-Limit** (`supabase/functions/ocr_tankbeleg/index.ts`).
   Einzige der 3 Functions ohne Role-Gate: kein `getUser()`, kein Größen-Check. Wer den (öffentlichen) anon-Key
   kennt, kann beliebig oft Bilder an die kostenpflichtige Google-Vision-API schicken → **Kosten-DoS** + Memory-Druck.
   Fix: `Authorization`-JWT prüfen (`getUser()`, wie admin-create-user/supplier-sync) **vor** dem Vision-Call +
   `if(image.length>8_000_000) 413`. → Deploy durch Sebastian.
2. **P2 `supplier-sync` set-credentials** validiert `supplierId`-Existenz nicht (`UPDATE ... WHERE id=…` = 0 Rows →
   `200 {ok:true}` trotz No-Op) + leere username/password erlaubt. Fix: `.select().maybeSingle()` + Leerstring-Check.
3. **P2 `admin-create-user`** nicht-atomares Rollback: schlägt `deleteUser` im Rollback fehl, wird der Fehler
   verschluckt (`.catch(()=>{})`) → verwaister auth.user + `rolledBack:true` gelogen. Fix: Rollback-Ergebnis prüfen.
4. **P3** alle 3 Functions leaken DB-Fehlertext im Response-Body + CORS `*`. Kosmetisch (außer #1).

---

## B) Notifications — RLS-abhängig (erst read-only Policy-Check gegen `jiggujpruejkaomgxarp`)

5. **P1/P2 `markAllRead`** wertet 0-Row-RLS-Silent-Denial (HTTP 200, 0 Zeilen) als Erfolg → lokal „alle gelesen",
   DB bleibt unread. (Der read-reconcile-Fix v3.9.415 mildert das Symptom, behebt aber nicht die Schreibseite.)
   Fix: `Prefer: return=representation,count=exact` + bei 0 betroffenen Zeilen warnen. **Erst Policy prüfen.**
6. **P2** GET `/api/notifications` filtert NICHT nach `user_id` (verlässt sich allein auf RLS); Kommentar
   „user-filtered" ist falsch. Defense-in-depth: serverseitig `user_id=eq.<curUser>` + Mapper ohne `||curUser.id`.

---

## C) Geschäftslogik / Reporting — braucht Entscheidung

7. **P2 Chef-Portal Budget-Ampel doppelt + widersprüchlich.** „Projekte"-Tabelle rechnet `usedH*85` (hartkodierter
   €85-Satz) gegen `betrag` (Auftrags-**Umsatz**!) mit Schwellen 80/100; die „Projekt-Budget (Soll-Ist)"-Karte rechnet
   echten `monteure.stundensatz` gegen `budget_euro` mit 85/100. Dasselbe Projekt kann zwei verschiedene Ampeln zeigen.
   **Entscheidung nötig:** welcher Satz + welche Bezugsgröße + welche Schwellen sind kanonisch? Dann eine gemeinsame
   Helper-Funktion.
8. **P2 Auslastungs-Ampel-Mix.** Altes „Zeit & Personal"-Widget: 70/90/100 gegen fixe 38,5 h. Neue „Auslastung/
   Kapazität": 70/95 gegen feiertags-korrekte Soll-Range. Gleicher Monteur kann in einem Widget gelb, im anderen grün
   sein. Vereinheitlichen oder altes Widget entfernen.
9. **P2 Teilzeit ignoriert.** Kapazitäts-Soll (`38.5` hartkodiert) und Urlaubs-Materialisierung (`_stdVonTagBrk`
   8,5/4,5 ohne `woche`-Faktor) skalieren NICHT mit Teilzeit-Wochenstunden → Teilzeit-MA werden bei Auslastung und
   Resturlaub falsch gerechnet. **Nur relevant, wenn es Teilzeit-Monteure gibt — bitte bestätigen.**
10. **P2 FZ-Schaden Dual-Store.** Schäden werden in `fahrzeuge.schaeden` (JSON) UND `fz_schaeden` (Tabelle) geschrieben,
    aber Status-Edits + Read nur über die JSON-Spalte → `fz_schaeden` veraltet still. Kanonische Quelle klären (oder
    toten `_sbPost("fz_schaeden")` entfernen).
11. **P2 FinkZeit-Abweichungs-Schwelle inkonsistent.** Dashboard-Warnung: `diff>1h` (absolut). Detail-View: `<0,5h`
    grün / `<5%` orange / sonst rot (relativ). Gleiche Sache, zwei Kriterien → Dashboard-Zähler weicht vom Detail ab.
    Auf eine gemeinsame Schwelle einigen.
12. **P2 exportBauwochenbericht Sonntag.** Gather-Loop läuft Mo–Sa, Render-Loop 7 Tage → Sonntagsstunden fehlen im
    Kunden/ÖBA-Beleg + eine leere Phantom-Zeile. `generateBWB` (andere BWB-Variante) erfasst Sonntag dagegen.
    **Fachfrage:** soll Sonntag im Bauwochenbericht zählen? (Wenn ja: Gather auf 7 Tage; wenn nein: Render auf 6 → dann
    verschwindet auch die Phantom-Zeile.)
13. **P2 Zeiterfassung Inline „0 h" wird nicht gespeichert.** `updateEntryHours` persistiert nur `>0` → korrigiert
    ein Monteur eine Zeile auf 0, zeigt die UI 0, die DB behält den alten Wert (kommt beim Reload zurück).
    **UX-Entscheidung:** 0 als gültigen Wert speichern (PUT hours:0) ODER Eintrag löschen?
14. **P2 Bereichs-Urlaubsantrag ohne Overlap-Guard.** Ein Bereichsantrag/Typ-Wechsel über bereits **genehmigte** Tage
    setzt diese lokal auf „beantragt" zurück und sendet POST mit existierender id → 409. Fix: vorhandene `genehmigt`-Tage
    überspringen/warnen, bei Update PUT statt POST.

---

## D) Externe Integration (Backend-Encoding/Semantik bestätigen)

15. **P3 `_juprowaSanitize` unvollständig.** Ersetzt nur em-dash/quotes/€/…, lässt Emoji + nicht-Latin-1-Buchstaben
    (rumänisch ț/ș/ă, tschechisch č/ř — z. B. „Cracana") durch. Falls Juprowa/OFFA echtes Latin-1/CP1252 erwartet,
    bricht der Push oder erzeugt Mojibake. **Backend-Encoding bestätigen,** dann NFKD-Transliteration ergänzen.
16. **P3 Juprowa Status-Reverse-Map nicht roundtrip-stabil.** `4→freigegeben→1` und `15→bar_bezahlt→11`: ein gepullter
    Status 4/15 wird beim nächsten Push auf 1/11 umgeschrieben, auch ohne User-Änderung. **OFFA-Semantik klären** (sind
    4≠1 / 15≠11 fachlich relevant?), dann Dirty-Check statt bedingungslosem REV-Push.

---

## E) Sync-Layer (Risiko — separat angehen)

17. **P2 POST-Sync nicht idempotent.** Schreib-POSTs nutzen feste Client-`id`; geht die HTTP-Antwort verloren (Zeile
    aber geschrieben), schickt der Retry denselben POST → 409 → nach 5 Versuchen Drop + Falsch-Warnung „nicht
    synchronisiert" (Nutzer legt evtl. Duplikat an). Fix: generischen Schreib-POST auf `_sbUpsert`
    (`resolution=merge-duplicates`) umstellen — alle Bodies tragen bereits stabile `id`. **Sync-Kern-Änderung, testen.**
18. **P3 `_portalSync` (Kundenportal)** ohne Retry-/Drop-Logik → ein permanent fehlerhaftes Item (`break`) wedget die
    Portal-Queue. Auf die transient/permanent-Klassifikation des Haupt-`doSync` bringen.
19. **P3 `syncQueueFailed`** wird beim User-Wechsel mit-gelöscht → Sync-Diagnose-Daten des Vorgängers weg.
    Intent prüfen (evtl. aus `_USER_SCOPED_ODB_STORES` nehmen).

---

## F) Polish (autonom machbar, niedriger Wert — auf Zuruf)

20. **epkolar-files (public) Storage-Waisen.** v3.9.408 räumt nur die privaten Buckets. Ticket-Fotos/Pläne im
    public Bucket `epkolar-files` bleiben beim Löschen liegen. Helper `_sbDeleteObj(bucket,path)` ist generisch →
    in delPhoto/deletePlan/delDoc nachziehbar.
21. **React-Leaks (alle guarded/harmlos):** `_wmTimer` + Inline-QR-Scanner + `geoTimeout` ohne Unmount-Cleanup.
22. **a11y/UX:** PdfViewerModal + Signatur-/viewPdf-Modal ohne ESC/Focus-Trap; Zeit-Eintrag-Bottom-Sheet ohne
    Tap-outside-to-close (Hinweis „Esc schließt" ist auf Mobile irreführend).
23. **Suche-Konsistenz:** Token-AND-Suche nur in AS/Material, nicht in Projekte/User/Tickets/Gefahrstoff;
    Wochenplan-„Meine"-Substring-Namensmatch (Legacy-String-Zellen) kann fremde Zeilen treffen.
24. **Quota-Monitor** überwacht nur localStorage, nicht IndexedDB (wo die Offline-Foto-base64 liegen) — proaktiver
    „Speicher voll"-Toast feuert bei der echten Gefahr nicht (`navigator.storage.estimate()` nutzen).

---

## Eingefroren (NICHT anfassen)
- **VOffa / ZUZEIT.ASC** — OFFA-Lohn-/Zeitübergabe, Format unverifiziert.
- **FinkZeit `freigeben()`** ohne canUpload-Guard ist lohn-adjacent → bewusst NICHT autonom gehärtet (gehört zu
  „keinen Lohn-Punkt autonom anfassen"). Bei Bedarf 1-Zeilen-Guard `if(!canUpload)return;` analog `loeschen`.
