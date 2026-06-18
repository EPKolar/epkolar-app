# EPKolar — PlanRadar-Angleich Tickets/Mängel 18.06.2026 (v3.9.462 → 464)

3 Features, je eigener Commit + Triade grün (958 pytest), alle live auf `epkolar.github.io/epkolar-app`.

## BLOCK A — Einzel-Ticket/Mangel-PDF (v3.9.462, `989d5c8`)
- **jsPDF** via cdnjs ergänzt (`jspdf.umd.min.js`, neben react/pdf.js/qrcode; kein SRI — konsistent mit Bestand, App-weite SRI wäre separate Härtung).
- `_genTicketPdf(ticket,plans,monteure,layers,proj)` — A4-Report:
  - Grüner CI-Header „EP: Kolar & Sohn / Ticket-Mangel-Report".
  - Meta-Block (Nr, Status, Prio, Typ, Erstellt, Frist, Projekt, Ebene/Gewerk, Zugewiesen, Fortschritt).
  - **Plan-Ausschnitt mit rotem Pin** bei `x/y` (Bild via `_tkLoadImg`, PDF-Plan via pdf.js `_tkRenderPdfPage`, ±150px Crop) — Fehler/kein Plan → Text-Fallback, nie Crash.
  - Beschreibung (autoWrap), Fotos 2×2 (dataUrl bzw. fetch→base64), Kommentar-Journal, Footer (Datum + Seitenzahl).
- `_pdfStr` strippt Emojis/Non-latin1 (jsPDF-Standardfont = latin1; Umlaute bleiben).
- Button **„📄 PDF"** im TicketDetail-Header (Admin/PL/Büro). `plans`+`proj` an TicketDetail durchgereicht.

## BLOCK B — Audit-Trail Status-Historie (v3.9.463, `1dc16a5`)
- **DB-Migration** (Plugin, self-guarded, CC-Freigabe): `tickets.status_history jsonb DEFAULT '[]'`.
- `updateTicket`: bei jedem Status-Wechsel **strukturierter Eintrag** `{status, fromStatus, changed_by_id, changed_by_name, changed_at, comment}` → `status_history` (ersetzt den bisherigen Event-Kommentar; `comments` bleibt sauber). jsonb → nicht in `TEXT_JSON_FIELDS` (App-Regel „neue Features = jsonb"), native Array im PUT, `_jp` beim Lesen.
- Neue **aufklappbare „📋 Status-Historie"-Timeline** im TicketDetail: von→nach, Wer, Wann (älteste oben).

## BLOCK C — Bulk-Status/-Zuweisung Mängel (v3.9.464, `a4d474a`)
- VMang: **Checkbox je Mangel-Karte** + **„Alle"-Toggle** im Filter (beide Admin/PL).
- **Sticky Aktionsleiste** wenn ≥1 ausgewählt: „n ausgewählt | Status ändern▾ (`MANGEL_ST`) | Zuweisen an▾ (Monteure) | ✓ Anwenden | ✕ Abbrechen".
- `_bulkApply`: Status via `updSt` (inkl. `_syncTicketStatus` → Ticket-Spiegel), Zuweisung via `defects`-PUT `{zugewiesen,worker}`, dann Toast + Auswahl zurücksetzen. Kein DB-Change.

## DB-Migrationen dieser Sitzung (Plugin, self-guarded, CC-Freigabe „CC führt SQL aus")
- `absence_files.storage_path` + RLS `absence_files_own_read` (v3.9.458).
- `tickets.status_history jsonb` (v3.9.463).

## Verbleibende PlanRadar-Lücken (nicht beauftragt)
Plan-Versionierung (Revisionen + Pin-Migration, größter Aufwand), Fälligkeits-/Eskalations-Automatik, Ticket-Vorlagen/Custom-Felder, Mengen/Aufmaß auf Plan. Bei Bedarf je eigene Aufgabe.

First-read Gesamt-Session: `docs/handoff/STAND-2026-06-18-SESSION.md` + diese Datei.
