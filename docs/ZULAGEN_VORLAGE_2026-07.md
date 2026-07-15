# KV-/Zulagen-Entscheidungsvorlage — Stand 15.07.2026

**Zweck:** Ist-Verhalten der App gegen die vertraglichen Fakten (Arbeitsvertrag +
Gleitzeit-Einzelvereinbarung + Zusatzvereinbarung, Muster Stand 06/2026) stellen. **Reine Analyse-
und Entscheidungsvorlage — kein Code-Umbau vor Sebastians Einzel-Freigaben.**

> **Beispiel-Stundensatz** für alle €-Deltas: **20 €/h brutto** — reine Rechenannahme, nicht der echte
> Satz. Der Lohnverrechner bleibt in allen Punkten maßgeblich.

> **Domänen-Grundlage** (Entscheid 14.07.): `time_entries` = Projektzeit, `stempel_log` = Anwesenheit.
> Die lohnrelevante Basis ist `stempel_log`, sobald Chips laufen; bis dahin `time_entries` als
> **gelabelte Näherung** (Punkt 2 des Rollout-Plans).

---

## Z1 — Zuschlagslogik → Gleitkonto-Report · **ENTSCHIEDEN (Sebastian 15.07.)**

**Entscheid:** Überstunden werden **mit Zeitausgleich 1:1 abgebaut**; die 50%/100%-Sätze kommen wegen
Gleitzeitregelung + Überstundenpool **nie zur Anwendung**. Der `KVZuschlagReport` (€-Zuschläge) wird
**ersetzt durch einen Gleitkonto-Report** (Stunden, kein €).

### Ist-Verhalten (Code-Fundstellen)

- `KVZuschlagReport` (Komponente ~Z. 21549, Berechnung ~Z. 21557–21596) rechnet **heute** je Monteur/Tag:
  `norm = _kvTagesnorm(dow,fei)` → `ueber = max(0, tagesstunden − norm)` → `_kvTagZuschlag(...)` mit
  Mehrarbeit/Ü50/Ü100.
- `_kvTagZuschlag` (`//@KV-ZUSCHLAG`, ~Z. 2182): **jede Stunde über der Tagesnorm** (Mo–Do 8,5 / Fr 4,5;
  Sa/So/Feiertag ab der 1. Std) zählt als Mehr-/Überstunde. **Keine 10-h-Tagesgrenze, kein Rahmen
  05:00–19:00, keine Wochenbetrachtung, keine „Anordnung"-Bedingung.**
- `_kvHundert100` (~Z. 2199): 100 %-Trigger bei So/Feiertag/Nacht (20–6) / ab 3. Ü-Std nach 19 h.
- UI-Warnhinweis (Z. 21604): *„Näherung zur Anspruchsführung … Lohnverrechner maßgeblich."*

### Vertrags-Soll (Gleitzeit)

- Rahmen 05:00–19:00, Kernzeit 07:00–15:00, tägl. Normalarbeitszeit **bis 10 h**.
- Mehrstunden **im Rahmen** = Normalarbeitszeit → **Gleitkonto**, **keine** Überstunde.
- Gleitzeitperiode 12 Monate ab **01.07.2026**, Übertrag Guthaben **und** Schuld je **max ±300 h**.
- Abwesenheit (Urlaub/Feiertag/Dienstverhinderung) zählt mit **fiktiver Normalarbeitszeit** ins Konto.
- Überstunde nur: außerhalb Rahmen **nach Anordnung** ODER So/Feiertag → 1:1 ZA-Abbau.

### Umsetzung (der Baustein — Konzept, NICHT jetzt gebaut)

**Ein neuer Gleitkonto-Report** (ersetzt `KVZuschlagReport`), je MA:
- **Ist-Stunden vs. Soll** je Tag, **Saldo kumulativ** über die Gleitzeitperiode 01.07.–30.06.
- **Übertrag ±300 h** (Kappung sichtbar machen).
- **ZA-Abbau 1:1** ausgewiesen (Zeitausgleich reduziert das Guthaben).
- **Ausweis in STUNDEN, keine €-Bewertung** von Mehr-/Überstunden.
- Abwesenheit = **Soll-Neutralisierung** (fiktive Normalarbeitszeit — die PZE-Gutschrift-Logik
  `absGutschrift` macht das bereits pro Tag, ~Z. 4389).
- **Datenbasis:** `stempel_log`, sobald Daten laufen (= Punkt-2-Fundament); bis dahin `time_entries`
  als gelabelte Näherung.
- **Z5 geht hierin auf** — ein Baustein statt zwei (siehe Z5 unten).

**Bleibt erhalten:** Die `KV_RULES`-Zuschlagsfaktoren (`zuschlagMehrarbeit`, `zuschlagUeStd`,
`zuschlagUeStd100`, `zaFaktor50/100`) werden **NICHT gelöscht** — sie bleiben als Konfiguration, nur
ihre **Anwendung im Report entfällt**. (`zaFaktor50/100` sind ohnehin schon definiert, aber nirgends
verrechnet — Agent-Befund.)

**CSV für den Lohnverrechner:** Stunden-Salden statt Zuschlagsbeträge; Lohnverrechner bleibt maßgeblich.

**Zahlenbeispiel (Stunden, keine €):** Di mit 9 h / 10 h / 11 h Anwesenheit, Sa 8 h angeordnet.
| Tag | Ist | Soll | heute (App) | Gleitzeit-Soll |
|---|---|---|---|---|
| Di 9 h | 9 | 8,5 | +0,5 h Mehrarbeit → Zuschlag | +0,5 h aufs Gleitkonto, kein Zuschlag |
| Di 10 h | 10 | 8,5 | +1,5 h (davon Ü50) | +1,5 h aufs Gleitkonto |
| Di 11 h | 11 | 8,5 | +2,5 h (Mehrarbeit+Ü50) | +1,5 h Gleitkonto **+ 1 h echte Überstunde** (>10 h) → ZA 1:1 |
| Sa 8 h angeordnet | 8 | 0 | 8 h × 100 %/50 % Zuschlag | 8 h Überstunde (angeordnet, außer Rahmen) → ZA 1:1 |

**Aufwand:** mittel (neuer Report + kumulative Periodenlogik). **Risiko:** lohnrelevant → nur mit
`stempel_log`-Daten und €-freiem Ausweis; die Periodenlogik (±300 h, 01.07.–30.06.) muss exakt sein.

> **⚠ EINE RÜCKBESTÄTIGUNG offen (statt zu raten):** Gilt „Überstunden 1:1 mit ZA, keine 50/100 %-Sätze"
> **ausnahmslos**, auch für **angeordnete Sonntags-/Feiertagsarbeit**? (Kommt betrieblich laut Sebastian
> praktisch nicht vor — hier nur sauber festhalten.)

---

## Z2 — Freitags-Tagesnorm 4,5 h vs. Vertrag „max 5 h" · **OFFEN**

**Ist:** Fr = **4,5 h** in drei Funktionen:
- `_kvTagesnorm` (~Z. 2177) — reine Live-Rechnung.
- `_stdVonTagK(d,woche)` (~Z. 19001) — skaliert auf Teilzeit, **schreibt `hours` in `absences`**.
- `_stdVonTagBrk` (~Z. 20929) — dritte, bewusst inline duplizierte Kopie (Urlaubs-Materialisierung).

**Alle Konsumenten** (Delta-relevant):

| Fundstelle | Zweck | schreibt DB? |
|---|---|---|
| `_kvTagesnorm` @ PZEView ~Z. 9748 | PZE-Soll (Monatsabrechnung) | nein — **live, rückwirkend** |
| `_kvTagesnorm` @ KVZuschlagReport ~Z. 21585 | Zuschlagsschwelle | nein — live (entfällt mit Z1) |
| `_stdVonTagK` @ Kiosk `_submitAntrag` ~Z. 6084 | `absences.hours` beim Terminal-Antrag | **ja** |
| `_stdVonTagK` @ AbsView `tog`/`submitRequest` ~Z. 19071/19104 | `absences.hours` bei App-Antrag | **ja** |
| `_stdVonTagBrk` @ `_materialisiereAbsence` ~Z. 20941 | `absences.hours` bei Auto-Materialisierung | **ja** |
| `_stdVonTagK` @ `_yearStK` ~Z. 19004 · `_absStats` ~Z. 8302 · `_krankRows` ~Z. 10548 | Fallback-Std, **wenn `v.hours` fehlt** | nein |
| `_stdVonTagK` @ ChefDashboard `_sollRange` ~Z. 21184 | Kapazitäts-Soll | nein — live |

**Wichtig:** Der Wert wird **persistiert** (4 Schreibpfade). Eine Änderung Fr → 5,0 wirkt **nur auf
künftige** `absences`-Zeilen; historische bleiben bei 4,5 (Leser nehmen `parseFloat(v.hours)||…`
vorrangig). Nur die **Live-Rechner** (PZE-Soll, Zuschlag, Kapazität) ändern sich auch rückwirkend.

**Delta je Fr:** Fr-**Feiertag** ist NICHT betroffen (immer 0). Fr-**Urlaubstag**: +0,5 h/Tag im
gespeicherten `hours` → bei 20 €/h ≈ **+10 €** pro Fr-Urlaubstag (falls lohnwirksam bewertet — das ist
Lohnverrechner-Sache). Fr-**Anwesenheit**: verschiebt PZE-Soll um +0,5 h/Fr.

**Offene Entscheidung:** Bleibt Fr bei 4,5 h, oder auf den genauen Vertrags-Sollwert (Vertrag sagt „max
5 h" — das ist eine Obergrenze, nicht zwingend der Soll)? **Der exakte Fr-Soll ist Lohnverrechner-/
Vertragsfrage** — die App bildet ab, was entschieden wird. Falls geändert: die 4 Schreibpfade + 3
Funktionen konsistent, plus Entscheid, ob Alt-`absences` migriert werden.

---

## Z3 — Label „Taggeld" → vertraglich „Entfernungszulage" · **OFFEN**

**Ist:** „Taggeld" steht als Datenfeld, Admin-Label, Report-Titel, Tabellenspalte **und CSV-Header** —
**„Entfernungszulage" kommt im Repo nirgends vor.** Fundstellen:
- Datenfelder `taggeldAb6h:11.94, taggeldAb11h:30.00, taggeldNacht:62.04` (`KV_RULES_FALLBACK` ~Z. 2151).
- Admin-UI-Labels „Taggeld ab 6h/ab 11h/Nacht" (~Z. 8140).
- Report-Titel „💶 KV-Zulagen — Taggeld & Montagezulage" (~Z. 9613), Spaltenkopf „Taggeld" (~Z. 9629).
- **CSV-Header** „Taggeld EUR" (~Z. 9557) — geht an den Lohnverrechner.

**Sätze** exakt hinterlegt (11,94 / 30,00 / 62,04), Stufen `_kvTaggeldTag` (~Z. 2215): `>11h → ab11h;
>6h → ab6h; sonst 0` (**nur zwei Stufen ausgewertet**). Bemessung = Tages-Summe `time_entries`
(gelabelte Näherung).

**Umsetzung:** reine Umbenennung „Taggeld" → „Entfernungszulage" in UI/Report/CSV (kein Rechenpfad).
**Risiko:** niedrig (Label). **Aber:** die Stufensätze/Stufengrenzen gegen den echten KV-Stand prüfen
ist **Lohnverrechner-Prüfpunkt** — die 11,94/30/62,04 sind nur als Fallback belegt, kein KV-Paragraphentext
im Repo (`KV_ENTSCHEIDUNG_v668.md`: „Quelle fehlt").

**Offene Entscheidung:** (1) Label umbenennen? (2) Sind 11,94/30,00/62,04 und die Stufen >6h/>11h der
korrekte Vertrags-/KV-Stand? (Lohnverrechner)

---

## Z4 — Pausenabzug 60 min vs. vertragliche 30 min ab >6 h · **OFFEN**

**Ist:** Monteur-Default = **60 min** (`STEMPEL_PAUSE_FALLBACK={Backoffice:0,default:60}`, ~Z. 2045).
Der Abzug ist **rollenabhängig, nicht arbeitszeitabhängig** — `_stPauseAbzug(role,rules)` kennt keine
Abhängigkeit von den Tagesstunden. Pro Rolle einstellbar (0–120) via `StempelPauseConfig` +
`system_config.stempel_pause_rules`. Abzug **einmal/Tag**, nie negativ (`_stTagNetto` ~Z. 2057).

**Wirkkette:** PZE-Netto (`_pzeTagRow` ~Z. 4377) und Kiosk-Feedback beim Gehen (~Z. 6032).

**Kein Pausen-Stempel im System** — es gibt nur Kommen/Gehen. Die Pause wird **nie gemessen**, immer
als fixer Rollenwert abgezogen:

| Szenario | echte Pause | App-Abzug (Monteur) | Netto-Effekt (20 €/h) |
|---|---|---|---|
| real 30 min | 30 | **60** | 30 min zu wenig → ≈ **−10 €** Anwesenheit |
| real 60 min | 60 | 60 | stimmt |
| gar nicht gestempelt (durchgearbeitet) | 0 | **60** | 60 min zu wenig → ≈ **−20 €** |

**Vertrag:** mind. 30 min ab >6 h. Die App-Regel (60 fix für Monteure) ist **eine Betriebsvorgabe**,
kein KV-Zwang — 30 min wäre das gesetzliche Minimum. Eine **arbeitszeitabhängige** Regel („30 ab >6 h,
mehr ab >9 h") ist im Code **nicht abgebildet**.

**Umsetzung (zwei Stufen):** (a) sofort ohne Code: den Monteur-Wert per `StempelPauseConfig` von 60 auf
30 setzen (Admin-UI, kein Deploy). (b) mit Code: arbeitszeitabhängige Pausenstaffel in `_stPauseAbzug`
(Aufwand mittel, ändert die lohnrelevante Netto-Rechnung → €-Beispiel-Abnahme wie Punkt 2).

**Offene Entscheidung:** Monteur-Pause auf 30 min? Und: fixer Rollenwert (einfach) oder
arbeitszeitabhängige Staffel (vertragsnah)?

---

## Z5 — Kumulatives Gleitkonto ±300 h · **geht in Z1 auf**

**Ist:** Es gibt **KEIN** kumulatives Gleitzeit-/Stundenkonto (Agent-Befund, Volltextsuche negativ).
Einziges kumulatives Feld: `_resturlaubK` (Urlaub, via `kontingent.vorjahr`). Die PZE zeigt den
Tages-Saldo (`_pzeTagRow.saldoMin = netto − soll`) und Wochen-/Monatssummen (`_pzeSummen`), aber
**ohne Fortschreibung über die Monatsgrenze** — jeder Zeitraum startet bei 0. `zaFaktor50/100` in
`KV_RULES` sind definiert, aber **nirgends verrechnet**.

**Soll = der Gleitkonto-Report aus Z1.** Skizze, wie er auf `stempel_log` aufsetzt (nur Konzept):
- Periodenanker **01.07.–30.06.**, Saldo = Σ (Tages-Netto − Tages-Soll) über die Periode.
- Tages-Netto aus `_stTagNetto` (Stempel, gerundet, Pausenregel), Tages-Soll aus `_kvTagesnorm`/
  `_stdVonTagK` (Teilzeit), Abwesenheit neutralisiert das Soll (PZE-`absGutschrift` liefert das schon).
- **Übertrag ±300 h** kappen und die Kappung sichtbar machen; ZA-Anträge reduzieren das Guthaben 1:1.
- Ist das **Fundament für Punkt 2** — dieselbe `stempel_log`-Basis. Bau erst nach Punkt-2-Freigabe +
  Z1-Rückbestätigung.

---

## Z6 — KV-Bezeichnung „Metallgewerbe" vs. Vertrag „Metallnebengewerbe" · **OFFEN (Lohnverrechner-Frage)**

**Ist:** Die App führt durchgehend **„Metallgewerbe"** — **„Metallnebengewerbe" kommt im Repo nirgends
vor.** Laufzeitrelevant nur an einer Stelle: `KV_RULES_FALLBACK.stand = 'KV Metallgewerbe 1.1.2026'`
(~Z. 2154, via `_kvLoadRules` an `window.KV_RULES`). Sonst nur Kommentare/UI-Titel (Admin „⚙ KV-Konstanten
(Metallgewerbe)" ~Z. 8173, Report „💶 KV-Zuschläge (Metallgewerbe)" ~Z. 21601) und Tests.

**Frage an den Lohnverrechner (nichts unterstellt):** Ist der maßgebliche KV **Metallnebengewerbe** (lt.
Vertrag) statt Metallgewerbe? Falls ja: **könnten** die hinterlegten `KV_RULES`-Werte (Sätze, Grenzen)
davon betroffen sein? Die App bildet nur ab, was der Lohnverrechner bestätigt — bei bestätigter
Abweichung: `stand`-String + UI-Titel korrigieren und Werte gegenprüfen.

---

## Bestehende offene KV-Punkte (aus v3.9.664, hier integriert)

| Punkt | Ist | Status |
|---|---|---|
| **Montagezulage auf ALLE Stunden** (inkl. Werkstatt/Fahrt) | war Näherung; seit v3.9.685 nur noch **manuell geflaggte Tage** (`montagezulage_tage`, `baustellenStd=0`) | **erledigt** |
| **100%-Zuschlag als Tages-Flag** statt Fenster-Overlap | `_kvHundert100` ~Z. 2199, „früheste von / späteste bis"-Näherung | **entfällt mit Z1** (keine %-Sätze mehr) |
| **„ab 3. Ü-Std nach 19 h"** greift übers Mehrarbeit-Band | `if(bm>19*60 && ueberStd>=3)` ~Z. 2206 | **entfällt mit Z1** |
| **`taggeldNacht` toter Konfig-Knopf** (62,04) | definiert (~Z. 2151) + Admin-Label (~Z. 8140), aber `_kvTaggeldTag` liest ihn **nie** | **offen** — bei Z3 mitentscheiden: aktivieren (Nacht-Stufe) oder entfernen |

---

## Entscheidungsübersicht

| # | Thema | Status | Nächster Schritt |
|---|---|---|---|
| Z1 | Zuschlag → Gleitkonto-Report (Stunden, ZA 1:1) | ✅ **entschieden** | 1 Rückbestätigung (So/Feiertag ausnahmslos?), dann Bau nach Punkt 2 |
| Z2 | Freitag 4,5 h vs. „max 5 h" | ⏳ offen | Fr-Soll bestätigen (Lohnverrechner); Migration Alt-`absences`? |
| Z3 | Label „Taggeld" → „Entfernungszulage" + Stufensätze | ⏳ offen | Umbenennen? Sätze 11,94/30/62,04 & Stufen KV-korrekt? |
| Z4 | Pause 60 vs. 30 min | ⏳ offen | 30 min? fix (Admin-UI sofort) oder arbeitszeit-Staffel (Code)? |
| Z5 | Gleitkonto ±300 h | → in Z1 | mit Z1 bauen (Punkt-2-Fundament) |
| Z6 | Metallgewerbe vs. Metallnebengewerbe | ⏳ offen | Lohnverrechner: welcher KV? Werte betroffen? |
| — | `taggeldNacht` | ⏳ offen | mit Z3: aktivieren oder entfernen |

**Nichts hiervon wird ohne Sebastians Einzel-Freigabe gebaut.** Lohnverrechner bleibt maßgeblich.
