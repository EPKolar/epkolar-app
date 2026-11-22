"""v3.9.1096 - Fahrzeug-Datenfehler: km -999999 (fz5), doppelte km-Zeilen (fz1b), "12,5" -> 125 in addKm.

Gemessen 22.11.2026 (read-only, Projekt jiggujpruejkaomgxarp):
  * fz5 km_log trug {km:-999999, datum 2026-03-18} - kanonische addKm-Form {km,datum,note,by}. Am 18.03. war
    addKm nur `parseInt(kmVal)||0` ohne jede Pruefung (Pruefung "kann nicht negativ sein" kam erst am 20.03.).
    Heute fehlte noch: eine Obergrenze, und die Tank-Wege (QR/Batch, apiPatch tankLog_add) liessen -5 durch.
  * fz1b km_log: 05.07./14.07./15.07. je zwei IDENTISCHE {km,date}-Zeilen ohne id. Quelle: der km-Zweig in apiPatch
    (PUT fahrzeuge mit kmStand) haengt ohne kmLogId bei JEDER Wiederholung derselben Sendung eine Zeile an. addTank
    schickte {tankLog, kmStand} ohne kmLogId; fz_tanklog_add ist am Server nicht angelegt -> dieser Rueckfall ist
    der Normalweg. (Damals Base64-Tankfoto im selben PUT -> Rest-PATCH scheiterte -> Eintrag lief erneut.)
  * addKm las `parseInt(String(kmVal).replace(/[^\\d-]/g,""))` -> "12,5" = 125.

Die Proben laufen an den ECHTEN Ausdruecken aus index.html, die Umkehrproben an denselben Stellen im Altstand.
"""
import json
import os
import re
import subprocess

import pytest

from conftest import _extract_fn

ALT_REF = "5807fce"  # v3.9.1095, letzter Stand vor dem Fix


def _n(s):
    return s.replace("\r\n", "\n")


@pytest.fixture(scope="module")
def neu(index_html):
    return _n(index_html)


@pytest.fixture(scope="module")
def alt(repo_root):
    try:
        r = subprocess.run(["git", "-C", repo_root, "show", ALT_REF + ":index.html"],
                           capture_output=True, timeout=60)
    except Exception as e:  # pragma: no cover
        pytest.skip("git nicht verfuegbar: %s" % e)
    if r.returncode != 0:
        pytest.skip("Altstand %s nicht im Repo" % ALT_REF)
    return _n(r.stdout.decode("utf-8"))


def _node(node_exe, tmp_path, js, name="probe.js"):
    p = os.path.join(str(tmp_path), name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(js)
    r = subprocess.run([node_exe, p], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


def _fns(src, *names):
    out = []
    for n in names:
        f = _extract_fn(src, n)
        assert f, n
        out.append(f)
    return "\n".join(out) + "\n"


# ── 1. km-Pruefung ─────────────────────────────────────────────────────────

def test_kmpruef_werte(node_exe, neu, tmp_path):
    js = _fns(neu, "_fzZahl", "_ganzZahl", "_fzKmPruef", "_fzKmPlausibel") + (
        "const P=_fzKmPruef;console.log(JSON.stringify({"
        "neg:P('-999999'),komma:P('12,5'),tsd:P('12.345'),zuviel:P('2000001'),grenze:P('2000000'),"
        "leer:P(''),text:P('abc'),ok:P(' 184260 '),zahl:P(129453),"
        "pl:[_fzKmPlausibel(-999999),_fzKmPlausibel(0),_fzKmPlausibel(184260),_fzKmPlausibel(3000000),_fzKmPlausibel('x')]}));")
    r = _node(node_exe, tmp_path, js)
    assert r["neg"]["ok"] is False and "negativ" in r["neg"]["fehler"]
    assert r["komma"] == {"ok": True, "km": 12, "fehler": ""}, "12,5 darf nie 125 werden"
    assert r["tsd"]["km"] == 12345
    assert r["zuviel"]["ok"] is False and "2.000.000" in r["zuviel"]["fehler"]
    assert r["grenze"]["ok"] is True
    assert r["leer"]["ok"] is False and r["text"]["ok"] is False
    assert r["ok"]["km"] == 184260 and r["zahl"]["km"] == 129453
    assert r["pl"] == [False, True, True, False, False]


def test_addkm_liest_ueber_kmpruef(neu, alt):
    a = neu.index("const addKm=async(fzId)=>{")
    body = neu[a:neu.index("upd(fzId,f=>{", a)]
    assert "_fzKmPruef(kmVal)" in body
    assert 'replace(/[^\\d-]/g,"")' not in body
    assert 'replace(/[^\\d-]/g,"")' in alt[alt.index("const addKm=async(fzId)=>{"):][:600], "Altstand-Anker fehlt"


def test_umkehr_alter_addkm_parser(node_exe, tmp_path):
    """Die alten Leser: heutiger addKm machte aus "12,5" 125, der vom 18.03. nahm -999999 ohne Rueckfrage."""
    js = ("const kmVal='12,5';const a=parseInt(String(kmVal).replace(/[^\\d-]/g,\"\"),10);"
          "const b=parseInt('-999999')||0;console.log(JSON.stringify({a:a,b:b}));")
    r = _node(node_exe, tmp_path, js)
    assert r == {"a": 125, "b": -999999}


def test_alle_km_schreibwege_geprueft(neu):
    # QR-km, QR-Tank, Batch-Tank, Tank-Dialog
    a = neu.index("const qDoKm=async()=>{")
    assert "_fzKmPruef(km).ok" in neu[a:a + 1200]
    for anker, var in (("const qDoTank=()=>{", "_qKmP"), ("const batchSave=()=>{", "_bKmP")):
        a = neu.index(anker)
        seg = neu[a:a + 1600]
        assert var + "=String(" in seg and "_fzKmPruef(" in seg, anker
        assert "km:(" + var + "?" + var + ".km:0)||" in seg, anker
    assert "K=parseInt(rawK,10)||0;if(K>2000000){" in neu


# ── 2. apiPatch fahrzeuge PUT: km-Zweig idempotent, Werte geprueft ────────

def _put_block(src):
    a = src.index('  if(resource==="fahrzeuge"&&idOrSub&&method==="PUT"){')
    e = src.index("    body=d;\n  }", a) + len("    body=d;\n  }")
    return src[a:e]


def _addtank_diff(src):
    m = re.search(r'u=>\(\{_tankAtomar:\{op:"add",[^\n]*?\}\)(?=\);)', src)
    assert m, "addTank-Diff nicht gefunden"
    return m.group(0)


def _harness(src, sendungen_js):
    tank = _extract_fn(src, "_fzTankAtomar")
    assert tank
    return (
        "let DB={tank_log:'[]',km_log:'[]',km_stand:100000};const PATCHES=[];\n"
        "const _sbGet=async()=>[JSON.parse(JSON.stringify(DB))];\n"
        "const _sbPatch=async(t,id,p)=>{PATCHES.push(Object.keys(p));Object.assign(DB,p);};\n"
        "const _ymd=()=>'2026-11-22';const _fzTankRpc=async()=>({fehlt:true});const _fzTankHatDatei=()=>false;\n"
        "const _RLS_SILENT_DENIAL_LABELS={fahrzeuge:'x'};\n"
        "async " + tank + "\n"
        "async function blk(resource,idOrSub,method,body){\n" + _put_block(src) + "\n  return {weiter:body};}\n"
        "(async()=>{const rest=[];" + sendungen_js + "\n"
        "console.log(JSON.stringify({km:JSON.parse(DB.km_log),stand:DB.km_stand,rest:rest}));})();\n")


def _addtank_sendung(src):
    """Die echte Diff-Funktion von addTank -> Koerper; zweimal gesendet (= Wiederholung nach verlorener Antwort)."""
    diff = _addtank_diff(src)
    return ("const _eid='tkprobe1';const _r={kmDowngraded:false};const _tkNeu={id:_eid,km:100500,liter:40,preis:60,datum:'2026-11-22'};"
            "const _f=(" + diff + ");"
            "for(let i=0;i<2;i++){const b=_f({tankLog:[_tkNeu],kmStand:100500});const r=await blk('fahrzeuge','fzP','PUT',b);"
            "rest.push(r&&r.weiter?Object.keys(r.weiter):null);}")


def test_addtank_wiederholung_keine_doppelte_kmzeile(node_exe, neu, tmp_path):
    r = _node(node_exe, tmp_path, _harness(neu, _addtank_sendung(neu)))
    assert len(r["km"]) == 1, r["km"]
    assert r["km"][0]["id"] == "km_tkprobe1" and r["km"][0]["km"] == 100500
    for rest in r["rest"]:
        assert rest is not None and "kmLogId" not in rest and "km_log_id" not in rest, \
            "kmLogId ist keine Spalte und darf nicht in den Rest-PATCH"
        assert "tankLog" in rest, "tankLog bleibt im Rest-PATCH (Schreibformat unveraendert)"


def test_umkehr_alt_addtank_wiederholung_doppelt(node_exe, alt, tmp_path):
    r = _node(node_exe, tmp_path, _harness(alt, _addtank_sendung(alt)), "alt.js")
    assert len(r["km"]) == 2, "Umkehrprobe: der Altstand haengt bei der Wiederholung eine zweite Zeile an"
    assert r["km"][0] == r["km"][1] and "id" not in r["km"][0], "exakt die fz1b-Form {km,date} ohne id"


def _tankadd_sendung(km):
    return ("const e={id:'tkq1',datum:'2026-11-22',liter:40,preis:60,km:" + km + "};"
            "await blk('fahrzeuge','fzP','PUT',{tankLog_add:e,kmStand:e.km});")


@pytest.mark.parametrize("km", ["-5", "-999999", "3000000"])
def test_tanklog_add_unplausibler_km_nicht_ins_kmlog(node_exe, neu, tmp_path, km):
    r = _node(node_exe, tmp_path, _harness(neu, _tankadd_sendung(km)))
    assert r["km"] == [] and r["stand"] == 100000


def test_umkehr_alt_tanklog_add_nahm_minus(node_exe, alt, tmp_path):
    r = _node(node_exe, tmp_path, _harness(alt, _tankadd_sendung("-5")), "alt2.js")
    assert len(r["km"]) == 1 and r["km"][0]["km"] == -5


def test_kmstand_zweig_obergrenze(node_exe, neu, alt, tmp_path):
    s = "await blk('fahrzeuge','fzP','PUT',{kmStand:3000000});"
    r = _node(node_exe, tmp_path, _harness(neu, s))
    assert r["km"] == [] and r["stand"] == 100000
    r = _node(node_exe, tmp_path, _harness(alt, s), "alt3.js")
    assert r["stand"] == 3000000, "Umkehrprobe: der Altstand setzte 3.000.000 km"


def test_tanklog_add_gueltig_unveraendert(node_exe, neu, tmp_path):
    """Normalfall: QR/Batch-Tankung legt wie bisher genau eine km-Zeile km_<tankId> an, zweimal gesendet = eine."""
    s = _tankadd_sendung("100700") + "await blk('fahrzeuge','fzP','PUT',{tankLog_add:e,kmStand:e.km});"
    r = _node(node_exe, tmp_path, _harness(neu, s))
    assert r["km"] == [{"id": "km_tkq1", "km": 100700, "date": "2026-11-22"}]
    assert r["stand"] == 100700


# ── 3. Anzeige: unplausible km ignoriert, mit Hinweis ─────────────────────

def test_tankstats_ignoriert_unplausiblen_km(node_exe, neu, alt, tmp_path):
    log = [{"liter": 40, "km": 100000, "datum": "2026-10-01"}, {"liter": 40, "km": 100500, "datum": "2026-10-10"},
           {"liter": 40, "km": 3000000, "datum": "2026-10-20"}, {"liter": 40, "km": -999999, "datum": "2026-10-25"}]
    call = "console.log(JSON.stringify(_fzTankStats({tankLog:" + json.dumps(log) + "},Date.parse('2026-11-22'))));"
    names = ("_fzZahl", "_fzDatumTeile", "_fzTagKey", "_fzTageBis", "_fzTankStats")
    r = _node(node_exe, tmp_path, _fns(neu, *names) + call)
    assert r["kmUnplausibel"] == 2 and r["ohneKm"] == 0
    assert abs(r["l100"] - 8.0) < 1e-9 and r["strecke"] == 500
    ra = _node(node_exe, tmp_path, _fns(alt, *names) + call, "alt4.js")
    assert ra["l100"] < 1, "Umkehrprobe: der Altstand rechnete 3.000.000 km als Strecke"


def test_anzeige_hinweise_vorhanden(neu):
    assert "⚠️ unplausibel, ignoriert" in neu and "_fzKmPlausibel(k.km)?null:" in neu
    assert "Tankung(en) mit unplausiblem km-Stand ignoriert" in neu
    assert "km-Stand (unter 0 oder über 2.000.000) und werden im Verbrauch ignoriert." in neu


def test_akte_unplausibler_km_ohne_kmwert(node_exe, neu, tmp_path):
    f = {"kmLog": [{"km": -999999, "datum": "2026-03-18", "note": "", "by": "X"},
                   {"km": 184260, "datum": "2026-11-11", "note": "", "by": "Y"}]}
    js = _fns(neu, "_fzZahl", "_fzDatumTeile", "_fzTagKey", "_fzTageBis", "_fzAkte") + "console.log(JSON.stringify(_fzAkte(" + json.dumps(f) + ")));"
    r = _node(node_exe, tmp_path, js)
    kmz = {z["datum"]: z for z in r if z["art"] == "km-Stand"}
    assert kmz["2026-03-18"]["km"] is None and "unplausibler km-Stand" in kmz["2026-03-18"]["text"]
    assert kmz["2026-11-11"]["km"] == 184260


# ── 4. SQL-Entwuerfe ──────────────────────────────────────────────────────

@pytest.mark.parametrize("stamm", ["FZ_KM_LOG_BEREINIGUNG_v1096", "FZ_KM_LOG_DUPLIKATE_v1096"])
def test_sql_dateien(repo_root, stamm):
    for teil in ("PROBE", "ENTWURF", "RUECKNAHME"):
        p = os.path.join(repo_root, "sql", stamm + "_" + teil + ".sql")
        assert os.path.exists(p), p
        s = open(p, encoding="utf-8").read()
        assert "cascade" not in re.sub(r"--[^\n]*", "", s).lower(), p
        if teil == "PROBE":
            assert re.search(r"(?im)^\s*rollback;\s*$", s) and not re.search(r"(?im)^\s*commit;", s), p
