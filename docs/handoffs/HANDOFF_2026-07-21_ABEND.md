# Handoff 2026-07-21 ABEND — Session-Abschluss (Context voll)

**Arbeitsklon** `C:\repos\epkolar-app`. **Letzter gepushter/LIVE Stand = v3.9.792** (`cd56244`), raw+Edge auf 792.
**⚠ Working Tree NICHT clean:** `index.html` hat eine **uncommittete, ungepushte** AS-`_setSub`-Zwischenarbeit
(Teil des ABGEBROCHENEN Etappe-2-Nachbesserungsversuchs, s.u.) — vor einem Rollback verwerfen. `git restore` war
in dieser Session geblockt; Stash verboten (bestehende Stashes-Tabu). pytest-Stand zuletzt grün: **1908 passed, 13 skipped**.

## ✅ Diese Session LIVE & abgenommen (v783–v791)
- **v783** EZ-Vorbelegung schließt genehmigte Abwesenheit aus (LA 2740). — **v784** Kiosk-Ansicht pro Tab überlebt
  SW-Hardreset. — **v785** Entfernungszulage 3-Stufen (klein 11,94 / mittel 30,00 / groß 62,04; **DDL gelaufen**,
  `sql/ENTFERNUNGSZULAGE_STUFE_v1.sql`; Chat-Claude-Abnahme). — **v786** Konflikt-Warnung Abwesenheit↔Projektzeit
  (Client-Guard, warnen nicht blockieren, isStaff-Lösen). — **v787** AS-Eskalation prüft Termin + Schwelle
  vereinheitlicht auf 14 Tage (live-Bug S075377). — **v788** Chef-Portal-Zähler-Kacheln auf `Kpi` (Admin-Optik).
  — **v789** Kontrast AbsView-Buttons Krankmeldung(#dc2626)/Zeitausgleich(#7c3aed). — **v790** Dispo-Kapazität
  Belegungs-Doppelabzug behoben (abwAbzug, `_dispoNormFrei`; `_dispoPlan`-Kern byte-identisch).
- **v791 Navigation-Neubau ETAPPE 1** — verhaltensneutrales Fundament (hash-erhaltender History-Core
  `_navMerge`/`_navPush`/`_navReplace`, Schema `{kat,sub,projId,projView,detailId?}`). **OK, keine Verhaltensänderung.**

## 🔎 DB-Diagnosen (read-only, geliefert)
- **Riedmann 01.07.** Projektzeit am Krank-Tag: kein Datums-Shift, Schreibpfad user-gewähltes Datum; Büro-Bereinigung.
- **AS-Zeit → time_entries** (v3.9.549): `arbeitsscheine.stunden/fahrzeit` = Minuten, App-only, NICHT in time_entries;
  Abschluss (Doppel-Sig) schreibt keine time_entry; 0/85 time_entries mit arbeitsschein_id. Auto-Übernahme-Punkt =
  `saveAs` `_shouldAutoClose`. **BAU wartet auf Sebastian-Entscheid** (Quell-Tag termin vs. abschluss, Fahrzeit,
  Idempotenz, monteur_text-only).

## ⛔ Navigation ETAPPE 2 (v792) — LIVE, aber FUNKTIONIERT NICHT (NICHT „erledigt")
**Sebastian Live-Test: Sub-Tab-Zurück greift bei AS, Chef, Büro-Portal UND Admin NICHT.** Nur Fahrzeug/Werkzeug
(useBackLayer, Bestand vor Etappe 2) funktionieren. Der Etappe-2-Ansatz (`_navPush({sub})` + `_regSubView`/`_unregSubView`
+ popstate-Restore) **zieht flächendeckend nicht.** v792 ist deployed, aber der Sub-Tab-Restore ist tot.

**HAUPTVERDACHT (nicht bewiesen, Root-Cause steht aus):** ZWEI konkurrierende History-Systeme —
(a) ALT `useBackLayer`/`window.__epkPushLayer`/`__epkPopLayer`/`_backLayers` (Fahrzeug/Werkzeug, **funktioniert**;
popstate-Handler `index.html` ~8362, Layer-Check `_backLayers.current.length>_targetLd` zuerst) vs.
(b) NEU `_navPush`/`_regSubView`/`history.state.sub` (Etappe 2, **funktioniert nirgends**).
Statische Analyse sagt: Cross-Tab-Restore sollte über Re-Mount (`_navSubResolve(history.state.sub,…)`) bzw. den
registrierten Setter greifen — tut es empirisch aber nicht. Der Widerspruch (Code „sollte", Live „tut nicht") ist
selbst das Signal: **entweder ein Zwei-System-Konflikt in der popstate-Kette, oder ein Runtime-Detail (Komponente
re-mountet nicht / history.state-Timing), das nur ein LIVE-Console-Trace pinnt.** Statisch nicht abschließend geklärt.

**NÄCHSTER SCHRITT (Sebastian-Entscheid offen):**
1. **Rollback v792 → v791** (verhaltensneutrales Fundament) und Sub-Tab-Support NEU auf `useBackLayer` aufsetzen
   (die bewiesen funktionierende Mechanik — EIN System statt zwei). Sauberer Weg: `git revert cd56244` (kein
   History-Rewrite/force-push, Tabu-konform). **NICHT ausgeführt — wartet auf „roll zurück".** Vorher die uncommittete
   AS-Zwischenarbeit in `index.html` verwerfen.
2. ODER erst Root-Cause per Live-Console-Trace (feuert popstate? kommt der Setter an? Layer-Check schluckt Back?).

**Kachel-Deep-Links (Chef, `_drill`/`onNav`/`__asFilter`/`__asOpenId`):** waren NIE im Etappe-2-Scope — **auch offen.**

## 📋 OFFENE PUNKTE (nichts verlieren)
- **Navigation Root-Cause + Etappe 2 Fix** (rollback vs. weiterdiagnostizieren) — Sebastian-Entscheid.
- **Navigation Etappe 3 (Detail-Layer/AS-form) + Etappe 4 (Browser-Zurück)** — nicht begonnen, hängen an Etappe-2-Fix.
- **Chef-Kacheln-Deep-Links** — offen, nie im Scope.
- **AUFRÄUM Phase A** — Löschliste NICHT als Datei erstellt (nur Entwurf im Chatverlauf: Kat 1 = 6 alte handoffs außer
  letzte 3; Kat 3 = viele Status-/Audit-Docs Root+docs+sql; Kat 2 = kaum saubere Kandidaten, index.html-referenzierte
  sql bleiben; Kat 4 Backups bleiben solange Tabelle lebt). Phase B (git rm) erst nach Sebastian-Freigabe pro Kategorie.
- **Zulagen-Speicher-Feedback (grüner Haken)** — Sebastian-Entscheid raus/bauen.
- **Dead-Code-Nachtsession**: OFFA_SB_MAP raus, `test_pze_v3692` TZ-Pin (host-abhängig), conftest timeout=10,
  Klon-Extraktoren (feiertag/hunt) — offen.
- **`drop column aktiv`** auf `entfernungszulage_tage` — erst wenn v785 stabil (App liest migration-tolerant).
- **Heute-Ring-Farbe** EZ-Kalender (EP-Grün vs. Blau) — Sebastian-Sicht.
- **Datenbereinigung 01.07. Riedmann** (Krank + Projektzeit) — Büro.

## Gates/Regeln (unverändert)
node_check 0 · bracket `() -1` (diesem Skript trauen) · `node sql/_check_version.js` · voller pytest NACH Bump ·
Kiosk-Tabu v784 (`_kioskScreenPick` md5-Pin, hash-erhaltend) · Kerne EZ/`_asEskalierbar`/`_dispoPlan` byte-identisch ·
Push nur via `git -c http.version=HTTP/1.1`.
