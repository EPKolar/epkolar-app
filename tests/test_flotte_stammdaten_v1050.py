"""v1050 Fahrzeug-Stammdaten (Leasing, Versicherung, Reifen, Service-km) + Fuehrerscheinkontrolle.

Schema live seit 19.11.2026 (fahrzeuge +11 Spalten, Tabelle fz_fs_kontrollen). Die DB nimmt in date-Spalten
KEIN '' und in Zahlspalten weder NaN noch '' noch negative Werte (Service-Intervall > 0).

Verhaltenstests: die ECHTEN Funktionen werden aus index.html ausgeschnitten und in Node ausgefuehrt.
Jede Regel hat eine Umkehrprobe ('' in einer date-Spalte MUSS auffallen, null darf nie 1970 werden).
"""
import json
import re

from conftest import run_node_snippet, _extract_fn
from test_flotte_ausbau_v1049 import _UI_STUBS, _node_datei, _texte

TZ = "process.env.TZ='Europe/Vienna';"
VARS1 = ("FZ_FRIST_RANG", "FZ_FRIST_ART", "FZ_FRIST_TXT", "FS_KTR_ERGEBNIS", "FS_KTR_RANG", "FS_KTR_TXT",
         "FZ_STAMM_FINANZ", "FZ_STAMM_REIFEN", "FZ_REIFEN_TXT")
BASIS = ("_fzZahl", "_fzDatumTeile", "_fzTagKey", "_fzTageBis", "_fzTageTxt", "_fzDatumAnz")
STAMM = ("_fzStammWert", "_fzStammAnzeige", "_fzStammPruef", "_fzStammBody", "_fzStammSpalten")
FS = ("_fsPlusMonate", "_fsKtrSortiert", "_fsKtrStatus", "_fsKtrFaellig", "_fsKtrNeu")
NOW = "new Date(2026,10,19,10,0,0).getTime()"  # Do 19.11.2026 10:00 Wiener Zeit


def _zeit(index_html):
    """Die echten TIME_*-Konstanten (falls ein Rechner sie benutzt) statt hart kodierter Millisekunden."""
    return "\n".join(m.group(0).rstrip("\r") for m in re.finditer(r"^const TIME_\w+=[^;\n]*;", index_html, re.M))


def _harness(index_html, *names):
    teile = [TZ, _zeit(index_html)]
    for n in VARS1:
        m = re.search(r"^var " + n + r"=[\[{].*?[\]}];\r?$", index_html, re.M)
        assert m, n + " nicht gefunden"
        teile.append(m.group(0).rstrip("\r"))
    m = re.search(r"^var FZ_STAMM_FELDER=\{.*?^\};", index_html, re.M | re.S)
    assert m, "FZ_STAMM_FELDER"
    teile.append(m.group(0).replace("\r\n", "\n"))
    for n in BASIS + names:
        fn = _extract_fn(index_html, n)
        assert fn, n + " nicht gefunden"
        teile.append(fn)
    return "\n".join(teile) + "\n"


def _eval(node_exe, index_html, ausdruck, *names):
    snip = _harness(index_html, *names) + "process.stdout.write(JSON.stringify(" + ausdruck + "));"
    return json.loads(run_node_snippet(node_exe, snip))


def _stamm_block(index_html):
    return index_html[index_html.index("//@FLOTTE-STAMM-START"):index_html.index("//@FLOTTE-STAMM-END")]


# ── Abbildung Eingabe -> Spaltenwert ─────────────────────────────────────────

def test_stammwert_leer_ist_null_und_zahlen_geparst(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{d0:_fzStammWert('leasing_ende',''),d1:_fzStammWert('leasing_ende','2027-03-31'),"
              "d2:_fzStammWert('versicherung_ablauf','31.3.2027'),d3:_fzStammWert('leasing_ende','2027-02-30'),"
              "d4:_fzStammWert('leasing_ende',null),d5:_fzStammWert('leasing_ende','  '),"
              "g0:_fzStammWert('leasing_rate',''),g1:_fzStammWert('leasing_rate','450,50'),g2:_fzStammWert('versicherung_praemie','1.234,5'),"
              "g3:_fzStammWert('leasing_rate','abc'),g4:_fzStammWert('leasing_rate','-3'),g5:_fzStammWert('leasing_rate',NaN),g6:_fzStammWert('leasing_rate',450),"
              "i0:_fzStammWert('naechst_service_km',''),i1:_fzStammWert('naechst_service_km','15.000'),i2:_fzStammWert('naechst_service_km','-5'),"
              "i3:_fzStammWert('service_km_intervall','0'),i4:_fzStammWert('service_km_intervall','15000'),i5:_fzStammWert('leasing_km_limit','12,5'),"
              "i6:_fzStammWert('naechst_service_km','0'),"
              "w0:_fzStammWert('reifen_saison','winter'),w1:_fzStammWert('reifen_saison','Sommer'),w2:_fzStammWert('reifen_saison',''),"
              "t0:_fzStammWert('reifen_lager','  Reifen Huber '),t1:_fzStammWert('leasing_geber','data:image/png;base64,AAA'),"
              "x:_fzStammWert('tracker_imei','1')}",
              *STAMM)
    assert r["d0"] == {"ok": True, "wert": None, "fehler": ""}, "leeres Datum = null, nie ''"
    assert r["d4"]["wert"] is None and r["d5"]["wert"] is None
    assert r["d1"]["wert"] == "2027-03-31" and r["d2"]["wert"] == "2027-03-31"
    assert r["d3"]["ok"] is False and r["d3"]["wert"] is None, "31.02. ist kein Datum"
    assert r["g0"]["wert"] is None and r["g1"]["wert"] == 450.5 and r["g2"]["wert"] == 1234.5 and r["g6"]["wert"] == 450
    for k in ("g3", "g4", "g5"):
        assert r[k]["ok"] is False and r[k]["wert"] is None, k
    assert r["i0"]["wert"] is None and r["i1"]["wert"] == 15000, "15.000 km = fuenfzehntausend"
    assert r["i2"]["ok"] is False and r["i3"]["ok"] is False and r["i5"]["ok"] is False
    assert r["i3"]["fehler"] == "muss größer als 0 sein", "CHECK service_km_intervall > 0"
    assert r["i4"]["wert"] == 15000 and r["i6"]["wert"] == 0
    assert r["w0"]["wert"] == "winter" and r["w1"]["ok"] is False and r["w2"]["wert"] is None
    assert r["t0"]["wert"] == "Reifen Huber"
    assert r["t1"]["ok"] is False, "keine Datei in einer Stammdaten-Zeile"
    assert r["x"]["ok"] is False


def test_stammbody_nur_geaenderte_spalten_ohne_leerstring(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "(function(){var f={id:'F1',leasing_ende:'2027-01-01',leasing_rate:450,naechst_service_km:null,reifen_saison:'sommer',kennzeichen:'TU-1'};"
              "var a=_fzStammBody(f,{leasing_ende:'',leasing_rate:'450,00',naechst_service_km:'60.000',reifen_saison:'sommer',versicherung_praemie:''});"
              "var b=_fzStammBody(f,{leasing_rate:'-1',service_km_intervall:'0',leasing_ende:'2027-13-01'});"
              "var c=_fzStammBody(f,{leasing_ende:'2027-01-01',leasing_rate:'450'});"
              "var d=_fzStammBody(f,{leasing_ende:'',naechst_service_km:'5000'},['naechst_service_km']);"
              "return {a:a,b:b,c:c,d:d,pa:_fzStammPruef(a.body)};})()",
              *STAMM)
    a = r["a"]
    assert a["body"] == {"leasing_ende": None, "naechst_service_km": 60000}, a
    assert a["fehler"] == {} and a["anzahl"] == 2 and r["pa"] == []
    assert "" not in a["body"].values()
    b = r["b"]
    assert b["body"] == {} and set(b["fehler"]) == {"leasing_rate", "service_km_intervall", "leasing_ende"}
    assert r["c"]["body"] == {} and r["c"]["anzahl"] == 0, "unveraendert = kein PUT-Rumpf"
    assert r["d"]["body"] == {"naechst_service_km": 5000}, "nur die erlaubten Felder (Fahrer: Reifen/Service)"


def test_umkehrprobe_riegel_faengt_leerstring_und_nan(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{leer:_fzStammPruef({leasing_ende:''}),nan:_fzStammPruef({leasing_rate:NaN}),null0:_fzStammPruef({service_km_intervall:0}),"
              "neg:_fzStammPruef({naechst_service_km:-1}),bruch:_fzStammPruef({leasing_km_limit:1.5}),txtzahl:_fzStammPruef({leasing_rate:'450'}),"
              "wahl:_fzStammPruef({reifen_saison:'Sommer'}),fremd:_fzStammPruef({tracker_imei:'1'}),datei:_fzStammPruef({leasing_geber:'data:x'}),"
              "leertext:_fzStammPruef({reifen_lager:''}),"
              "gut:_fzStammPruef({leasing_ende:null,leasing_rate:0,naechst_service_km:0,service_km_intervall:15000,versicherung_ablauf:'2027-05-01',reifen_saison:'ganzjahr',reifen_lager:'Huber'})}",
              *STAMM)
    for k in ("leer", "nan", "null0", "neg", "bruch", "txtzahl", "wahl", "fremd", "datei", "leertext"):
        assert r[k], "Umkehrprobe: " + k + " muss vom Riegel erkannt werden"
    assert "leasing_ende" in r["leer"][0]
    assert r["gut"] == []


def test_spalten_sniff(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "[_fzStammSpalten([]),_fzStammSpalten(null),_fzStammSpalten([{kennzeichen:'A'}]),"
              "_fzStammSpalten([{kennzeichen:'A'},{leasing_ende:null,naechst_service_km:null}])]", *STAMM)
    assert r == [False, False, False, True]


def test_anzeige_nie_null_oder_nan(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "[_fzStammAnzeige('leasing_rate',null),_fzStammAnzeige('leasing_rate',450.5),_fzStammAnzeige('leasing_ende',null),"
              "_fzStammAnzeige('naechst_service_km',60000),_fzStammAnzeige('leasing_ende','2027-01-01'),_fzStammAnzeige('reifen_lager',undefined)]",
              *STAMM)
    assert r == ["", "450,5", "", "60000", "2027-01-01", ""]


# ── Fristen aus den Stammdaten ───────────────────────────────────────────────

def _fristen(node_exe, index_html, fz):
    return _eval(node_exe, index_html,
                 "_fzFristen(" + json.dumps(fz) + "," + NOW + ",[])",
                 "_fzPickerlStufe", "_fzTerminErledigt", "_fzServiceStats", "_fzFristen")


def test_fristen_leasing_versicherung(node_exe, index_html):
    fz = [{"id": "a", "kennzeichen": "TU-1", "pickerl": "2027-06-01", "naechstService": "2027-06-01",
           "leasing_ende": "2027-01-18", "leasing_geber": "VW Leasing", "versicherung_ablauf": "2026-12-09", "versicherung_polizze": "P-1"},
          {"id": "b", "kennzeichen": "TU-2", "pickerl": "2027-06-01", "naechstService": "2027-06-01",
           "leasing_ende": "2027-03-19", "versicherung_ablauf": "2026-12-29"},
          {"id": "c", "kennzeichen": "TU-3", "pickerl": "2027-06-01", "naechstService": "2027-06-01",
           "leasing_ende": "2026-11-18", "versicherung_ablauf": "quatsch"}]
    r = _fristen(node_exe, index_html, fz)
    by = {(x["kennzeichen"], x["art"]): x for x in r}
    assert by[("TU-1", "leasing")]["stufe"] == "bald" and by[("TU-1", "leasing")]["tage"] == 60
    assert by[("TU-1", "leasing")]["hinweis"] == "VW Leasing"
    assert by[("TU-2", "leasing")]["stufe"] == "ok", "120 Tage > 90 Tage Vorlauf"
    assert by[("TU-3", "leasing")]["stufe"] == "ueberfaellig"
    assert by[("TU-1", "versicherung")]["stufe"] == "bald" and by[("TU-1", "versicherung")]["hinweis"] == "Polizze P-1"
    assert by[("TU-2", "versicherung")]["stufe"] == "ok", "40 Tage > 30 Tage Vorlauf"
    assert by[("TU-3", "versicherung")]["stufe"] == "ungueltig"
    assert by[("TU-1", "leasing")]["artLabel"] == "Leasing-Ende"


def test_fristen_ohne_stammdaten_keine_neuen_eintraege(node_exe, index_html):
    r = _fristen(node_exe, index_html, [{"id": "a", "kennzeichen": "TU-1", "pickerl": "2027-06-01", "naechstService": "2027-06-01",
                                          "kmStand": 50000, "leasing_ende": None, "versicherung_ablauf": "", "naechst_service_km": None,
                                          "service_km_intervall": None}])
    assert sorted(x["art"] for x in r) == ["pickerl", "service"], "nicht erfasst = keine Zeile (kein erfundenes 'fehlt')"


def test_fristen_service_km(node_exe, index_html):
    base = {"pickerl": "2027-06-01", "naechstService": "2027-06-01"}
    fz = [dict(base, id="a", kennzeichen="K-BALD", kmStand=49200, naechst_service_km=50000),
          dict(base, id="b", kennzeichen="K-OK", kmStand=48000, naechst_service_km=50000),
          dict(base, id="c", kennzeichen="K-UEB", kmStand=50100, naechst_service_km=50000),
          dict(base, id="d", kennzeichen="K-RAND", kmStand=49000, naechst_service_km=50000),
          dict(base, id="e", kennzeichen="K-KMLOS", kmStand=0, naechst_service_km=50000),
          dict(base, id="f", kennzeichen="K-ABGEL", kmStand=54500, naechst_service_km=None, service_km_intervall=15000,
               serviceheft=[{"datum": "2026-01-10", "km": 40000}, {"datum": "2025-01-10", "km": 25000}]),
          dict(base, id="g", kennzeichen="K-NULL", kmStand=54500, naechst_service_km=None, service_km_intervall=15000)]
    r = _fristen(node_exe, index_html, fz)
    km = {x["kennzeichen"]: x for x in r if x["art"] == "service_km"}
    assert km["K-BALD"]["stufe"] == "bald" and km["K-BALD"]["kmRest"] == 800
    assert km["K-BALD"]["hinweis"] == "noch 800 km bis 50.000 km"
    assert km["K-OK"]["stufe"] == "ok"
    assert km["K-RAND"]["stufe"] == "bald", "genau 1000 km Rest = Warnung"
    assert km["K-UEB"]["stufe"] == "ueberfaellig" and "100 km über 50.000 km" in km["K-UEB"]["hinweis"]
    assert km["K-KMLOS"]["stufe"] == "fehlt" and "km-Stand nicht erfasst" in km["K-KMLOS"]["hinweis"]
    assert km["K-ABGEL"]["stufe"] == "bald" and km["K-ABGEL"]["kmRest"] == 500, "letztes Service 40.000 + 15.000"
    assert "letztes Service + Intervall" in km["K-ABGEL"]["hinweis"]
    assert "K-NULL" not in km, "ohne Serviceheft-km kein abgeleiteter Wert"
    alle = json.dumps(r, ensure_ascii=False)
    assert "NaN" not in alle.replace("null", "") and "1970" not in alle


def test_fixkosten_getrennt_und_ohne_erfundene_null(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "(function(){var o=function(x){return {l:isNaN(x.leasing)?'NaN':x.leasing,v:isNaN(x.versicherung)?'NaN':x.versicherung,s:isNaN(x.summe)?'NaN':x.summe};};"
              "return [o(_fzFixkosten({})),o(_fzFixkosten({leasing_rate:null,versicherung_praemie:''})),"
              "o(_fzFixkosten({leasing_rate:450,versicherung_praemie:1200})),o(_fzFixkosten({leasing_rate:'0'})),o(_fzFixkosten(null))];})()",
              "_fzFixkosten")
    assert r[0] == {"l": "NaN", "v": "NaN", "s": "NaN"}, "Umkehrprobe Number(null)===0: nichts erfasst = keine 0"
    assert r[1] == {"l": "NaN", "v": "NaN", "s": "NaN"}
    assert r[2] == {"l": 450, "v": 100, "s": 550}, "Versicherung = Jahrespraemie / 12"
    assert r[3] == {"l": 0, "v": "NaN", "s": 0}
    assert r[4] == {"l": "NaN", "v": "NaN", "s": "NaN"}


# ── Fuehrerscheinkontrolle ──────────────────────────────────────────────────

def test_plus_monate_klemmt_monatsende(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "[_fsPlusMonate('2026-08-31',6),_fsPlusMonate('2027-08-31',6),_fsPlusMonate('2026-05-19',6),_fsPlusMonate('2026-11-30',3),"
              "_fsPlusMonate(null,6),_fsPlusMonate('',6),_fsPlusMonate('1970-01-01',6)]", *FS)
    assert r == ["2027-02-28", "2028-02-29", "2026-11-19", "2027-02-28", "", "", ""]


def test_fs_status_regeln(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "(function(){var n=" + NOW + ";var s=function(rows){var x=_fsKtrStatus(rows,n);return {st:x.stufe,hw:x.hinweis,f:x.faelligAm};};return {"
              "leer:s([]),nulldat:s([{geprueft_am:null},{geprueft_am:''}]),"
              "grenze:s([{geprueft_am:'2026-05-19',ergebnis:'ok'}]),alt:s([{geprueft_am:'2026-05-18',ergebnis:'ok'}]),"
              "bald:s([{geprueft_am:'2026-10-01',ergebnis:'ok',gueltig_bis:'2026-12-19'}]),"
              "frei:s([{geprueft_am:'2026-10-01',ergebnis:'ok',gueltig_bis:'2027-01-19'}]),"
              "ab:s([{geprueft_am:'2026-10-01',ergebnis:'ok',gueltig_bis:'2026-11-18'}]),"
              "entz:s([{geprueft_am:'2026-10-01',ergebnis:'entzogen'}]),mangel:s([{geprueft_am:'2026-10-01',ergebnis:'mangel'}]),"
              "neu:s([{geprueft_am:'2026-01-01',ergebnis:'entzogen'},{geprueft_am:'2026-10-01',ergebnis:'ok'}]),"
              "gleich:s([{geprueft_am:'2026-10-01',ergebnis:'ok',created_at:'2026-10-01T08:00:00Z'},{geprueft_am:'2026-10-01',ergebnis:'mangel',created_at:'2026-10-01T09:00:00Z'}]),"
              "mehr:s([{geprueft_am:'2026-04-01',ergebnis:'mangel',gueltig_bis:'2026-11-01'}])};})()", *FS)
    assert r["leer"]["st"] == "fehlt" and r["nulldat"]["st"] == "fehlt"
    assert "1970" not in json.dumps(r), "Umkehrprobe: null darf nie 1.1.1970 werden"
    assert r["grenze"]["st"] == "ok" and r["grenze"]["f"] == "2026-11-19", "genau 6 Monate = heute noch gueltig"
    assert r["alt"]["st"] == "alt" and "älter als 6 Monate" in r["alt"]["hw"]
    assert r["bald"]["st"] == "bald", "gueltig_bis in 30 Tagen"
    assert r["frei"]["st"] == "ok", "61 Tage = ausserhalb der 60-Tage-Warnung"
    assert r["ab"]["st"] == "abgelaufen"
    assert r["entz"]["st"] == "entzogen" and r["mangel"]["st"] == "mangel"
    assert r["neu"]["st"] == "ok", "die NEUESTE Kontrolle zaehlt"
    assert r["gleich"]["st"] == "mangel", "gleicher Tag: die spaeter angelegte zaehlt"
    assert r["mehr"]["st"] == "abgelaufen" and "älter als 6 Monate" in r["mehr"]["hw"] and "Mangel" in r["mehr"]["hw"]


def test_fs_status_tagesgrenze_lokal(node_exe, index_html):
    # 00:30 Ortszeit am 20.11. ist in UTC noch der 19.11. - die Faelligkeit muss nach LOKALEM Tag kippen
    r = _eval(node_exe, index_html,
              "[_fsKtrStatus([{geprueft_am:'2026-05-20'}],new Date(2026,10,20,0,30).getTime()).stufe,"
              "_fsKtrStatus([{geprueft_am:'2026-05-19'}],new Date(2026,10,20,0,30).getTime()).stufe,"
              "_fsKtrStatus([{geprueft_am:'2026-05-19'}],new Date(2026,10,19,23,30).getTime()).stufe]", *FS)
    assert r == ["ok", "alt", "ok"]


def test_fs_faellig_auswahl(node_exe, index_html):
    ma = [{"id": "m1", "n": "Auer", "vorname": "Anna"}, {"id": "m2", "n": "Berger"}, {"id": "m3", "n": "Czerny"},
          {"id": "m4", "n": "Dorn", "austritt": "2026-01-31"}, {"id": "m5", "n": "Eder"}, {"id": "m6", "n": "Fink"}]
    fz = [{"id": "f1", "fahrer": "m1"}, {"id": "f4", "fahrer": "m4"}, {"id": "f5", "fahrer": "m5", "status": "stillgelegt"},
          {"id": "f6", "fahrer": "m6", "typ": "Anhänger"}]
    rows = [{"monteur_id": "m2", "geprueft_am": "2026-10-01", "ergebnis": "ok"}]
    r = _eval(node_exe, index_html, "_fsKtrFaellig(" + json.dumps(ma) + "," + json.dumps(fz) + "," + json.dumps(rows) + "," + NOW + ")", *FS)
    ids = [x["mid"] for x in r]
    assert ids == ["m1", "m2"], ids
    assert r[0]["stufe"] == "fehlt" and r[0]["name"] == "Auer Anna" and r[0]["fahrer"] is True
    assert r[1]["stufe"] == "ok" and r[1]["fahrer"] is False


def test_fs_neu_normalisiert(node_exe, index_html):
    r = _eval(node_exe, index_html,
              "{a:_fsKtrNeu({geprueft_am:'2026-11-19',ergebnis:'ok',klassen:' B,BE ',gueltig_bis:'',pruefer:'Büro',notiz:''},'m1','id1'),"
              "b:_fsKtrNeu({geprueft_am:'',ergebnis:'xyz',gueltig_bis:'2027-02-30',notiz:'data:image/png;base64,AA'},'','id2'),"
              "c:_fsKtrNeu({geprueft_am:'2026-11-19'},'m1','id3')}", *FS)
    a = r["a"]
    assert a["ok"] is True
    assert a["row"] == {"id": "id1", "monteur_id": "m1", "geprueft_am": "2026-11-19", "ergebnis": "ok", "klassen": "B,BE",
                        "gueltig_bis": None, "pruefer": "Büro", "notiz": None}
    assert "" not in a["row"].values(), "date-Spalte gueltig_bis nimmt kein ''"
    assert r["b"]["ok"] is False and r["b"]["row"] is None
    assert set(r["b"]["fehler"]) == {"geprueft_am", "ergebnis", "gueltig_bis", "monteur_id", "notiz"}
    assert r["c"]["row"]["ergebnis"] == "ok" and r["c"]["row"]["gueltig_bis"] is None


def test_fs_zeile_ueberlebt_mapbody(node_exe, index_html):
    """Der generische Warteschlangen-Weg schickt _mapBody(body) - kein Spaltenname darf umbenannt werden."""
    snip = (_extract_fn(index_html, "_toSnake") + "\n" + _extract_fn(index_html, "_mapBody") + "\n"
            "var row={id:'x',monteur_id:'m1',geprueft_am:'2026-11-19',ergebnis:'ok',klassen:'B',gueltig_bis:null,pruefer:'P',notiz:null,nachweis_path:'sbpriv:epkolar-docs/a.jpg',created_at:'t'};"
            "var fz={leasing_geber:'A',leasing_ende:null,leasing_rate:450,leasing_km_limit:1,versicherung_polizze:'p',versicherung_ablauf:null,versicherung_praemie:1,reifen_saison:'winter',reifen_lager:'x',service_km_intervall:15000,naechst_service_km:1};"
            "process.stdout.write(JSON.stringify([_mapBody(row),row,_mapBody(fz),fz]));")
    r = json.loads(run_node_snippet(node_exe, snip))
    assert r[0] == r[1] and r[2] == r[3]


# ── Verdrahtung: Schreibwege, Gates, Lese-Block bleibt lesend ───────────────

def test_schreibwege_und_gates(index_html):
    b = _stamm_block(index_html)
    assert '"fz-fs-kontrollen":["fz-fs-kontrollen","fz_fs_kontrollen"]' in index_html, "ROUTE_MAP -> generischer Weg"
    assert "else if(mapped&&mapped.id){await _sbInsertIfAbsent(table,mapped);" in index_html, "POST mit Client-id = idempotent"
    assert "SQ.push({url:'/api/fz-fs-kontrollen',method:'POST',body:row});" in b
    assert b.count("SQ.push(") == 1,"einzige neue Warteschlangen-Schreibstelle"
    for verboten in ("_sbPatch", "_sbPost", "_sbDelete", "fetch(", "localStorage.", "?.", "readAsDataURL"):
        assert verboten not in b, verboten
    assert "_dateiZiel('fz_fs_kontrollen','nachweis',id,foto)" in b and "row.nachweis_path=z.ref;" in b
    assert "fz_fs_kontrollen:1" not in index_html, "Nachweis bleibt PRIVAT (nicht in _DATEI_OEFFENTLICH)"
    # Fahrzeug: nur ueber upd() mit Spalten-Rumpf, Rechte wie RLS
    assert ("React.createElement(FahrzeugStammKarte, {key: \"stamm_\"+selFz.id, f: selFz, isMob: isMob, spaltenDa: _fzStammSpalten(fahrzeuge), "
            "siehtFinanz: isVAdmin, darfFinanz: _maStaffRolle(curUser), darfReifen: _maStaffRolle(curUser)||!!(curUser&&curUser.monteurId&&selFz.fahrer===curUser.monteurId), "
            "onSpeichern: function(body){upd(sel,function(x){return Object.assign({},x,body);},body);}})") in index_html
    assert "zeigeFsKtr: _maStaffRolle(curUser), onOpen: setSel})" in index_html
    assert "isAdmin?React.createElement(FsKontrolleSection,{key:\"fsk_\"+selM.id,monteur:selM,curUser:curUser,isMob:isMob})" in index_html
    assert "if(!_maStaffRolle(cu)||!mid)return null;" in b, "Abschnitt selbst gated"
    assert "function _maStaffRolle(u){\n  return !!(u&&(u.role===\"admin\"||u.role===\"projektleiter\"||u.role===\"buero\"));" in index_html, \
        "is_hr der RLS = admin/projektleiter/buero"


def test_lese_block_bleibt_lesend(index_html):
    a = index_html[index_html.index("//@FLOTTE-AUSBAU-START"):index_html.index("//@FLOTTE-AUSBAU-END")]
    for verboten in ("SQ.push", "_sbPatch", "_sbPost", "upd(", "_fz_fs_kontrollen"):
        assert verboten not in a
    assert "props.zeigeFsKtr?h(FsKontrolleFristenKarte" in a


# ── Render-Rauchprobe ───────────────────────────────────────────────────────

def test_ansichten_rendern(node_exe, index_html, tmp_path):
    linien = []
    for pat in (r"^const COLORS=\{.*?\};", r"^const fmt\$=.*$"):
        m = re.search(pat, index_html, re.M)
        assert m, pat
        linien.append(m.group(0).rstrip("\r"))
    ui = re.search(r"const UI=\{grund:.*?fSeite:22,", index_html)
    ui_zeile = ui.group(0).rstrip(",") + "};"
    fns = STAMM + FS + ("_fzPickerlStufe", "_fzTerminErledigt", "_fzFristen", "_fzTankStats", "_fzServiceStats", "_fzFixkosten",
                        "_fzFahrerCheck", "_fzCsvZelle", "_fzCsv", "_fzCsvZahl", "_fzStufeChip", "_fzCsvLaden", "_fzChipBtn",
                        "_fsKtrMerken", "_fsKtrAusCache", "_fsKtrChip", "_maStaffRolle", "_n",
                        "FlotteFristenPanel", "FlotteKostenPanel", "FahrzeugStammKarte", "FsKontrolleSection", "FsKontrolleFristenKarte")
    zusatz = ("var _fsKtrCache={};function LL(){return {};}var bpS={};function td2(){return '2026-11-19';}function uid(){return 'u1';}"
              "_react.useRef={call:function(){return {current:null};}};var SQ={push:function(){}};\n")
    fz = [{"id": "F1", "kennzeichen": "TU-1", "pickerl": "2027-06-01", "naechstService": "2027-06-01", "fahrer": "m1", "kmStand": 49200,
           "leasing_ende": "2027-01-18", "leasing_rate": 450, "versicherung_praemie": 1200, "versicherung_ablauf": "2026-12-09",
           "leasing_geber": None, "leasing_km_limit": None, "versicherung_polizze": None, "reifen_saison": "winter", "reifen_lager": None,
           "service_km_intervall": 15000, "naechst_service_km": 50000},
          {"id": "F2", "kennzeichen": "TU-2", "pickerl": "2027-06-01", "naechstService": "2027-06-01"}]
    ma = [{"id": "m1", "n": "Auer", "fs": "B"}]
    snip = (_UI_STUBS + zusatz + "\n".join(linien) + "\n" + ui_zeile + "\n"
            + _harness(index_html).replace(TZ, "")
            + "\n".join(_extract_fn(index_html, n) for n in fns) + "\n" + _texte(None) + "\n"
            "var fz=" + json.dumps(fz) + ",ma=" + json.dumps(ma) + ";var out={};"
            "var hr={role:'buero',name:'Büro Eva'},mont={role:'monteur',monteurId:'m1'};"
            "[false,true].forEach(function(mob){"
            "out['fr'+mob]=_tx(FlotteFristenPanel({fahrzeuge:fz,monteure:ma,isMob:mob,zeigeFahrer:true,zeigeFsKtr:true,onOpen:function(){}}));"
            "out['ko'+mob]=_tx(FlotteKostenPanel({fahrzeuge:fz,isMob:mob,onOpen:function(){}}));"
            "out['st'+mob]=_tx(FahrzeugStammKarte({f:fz[0],isMob:mob,spaltenDa:true,siehtFinanz:true,darfFinanz:true,darfReifen:true,offenStart:true}));"
            "out['stLeer'+mob]=_tx(FahrzeugStammKarte({f:fz[1],isMob:mob,spaltenDa:true,siehtFinanz:false,darfFinanz:false,darfReifen:false,offenStart:true}));"
            "out['stAlt'+mob]=_tx(FahrzeugStammKarte({f:fz[1],isMob:mob,spaltenDa:false,siehtFinanz:true,darfFinanz:true,darfReifen:true,offenStart:true}));"
            "out['fs'+mob]=_tx(FsKontrolleSection({monteur:ma[0],curUser:hr,isMob:mob}));});"
            "out.fsMonteur=FsKontrolleSection({monteur:ma[0],curUser:mont,isMob:false});"
            "out.koOhne=_tx(FlotteKostenPanel({fahrzeuge:[fz[1]],isMob:false}));"
            "_hooks.forEach(function(fn){var c=fn();if(typeof c==='function')c();});"
            "process.stdout.write(JSON.stringify(out));")
    r = json.loads(_node_datei(node_exe, tmp_path, snip))
    for mob in ("false", "true"):
        fr, ko, st = r["fr" + mob], r["ko" + mob], r["st" + mob]
        assert "Leasing-Ende" in fr and "Versicherung" in fr and "Service (km)" in fr and "noch 800 km" in fr
        assert "Führerscheinkontrolle (Halterpflicht)" in fr and "nie kontrolliert" in fr and "Auer" in fr
        assert "Leasing €/Monat" in ko or mob == "true"
        assert "Leasing + Versicherung je Monat" in ko and "550" in ko
        assert "Leasing & Versicherung" in st and "Reifen & Service-Intervall" in st and "Speichern" in st
        assert "Leasing & Versicherung" not in r["stLeer" + mob], "Betraege nur fuer Verwalter"
        assert "Speichern" not in r["stLeer" + mob]
        assert "noch nicht geladen" in r["stAlt" + mob] and "Speichern" not in r["stAlt" + mob], "Spalten-Sniff sperrt"
        assert "Kontrolle erfassen" in r["fs" + mob] and "nie kontrolliert" in r["fs" + mob]
        for t in (fr, ko, st, r["fs" + mob]):
            assert "NaN" not in t and "1970" not in t and "null" not in t and "undefined" not in t
    assert r["fsMonteur"] is None, "Monteur sieht keine Kontrollen anderer"
    assert "Leasing €/Monat" not in r["koOhne"] and "Leasing + Versicherung" not in r["koOhne"], "ohne Daten keine Spalten"
