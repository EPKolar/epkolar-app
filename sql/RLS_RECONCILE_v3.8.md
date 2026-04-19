# RLS-Matrix ↔ Policy Reconcile v3.8 · Block 5 Template

Sebastian führt `sql/RLS_SNAPSHOT_v3.8.sql` aus, füllt dann die folgende Tabelle mit Gap-Analyse.

## Methode

1. SNAPSHOT-SQL ausführen, Output in `RLS_SNAPSHOT_v3.8_OUTPUT.md` dumpen (optional).
2. Für jede Tabelle aus `PERMISSION_MATRIX_v3.7.md` Vergleich:
   - **Erwartete Regel** (Matrix): was SOLL die Rolle können?
   - **Reale Policy** (Snapshot): was kann die Rolle wirklich?
3. Status pro Tabelle × Rolle × Command (SELECT/INSERT/UPDATE/DELETE) klassifizieren.

## Status-Kategorien

| Status | Bedeutung | Aktion |
|---|---|---|
| **MATCH** | Matrix ↔ Policy stimmen überein | Nichts tun |
| **MISSING_POLICY** | Matrix erlaubt, aber keine Policy vorhanden + RLS aktiv | Policy erstellen (wenn Tabelle sensibel) |
| **POLICY_WEITER** | Policy erlaubt MEHR als Matrix → Sicherheitsrisiko | DROP+CREATE enger (P1!) |
| **MATRIX_WEITER** | Matrix sagt MEHR als Policy → UX-Bug | Entscheidung: Matrix korrigieren ODER Policy erweitern |
| **RLS_DISABLED** | Tabelle hat `rowsecurity=false` → alles lesbar | ENABLE + Policies bauen (P1!) |

## Reconcile-Tabelle

Pro Tabelle aus PERMISSION_MATRIX_v3.7.md:

### arbeitsscheine
| Rolle | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| admin | MATCH | MATCH | MATCH | MATCH |
| buero | MATCH | MATCH | MATCH | MATCH |
| projektleiter | MATCH | MATCH | MATCH | MATCH |
| monteur | MATCH (RLS auf monteur=self) | __ | __ | __ |

### time_entries
| Rolle | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| admin | __ | __ | __ | __ |
| monteur | MATCH (RLS auf worker_id=self) | __ | __ | __ |

### notifications · absences · fahrtenbuch · as_kommentare · worker_kompetenzen
(B-007 schon deployed, erwartet MATCH)

### users
| Rolle | SELECT |
|---|---|
| admin/buero | MATCH (alle sichtbar) |
| monteur | **PRÜFEN**: Policy sollte non-staff nur `id=current_user_pk()` erlauben |

### photos
Block 1 (PHOTOS_RLS_AUDIT.sql) liefert die Daten. Nach Audit hier eintragen.

### supplier_articles
| Rolle | SELECT |
|---|---|
| alle authenticated | sollten sehen (Produktkatalog) |
| ek_preis-Spalte | **PRÜFEN**: nur Admin/PL/Lagerleitung |

→ **Column-Level Security mit `ek_preis` über `grant SELECT(..) TO role`?** (nicht per-row, sondern per-column)

### supplier_configs
| Rolle | SELECT | WRITE |
|---|---|---|
| admin | MATCH | MATCH |
| andere | sollten NICHT sehen (enthält Credentials!) | nein |

→ **P1 wenn non-admin lesen kann** → DROP public-select-Policy

### activity_log
| Rolle | SELECT |
|---|---|
| admin | MATCH |
| andere | **PRÜFEN**: manche apps leaken dies |

## Gefundene Gaps

*(Nach Snapshot-Review befüllen)*

- [ ] Gap 1: ___
- [ ] Gap 2: ___

## Fix-Strategie je Gap-Typ

**POLICY_WEITER (Security-Risk)** → sofort in `sql/RLS_FIX_v3.8.sql` DROP+CREATE-engere-Policy.

**MISSING_POLICY auf sensibler Tabelle** → sofort CREATE in `sql/RLS_FIX_v3.8.sql`.

**MATRIX_WEITER** → in diesem MD-File Entscheidung dokumentieren (Matrix korrigieren oder Policy erweitern), Sebastian entscheidet.

**RLS_DISABLED auf sensibler Tabelle** → sofort ALTER TABLE ENABLE RLS + Policies.

## Template `sql/RLS_FIX_v3.8.sql`

Wird erst angelegt wenn Reconcile-Ergebnis vorliegt. Bis dahin leer.
