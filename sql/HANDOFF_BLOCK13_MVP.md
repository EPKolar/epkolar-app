# Block 13 — Status: already-done + CSV-Bonus · v3.5.176

## Finding
Block 13 (Audit-Log-UI) **war bereits komplett implementiert** vor dieser Session:

**Location**: `adminTab='aktivitaet'` im AdminPanel (index.html Line 5839-5913)

**Features (bereits da)**:
- Login-Verlauf-Tabelle (letzte 50)
- Activity-Log-Tabelle mit Filtern (Benutzer, Aktion, Zeitraum 1/7/30/90 Tage)
- Action-Labels via `ACT_LABELS`, Entity-Labels via `ENT_LABELS`
- Color-coded indicators pro Aktion (login green, delete red, create blue, update orange)
- Max-500-Zeilen-Scope, UI-scroll-Limit bei 200 (maxHeight 400px)
- User-Name-Resolution (user_id → Name aus users-Array)

Das war bereits mehr als der Block-13-MVP-Scope des Prompts ("nur 4 Spalten, keine Filter, kein CSV").

## Bonus-Delivery: v3.5.176 CSV-Export

Da Block 13 bereits erledigt war, habe ich die in der Roadmap für "v3.5.177" geplante CSV-Funktion vorgezogen:

**CSV-Export-Button** "📥 CSV" neben den Filter-Selects.

**Commit**: `d2efc6f`

### Spec
- Spalten: `Zeit;Benutzer;Aktion;Entity-Typ;Entity-ID;Details`
- Separator: `;` (Excel AT-Locale)
- Encoding: UTF-8 mit BOM (für Excel Umlauts)
- Escaping: `""` (RFC-4180 konform)
- Zeilenumbrüche: `\r\n`
- Filename: `audit_log_YYYY-MM-DD.csv`
- Scope: exportiert die aktuell geladenen/gefilterten Zeilen (respektiert User/Action/Days-Filter)

### Smoke-Test (2 min)
1. Admin-Panel → Tab "📋 Aktivität"
2. Filter einstellen (z.B. "7 Tage", alle User)
3. "📥 CSV"-Button klicken
4. Download `audit_log_2026-04-19.csv` sollte starten
5. In Excel öffnen:
   - Spalten erkannt via `;`
   - Umlauts korrekt (ä, ö, ü)
   - Keine zerrissenen Zeilen bei Details mit Kommas
   - Toast "📥 N Zeilen exportiert"

### Regression-Risiko
**Niedrig** — nur ein neuer Button hinzugefügt, kein Refactor der bestehenden Tabelle.
