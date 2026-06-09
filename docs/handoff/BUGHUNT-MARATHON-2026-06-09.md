# Bug-Hunt-Marathon 2026-06-09 — Abschluss + Backlog

**Stand:** main HEAD `78b5b70` = **v3.9.225**, 726 pytest grün, Triade je Welle grün, alles gepusht.
**Methode:** 6 read-only Finder-Wellen (je 6 Dimensionen) → adversariale Synthese → seriell gefixt → Triade+Push pro Welle. DB read-only, kein Live-Browser-Write.

## Live gefixt (v3.9.213 → 225)
**Auth-Resilienz (213–218):** login_lookup-Hash-Abhängigkeit entfernt (GoTrue-only) + authentifizierter Profil-Self-Read · 403≠Session-Ablauf · kein Logout solange Access-Token gültig · Cross-Tab-Token-Übernahme · Refresh-statt-anon-Key · Reload-Loop-Zeitschutz · 403→HTTP403.
**Bug-Hunt (219–225), Schwerpunkt Datenverlust:**
- Checkliste-items-POST (Reload-Verlust) · RMW-transient-Drop (serviceheft/tank/km/WZ) · Save-Clobber `useEditable`/`FRegie` (parallele Geräte) · **MAT_KATALOG-Verlust** · **Mängel-Poll-Korruption (jede 60s, `_mapDefect`)** · **Foto-Verlust bei vollem Speicher (PhotoQ-Quota)** · Cross-User-meta-Leak.
- notif read-all/clear throw statt {ok:0} · Glocken-Klick `deadline_fz` · juprowa `.catch` · Kunde-Notif `melder` · **Doppel-Material-Bestellung** (sendOrder-Guard) · deleteOrder-Guard.
- `_pickerlStatus`/serviceFaellig Datum-UTC-Fix · Wochenstunden-Zeilencap · generateBWB-esc · BWB-Spaltenkopf-Kollision · DATANORM-Toggle-Auswahlverlust · 2× A11y (Checklisten-/Kompetenz-Toggle tastaturbedienbar).

## 🔴 Review-Backlog — braucht Chef-/Sebastian-ENTSCHEIDUNG (NICHT blind gefixt)
1. **Urlaub→Kontingent-Brücke (P1):** Genehmigte Anträge im Antrags-Panel werden nie vom Resturlaub abgezogen (zwei getrennte Datenflüsse `urlaubsantraege` vs `absences`). Soll Panel-Genehmigung Kalender-`absences`-Einträge erzeugen?
2. **Cross-Year-Wochenplan (F3):** `wpHistory` nur per KW-Nr gekeyt → Jahresgrenzen-Kollision. Multi-Site State-Key-Refactor (HomeView + `Object.keys().map(Number)` + IDB), eigener PR.
3. **„Alle genehmigen" über Jahre:** genehmigt Vorjahres-Ausstände mit (`allEntries` Z~14604) — Approval-Panel auf lfd. Jahr begrenzen? (fachlich: dürfen Vorjahres-Anträge noch genehmigt werden?)
4. **Approval-Reset bei Typwechsel:** Urlaub→ZA/Krank behält „genehmigt".
5. **Mangel-Tab → Plan-Pin asymmetrisch:** VMang-Edit/Delete spiegelt nicht zum Plan-Ticket (Geister-Pin). Braucht `setPlanData`-Prop-Threading.
6. **tickets.type / tickets.due_date** werden nie persistiert — **zuerst DB-Spalten-Check** (`tickets.type`, `tickets.due_date`), sonst POST-400.
7. **Bestell-Lücke:** Positionen ohne Händler-Match (`grouped["_manual"]`) werden still nicht bestellt, Status sagt „bestellt".
8. **FZ/WZ-Voll-PUT-Clobber (P1, bekanntes Architektur-Defer):** Fahrzeug-/Werkzeug-Detail-Save PUTtet Vollobjekt → überschreibt parallel dazugekommene km/tank/schaeden/serviceheft. Lösung: Mutatoren auf inkrementelle Ops umstellen (wie Scan-Pfad). 
9. **JUPROWA Status-Roundtrip-Drift (P1):** Pull n:1 (4→freigegeben/15→bar_bezahlt), Reverse 1:1 (→1/→11) + unbedingter Autopush bei jedem Save → 4→1 / 15→11. Braucht JUPROWA-Status-Semantik (Sebastian) + Drift-Guard via `juprowa_raw.AK_AUFSTATUS`.
10. **Kamera-Leak (P2):** Inline-QR-Overlay (Werkzeug-Inventarnr, ~Z19221) ohne Unmount-Cleanup → Kamera läuft bis 30s weiter + z-index-Overlay blockt. Closure→Ref-Refactor (riskant, daher Review).
11. **PlanRadar Zoom-Fokusdrift (P3):** 4 Cursor-Zoom-Handler ignorieren flex-Offset → Punkt unter Cursor driftet. Widerlegt Kommentar „Inkrement-Zoom korrekt". Hoher Regress-Risiko im Flagship-Viewer → Live-Repro vor Apply.
12. **PDF-Offline-Druck (P2):** `_pdfToImages`=[] ohne pdfjsLib (CDN) → PDF-data-URL in `<img>` = kaputtes Bild ohne Hinweis. Fix = Hinweis-Div statt img.
13. **delFolder folder_id (P3):** Reassignment nicht server-persistiert (Render fängt's ab → kein Verlust, nur DB-Drift).
14. **worker-projects DELETE-then-UPSERT (P2-low):** bei transientem Fehler nach DELETE temporär „Worker ohne Projekt" bis Retry. Reihenfolge umdrehen (erst upsert, dann `not.in`-delete).

## 🔧 Sebastian/DB-Actions (kein Frontend)
- **5 DB-Security-Migrationen anwenden** (`docs/handoff/HANDOFF-2026-06-09-DB-SECURITY-APPLY.md`) — Reihenfolge + P0-Gate (`users.auth_user_id` für alle 10) + Capture-Befehle dort.
- **jwt_exp 8h** (Dashboard → Auth → Sessions; optional, Frontend-Resilienz mildert das Symptom bereits stark).
- **nextNr Scheinnummer:** client-generiert → Duplikat-Risiko auf Shared-Tablets → DB-Sequenz/UNIQUE-Index.
- **bautagebuch.anwesende:** jsonb-String-Skalar → einmalige Normalisierung (`UPDATE … SET anwesende = anwesende #>> '{}' ::jsonb WHERE jsonb_typeof(anwesende)='string'`).

## Sauber bestätigt (0 Funde nach Verifikation)
Security/RLS-Frontend, Mobile/iOS-Zoom/Tap-Targets, Memory/Listener/Timer-Leaks, Zahlen/NaN/de-AT-Format, Geld-/Skonto-/EK-Kette, Empty-States/Zero-Data, Sync-Concurrency/Idempotenz, Zeitberechnung (von/bis/pause/KW). Mehrere Finder-Funde als **False-Positive** verworfen (z.B. „Team-aktiv-TZ" — Date-Time wird lokal geparst; Fahrbew-`it.file_url` existiert nicht; getPhotos-select unbestätigte Spalten).
