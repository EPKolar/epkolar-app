# MORNING — Übergabe Overnight-Lauf (2026-06-29 → 30)

## ⚡ DAS MUSST DU ENTSCHEIDEN (oben, kurz)
1. **A-2 Juprowa-Fix freigeben?** Liegt fertig + verifiziert auf Branch `a2-juprowa-roundtrip` (`b72742d`), **nicht gepusht**. Freigabe = (a) Tabu-Auslegung `_juprowaReversMap` bestätigen, (b) Deploy erlauben → ermöglicht echten OFFA-Push. **Dry-Run unten ist grün.**
2. **Dead-Code löschen?** 8 tot-belegte Elemente + 1 verwaistes File (Liste in `FINDINGS_v3568.md` TEIL B). Nichts gelöscht — deine Entscheidung. `toggleFZ` NICHT löschen (evtl. Mobile-Wochenplan).
3. **Welche Korrektheit-Bugs als nächstes?** (alle in `FINDINGS_v3568.md`, keiner gefixt). Top-Kandidaten nach Realwert:
   - **🔴 `qDoSchaden` ohne `SQ.push`** (`:21035`) — FZ-QR-Schadenmeldung wird NIE gespeichert, Datenverlust. (Pass 4, klar live-brechend, kleiner Fix.)
   - **`updSt` ohne `kunde_status`-Spiegel** (`:12308`) — Kunde sieht Abnahme-Button nicht. (Pass 4, kundenrelevant.)
   - **`SQ.push` stiller Quota-Datenverlust** (`:2748`) — Offline-Änderung geht ohne Toast verloren bei vollem IndexedDB. (Pass 3, höchster Realwert.)
   - **JWT base64url-Decode still fehlerhaft** (`:1305/5838/6348`) — passt zum „3× 401"-Symptom. (Pass 3.)
   - **Nicht-idempotenter POST → Duplikate** (`:2377`) — verlorene Antwort = Doppel-Eintrag. (Pass 3, = altes Backlog #17.)
   - km_stand-Klobber (`:2188`), Juprowa-Import-Silent-Success (`:3162`), Fahrtenbuch +32-Tage-Überfetch (`:19553`), reviewProgress ungated (`:12350`), BWB-KW-Kopfzeile (`:20304`), Auslastung-Zukunftsstunden (`:19126`).
   - **`_juprowaSanitize` unvollständiges Latin-1** (`:3275`) — OFFA-Mojibake, gehört zum A-2/OFFA-Komplex (zusammen freigeben?).

---

## ✅ COMMITTET + GEPUSHT (Doku auf main, kein index.html, kein Live-App-Change)
- `docs/handoff/BUGHUNT-2026-06-17-OFFEN.md` — Stale-Kopfnotiz (~75% überholt; A1/B5/B6/B034/A3 erledigt/tot).
- `OPEN_BUGS_v3568.md` — einziger echter offener Bug = A-2; PII-Leck CLOSED dokumentiert.
- `FINDINGS_v3568.md` — komplette Befundliste beider Hunt-Pässe (Bugs nach Schwere + Dead-Code nach Risiko).
- `HANDOFF_A2_juprowa_status_roundtrip.md` — A-2-Detail + Fix-Diff + Tabu-Klärung.
- `KIOSK_PII_RPCS_stage.sql` + `KIOSK_PII_LOCKDOWN_stage.sql` + `AUTH_FIX_buero_gotrue_2b.sql` — angewandte prod-SQL als Record.
- (main HEAD nach Push siehe `git log`; origin/main == lokaler main.)

## 📦 GESTAGED (NICHT gepusht / NICHT angewandt)
- **A-2-Fix:** Branch `a2-juprowa-roundtrip`, Commit `b72742d` (v3.9.570). Ändert `index.html` (Builder `_juprowaReversMap:3307`) + sw.js + `scripts/a2_dryrun.mjs`. `_juprowaPush` unberührt. Voller Gate grün (node-check 0, bracket-Baseline, pytest 998, Version-Triple 3.9.570). **main bleibt sauber bei origin (d065111).**
- **Dead-Code-Löschliste:** in `FINDINGS_v3568.md` TEIL B — nur gelistet, nichts gelöscht.

## 🔒 BRAUCHT DEINE FREIGABE (nie autonom gemacht)
- A-2 Live-Deploy + erster echter OFFA-Push (Hard-Stop eingehalten: kein OFFA-Write heute).
- Dead-Code-Löschungen.

---

## A-2 DRY-RUN ERGEBNIS (scripts/a2_dryrun.mjs — kein OFFA-Kontakt)
```
ROUNDTRIP (gepullter Code -> App-Status -> Push unveraendert):
 CODE | App-Status     | OLD | NEW | stabil?
  0 aufgenommen   0  0  YES      4 freigegeben   1  4  YES   ← Fix: 4 bleibt 4 (alt: 4→1)
  1 freigegeben   1  1  YES      5 erledigt      5  5  YES
  2 aufgeschoben  2  2  YES     10 abgerechnet  10 10  YES
  3 in_bearbeitung 3 3 YES      11 bar_bezahlt  11 11  YES
                              15 bar_bezahlt  11 15  YES   ← Fix: 15 bleibt 15 (alt: 15→11)
                              20 storniert    20 20  YES
=> Injektiver Roundtrip ueber alle 10 Codes: BESTANDEN
Echte Aenderung: freigegeben->erledigt = 5 ✓ | ->storniert = 20 ✓ | Fallback ohne raw = 1 ✓
```

## So gibst du A-2 frei (morgen)
1. Dry-Run gegenprüfen: `node scripts/a2_dryrun.mjs` (auf Branch `a2-juprowa-roundtrip`).
2. Branch nach main mergen: `git checkout main && git merge a2-juprowa-roundtrip` → push.
3. GitHub Pages-Build abwarten, dann an EINEM Juprowa-Schein einen Push triggern und in OFFA prüfen dass Status 4/15 erhalten bleibt.

## Stand Hunt
Drei Pässe abgeschlossen (9 Agenten Pass 1 + 5 Pass 2 + 5 Pass 3). Autonomer Weiter-Hunt läuft bis dein „stop".
Codebasis auffällig defensiv gehärtet — Memory-Leaks/XSS/Zahlen/Race/Datums-Kern-Helfer weitgehend sauber.
Die wertvollsten neuen Funde stecken in **Sync-Queue/Offline** (`SQ.push`-Quota-Verlust `:2748`, Nicht-Idempotenz `:2377`), **Auth** (JWT base64url `:1305`) und **OFFA-Encoding** (`_juprowaSanitize` `:3275`). Voll in `FINDINGS_v3568.md`.
