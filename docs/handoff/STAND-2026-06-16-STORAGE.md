# EPKolar Stand 2026-06-16 — Storage Personaldokumente + Chef-Portal + Kontrast

main = origin = **v3.9.403** (`5661c6e`), working tree clean, 903 pytest grün, node_check 0.

## NACHTRAG 2026-06-16 (v3.9.400 → v3.9.403)
- **v3.9.400 Chef-Portal:** Karte **Auslastung/Kapazität** (aktive Feld-MA × 38,5h Soll vs. time_entries Ist, Woche/Monat-Toggle, Ampel <70/70-95/>95, AA) + **Auftragsvolumen-Trend** (projects.betrag/Monat nach created_at, 12 Mon, ChartBox). v3.9.401: Kapazität = ALLE Feld-Rollen (außer Backoffice/Verkauf/GF/Lager) — inkl. Störungstechniker+Techniker.
- **v3.9.401 Zeiterfassung-Self-Edit:** Monteure dürfen EIGENE time_entries editieren (`_canEditEntry` = zeit_other ODER Feld-Rolle & selWorker===eigene monteurId, analog _canDelEntry). + Auftragsvolumen-Trend sauber (SvgBar/ChartBox optionaler `fmt`, €-Tausender, leere Monate ohne 0).
- **v3.9.402 Projekt-Budget vs. Ist:** DB `projects.budget_stunden`+`budget_euro` (numeric nullable). Projekt-Formular 2 optionale Felder. Chef-Portal-Karte „Projekt-Budget (Soll-Ist)": Stunden Ist(time_entries)/Ziel + €-Ziel vs. KALK. Kosten (Std×workers.stundensatz, ehrlich „geschätzt", €-Teil weg wenn kein Satz). Ampel <85/85-100/>100. Live verifiziert (Write-Pfad + Anzeige), Test-Budget wieder entfernt.
- **v3.9.403 Gefahrstoff-SDBs → Storage (KOMPLETT):** plans waren schon im Storage (kein Bloat); echter Bloat = **gefahrstoff_files (59 base64-PDFs, 26 MB)**.
  - **Stufe A (DB):** `gefahrstoff_files.storage_path text` + privater Bucket **`epkolar-gefahrstoff`** + Storage-RLS = **Spiegel der DB-RLS**: SELECT=authenticated (alle Eingeloggten lesen SDBs), INSERT/UPDATE/DELETE=`is_staff()`.
  - **Stufe B (Code):** Helfer `_sbUploadGef`/`_sbSignedGefUrl` (Pfad `gefahrstoff/{folder_id|misc}/{uuid}_{name}`). onUpload → Storage (storage_path) mit base64-Fallback bei Storage-Fehler (kein Datenverlust/Silent-Drop). openFile: storage_path→signed URL, sonst file_data/file_url. Liste lädt storage_path. ROUTE_MAP-Key `gefahrstoff-files` ok.
  - **Stufe C (Migration):** 59/59 migriert (upload→signed-URL verifiziert→storage_path→file_data=null), 0 Fehler, 59 Objekte im Bucket. **Tabelle 27 MB → 56 kB** (VACUUM FULL). UI-Stichprobe: SDB öffnet via signed URL.
  - **Stufe D OFFEN (separates Go):** `file_data`-Spalte ist überall NULL — ganz droppen/leeren nur auf explizites OK (Code nutzt file_data noch als Fallback).
  - **Storage-403-Mythos widerlegt:** v3.9.197-Annahme „Storage authentifiziert User-JWT nicht" ist FALSCH — mit echtem Login löst Storage is_staff/auth korrekt auf (bei epkolar-docs + jetzt gefahrstoff bewiesen).

## Heute live (alle gepusht)
- **v3.9.382** Dead-Code (4 ungenutzte Funktionen).

## Heute live (alle gepusht)
- **v3.9.382** Dead-Code (4 ungenutzte Funktionen).
- **v3.9.383/384** Bug-Hunt: dringendeAS-Sentinel, BWB-Export-null, Matrix-Rundung, Foto-Loader-dep, Werkzeug-Recht (wz_edit=Lager+Büro), Sync-Banner owner-skopiert (SQ.countMine), _moOwner, Ordner-Cycle-Guard, KW-Dezimal.
- **v3.9.385–388** Chef-Übersicht Auftragsvolumen/GJ (start/ende-Toggle) + Kontrast Grün-Familie (V.acTx hell #006e30/dunkel #00b050, _okG hue-aware) — alle grünen Texte AA in Hell+Dunkel (Status-Grids inkl.).
- **v3.9.389** Desktop-Nav 2-zeilig (flexWrap:wrap statt nicht-swipebarem overflow).
- **v3.9.390** Auswertungen Chart-Grid füllt Breite (minmax 330,1fr + ChartBox maxWidth 520).
- **v3.9.391–396** Kontrast 2. Welle (success/positiv-grün via _okG, single+double quote, Status-Maps).
- **v3.9.394** „Anmeldungen" → „Persönliche Dokumente" (nur Label; Tabelle anmeldungen bleibt).
- **v3.9.397** **Chef-Portal** (ChefDashboard Bereichs-Karten: Projekte/Finanzen/AS/Zeit/Urlaub/Fahrzeuge/Werkzeuge/Material/Gefahrstoffe, collapsible, KPIs, Handlungsbedarf) + Health-Check-Fix (HTTP-Antwort=Server erreichbar, nur 5xx/throw=serverOk:false).
- **v3.9.398** **Storage Stufe 1** (Personaldokumente → privater Bucket epkolar-docs).
- **v3.9.399** FIX: `anmeldungen` in ROUTE_MAP ergänzt (fehlte → /api/anmeldungen war No-op → Persönliche-Dokumente-Inserts landeten NIE, auch alte base64).

## DB-Änderungen heute (CC via Supabase-Plugin, Sebastian-Freigabe, jiggujpruejkaomgxarp)
- **Urlaub:** Günther (w6) 16 absences `beantragt`→`genehmigt` (self-guarded). „16 ausstehend" weg.
- **RLS supplier_articles/supplier_configs:** Schreiben nur is_staff (permissive _write_auth entfernt).
- **RLS anmeldungen:** Write-Policies = fahrbewilligungen (TO authenticated, is_staff).
- **Storage Stufe 2:** Spalte `storage_path text` auf anmeldungen+fahrbewilligungen; **privater Bucket epkolar-docs** (public=false); Storage-RLS auf storage.objects: INSERT/UPDATE/DELETE=is_staff(), SELECT=is_staff() OR `(storage.foldername(name))[2]=current_monteur_id()`. Pfad `docs/{monteur_id}/{uuid}_{name}.pdf`.

## Storage-Auth-Erkenntnis (wichtig)
Storage LÖST das User-JWT auf (is_staff/current_monteur_id funktionieren mit echter Session) — Owner-Scoping bewiesen (eigener Pfad signierbar, fremd blockiert). KEIN Auth-Hook/app_metadata-Umbau nötig. Früherer 403 war nur Anon-Session (restaurierter User ohne GoTrue-Token).

## Stufe 1 Code
FahrbewSection + AnmeldungSection: onUpload → `_sbUploadDoc(workerId,name,dataUrl)` (privat, gibt storage_path) → DB-Insert nur storage_path (kein file_data). openItem: storage_path→`_sbSignedDocUrl` sonst altes file_data. Helfer bei `_sbUploadFile` (~1571). _sbUploadFile/epkolar-files (public Fotos/Pläne) unberührt.

## OFFEN
- **Stufe 3 Migration** base64→Storage: NUR auf Sebastians off-peak-Go (keiner live). Pro Datei: lesen→hochladen→signed-URL verifizieren→erst dann file_data leeren. Idempotent, Zähler, kein Löschen vor verifiziertem Upload.
- Backup-Tabellen `_rls_snapshot_v3923`/`_wp_orphan_backup_v3946` nur auf OK droppen. `auth_leaked_password_protection` im Dashboard aktivieren. VOffa/ZUZEIT.ASC eingefroren.
- Admin-Login admin/34kolar70. Live https://epkolar.github.io/epkolar-app/
