# -*- coding: utf-8 -*-
"""v3.9.785 — Entfernungszulage 3-Stufen (klein/mittel/gross), LOHNRELEVANT (Sebastian 21.07.2026).

KV-Blatt ab 01.01.2026: klein 11,94 / mittel 30,00 / gross 62,04 EUR/Tag. GENAU EINE Stufe pro Tag, nie additiv.
Modell: entfernungszulage_tage.aktiv(bool) -> stufe text CHECK(klein/mittel/gross), NULL=keine. Klick-Zyklus
Vorschlag->klein->mittel->gross->keine->Vorschlag. Saetze editierbar im Buero-Portal (admin+buero).
"""
import re
import subprocess


def _block(index_html):
    start = index_html.index("function _ezWtag(iso){")
    end = index_html.index("async function _ezFetch(ym){", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "ez785.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_saetze_pin(index_html):
    """Satz-Pin: klein 11,94 (taggeldAb6h, Alt 11,71 war falsch) / mittel 30,00 (ezMittel) / gross 62,04 (ezGross)."""
    assert "taggeldAb6h:11.94," in index_html
    assert "ezMittel:30.00, ezGross:62.04," in index_html
    # _ezSaetze liefert die 3 Saetze mit KV-2026-Fallback
    assert "function _ezSaetze(kv){" in index_html
    assert "window._ezSaetze=_ezSaetze" in index_html


def test_klick_zyklus_pure(index_html, node_exe, tmp_path):
    """PURE Klick-Zyklus: Vorschlag(undef)->klein->mittel->gross->keine(null)->Vorschlag; 'keine' NIE in 1 Klick."""
    js = _block(index_html) + _OK + u"""
ok(_ezCycleNext(undefined)==='klein','Vorschlag -> klein (1 Klick bestaetigt)');
ok(_ezCycleNext('klein')==='mittel','klein -> mittel');
ok(_ezCycleNext('mittel')==='gross','mittel -> gross');
ok(_ezCycleNext('gross')===null,'gross -> keine (null)');
ok(_ezCycleNext(null)===undefined,'keine -> zurueck Vorschlag (undefined = Zeile loeschen)');
// 'keine' (null) darf NIE in einem Klick aus dem Vorschlag erreichbar sein
ok(_ezCycleNext(undefined)!==null,'keine nicht in 1 Klick aus Vorschlag');
ok(_ezCycleNext('klein')!==null,'keine nicht in 1 Klick aus klein');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_stufe_meta_pure(index_html, node_exe, tmp_path):
    """_ezStufeMeta: Klartext + Farbe je Stufe (Anzeige)."""
    js = _block(index_html) + _OK + u"""
ok(_ezStufeMeta('klein').label==='klein' && _ezStufeMeta('klein').lang==='Entfernungszulage klein','klein');
ok(_ezStufeMeta('mittel').label==='mittel','mittel');
ok(_ezStufeMeta('gross').label==='groß' && _ezStufeMeta('gross').lang==='Entfernungszulage groß','gross ausgeschrieben');
ok(_ezStufeMeta('').label==='keine','leere Stufe -> keine');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_migration_pin(index_html, node_exe, tmp_path):
    """Migrations-Pin: alt aktiv=true liest als 'klein'; aktiv=false -> keine; gesetzte stufe gewinnt."""
    js = _block(index_html) + _OK + u"""
ok(_ezStufeFromRow(null,true)==='klein','alt aktiv=true -> klein');
ok(_ezStufeFromRow(null,false)===null,'aktiv=false -> keine (null)');
ok(_ezStufeFromRow('mittel',false)==='mittel','stufe gewinnt vor aktiv');
ok(_ezStufeFromRow('gross',true)==='gross','stufe gross');
ok(_ezStufeFromRow('unsinn',true)===null,'ungueltige stufe -> keine');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_migration_sql_datei():
    """DDL liegt als Datei (HUMAN-RUN-GATE): additiv stufe, Backfill aktiv=true->klein, aktiv NICHT gedroppt."""
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "ENTFERNUNGSZULAGE_STUFE_v1.sql")
    assert os.path.exists(p), "sql/ENTFERNUNGSZULAGE_STUFE_v1.sql fehlt"
    sql = open(p, encoding="utf-8").read()
    assert "-- IDEMPOTENT" in sql
    assert "add column if not exists stufe text" in sql
    assert "check (stufe in ('klein','mittel','gross'))" in sql
    assert "set stufe = 'klein'" in sql and "aktiv = true" in sql
    assert "drop column aktiv" not in sql.split("SPAETERER")[0], "aktiv darf in diesem Schritt NICHT gedroppt werden"


def test_report_und_pdf_stufen_ausgeschrieben(index_html):
    """PDF + Report: ausgeschriebene Stufe je Tag (Notiz) + Fuss je Stufe (klein/mittel/groß + Summe)."""
    pdf_start = index_html.index("async function _pzePdf(")
    pdf = index_html[pdf_start:index_html.index("function PZEView(", pdf_start)]
    # Notiz je Tag: ausgeschriebene Stufe statt "EZ"
    assert "var notiz=_stTag?_ezStufeMeta(_stTag).lang:'';" in pdf, "Notiz muss die ausgeschriebene Stufe zeigen"
    # Fuss je Stufe + Summe
    assert "Entfernungszulage — klein:" in pdf and "mittel:" in pdf and "groß:" in pdf
    assert "Summe Entfernungszulage:" in pdf
    # Report-Tabelle: Spalten je Stufe
    assert "['Monteur','klein','mittel','groß','Entfernungszulage']" in index_html
    assert "ezKlein:ez.tageKlein,ezMittel:ez.tageMittel,ezGross:ez.tageGross" in index_html


def test_satz_maske_buero_portal(index_html):
    """Zulagensaetze im Buero-Portal editierbar (admin+buero via bueroexport-Gate): Maske + Persistenz kv_rules."""
    # Der EZ-Report (KVZulagenReport) sitzt im bueroexport-gegateten VBueroExport
    assert "React.createElement(KVZulagenReport, {" in index_html
    # Maske: Bearbeiten-Button + Save auf system_config.kv_rules (gemergt, nur EZ-Felder)
    assert "⚙ Zulagensätze bearbeiten" in index_html
    assert "const _ezRateSave=async()=>{" in index_html
    assert "base.taggeldAb6h=nk;base.ezMittel=nm;base.ezGross=ng;" in index_html, "nur die 3 EZ-Felder ueberschreiben"
    assert "_sbUpsert('system_config',{key:'kv_rules'" in index_html, "Persistenz system_config.kv_rules"


def test_zaehler_ausgeschrieben(index_html):
    """Zaehler zeigt klein/mittel/groß ausgeschrieben (Sebastian: keine K/M/G-Kuerzel)."""
    assert "c.klein+' klein / '+c.mittel+' mittel / '+c.gross+' groß'" in index_html
