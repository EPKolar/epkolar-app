# Cleanup: Montagezulage aus der App entfernt (v3.9.774, 2026-07-20)

Sebastian-Entscheid (endgueltig): Die **Montagezulage** wird kuenftig ausschliesslich
vom **Lohnverrechner** gemacht. Die App fuehrt nur noch die **Entfernungszulage**.

## App-seitig entfernt (v3.9.774)

- Modul-Rechenhelfer: `_kvMontagezulage`, `_kvMontagezulageSatz`, `_kvMontagezulageTag`,
  `_kvMontagezulageMonat`, `_mzKey`, `_mzWtag` (inkl. window-Exports).
- Modul-Datenzugriffe: `_mzFetch` / `_mzSet` (lasen/schrieben `montagezulage_tage`).
- `KVZulagenReport`: mz-States (`mzFlags`/`mzMissing`/`mzOpen`/`mzWid`), Lade-Effekt,
  Vergabe-Panel (`_mzToggle`/`_mzPanel`/`_tagBtn`), Montage-Spalten in Tabelle + CSV.
- `KV_RULES_FALLBACK`: Felder `montagezulageStd` und `montagezulage` (Jahres-Saetze).
- `KVRulesConfig`: Montagezulage-Jahres-Saetze-Block + `montagezulageStd`-Input.

Unveraendert geblieben (Entfernungszulage): `taggeldAb6h` (11,71), `taggeldAb11h` (30,00),
`taggeldNacht`, `kmGeld`, `_kvTaggeldTag`, `_kvZulagenMonat` (nur noch Taggeld), die
Tage>6h/Tage>11h-Zaehlung, der Vorschau-Warnkasten inkl. `_ezDetail`-Detail-Aufklapp.

## DB-Tabelle `montagezulage_tage`

**Tabelle `montagezulage_tage` + RLS bleiben, App-seitig ab v3.9.774 ungenutzt
(Montagezulage macht der Lohnverrechner). DDL-Drop = spaeteres Human-Gate.**

Kein Drop in dieser Aenderung. Bestehende Datensaetze bleiben unangetastet; sie werden
von der App weder gelesen noch geschrieben.
