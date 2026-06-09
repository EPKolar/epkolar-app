# Gefahrenstoffe-Modul (Sicherheitsdatenblätter) — IST-Stand v3.9.199 (LIVE)

**Modul ☣️ „Gefahrenstoffe — Sicherheitsdatenblätter"** — eigenständig wie Werkzeuge/Fahrzeuge. Explorer mit freien Ordnern + Volltextsuche, PDFs. **Live + verifiziert** (Upload, Ordner, Suche, Inline-PDF-Viewer, Datum/Bearbeiter, Mobile/Swipe/Back).

## Rechte (in `canDo` eingebaut)
- **Lesen + PDF ansehen = ALLE Mitarbeiter** (`hasPerm('gefahrstoff')` → true für jede nicht-gesperrte Rolle; gesetzlicher Zugang).
- **Bearbeiten** (Ordner anlegen/umbenennen/löschen, PDF hochladen/löschen) = **Admin + Pinger (u5/w4) + Schmid (u6/w5)** via `canDo('gefahrstoff_edit')`. Nicht-Editoren sehen die Buttons nicht (read-only).

## Speicherung — PDFs liegen in der DB (NICHT im Storage)
- **`gefahrstoff_files.file_data` = base64-dataUrl** (Postgres `text`). DB-Tabellen: `gefahrstoff_folders` + `gefahrstoff_files` (RLS `authenticated`, FK-Kaskade Ordner→Dateien).
- Stand 09.06.: 39 Dateien, ~19 MB in der DB, 0 im Storage.
- Upload via PostgREST (authentifiziert) — die Liste lädt `file_data` NICHT (nur Metadaten), `file_data` wird erst beim Öffnen geladen → Browsen bleibt schnell.
- Inline-PDF-Viewer: `file_data` → Blob-URL (`URL.createObjectURL`) → `<iframe>`; CSP erlaubt `frame-src 'self' blob: data:` (v3.9.199). Revoke beim Schließen.

## ⚠️ WARUM base64-in-DB statt Storage (Plattform-Finding — Sebastian)
Der Storage-Upload (Bucket `epkolar-files`, `_sbUploadFile`) gibt **HTTP 403 "new row violates RLS"** zurück, OBWOHL ein **gültiges authenticated User-JWT** (ES256, role:authenticated, is_anonymous:false) im Authorization-Header gesendet wird (mitgeschnitten + dekodiert — KEIN anon-Key). PostgREST akzeptiert dasselbe Token (REST 200, Ordner-Anlage ok). → **Die Storage-API honoriert das ES256-User-JWT nicht** (behandelt den Request als anon) → jede rollenbasierte Storage-Policy (`auth.role()='authenticated'`) lehnt ab.
- **Betrifft generell ALLE Storage-Uploads** (auch Pläne/Fotos via `_sbUploadFile`) — letzter erfolgreicher Storage-Upload war 01.06.2026; seither vermutlich gebrochen (Zeitpunkt korreliert evtl. mit JWT-Signing-Keys-Umstellung auf ES256).
- **Policy wurde NICHT aufgeweicht** — `epkolar_auth_upload/update` auf Original-Härtung (`auth.role()='authenticated'`) belassen/revertiert; KEINE anon-INSERT-Policy, KEIN public-write.
- **Sebastian-Action (Plattform):** Storage-API/JWT-Verifikation prüfen — Asymmetric-Keys (ES256) im Storage-Service aktivieren, ODER JWT-Signing zurück/parallel, sodass `auth.jwt()`/`auth.role()` im Storage-Kontext greift. Dann funktionieren Pläne/Fotos-Uploads wieder.

## 📋 BACKLOG — Storage-Auslagerung (sauber, NACH Plattform-Fix)
Wenn der Storage-API/JWT-Punkt gelöst ist UND/ODER die DB-Menge zu groß wird:
1. PDFs aus `gefahrstoff_files.file_data` nach Storage (`epkolar-files`, Prefix `gefahrstoff/<id>.pdf`) auslagern, `file_path`/`file_url` setzen, `file_data` leeren.
2. Frontend: `onUpload` → wieder `_sbUploadFile` (Storage); `openFile` lädt `file_url` (Blob via fetch) statt `file_data`. Spalten + Viewer bleiben kompatibel (file_url-Fallback ist bereits drin).
3. Migration für Bestands-39: Skript liest `file_data`, lädt in Storage, schreibt `file_url`, nullt `file_data`.
**Schwelle:** Für Dutzende–wenige Hundert SDS (<1–2 MB) ist DB-base64 unkritisch (DB Pro 8 GB; Liste ohne file_data). Erst bei sehr vielen großen Dateien / mehreren GB lohnt die Auslagerung.

## Verwandte Fixes dieser Session
- **v3.9.198** Sparkasse-Ticket-Datenverlust: `tickets.photos/comments` (TEXT) wurden als rohe Arrays gepostet (nicht in `TEXT_JSON_FIELDS`) → POST 400 → Ticket nach 5 SyncQueue-Retries still verworfen (2/3 Tickets verloren). Fix: `'photos','comments'` in `TEXT_JSON_FIELDS`. **Verlorene Tickets sind NICHT wiederherstellbar** (waren nie in der DB) — ggf. neu anlegen.
- Keine Orphan-Gefahrstoff-Zeilen (0 ohne file_data, 0 verwaiste Storage-Objekte) → kein Cleanup nötig.

## Integrationspunkte (index.html, IST)
- `hasPerm` (~3714): `if(mod==="gefahrstoff") return true;`
- Nav-Item (~5509): `{l:"Gefahrenstoffe",i:"☣️",c:"#dc2626",perm:"gefahrstoff",g:3}`
- Render-Switch (~5858): `...perm)==="gefahrstoff" && React.createElement(VGefahrstoff,{curUser,ww})`
- `canDo` (~3724 `m`): `gefahrstoff_edit:isA||(user&&(user.username==="pinger"||user.username==="schmid"||user.monteurId==="w4"||user.monteurId==="w5"))`
- ROUTE_MAP (~1860): `gefahrstoff-folders`/`gefahrstoff-files`
- Komponente `VGefahrstoff` (~18449, vor WerkzeugView)
- CSP (Z.8): `frame-src 'self' blob: data:; object-src 'self' blob: data:;`
