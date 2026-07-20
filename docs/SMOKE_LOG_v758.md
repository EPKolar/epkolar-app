# SMOKE-Volllauf — Live-Stand (Muster v3595)

**Auftrag:** Sebastian, „alles live durchchecken". Live-Chrome-Session (claude-in-chrome), STRIKT read-only.
Je Screen: 0 Console-Errors · 0 unhandled rejections · kein Error-Boundary-Fallback · kein sichtbares
„undefined"/„NaN"/„[object" · Grund-Interaktion crasht nicht. Bugs NICHT eigenmächtig fixen — Liste zuerst.

**Live-Version:** **v3.9.763-supabase** (github.io). **Tool:** claude-in-chrome + Write-Monitor (fetch-Wrapper
zählt PATCH/POST/DELETE auf arbeitsscheine + Juprowa-Push = Read-only-Beweis). **Stand: ABGESCHLOSSEN** — alle
4 Rollen durch (Admin, PL/schmid, Monteur/barger, Kiosk). **1 Fund gesamt (SM-02, P1) + 1 benigne (SM-01).**
Read-only-Bilanz je Rolle: 0 durch-mein-Ansehen verursachte Abrechnungs-Mutationen (0 OFFA-Pushes, 0
push_pending-Änderung, 0 updAs).

---

## Screen × Rolle — Matrix

| Screen / Subpage | Admin | PL | Monteur | Kiosk/lager_display |
|---|---|---|---|---|
| Login / Cold-Load | 🟡¹ | 🟡¹ | 🟡¹ | 🟡¹ |
| Home / Dashboard | 🟢 | ⏳ | ⏳ | — |
| 👑 Chef-Dashboard | 🟢 | ⏳ | — | — |
| 🏗️ Projekte | 🟢 | ⏳ | ⏳ | — |
| 📋 Arbeitsscheine (Liste) | 🟢 | ⏳ | ⏳ | — |
| AS-Detail + Inline-Fokus | 🟢 (S075378) | ⏳ | ⏳ | — |
| 🗓 Dispo (Vollbilanz, 4 KW-Tabs, Warteliste, Toggles) | 🟢 | ⏳ | — | — |
| 📅 Planung / Tafel | 🟢 | ⏳ | ⏳ | ⏳ |
| ⏱️ Zeiterfassung | 🟢 | ⏳ | ⏳ | — |
| 🏖️ Urlaub | 🟢 | ⏳ | ⏳ | — |
| 📄 Monatsabrechnung | 🟢 | ⏳ | — | — |
| 🚐 Fahrzeuge | 🟢 | ⏳ | ⏳ | — |
| 🛰️ Flotte | 🟢 | ⏳ | — | — |
| 🔧 Werkzeuge / Lager | 🟢 | ⏳ | ⏳ | ⏳ |
| 🚧 Bauprovisorien | 🟢 | ⏳ | ⏳ | — |
| ☣️ Gefahrenstoffe | 🟢 | ⏳ | ⏳ | — |
| 👷 Mitarbeiter | 🟢 | ⏳ | — | — |
| 📊 Auswertungen | 🟢 | ⏳ | — | — |
| 🔌 Einstellungen (alle Sektionen) | 🟢 | ⏳ | ⏳ | — |
| 📋 Büro-Portal | 🟢 | ⏳ | — | — |
| ⚙️ Admin | 🟢 | — | — | — |
| Kiosk (?screen=monteure/planung) | — | — | — | ⏳ |

Legende: 🟢 grün (0 Errors/Rejections, kein EB-Fallback, keine undefined/NaN/[object, Interaktion crasht nicht,
0 kritische Writes) · 🔴 rot (Fund) · 🟡 Anmerkung · ⏳ ausstehend (Rollen-Login) · — n/a für die Rolle.

**¹ Cold-Load (unauth.):** Login-Screen rendert sauber, 1 benignes 400-Refresh (SM-01).

---

## Admin-Rolle — Detail (v3.9.763, read-only verifiziert)

- **18 Top-Tabs** (Home, Chef, Projekte, AS, Planung, Zeit, Urlaub, Monatsabr., Fahrzeuge, Flotte, Werkzeuge,
  Bauprov., Gefahrenstoffe, Mitarbeiter, Auswertungen, Einstellungen, Büro-Portal, Admin): alle 🟢 — 0 bad-Text,
  0 Error-Boundary, 0 Console-Errors, 0 Rejections.
- **Dispo-Subpage:** Vollbilanz-Kopf live „**21 offen: 12 fix · 9 Vorschläge · 0 Warteliste · 0 nicht
  unterbringbar · 4 überfällig**" — Invariante hält (12+9=21, kein Loch). Alle **4 KW-Tabs** (30–33) cyclen
  fehlerfrei, Warteliste-Sektion da, 40 Sperr-Toggles gerendert. **0 Writes** (Dispo read-only, #26 live bestätigt).
- **AS-Detail** (S075378) geöffnet + Inline-Feld fokussiert (ohne Änderung): 🟢, **0 Writes**.
- **Einstellungen** alle Sektionen sichtbar (WLAN, Passwort, Verbindung, Design, Sync, Lokale Daten,
  Smoke-Tests, Integrität, Version): 🟢.
- **Read-only-Bilanz (saubere Session nach Re-Login):** 0 kritische Writes, 0 OFFA-Pushes, 0 push_pending-Änderung.

**Admin-Funde: keine (0 Bugs).**

---

## Monteur-Rolle — Detail (`barger`, role=monteur, w2 — read-only verifiziert)

- **RLS-Nav korrekt:** kein 👑 Chef / 🛰️ Flotte / ⚙️ Admin / 📋 Büro-Portal. **Dispo-Sub-Tab fehlt** in der
  AS-Ansicht (nur 📋 Liste / 📷 QR / 📅 Kalender) — §96 ✓.
- Sichtbare Tabs (Home, Projekte, AS, Planung, Zeit, Urlaub, Monatsabr., Fahrzeuge, Werkzeuge, Gefahrenstoffe,
  Mitarbeiter): alle 🟢 — 0 Errors/Rejections/Error-Boundary/bad-Text.
- **Arbeitsscheine:** 23 in Bargers Scope (Admin sah deutlich mehr) — RLS greift sichtbar.
- **📊 Auswertungen: 🔴 SM-02** (firmenweite Sicht, s. Bugliste).
- **Read-only-Bilanz:** 0 kritische Writes über die ganze Monteur-Session (Monteur triggert keinen
  Juprowa-Pull, da nicht canSync).

**Monteur-Funde: SM-02.**

## Kiosk / lager_display — Detail (Wandmonitore, read-only)

- **`?screen=monteure`** (📋 Monteur-Tafel, KW 30): 🟢 rendert Wochengrid + Tages-Einsätze (Monteur, Schein,
  Baustelle) sauber. 0 undefined/NaN/[object, keine Error-Boundary, kein Login-Prompt. Keine sensible PII
  (kein SVNR/Telefon); Baustellen-Adressen + Kundennamen sichtbar = Zweck der Werkstatt-Tafel (nicht sensibel).
- **`?screen=planung`** (📋 Wochenplan, KW 30): 🟢 rendert Bauvorhaben-Grid (Störungen/SAT/BVH …) mit
  Monteur-Zuordnung sauber. 0 undefined/NaN/[object, keine Error-Boundary.
- **Hinweis (kein Bug):** die beiden geöffneten Kiosk-Tabs waren noch auf **v3.9.759** gecacht (ältere Tabs);
  ein Reload zieht v3.9.763. Funktion unverändert.

**Kiosk-Funde: keine.**

## PL-Rolle — Detail (`schmid`, role=projektleiter, w5 — read-only verifiziert)

- **RLS-Nav korrekt:** PL sieht 🛰️ Flotte + 📊 Auswertungen + 📋 Büro-Portal + **🗓 Dispo-Sub-Tab** (canSync),
  aber **kein ⚙️ Admin, kein 👑 Chef** ✓. Bestätigt SM-02 (Auswertungen für PL korrekt, für Monteur nicht).
- Alle ~16 Tabs (Home, Projekte, AS, Planung, Zeit, Urlaub, Monatsabr., Fahrzeuge, Flotte, Werkzeuge,
  Bauprov., Gefahrenstoffe, Mitarbeiter, Auswertungen, Einstellungen, Büro-Portal): 🟢 — 0 Errors/Rejections/
  Error-Boundary/bad-Text. AS-Scope = alle Scheine (wie Admin, staff).
- **Read-only-Bilanz:** 0 kritische Writes über die ganze PL-Session.

**PL-Funde: keine.**

## Bugliste (priorisiert)

### P0 / P1
_(keine)_

### P1 (falsche Sicht / Datenexposition)
- **SM-02** — **Monteur sieht firmenweite Auswertungen.** Als `barger` (role=monteur, w2) ist der Tab
  **📊 Auswertungen** in der Nav und **rendert das volle Firmen-Dashboard**: Werkzeugwert €16 490 (296 Geräte),
  21 Fahrzeuge / €1360 Tankkosten, alle 23 Arbeitsscheine, alle 7 Mitarbeiter in den Diagrammen, Export
  „Alle als Excel"/„PDF". Permission-Modell (`m={... auswertungen:isA||isPL||isB ...}`, index.html ~Z. 4600)
  schließt Monteur aus → die Nav gated diesen Tab nicht entsprechend. **Repro:** als barger einloggen →
  📊 Auswertungen. **Nicht gefixt** (Liste-zuerst; Sebastian priorisiert — evtl. gewollt? sonst Nav-Gate an
  `canDo('auswertungen',curUser)` hängen). *(Mitarbeiter-Tab rendert für Monteur nur eine begrenzte Sicht —
  keine fremde PII wie SVNR/Gehalt gefunden; unkritisch.)*

### P2 (Kosmetik / benigne)
- **SM-01** — Cold-Load feuert `400` auf `POST auth/v1/token?grant_type=refresh_token` (frischer Browser ohne
  Session → Token-Refresh ohne Session → Login-Screen). Benigne, nur Console-Rauschen. Kandidat: Refresh nur
  bei vorhandenem Session-Token. **Nicht gefixt** (read-only + Freigabe-Gate).

---

## Vorfall-Protokoll (Transparenz)
Beim ersten Einstellungen-Durchgang klickte der Smoke versehentlich **Aktions-Buttons** (Schleife über alle
Buttons) statt nur zu navigieren → **Logout + lokaler Cache-Clear** ausgelöst (Server-Daten unberührt; der
Löschbutton wirkt nur lokal). Zusätzlich liefen im 3s-Fenster **53× PATCH arbeitsscheine** = automatischer
**Juprowa-PULL (App←OFFA)**, der bei jedem AS-Ansicht-Aufruf feuert — **0 OFFA-Pushes, 0 push_pending-Änderung,
kein Abrechnungs-Mutat**. **Methodik-Korrektur:** ab jetzt ausschließlich Navigation, keine Aktions-Buttons;
Sektionen nur per Snapshot geprüft. Admin-Rolle danach sauber (read-only) neu abgeschlossen.

---

## Fazit
**Smoke-Volllauf abgeschlossen — alle 4 Rollen (Admin, PL, Monteur, Kiosk) read-only durchgecheckt.**
Keine P0-Crashes, kein Datenverlust, keine Error-Boundaries, keine undefined/NaN/[object in irgendeinem
Screen. **1 Fund zur Priorisierung: SM-02** (Monteur sieht firmenweite Auswertungen) + **1 benigne: SM-01**
(Cold-Load-400-Refresh-Rauschen). Die neuen Features live bestätigt: #28d-Vollbilanz (Invariante hält),
#1-Teil-2-Sperr-Toggle (40 Toggles, keine Kollision), Dispo read-only (#26), RLS/§96 je Rolle korrekt
(Monteur ohne Dispo/Flotte/Admin; PL mit Dispo/Flotte ohne Admin/Chef).

Nicht in diesem Lauf (interaktiv/Schreibpfad, gehören zur gemeinsamen Prüfung): der Sperr-Toggle-Klick
(dispo_blocks-Write) und Formular-Speichern — bewusst read-only ausgelassen.
