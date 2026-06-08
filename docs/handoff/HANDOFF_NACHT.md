# HANDOFF NACHT — EPKolar-App Session 2026-06-08 (Fortsetzung)

**Version-Range: v3.9.182 → v3.9.192.** main `bbea6c0` = origin/main = **v3.9.192 LIVE**, 726 pytest grün, Working-Tree clean (nur Alt-Junk untracked), Bracket `() -1`.
Repo: `T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app`. Supabase `jiggujpruejkaomgxarp`. **Autonomes Pushen auf main erlaubt.**

## FINAL-VERIFY (read-only, 2026-06-08, alle PASS)
| Check | Soll | Ist |
|---|---|---|
| Bracket index.html | () -1 | **() -1** ✓ |
| APP_VERSION | — | **3.9.192-supabase** |
| SW_VER / sw.js CACHE | — | **epkolar-v3.9.192** ✓ |
| pytest (letzter grüner Lauf) | grün | **726 passed, EXIT=0** ✓ |
| HEAD == origin/main | = | **`bbea6c0` == `bbea6c0`** ✓ |
| projects.plan_layers | jsonb | **vorhanden** ✓ (heute migriert) |
| Orphan-Audit 9 Kind-Tabellen | 0 | **0** ✓ |

## COMMITS DIESER SESSION (alle triade-gegated + gepusht)
| Version | Hash | Inhalt |
|---|---|---|
| 3.9.192 | `bbea6c0` | PlanRadar Zoom/Pan je Plan merken (localStorage epk_pv_) + Carry-over-Fix |
| 3.9.191 | `da9426f` | Mobile: Schnellerfassung-Modal Bottom-Sheet + Mehr-Menü Safe-Area |
| 3.9.190 | `912d4ba` | **Pläne#4 Ebenen-Persistenz pro Projekt** (projects.plan_layers jsonb) |
| 3.9.189 | `955e096` | PlanRadar Pin-Suche + Jump-to-Pin |
| 3.9.188 | `d0471ef` | PlanRadar Schnell-Status-Filter-Pills (Live-Count) |
| 3.9.187 | `f26132b` | Projekte-Lösch-Kaskade (9 Tabellen) + Mobile-Welle + Material/Vignette/Pin-Politur |
| (test) | `5a5a32b` | Zähler-Asserts an 187 nachgezogen (Suite 726 grün) — Korrektur nach Pipe-maskiertem Exit-Code |
| 3.9.185 | `3b7fc30` | Material-Gewerk-Filter sichtbar im Warenkorb (In-Kontext-Umschalter) |
| 3.9.184 | `5ea37bf` | **PlanRadar-Viewer Massiv-Upgrade**: Pin-Drag, Mausrad-Zoom, Vollbild, Shortcuts, Fit-Width, Status-Legende |
| 3.9.183 | `0c779a3` | **Vignette-Frontend** + Bug-Fixes (Projekte#3/#4, Pläne#6) + Material-Freitext-Position |
| (Basis) | `29f04ec` | Session-Start = v3.9.182 (Docs-Commit der Vorsession) |

## DB — APPLIED vs FILE-ONLY vs DEFERRED
- **APPLIED (live, diese Session):** `apply_migration projects_add_plan_layers` — `ALTER TABLE projects ADD COLUMN IF NOT EXISTS plan_layers jsonb` (verifiziert; projects HAT updated_at → kein PGRST204). Genutzt von Ebenen-Persistenz (`_persistLayers` → projects-PUT nur plan_layers).
- **APPLIED (Vorsession):** tickets.comments, fahrzeuge.vignette_typ/vignette_bis (Frontend dazu kam diese Session v3.9.183).
- **DEFERRED / bewusst NICHT gemacht:**
  - **FK `ON DELETE CASCADE`** auf projects-Kinder — **verworfen**: offline-SyncQueue kann Kinder VOR dem Parent syncen → strenge FK würde Child-Inserts abweisen (Sync-Bruch). Client-Kaskade (v3.9.187) ist die korrekte Wahl. Orphan-Audit = 0 → keine Altlasten.
  - **persist pageNum je Plan** — ausgelassen (kollidiert mit Load-setPageNum(1)); nur zoom/pan persistiert.

## LIVE-VERIFIKATION (Playwright, Produktion, read-only)
v3.9.192 deployed auf GitHub Pages, **0 Console-Errors**. Vignette rendert im Anlege-Formular (Label + 4 Typen). Plan-Viewer mountet fehlerfrei (Fit-Page/Vollbild/„Doppeltipp/Pin ziehen"-Hinweis da). Beide Live-Projekte haben **keine Pläne hochgeladen** → Pins/Pills/Suche live erst nach Plan-Upload sichtbar (Datenlage, kein Code-Bug). Keine echten Daten verändert.

## 🔴 STARTPUNKT NÄCHSTE SESSION: `docs/handoff/BUGHUNT-NACHT-FINAL.md`
13-Agenten-Bug-Hunt (6 Dim + 6 Verify + Synth, adversarial, zeilen-verifiziert) liefert die Work-Order: **1× P1 + mehrere P2/P3, alle test-sicher als additive Varianten** beschrieben. Top-Funde:
- **[P1] DOM-XSS in `genAsPdf`** (Zeile 6422): `kundName`/`nummer` werden via `JSON.stringify` in einen inline-`<script>` geschrieben → `</script>` im Kundennamen (Juprowa/Portal-Import) bricht aus. **Korrekter Fix (steht bereit, NICHT angewendet — Doc-only-Grenze):** die zwei `JSON.stringify(...)` auf 6422 mit `.replace(/</g,"\\u003c")` ergänzen (nur die eingebetteten Daten escapen). ⚠️ Die vom Synth vorgeschlagene `html.replace(/<\/script/...)`-Variante ist FALSCH (zerschösse das legitime schließende `</script>` @6427) — NICHT verwenden.
- **[P2] finkzeit PATCH clobbert** (15096/15102): `finkStunden` und `abgeglichen` teilen sich EINE text-Spalte `data`, Einzel-Key-Writes überschreiben sich → merge nötig (FinkZeit-Page nicht durch FINKZEIT_ENABLED gegated → live).
- **[P2] Cross-User-syncQueue-Bleed** (SQ.push 2512 / doSync): Queue-Items ohne owner → flushen auf geteilten Tablets unter fremder Session. Additiv: owner stempeln + nur eigene flushen.
- **[P2] Ticket-Typ-Wechsel desynct Defect-Spiegel** (updateTicket 11368): mangel↔nicht-mangel hinterlässt Geister-/fehlenden Defect → idempotenter Upsert.
- **[P2] QuickEditPin** (11201/11315): kein scroll-lock + kein Escape → additiver Effekt.
- **[P2] PlanViewer Escape** (11008): schließt nur Vollbild, nicht placing/pendingPin/newTicket; deps-Array 11018 `[isFs,pageCount]` → stale closure (newTicket/pendingPin/placing ergänzen).
- **[P3]** _OFFPW._derive empty-salt-crash (2478) · genBescheinigung Monat-Index (3337-3338) · Notif/Photo/Sync-Panel safe-area-top (5664/5737/5772) · Zeiterfassung addModal Bottom-Sheet mobil (17135/9744) · Mobile-Fullbleed-Modal-CSS tot (187/290).
Vollständig mit Datei:Zeile + Fix + Test-Caution in `BUGHUNT-NACHT-FINAL.md`. **Regel: Zeilen vor Edit per grep bestätigen (driften), Fixes additiv, Triade pro Welle, pytest-Exit aus DATEI prüfen (`| tail` maskiert Exit-Code!).**

## GOTCHAS (bestätigt diese Session)
- **`pytest | tail` maskiert den Exit-Code** → führte zu rotem Push f26132b (in 5a5a32b gefixt). Immer `pytest > file 2>&1; echo EXIT=$? >> file` und EXIT aus Datei lesen.
- Agenten-Funde: Zeilennummern ±daneben + gelegentlich halluziniert → IMMER per grep/Read gegenprüfen; sogar „safe"-Fix-Vorschläge können falsch sein (XSS-Beispiel oben).
- index_html-pytest-Fixture ist session-scoped (1× gelesen) → Editieren während laufendem pytest beeinflusst den Lauf NICHT (aber pollutet den Commit → trennen).
- DB-DDL = AskUserQuestion-Freigabe (diese Session für plan_layers erteilt).
- Edit „file changed since read" oft False-Trigger nach git/bump/Linter → Read-refresh + retry.

## NEUSTART
Neue CC-Session im Repo. First-read: dieses Doc + `docs/handoff/BUGHUNT-NACHT-FINAL.md` + Memory `epkolar-app-hunt-marathon-2026-06-04`.
