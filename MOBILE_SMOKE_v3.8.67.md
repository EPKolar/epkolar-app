# Mobile Smoke-Test v3.8.67 — Sebastian's Handy

Branch: `cc-mobile-refactor/2026-04-30`
Vorbedingung: PWA gepusht, Service-Worker neu installiert (Reload mit hard refresh oder via Burger-Menü "🔌 Einstellungen → Cache löschen").

Test auf einem realen Phone (320–480px) und einem Tablet im Portrait (~768px).

Pro Punkt: ✅ OK / ❌ ROT / ❓ unklar

---

## 1) Login & Boot

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 1.1 | App im Browser/PWA öffnen | Login-Screen erscheint, Logo zentriert, Eingabefelder einlogbar (kein H-Scroll) | ⬜ |
| 1.2 | Login mit `riedmann/12345678` (oder Test-User) | Dashboard lädt, kein Loop | ⬜ |
| 1.3 | Hardrefresh (3x reload nacheinander) | KEIN Loop-Counter Reset, kein automatic-logout | ⬜ |

## 2) Sidebar / Burger-Menü (v3.8.66)

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 2.1 | Burger-Icon (oben links) sichtbar? | Ja, ≥40×40px tap-Area | ⬜ |
| 2.2 | Burger antippen | Sidebar gleitet von links rein, mit dunklem Backdrop | ⬜ |
| 2.3 | Backdrop antippen | Sidebar schließt | ⬜ |
| 2.4 | Sidebar offen — alle Navi-Punkte sichtbar (Home, Chef, Projekte, Arbeitsscheine, Planung, Zeiterfassung, Urlaub, Monatsabrechnung, Fahrzeuge, Werkzeuge, Mitarbeiter, Auswertungen, Einstellungen, Büro-Export, Admin)? | Alle 13–15 (rollenabhängig) sichtbar, scrollbar wenn nötig | ⬜ |

## 3) Bottom-Nav (5-Bucket-Layout)

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 3.1 | Bottom-Nav mit 5 Buttons sichtbar (🏠 Home / 🏗️ Baustelle / ⏱️ Zeit / 🚐 Fuhrpark / ⚙️ Mehr)? | Ja, fixiert am unteren Rand | ⬜ |
| 3.2 | Jeder Button antippen → wechselt zur Top-Tab dieser Gruppe | g:0 Home/Chef · g:1 Projekte/AS · g:2 Planung/Zeiterf./Urlaub/Monatsabr. · g:3 Fahrzeuge/Werkzeuge · g:4 Popup mit Mitarbeiter/Auswertungen/Einstellungen/Büro-Export/Admin | ⬜ |
| 3.3 | "Mehr" antippen → Popup über Bottom-Nav | Liste mit allen g:4-Tabs, jeder antippbar (≥40px) | ⬜ |
| 3.4 | Aktiven Bucket nochmals antippen | Wechselt zum nächsten Tab in dieser Gruppe (Round-Robin) | ⬜ |
| 3.5 | Sichtbarkeit nach Rolle: monteur sieht KEIN Admin/Auswertungen/Einstellungen/Mitarbeiter | Ja (rollengefiltert) | ⬜ |

## 4) Tabellen — kein H-Scroll auf Phone

Auf 320–380px Phones testen:

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 4.1 | Tab `Arbeitsscheine` öffnen | Tabelle füllt Bildschirm, kein Body-H-Scroll. Spalten kompakt. ggf. Scrollbar nur in der Tabelle selbst (nicht der Page) | ⬜ |
| 4.2 | Tab `Projekte` öffnen | dito | ⬜ |
| 4.3 | Tab `Fahrzeuge` öffnen | dito | ⬜ |
| 4.4 | Tab `Werkzeuge` öffnen | dito | ⬜ |
| 4.5 | Tab `Auswertungen` öffnen → Bericht-Tabelle (`.ber-table`) | Spalten enger, Schrift 11px, kein H-Scroll | ⬜ |
| 4.6 | Tab `Mitarbeiter` öffnen | KPI-Karten 2-spaltig oder 1-spaltig (je nach Breite), Mitarbeiter-Liste lesbar | ⬜ |
| 4.7 | Tab `Wochenplanung` öffnen | Kalender-Grid responsiv (notfalls eigener H-Scroll innen, kein Body-Scroll) | ⬜ |

→ ROT melden wenn die GANZE Page horizontal scrollt (das ist der Fehler). Wenn nur eine Tabelle innen scrollt = OK.

## 5) Inputs / Form-Breiten

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 5.1 | AS → "QR Scan" Tab → Scheinnummer-Input | Input nimmt 100% Breite, kein Überlauf | ⬜ |
| 5.2 | Einstellungen → Material → DATANORM neu importieren | System/Kategorie/Trade-Inputs alle volle Breite, gestapelt | ⬜ |
| 5.3 | Einstellungen → System-Config | Werte-Inputs volle Breite | ⬜ |
| 5.4 | Fahrzeuge → Fahrtenbuch | Monat-Picker volle Breite | ⬜ |
| 5.5 | Login-Modal/Modals generell | Zentriert, max-width respektiert, kein Überlauf | ⬜ |

## 6) Touch-Targets — Daumenfreundlich

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 6.1 | TopBar: Theme-Toggle (☀️/🌙), Notif-Glocke, Sync-Button | Jeder Button ≥40×40px, mit Daumen treffbar | ⬜ |
| 6.2 | AS-Tabellen-Aktionen (✏️ 📄 ⬜ ☁️↑ ⊘) | Jeder ≥40px hoch (auch wenn kompakt nebeneinander) | ⬜ |
| 6.3 | Modal-Schließen (✕) bei Notif/Sync/Photo-Queue/iOS-Install | Tap-Area ≥44×44, leicht treffbar | ⬜ |
| 6.4 | Filter-Chips (Search-Modal Categories) | Jeder ≥40px hoch | ⬜ |
| 6.5 | Bottom-Nav-Buttons | Jeder Button ≥40px hoch (meist 60px durch Padding) | ⬜ |

## 7) Funktionscheck Light

| # | Schritt | Erwartet | Status |
|---|---------|----------|--------|
| 7.1 | Arbeitsschein anlegen, abspeichern | Geht durch, erscheint in der Liste | ⬜ |
| 7.2 | Zeiteintrag erfassen | Geht durch | ⬜ |
| 7.3 | Foto an AS hängen | Photo-Picker geht auf, Bild lädt hoch | ⬜ |
| 7.4 | Sync-Button: tippen → Sync läuft, OFFLINE-Banner verschwindet | Ja | ⬜ |
| 7.5 | Logout / Re-Login | Geht ohne Loop | ⬜ |

---

## Was als ROT zu markieren ist

- Body-H-Scroll an irgendeinem Tab → ROT (Phase 3 hat versagt)
- Bottom-Nav Button reagiert nicht auf Tap → ROT (sehr unwahrscheinlich)
- Ein Menüpunkt fehlt, obwohl die Rolle ihn haben sollte → ROT
- Touch-Target visuell <30px → ROT (testen mit Daumen, nicht mit Maus)
- Sidebar/Drawer öffnet/schließt nicht → ROT (Phase v3.8.66 hat versagt)
- Modal-Schließen-X nicht treffbar → ROT
- App-Loop (Reload, Reload, Reload) → SOFORT KILL und Sebastian melden

## Was als OK zu sehen ist

- Tabellen scrollen INNEN (nicht die Page) → OK, Phase-3-Design
- Tabs in der "Mehr"-Liste sind kompakt → OK, by design
- Auf Tablets 600–768px: Layout sieht aus wie Phone — OK, gleiche CSS-Regel greift bis 768px
- Tabelle hat 8+ Spalten und auf Phone scrollt sie horizontal innen → OK (echte Stapelung wäre Refactor)

## Wenn alles ✅: in main mergen

```bash
git checkout main
git merge --no-ff cc-mobile-refactor/2026-04-30 -m "merge: v3.8.67 mobile-refactor"
git push
```

## Wenn rote Punkte: nicht mergen

Liste der roten Punkte an Sebastian/CC zurück, dann gezielt fixen oder ROLLBACK auf 27a0040.
