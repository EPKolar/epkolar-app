"""v3.9.681 Fahrtenbuch (Phase F2) — UI auf der Segmentierungs-Engine.

Die Fahrten kommen NICHT aus der DB, sondern werden bei jedem Laden aus fz_positions
segmentiert (_fzSegmente, v3.9.679). fz_fahrten haelt nur die Persistenz + die nachtraegliche
Kundenzuordnung durch Buero/PL.

Diese Guards sichern die Eigenschaften ab, die man beim Weiterbauen leicht kaputt macht:
  1. Das Fahrtenbuch degradiert sauber, wenn sql/FZ_FAHRTEN_v1.sql noch nicht gelaufen ist.
  2. Die Karte wird NICHT ent-mountet (Overlay) — sonst bricht der Leaflet-Lifecycle aus v3.9.663.
  3. Kein Privat/Geschaeftlich-Feld (Sebastian 13.07.: alles geschaeftlich).
  4. Kein rohes new Date("YYYY-MM-DD") im Zeitraum-Filter (UTC-Falle).
  5. §96: Fahrtenbuch haengt am isStaff-gegateten Flotte-Tab, kein eigener Rechte-Pfad noetig.
"""


def test_komponente_existiert(index_html):
    assert "function FahrtenbuchView(props){" in index_html


def test_fahrten_kommen_aus_der_engine_nicht_aus_der_db(index_html):
    # Quelle der Wahrheit ist die Segmentierung, nicht fz_fahrten.
    assert "const s=_fzSegmente(pos,{});" in index_html
    assert "async function _fzFetchRange(fid,fromIso,toIso){" in index_html


def test_degradiert_ohne_tabelle(index_html):
    # fz_fahrten fehlt (404 / 42P01) -> missing-Flag statt Crash, wie bei fz_latest.
    assert "async function _fzFetchFahrten(fid,fromIso,toIso){" in index_html
    assert "return{ok:false,missing:true,rows:[]};" in index_html
    assert "Tabelle fz_fahrten fehlt — sql/FZ_FAHRTEN_v1.sql ausführen" in index_html


def test_upsert_ist_idempotent(index_html):
    # Ohne on_conflict wuerde jeder Seitenaufruf die Fahrten duplizieren.
    assert 'SB_REST+"/fz_fahrten?on_conflict=fahrzeug_id,beginn"' in index_html
    assert "resolution=merge-duplicates" in index_html


def test_karte_bleibt_gemountet(index_html):
    # Overlay UEBER der Karte — kein bedingtes Rendern des Map-Containers. Sonst brechen
    # Popup-Restore / In-Flight-Guard / Trail aus v3.9.663.
    assert "buchOpen?h(FahrtenbuchView,{" in index_html
    assert "const [buchOpen,setBuchOpen]=_react.useState.call(void 0, false);" in index_html


def test_kein_privat_geschaeftlich_feld(index_html):
    # Entscheid Sebastian 13.07.2026: alles geschaeftlich. Kein zweck-Feld, kein Toggle.
    fb = index_html[index_html.index("function FahrtenbuchView(props){"):]
    fb = fb[: fb.index("\nfunction FlotteView(props){")]
    for verboten in ("privat", "geschäftlich", "geschaeftlich", "zweck"):
        assert verboten.lower() not in fb.lower(), (
            f"'{verboten}' im Fahrtenbuch — es gibt keinen Privat/Geschaeftlich-Unterschied"
        )


def test_zeitraum_ohne_utc_falle(index_html):
    # new Date("YYYY-MM-DD") waere UTC-Mitternacht -> abends gefahrene Strecken rutschen in den
    # Vortag. Der Filter muss die Datums-Teile lokal zusammensetzen.
    assert (
        "const _pd=function(s){const p=String(s||'').split('-');"
        "return new Date(parseInt(p[0],10),parseInt(p[1],10)-1,parseInt(p[2],10));};"
    ) in index_html
    assert "d.setHours(0,0,0,0);return d.toISOString();" in index_html
    assert "d.setHours(23,59,59,999);return d.toISOString();" in index_html


def test_paragraf_96_gate_unveraendert(index_html):
    # Der Flotte-Tab bleibt auf admin/projektleiter/buero gegated — Monteure sehen ihn nicht,
    # und damit auch das Fahrtenbuch nicht. Kein zweiter Rechte-Pfad.
    assert (
        'if(t.perm==="flotte")return curUser.role==="admin"'
        '||curUser.role==="projektleiter"||curUser.role==="buero";'
    ) in index_html


def test_sql_datei_ist_gestaged(index_html):
    from pathlib import Path

    p = Path(__file__).parent.parent / "sql" / "FZ_FAHRTEN_v1.sql"
    assert p.exists(), "sql/FZ_FAHRTEN_v1.sql fehlt"
    sql = p.read_text(encoding="utf-8")
    assert "HUMAN-RUN-GATE" in sql
    assert "CREATE TABLE IF NOT EXISTS public.fz_fahrten" in sql
    # Idempotenz-Anker fuer den Upsert
    assert "fz_fahrten_fz_beginn_uidx" in sql
    # RLS wie fz_positions: Staff lesen, lager_display hart geblockt (GPS = Kontrollmassnahme)
    assert "ENABLE ROW LEVEL SECURITY" in sql
    assert "is_staff()" in sql
    assert "lager_display" in sql
    # Keine zweck-SPALTE (das Wort darf im Kommentar stehen — dort erklaert es ja gerade,
    # dass der "Zweck" einer Fahrt die Kundenzuordnung ist und kein Privat/Geschaeftlich-Flag).
    spalten = sql[sql.index("CREATE TABLE IF NOT EXISTS public.fz_fahrten") :]
    spalten = spalten[: spalten.index(");")]
    assert "zweck" not in spalten.lower(), "fz_fahrten darf keine zweck-Spalte haben"
    assert "privat" not in spalten.lower()
    assert "projekt_id" in spalten and "arbeitsschein_id" in spalten
