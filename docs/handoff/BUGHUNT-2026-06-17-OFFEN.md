> # ⚠️ STALE — ~75% überholt (Stand 2026-06-29, v3.9.568/569)
> Dieser Backlog ist durch den frischen Hunt-Pass auf v3.9.568 weitgehend abgelöst. Verifiziert:
> **A1** (ocr_tankbeleg Auth+Size-Limit) = bereits live seit v3.9.419 · **B5/B6** (markAllRead /
> GET notifications user_id-Filter) = bereits gefixt (v3.9.53/420) · **B034** (tickets.page Spalte)
> = existiert längst in der DB · **A3** (admin-create-user Rollback) = tote, nicht deployte Edge-Fn,
> 2026-06-29 aus dem Repo entfernt. **A2** (supplier-sync set-credentials Validierung) = gefixt+committet.
> **Einziger echter offener Bug aus diesem Dokument-Kontext + neuer Hunt:** Juprowa-Status-Roundtrip —
> siehe `OPEN_BUGS_v3568.md` + `HANDOFF_A2_juprowa_status_roundtrip.md`. Aktuelle Befundliste: `FINDINGS_v3568.md`.

# Bug-Hunt-Marathon 2026-06-17 — OFFENE Punkte (Sebastian-Entscheidung / Backend)

> **UPDATE nach Erstellung (Stand v3.9.418):** Seit diesem Dokument zusätzlich autonom
> behoben+gepusht (v3.9.416–418): a11y (PdfViewerModal-ESC, Zeit-Sheet-Tap-outside);
> **2× P1 Datenverlust** „Reload überholt Sync" in BWB-Büro-Edit (editMonteurEntries +
> openMultiEntryEdit → `_syncThenReload`); Dashboard-6-Monats-Chart `setMonth`-Overflow;
> Fleet-Service-Termin + Pickerl-Badge Timezone; **2× P1 DB-Schema-Mismatch** (read-only
> gegen jiggujpruejkaomgxarp verifiziert): `time_entries.stunden` existiert nicht →
> Phantom-Feld entfernt; `arbeitsscheine` hat `unterschrift_monteur/_kunde` statt
> `sig_ma/sig_kunde` → in-App-Signatur war funktionslos (0/100 AS signiert), jetzt
> AS-scoped gemappt. **Schema-Fakten:** time_entries={hours real, KEIN stunden};
> arbeitsscheine={unterschrift_monteur text, unterschrift_kunde text}.
> **NEU offen (unten ergänzt):** G1 AS-Voll-Row-PUT Lost-Update, G2 focus/visibility-
> Reload-Clobber, G3 "Heutige AS"-KPI-Status.

Stand: main = origin = **v3.9.441** (war v3.9.415 bei Erstellung).

> **UPDATE 3 (v3.9.437–441, „weiter was offen ist"-Lauf, Sebastian-Entscheidungen via AskUserQuestion):**
> Erledigt+gepusht (je Commit+Triade, 957 pytest grün):
> - **#13 (v3.9.437)** Zeiterfassung Inline „0 h" → **Eintrag LÖSCHEN** (Chef-Entscheid) statt still No-Op
>   (DB behielt alten Wert). DELETE + entries-Prop + dayEntries, ohne Modal (800ms-Debounce schützt).
> - **#12 (v3.9.438)** Bauwochenbericht **zählt Sonntag mit** (Chef-Entscheid): lokale 7-Tage-Woche
>   `BWB_DAYS` nur in exportBauwochenbericht (Gather+Review+Render i<7), globale `DAYS` bleibt Mo-Sa
>   (Matrix/Wochentabelle/Tages-Stz unberührt). Konsistent mit generateBWB.
> - **#24 (v3.9.439)** Quota-Monitor deckt jetzt **IndexedDB** ab (`navigator.storage.estimate`,
>   origin-weit) → „Speicher voll"-Toast feuert vor dem echten QuotaExceededError; läuft im 5-min-Timer.
> - **#14 (v3.9.440)** Urlaubs-**Bereichsantrag Overlap-Guard**: genehmigte Tage überspringen+melden,
>   existierende Tage via PUT statt POST (kein 409, kein lokaler Reset genehmigter Tage).
> - **#23 (v3.9.441)** **Token-AND-Suche** jetzt auch in Projekte/User/Tickets/Gefahrstoff (wie AS/Material).
> - **#9 Teilzeit GESCHLOSSEN** (Chef: alle Vollzeit) → 38,5h-Annahme bleibt, kein Code.
>
> **NOCH OFFEN (bewusst nicht autonom):** #17 POST-Sync idempotent (Sync-Kern, Risiko → braucht Go +
> Test), #21 React-Leaks (guarded/harmlos, optional), Backend-Edge-Fns #2 supplier-sync / #3
> admin-create-user (Deploy nötig), D) Juprowa-Encoding/Reverse-Map (Backend-Semantik bestätigen),
> eingefroren: VOffa/ZUZEIT.ASC + FinkZeit-freigeben.

> **UPDATE 2 (v3.9.419–423, „fix all bugs"-Lauf):** Autonom behoben+gepusht:
> A1 **ocr_tankbeleg Auth+Bildlimit** (Edge-Fn fixed+LIVE deployed v5, Smoke: anon→401)
> · BWB-Phantom-Sonntagszeile (Render-Loop Mo-Sa) · B6 **Notif-GET user_id-Filter**
> (Staff-Cross-User, schema-verifiziert) · G1 **AS Diff-PUT** (Lost-Update behoben) ·
> _portalSync transient/permanent-Split (Queue-Wedge weg) · epkolar-files Waisen-Cleanup
> (Foto/Plan/Doc best-effort). B5 (markAllRead 0-Row) verifiziert gegenstandslos.
> **ENTSCHIEDEN + umgesetzt (v3.9.424/425):** Budget-Ampel → Option 1 (echter Stundensatz
> + €85-Pauschalfallback nie 0, budget_euro-Basis, Schwellen 85/100, UI-Hinweis) ·
> Auslastungs-Ampel → beide 70/90/100 · „Heutige AS"-KPI → nur offene (AS_GRP_OFFEN) ·
> FinkZeit-Schwelle → bleibt wie ist (Chef-Entscheid).
> **NOCH OFFEN (Entscheidung):** Teilzeit-Soll (workers hat KEIN Wochenstunden-Feld,
> urlaubskontingent leer → Feld einführen ODER 38,5h-Annahme behalten?) · FZ-Schaden-
> Dual-Store (kanonische Quelle? liest ein Report fz_schaeden?) · Juprowa-Encoding (TABU).
> Verbleibend low-value/optional: G2 focus/visibility-Reload-Clobber (eng, selbstheilend),
> React-Leaks (_wmTimer/geoTimeout, guarded/harmlos), Quota-IndexedDB-Monitor, Such-Token-AND. 9 Fix-Batches autonom gepusht (v3.9.407–415), 931 pytest grün,
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
10. **~~P2 FZ-Schaden Dual-Store~~ — ✅ STALE/ERLEDIGT (Fall A, server-seitig verifiziert 2026-06-30).** KEIN
    Dual-Store mehr: Tabelle `fz_schaeden` existiert physisch NICHT (information_schema/pg_class →
    KEINE_RELATION, nicht nur PGRST205; entfernt v3.9.427/432). `fahrzeuge.schaeden` (Spalte type `text`,
    JSON-serialisiert) ist die einzige/kanonische Quelle, aktuell leer (0/21 Fahrzeuge). Code-Seite: nur
    JSON-Lese/Schreibpfade (`addSchaden`/`_schSync` Diff-PUT), die 7 `fz_schaeden`-Treffer sind 1 Label-String
    + Kommentare zur Entfernung. Nichts zu droppen, nichts zu migrieren. *(Ursprünglich:)* Schäden wurden in
    `fahrzeuge.schaeden` (JSON) UND `fz_schaeden` (Tabelle) geschrieben, aber Status-Edits + Read nur über
    die JSON-Spalte → `fz_schaeden` veraltet still.
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

## G) Neu gefunden (Welle 5) — strukturell/Entscheidung, nicht autonom gefixt

- **G1 (P2) AS-Edit ist Voll-Row-PUT → Lost-Update.** `saveAs` (~Z.6877) sendet das
  komplette `_finalForm` per PUT. Läuft parallel ein Juprowa-Auto-Sync oder eine
  Zweit-Bearbeitung (aktualisiert `juprowa_*`/andere Felder serverseitig), während der
  Editor mit altem Stand offen ist, überschreibt der stale Client-Stand alle Spalten →
  verlorene Server-Updates. Fahrzeuge/Material sind bereits auf column-scoped Diff-PUTs
  umgestellt; AS-Edit ist der verbliebene Voll-Row-Clobber. Fix: nur geänderte Felder
  diffen/senden (Muster `_svcSync`) bzw. `juprowa_*` nie aus Client-Stand mitschreiben
  außer im Push-Zweig. (Strukturell + legal-doc → mit Live-Test angehen.)
- **G2 (P2) focus/visibility-Reload clobbert optimistischen Matrix-Wert.** Die
  `visibilitychange`/`focus`-Listener (~Z.7623) rufen `loadAll(true)` und überschreiben
  `allEntries` komplett. Editiert man eine BWB-Zelle und wechselt innerhalb des ~3,2s-
  `_syncThenReload`-Drain-Fensters kurz zu Excel/Outlook und zurück, zieht das fremde
  `loadAll` den noch-nicht-geschriebenen Server-Stand → Wert „flackert/verschwindet kurz"
  (selbstheilend nach Drain). Fix: `_syncInFlight`-Ref setzen während `_syncThenReload`
  läuft, und in den Listenern `loadAll` überspringen/verzögern wenn `SQ.count()>0`.
- **G3 (P3) „Heutige AS"-KPI** (Chef-Portal ~Z.17508) zählt ALLE Scheine mit heutigem
  Termin inkl. erledigt/abgerechnet/storniert; die Nachbar-Kennzahl `ueberfaellige` filtert
  dagegen `AS_GRP_OFFEN`. Inkonsistent. **Entscheidung:** „heute offen" (dann
  `&&AS_GRP_OFFEN.includes(scheinstatus)`) oder „alle heutigen" (dann so lassen)?

## Eingefroren (NICHT anfassen)
- **VOffa / ZUZEIT.ASC** — OFFA-Lohn-/Zeitübergabe, Format unverifiziert.
- **FinkZeit `freigeben()`** ohne canUpload-Guard ist lohn-adjacent → bewusst NICHT autonom gehärtet (gehört zu
  „keinen Lohn-Punkt autonom anfassen"). Bei Bedarf 1-Zeilen-Guard `if(!canUpload)return;` analog `loeschen`.
