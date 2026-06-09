# Gefahrstoff-Modul (Sicherheitsdatenblätter) — Build-Spec v3.9.196

**Ziel:** Eigenständiges Modul wie Werkzeuge/Fahrzeuge für Gefahrenstoff-/Sicherheitsdatenblätter (gesetzliche Mitarbeiter-Zugangspflicht). Explorer-Style mit **freien Ordnern** + **Suche**, überwiegend PDFs.
**Rechte:** Lesen = alle Monteure/Mitarbeiter. Bearbeiten (Upload/Ordner/Löschen) = **Admin + Pinger (u5/w4) + Schmid (u6/w5)** — in die Rechtevergabe (`canDo`) eingebaut.
**Speicher:** bestehender Storage-Bucket, Prefix `gefahrstoff/`. DB: `gefahrstoff_folders` + `gefahrstoff_files` (siehe `sql/gefahrstoff_module.sql`).

## Status
- ✅ DB-Migration als Datei: `sql/gefahrstoff_module.sql` (NOCH NICHT appliziert — sauberes Fenster wählen, Pinger war live).
- ⏳ Frontend (index.html) + apply + Push: offen (NICHT pushen während Pinger live — Push bumpt SW → Reload).

## Integrationspunkte (index.html)
1. **ROLES.modules** (~2671-…): `"gefahrstoff"` in alle Rollen aufnehmen, die lesen dürfen (admin/projektleiter/buero/obermonteur/techniker/monteur/helfer/viewer → alle, da gesetzlicher Zugang).
2. **_navIds** (~4957): `"gefahrstoff"` einreihen (z.B. nach `"werkzeuge"`). Label/Icon: "☣️ Gefahrstoffe" o.ä.
3. **Modul→Komponente-Switch** (App-Render, wo `tab==="werkzeuge"` etc. auf Komponenten mappt): `tab==="gefahrstoff" && React.createElement(VGefahrstoff,{curUser, ww})`.
4. **canDo** (3724, im `m`-Objekt): `gefahrstoff_edit: isA || (user&&(user.username==="pinger"||user.username==="schmid"))` (admin + Pinger + Schmid; via username = stabil, monteurId w4/w5 als Fallback).
5. **API.* / Loader**: `getGefahrstoffFolders()` = `_sbGetOrder("gefahrstoff_folders","name.asc")`, `getGefahrstoffFiles()` = `_sbGetOrder("gefahrstoff_files","name.asc")`. CRUD via `SQ.push({url:"/api/gefahrstoff-folders"...})` + ROUTE_MAP-Einträge (gefahrstoff-folders→gefahrstoff_folders, gefahrstoff-files→gefahrstoff_files).
6. **Storage-Upload**: bestehendes Muster (Bucket-Helper ~1583 `SUPABASE_URL+"/storage/v1/object/public/"+SB_BUCKET+"/"+path`). PDF → `gefahrstoff/<uid()>.pdf` hochladen (PUT auf storage/v1/object), `file_url` ableiten, Datei-Row anlegen.

## Komponente VGefahrstoff (Explorer)
- State: `folders, files, curFolder (id|null=root), q (Suche), uploading`.
- Load: folders + files beim Mount (API), Fallback ODB/Demo.
- `canEdit = canDo("gefahrstoff_edit", curUser)`.
- **Breadcrumb** (Root / … / aktueller Ordner) + **Zurück**.
- **Ordner-Kacheln** (curFolder-Kinder: `folders.filter(f=>f.parent_id===curFolder)`), Klick = reingehen.
- **Datei-Liste** (`files.filter(f=>f.folder_id===curFolder)`): Name, Lieferant, Größe, 📄-Icon, Klick = PDF öffnen (file_url im neuen Tab / Inline-Viewer).
- **Suche `q`**: wenn aktiv → flach über ALLE files (name/lieferant/notiz, case-insensitiv), ignoriert curFolder; Treffer mit Ordner-Pfad.
- **Edit-only (canEdit):** „+ Ordner" (prompt name → folders-POST), „📤 PDF hochladen" (file-input accept=.pdf, multiple → Storage-Upload + files-POST), Umbenennen, 🗑️ Löschen (Ordner kaskadiert via FK, Datei + Storage-Objekt). Nicht-Editoren sehen diese Buttons NICHT (read-only).
- Mobile: Kacheln/Liste responsive (isMob via ww), Touch-Targets ≥44px (globale CSS greift).

## Triade + Deploy
- Bracket `() -1`, node --check (Vorsicht: KEIN `</script>` in Kommentaren!), pytest 726 (`>file; echo EXIT=$?>>file`).
- Version-Bump 4 Stellen → v3.9.196.
- **Apply** `sql/gefahrstoff_module.sql` (DDL, Freigabe) + Storage-Prefix nutzbar.
- **Push erst wenn Pinger offline** (SW-Bump = Reload).
