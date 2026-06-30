# HANDOFF — Kiosk/Tafel-Session 2026-06-29

**Stand:** LIVE **v3.9.568**, HEAD `c7b8b82`, `origin/main` in sync, working tree clean.
**Hosting:** GitHub Pages → `https://epkolar.github.io/epkolar-app/` (NICHT Vercel).
**Kiosk-URLs:** `?screen=planung` (WochenplanTafel) · `?screen=monteure` (MonteurTafel). Login `lager` / `<PW maskiert - sichere Ablage>` (Rolle lager_display).

---

## ⚠️ WICHTIGE GOTCHAS (zuerst lesen)

1. **RPC-Calls brauchen `Content-Type: application/json`.** `_sbH()` setzt ihn NICHT (nur `_sbWH()` / explizit). Jeder `fetch(SB_REST+"/rpc/…")` muss `headers:_sbH({"Content-Type":"application/json"})` nutzen — sonst parst PostgREST die Params nicht und der Call ist wirkungslos (war der Bug hinter „createUser legt keinen Login an" + „Krankenstand leer"). Vorbild: `login_lookup` Z.~2429.
2. **GitHub-Pages + Service Worker:** Nach Push dauert Pages ~1 Min. Kiosk-Monitore aktualisieren den SW NICHT bei normalem Reload — **Browser komplett schließen & neu öffnen** (CACHE_NAME-Bump). Erst dann ist neue Version aktiv.
3. **lager_display ist RLS-gesperrt** für viele Tabellen (RESTRICTIVE `lager_display_no_select`/`_no_insert`, Bedingung `app_metadata.role IS DISTINCT FROM 'lager_display'`). Daten für den Kiosk daher über **SECURITY-DEFINER-RPC mit minimalem Output** holen, NICHT RLS breit öffnen.
4. **Version-Triple/Quad bei JEDEM Code-Commit:** `index.html` `SW_VER` (Z.15) + `APP_VERSION` (~Z.2543) + `sw.js` Header (Z.1) + `sw.js` `CACHE_NAME` (Z.2). `node sql/_check_version.js` prüft.
5. **Gates vor jedem Push:** `python scripts/node_check.py index.html` (exit 0) · `python scripts/_bracket_check.py index.html` (Baseline `() -1, {} 0, [] 0`) · `node --check sw.js` · `node sql/_check_version.js` · `python -m pytest tests/ -q` (998 grün). Push `git push origin main`, dann curl-Verify auf `raw.githubusercontent.com/EPKolar/epkolar-app/main/…`.
6. **DB-Writes** laufen via Supabase-MCP (Projekt `jiggujpruejkaomgxarp`) — autorisiert in dieser Session. `from_date` in `absences` ist **text** (kein date).

---

## ✅ ERLEDIGT (v3.9.557 → v3.9.568)

| Ver | Inhalt |
|---|---|
| 557 | `deactivate_at` in `_USER_SAFE_COLS` (geplante Deaktivierung nach Reload sichtbar) |
| 558/559 | Bug-A: Mitarbeiter ohne users-Login in Benutzerverwaltung sichtbar + „➕ Login erstellen" (Prefill) + Scroll/Focus-Fix |
| 560 | MonteurTafel: ALLE aktiven Feld-MA als Zeilen (`fieldM`, FIELD_ROLES Monteur/Obermonteur/Techniker/Störungstechniker), Wand-lesbares Layout |
| 561 | Neue **WochenplanTafel** (`?screen=planung`, read-only Excel-Look aus weekplan_rows) |
| 562 | Startzeit-Chip + Zeit-Sortierung + Auto-Rotation Woche/Tag (Button, default AUS) + Kiosk-Logout |
| 563 | Wochenplanung-PDF Querformat-Excel-Gitter (`_wpBuildPrintHTML`/`_wpPrintPlan`, Logo via LOGO_MD) |
| 564 | createUser → **admin_create_user-RPC** (echter GoTrue-Login) · MonteurTafel tagView Rich-Liste (00:00=keine Zeit) · WochenplanTafel Krankenstand/Urlaub · Eskalation FIXTERMIN/„sehr hoch" nach 3 statt 14 Tagen |
| 565 | Logout-Button klar sichtbar · Wochen-Chip mehr Info (Zeit+Nr/Kunde/Ort) |
| 566 | Krankenstand via **kiosk_week_absences-RPC** (lager_display RLS-gesperrt) · Logout in Kopfzeile (kein Overlay) |
| 567 | **FIX Content-Type** auf beiden RPC-Calls (admin_create_user + kiosk_week_absences) |
| 568 | WochenplanTafel eigene **Bemerkung-Spalte** rechts (wie Excel) |

**DB-RPCs angelegt (MCP, admin-gated, SECURITY DEFINER):**
- `public.admin_create_user(p_email,p_password,p_name,p_username,p_role,p_monteur_id)` — Gate `auth_role()='admin'`, legt auth.users+identity (bcrypt, Token-Spalten='') an + verknüpft `public.users.auth_user_id`. EXECUTE nur authenticated.
- `public.kiosk_week_absences(p_from text,p_to text)` — Gate `auth_role()='lager_display' OR is_staff()`, liefert nur `worker_name/day/atype` der Woche (Krankenstand/Urlaub). EXECUTE nur authenticated.
- Bestehende RLS-Quellen-Regeln: `auth_role()`=public.users.role, `is_staff()`=admin/buero/projektleiter (sub-basiert), `auth.role()` ist im **Storage-Pfad null** → Storage-Policies sub-basiert.

**Manuell:** GoTrue-Logins für **aliti** (Ismael Aliti, w-id mqyxfca35x6i) + **lager** angelegt, Passwort `<PW maskiert - sichere Ablage>`.

---

## 🔜 OFFEN — Mobile-Wochenplanung umbauen (nächste Aufgabe)

**Problem:** Im WeekPlan-Component ist die Haupt-Planung auf Mobile (<600px) unbrauchbar — Bearbeiten geht nicht, weil der `cellPick`-Picker NUR in `renderCell` (Desktop-Tabelle, `!isMob`) gerendert wird. Mobile setzt zwar `cellPick`, rendert aber keinen Picker.

**Auftrag (NUR isMob-Zweig, Desktop `!isMob` BYTE-IDENTISCH lassen, `selDay`-State behalten):**
1. **Kompakte Wochen-Karten:** pro Bauvorhaben EINE Karte mit Kopf (Nr + BVH bold, wordBreak) + 6-Spalten-Mini-Grid Mo–Sa (gleich breit, flex). Zelle = zugeteilte Personen als gekürzte Nachnamen (~6 Z., rollenfarbig), max 3 dann „+N"; Fahrzeuge „🚛 Kennz."; leerer Tag „·"; voller Name als `title`. HEUTE (V.ac) + Sa getönt. Keine großen MA/FZ-Chips, keine Tag-Reiter mehr. Tap-Ziele ≥40px.
2. **Picker auf Mobile:** Tap Tageszelle → `setCellPick({rowId:r.id,days:[tag],type:'ma'})`. cellPick-Picker als **zentriertes fixed-Overlay** (position:fixed, zIndex 9999, V.cd-bg, ✕ + Tap-außen schließt) — NICHT die `<td>`-Smart-Positionierung. **Picker-Body aus dem Desktop-Popup wiederverwenden/extrahieren** (MA/FZ-Toggles + Kopier-Tag-Chips), IDENTISCHE Schreiblogik (Toggle in `cell.ma`/`cell.fz` am Tag, `setRows`→Auto-Save). KEIN zweiter Datenpfad, kein REST/Modell-Change.
3. Krankenstand/Urlaub-Streifen + „+ Zeile hinzufügen" bleiben (kompakt unter den Karten).

**STOPP:** Wenn der Picker-Body nicht sauber wiederverwendbar extrahierbar ist (zu viele Render-Closures) → melden statt mit Logik-Drift duplizieren.

**Code-Anker (Stand v3.9.568, vor evtl. weiteren Shifts NEU greppen!):**
- `cellPick`-State: `const [cellPick,setCellPick]` ~Z.16238
- `renderCell` (Desktop-Zelle + Picker-Popup): ~Z.16710; **Picker-Body** ~Z.16733–16800 (MA/FZ-Toggles, Kopier-Tag-Chips, ✕ Z.16800); Smart-Positioning `cellPickPos` ~16450–16480
- Mobile-Render-Zweig: ~Z.16976–16982 · Desktop-Tabelle (`!isMob`): ~Z.16984+ (`renderCell`-Aufruf ~17116, bem-Doppelklick-td ~17117)
- Schreibmuster: `setRows(prev=>prev.map(...z:{...[tag]:{ma,fz}}))` (siehe Kopier-Logik ~16791)

---

## Greift sonst noch (kleinere offene/Hinweise)
- **Mängel-Fotos** (`defects.images`): nur 120px-Base64-Thumbs, Vollbilder längst im Storage → Migration NICHT lohnend (Agent-Analyse), bewusst gelassen.
- **Seit v3.9.564 vor v567 per App angelegte Benutzer** bekamen evtl. keinen GoTrue-Login (Content-Type-Bug) → ggf. via „Login erstellen" neu anlegen; MCP-Abgleich public.users↔auth.users möglich.
- **DELETE epkolar-files** (`epkolar_admin_delete`) = admin/PL-only (sub-basiert); Monteure können eigene AS-Fotos NICHT löschen (bewusst, separate Entscheidung offen).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
