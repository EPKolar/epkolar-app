# OFFA Land-Feld Regression-Analyse · Phase 1 · 2026-04-24

**Context:** OFFA-Log 24.04.2026 07:03 zeigt bei jedem AS-Sync:
```
S07xxxx: Das Feld Länderkürzel wurde von 'A' in '' geändert.
         (Einsatz- UND Rechnungsadresse)
```

**Baseline:** `3ad138e` (v3.8.39 LIVE).
**Modus:** Pure Analyse, kein Code-Touch, kein Supabase-Write.

---

## 1 · Git-Archäologie

### exportOffa-Commits
```
3d620a9  Add files via upload
```

Exakt **ein** Commit — der initiale Repo-Import. Keine Änderung der `exportOffa`-Funktion seither.

### Länderkürzel / laenderkuerzel / kund_land / kundLand / countryCode / country_code — Commits

```
(keine)
```

**NONE FOUND.** Keine dieser Zeichenketten wurde je in einem tracked Commit von `index.html` eingeführt oder entfernt.

### Initial-Commit-Snapshot von `exportOffa` (3d620a9)

```js
const exportOffa=()=>{
  if(navigator.onLine&&API.getToken()){API.exportOffa({}).catch(()=>{});}
  const hdrs=["Nr","KdNr","Kunde","ProjNr","Art","Status","Monteur","Datum",
              "Arbeitsanweisung","Durchgeführt","Verrechnung","Sachbearbeiter"];
  const data=arbeitsscheine.filter(a=>a.scheinstatus!=="storniert").map((a,i)=>[
    i+1, a.kundNr, a.kundName, a.projektnr, …, a.sachbearbeiter]);
  genXls("📋 OFFA Export — Arbeitsscheine", …);
};
```

**12 Spalten, keine Adressfelder außer `KdNr`+`Kunde`. Kein Länderkürzel.** Identische Struktur wie heute (v3.8.39) — nur kleine Detail-Unterschiede (statusFilter-Arg, erweiterter statusMap).

---

## 2 · Aktueller exportOffa-Code (index.html L5107-5113)

**Spalten (12):**

| # | Header | Quelle |
|---:|---|---|
| 1 | `Nr` | Row-Index |
| 2 | `KdNr` | `a.kundNr` |
| 3 | `Kunde` | `a.kundName` |
| 4 | `ProjNr` | `a.projektnr` |
| 5 | `Art` | `AS_ART[a.scheinart].l` |
| 6 | `Status` | `AS_STATUS[a.scheinstatus].l` |
| 7 | `Monteur` | `monteure.find(m.id===a.monteur).n` |
| 8 | `Datum` | `fdt(a.aufgenommen)` |
| 9 | `Arbeitsanweisung` | `(a.arbeitsanweisungen||"").slice(0,80)` |
| 10 | `Durchgeführt` | `(a.durchgefuehrte||"").slice(0,80)` |
| 11 | `Verrechnung` | `AS_VERRECH[a.verrechnung].l` |
| 12 | `Sachbearbeiter` | `a.sachbearbeiter` |

- **SheetJS-Methode:** Keine direkte XLSX-Lib. Verwendet **`genXls(...)`** (L2911 — eigener AOA-basierter Excel-HTML-Blob-Generator). Headers+Rows als 2D-Array.
- **Adressfelder verwendet:** nur `kundNr` + `kundName`. **Keine Nutzung** von `kundStr`, `kundPlz`, `kundOrt`, `arbeitsort`.
- **Keine Stelle** mit hardcodiertem `"A"`, `"AT"` oder `"Österreich"` im Zusammenhang mit Land-Feld (weder in exportOffa noch in umgebendem Code).

---

## 3 · Juprowa-Pull/Push (der wahrscheinliche "Sync"-Pfad)

**KRITISCH:** Der OFFA-Log-Fehler kommt **nicht** vom Excel-Export (der ist manuell + Excel-Datei), sondern wahrscheinlich vom **Juprowa-Push-RPC**, der bei jedem Pending-Schein an Juprowa Cloud pusht (und von dort evtl. an OFFA relayed).

### Juprowa-Pull (`_mapJuprowaWorksheet`, L2314-2361)

Liest aus Juprowa-Worksheet-JSON:

| Juprowa-Feld | Lokal |
|---|---|
| `AK_BAUADR_NUMMER` / `ID_CUSTOMER` | `kundNr` |
| `AK_BAUADR_NAM1` / `RE_ADR_NAM1` | `kundName` |
| `AK_BAUADR_STR` | `kundStr` |
| `AK_BAUADR_PLZ` | `kundPlz` |
| `AK_BAUADR_ORT` | `kundOrt` |
| `AK_KONTAKT_TELEFON1` / `RE_KONTAKT_TELEFON1` | `kundTel` / `telefon` |
| `AK_KONTAKT_EMAIL` / `RE_KONTAKT_EMAIL` | `kundEmail` |
| `AK_BAUADR_*` (konkateniert) | `arbeitsort` (Str + PLZ + Ort) |

**Zwei separate Adress-Blöcke** im Juprowa-Format:
- `AK_BAUADR_*` = **Einsatz-/Bauadresse**
- `RE_ADR_*` = **Rechnungsadresse** (nur Name+Telefon+Email ausgelesen, keine Straße/PLZ/Ort)

**Kein `_LAND`-Suffix** in den gepullten Feldern — Pull ignoriert Länderkürzel komplett.

### Juprowa-Push (`_juprowaReversMap`, L2503-2525)

Push-JSON enthält **9 Felder:**

```
ID, AK_SCHEINNR, AK_ARBEITEN, AK_NOTIZ, AK_DURCHZUFUEHREN,
AK_MONTEUR, AK_TERMIN, AK_DAUER, AK_PRIOR, AK_AUFSTATUS
```

**KEINE Adress-Felder im Push.** Kein `AK_BAUADR_*`, kein `RE_ADR_*`, kein `*_LAND`.

**Implikation:** Wenn Juprowa (oder ein nachgelagertes OFFA-Relay) "nicht gesendete Felder" als "Feld soll leer gesetzt werden" interpretiert → entsteht genau der beobachtete Log-Eintrag "Länderkürzel von 'A' auf '' geändert".

---

## 4 · arbeitsort-Feld-Analyse

**Definition:** Einzelnes **String-Feld** (nicht strukturiert!).

| Line | Kontext | Nutzung |
|---|---|---|
| 1389 | `_mapArbeitsschein` (Pull-Mapping) | `arbeitsort: a.arbeitsort \|\| ""` |
| 2356 | `_mapJuprowaWorksheet` | **Konkateniert** `AK_BAUADR_STR + ", " + AK_BAUADR_PLZ + " " + AK_BAUADR_ORT` zu einem String |
| 2413 | Pull-Merge | `if(mapped.arbeitsort!==existing.arbeitsort) upd.arbeitsort=...` |
| 2606 | `_parseOffaPdf` (defaults) | Leer initialisiert |
| 2636 | OFFA-PDF-Parser | Aus PDF-Feld "Arbeitsort" extrahiert, mit `", "` zusammengefügt |
| 5038 | `defAs()` (neuer AS) | Leer initialisiert |
| 5133 | OFFA-Import | aus Parser übernommen |

Befüllung via UI-Input: **nicht via grep sichtbar** — wahrscheinlich nur aus Pull/Import gespeist, kein dediziertes Input-Field (Monteur sieht es nur read-only aus Juprowa-Sync).

**Im OFFA-Excel-Export (L5108) kommt `arbeitsort` NICHT vor.**

---

## 5 · Supabase-Schema (pending Sebastian-Output)

Sebastian führt `sql/OFFA_LAND_CHECK.sql` manuell aus. Erwartet werden:

- **Query 1:** Land-/Country-/Einsatz-Spalten in `arbeitsscheine`. Wahrscheinliches Ergebnis: leer (keine solche Spalte existiert) → **GREENFIELD**-Indikator.
- **Query 2:** Vollständiges Schema von `arbeitsscheine` — um zu prüfen ob evtl. unbekannte Spalte mit exotischem Namen existiert (z. B. `kunde_land`, `einsatz_land`, etc.).
- **Query 3:** Separate Adress-Tabellen (unwahrscheinlich, aber ausgeschlossen).

**Sebastian liefert das Ergebnis nach Ausführung.**

---

## 6 · Regression-Verdikt

**Kategorie: GREENFIELD** (mit einem DISCONNECTED-Twist).

### Begründung

1. **`index.html` hatte nie** ein Land-/Country-Feld in getrackten Commits (git `-S`-Search 0 Treffer).
2. Der OFFA-Excel-Export hat und hatte **nie** eine Adress-Spalte mit Länderkürzel.
3. Der Juprowa-Push schickt **nie** Adress-Felder mit (keine `AK_BAUADR_*` oder `RE_ADR_*` im Push-JSON). Das ist keine Regression — das war immer so.
4. **DISCONNECTED-Twist:** Juprowa-Cloud (und ein vermuteter OFFA-Relay) **hat** diese Adress-Felder inklusive Länderkürzel server-side. Unser Pull liest sie (aber nur Str/PLZ/Ort). Unser Push sendet sie nicht zurück.

### Warum erscheint der Log "von 'A' auf '' geändert"?

**Hypothese (zu verifizieren):** Das OFFA/Juprowa-Backend führt bei jedem `juprowa_push_worksheet`-RPC ein **Full-Update** durch, bei dem nicht-gesendete Adress-Felder als "explizit leer" interpretiert werden. Vorher war das Längen-Kürzel implizit "A" (aus Stammdaten/Default). Nach Push → "" weil unser JSON das Feld nicht enthält.

**Alternative Hypothese:** Ein Schema-Change oder Konfig-Update in OFFA/Juprowa selbst (nicht in unserem Repo) zwingt seit kurzem, dass Adress-Länderkürzel explizit gesendet werden müssen.

### Sebastian's Aussage "Der Sync war schonmal OHNE diesen Fehler"

Ehrlich: **Ich kann das aus der git-History allein nicht bestätigen.** Der einzige getrackte Commit auf `exportOffa` ist der Initial-Import; `_juprowaReversMap` ebenfalls kein Änderungs-Commit sichtbar (nicht explizit geprüft, aber der Push-JSON-Aufbau ist stabil). Wenn der Fehler früher NICHT auftrat, liegt die Änderung:
- entweder vor dem Initial-Commit (außerhalb git-History),
- oder in Juprowa/OFFA server-side,
- oder der Fehler existiert länger und fiel bisher nicht auf (zB weil Log-Level niedriger war).

---

## 7 · Empfehlung für Sebastian

Drei Fix-Pfade:

### Pfad A · Länderkürzel in Push ergänzen (minimalinvasiv)

In `_juprowaReversMap` die Länderkürzel-Felder hart auf `"A"` setzen:
```js
json.AK_BAUADR_LAND = "A";
json.RE_ADR_LAND = "A";
```

**Voraussetzung:** Exakte Juprowa-Feldnamen verifizieren (via Pull-Response `jws`-Snapshot oder Juprowa-Doku). Der Pull-Code kennt `AK_BAUADR_STR/PLZ/ORT` aber kein LAND — heißt das Juprowa hat das Feld unter anderem Namen?

**Aufwand:** 15 min (2 Zeilen + Doku + Test). Kein Schema-Change nötig.

**Risiko:** Niedrig. Falls falscher Feldname → Juprowa ignoriert es still, nichts kaputt.

### Pfad B · Land-Feld in Schema + UI einführen

- Neue Spalte `arbeitsscheine.kund_land TEXT DEFAULT 'A'`.
- `_mapBody`-RENAME erweitern: `kundLand: 'kund_land'`.
- UI-Input für Admin/PL beim AS-Edit (optional).
- Push sendet `json.AK_BAUADR_LAND = schein.kundLand || 'A'`.
- (optional) Einsatz- vs. Rechnungsadresse trennen: zusätzliche `re_adr_land`.

**Aufwand:** 2-3 h (Schema + RENAME + UI + Push + Tests + Migration-Default).

**Risiko:** Mittel. Schema-Migration + RLS-Prüfung.

### Pfad C · Nichts ändern, OFFA-Log ignorieren

Nur sinnvoll wenn das OFFA-Log lediglich informativ ist und keinen Fehlschlag triggert. Sebastian prüft das.

**Aufwand:** 0. Doku-Entry dass "Log von 'A' auf '' ist erwartet, kein Bug".

---

## Empfohlener Nächster Schritt

1. **Sebastian** führt `sql/OFFA_LAND_CHECK.sql` aus und liefert das Ergebnis.
2. **Sebastian** prüft in Juprowa-Doku / Support-Portal den exakten Feldnamen (`AK_BAUADR_LAND` oder ähnlich) und ob leer-setzen valide ist oder ein Fehler-Trigger.
3. **Sebastian** entscheidet Pfad A / B / C basierend auf (1)+(2).
4. Phase 2 (Fix) erst nach expliziter Freigabe.
