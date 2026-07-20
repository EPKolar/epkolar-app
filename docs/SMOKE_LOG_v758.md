# SMOKE-Volllauf — Live-Stand (Muster v3595)

**Auftrag:** Sebastian, „alles live durchchecken". Live-Chrome-Session (claude-in-chrome), STRIKT read-only.
Je Screen: 0 Console-Errors · 0 unhandled rejections · kein Error-Boundary-Fallback · kein sichtbares
„undefined"/„NaN"/„[object" · Grund-Interaktion crasht nicht. Bugs NICHT eigenmächtig fixen — Liste zuerst.

**Live-Version:** **v3.9.763-supabase** (github.io). **Tool:** claude-in-chrome + Write-Monitor (fetch-Wrapper
zählt PATCH/POST/DELETE auf arbeitsscheine + Juprowa-Push = Read-only-Beweis). **Stand: ABGESCHLOSSEN** — alle
4 Rollen durch (Admin, PL/schmid, Monteur/barger, Kiosk). **0 Bugs.** Beide Anfangs-Funde geklärt: SM-02 =
gewollte Admin-Freigabe (`perms_override`); SM-01 = erwartetes Session-Ablauf-Verhalten (Dev-Console-only,
Sebastian-Entscheid: nicht fixen).
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
- **📊 Auswertungen: 🟢** — für Monteur sichtbar, aber **gewollt** (perms_override `auswertungen:true`, vom
  Admin freigegeben; ursprüngl. als SM-02 geflaggt, nach DB-Check zurückgezogen).
- **Read-only-Bilanz:** 0 kritische Writes über die ganze Monteur-Session (Monteur triggert keinen
  Juprowa-Pull, da nicht canSync).

**Monteur-Funde: keine** (SM-02 = gewollte perms_override-Freigabe, zurückgezogen).

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

### GEKLÄRT — kein Bug
- **SM-02 (zurückgezogen)** — „Monteur sieht Auswertungen" ist **gewollt**: die Nav gated per
  `hasPerm(curUser,"auswertungen")`, und `hasPerm` (index.html Z. 4594-4596) respektiert das per-User-Feld
  **`permsOverride`** ÜBER die Rollen-Default-Module. DB-Check (live, read-only): **alle 5 Monteure**
  (riedmann/barger/aliti/cracana/kiener) haben `perms_override = {stunden,werkzeuge,auswertungen,fahrzeuge,
  material_order: true}` — vom Admin bewusst freigegeben. App verhält sich korrekt. *(Ursprünglicher
  False-Positive: nur die harte `canDo`-Default-Map betrachtet, nicht die DB-Overrides.)* Der Mitarbeiter-Tab
  zeigt Monteuren nur eine begrenzte Sicht (keine fremde PII).

### GEKLÄRT — kein Bug (Forts.)
- **SM-01 (geschlossen, erwartetes Verhalten)** — Der `400` auf `token?grant_type=refresh_token` tritt
  **nicht** bei jedem Cold-Load auf, sondern nur bei einer **abgelaufenen gespeicherten Session**: die App
  refresht mit dem stale `refresh_token`, GoTrue antwortet korrekt `400 (invalid_grant)`, die App fängt das
  sauber und zeigt den Login. Ein **wirklich frischer** Browser (kein `epkolar_refresh`) macht gar keinen
  Refresh-POST (Guard `if(!_rt)`, index.html Z. 1341/1379) → kein 400. Der 400 ist damit die korrekte
  Server-Antwort auf Session-Ablauf, rein im Dev-Console sichtbar (kein User-Impact, UX korrekt).
  **Bewusst NICHT gefixt** (Sebastian-Entscheid): den Refresh zu überspringen würde unnötige Re-Logins
  riskieren (refresh_token opak, Gültigkeit lokal nicht prüfbar) — schlechtere UX als ein benignes Console-Log.

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
Screen. **0 Bugs.** Beide Anfangs-Funde nach genauerer Prüfung geklärt: **SM-02** „Monteur sieht Auswertungen"
= gewollte Admin-Freigabe via `perms_override`; **SM-01** 400-Refresh = korrektes Session-Ablauf-Verhalten
(Dev-Console-only, bewusst nicht gefixt). Die neuen Features live bestätigt: #28d-Vollbilanz (Invariante hält),
#1-Teil-2-Sperr-Toggle (40 Toggles, keine Kollision), Dispo read-only (#26), RLS/§96 je Rolle korrekt
(Monteur ohne Dispo/Flotte/Admin; PL mit Dispo/Flotte ohne Admin/Chef).

Nicht in diesem Lauf (interaktiv/Schreibpfad, gehören zur gemeinsamen Prüfung): der Sperr-Toggle-Klick
(dispo_blocks-Write) und Formular-Speichern — bewusst read-only ausgelassen.
