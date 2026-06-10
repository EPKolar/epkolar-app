# Hunt-Welle 1+2 (2026-06-10) — Server-/RLS-seitige Findings für Chat-Claude

Adversarialer Agenten-Bughunt über die ganze App (`index.html`), 41 bestätigte Funde.
Die **Code-Funde** (Datenverlust/Logik) sind in v3.9.252–256 bereits gefixt + live (CC).
Diese Datei sammelt die Funde, deren **saubere Lösung serverseitig** liegt (RLS / Optimistic-Concurrency)
— bewusst KEIN Client-Patch, weil Client-Gates umgehbar sind bzw. ein Client-Merge Daten gefährden würde.

DB: Supabase `jiggujpruejkaomgxarp`. Helfer im Projekt: `current_user_role()`, `is_staff()`.

---

## A) Permission / RLS — Client-Gate ist umgehbar, Durchsetzung fehlt serverseitig

Alle folgenden Schreibpfade laufen über den generischen PATCH/POST (`/api/<table>/:id` → `_sbPatch`/`_sbPost`)
und tragen KEINE Rollendurchsetzung. Ein authentifizierter interner User (Monteur/Helfer mit
`hasPerm('arbeitsscheine'/'maengel')`) kann via DevTools/SyncQueue direkt schreiben.

1. **defects / Mängel-Status** — `updSt` (~Z.6509), `reviewProgress` (~Z.10536), `reviewDone` (~Z.10541),
   `reviewAccept`/`reviewReject` (~Z.10518+). Monteur kann Kunden-/Review-Status frei setzen.
   → RLS auf `defects` (und gespiegelte Mängel): UPDATE von `kunde_status`/`review_*`/`status`
   nur für `current_user_role() in ('admin','projektleiter','buero')` bzw. Owner.

2. **arbeitsscheine — Inline-Selects** (Status/Monteur/Termin, `updAs` ~Z.6338). Form-`saveAs` hat
   Monteur-Guards (kein Anlegen, keine Fremdzuweisung), die Listen-Inline-Controls NICHT.
   Ein Monteur kann eigene Scheine einem anderen Monteur zuweisen / Status frei setzen.
   → RLS auf `arbeitsscheine`: UPDATE `monteur`/`scheinstatus` rollen-/ownership-geprüft.

3. **Kundenportal-Sync ohne Owner-Filter** — `_portalSync` (~Z.4329) überschreibt `window.__doSync`
   und flusht ALLE SyncQueue-Items im anonymen Portal-Kontext (keine Owner-Begrenzung).
   → sicherstellen, dass anon-Portal-Rolle per RLS nur die freigegebenen eigenen Datensätze schreiben darf;
   ideal Client zusätzlich: im Portal-Kontext nur portal-eigene Queue-Items flushen.

4. **`hasPerm`/`canDo` prüfen `user.active` nicht** (~Z.3804-3814). Ein in der laufenden Session
   deaktivierter User behält Client-Berechtigungen bis zum Reload.
   → Server: GoTrue/RLS muss Writes deaktivierter User ohnehin ablehnen (Quelle der Wahrheit).
   Client-Härtung (active-Check in hasPerm) ist optional als Defense-in-Depth möglich.

---

## B) Optimistic-Concurrency — Voll-Row-Writes ohne Versionsprüfung (Lost-Update)

Architektonisch: Formular-Editoren snapshotten die Zeile beim Öffnen und schreiben beim Speichern
die ganze Form zurück. Ohne Versions-/Timestamp-Prüfung gehen zwischenzeitliche Änderungen
(anderes Gerät, Inline-Edit, Juprowa-Pull) verloren. Ein Client-Merge ist hier riskant
(Stale-Snapshot ≠ „unverändert"), daher serverseitig lösen.

5. **Arbeitsschein `saveAs`** (~Z.6334) — PUT mit kompletter Form-Row. Clobbert parallele Inline-/
   Pull-/Fremdgeräte-Änderungen an derselben Zeile (durchgefuehrte/notizen/scheinstatus/termin …).
   → Empfehlung: Spalte `local_updated_at`/`version` auf `arbeitsscheine`; conditional UPDATE
   (`WHERE id=… AND updated_at = <snapshot>`); bei 0 rows → Client warnt „inzwischen geändert, neu laden".
   Alternativ feldgranulare Saves. (Juprowa-Push-Pfad `_juprowaPush` NICHT anfassen.)

6. **Monatsabrechnung-Reload-Merge** (StundenzettelView, ~Z.15351) — Lade-Effekt ersetzt bestehende
   Zettel und kann eine frischere DB-Version durch lokal-stale verdrängen (cross-device).
   → Merge by `updated_at` (jüngere Version gewinnt) bzw. pending-Overlay beim Reload.
   `finkzeit` hat KEINE `updated_at`-Spalte (s. _translateAndExec-Blacklist) → ggf. Spalte ergänzen.

---

## Hinweis
Die reinen Code-Datenverlust-/Logik-Funde aus demselben Hunt sind bereits behoben (CC, v3.9.252–256):
Fahrzeug-Voll-Row-Clobber (10 Pfade), Export-Doppelsumme, Urlaub-Typ-Wechsel-409,
Material-PV-Persistenz, Werkzeug-Service-Delete-Resurrection, Bautagebuch-Temp-0°C.
Vollständige Fund-Liste (41) im Hunt-Output / Session-Log.
