# EPKolar — Session-Stand 18.06.2026 (v3.9.436 → v3.9.455 + 1 DB-Migration)

App: `index.html` (Single-File React, Babel-transpiled) + `sw.js`. Live: GitHub Pages `https://epkolar.github.io/epkolar-app/`.
Supabase-Projekt `jiggujpruejkaomgxarp` ("Baumanagement & Zeiterfassung", eu-west-2).
Triade pro Commit: `python scripts/node_check.py index.html` (exit 0) · `python scripts/_bracket_check.py index.html` (Baseline `()-1 / {}0 / []0`) · `node sql/_check_version.js` (3 Versionen synced) · `python -m pytest tests/ -q` (958 grün).
Version-Bump je Patch: `var SW_VER='epkolar-vX'` + `const APP_VERSION="X-supabase"` + sw.js Header-Kommentar + `const CACHE_NAME`.

## Diese Session — gepusht auf main (alle live, je eigener Commit + Triade grün)

| Version | Commit | Inhalt |
|---|---|---|
| v3.9.436 | eb68b3f | CSP frame-src/object-src: Supabase-Host → PDF-Viewer (Dokumente/Fahrbewilligungen) entblockt. Playwright-verifiziert. |
| v3.9.437 | a0a594d | Zeiterfassung Inline „0 h" → Eintrag LÖSCHEN (statt still No-Op; DB behielt alten Wert). |
| v3.9.438 | 945cda2 | Bauwochenbericht zählt **Sonntag** mit (lokale 7-Tage-Woche `BWB_DAYS` nur in exportBauwochenbericht; globale `DAYS` Mo-Sa unangetastet). |
| v3.9.439 | 3f3a14e | Quota-Monitor deckt **IndexedDB** ab (`navigator.storage.estimate`, 5-min-Timer) — „Speicher voll" vor echtem QuotaError. |
| v3.9.440 | 23c0c47 | Urlaubs-**Bereichsantrag Overlap-Guard**: genehmigte Tage überspringen, existierende via PUT statt POST (kein 409). |
| v3.9.441 | 8ab357f | **Token-AND-Suche** in Projekte/User/Tickets/Gefahrstoff (wie AS/Material). |
| v3.9.442 | 1563b47 | **#17 idempotenter AS-POST**: ON CONFLICT(id) DO NOTHING (`resolution=ignore-duplicates`) NUR im arbeitsscheine-Branch des Dispatchers. Kein Overwrite (Juprowa autoritativ). `_juprowaPush` unberührt. Server-Mechanismus per Rollback-Probe verifiziert. |
| v3.9.443 | de9c534 | Fahrzeug TechDaten (8 Felder) `input` → `textarea`. |
| v3.9.444 | 59337bb | Serviceheft-Dokumente klickbar → **PdfViewerModal** (signierte FZ-URL / Legacy-base64). Playwright-verifiziert. |
| v3.9.445 | 53f070a | TechDaten-Textareas **auto-grow** (ref+onInput height=scrollHeight, resize:none). |
| v3.9.446 | c250581 | **PDF-Preview mobil**: Android/iOS rendern iframe-PDF nicht → auf Mobile (`_isMobileViewer`: innerWidth<768 \|\| UA) direkt im Geräte-Viewer (`window.open` via `_openFileUrl`). Zentral für Fahrbew/Anmeldungen/Gefahrstoff/Serviceheft. Desktop = iframe-Modal. Playwright-mobil verifiziert. |
| v3.9.447 | a9105c3 | **WLAN-Status SVG-Icon** (`WifiStatusIcon`, grün aktiv / rot durchgestrichen) statt Ampel-Punkt — Header-Sync-Indikator + Notif-Panel-Bar. Status-Texte bleiben. |
| v3.9.448 | 783a5be | Lenkfrei **BIS-Uhrzeit** type=time → Textfeld HH:MM, erlaubt 24:00 (Validierung 00:00–24:00). DB `bis_uhr`=text → String direkt. |
| v3.9.449 | 978b5b9 | Lenkfrei **VON-Uhrzeit** ebenfalls Textfeld (analog BIS, 00:00–23:59). 24:00-Druck per Playwright verifiziert (Feld 13). |
| v3.9.450 | a8d11f1 | Lenkfrei-**Druck via verstecktes iframe** statt `window.open`-Popup (Popups in PWA/Handy blockiert → „kein Drucker"). Funktioniert Desktop+Mobile. |
| v3.9.451 | 90594e9 | **Glocke-Eskalation erst nach 14 Tagen** (AS/Material). Davor sanfte Erinnerung (Typ `as_new`/`material_order`, nicht in eskCount → Glocke pulst nicht). |
| v3.9.452 | 9d28c05 | Tankung: **km-Stand nie geringer** — Admin-Override (`allowKmDowngrade`) entfernt, `_tankConfirmModal` blockt km<aktuell für alle Rollen. |
| v3.9.453 | 10c978c | **Urlaub-Genehmigung Büro** + DB-Trigger-Fix (siehe unten). |
| v3.9.454 | a4b6766 | Label-Rename „Büro-Export" → „Büro-Portal" (Modul-id `bueroexport` unverändert). |
| v3.9.455 | (push folgt) | Schnellsuche: Fahrzeug-Treffer öffnet Fahrzeug-Detail direkt (`window.__pendingFzSel` → FahrzeugView Mount-Effect `setSel`). |

## DB-Migration (Supabase-Plugin, explizite Chef-Freigabe „ja büro darf auch genehmigen")
**`guard_urlaub_edit_allow_buero_pl_override`** (v3.9.453): Trigger-Funktion `public.guard_urlaub_edit()` (BEFORE INS/UPD/DEL auf `absences`) — Voll-Zugriff (Genehmigen/Bearbeiten) jetzt für `role IN ('admin','projektleiter','buero')` **ODER** `urlaub_edit` aus `permissions` **ODER** `perms_override`.
**Root Cause** des „Schober sync ausstehend": Schober (buero) hat `perms_override={"urlaub_edit":true}` aber `permissions="[]"`; Frontend zeigte den Genehmigen-Button (hasPerm prüft perms_override), der alte Trigger prüfte aber nur `permissions`-Spalte + `admin`-Rolle → RAISE EXCEPTION → PATCH stuck. Self-guarded verifiziert: admin/PL/buero=true, monteur/techniker=false (fallen in Selbst-Regeln → kein Selbst-Genehmigen). Frontend `AbsView.isAdmin` zusätzlich um `buero` ergänzt. Monteure sehen Genehmigen/Ablehnen NICHT (alle Buttons isAdmin-gegated, verifiziert).

## OFFENER BACKLOG (vom Chef in dieser Session gewünscht, noch NICHT umgesetzt)
1. **Werkzeuge Aus-/Ein-/Umbuchen einfacher & schneller** — Chef-Entscheidungen via AskUserQuestion bereits gewählt: **QR-Scan-Schnellbuchung + Monteure self-service + Bulk schneller**, Berechtigung **auch Monteure selbst** (aktuell Bulk-Ausgabe nur Admin, Patch Z.~20797 `zugewiesen+status:ausgegeben+Baustelle` ↔ Lager). QR-Scanner-Infra existiert (`scanning`/`scannedWz`). Groß.
2. **Bautagebuch (Projekte) — volle Spracherkennung mobil + Rechtschreibung + Groß/Klein** — `SpeechWrap`/`MicBtn`/`SpeechRec` (Z.4506/4530/4546) existieren und werden in AS/Mängel/Tickets/Schaden genutzt; VBautag (Z.13609) Textfelder noch OHNE SpeechWrap. Idee: VBautag-Textareas in `SpeechWrap` wrappen + optional Satz-Anfang-Großschreibung/Trim.
3. **Projekte näher an PlanRadar** — „was fehlt, nicht übertreiben, Bestand verbessern". Offen/Scoping nötig (VPlan/VMang/Tickets bestehen bereits). 
4. **Lenkfrei-Bescheinigung CI-Redesign (FIX B)** — Chef wollte Ausdruck ans EP-CI anpassen; Spec nannte ROT #e63946-Header, App-CI ist aber GRÜN #009640 (aktueller Druck-Header schon grün-CI). **Widerspruch klären** (grün behalten vs. rot wie Spec) bevor umgesetzt.

## Wichtige Pfade/Regeln
- PATH-LOCK: NUR `T:\05_Claude\02_Baumanagment & Zeiterfassungs - APP\03_Repos\epkolar-app\` (NIE `T:\03_Repos\`).
- Prod-DB-Write nur auf explizite Chef-Anweisung („fix das über supabase"); sonst read-only. Self-guarding Pflicht.
- Cache-Hinweis an User: nach Deploy „🔄 Neue Version verfügbar → Jetzt aktualisieren" bzw. PWA neu öffnen (häufige Ursache für „geht nicht" = alte gecachte Version).
- Mobile-Browser-Lock: verwaiste `ms-playwright-mcp`-Chrome-PIDs killen.
