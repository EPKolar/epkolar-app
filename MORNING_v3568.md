# MORNING — Übergabe Overnight-Lauf (2026-06-29 → 30)

## ✅ GEFIXT + GEPUSHT 2026-06-30 (live **v3.9.575**)
- **#1 qDoSchaden** FZ-Schaden-Datenverlust → `3ed7d08` (572) · **#5 updSt kunde_status-Spiegel** → `db45153` (573) · **#2 SQ.push Quota-Warnung** → `5d54a33` (574) · **#4 Zeit-Edit-Guard (orthogonal)** → `3a4229a` (575). Je voller Gate (pytest 998/0, #4 mit den 4 Lohnpfad-Freezes explizit grün), eigener Commit. Versionen 570=A-2-Branch (ungepusht), 571=verworfener erster #4-Versuch (übersprungen).
- **PW-Rotation** `34kolar70` → durch Sebastian ausgeführt. Geteiltes Standard-PW eliminiert (5 Accounts je eigenes), git-History-Eintrag wertlos. Doku/Memory maskiert.

## ⚡ DAS MUSST DU ENTSCHEIDEN (Stand 2026-06-30)
1. **A-2 Juprowa-Fix freigeben?** Branch `a2-juprowa-roundtrip` (`b72742d`, v3.9.570), **nicht gepusht**, Dry-Run grün. Freigabe = Tabu-Auslegung `_juprowaReversMap` bestätigen + Merge/Push (= OFFA-Live-Push). **KEIN OFFA-Write bis dahin.**
2. **Dead-Code löschen?** **7 Funktionen sicher tot** (count=1: doJuprowaSync/FullSync/PushAll, getAllDescendantIds, _planClearPdfCache, _safeSessionSet, _titleCase) + `preview/whatsapp_ui_v0.html` (0 Refs). `getWeekplans` (count=1, aber `window.API` = extern aufrufbar → Vorsicht). **`toggleFZ` (6 Refs) + `_V` NICHT tot → NICHT löschen.** Nichts gelöscht — deine Entscheidung.
3. **Befund-only-Reste (NICHT autonom angefasst):** ⛔ #6 JWT base64url (`:1305`, **Auth**) · `_juprowaSanitize`/Juprowa-PULL-Zeit (`:3275/3085`, **OFFA**). Plus offene Korrektheits-Themen: BWB-KW-Kopf (`:20304`), Foto-Storage-Orphans (`:2801`), km_stand-Klobber (`:2188`), FinkZeit #11 (`:10346`), **Mobile-Wochenplan-Umbau** (`:16987` = Ur-Auftrag, größere isMob-Arbeit). Du wählst Reihenfolge.

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
