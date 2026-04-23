# NEXT CHAT — ab v3.5.23

## Nächster Chat: Monatsabrechnung Monteur (VMonatsblatt)

### Konzept
- Monteur sieht Kalender-Monatsansicht (read-only) seiner Zeitbuchungen
- Tage mit Buchungen farbig markiert, Stunden pro Tag sichtbar
- Monatsgesamt + Überstunden-Berechnung
- "Änderung beantragen" Button → Notification an Admin/PL
- "Unterschreiben" mit digitalem Zeitstempel (Monteur bestätigt Richtigkeit)
- DB: `monthly_confirmations` Tabelle + optional `change_requests`

### Danach: Planung Multi-Tag — MIT SEBASTIAN KLÄREN
- Mo-Fr Buttons in Cell-Picker existieren — was genau geht nicht?
- Alternative: Bulk-Assign Modal (Monteur+Projekt auf mehrere Tage gleichzeitig)

## Offene Tests nach Push v3.5.23
- [ ] Bautagebuch: HKLSE-Chips sichtbar? Gewerk-Tabs wechselbar?
- [ ] Chip-Klick → Text wird an Tätigkeiten angefügt mit "; "?
- [ ] Mitarbeiter: Mobile — größere Schrift, Cards lesbar?
- [ ] Detail-Grid: Labels + Werte gut lesbar auf Handy?
- [ ] Projekt-Zuweisungen: Toggle + Text gut tippbar?

## Backlog (priorisiert)
1. ~~Bautagebuch HKLSE-Chips~~ ✅ DONE
2. ~~Mitarbeiter Lesbarkeit~~ ✅ DONE
3. Monatsabrechnung Monteur (VMonatsblatt) ← NEXT
4. Planung Multi-Tag (mit Sebastian klären)
5. Material Umbau (mit Sebastian besprechen!)
6. Dashboard-KPIs live
7. Benachrichtigungen 2.0
8. Urlaubsplanung visuell
9. QR-Code AS
10. Offline-Indikator
11. Multi-Projekt WÜ PL

## Operativ
- Schober PW = "test1234" → ändern
- Lindhuber PW → setzen
