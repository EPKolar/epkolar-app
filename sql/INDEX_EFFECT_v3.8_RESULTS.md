# Index-Effekt-Verify Results v3.8 · Template

Sebastian füllt die Tabelle nach Ausführung von `sql/INDEX_EFFECT_v3.8.sql` im Supabase SQL-Editor aus.

## Methode

1. **Vor Index-Deploy**: `INDEX_EFFECT_v3.8.sql` einzeln durchlaufen, pro Query den `Planning Time` + `Execution Time` aus EXPLAIN ANALYZE notieren. Plan-Mode (Seq Scan vs Index Scan) markieren.
2. **Index deployen**: `INDEX_AUDIT_v3.6.sql` + `INDEX_AUDIT_v3.7.sql` ausführen.
3. **Nach Index-Deploy**: gleiche Queries erneut, selbe Werte notieren.
4. **Im Browser**: `await window._perfBench()` — Client-Wall-Clock (network-included).

## Results-Tabelle

| # | Query | Index | Vor (ms/plan) | Nach (ms/plan) | Verbesserung | Verdict |
|---|---|---|---|---|---|---|
| 1 | AS monteur+status+termin | ix_as_monteur_status | __/__ | __/__ | __% | __ |
| 2 | AS UPPER(nummer) | ix_as_nummer | __/__ | __/__ | __% | __ |
| 3 | AS termin offen partial | ix_as_termin_offen (v3.7) | __/__ | __/__ | __% | __ |
| 4 | TE worker+date | ix_te_worker_date | __/__ | __/__ | __% | __ |
| 5 | TE project+date | ix_te_project_datum (v3.7) | __/__ | __/__ | __% | __ |
| 6 | Notif user+unread partial | ix_notif_user_unread | __/__ | __/__ | __% | __ |
| 7 | Activity user | ix_activity_user_created | __/__ | __/__ | __% | __ |
| 8 | Activity action | ix_activity_action_created | __/__ | __/__ | __% | __ |
| 9 | SA FTS grohe | ix_sa_fts_german | __/__ | __/__ | __% | __ |
| 10 | FB worker | ix_fb_worker_datum (v3.7) | __/__ | __/__ | __% | __ |
| 11 | Komm per AS | ix_kommentare_as_created (v3.7) | __/__ | __/__ | __% | __ |
| 12 | Photos per entity | ix_photos_entity (v3.7) | __/__ | __/__ | __% | __ |

## Verdict-Kategorien

- **EFFECTIVE** (≥ 20% schneller ODER Seq→Index): Index behalten.
- **MARGINAL** (<20%, noch Index-Scan): behalten, niedriger Wartungsaufwand.
- **INEFFECTIVE** (keine Besserung oder Planner wählt Seq trotzdem): `DROP INDEX CONCURRENTLY IF EXISTS ix_xxx;`

## Client-Wall-Clock Baseline (_perfBench)

Vor Index-Deploy als admin auf gutem Laptop + AT-DSL:

| Test | ms |
|---|---|
| AS-Liste-50 | __ |
| AS-Suche-kundName | __ |
| AS-Offen-Count | __ |
| ZE-Monat-Current | __ |
| Artikel-FTS-grohe | __ |
| Notifications-Unread | __ |
| Projects-Active | __ |
| Fahrtenbuch-Recent | __ |
| Users-All | __ |

Nach Index-Deploy dieselbe Tabelle erneut, Differenz markieren.

## Pg_stat Monitoring (nach 1-2 Tagen Betrieb)

Query am Ende von `INDEX_EFFECT_v3.8.sql` erneut ausführen:
- `idx_scan=0` → UNUSED, DROP candidate
- `idx_scan<10` → LOW-USE, weiter beobachten
- `idx_scan>=10` → wird genutzt, behalten
