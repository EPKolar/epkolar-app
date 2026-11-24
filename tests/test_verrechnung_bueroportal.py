# -*- coding: utf-8 -*-
"""Buero-Portal > Verrechnung (GF 23.11.2026). Reine Rechenfunktionen in Node ausgefuehrt + SQL-/Andock-Riegel.

Logik: Eintrag verrechnet, wenn voll ODER Eintragsdatum <= verrechnet_bis. Ohne Satz: AS/Stoerung, die OFFA als
abgerechnet fuehrt, sind voll vorbelegt; ein gespeicherter Satz gewinnt immer (ueberschreibbar).
Jede Pruefung hat eine Umkehrprobe (mutierte Funktion -> anderes Ergebnis).
"""
import io
import json
import os
import re
import subprocess

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.join(HIER, "..")
HTML = os.path.join(WURZEL, "index.html")
FUNKTIONEN = ("_vrNorm", "_vrBezug", "_vrSatzWirksam", "_vrIstVerrechnet", "_vrKW", "_vrR",
              "_vrAuswerten", "_vrNachMonteur", "_vrKennzahlen")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(src, name):
    i = src.index("function " + name + "(")
    j = src.index("\nfunction ", i + 10)
    return src[i:j]


def _code(mutation=None):
    s = _src()
    c = "const TIME_DAY=24*60*60*1000;\n" + "\n".join(_fn(s, n) for n in FUNKTIONEN)
    if mutation:
        alt, neu = mutation
        assert c.count(alt) == 1, alt
        c = c.replace(alt, neu)
    return c


def _node(ausdruck, mutation=None):
    r = subprocess.run(["node", "-e", _code(mutation) + "\nconsole.log(JSON.stringify(" + ausdruck + "));"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


# Auftrag (Projekt p1) KW 42-48/2026, je Montag 8 h, zwei Monteure abwechselnd
MONTAGE = ["2026-10-12", "2026-10-19", "2026-10-26", "2026-11-02", "2026-11-09", "2026-11-16", "2026-11-23"]
E = [{"date": d, "project_id": "p1", "arbeitsschein_id": "", "hours": 8, "worker_id": "m1" if i % 2 == 0 else "m2"}
     for i, d in enumerate(MONTAGE)]
P = [{"id": "p1", "nr": "PA9", "name": "Halle"}]


def _auftrag(saetze, entries=E, scheine=None, mutation=None):
    a = _node("_vrAuswerten(%s,%s,%s,%s)" % (json.dumps(entries), json.dumps(P), json.dumps(scheine or []), json.dumps(saetze)),
              mutation)
    return a


def _satz(**k):
    d = {"bezug_typ": "projekt", "bezug_ref": "p1", "verrechnet_bis": None, "voll": False}
    d.update(k)
    return d


def test_split_kw42_48_bis_in_kw45():
    a = _auftrag([_satz(verrechnet_bis="2026-11-04")])[0]   # Mittwoch KW 45
    assert (a["summe"], a["verrechnet"], a["offen"]) == (56, 32, 24)
    assert _node("_vrKW('2026-10-12')") == "KW 42/2026" and _node("_vrKW('2026-11-23')") == "KW 48/2026"
    assert [w["kw"] for w in a["wochenListe"]] == ["KW %d/2026" % k for k in range(42, 49)]
    assert [w["offen"] for w in a["wochenListe"]] == [0, 0, 0, 0, 8, 8, 8]


def test_grenzfall_genau_am_datum():
    assert _auftrag([_satz(verrechnet_bis="2026-11-02")])[0]["verrechnet"] == 32
    assert _auftrag([_satz(verrechnet_bis="2026-11-01")])[0]["verrechnet"] == 24
    # Umkehrprobe: mit "<" statt "<=" faellt der Eintrag am Stichtag heraus
    mut = ("return !!(w.bis&&d&&d<=w.bis);", "return !!(w.bis&&d&&d<w.bis);")
    assert _auftrag([_satz(verrechnet_bis="2026-11-02")], mutation=mut)[0]["verrechnet"] == 24


def test_voll_und_nichts_gesetzt():
    assert _auftrag([_satz(voll=True)])[0]["offen"] == 0
    a = _auftrag([])[0]
    assert (a["verrechnet"], a["offen"]) == (0, 56)
    # Umkehrprobe: ohne voll-Zweig waere "voll" alles offen
    mut = ("if(w.voll===true)return true;", "")
    assert _auftrag([_satz(voll=True)], mutation=mut)[0]["offen"] == 56


def test_pro_monteur_summe():
    a = _auftrag([_satz(verrechnet_bis="2026-11-04")])
    m = {x["id"]: x for x in _node("_vrNachMonteur(%s)" % json.dumps(a))}
    # m1: 12.10, 26.10, 09.11, 23.11 -> 32 h, verrechnet 16; m2: 19.10, 02.11, 16.11 -> 24 h, verrechnet 16
    assert (m["m1"]["summe"], m["m1"]["verrechnet"], m["m1"]["offen"]) == (32, 16, 16)
    assert (m["m2"]["summe"], m["m2"]["verrechnet"], m["m2"]["offen"]) == (24, 16, 8)
    assert m["m1"]["summe"] + m["m2"]["summe"] == a[0]["summe"]
    k = _node("_vrKennzahlen(%s)" % json.dumps(a))
    assert k == {"summe": 56, "verrechnet": 32, "offen": 24, "offeneAuftraege": 1, "prozent": 57}


S_AS = [{"id": "s1", "nummer": "AS-100", "kundName": "Huber", "scheinart": "service", "scheinstatus": "abgerechnet"},
        {"id": "s2", "nummer": "ST-7", "kundName": "Maier", "scheinart": "stoerung", "scheinstatus": "in_bearbeitung"}]
E_AS = [{"date": "2026-11-10", "project_id": "", "arbeitsschein_id": "s1", "hours": 3, "worker_id": "m1"},
        {"date": "2026-11-11", "project_id": "", "arbeitsschein_id": "s2", "hours": 2, "worker_id": "m1"}]


def test_as_offa_abgerechnet_vorbelegt_aber_ueberschreibbar():
    a = {x["ref"]: x for x in _auftrag([], entries=E_AS, scheine=S_AS)}
    assert a["s1"]["typ"] == "as" and a["s1"]["w"]["vorbelegt"] is True and a["s1"]["offen"] == 0
    assert a["s2"]["typ"] == "stoerung" and a["s2"]["offen"] == 2
    # gespeicherter Satz (offen) gewinnt gegen OFFA
    b = {x["ref"]: x for x in _auftrag([{"bezug_typ": "as", "bezug_ref": "s1", "verrechnet_bis": None, "voll": False}],
                                       entries=E_AS, scheine=S_AS)}
    assert b["s1"]["offen"] == 3 and b["s1"]["w"]["vorbelegt"] is False
    # Umkehrprobe: Satz-Vorrang entfernt -> OFFA wuerde den gespeicherten Stand ueberstimmen
    mut = ("if(satz)return {voll:satz.voll===true", "if(false)return {voll:satz.voll===true")
    c = {x["ref"]: x for x in _auftrag([{"bezug_typ": "as", "bezug_ref": "s1", "verrechnet_bis": None, "voll": False}],
                                       entries=E_AS, scheine=S_AS, mutation=mut)}
    assert c["s1"]["offen"] == 0


def test_freitext_gruppe_und_leere_bezuege():
    e = [{"date": "2026-11-10", "project_id": "", "arbeitsschein_id": "", "taetigkeit": "Lager  aufraeumen", "hours": 1, "worker_id": "m1"},
         {"date": "2026-11-11", "project_id": "", "arbeitsschein_id": "", "taetigkeit": " lager aufraeumen", "hours": 2, "worker_id": "m2"}]
    a = _auftrag([], entries=e)
    assert len(a) == 1 and a[0]["typ"] == "freitext" and a[0]["ref"] == "lager aufraeumen" and a[0]["summe"] == 3


def test_sql_rls_nur_admin_buero_schreiben():
    sql = io.open(os.path.join(WURZEL, "sql", "VERRECHNUNG_v1_ENTWURF.sql"), encoding="utf-8").read()
    assert "enable row level security" in sql
    assert "revoke all on table public.verrechnung from public;" in sql
    assert "revoke all on table public.verrechnung from anon;" in sql
    # GF 23.11.: auch Lesen nur admin/buero ("Monteure duerfen das Buero-Portal nicht sehen")
    sel = re.findall(r"create policy verrechnung_select[^;]*;", sql)
    assert len(sel) == 1 and "public.current_user_role() in ('admin','buero')" in sel[0] and "using (true)" not in sel[0]
    assert "revoke all on table public.verrechnung from authenticated;" in sql, "TRUNCATE/TRIGGER aus den Standardrechten weg"
    schreib = re.findall(r"create policy verrechnung_(insert|update|delete)[^;]*;", sql)
    assert sorted(schreib) == ["delete", "insert", "update"]
    for pol in re.findall(r"create policy verrechnung_(?:insert|update|delete)[^;]*;", sql):
        assert "public.current_user_role() in ('admin','buero')" in pol
        assert "monteur" not in pol and "projektleiter" not in pol
    assert "as restrictive" in sql and "is_kiosk_role" in sql
    assert "cascade" not in sql.lower().replace("kein cascade", "")
    for f in ("PROBE", "RUECKNAHME"):
        assert os.path.exists(os.path.join(WURZEL, "sql", "VERRECHNUNG_v1_%s.sql" % f))


def test_app_schreibt_nur_verrechnung_und_dockt_an():
    s = _src()
    w = re.sub(r"/\*.*?\*/", "", _fn(s, "_vrSatzSchreiben"), flags=re.S)  # Kommentare zaehlen nicht
    assert '_sbUpsert("verrechnung",' in w
    for verboten in ("time_entries", "arbeitsscheine", "projects", "_juprowa", "SQ.push"):
        assert verboten not in w
    assert "var BX_TABS=[['projekte','','Projekte'],['zeit','','Zeiterfassung'],['verrechnung','','Verrechnung']," in s
    assert "_bxTab==='verrechnung' && React.createElement(VerrechnungView," in s
    v = _fn(s, "VerrechnungView")
    assert 'const darf=!!(curUser&&(curUser.role==="admin"||curUser.role==="buero"));' in v
    assert 'useState.call(void 0,"auftrag")' in v, "Standard-Ansicht Nach Auftrag"
