"""v3.9.685 Montagezulage Phase 2 — manuelle Tages-Vergabe.

Entscheid Sebastian (05.07.2026, KV Metallgewerbe Abschn. VIII Pkt. 5): Die Montagezulage wird
MANUELL pro Mitarbeiter-Tag vergeben. Keine Auto-Erkennung Baustelle/Werkstatt/Fahrt.

Phase 1 (v3.9.671) hatte die Rechenfunktionen, aber kein Flag — der Report setzte deshalb
`baustellenStd = Summe ALLER Monatsstunden` und liess die Zulage damit auch auf Werkstatt- und
Fahrtzeit laufen. Das war zu hoch und stand als offener KV-Punkt im Handoff. Phase 2 ersetzt die
Naeherung durch die echte Vergabe — die Zahl im Report aendert sich dadurch, und zwar nach unten.

Der Lohnverrechner bleibt massgeblich; die App verbucht nichts automatisch.
"""
import json

from conftest import run_node_snippet, _extract_fn

KV = """const KV_RULES_FALLBACK={montagezulageStd:1.155,montagezulage:{2026:1.155,2027:1.178}};
const _num=function(v,d){var n=parseFloat(String(v==null?'':v).replace(',','.'));return (isNaN(n)||!isFinite(n))?d:n;};"""


def _harness(index_html, *extra):
    teile = [KV]
    for n in ("_kvMontagezulageSatz", "_kvMontagezulageTag", "_mzKey", "_kvMontagezulageMonat") + extra:
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck):
    snip = _harness(index_html) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


TAGE = {"2026-07-13": 8.0, "2026-07-14": 7.5, "2026-07-15": 9.0}


def _call(tage, flags, wid="w4"):
    return (
        f"_kvMontagezulageMonat({json.dumps(tage)},{json.dumps(flags)},"
        f"{json.dumps(wid)},KV_RULES_FALLBACK)"
    )


def test_ohne_vergabe_keine_zulage(node_exe, index_html):
    """Der Kern des Entscheids: nichts vergeben = nichts bezahlt. Keine Auto-Erkennung."""
    r = _eval(node_exe, index_html, _call(TAGE, {}))
    assert r == {"montageStd": 0, "montageTage": 0, "montageSum": 0}


def test_nur_geflaggte_tage_zaehlen(node_exe, index_html):
    flags = {"w4_2026-07-14": True}
    r = _eval(node_exe, index_html, _call(TAGE, flags))
    assert r["montageTage"] == 1
    assert r["montageStd"] == 7.5
    assert abs(r["montageSum"] - 7.5 * 1.155) < 0.001


def test_mehrere_tage_summieren(node_exe, index_html):
    flags = {"w4_2026-07-13": True, "w4_2026-07-15": True}
    r = _eval(node_exe, index_html, _call(TAGE, flags))
    assert r["montageTage"] == 2
    assert r["montageStd"] == 17.0
    assert abs(r["montageSum"] - 17.0 * 1.155) < 0.001


def test_flag_eines_anderen_monteurs_zaehlt_nicht(node_exe, index_html):
    """Der Schluessel enthaelt die worker_id — sonst wuerde eine Vergabe auf ALLE wirken."""
    flags = {"w9_2026-07-14": True}
    r = _eval(node_exe, index_html, _call(TAGE, flags, wid="w4"))
    assert r["montageTage"] == 0
    assert r["montageSum"] == 0


def test_satz_nach_jahr_des_tages(node_exe, index_html):
    """2027 hat einen anderen Satz (1,178). Massgeblich ist das Datum des TAGES, nicht heute."""
    tage = {"2026-12-30": 8.0, "2027-01-04": 8.0}
    flags = {"w4_2026-12-30": True, "w4_2027-01-04": True}
    r = _eval(node_exe, index_html, _call(tage, flags))
    assert r["montageTage"] == 2
    assert abs(r["montageSum"] - (8.0 * 1.155 + 8.0 * 1.178)) < 0.001


def test_tag_ohne_stunden_gibt_nichts(node_exe, index_html):
    """Ein geflaggter Tag ohne Stunden darf keine Zulage erzeugen — auch nicht bei Muell-Werten."""
    tage = {"2026-07-13": 0, "2026-07-14": -3, "2026-07-15": "abc"}
    flags = {"w4_2026-07-13": True, "w4_2026-07-14": True, "w4_2026-07-15": True}
    r = _eval(node_exe, index_html, _call(tage, flags))
    assert r == {"montageStd": 0, "montageTage": 0, "montageSum": 0}


def test_leere_eingaben(node_exe, index_html):
    for ausdruck in (
        "_kvMontagezulageMonat({},{},'w4',KV_RULES_FALLBACK)",
        "_kvMontagezulageMonat(null,null,'w4',KV_RULES_FALLBACK)",
    ):
        r = _eval(node_exe, index_html, ausdruck)
        assert r == {"montageStd": 0, "montageTage": 0, "montageSum": 0}


def test_mz_key_spiegelt_den_primaerschluessel(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        "[_mzKey('w4','2026-07-14'), _mzKey('w4','2026-07-14T00:00:00Z'), _mzKey(null,null)]",
    )
    assert r[0] == "w4_2026-07-14"
    assert r[1] == "w4_2026-07-14", "ein timestamptz aus der DB muss auf das Datum gekuerzt werden"
    assert r[2] == "_"


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_report_nutzt_nicht_mehr_alle_stunden(index_html):
    """Die alte Naeherung darf nicht zurueckkommen: baustellenStd ist jetzt 0."""
    assert "var z=_kvZulagenMonat(tageStd,0,kv);" in index_html
    assert "var z=_kvZulagenMonat(tageStd,byW[wid].baustelle,kv);" not in index_html
    assert "var mz=_kvMontagezulageMonat(byW[wid].days,mzFlags,wid,kv);" in index_html


def test_degradiert_ohne_tabelle(index_html):
    # montagezulage_tage fehlt (Run-Gate offen) -> Hinweis + Vergabe gesperrt, kein Crash.
    assert "async function _mzFetch(ym){" in index_html
    assert "return{ok:false,missing:true,flags:{}};" in index_html
    assert "Tabelle montagezulage_tage fehlt — sql/MONTAGEZULAGE_v1.sql ausführen" in index_html
    assert "disabled:mzMissing" in index_html


def test_schreibpfad_idempotent(index_html):
    # PK ist (worker_id,datum) -> Upsert darauf. Ohne on_conflict wuerde ein zweiter Klick knallen.
    assert "async function _mzSet(wid,datum,aktiv,von){" in index_html
    assert "'/montagezulage_tage?on_conflict=worker_id,datum'" in index_html
    assert "resolution=merge-duplicates" in index_html


def test_optimistischer_toggle_mit_rollback(index_html):
    """Ein Schalter, der umspringt, obwohl die DB nichts gespeichert hat, ist schlimmer als einer,
    der haengt — der Lohnverrechner bekaeme sonst eine Zahl, die niemand vergeben hat."""
    assert "const _mzToggle=async function(wid,datum){" in index_html
    assert "if(!ok){" in index_html
    assert "window.__toast('❌ Vergabe nicht gespeichert','error',4000);" in index_html


def test_kein_request_auf_verdacht(index_html):
    # Erst laden, wenn der Report aufgeklappt ist.
    assert "if(!open)return;/* erst laden, wenn der Report aufgeklappt ist" in index_html


def test_lohnverrechner_bleibt_massgeblich(index_html):
    assert "Für die Lohnabrechnung bleibt der Lohnverrechner maßgeblich — KEINE automatische Verbuchung." in index_html


def test_sql_gestaged(index_html):
    from pathlib import Path

    p = Path(__file__).parent.parent / "sql" / "MONTAGEZULAGE_v1.sql"
    assert p.exists()
    sql = p.read_text(encoding="utf-8")
    assert "Human-Run-Gate" in sql
    assert "CREATE TABLE IF NOT EXISTS public.montagezulage_tage" in sql
    assert "PRIMARY KEY (worker_id, datum)" in sql
    assert "is_staff()" in sql
