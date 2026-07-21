# Stempeluhr-Fundament — Status 20.07.2026 (READ-ONLY geklärt, nichts gebaut)

**Ziel (Sebastian):** Die App soll perspektivisch **FinkZeit ablösen** und die PZE-Monatsübersicht selbst
erzeugen. Erster Baustein = eine funktionierende Stempeluhr am Werkstor.

**Kurzbefund:** Die **App-Seite ist fast vollständig** (Kiosk-Screen, Toggle-Logik, PZE-Rechenkern,
Büro-Auswertung mit Excel/PDF-Export — alles live im Code auf v3.9.768). Es fehlt **ausschließlich das
DB-/Auth-Fundament für die eigenständige Terminal-Rolle**. Das ist genau der Widerspruch aus dem Vorbefund:
`STEMPEL_TERMINAL_v2.sql` behauptet, es sei am 14.07. gelaufen — **die DB widerlegt das**.

Alle Aussagen unten sind read-only gegen die Live-DB (`pg_proc`, `pg_policies`, `pg_class`,
`information_schema`) bzw. gegen `index.html` @ v3.9.768 geprüft. Kein DDL, kein DML, kein index.html-Commit.

---

## 1) RPCs & Rollen — was fehlt

**`stempel_terminal_workers()` existiert NICHT.** `pg_proc`-Suche über `%stempel%`/`%kiosk%`/`%pze%`/
`is_kiosk_role` findet:

| RPC | Args | Security | für die Stempeluhr? |
|---|---|---|---|
| `is_kiosk_role()` | — | DEFINER | Baustein (prüft Kiosk-Rolle) — **da** |
| `kiosk_fahrzeuge()` | — | DEFINER | Flotte-Kiosk, nicht Stempel |
| `kiosk_field_workers()` | — | DEFINER | Monteur-Tafel, nicht Stempel |
| `kiosk_week_absences(p_from,p_to)` | text,text | DEFINER | Dispo-Kiosk, nicht Stempel |
| `kiosk_week_arbeitsscheine(p_from,p_to)` | text,text | DEFINER | Dispo-Kiosk, nicht Stempel |
| **`stempel_terminal_workers()`** | — | — | **FEHLT** |

**Die App ruft diesen RPC bereits auf** (`index.html:6677`, in `StempelTafel`, v3.9.695): sie lädt ihre
Minimaldaten (id/name/role/nfc_uid) über `POST /rpc/stempel_terminal_workers`. Fehlt der RPC, zeigt die
Tafel den Fehler „RPC stempel_terminal_workers() fehlt — sql/STEMPEL_TERMINAL_v2.sql ausführen"
(`index.html:6684`) statt Monteuren. **→ Die Stempeluhr ist für einen Terminal-User aktuell nicht bedienbar.**

**Damit die Terminal-Rolle funktionieren würde, fehlen drei Dinge (alle NICHT vorhanden):**
1. **RPC `stempel_terminal_workers()`** (SECURITY DEFINER) — liefert die Worker-Minimalliste, durchlässig
   für `auth_role()='stempel_terminal'` ODER `is_staff()`.
2. **Auth-User + `public.users`-Zeile mit `role='stempel_terminal'`** — geprüft: `auth.users` mit
   Stempel-Bezug = **0**, `public.users WHERE role='stempel_terminal'` = **0**. Es gibt die Rolle in der
   DB also noch gar nicht (nur im App-Code als String).
3. **RLS-Zweig auf `stempel_log` für die Terminal-Rolle** — siehe Punkt 2, das ist der eigentliche Blocker.

---

## 2) `stempel_log` — Tabelle da, aber RLS sperrt genau die Terminal-Rolle aus

| Prüfung | Ergebnis |
|---|---|
| Tabelle `public.stempel_log` | ✅ existiert |
| RLS aktiv | ✅ `true` |
| Zeilen **gesamt** | **0** (nicht nur Juni/Riedmann — die Tabelle ist komplett leer, es wurde nie gestempelt) |
| Schema | `id uuid` · `worker_id text` · `ts timestamptz` · `direction text` · `device text NULL` · `created_at timestamptz NULL` |

**Policies — alle vier `is_staff()`:**

| Policy | cmd | USING / WITH CHECK |
|---|---|---|
| `stempel_log_select_staff` | SELECT | `is_staff()` |
| `stempel_log_insert_staff` | INSERT | WITH CHECK `is_staff()` |
| `stempel_log_update_staff` | UPDATE | `is_staff()` |
| `stempel_log_delete_staff` | DELETE | `is_staff()` |

**⚠️ Das ist der Kern-Blocker.** `is_staff()` = `role IN ('admin','buero','projektleiter')`. Ein
`stempel_terminal`-User ist **kein Staff** → er dürfte **nicht in `stempel_log` schreiben**. Die INSERT-Policy
lässt genau die Rolle nicht durch, für die das Terminal gedacht ist. Solange nur diese vier Policies
existieren, kann die eigenständige Stempeluhr keine Daten sammeln, selbst wenn RPC + User angelegt wären.

(Heute funktioniert das Stempeln nur, wenn ein **Staff-User** im Kiosk-Screen `?screen=stempel` eingeloggt
ist — dann greift `stempel_log_insert_staff`. Als dauerhaft offenes Werkstor-Terminal mit eigener Rolle
ist es nicht betriebsbereit.)

---

## 3) App-Seite — was live im Code ist (v3.9.768) und wo die Lücke sitzt

**Vollständig vorhanden:**
- **Kiosk-Screen `?screen=stempel`** — Gate in `_isKioskPath` (`index.html:7421`), rendert
  **ausschließlich** `StempelTafel` (`index.html:6590`); für `stempel_terminal` lädt der App-Bootstrap
  bewusst NICHTS (`index.html:7607`, sonst 403-Sturm über die 13 Portal-Fetches).
- **Toggle-Logik:** Scan → workers-Lookup per `nfc_uid` → letzter heutiger `stempel_log`-Eintrag bestimmt
  Richtung → INSERT via `POST /stempel_log` (`index.html:6811`). `id` ist eine echte uuid (v-Fix gegen 22P02).
- **PZE-Rechenkern `//@PZE-START..@PZE-END`** (`index.html:4517–4605`, v3.9.692): `_pzeDayKey` (lokaler
  Kalendertag, DST-sicher), `_pzeUngerade` (unpaarige Stempel-Flag), `_pzeAutoPause`, `_pzeTagRow`,
  `_stTagNetto`/`_stPauseAbzug` (Brutto = Summe gerundeter Paare, Abzug 1×/Tag, nie negativ).
- **Büro-Auswertung `PZEView`** (`index.html:10944`, v3.9.692, „⏱ Stempelzeiten", Vorbild FinkZeit): liest
  `stempel_log` als Anwesenheits-Wahrheit, zeigt `time_entries` nur als neutrale Info-Spalte „Projektzeit".
  **Excel-Export** (`.xls`, `index.html:11117`) + **PDF-Export** (`index.html:11129`). Korrektur ist rein
  **additiv** (fehlender Stempel = neue Zeile `device='korrektur:<user>'`, nie UPDATE/DELETE — das Roh-Log
  ist die lohnrelevante Urkunde).

**Die Lücke zwischen „Code da" und „sammelt echte Daten":**

| Ebene | Status |
|---|---|
| App-UI (Kiosk, Tafel, Toggle) | ✅ fertig |
| PZE-Rechenkern + Büro-Auswertung + Export | ✅ fertig |
| RPC `stempel_terminal_workers()` | ❌ fehlt → Tafel lädt keine Worker |
| DB-Rolle `stempel_terminal` (auth + users) | ❌ nicht angelegt |
| `stempel_log`-INSERT für die Terminal-Rolle | ❌ nur `is_staff()`, Rolle ausgesperrt |
| `nfc_uid` an den Workern gepflegt | ⚠️ offen (nicht Teil dieser Prüfung — die Tafel matcht darüber) |
| Physisches Gerät am Werkstor + NFC-Leser | ⚠️ Hardware, außerhalb Software |

**Fazit:** Es fehlt **keine nennenswerte Software**, sondern das **DB-/Auth-Fundament** und die Hardware.
Genau das, was `STEMPEL_TERMINAL_v2.sql`/`TERMINAL_FINAL_v3.sql` liefern sollten — deren Kern-RPC aber
in der DB fehlt (siehe `docs/SQL_STATUS_2026-07-20.md`: `is_kiosk_role()` + `*_no_kiosk`-Policies aus
`TERMINAL_FINAL_v3.sql` Abschnitt B **sind** gelaufen, der Terminal-RPC-Teil **nicht**).

---

## Schritt 1 zum Scharfmachen (Vorschlag — NICHT umgesetzt)

Reine Skizze, nichts davon ausgeführt. Reihenfolge:

1. **SQL-Run (Human-Gate, Sebastian):** `sql/TERMINAL_FINAL_v3.sql` gegen die Live-DB verifizieren und den
   **fehlenden RPC-/Policy-Teil** ausführen. Das Dokument ist idempotent; Abschnitt B ist schon durch, es
   geht um: RPC `stempel_terminal_workers()` + einen **`stempel_log`-INSERT-Zweig, der `stempel_terminal`
   durchlässt** (analog `lager_display`). **Vor dem Run** verifizieren, dass der SQL-Inhalt exakt das
   anlegt — der Datei-Kopf ist nachweislich veraltet (behauptet „gelaufen", ist es nicht).
2. **Auth-User `stempel_terminal` im Supabase-Dashboard anlegen** (kein `auth.users`-Write aus der App —
   TABU) + `public.users`-Zeile mit `role='stempel_terminal'`.
3. **`nfc_uid` an den Monteuren pflegen** (sonst matcht die Tafel keinen Scan).
4. **Live-Smoke am Terminal:** einloggen als `stempel_terminal`, Scan → Kommen, Scan → Gehen, prüfen dass
   `stempel_log` füllt und `PZEView` (Büro) die Zeilen zeigt.
5. **Hardware** (Gerät + NFC-Leser am Werkstor) — außerhalb Software.

**Erst wenn 1–3 stehen, ist die App-Seite betriebsbereit — sie ist es code-seitig schon.** Danach ist der
Weg zu „FinkZeit ablösen" die schon existierende PZE-Monatsübersicht (`PZEView` + Export), gespeist aus
echten `stempel_log`-Daten statt aus null.

**Offene Detailfragen (für den Bau, nicht jetzt):** exakter SQL-Inhalt von `TERMINAL_FINAL_v3.sql`
gegenprüfen; Pausenregeln je Rolle (`system_config.stempel_pause_rules`) bestätigen; ob die
Monatsübersicht 1:1 dem FinkZeit-Layout folgen muss.
