# FINDINGS — Bug- & Dead-Code-Hunt v3.9.568/569 (2026-06-29)

Frischer Hunt auf aktuellem Stand (NICHT der ~75% stale 17.06.-Backlog). Zwei Pässe:
**Pass 1** (Auth/Sync, RLS-Client, weekplan-Race, km_stand, React-#310, Lager-Kiosk, Juprowa, Version-Triple, Dead-Code) +
**Pass 2** (Race/Stale-Closure, Datum/Zeitzone, Zahlen/Währung, XSS/Injection, Rechte-Lücken/Fehler-Schlucker).
Jeder Fund: Zeile + Ist-Code-Beleg + Kategorie. **Nichts gefixt** (außer A-1 CLOSED + A-2 gestaged). Zeilennummern Stand v3.9.569 (`d065111`); bei Edits neu greppen.

---

# TEIL A — BUGS (nach Schwere)

## 🔴 HIGH
- **A-1 · Kiosk-PII-Leck — ✅ GESCHLOSSEN** (RPCs + Client v3.9.569 + RLS-Lockdown, live-verifiziert). Details `OPEN_BUGS_v3568.md`.

## 🟠 MEDIUM (Korrektheit)
- **A-2 · Juprowa Status-Roundtrip 4→1 / 15→11** · `index.html:3017/3244/3307` · `JUPROWA_STATUS_MAP` nicht-injektiv → Push schreibt gepullten OFFA-Status 4→1/15→11 zurück, auch ohne echte Änderung. **STAGED** Branch `a2-juprowa-roundtrip` (`b72742d`), Dry-Run grün, NICHT gepusht. → `HANDOFF_A2_juprowa_status_roundtrip.md`.
- **km_stand-Klobber nach unten** · `:21022/21042` (qDoTank/batchSave senden rohes `kmStand:entry.km`) + Server-Handler `:2188` (`patch.km_stand=km` bedingungslos, keine date/km-desc-Aggregation). Ein niedrigerer/offline-nachsyncender Beleg senkt den Tacho. Nur `_tankEditSave` (`:8429`) sortiert korrekt.
- **Juprowa-Import meldet Erfolg trotz fehlgeschlagenem Write** · `:3162/3167` · `try{await _sbPatch/_sbPost(...)}catch(e){console.warn}` — `_sbPost/_sbPatch` werfen bei non-OK (400/403/409), aber Zähler `updated++/added++` (`:3163/3168`) + Erfolgs-Toast laufen trotzdem → „X angelegt/aktualisiert" auch bei verlorenem AS. (Selbstheilend via autoritativen Pull, aber irreführend.)
- **Fahrtenbuch-Monatsabfrage Über-Fetch** · `:19553–19555` · `to=_ymd(new Date(new Date(from).getTime()+32*TIME_DAY))` → `to` landet 1–3 Tage im Folgemonat → fremde Einträge in der Monatsliste.

## 🟡 LOW / Korrektheit
- **weekplan Dirty/Deleted-Set-Leak im Drop-Pfad** · `:6405` vs `:6424` · verworfenes WP-SQ-Item entfernt row_id aus `__wpPendingRowIds`, aber nicht aus `__wpDirtyRowIds`/`__wpDeletedRowIds` → maskiert Server-Updates die Session lang.
- **`_fmtDatetime` UTC-Parse** · `:682` · `new Date("YYYY-MM-DD")` = UTC-Mitternacht → `getHours()` zeigt in Wien 01/02 statt 00 (Zeitteil falsch). Andere Stellen nutzen `+"T00:00:00"`.
- **Kalender-Wochentitel nicht-kanonische KW-Formel** · `:7888` · `Math.ceil(...ms-Division...)` statt der gefixten `_isoKW`/`_kwFromDate` → DST-1h kann KW an Wochengrenze kippen.
- **`reviewProgress`/`reviewDone` ungated** · `:12350/12355` · setzen `kunde_status` (customer-facing) per PUT ohne `if(!isAdmin)`; Buttons (`:12404/12406`) nur status-gegated, NICHT `isAdmin` — inkonsistent zu Triage-Geschwistern `reviewAccept`/`reviewReject` (die guarden).
- **Juprowa-Auto-Sync ohne Pending-Merge** · `:3176/3198` (5-Min-`setInterval` `:3214`) überschreibt `arbeitsscheine` direkt mit DB-Stand, anders als `loadAll` (`:6004+`, Pending-geschützt) → un-gedrainte lokale AS-Edits kurz zurückgesetzt bis nächster Merge.
- **EK-Summen ungerundet persistiert** · `:15598–15603/15754` · `grouped[key].total+=ek*menge` (eff mit vielen Nachkommastellen `:14977`) → DB-`total`/`effektiver_total` tragen Sub-Cent-Float-Rauschen; nur Anzeige rundet.

## 🔵 Defense-in-depth / Verdacht (kein akuter Handlungsbedarf)
- `updateTicket` (`:13421`) ohne Handler-Guard → Console-Bypass (Monteur fremd-zuweisen). Verdacht.
- `_placeOnPlan` (`:12309`), `setPlanGeschoss` (`:13378`) ohne Handler-Guard (nur Render-Gate). DiD.
- `notif_insert` `with_check=true` → lager_display könnte notifications INSERTen (DB-Policy). DiD.
- worker_projects/ROUTE_MAP generischer GET ohne Client-Scope (`:2096/2106`). DiD.
- Juprowa Doppel-Push-Race (`:3343` push_pending=Marker, kein Lock) + push_pending evtl. zu früh `false` (`:3369/3376`). Verdacht.
- `VCheck.update/del` (`:12086/12094`) + `_persistLayers` (`:13327`): SQ.push-Wurf verschluckt → Checklisten-Häkchen/Ebenen lokal sichtbar, serverseitig verloren. DiD.
- `<img src="${url}">` ungeescaped (`:7816/12263/18157`) + Signatur-`data:`-URLs (`:7821+`) — Bruch nur bei manipuliertem Server-Wert; Monatsabrechnung escapt korrekt (Inkonsistenz). Verdacht/DiD.
- PostgREST-Filter ohne `encodeURIComponent` bei Datums-Werten (`:2530/19039/19555`). DiD (Datumsformat erzwungen).
- `addEntry` Doppel-Tap-Guard nicht zurückgesetzt bei Validierungs-Bail (`:11583/11586/11589`, Klon `:20004+`) → 800ms-Lockout. UX.
- stündlicher `loadAll(true)` (`:8478`) nicht durch `_syncInFlight` gegated (Focus/Vis sind es). Verdacht.
- `effEk` Brutto-Fallback bei fehlendem Lieferant (`:14977`) → Preisvergleich verzerrbar. Verdacht.
- `.replace(',','.')` nicht tausender-fest / inkonsistente Liter-vs-Preis-Validierung (`:15161/4204/4207/21045`). DiD.
- DST-anfällige Restlauf-/Überfällig-`ceil`-Berechnungen (`:6315/10845/19450/21708` u.a.). DiD.

## ✅ Geprüft & ENTWARNT (sauber / Phantome)
- **Version-Triple** konsistent (`3.9.569`/`570`), 23 Tests grün · **React #310** kein Hook-nach-early-return · **Auth/Sync Silent-401** kein ungewrappter Write · **absence_files** RLS own-scoped (kein Leck) · **CSV/Excel/Print-Templates** durchgängig escaped (Formel-Injektion geschützt) · **kein** `eval`/`new Function` · Stunden-/%-Berechnungen NaN-/div0-sicher · ISO-Wochen-Kern-Helfer (`isoW`/`_isoKW`/`_kwFromDate`) DST-robust · Doppel-Submit breit via In-Flight-Refs abgedeckt.

---

# TEIL B — DEAD-CODE (nach Risiko) — NUR gelistet, NICHT gelöscht

## Niedriges Risiko — tot belegt (0 Aufrufe inkl. dynamisch geprüft)
| Element | Zeile | Beleg |
|---|---|---|
| `doJuprowaSync` | ~7365 | nur Def, kein onClick (Reste nach „v3.9.346 Buttons entfernt") |
| `doJuprowaFullSync` | ~7366 | nur Def |
| `doJuprowaPushAll` | ~7368 | nur Def |
| `getAllDescendantIds` | ~14429 | rekursiver Helper, nur Def |
| `_planClearPdfCache` | ~3527 | globaler Helper, nur Def |
| `_safeSessionSet` | ~1726 | nur Def (kein `_safeSessionGet`) |
| `_titleCase` | ~3286 | String-Helper, nur Def |
| `preview/whatsapp_ui_v0.html` | Datei | verwaistes 403-Zeilen-Artefakt, 0 Refs in index.html/sw.js |

## Vorsicht (Verdacht — vor Löschung verifizieren)
| Element | Zeile | Warum Vorsicht |
|---|---|---|
| `toggleFZ` | ~16323 | Wochenplan-FZ-Toggle — evtl. für Mobile-Wochenplan-Umbau gebraucht. NICHT löschen bis entschieden. |
| `getWeekplans` | ~2535 | auf `window.API` exponiert → theoretisch extern aufrufbar |
| `_V` | ~4055 | Theme-Accessor, sehr kurzer Name → konservativ Verdacht |
| `supplier-sync` Edge-Fn | Repo+DB | client-seitig 0× aufgerufen, aber deployed → Dashboard/Cron-Aufruf vor Entfernen klären |
| supplier-sync Sync-Body-Stub | `functions/supplier-sync/index.ts:130-136` | intentionaler Platzhalter (`rows=[]`), kein „tot"-Löschen |

## Hinweis
Zeilennummern aus Pass 1 (vor v3.9.569-Shift) mit `~` markiert — vor Löschung neu greppen. **Löschen entscheidet Sebastian** (Hard-Stop: kein autonomes Code-Löschen).

---

# PASS 3 — Nachtrag (5 weitere Dimensionen)

## 🟠 MEDIUM / Korrektheit
- **`SQ.push` stiller Datenverlust bei IndexedDB-Quota** · `:2748` (+`:2696/2751`) · `ODB.save` schluckt jeden Fehler (`catch console.warn`), `SQ.push` warnt nur in Konsole, kein Aufrufer prüft Return. Bei `QuotaExceededError` wird die Offline-Änderung **nicht gequeued, kein Toast/Banner** → stiller Verlust. PhotoQ wurde genau dafür gehärtet (`:2778/2833`), SQ.push NICHT. **Höchster Realwert in Pass 3.**
- **Nicht-idempotenter POST → Duplikate** · `:2377` (vs `:2376`) · roher `_sbPost` (kein `resolution=`-Header, `:1951`) für ALLE Tabellen außer arbeitsscheine; Bodies tragen feste Client-`id`. Verlorene HTTP-Antwort → Re-POST → 409/23505 → nach 5 Drop + Falsch-Warnung „verworfen", obwohl Zeile in DB → User legt Duplikat an. Idempotenz (`_sbInsertIfAbsent`) nur für arbeitsscheine verdrahtet. (= altes Backlog #17, bestätigt.)
- **JWT base64url-Decode schlägt still fehl** · `:1305/5838/6348` (+`:740/1369/1375`) · `atob(token.split('.')[1])` OHNE `-/_`→`+/`-Konvertierung (die `:1287` korrekt macht) → bei JWTs mit `-`/`_` wirft `atob`, role/exp-Prüfung im try/catch schlägt **still** fehl (curuser-recover, anon-Refresh übersprungen). **Passt zum dokumentierten „3× 401"-Symptom.**
- **`_juprowaSanitize` unvollständiges Latin-1** · `:3275` · ț/ș/ă/č/ř + Emoji bleiben durch → AK_ARBEITEN/NOTIZ/BAUADR_NAM1 (Kundenname „Cracana") bei echtem CP1252 auf OFFA → Mojibake/Push-Bruch. **OFFA-relevant** (zu A-2-Komplex).
- **BWB KW-Zeitraum-Kopfzeile schließt Sonntag aus** · `:20304` · `exportBauwochenbericht` rendert 7 Tage inkl. Sonntag mit Stunden, Kopf zeigt aber `dateFmt(0)–dateFmt(5)` (Mo–Sa, müsste `dateFmt(6)`). Plus kosmetisch leere Sonntag-Phantomzeile (`:20274`).
- **Auslastungs-Widget zählt Zukunfts-Stunden** · `:19126` · Filter nur `>=_weekStart`, kein `<=_weekEnd` → % überhöht; Kapazitäts-Widget (`:19284`, korrekt gebounded) zeigt für denselben MA grün.

## 🟡 LOW / Defense-in-depth / Verdacht
- Auslastungs-Ampel-Inkonsistenz (`:19127` fix 38,5 vs `:19284` feiertags-korrigiert) → in Feiertagswochen zwei Ampelfarben für denselben MA.
- **Teilzeit ignoriert** (`:19021 _stdVonTagBrk` 8,5/4,5 + `:19276/20087` 38,5 hartkodiert) — **NUR relevant wenn Teilzeit-Monteure existieren** (aktuell 38,5 Default überall → latent/Folge-Ticket). Bestätigung nötig.
- SQ Falsch-Erfolgszählung: gedroppte Items im „N synchronisiert"-Toast mitgezählt (`:6443`).
- Cross-User-Queue-Verlust bei Logout auf Leihgerät (`:6624` `SQ.clear()` = alle Owner).
- `syncQueueFailed` beim User-Wechsel gepurgt → Drop-Diagnose des Vorgängers weg (`:6798`). DiD.
- Orphaned PUT nach POST-Drop → `_sbPatch` auf nicht-existente id = 200+leer = stiller No-Op (`:2378`). Verdacht.
- OCR-Parser `substring(indexOf("Monteur:"))` ohne -1-Guard → stilles Falschergebnis bei Format-Drift (`:3571`). Korrektheit.
- AK_TERMIN nimmt `terminZeit`=HH:MM an → bei HH:MM:SS ungültiges Format (`:3300`). Verdacht.
- Resturlaub hängt vom Antrags-UI ab (Kalender `beantragt` zieht sofort ab, `urlaubsantraege` erst bei Genehmigung) (`:17283` vs `:19046`). Verdacht (evtl. gewollt).
- Materialisierung-Dedupe über Namens-Key fragil (`:19030/19034`) → Doppel-Insert bei Namens-Divergenz. Verdacht.

## ✅ Pass-3 ENTWARNT
- **Memory/Timer/Listener-Cleanup:** außergewöhnlich sauber — Kamera/MediaStream-Scanner (getTracks().stop()), rAF (cancel), WakeLock, Geolocation (AbortController), alle Debounce-Timer-Maps symmetrisch aufgeräumt. Kein Leak. (Nebenbefund: IntersectionObserver-Lazy-Wrapper `:18646` = toter Code.)
- **BWB Gather/Render:** beide Zwillinge 7-tägig + summenkonsistent (alte „Gather-6/Render-7"-Vermutung existiert NICHT). Wochenplan-Export bewusst 6-tägig korrekt.
- **Urlaub-Kern:** Overlap-Guard vorhanden (`:17280` skip genehmigt + PUT statt POST), Krankenstand/Urlaub-Matching getrennt, Halbtage/Feiertage korrekt.
- **Parsing:** `_safeJsonParse` robust, KEINE `new RegExp(userInput)` (keine RegExp-Injection), ~40 JSON.parse durchgängig guarded.
- `_onAuthFail(403)` reißt Session/Queue NICHT ab (nur warn+return).
