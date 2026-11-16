# -*- coding: utf-8 -*-
"""Datanorm-Client Rest (16.11.2026) - Brutto/Netto, last_updated, Katalog ueber den Bytepfad.

  A1  Material-Katalog-Import las per readAsText(...,'ISO-8859-1') (= windows-1252) und riet
      danach mit _fixCp850. Jetzt _dnKatalogLesen: Bytes -> _dnBytesZuText -> _parseDatanorm
      mit dekodiert=true (wie der Haendler-Upload).
  A2  Preiskennzeichen 1 = Bruttopreis, 2 = Nettopreis (A-Satz Stelle 7, P-Satz je Block
      Stelle 4; hilfe.comtech.at/ce/2020/HTML/datanorm_datei.htm, Beispiel flace.de/?p=577
      "EV10;1;2010" = Bruttopreis 20,10). Brutto -> listenpreis, Netto -> ek_preis. Nur EIN
      Preis bekannt -> wie bisher in beiden Spalten, aber gezaehlt (rows.preise).
  A4  last_updated in jeder Upsert-Zeile (wie zeilenFuerUpsert im Server-Parser).

Alle Proben laufen in node gegen die ECHTEN Funktionen aus index.html, jede mit Umkehrprobe.
"""
import base64
import json
import re
import subprocess

import pytest

from conftest import EPK_TEST_TIMEOUT


def _funktion(src, name):
    i = src.find("\nfunction " + name + "(")
    if i < 0:
        i = src.index("\nasync function " + name + "(")
    a = i + 1
    e = src.index("\n}\n", a) + 2
    return src[a:e]


def _quelle(src):
    teile = [_funktion(src, n) for n in (
        "_fixCp850", "_dnZeichensatz", "_dnDekodieren", "_dnBytesZuText", "_parseDatanorm",
        "_parseDatanormFiles", "_dnKatalogLesen", "_epAutoMatch", "_dnUpsertZeilen")]
    a = src.index("const EP_AUTO_FILTER=[")
    teile.insert(0, src[a:src.index("\n];\n", a) + 4])
    return "\n".join(teile)


NODE = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8')+"\n;global._p={_parseDatanormFiles,_dnKatalogLesen,_epAutoMatch,_dnUpsertZeilen};");
const ein=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const datei=(d)=>new File([Buffer.from(d.b64,'base64')],d.name);
(async()=>{
  const aus={};
  const r=await _p._parseDatanormFiles(ein.upload.map(datei),0);
  const z=_p._dnUpsertZeilen(r,_p._epAutoMatch(r),"11111111-2222-3333-4444-555555555555");
  aus.zeilen={};for(const x of z)aus.zeilen[x.art_nr]=x;
  aus.preise=z.preise||null;
  aus.katalog={};
  for(const k of Object.keys(ein.katalog)){const k2=await _p._dnKatalogLesen(datei(ein.katalog[k]),0);aus.katalog[k]={zs:k2.zs,namen:k2.arts.map(a=>a.name)};}
  process.stdout.write(JSON.stringify(aus));
})().catch(e=>{process.stdout.write("FEHLER "+e.stack);process.exit(1);});
"""

# A-Saetze DATANORM 4: A;Vkz;ArtNr;Textkz;KT1;KT2;Preiskz;PE-Code;ME;Preis;RabGrp;WG
DN4 = "\r\n".join([
    "V 161126Testhaendler                               EUR",
    "A;N;7001;00;Geberit Mepla Verbundrohr;16 mm;1;0;Stk;1000;R1;WG1;",  # brutto 10,00 + DATPREIS netto 7,00
    "A;N;7002;00;Geberit Mepla Verbundrohr;20 mm;1;0;Stk;1200;R1;WG1;",  # nur brutto 12,00
    "A;N;7003;00;Geberit Mepla Verbundrohr;26 mm;2;0;Stk;900;R1;WG1;",   # nur netto 9,00
    "A;N;7004;00;Geberit Mepla Verbundrohr;32 mm;1;0;Stk;0;R1;WG1;",     # Preise nur aus DATPREIS
    "",
]).encode("cp850")
# DATPREIS: Bloecke ArtNr;Preiskz;Preis;Rabattkz;Rabatt + 4 Leerfelder; 7004 zweimal (brutto, netto)
DATPREIS = (b"P;A;7001;2;700;1;0;;;;;7004;1;1500;1;0;;;;\r\n"
            b"P;A;7004;2;1100;1;0;;;;\r\n")
# DATANORM 5 ohne Preiskennzeichen im Parser -> "ohne Kennzeichen"
DN5 = ("V;1;Haendler;DATANORM;5.0;161126\r\n"
       "A;7005;;Geberit Mepla Verbundrohr;40 mm;;Stk;\r\n"
       "P;7005;1;2500;1;R1\r\n").encode("latin-1")

KATALOG = {
    "cp850": "A;N;8001;00;Rohrschelle Straße;verzinkt;1;0;Stk;100;R1;WG1;\r\n".encode("cp850"),
    "utf8": "A;N;8002;00;Größe „Spezial“;Cafá;1;0;Stk;100;R1;WG1;\r\n".encode("utf-8"),
}


def _b64(b):
    return base64.b64encode(b).decode("ascii")


def _lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "q.js"
    q.write_text(quelle, encoding="utf-8")
    d = tmp_path / "d.json"
    d.write_text(json.dumps({
        "upload": [{"name": "DATANORM.001", "b64": _b64(DN4)},
                   {"name": "DATPREIS.001", "b64": _b64(DATPREIS)},
                   {"name": "DN5.001", "b64": _b64(DN5)}],
        "katalog": {k: {"name": "KAT.001", "b64": _b64(v)} for k, v in KATALOG.items()},
    }), encoding="utf-8")
    s = tmp_path / "l.js"
    s.write_text(NODE, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q), str(d)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return json.loads(out)


@pytest.fixture
def ergebnis(index_html, node_exe, tmp_path):
    return _lauf(node_exe, tmp_path, _quelle(index_html))


def _umkehr(index_html, node_exe, tmp_path, alt, neu):
    q = _quelle(index_html)
    kaputt = q.replace(alt, neu, 1)
    assert kaputt != q, "Umkehrprobe greift nicht: %r" % alt
    return _lauf(node_exe, tmp_path, kaputt)


# ── A2 Brutto/Netto ─────────────────────────────────────────────────────────
def test_brutto_listenpreis_netto_ek(ergebnis):
    z = ergebnis["zeilen"]
    assert z["7001"]["listenpreis"] == pytest.approx(10.0) and z["7001"]["ek_preis"] == pytest.approx(7.0), z["7001"]
    assert z["7004"]["listenpreis"] == pytest.approx(15.0) and z["7004"]["ek_preis"] == pytest.approx(11.0), z["7004"]


def test_nur_ein_preis_bleibt_in_beiden_spalten_und_wird_gezaehlt(ergebnis):
    z = ergebnis["zeilen"]
    assert z["7002"]["listenpreis"] == z["7002"]["ek_preis"] == pytest.approx(12.0)
    assert z["7003"]["listenpreis"] == z["7003"]["ek_preis"] == pytest.approx(9.0)
    assert z["7005"]["listenpreis"] == z["7005"]["ek_preis"] == pytest.approx(25.0)
    assert ergebnis["preise"] == {"getrennt": 2, "nurBrutto": 1, "nurNetto": 1, "ohneKz": 1}


def test_umkehrprobe_ein_preis_fuer_beide_spalten(index_html, node_exe, tmp_path):
    r = _umkehr(index_html, node_exe, tmp_path,
                "listenpreis:_b||art.preis||0,ek_preis:_n||art.preis||0",
                "listenpreis:art.preis||0,ek_preis:art.preis||0")
    assert r["zeilen"]["7001"]["ek_preis"] != pytest.approx(7.0)


def test_umkehrprobe_a_satz_kennzeichen_ignoriert(index_html, node_exe, tmp_path):
    r = _umkehr(index_html, node_exe, tmp_path, 'pk=(parts[6]||"").trim();', 'pk="";')
    assert r["preise"] != {"getrennt": 2, "nurBrutto": 1, "nurNetto": 1, "ohneKz": 1}


def test_umkehrprobe_datpreis_kennzeichen_ignoriert(index_html, node_exe, tmp_path):
    r = _umkehr(index_html, node_exe, tmp_path, 'const _pk=(p[b+1]||"").trim();', 'const _pk="";')
    assert r["zeilen"]["7001"]["ek_preis"] != pytest.approx(7.0)


def test_ergebniszeile_nennt_die_preisart(index_html):
    h = index_html[index_html.index("const handleDnUpload="):]
    h = h[:h.index("setTimeout(fetchSuppliers,500);")]
    assert "preisArt:_dnPreisArt" in h
    for t in ('"Nur Bruttopreis: "', '"Nur Nettopreis: "', '"Ohne Preiskennzeichen: "', '"Brutto und Netto getrennt: "'):
        assert t in index_html, t


# ── A4 last_updated ─────────────────────────────────────────────────────────
def test_last_updated_in_jeder_zeile(ergebnis):
    for nr, z in ergebnis["zeilen"].items():
        assert re.match(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$", z.get("last_updated", "")), (nr, z)
        assert "id" not in z


def test_umkehrprobe_ohne_last_updated(index_html, node_exe, tmp_path):
    r = _umkehr(index_html, node_exe, tmp_path, ",last_updated:_jetzt", "")
    assert "last_updated" not in r["zeilen"]["7001"]


# ── A1 Katalog ueber den Bytepfad ───────────────────────────────────────────
def test_katalog_liest_bytes(ergebnis):
    k = ergebnis["katalog"]
    assert k["cp850"] == {"zs": "cp850", "namen": ["Rohrschelle Straße verzinkt"]}
    assert k["utf8"] == {"zs": "utf-8", "namen": ["Größe „Spezial“ Cafá"]}


def test_umkehrprobe_katalog_alter_textpfad(index_html, node_exe, tmp_path):
    r = _umkehr(index_html, node_exe, tmp_path,
                "_parseDatanorm(d.text,ver===0?null:ver,true)",
                "_parseDatanorm(new TextDecoder('windows-1252').decode(new Uint8Array(buf)),ver===0?null:ver)")
    k = r["katalog"]
    assert k["cp850"]["namen"] != ["Rohrschelle Straße verzinkt"]
    assert k["utf8"]["namen"] != ["Größe „Spezial“ Cafá"]


def test_katalog_handler_nutzt_den_bytepfad(index_html):
    i = index_html.index("const renderKatalog=()=>{")
    h = index_html[i:index_html.index("const filtered=dnArticles.filter(", i)]
    h = re.sub(r"/\*.*?\*/", "", h, flags=re.S)  # Kommentare nennen den alten Weg - gemessen wird Code
    assert "_dnKatalogLesen(file,dnVersion||0)" in h
    assert "readAsText" not in h and "tryParse" not in h
    assert "Datei konnte nicht gelesen werden" in h  # Lesefehler meldet sich weiter (v3.9.22 F-4)
