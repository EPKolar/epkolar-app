# Smoke-Log v3.8.18 · Rest der Smoke-Tests nach Nacht-2

**Stand**: 2026-04-19 (v3.8.19 Block F)
**Basis**: Nacht-2 smoke-basis 0-2 ist grün (DB_VER=7, APP_VERSION v3.8.18,
`_curUser`/`_b017check`/`_selfTest` alle PASS).

Dieses File sammelt die **verbleibenden** Smoke-Tests. CC kann nur Code-Level
verifizieren — UI-/Browser-Tests sind Sebastian-Aufgabe.

---

## Abschnitt 1 · 4 UI-Fixes visuell (v3.8.0)

### T-1 · Mitarbeiter-Dropdown: 9 Einträge (nicht 18)

**Ziel**: FinkZeit-Monatsabrechnung-Dropdown zeigt nur aktive Monteure (9 stückweise),
nicht inkl. Ex-Monteure (18 stückweise).

**CC Code-Check**: Komponente nutzt `allMA` / `monteure` — filter auf `m.aktiv !== false`
oder `m.austritt` leer? Zu prüfen in FinkZeit-Tab.

**Sebastian-Test**:
- Login als admin → Tab "Stunden" → FinkZeit-Panel → Mitarbeiter-Dropdown öffnen
- Erwartet: 9 Einträge (nur Ex-Ausgetretene raus)
- PASS [  ] / FAIL [  ] — Notiz:

### T-2 · Monatsabrechnung-Kachel: Namen (nicht nur Zahl)

**Ziel**: Home-Dashboard zeigt Namen der nicht-freigegebenen Monatsabrechnungen,
nicht nur Count.

**CC Code-Check**: Siehe v3.8.19 Block C.2 Sorgenkind-Widget — Namen werden jetzt
auch in der Chef-Seite angezeigt. Im Home-Dashboard: v3.8.0-Fix prüfen.

**Sebastian-Test**:
- Login als admin → Home-Dashboard → Monatsabrechnung-Kachel
- Erwartet: Namen der offenen MA-Einreicher anstatt reiner Zahl
- PASS [  ] / FAIL [  ] — Notiz:

### T-3 · 38,5h-Auslastung: 38,5h = 100% (nicht 96,25%)

**Ziel**: Auslastungs-Balken rechnet gegen 38,5h als 100%-Marke.

**CC Code-Check**: index.html:13594 `const pct=Math.round(h/38.5*100);` — ✅ 38.5h
als Divisor. 100% = 38.5h genau. **Code-verified PASS.**

**Sebastian-Test** (Bestätigung):
- Login als admin → Chef-Seite → Auslastung diese Woche
- Monteur mit exakt 38.5h Week-Summe: Balken 100%
- PASS [  ] / FAIL [  ] — Notiz:

### T-4 · Riedmann-Nav: `riedmann` Login → nur Monteur-Tabs

**Ziel**: User `riedmann` (role=monteur) sieht nur monteur-Tabs.

**CC Code-Check**: index.html:4357+ Tab-Permission-Matrix — `_chef` perm gated auf
`curUser.role==="admin"`. Riedmann sollte also Chef-Tab NICHT sehen. Monteur-Tabs
sichtbar per perm-Check (`m.role==='monteur'` oder tab.perm check).

**Sebastian-Test**:
- Login als `riedmann` (wenn Account existiert — ggf. OOF)
- Erwartet: Home, Projekte (oder ähnlich), AS, Zeit, Urlaub, Fahrzeuge, Werkzeuge, Einstellungen
- NICHT sichtbar: Chef, Admin, Büro-Export, Stunden
- PASS [  ] / FAIL [  ] — Notiz:

---

## Abschnitt 2 · Photos-Upload (B-021 Status Quo)

**Ziel**: Foto-Upload funktioniert, `uploaded_by` wird korrekt gesetzt (v3.8.12 Fix).

**CC Code-Check**: index.html:2040 (captureAndQueue) liest `_user` via
`JSON.parse(localStorage.getItem('epkolar_user'))`.name oder .username. ✅ Fix
v3.8.12 aktiv.

**Sebastian-Test**:
1. Login als `paschinger/test1234` (falls GoTrue fail: auf schober ausweichen)
2. AS → Foto aufnehmen → POST 201 Created erwartet
3. Supabase SQL: `SELECT uploaded_by FROM photos ORDER BY uploaded_at DESC LIMIT 1`
   → Erwartet: `'w1'` (paschinger-worker_id) oder entsprechend
4. **Cross-User-Sichtbarkeit NICHT teil des Tests** (B-021 Status Quo bewusst)

- Upload-POST 201: PASS [  ] / FAIL [  ]
- uploaded_by korrekt: PASS [  ] / FAIL [  ]
- Notiz:

---

## Abschnitt 3 · Cross-User-Cleanup (v3.8.10/11)

**Ziel**: Logout mit "verwerfen"-Confirm cleart SQ + PhotoQ + User-Data-ODB-Stores.

**CC Code-Check**: index.html:4229+ logout() Handler — v3.8.10 (SQ/PhotoQ.clear)
und v3.8.11 (13 ODB stores) Fixes aktiv. ✅ Code-verified.

**Sebastian-Test**:
1. User A (Sebastian) Login → Timer starten → Offline gehen → irgendeine Mutation
2. Logout mit "verwerfen"-Button (SQ/PhotoQ-Dialog bestätigen)
3. User B (schober) Login
4. Browser-Console:
   - `JSON.parse(localStorage.getItem('epk_timer'))` → `null` erwartet
   - `JSON.parse(localStorage.getItem('epkolar_user'))` → schober-Objekt
   - `window._syncDiag()` → `total === 0`
5. IndexedDB Inspektor (DevTools → Application → IndexedDB → epkolar_offline):
   - `entries/arbeitsscheine/monteure/...` Stores: leer oder nur User-B-scoped Daten

- Timer null: PASS [  ] / FAIL [  ]
- epkolar_user User B: PASS [  ] / FAIL [  ]
- syncQueue leer: PASS [  ] / FAIL [  ]
- IDB stores User-B-only: PASS [  ] / FAIL [  ]
- Notiz:

---

## Abschnitt 4 · Login-Regression (4 User für CC-Scope)

**CC-Scope**: admin, schober, riedmann, lindhuber.
**OOF-Scope**: paschinger, barger, cracana, pinger, schmid (5 nie-eingeloggte — Sebastian-Aufgabe separat).

### T-admin (guenther)

- Login: ✅ schon im Nacht-2-Smoke grün
- Dashboard-Load: ✅
- Chef-Tab sichtbar: PASS [  ] / FAIL [  ]

### T-schober

- Login schober/test1234: PASS [  ] / FAIL [  ]
- Role=buero erkannt: PASS [  ] / FAIL [  ]
- Keine monteur-only-Tabs sichtbar: PASS [  ] / FAIL [  ]

### T-riedmann

- Login riedmann/test1234 (oder bekanntes PW): PASS [  ] / FAIL [  ]
- Role=monteur Tabs: PASS [  ] / FAIL [  ]

### T-lindhuber

- Login lindhuber/test1234: PASS [  ] / FAIL [  ]
- Role=buero: PASS [  ] / FAIL [  ]

---

## Rot-Regel Anwendung

Wenn irgendwo oben FAIL markiert ist:
- Sebastian dokumentiert den konkreten Fehler (Console-Error, Screenshot, Beschreibung)
- CC schiebt v3.8.19-wip-hotfix NUR für diese eine Stelle
- Dann weiter zu Block G (Logging + Silent-Catch)

Wenn alles grün/OOF:
- Block G sofort starten

---

## CC-Ehrlichkeit

CC kann nicht im Browser klicken oder DB queryen. Diese Smoke-Tests sind
**Anleitungen für Sebastian**, nicht CC-ausgeführt. Code-Level-Befunde
(T-3, Photos-captureAndQueue, Logout-Handler) sind in den T-Kästen explizit
als "CC Code-Check PASS" markiert.

Alle mit "[  ]" markierten Felder sind Sebastian-TODO.
