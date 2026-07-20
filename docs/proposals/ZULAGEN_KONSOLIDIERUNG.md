# Zulagen-Konsolidierung — EIN Draft für BEIDE Zulagen

**Stand 20.07.2026 · SCHRITT 0 — nichts gebaut, kein Code, keine UI.** Alles unten ist Vorschlag + Befund.
Code-Anker = Zeilennummern in `index.html` bei HEAD **v3.9.767**. Lohnverrechner bleibt maßgeblich.

**Setzt auf `docs/ZULAGEN_VORLAGE_2026-07.md` auf** (Z1–Z6, Stand 15.07.) — insbesondere **Z3** behandelt
die Label-Frage bereits. Dieses Dokument dupliziert Z3 nicht, sondern führt es zu Ende und ergänzt die
Montagezulage. Die Zeilennummern in Z3 sind inzwischen verschoben; unten stehen die **aktuellen** Anker.

---

## ⚠️ Drei Prämissen des Auftrags, die der Code nicht bestätigt

Bitte zuerst lesen — sie verkleinern den Auftrag erheblich.

| Auftrags-Annahme | Realität im Code / in der DB | Konsequenz |
|---|---|---|
| „Montagezulage wird auf ALLE gebuchten Std inkl. Fahrt/Werkstatt gerechnet" | **Seit v3.9.685 nicht mehr.** Der Report übergibt `baustellenStd = 0` an `_kvZulagenMonat` (Z.10828) und holt die Zulage ausschließlich aus `_kvMontagezulageMonat(byW[wid].days, mzFlags, wid, kv)` (Z.10829) = **nur manuell geflaggte Tage** | **TEIL 2 „Report-Umstellung" ist bereits erledigt.** Es bleibt nichts umzustellen |
| „Vergabe-UI muss noch gebaut werden" | **Existiert** (v3.9.685 Phase 2): Vergabe-Panel `_mzPanel` (Z.10864), Tages-Button `_tagBtn` (Z.10866), Toggle `_mzToggle` (Z.10854), Schreibpfad `_mzSet` (Z.10775), Lesepfad `_mzFetch` (Z.10755) | **TEIL 2 „Vergabe-UI" ist bereits gebaut.** Offen sind nur Detail-Entscheide (P4–P6) |
| „DB-Fundament steht" | ✅ bestätigt: `montagezulage_tage` existiert, 4 `is_staff()`-Policies live | stimmt |

**Zusätzlicher Befund:** die Tabelle ist **leer (0 Zeilen)** — es wurde noch **kein einziger Tag vergeben**.
Der Hinweistext „⚠ Tabelle montagezulage_tage fehlt — sql/MONTAGEZULAGE_v1.sql ausführen" (Z.10906) ist
damit **veraltet** und wird nie mehr angezeigt (die Tabelle ist da). Kein Bug, nur toter Hinweis.

---

# TEIL 1 — Entfernungszulage (Label-Wahrheit)

## 1.1 Alle Fundstellen von „Taggeld"

| # | Fundstelle | Anker | Art | Sichtbar für |
|---|---|---|---|---|
| T1 | `taggeldAb6h:11.94, taggeldAb11h:30.00, taggeldNacht:62.04` in `KV_RULES_FALLBACK` | **Z.2187** | **Feldnamen (Daten)** | — (intern) |
| T2 | Kommentar 2027-Werte (`taggeldNacht 63.28`) | Z.2191 | Kommentar | — |
| T3 | NaN-Guard-Kommentar („still in Taggeld/Zuschlag/Montagezulage laufen") | Z.2198 | Kommentar | — |
| T4 | Blockkommentar KV-V4 („KV: Taggeld einschl. Wegzeit…") | Z.2249–2250 | Kommentar | — |
| T5 | **Funktion `_kvTaggeldTag(anwStd,rules)`** | **Z.2251** | **Funktionsname** | — (intern) |
| T6 | Fallback-Sätze im Rechenpfad (`t6`, `t11`) | Z.2253–2254 | Code | — |
| T7 | Akkumulator `taggeld` + Rückgabefeld **`taggeldSum`** | Z.2267–2270 | **Feldname (Rückgabe)** | — (intern) |
| T8 | `window._kvTaggeldTag=…` (Export) | Z.2316 | Export-Name | — |
| T9 | **Admin-UI-Konfig: Gruppe `'Taggeld & Zulagen'`, Labels „Taggeld ab 6h / ab 11h / Nacht"** | **Z.8996** | **Label (UI)** | Admin |
| T10 | Report-Kommentar („degradiert der Report: er zeigt Taggeld weiter") | Z.10753 | Kommentar | — |
| T11 | Report-Blockkommentar („KVZulagenReport — Monteur-Zulagen (Taggeld/Montagezulage)") | Z.10785 | Kommentar | — |
| T12 | Kommentar v3.9.685 („Taggeld weiter aus `_kvZulagenMonat`") | Z.10824 | Kommentar | — |
| T13 | `z.taggeldSum + mz.montageSum` | Z.10830 | Code | — |
| T14 | **CSV-Header `'Taggeld EUR'`** | **Z.10844** | **Export an den Lohnverrechner** | Lohnverrechner |
| T15 | CSV-Zelle `_eur(r.taggeldSum)` | Z.10846 | Export | Lohnverrechner |
| T16 | **Report-Titel `'💶 KV-Zulagen — Taggeld & Montagezulage'`** | **Z.10900** | **Label (UI)** | Büro/PL/Admin |
| T17 | **Tabellen-Spaltenkopf `'Taggeld'`** | **Z.10916** | **Label (UI)** | Büro/PL/Admin |
| T18 | Tabellen-Zelle `_c(r.taggeldSum,true)` | Z.10919 | Code | — |
| T19 | Kommentar am Report-Mount | Z.12007 | Kommentar | — |

**PDF:** **keine Fundstelle.** Es gibt keinen PDF-Export der Zulagen — der Weg zum Lohnverrechner ist
ausschließlich der **CSV-Export** (T14/T15). (Geprüft: kein `taggeld`-Treffer in einem jsPDF-Pfad.)

**„Entfernungszulage" kommt im gesamten Repo nicht vor** — bestätigt Z3.

## 1.2 Vorschlag: Umbenennung Taggeld → Entfernungszulage

**An den Zahlen ändert sich NICHTS — das bestätige ich ausdrücklich.** Begründung, nicht Behauptung:
Die Umbenennung berührt ausschließlich **Anzeige-Strings** (T9, T16, T17) und den **CSV-Spaltenkopf** (T14).
Der Rechenpfad ist `_kvTaggeldTag` (Z.2251) → `if(a>11) return t11; if(a>6) return t6; return 0;` mit
`t6`/`t11` aus den KV_RULES-Feldern. Weder Stufengrenzen (6 h / 11 h) noch Sätze (11,94 / 30,00) hängen
an einem der Strings. Solange die **Feldnamen** `taggeldAb6h`/`taggeldAb11h` unangetastet bleiben
(→ **P3**), ist die Änderung rein kosmetisch und ergebnisneutral.

**Empfohlener Scope (P3, Variante A):** nur die 4 sichtbaren Stellen umbenennen — T9, T14, T16, T17.
Feldnamen (T1), Funktionsname (T5), Rückgabefeld `taggeldSum` (T7) und Export (T8) **bleiben**, weil
sie in `system_config.kv_rules` **persistiert** sind: ein Umbenennen der Datenfelder erforderte eine
Datenmigration der gespeicherten Konfiguration und würde bei Altbeständen still auf die Fallback-Sätze
zurückfallen. Genau **das** wäre die einzige Variante, die Zahlen ändern könnte — deshalb nicht empfohlen.

## 1.3 Sätze und Stufen — Lohnverrechner-Prüfpunkte

| Stufe | Satz in der App | Anker | Status |
|---|---|---|---|
| > 6 h | **11,94 €** | Z.2187 / Z.2253 | **wird gerechnet** |
| > 11 h | **30,00 €** | Z.2187 / Z.2254 | **wird gerechnet** |
| mit Nächtigung | **62,04 €** (2027-Kommentar: 63,28 €) | Z.2187 / Z.2191 | ❌ **TOTER KNOPF — wird NIE gerechnet** |

**Befund zur Nächtigungsstufe:** `taggeldNacht` ist als Feld definiert **und** im Admin-UI editierbar
(T9), aber `_kvTaggeldTag` (Z.2251) liest den Wert **nirgends** — die Funktion kennt nur `>11h` und `>6h`.
Ein Admin kann den Satz also pflegen, ohne dass er je in eine Zahl einfließt. Das ist die gefährlichere
Variante von „tot": es sieht konfiguriert aus. Entscheidung dazu = **P2**.

**Nicht unterstellt, sondern offen:** ob 11,94 / 30,00 / 62,04 und die Grenzen 6 h / 11 h dem
aktuellen KV-Stand entsprechen, ist **im Repo nicht belegbar** — es existiert kein KV-Paragraphentext,
nur der Fallback-Wert im Code. `KV_ENTSCHEIDUNG_v668.md` hält dazu bereits fest: „Quelle fehlt".
→ **Lohnverrechner-Prüfpunkt**, keine App-Entscheidung.

**Zwei weitere Eigenschaften, die der Lohnverrechner kennen sollte:**
1. **Bemessungsgrundlage ist die Tages-Summe der `time_entries`** (Anwesenheitsnäherung, im Code als
   Näherung gelabelt: „KV: einschl. Wegzeit, ausschl. Mittagspause"), nicht eine geprüfte Anwesenheitszeit.
2. **Die Grenzen sind strikt** (`>6`, nicht `>=6`): ein Tag mit exakt 6,0 h ergibt **0 €**.

---

# TEIL 2 — Montagezulage (Vergabe-UI + Report)

## 2.1 Vergabe-UI — existiert bereits, hier der Ist-Zustand

| Frage aus dem Auftrag | Antwort (Code) |
|---|---|
| **Wo sitzt das Tages-Flag-Toggle?** | Im **Büro-Portal**, in der Komponente **`KVZulagenReport`** (Z.10787), Vergabe-Panel `_mzPanel` (Z.10864). Ein Button **pro Mitarbeiter-Tag** (`_tagBtn`, Z.10866) mit Tagesnummer + Stunden; grün = vergeben. Mobil: erst Monteur wählen, dann seine Tage (31 Spalten sind am Handy nicht darstellbar, Z.10876) |
| **Gate Büro/PL/Admin?** | ✅ Zweifach. **App-seitig:** der Report ist im Büro-Portal montiert, das „bereits staff-only" ist (Z.12007). **DB-seitig:** 4 Policies auf `montagezulage_tage`, alle `is_staff()` = `users.role IN ('admin','buero','projektleiter')` |
| **Monteur read-only?** | **Strenger als gefordert:** die SELECT-Policy ist ebenfalls `is_staff()` → ein Monteur kann die Vergabe **gar nicht lesen**. Falls „read-only" heißen soll, dass der Monteur seine eigenen vergebenen Tage sehen darf, wäre das eine **neue** Policy (→ **P7**) |
| **Schreibpfad** | `_mzSet(wid,datum,aktiv,von)` (Z.10775): **UPSERT** per `POST …?on_conflict=worker_id,datum` mit `Prefer: resolution=merge-duplicates,return=minimal` |
| **INSERT aktiv=true / DELETE bei Abwahl?** | **Weder noch — es ist ein UPSERT mit `aktiv`-Boolean.** Abwahl schreibt `aktiv=false`, die Zeile **bleibt** stehen. Die DELETE-Policy existiert, wird aber **nirgends benutzt**. Bewertung + Entscheid → **P5** |
| **`created_by`** | Gesetzt auf **`props.curUser.name`** (Z.10858), also den **Namen als Text**, nicht die User-ID. Spalte ist `text NULL`. Bewertung → **P6** |
| **Offline (SQ.push)?** | **Nein.** `_mzSet` ist ein direkter `fetch` über `_authRetry`, **nicht** über die Sync-Queue. Offline schlägt die Vergabe fehl; die UI dreht das optimistische Flag zurück und zeigt „❌ Vergabe nicht gespeichert" (Z.10859–10862). Bewusst so gebaut (Kommentar Z.10850: ein Schalter, der umspringt ohne DB-Speicherung, wäre schlimmer). Entscheid, ob das reicht → **P8** |

**Tabellen-Schema (DB, verifiziert):**
`worker_id text NOT NULL` · `datum date NOT NULL` · `aktiv boolean NOT NULL DEFAULT true` ·
`created_by text NULL` · `created_at timestamptz DEFAULT now()` · PK `(worker_id, datum)`.

## 2.2 Report — bereits umgestellt

**Alte Basis (Phase 1, bis v3.9.684):** `baustellenStd` = **Summe ALLER Monatsstunden** → die Zulage lief
über Werkstatt- und Fahrtzeiten mit. Zu hoch, bekannter KV-Punkt.

**Neue Basis (Phase 2, seit v3.9.685 — live):** `_kvZulagenMonat(tageStd, **0**, kv)` (Z.10828) liefert nur
noch das Taggeld; die Montagezulage kommt aus `_kvMontagezulageMonat(days, mzFlags, wid, kv)` (Z.2291),
das **ausschließlich geflaggte Tage** summiert: `std += h; tage++; sum += _kvMontagezulageTag(h,k,rules,true)`.
Satz nach **Jahr des Tages** (`_kvMontagezulageSatz`, Z.2274): `{2026: 1,155 · 2027: 1,178}`, nie rückwirkend;
unbekanntes Jahr → Fallback `montagezulageStd`.

**Was sich am Ergebnis ändert — heute: nichts.** Die Tabelle ist leer, also ist die Montagezulage in jedem
Report aktuell **0,00 €**. Sobald der erste Tag geflaggt wird, steigt sie von 0 aus an. Die Umstellung von
„alle Stunden" auf „geflaggte Tage" hat den Betrag also nicht gesenkt, sondern **auf null gesetzt, bis
jemand vergibt**. Das ist der eigentlich wichtige Governance-Punkt: **solange niemand flaggt, bekommt kein
Monteur Montagezulage.** → **P1** ist damit auch eine Frage, ob rückwirkend für Juli vergeben werden muss.

---

# TEIL 3 — €-Beispiele

> **ANNAHME (markiert, nicht belegt):** Stundensatz **20,00 € brutto**. Er dient nur der Größeneinordnung —
> **keine der beiden Zulagen hängt rechnerisch vom Stundensatz ab.** Die Montagezulage ist ein €-Betrag
> **je Stunde**, die Entfernungszulage ein €-Betrag **je Tag**.

### B1 — Montagezulage, Volltag Baustelle MIT Flag
Monteur, 14.07.2026, **8,5 h** gebucht (bereits ohne Mittagspause), Tag geflaggt.
```
8,5 h × 1,155 €/h (Satz 2026)          =  9,8175 €  →  9,82 €
```
Zum Vergleich Lohn (Annahme 20 €): 8,5 × 20 = 170,00 € → die Zulage sind **+5,8 %**.
Derselbe Tag im Jahr **2027**: `8,5 × 1,178 = 10,013 € → 10,01 €` (Satz nach **Jahr des Tages**, nie rückwirkend).

### B2 — Fahrtzeitlastiger Tag OHNE Flag
Monteur, 15.07.2026, **7,0 h** gebucht, davon ~3 h Wegzeit/Werkstatt, **kein Flag gesetzt**.
```
Montagezulage: _kvMontagezulageTag(7,0; flag=false)  =  0,00 €
```
**Büro-Briefing (KV Pkt. 6/7):** Wegzeiten und Werkstatttage **nicht** flaggen. Genau dafür ist die
manuelle Vergabe da — die alte Automatik hätte hier fälschlich `7,0 × 1,155 = 8,09 €` ausgeworfen.

### B3 — Entfernungszulage, 1 Beispieltag je Stufe

| Fall | Tages-Anwesenheit | App rechnet heute | Anmerkung |
|---|---|---|---|
| Stufe > 6 h | 7,5 h | **11,94 €** | |
| Stufe > 11 h | 11,5 h | **30,00 €** | ersetzt die 6h-Stufe, wird nicht addiert |
| **mit Nächtigung** | z.B. 12,0 h + Übernachtung | **30,00 €** ⚠️ | **nicht 62,04 €** — die Nächtigungsstufe wird nie ausgewertet (siehe 1.3 / **P2**). Die App kennt „Nächtigung" als Sachverhalt überhaupt nicht |
| Grenzfall | exakt 6,0 h | **0,00 €** | strikt `>6` |

### B4 — Kombinierter Tag (beide Zulagen)
8,5 h Baustelle, Tag geflaggt, Anwesenheit > 6 h:
```
Montagezulage   8,5 × 1,155  =  9,82 €
Entfernungszul. Stufe >6 h   = 11,94 €
────────────────────────────────────────
Summe Tag                    = 21,76 €
```
So erscheint es auch im CSV an den Lohnverrechner (Spalten `Taggeld EUR` + `Montagezulage EUR` + `Gesamt EUR`).

---

# TEIL 4 — Offene Entscheidungspunkte

Bitte pro Punkt freigeben (z.B. „P1 A, P2 B, P3 A, …"). **Nichts davon wird ohne Einzel-Freigabe gebaut.**

### P1 — Montagezulage-Basis: welche Stunden sind zulagefähig?
Der Auftrag fragt „alle Std ODER ohne Fahrt/Werkstatt?". **Im Code ist das bereits entschieden:** es zählen
die **gebuchten Tages-Stunden eines geflaggten Tages** — ungetrennt. Wird ein Tag geflaggt, gehen **alle**
Stunden dieses Tages in die Zulage, auch die 1,5 h Rückfahrt.
- **A** (Ist, empfohlen): bleibt so. Die Trennung passiert **organisatorisch** über die Flag-Vergabe (Büro
  flaggt nur echte Montagetage). Einfach, keine neue Datenerfassung.
- **B**: Zulage nur auf Stunden, die auf Baustellen-Projekte gebucht sind (Fahrt/Werkstatt raus). **Braucht
  eine verlässliche Tätigkeitsart je `time_entry` — die gibt es heute nicht.** Wäre ein eigenes Projekt.
- **C**: Pauschale je geflaggtem Tag statt × Stunden (Tagessatz).
- **Teilfrage P1b:** muss für **Juli rückwirkend** vergeben werden? (Tabelle ist leer → Juli-Report zeigt
  aktuell 0,00 € Montagezulage für alle.)

### P2 — Nächtigungsstufe `taggeldNacht` (62,04 €)
Toter Konfig-Knopf: editierbar, wird nie gerechnet.
- **A**: **entfernen** (Feld + Admin-Label) — ehrlichster Zustand, keine Scheinkonfiguration.
- **B**: **aktivieren** — braucht ein Nächtigungs-Kennzeichen je Tag (die App erfasst das heute nirgends);
  wäre faktisch ein zweites Flag analog zur Montagezulage.
- **C**: stehen lassen, im Admin-UI als „derzeit ohne Funktion" kennzeichnen.
- ⚠️ Solange A/B nicht entschieden ist, gilt: **Nächtigungen werden nicht abgegolten** (nur 30,00 €).

### P3 — Umbenennungs-Scope „Taggeld" → „Entfernungszulage"
- **A** (empfohlen): **nur Anzeige** — Admin-Labels (T9), Report-Titel (T16), Spaltenkopf (T17),
  **CSV-Header** (T14). Ergebnisneutral, kein Migrationsrisiko.
- **B**: zusätzlich **KV_RULES-Feldnamen** (`taggeldAb6h` → `entfernungszulageAb6h` …). **Nicht empfohlen:**
  die Felder liegen persistiert in `system_config.kv_rules`; ohne Datenmigration fiele die App still auf die
  Fallback-Sätze zurück — die einzige Variante, die Zahlen ändern kann.
- **C**: zusätzlich Funktions-/Feldnamen im Code (`_kvTaggeldTag`, `taggeldSum`) — reine Kosmetik, berührt
  Tests und window-Exporte.
- **Teilfrage P3b:** soll der **CSV-Header** mitwandern? Der Lohnverrechner erkennt die Spalte evtl. am
  Namen — Umbenennung bitte mit ihm abstimmen, sonst bricht dort ggf. eine Weiterverarbeitung.

### P4 — Report-Titel
Aktuell „💶 KV-Zulagen — Taggeld & Montagezulage".
- **A**: „💶 Zulagen — Entfernungszulage & Montagezulage" (Sebastians „genau zwei Zulagen" wörtlich).
- **B**: „💶 KV-Zulagen — Entfernungszulage & Montagezulage" (KV-Bezug behalten; beachte offenes **Z6**:
  Metallgewerbe vs. Metallnebengewerbe).

### P5 — Abwahl: `aktiv=false` (Ist) oder DELETE?
- **A** (Ist, empfohlen): UPSERT auf `aktiv=false`. Die Zeile bleibt inkl. `created_by`/`created_at` →
  **nachvollziehbar, dass jemand bewusst abgewählt hat.** Bei einer lohnrelevanten Größe ist das der
  bessere Audit-Trail.
- **B**: DELETE (Policy existiert bereits). Tabelle bleibt schlank, aber die Abwahl ist danach unsichtbar.
- ⚠️ Hinweis zu A: `_mzFetch` liest **nur `aktiv=true`** in die Flags (Z.10770) — funktional korrekt.
  Eine spätere Auswertung „wer hat wann abgewählt" wäre mit A möglich, mit B nicht.

### P6 — `created_by` = Name statt User-ID
Heute wird `curUser.name` als **Text** gespeichert (Z.10858).
- **A**: so lassen (im CSV/Report sofort lesbar, kein Join nötig).
- **B**: auf `users.id` umstellen (stabil bei Namensänderungen, saubere Referenz) — braucht Spalte/Migration.
- **C**: beides (`created_by_id` ergänzen).
- Praktisch: bei zwei Mitarbeitern gleichen Namens ist A nicht eindeutig.

### P7 — Darf der Monteur seine vergebenen Tage sehen?
Heute: **nein** (SELECT ist `is_staff()`).
- **A** (Ist): bleibt intern. Weniger Rückfragen an der Front, aber der Monteur kann seine Zulage nicht prüfen.
- **B**: neue SELECT-Policy „eigene Zeilen" (`worker_id` = eigener Worker) + kleine Anzeige in der
  Mitarbeiter-Ansicht. **Lohnrelevante Transparenz** — bitte bewusst entscheiden.

### P8 — Offline-Vergabe
Heute: kein SQ, Fehlschlag + Rückdrehen + Toast.
- **A** (Ist, empfohlen): so lassen. Bei einer lohnrelevanten Vergabe ist „nicht gespeichert" ehrlicher als
  eine Queue, die später still durchläuft.
- **B**: in die Sync-Queue aufnehmen (offline vergeben, drained später).

### P9 — Toter Hinweistext
Z.10906 warnt „Tabelle `montagezulage_tage` fehlt — SQL ausführen". Die Tabelle **existiert**; der Text
kann nie mehr erscheinen.
- **A**: Hinweis entfernen (Aufräumen, 1 Zeile).
- **B**: als Sicherheitsnetz stehen lassen (falls die Tabelle je verschwindet).

---

## Zusammenfassung für die Freigabe

| Punkt | Frage | Meine Empfehlung |
|---|---|---|
| **P1** | Zulagefähige Stunden | **A** (geflaggter Tag = alle Std) + **P1b klären: Juli rückwirkend?** |
| **P2** | `taggeldNacht` 62,04 € | **A entfernen** oder bewusst **B aktivieren** — Status quo ist irreführend |
| **P3** | Umbenennungs-Scope | **A** (nur Anzeige + CSV), **B ausdrücklich nicht** |
| **P4** | Report-Titel | **A** |
| **P5** | Abwahl-Semantik | **A** (`aktiv=false`, Audit-Trail) |
| **P6** | `created_by` | **A** kurzfristig, **C** wenn Eindeutigkeit gefordert |
| **P7** | Monteur-Sicht | bewusst entscheiden — Transparenz vs. Rückfragen |
| **P8** | Offline | **A** |
| **P9** | Toter Hinweis | **A** |

**Lohnverrechner-Prüfpunkte (nicht von uns entscheidbar):** Sätze 11,94 / 30,00 / 62,04 und die Stufen
6 h / 11 h · Montagezulage-Sätze 1,155 (2026) / 1,178 (2027) · CSV-Spaltenname (P3b) · offener **Z6**
(Metallgewerbe vs. Metallnebengewerbe).

**Nicht gebaut. Kein Code, keine UI, kein `index.html`-Commit.** Der Bau folgt nach den Einzel-Freigaben.
