# Bug-Verfolgung v3.9.98 — Code-Analyse Sprint 76 Findings + Chat-Claude Live-DB

**Datum:** 2026-06-03
**HEAD:** `f5bd5d1` v3.9.97 (Audit-Prep)
**Modus:** Code-Analyse (kein Service-Role, kein MCP-Login)

---

## PRIO 0 — Sprint 76 15 Findings (Tabelle)

| # | Severity | Page | Rolle | Finding | Code-Site |
|---|---|---|---|---|---|
| P1-1 | P1 | StundenzettelView | helfer/monteur/techniker/obermonteur | `meineZettel` filtert `z.mitarbeiterId===curUser.id` aber Stundenzettel haben meistens `mitarbeiterId=monteur.id` (`w*`) → Field-User sehen LEERE Liste statt eigene. Cross-User-Leak in Gegenrichtung wenn `u*`-ID hochgeladen wurde | Z14680 |
| P1-2 | P1 | ZeiterfassungView | monteur/helfer | `loadAllOverview` (viewAll-Modus) liest alle entries UNABHÄNGIG von isAdmin → Console-Bypass | Z16282-16292 |
| P2-1 | P2 | AbsView | helfer | `kontingent`-Defaults hardcoded (25 Tage/192.5 h) statt aus DB pro Worker | Z13993 |
| P2-2 | P2 | FahrzeugView | buero | `isVAdmin = admin\|\|projektleiter` — buero nicht drin obwohl `canDo("fz_edit", buero)==true` | Z16940 |
| P2-3 | P2 | ArbeitsscheinView | techniker/obermonteur | `isMonteurRole=role===monteur\|\|role===helfer` — techniker/obermonteur sehen ALLE AS unfiltered | Z5921 |
| P2-4 | P2 | AdminPanel | buero (Backoffice) | `canDo("admin_panel")` nur für `rolle=Lagerleitung` → Schober/Lindhuber (rolle=Backoffice, role=buero) sehen Admin-Tab NICHT | Z5321/Z3587 |
| P2-5 | P2 | MitarbeiterView | buero | `isAdmin=admin\|\|projektleiter` — buero nicht drin obwohl `canDo("worker_edit", buero)==true` | Z5694 |
| P2-6 | P2 | ChefDashboard | zweiter GF | `role==="admin"` hartes Gate — `role=projektleiter mit rolle=Geschäftsführer` sieht Chef-Tab nicht | Z5318 |
| P3-1 | P3 | ZeiterfassungView | viewer | `_isFieldRoleZE` prüft 4 Rollen — `viewer` nicht abgefangen bei direktem Aufruf | Z16201 |
| P3-2 | P3 | AbsView | non-admin | `tog` early-returns ohne Toast → User klickt + nichts passiert | Z14019 |
| P3-3 | P3 | FahrzeugView | monteur | `addKm`-Handler kein `fzId===myFzId`-Check → Console-Bypass | Z17036 |
| P3-4 | P3 | WerkzeugView | helfer | `_wzPool` filtert auf `monteurId\|\|__none__` → helfer ohne monteurId → leere Liste | Z17999 |
| P3-5 | P3 | StundenzettelView | Lindhuber | `canUpload=admin\|\|username==="schober"` hardcoded statt role-basiert | Z14585 |
| P3-6 | P3 | AuswertungView | techniker | `techniker.modules` listet `auswertungen` NICHT (buero/obermonteur ja) — Konsistenz unklar | Z2609 |
| P3-7 | OK | Sidebar/TopBar | - | `Mehr`-Button gated auf `moreTabs.length>0` — OK |
| P3-8 | OK | Routing | - | Deep-link Admin-Route hat `&&hasPerm` Block — OK |

**Stats:** 15 Findings = 2 P1 + 6 P2 + 5 P3 + 2 OK.

---

## PRIO 1 — absences-Bug ROOT-CAUSE im Code GEFUNDEN

### Befund (Chat-Claude Live-DB)
- 30/30 absences kaputt: `worker_id = NAME` statt wX
- Verteilung: Günther 16×, Pinger 7×, Schmid 6×, Paschinger 1×
- `from_date/to_date` LEER ("")
- id-Key = "Name_YYYY-MM-DD"
- alle Status="beantragt", April 2026
- `time_entries 41/41 wX` ✓, `worker_projects 29/29 wX` ✓ → NUR `absences` betroffen

### Code-Analyse (Schreib-Pfad)

**Datei:** `index.html` `AbsView.tog`-Handler

```js
// Z14021
const tog=d=>{
  if(!isAdmin && sel!==myMonteurName) return;
  const k=sel+"_"+dk(d);          // ← id = NAME + "_" + Date
  const isDelete=abs[k]?.type===typ;
  setAbs(p=>{...});
  setApprovals(p=>({...p, [k]:"ausstehend"}));
  if(isDelete){
    SQ.push({url:"/api/absences/"+encodeURIComponent(k), method:"DELETE"});
  } else {
    // Z14027 ← SCHREIB-BUG
    SQ.push({
      url:"/api/absences",
      method:"POST",
      body:{
        id: k,                    // "Günther_2026-04-22"
        worker_id: sel,           // "Günther" ← NAME statt wX!
        type: typ,
        from_date: dk(d),
        to_date: dk(d),
        note: ""
      }
    });
  }
  // ...pushNotif(...)
};
```

### ENTSCHEIDUNG: **AKTIVER SCHREIB-BUG**

Der Code schreibt heute `worker_id = NAME` (`sel` ist der Mitarbeiter-Name aus Dropdown). Das ist KEINE Altlast — jeder neue Eintrag wird genauso kaputt geschrieben.

`from_date / to_date` werden technisch gesetzt (`dk(d)` = YYYY-MM-DD).
**Sebastian's Befund "von/bis leer ("")"** deutet auf Schema-Mismatch hin:
- Server-Tabelle `absences` hat möglicherweise Spalten `von`/`bis` statt `from_date`/`to_date`
- Oder `_mapBody` (NO-GO) hat ein TEXT_JSON_FIELDS-Mapping das fehlt
- Oder Sebastian's Diagnose-Tool prüfte andere Spalten

### CODE-FIX (NICHT applied — Sebastian-Action)

Lookup-Map: `monteure[].n` → `monteure[].id`:
```js
// Vor Z14021:
const _selWorker = (monteure||[]).find(m => m.n===sel);
const _workerId = _selWorker?.id || sel;  // Fallback NAME falls nicht gefunden
```

Then Z14027:
```js
body:{
  id: k,
  worker_id: _workerId,   // ← wX statt NAME
  type: typ,
  from_date: dk(d),
  to_date: dk(d),
  note: ""
}
```

**Plus:** id-Key sollte konsistent sein. Empfehlung: `id = _workerId + "_" + dk(d)` (wX-Prefix statt NAME-Prefix). Aber das ändert localStorage/IDB-Keys → Cleanup-Skript für bestehende cache-Daten nötig.

### Verhältnis absences vs urlaubsantraege

| Tabelle | Schreib-Pfad | Status |
|---|---|---|
| `absences` | `AbsView.tog` Z14021 + Z14026 (DELETE) + Z14049 (approve) + Z14050 (reject) + Z14053 (updateEntry) + Z14054 (bulkApprove) + Z14067 (approveAll) + Z14068 (rejectAll) | **Primärer Pfad** — Kalender-Click setzt Tag-Markierung |
| `urlaubsantraege` | `_api.post('urlaubsantraege', item)` Z15677 + GET Z15661 | v3.5.80 NEUE Tabelle — UI zeigt sie aber Tabelle LEER laut Chat-Claude |

**Konsolidierung-Plan:**
- `absences` = pro-Tag-Markierungen (1 Eintrag = 1 Tag mit Type), via Kalender-Click
- `urlaubsantraege` = Antrags-Datensatz (von/bis Range, status, grund), via Antrag-Formular
- Sebastian-Decision: behalten beide oder einer abschaffen?
- Wenn v3.9.x noch in `absences` schreibt → Konsolidierung nach `urlaubsantraege` ist Migration-Aufgabe

### SQL Vorbereitet (NICHT ausführen)

Datei: `sql/migrate_absences_fix_v3998.sql` — siehe nebenan.

---

## PRIO 2 — notifications-Masse (5775 Rows bei 9 Usern)

### Code-Pfad Analyse

**`pushNotif` Z4896:**
```js
const pushNotif=(type,title,body,targetUsers)=>{
  const targets = targetUsers || users.filter(u =>
    notifPrefs[u.id]?.[type]).map(u=>u.id);
  const newN = targets.map(tuid => ({
    id: uid()+Math.random().toString(36).slice(2,4),
    type, title, body,
    time: new Date().toISOString(),
    read: false, user: tuid,
    link: NOTIF_TYPES[type]?.cat || ""
  }));
  setNotifications(p => [...newN, ...p].slice(0,200));  // ← Client behält nur 200
  ODB.save("notifications", upd);
  if(newN.length>0){
    SQ.push({
      url: "/api/notifications/batch",
      method: "POST",
      body: { items: newN.map(...) }   // ← Server bekommt ALLE pro Target
    });
  }
  // ...sound + browser-notification
};
```

**Auto-Notifier Z4924 `_checkAutoNotifs`:**
- Cooldown via `localStorage.epk_autonotif_cd` mit 4h-Window (Z4930: `(now-cd[key])<14400000`)
- AS-Eskalation (>24h dringend), FZ-Pickerl (Sprint-?), etc.

**Cleanup/TTL: KEINER GEFUNDEN.**
- Z4899 `slice(0,200)` ist NUR Client-State
- Server hat keinen Auto-Prune
- localStorage-Cooldown kann gecleared werden (cache-clear, logout-cleanup) → Cooldown verloren → wiederholtes Re-Fire möglich

### Ursachen-Hypothesen (warum 5775)

1. **Fan-Out pro Target:** `pushNotif` Z4901 erzeugt N Rows pro Event (1 pro Target-User)
   - Bei "alle Admins benachrichtigen" mit 3 Admins → 3 Rows pro Event
2. **Auto-Notifier Cooldown-Loss:** wenn localStorage-Cooldown gecleared → wiederholtes Re-Fire
3. **Keine TTL:** alte Notifs werden nie gelöscht serverseitig
4. **2.164 Rows vor Mai:** historische Akkumulation seit Inbetriebnahme

### Plan

**Code-Fix (Sebastian-Decision):**
- Optional: Server-Side TTL (Trigger) für notifications älter X Tage + read=true
- Optional: Pro-Type Rate-Limit als Insert-Trigger (max 1 pro 4h pro user_id+type)
- KEIN sofortiger Code-Fix nötig

**Cleanup (jetzt machbar):**
- Sebastian: SQL-Skript ausführen das `read=true AND created_at < now() - 30 days` löscht

### SQL Vorbereitet (NICHT ausführen)

Datei: `sql/cleanup_notifications_v3998.sql` — siehe nebenan.

---

## PRIO 3 — Kleinere Datenlücken (NUR Dokumentation)

### 3.1 Fahrzeuge ohne pickerl/naechst_service-Datum
- N-719.920
- N-779.427
- TU-777DF
- TU-481FK

Sebastian-Action: Daten manuell ergänzen via FahrzeugView UI.

### 3.2 Arbeitsscheine ohne monteur-Zuweisung (10 Stück)
Vermutlich Büro-/Aufnahme. Sebastian-Action: verifizieren ob OK ist (status=aufgenommen/geplant) oder nachträglich zuweisen.

---

## Was bleibt blockiert (Sebastian lokal)

### Audit-Skript-Run
```powershell
$env:SUPABASE_SERVICE_ROLE = "<key>"
pwsh -File scripts\audit_v3_9_95.ps1 `
  -MonteurPw "<barger>" `
  -BueroPw   "<schober>" `
  -PLPw      "<pinger>" `
  -AdminPw   "<chef>"
```

Skripte bereit unter:
- `scripts/audit_v3_9_95.ps1` (All-in-One Kiener + 8 NO-OP Probes)
- `sql/migrate_remove_anon_users_select_v3997.sql` (anon-Lockdown VORZIEHEN)
- `sql/migrate_rls_hardening_v3997.sql` (Phase-3 Hardening)
- `sql/migrate_absences_fix_v3998.sql` (Altlast-Repair)
- `sql/cleanup_notifications_v3998.sql` (Mass-Cleanup)

### Wichtigste Probes
**Probe 3:** monteur PATCH self role → 403 erwartet; **wenn 200 → Self-Elevation-Lücke real → STOP + Hardening-Run**.

---

## Zwei Kern-Ergebnisse (Sebastian-Spec)

1. **15 Findings table:** siehe PRIO 0 oben.
2. **absences-Schreibpfad-Entscheidung:** **AKTIVER Code-Bug Z14027** (`worker_id=sel` = NAME). Nicht Altlast. Fix-Patch ready, Sebastian appliziert nach Decision (Schema vs. Konsolidierung).

— Ende Code-Verfolgung —
