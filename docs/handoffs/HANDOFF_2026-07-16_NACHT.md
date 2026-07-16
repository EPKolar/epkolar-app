# Handoff 16.07.2026 (Nacht) — Dispo-Umbau Register 0–20, Stand v3.9.727

**Arbeitsklon:** `C:\repos\epkolar-app`. Push `git push origin main`, Remote-Verify per curl raw/github.io.
**Stand HEAD:** **v3.9.727** (`bcb403a`). **pytest 1659 grün.** Working tree clean, alles gepusht.
**Resume-Wahrheit:** dieser Handoff + `git log` + das MASTER-REGISTER (Sebastian, im Chat) = voller Kontext.

> **Pflicht-Gates je Push (unverkürzt):** `python scripts/node_check.py index.html` (0) ·
> `python scripts/_bracket_check.py index.html` (**`() -1`**, {} 0, [] 0) · `node sql/_check_version.js` ·
> voller `python -m pytest tests/ -q` lokal · Browser-Smoke (Boot, APP_VERSION, `#root`, 0 Script-Errors).
> **Kein optional chaining** (`?.`). Kommentar-Behauptung → Test. Version 4 Stellen (SW_VER Z.15 · APP_VERSION
> ~Z.2854 · sw.js L1 · sw.js L2). **Build-Agenten NEIN, DDL nur stagen, TABU** (_juprowaPush, Auth/RLS-Writes,
> guard_urlaub_edit, OFFA-Direkt, .github/workflows, Kiosk byte-identisch).
> **Gate-Lektion v727:** node_check fing einen echten Syntaxfehler (gerades `"` in `„aufgeschoben"` schloss
> den JS-String). Deutsche Anführungszeichen in JS-Strings: `'...'` innen oder `\"` — nie ein rohes `"`.

## MATRIX (0–20, R1/R2 — bei jedem Push führen)
`0✔724 1– 2✔723 3✔723 4✔723 5– 6– 7– 8– 9– 10– 11– 12– 13– 14✔725 15✔726 16– 17✔727 18– 19– 20–`

## ✅ Diese Session gebaut & gepusht (alle TDD + live im Browser verifiziert)
| Reg | Ver | SHA | Inhalt |
|---|---|---|---|
| P1-a | 717 | 4f19aff | Monteur kommt AUS dem AS, Dispo wählt nie (fieldMA-Zeilen, ohne Monteur→Warteliste, kein Spillover) |
| P1-b | 718 | 9169f18 | Chip + Wartelisten-Eintrag öffnen den AS (`onOpenSchein`, stopPropagation, Schein-Nr) |
| P1-c | 719 | ff61800 | AS-Anlage nur OFFA (ASVorlagenPanel + `_vorlagenBus` + Sub-Tab + Boot-Selbsttest raus, 0 Refs) |
| P1-d | 720 | d2626f3 | Dispo-Tab am Handy auffindbar (Label unter Icon) |
| — | — | cda2867 | E4b-Diff==manuell belegt (test-only) |
| P2 | 721 | aecb451 | Theme-Hotfix Mobil (350ms `_themeTapAllowed` live-verifiziert + Segmented Control + Toast) |
| — | 722 | ce1bc9a | 3-Wochen-Horizont + `DISPO_WOCHEN_MALUS` + km ab Firma (feste Endpunkte) |
| #2/3/4 | 723 | 7176bc3 | Lesbarkeit: Nr+Kunde+Arbeit+Ort, Blockade-Grund statt „—", Kopf „später" |
| **#0** | 724 | 04f088d | Kapazitätsmodell: Störungsdienst-Tage (⚡, voll+`DISPO_STOERTAG_BONUS`) · Baustellen-Tag = Vorab-Fenster `DISPO_VORAB_MIN=120` statt Vollblock · `_dispoIstSat`/`_dispoBvhNorm`/`tagArt` |
| **#14** | 725 | 0cea9f8 | KW-Navigation (KW-Tabs `_kwIdx`, Desktop=Mobile, ◀/▶, Klapp-Sektionen raus) |
| **#15** | 726 | 4b6df96 | Vorab-Optik beruhigt (leere Baustellen-Zelle kein Kasten, dezent + Tooltip; Legende) |
| **#17** | 727 | bcb403a | Scope: überfällig (termin<heute) rein (⚠ war…+Alters-Bonus), Zukunft = fix (`fixMap`, 📌, Kap-Abzug, kein Umplanen), aufgeschoben = Parkplatz raus; Kopf +überfällig |

## Dispo-Architektur (für Wiederaufnahme)
- **Rechenkern `//@DISPO`** (pure, node-eval-getestet) ~Z.4586–4830: Konstanten (`DISPO_HORIZONT_WOCHEN=3`,
  `DISPO_WOCHEN_MALUS=10000`, `DISPO_VORAB_MIN=120`, `DISPO_STOERTAG_BONUS=3000`, `DISPO_SAT_CROSS_MALUS=1000`,
  `DISPO_VORAB_MALUS=50000`, `DISPO_RESERVE_MIN=60`, `PUFFER_JE_STOPP=10`, `DISPO_INNERORTS_KM/MIN=2/5`).
  Funktionen: `_dispoAdrKey`, `_dispoDauer`, `_dispoHaversine`, `_dispo2opt`, `_dispoKapazitaet`, `_dispoTopf`,
  `_dispoIstSat`, `_dispoBvhNorm`, `_dispoAbwAbzug`, `_dispoAbwLabel`, **`_dispoPlan`**, **`_dispoBuildInput`**.
  Alle als `window._dispo*` exportiert (node-eval).
- **`_dispoBuildInput(scheine,monteure,wpHistory,absMap,now,horizontWochen)`** → liefert
  `{cfg:{monteure,tage,firma,dist,kapAbzug,hatFz,scheine(planScheine),horizont,tagArt}, tage, wochen,
  kwLabel, offenCount, monteure, horizont, blockGrund, tagArt, fixMap, ueberfaelligCount, heute}`.
  tag: `{key(=ISO-Datum, eindeutig), wtag(Mo..Fr), iso, normMin, woche(0..HOR-1)}`.
  `tagArt[mid][isoKey]` = `{art:'frei'|'stoerung'|'sat'|'vorab', bvh?}`. `blockGrund[mid][isoKey]` = `[{icon,label}]|null`.
  `fixMap[mid][isoKey]` = `[{scheinId,bvh,dauerMin,terminZeit}]` (fixe Zukunfts-Termine, 17d).
- **`DispoPanel`** ~Z.8929: `_kwIdx`-State (KW-Nav), `_zelle(m,t)` rendert fixe 📌-Chips → dann Vorschlags-Chips
  (dashed, ⚠-Badge bei ueberfaelligVon, ✓ Übernehmen via `onUebernehmen` prop) → leere Zelle: Vorab dezent /
  Blocker kompakt / „—". Callsite in ArbeitsscheinView ~Z.9756 (`onUebernehmen`/`onOpenSchein`).
- **Übernahme (E4b)** byte-gleich zu manuell: `onUebernehmen` → `updAs(scheinId,{terminBestaetigt:iso,
  monteur,dauer:_dispoMinToHHMM(dauerMin)})`. terminBestaetigt/monteur/dauer ∈ JUPROWA_PUSH_FIELDS → push_pending.

## ⏳ OFFEN — Reihung FIX: 18 → 19 → 1 → 16 → 20 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13
- **#18 OFFA-verwaiste Scheine** (kein DDL): Erkennung `juprowa_id` gesetzt + scheinstatus ∈ AS_GRP_OFFEN +
  `juprowa_sync_at` älter als `OFFA_VERWAIST_TAGE=7` obwohl Pull-Läufe stattfanden (letzten erfolgreichen Pull-
  Zeitstempel global merken, localStorage/State). Badge „⚠ in OFFA prüfen" (Liste+Form) + Sammel-Hinweis Büro-
  Portal. KEINE Auto-Statusänderung. **Schritt 0:** Bestandscode/Cloud-API prüfen ob Worksheet-Einzel-GET je
  juprowa_id existiert (API kennt `ResponseType_WorksheetPOST` — GET-Pendant?). Wenn ja: verwaiste sanft per
  Einzel-GET nachschlagen, Status über BESTEHENDEN Pull-Mapper (JUPROWA_STATUS_MAP), kein Push. Wenn nein: nur
  Badge + Befund in Report. Tests: sync_at 10 Tage + Pull lief→Badge; frisch→kein Badge; ohne juprowa_id nie verwaist.
- **#19** — **WORTLAUT FEHLT** (im Feed referenziert als „Fahrzeit-Kaskade" für #20a, aber der #19-Befehl kam nie
  bei CC an). **Fresh-Session muss den #19-Befehl von Sebastian/Chat-Claude anfordern**, bevor #19 gebaut wird.
- **#1 P1-e Teil 2 blockierbare Tage:** `sql/DISPO_BLOCKS_v1.sql` **stagen** (worker_id+datum PK, grund,
  created_by; is_staff-RLS + Kiosk-RESTRICTIVE, idempotent — Muster `sql/MONTAGEZULAGE_v1.sql`). Client 42P01-
  tolerant. 🚫-Toggle je Monteur×Tag (Gate Büro/PL/Admin, als `onToggleBlock`-prop — DispoPanel bleibt read-only),
  geblockt = Kap 0 über alle 3 KWs (in `_dispoBuildInput` integrieren: blockierter Tag → abz=normMin +
  blockGrund `{🚫, grund||"gesperrt"}` + tagArt dominiert). Prio-1/fixer Termin auf geblocktem Tag → Konflikt-Badge.
  SQL an Sebastian melden (nicht warten).
- **#16 Drag&Drop** (2 Pushes 16a/16b): Pointer Events (kein HTML5-DnD), 8px-Schwelle trennt Klick(öffnet AS)
  von Drag. 16a Chip ziehen → nur Zellen DERSELBEN Monteur-Zeile, grün/orange/rot-Feedback, Drop = Pin (📌,
  localStorage pro Woche, „Neu berechnen" respektiert Pins), fremde Zeile = rot+Toast, Warteliste ziehbar,
  KW-Tab-Hover 600ms wechselt Woche. 16b Dauer-Griff (≡, ≥20px) horizontal = Dauer 15-min-Schritte (min30/maxNorm),
  Live-Label, Balken zieht mit; Plan-Dauer erst bei ✓ Übernehmen als dauer (HH:MM:SS, updAs/E4b, kein neuer Push).
- **#20 Zeitachse 15-min-Takt:** Ablaufzeiten je Chip (`DISPO_TAG_START=07:00` ab Firma, kumulativ Fahrzeit
  (#19-Kaskade / solange unbekannt DISPO_INNERORTS_MIN|Haversine-min) + Dauer + PUFFER, Start auf `DISPO_ZEITRASTER_MIN=15`
  gerundet, Chip-Label „07:00–08:30"). Tageszelle als Mini-Timeline (Stunden-Skala 07–17, 15-min-Snap-Ticks leise).
  Fixe 📌 an echter termin_zeit; ohne Zeit → „ohne Zeit"-Band oben (Muster MonteurTafel v536). D&D-Kopplung (#16):
  vertikal=Startzeit-Snap, Überlapp schiebt Folge-Chips. **Übernahme schreibt zusätzlich Startzeit — Schritt 0:
  Zielfeld wörtlich verifizieren (`termin_zeit`, wie MonteurTafel v536 liest; Push-Feld-Status), via updAs.**
- **#5 Phantom-Krankmeldung** (P1, DB-bewiesen, client-only): Poll-Diff ~Z.7819-7835 `lastSnapshot.absenceKeys`
  NUR additiv mergen (Union, nie ersetzen); Plausi-Guard freshAbs<50% letzter Länge → keine Diff-Notif + warn-Log;
  `absence_sick` nur wenn from_date≥heute-3 (Wiener Datum). **absences hat from_date/to_date, KEINE date-Spalte
  (42703).** Gleiche Musterklasse an ALLEN Poll-Snapshot-Diffs prüfen. Tests: partiell→0+Snapshot groß; voller
  nach Teilmenge→0 Alt-Notif; echt neu from_date=heute→1; Alt<heute-3 nie; 42703 from_date nie date.
- **#6 E2-🚛-UI** fz_bedarf-Block AS-Form (~8890/9588, save~8929, außerhalb `_asMtLocked`) + Feature-Detect-
  Schreibpfad + Listen-Badge. SQL `AS_FZ_BEDARF_v1.sql` gestaged.
- **#7 Büro-Extras A5** (intern fix): Chip-tel: (kund_tel+AK_KONTAKT_TELEFON1-3, v548) → „📞 vereinbart"(→Prio1)
  → Morgen-Check-Kopf → Tagesplan-PDF/Monteur-Tag + Wochen-Excel.
- **#8** Team-Kachel→MA-Wochen-Popup (ma-Key wörtlich). **#9** Material Symbole+25k-Messlauf. **#10** Perf 2+3.
- **#11 Bug-Hunt** v713–727, Klassen (a)Freiheitsgrad-Betrieb-nicht-hat (b)Snapshot-vs-partiell (c)Touch-Doppelfeuer.
- **#12 Cleaning** Batch 2 (v698-Muster, max 8, Beweis je Symbol).
- **#13 HANDOFF+ENDREPORT** (letzter Push, Pflicht): Matrix 0–20 mit Version/SHA + alle Sebastian-Gates.

## Offene Sebastian-Gates (sammeln für #13)
`geo` (PLZ_GEO/DISTANZ+OSRM) · `AS_FZ_BEDARF`-SQL · `DISPO_BLOCKS`-SQL (mit #1) · S4×4 **+ as_vorlagen (S4-5 neu
in `sql/CLEANUP_2026-07.sql`)** · Tankfoto-Migration go · **E4b-Live-Abnahme** (Diff belegt, Test grün) · PAT workflow-scope.

## Live-Abnahmen offen (Chat-Claude)
- v727: ~28 planbar (10 ohne Termin + 18 überfällig), Kopf „Y überfällig", Zukunfts-Termine als 📌 (Kap abgezogen).
- Auf Sebastian-Zuruf: EINE kontrollierte E4b-Übernahme am echten Schein.

## Empfehlung
Kontext dieser Session ist voll. **Frische Session:** Einlese-Befehl + dieser Handoff + `git log -14` + Register
= Wahrheit. An der ersten offenen Nummer (#18) weitermachen; **#19-Wortlaut zuerst anfordern** (fehlt).
