"""v3.9.689 — Flotte-Leerzustand, IMEI-Zuordnung und GPS-Geräte-Stammdaten.

Der Zustand vorher (live, 14.07.): 21 Fahrzeuge, **0 mit tracker_imei**. Der `trackerFz`-Filter
blendete alles ohne IMEI aus — die Fleet-Liste war leer, der Tab zeigte nur eine Karte.
Sebastian: „ich seh nur eine Karte, das ist zu wenig."

Und der eigentliche Blocker: es gab **nirgends** ein Eingabefeld für `tracker_imei`. Beim
Eintreffen der 13 Tracker hätte die Zuordnung nur per SQL gemacht werden können.

Getestet wird hier die pure Logik (Status/Sortierung/Validierung) plus die Guards, die verhindern,
dass die Sichtbarkeit oder die Degradation wieder verlorengehen.
"""
import json

from conftest import run_node_snippet, _extract_fn

STATUS_DEPS = """const TIME_SECOND=1000;const TIME_MINUTE=60*TIME_SECOND;const TIME_HOUR=60*TIME_MINUTE;const TIME_DAY=24*TIME_HOUR;"""


def _harness(index_html, *names):
    teile = [STATUS_DEPS]
    for n in names:
        if n == "FZ_ROLLOUT_RANK":
            import re

            m = re.search(r"^var FZ_ROLLOUT_RANK=\{.*?\};$", index_html, re.M)
            assert m, "FZ_ROLLOUT_RANK nicht gefunden"
            teile.append(m.group(0))
            continue
        fn = _extract_fn(index_html, n)
        assert fn, f"{n} nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + f"process.stdout.write(JSON.stringify({ausdruck}));"
    return json.loads(run_node_snippet(node_exe, snip))


STATUS_FNS = ("_flotteInactive", "_fzFaehrt", "_fzStatusSeit", "_fzStatus", "_fzHatTracker", "_fzFleetZeilen")
SORT_FNS = ("_fzHatTracker", "_fzFleetZeilen", "FZ_ROLLOUT_RANK", "_fzFleetSort",
            "_flotteInactive", "_fzFaehrt", "_fzStatusSeit", "_fzStatus")

NOW = 1_760_000_000_000  # fixer Bezugspunkt


# ── Vier Stufen ─────────────────────────────────────────────────────────────

def test_fahrzeug_ohne_imei_ist_sichtbar(node_exe, index_html):
    """Der Kern des Bugs: ohne IMEI war das Fahrzeug GAR NICHT in der Liste."""
    fz = [{"id": "f1", "kennzeichen": "TU-1", "tracker_imei": None}]
    r = _eval(node_exe, index_html, f"_fzFleetZeilen({json.dumps(fz)},{{}},{NOW})", *STATUS_FNS)
    assert len(r) == 1, "Fahrzeug ohne IMEI muss in der Liste stehen"
    assert r[0]["status"] == "kein_tracker"
    assert r[0]["hatTracker"] is False
    assert r[0]["p"] is None


def test_vier_stufen(node_exe, index_html):
    fz = [
        {"id": "a", "kennzeichen": "A", "tracker_imei": "111"},   # faehrt
        {"id": "b", "kennzeichen": "B", "tracker_imei": "222"},   # steht
        {"id": "c", "kennzeichen": "C", "tracker_imei": "333"},   # inaktiv (>24h)
        {"id": "d", "kennzeichen": "D", "tracker_imei": "444"},   # wartet (nie gemeldet)
        {"id": "e", "kennzeichen": "E", "tracker_imei": ""},      # kein Tracker
    ]
    byId = {
        "a": {"ts": "2026-07-14T10:00:00Z", "speed": 50, "ignition": True},
        "b": {"ts": "2026-07-14T10:00:00Z", "speed": 0, "ignition": False},
        "c": {"ts": "2026-07-10T10:00:00Z", "speed": 0, "ignition": False},
    }
    # ts von a/b auf "frisch" setzen: NOW - 1 min ; c auf NOW - 3 Tage
    js = (
        f"(function(){{var now={NOW};"
        f"var byId={{a:{{ts:new Date(now-60000).toISOString(),speed:50,ignition:true}},"
        f"b:{{ts:new Date(now-60000).toISOString(),speed:0,ignition:false}},"
        f"c:{{ts:new Date(now-3*TIME_DAY).toISOString(),speed:0,ignition:false}}}};"
        f"return _fzFleetZeilen({json.dumps(fz)},byId,now).map(function(x){{return x.status;}});}})()"
    )
    r = _eval(node_exe, index_html, js, *STATUS_FNS)
    # Vierstufig (Sebastian 14.07.): faehrt/steht kollabieren in der LISTE zu "aktiv" — kein
    # Zwischenzustand im Statuspunkt. Die Zuendung bleibt sichtbar, aber nur im Popup.
    assert r == ["aktiv", "aktiv", "inaktiv", "wartet", "kein_tracker"]


def test_24h_grenze(node_exe, index_html):
    fz = [{"id": "a", "kennzeichen": "A", "tracker_imei": "1"}]
    for delta, soll in ((23 * 3600 * 1000, "aktiv"), (25 * 3600 * 1000, "inaktiv")):
        js = (
            f"(function(){{var now={NOW};"
            f"var byId={{a:{{ts:new Date(now-{delta}).toISOString(),speed:0,ignition:false}}}};"
            f"return _fzFleetZeilen({json.dumps(fz)},byId,now)[0].status;}})()"
        )
        assert _eval(node_exe, index_html, js, *STATUS_FNS) == soll


# ── Sortierung ──────────────────────────────────────────────────────────────

def test_kein_tracker_ans_ende(node_exe, index_html):
    js = (
        "(function(){var z=["
        "{f:{id:'x',kennzeichen:'X'},status:'kein_tracker'},"
        "{f:{id:'w',kennzeichen:'W'},status:'wartet'},"
        "{f:{id:'a',kennzeichen:'A'},status:'aktiv'},"
        "{f:{id:'i',kennzeichen:'I'},status:'inaktiv'}];"
        "return _fzFleetSort(z,function(){return false;}).map(function(x){return x.status;});})()"
    )
    r = _eval(node_exe, index_html, js, "FZ_ROLLOUT_RANK", "_fzFleetSort")
    assert r == ["aktiv", "inaktiv", "wartet", "kein_tracker"]


def test_favoriten_stehen_ueber_allem(node_exe, index_html):
    """Auch ein Fahrzeug OHNE Tracker steht oben, wenn es Favorit ist — der Nutzer hat entschieden."""
    js = (
        "(function(){var z=["
        "{f:{id:'a',kennzeichen:'A'},status:'aktiv'},"
        "{f:{id:'x',kennzeichen:'X'},status:'kein_tracker'}];"
        "return _fzFleetSort(z,function(id){return id==='x';}).map(function(x){return x.f.id;});})()"
    )
    r = _eval(node_exe, index_html, js, "FZ_ROLLOUT_RANK", "_fzFleetSort")
    assert r == ["x", "a"]


# ── IMEI-Validierung ────────────────────────────────────────────────────────

def test_imei_clean(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        "[_fzImeiClean('  35 07 12 34 5678 901 '), _fzImeiClean('abc123'), _fzImeiClean(null)]",
        "_fzImeiClean",
    )
    assert r == ["350712345678901", "123", ""]


def test_imei_15_stellen_ist_nur_warnung(node_exe, index_html):
    """Abweichende Länge WARNT, blockt aber nicht — ein Rollout darf nicht daran scheitern, dass
    die App klüger sein will als der Mensch mit dem Gerät in der Hand."""
    r = _eval(node_exe, index_html, "_fzImeiPruef('350712345678901',[])", "_fzImeiClean", "_fzImeiPruef")
    assert r["ok"] is True and r["warn"] == "" and r["fehler"] == ""
    r2 = _eval(node_exe, index_html, "_fzImeiPruef('12345',[])", "_fzImeiClean", "_fzImeiPruef")
    assert r2["ok"] is True, "kurze IMEI darf NICHT blockiert werden"
    assert "5 statt 15" in r2["warn"]
    assert r2["fehler"] == ""


def test_duplikat_ist_harter_fehler(node_exe, index_html):
    """Zwei Fahrzeuge mit derselben IMEI würden sich gegenseitig die Positionen überschreiben —
    und niemand sähe es. Deshalb hart."""
    r = _eval(
        node_exe, index_html,
        "_fzImeiPruef('350712345678901',['350712345678901'])",
        "_fzImeiClean", "_fzImeiPruef",
    )
    assert r["ok"] is False
    assert "bereits einem anderen Fahrzeug" in r["fehler"]


def test_duplikat_erkennt_auch_formatierte_schreibweise(node_exe, index_html):
    r = _eval(
        node_exe, index_html,
        "_fzImeiPruef('350712345678901',['350 712 345 678 901'])",
        "_fzImeiClean", "_fzImeiPruef",
    )
    assert r["ok"] is False


def test_leere_imei(node_exe, index_html):
    r = _eval(node_exe, index_html, "_fzImeiPruef('',[])", "_fzImeiClean", "_fzImeiPruef")
    assert r["ok"] is False and "leer" in r["fehler"]


# ── Struktur-Guards ─────────────────────────────────────────────────────────

def test_liste_zeigt_alle_fahrzeuge(index_html):
    # Der trackerFz-Filter darf die Liste NICHT mehr speisen.
    assert "var fleet=_fzFleetZeilen(fahrzeuge,byId,_now2);" in index_html
    assert "var fleet=trackerFz.map(" not in index_html
    # Der Toggle zaehlt den ganzen Fuhrpark.
    assert "'Fahrzeuge ('+fahrzeuge.length+')'" in index_html


def test_zaehler_bleiben_gesamtbestand(index_html):
    """F4-Prinzip: der Filter aendert die Anzeige, nicht die Wahrheit."""
    assert "var _nOhne=fleet.filter(function(r){return r.status==='kein_tracker';}).length;" in index_html
    assert "(_nOhne?(' · '+_nOhne+' ohne Tracker'):'')" in index_html
    assert "var fleetView=_fq?fleet.filter(" in index_html


def test_zeile_ohne_tracker_zentriert_nichts(index_html):
    assert "onClick:function(){if(row.hatTracker)_focus(row);}" in index_html


def test_banner_unterscheidet_die_beiden_lagen(index_html):
    # "GPS-Pilot ausstehend" war irrefuehrend, solange schlicht keine IMEI zugeordnet ist.
    assert "Noch keine Tracker zugeordnet — IMEI im Fleet-Panel oder im Fahrzeug-Formular eintragen" in index_html
    assert "GPS-Pilot ausstehend" not in index_html


def test_imei_inline_mit_rls_check(index_html):
    assert "const _imeiSpeichern=async function(fid){" in index_html
    assert "_sbPatch('fahrzeuge',fid,{tracker_imei:pr.imei})" in index_html
    # v3.9.612-Muster: HTTP 200 + leeres Array = RLS hat stumm geblockt.
    assert "if(Array.isArray(r)&&r.length===0){" in index_html
    assert "IMEI NICHT gespeichert (keine Berechtigung)" in index_html


def test_spalten_sniff_degradation(index_html):
    """Die App wird deployt, BEVOR sql/FZ_TRACKER_v1.sql laeuft. Ein PATCH auf eine fehlende
    Spalte quittiert PostgREST mit 400 — der Nutzer saehe nur einen Fehler ohne Erklaerung."""
    assert (
        "const _trkSpalten=(fahrzeuge||[]).some(function(f){"
        "return f&&Object.prototype.hasOwnProperty.call(f,'tracker_typ');});"
    ) in index_html
    # Ohne Spalten: Felder gesperrt, IMEI trotzdem bedienbar.
    assert "(isVAdmin&&_trkSpalten)?React.createElement('select'" in index_html
    assert "sql/FZ_TRACKER_v1.sql ausführen. Die IMEI kann schon jetzt gesetzt werden." in index_html


def test_geraetetyp_im_popup(index_html):
    assert "if(f.tracker_typ){_trk=String(f.tracker_typ);" in index_html
    assert "_rich+_trkLine,{autoPan:false});" in index_html


def test_sql_gestaged_und_idempotent(index_html):
    from pathlib import Path

    p = Path(__file__).parent.parent / "sql" / "FZ_TRACKER_v1.sql"
    assert p.exists()
    sql = p.read_text(encoding="utf-8")
    assert "HUMAN-RUN-GATE" in sql
    for spalte in ("tracker_typ", "tracker_sim", "tracker_eingebaut"):
        assert f"ADD COLUMN IF NOT EXISTS {spalte}" in sql, f"{spalte} fehlt oder ist nicht idempotent"
    # Kein DROP, kein Policy-Umbau — die bestehende fahrzeuge_update-Policy deckt Spalten mit ab.
    assert "DROP TABLE" not in sql.upper()
    assert "CREATE POLICY" not in sql.upper()
