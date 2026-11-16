# -*- coding: utf-8 -*-
"""Datanorm-Client (16.11.2026) - manueller DATANORM-Upload in der Haendlerverwaltung.

Befunde aus dem Server-Port (feature/datanorm-sync, supplier-sync/datanorm.ts), am Client geprueft:
  a) Upsert schickte id:_uuid() je Zeile -> mit on_conflict=supplier_id,art_nr und
     merge-duplicates tauschte JEDER Import die ids bestehender supplier_articles.
     Jetzt: _dnUpsertZeilen ohne id (DB-Default gen_random_uuid()).
  b) DATPREIS (DATANORM 4 P-Satz): P;A;[ArtNr;Preiskz;Preis;Rabattkz;Rabatt;...] x bis zu 3
     Bloecke je 9 Felder. Eine Preiseinheit hat der P-Satz nicht - sie kommt aus dem A-Satz
     (Feld 8, Code 0/1/2/3 = 1/10/100/1000). Vorher: p[5] (Rabattkennzeichen) als PE, nur Block 1,
     Verarbeitungskennzeichen "A" unerkannt.
  c) Zeichensatz byteweise (CP850 / ISO-8859-1 / UTF-8), Entscheidung an der ersten Zeile mit
     hohen Bytes - wie der Server-Parser.

Alle Proben laufen in node gegen die ECHTEN Funktionen aus index.html, jede mit Umkehrprobe.
"""
import base64
import json
import os
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


def _konstante(src, kopf):
    a = src.index(kopf)
    e = src.index("\n];\n", a) + 4
    return src[a:e]


def _quelle(src):
    teile = [_funktion(src, n) for n in (
        "_fixCp850", "_dnZeichensatz", "_dnDekodieren", "_dnBytesZuText",
        "_parseDatanorm", "_parseDatanormFiles", "_epAutoMatch", "_dnUpsertZeilen")]
    teile.insert(0, _konstante(src, "const EP_AUTO_FILTER=["))
    return "\n".join(teile)


NODE = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8')+"\n;global._p={_dnZeichensatz,_dnDekodieren,_dnBytesZuText,_parseDatanormFiles,_epAutoMatch,_dnUpsertZeilen};");
const ein=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
const B=(x)=>new Uint8Array(Buffer.from(x,'base64'));
// echte Blob/File-Schnittstelle (arrayBuffer), wie im Browser
const datei=(d)=>new File([Buffer.from(d.b64,'base64')],d.name);
(async()=>{
  const aus={};
  aus.tafel=_p._dnDekodieren(B(ein.hoch),"cp850");
  aus.zs={};for(const k of Object.keys(ein.texte)){const r=_p._dnBytesZuText(B(ein.texte[k]));aus.zs[k]={zs:r.zs,text:r.text};}
  aus.dateien={};
  for(const k of Object.keys(ein.dateien)){
    const r=await _p._parseDatanormFiles(ein.dateien[k].map(datei),0);
    aus.dateien[k]=r.map(a=>({artNr:a.artNr,name:a.name,preis:a.preis,rabGrp:a.rabGrp}));
    if(k==="upsert"){const m=_p._epAutoMatch(r);aus.zeilen=_p._dnUpsertZeilen(r,m,"11111111-2222-3333-4444-555555555555");}
  }
  process.stdout.write(JSON.stringify(aus));
})().catch(e=>{process.stdout.write("FEHLER "+e.stack);process.exit(1);});
"""


def _b64(b):
    return base64.b64encode(b).decode("ascii")


def _cp(s):
    return s.encode("cp850")


# A-Saetze DATANORM 4: A;Vkz;ArtNr;Textkz;KT1;KT2;Preiskz;PE-Code;ME;Preis;RabGrp;WG
DN4 = _cp("\r\n".join([
    "V 161126Holter Testdaten                           EUR",
    "A;N;3001;00;Kugelhahn Messing;DN15;1;2;Stk;12345;R1;WG1;",
    "A;N;3002;00;Rohrschelle Straße;verzinkt;1;2;Stk;0;R1;WG1;",
    "A;N;3003;00;Schraube;M6;2;0;Stk;0;R2;WG1;",
    "A;N;3004;00;Dübel;8 mm;1;1;Stk;0;R3;WG1;",
    "",
]))
# DATPREIS nach Spezifikation: drei Artikelbloecke je 9 Felder in EINER Zeile,
# Rabattkennzeichen 1 bzw. 0 an der Stelle, die der alte Parser als Preiseinheit las.
DATPREIS = b"P;A;3002;1;12345;1;4050;;;;;3003;2;990;0;R1;;;;;3004;1;500;1;0;;;;\r\n"

# Probe c: CP850 "Stra\xe1e", echtes ISO-8859-1, UTF-8 mit typografischen Anfuehrungszeichen
TEXTE = {
    "cp850": b"A;N;1;00;Stra\xe1e;\r\n",
    "latin1": b"A;N;1;00;Stra\xdfe Gr\xf6\xdfe;\r\n",
    "utf8": "A;N;1;00;Größe „Spezial“ Cafá;\r\n".encode("utf-8"),
    # erste hohe Zeile unentscheidbar (nur 0xE9), Entscheidung erst in Zeile 2 -> CP850 ab dort
    "spaet": b"A;N;1;00;Caf\xe9;\r\nA;N;2;00;Stra\xe1e;\r\n",
    "ascii": b"A;N;1;00;Rohr;\r\n",
}

UPSERT = _cp("\r\n".join([
    "A;N;9001;00;Geberit Mepla Verbundrohr;16 mm;1;0;Stk;450;R1;WG1;",
    "A;N;9002;00;Irgendwas ohne Linie;;1;0;Stk;100;R1;WG1;",
    "",
]))


def _lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "q.js"
    q.write_text(quelle, encoding="utf-8")
    d = tmp_path / "d.json"
    d.write_text(json.dumps({
        "hoch": _b64(bytes(range(128, 256))),
        "texte": {k: _b64(v) for k, v in TEXTE.items()},
        "dateien": {
            "dn4": [{"name": "DATANORM.001", "b64": _b64(DN4)}, {"name": "DATPREIS.001", "b64": _b64(DATPREIS)}],
            "utf8": [{"name": "DATANORM.001", "b64": _b64(
                "A;N;4001;00;Größe „Spezial“;Cafá;1;0;Stk;100;;\r\n".encode("utf-8"))}],
            "upsert": [{"name": "DATANORM.001", "b64": _b64(UPSERT)}],
        },
    }), encoding="utf-8")
    s = tmp_path / "l.js"
    s.write_text(NODE, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q), str(d)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return json.loads(out)


def _nr(arts):
    return {a["artNr"]: a for a in arts}


@pytest.fixture
def ergebnis(index_html, node_exe, tmp_path):
    return _lauf(node_exe, tmp_path, _quelle(index_html))


# ── a) Upsert ohne id ───────────────────────────────────────────────────────
def test_upsert_zeilen_ohne_id(ergebnis):
    z = ergebnis["zeilen"]
    assert len(z) == 1, z  # 9002 passt zu keiner EP-Linie
    assert "id" not in z[0]
    assert z[0]["art_nr"] == "9001" and z[0]["supplier_id"] == "11111111-2222-3333-4444-555555555555"
    assert z[0]["ep_system"] == "Geberit Mepla" and z[0]["ek_preis"] == pytest.approx(4.50)


def test_handler_nutzt_den_helfer_und_kein_id_im_body(index_html):
    h = index_html[index_html.index("const handleDnUpload="):]
    h = h[:h.index("setTimeout(fetchSuppliers,500);")]
    assert "const rows=_dnUpsertZeilen(articles,autoMap,_suppId);" in h
    assert "id:_uuid()" not in h
    assert "on_conflict=supplier_id,art_nr" in h


def test_umkehrprobe_upsert_mit_id(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("rows.push({supplier_id:suppId,", "rows.push({id:'x',supplier_id:suppId,", 1)
    assert alt != q
    assert "id" in _lauf(node_exe, tmp_path, alt)["zeilen"][0]


# ── b) Preiseinheit A-Satz und DATPREIS ─────────────────────────────────────
def test_a_satz_preis_cent_mit_pe_code_2(ergebnis):
    a = _nr(ergebnis["dateien"]["dn4"])
    assert a["3001"]["preis"] == pytest.approx(1.2345)  # 12345 Cent je 100 Stk


def test_datpreis_drei_bloecke_pe_aus_a_satz(ergebnis):
    a = _nr(ergebnis["dateien"]["dn4"])
    assert a["3002"]["preis"] == pytest.approx(1.2345), a["3002"]  # PE-Code 2 aus dem A-Satz
    assert a["3003"]["preis"] == pytest.approx(9.90), a["3003"]    # Block 2, netto, je 1 Stk
    assert a["3004"]["preis"] == pytest.approx(0.50), a["3004"]    # Block 3, PE-Code 1 -> je 10 Stk
    # Rabattwert/-kennzeichen werden NICHT zur Rabattgruppe; die aus dem A-Satz bleibt
    assert a["3002"]["rabGrp"] == "R1" and a["3003"]["rabGrp"] == "R2"
    assert "A" not in a


def test_umkehrprobe_alte_datpreis_preiseinheit(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    # alter Lesefehler: das Feld nach dem Preis (Rabattkennzeichen) als Preiseinheit
    alt = q.replace("out[artNr]={preis:preis,pe:null,rabGrp:\"\"}",
                    "out[artNr]={preis:preis,pe:parseInt(p[b+3],10)||1,rabGrp:\"\"}", 1)
    assert alt != q
    a = _nr(_lauf(node_exe, tmp_path, alt)["dateien"]["dn4"])
    assert a["3002"]["preis"] != pytest.approx(1.2345)


def test_umkehrprobe_nur_erster_block(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("for(let b=2;b<p.length;b+=9)", "for(let b=2;b<3;b+=9)", 1)
    assert alt != q
    a = _nr(_lauf(node_exe, tmp_path, alt)["dateien"]["dn4"])
    assert a["3003"]["preis"] == 0


# ── c) Zeichensatz ──────────────────────────────────────────────────────────
def test_cp850_tafel_gleich_python(ergebnis):
    assert ergebnis["tafel"] == bytes(range(128, 256)).decode("cp850")


def test_zeichensatz_entscheidung(ergebnis):
    z = ergebnis["zs"]
    assert z["cp850"] == {"zs": "cp850", "text": "A;N;1;00;Straße;\r\n"}
    assert z["latin1"]["zs"] == "iso-8859-1" and "Straße Größe" in z["latin1"]["text"]
    assert z["utf8"]["zs"] == "utf-8" and "Größe „Spezial“ Cafá" in z["utf8"]["text"]
    assert z["spaet"]["zs"] == "cp850"
    assert z["spaet"]["text"] == "A;N;1;00;Café;\r\nA;N;2;00;Straße;\r\n"
    assert z["ascii"]["zs"] == "ascii"


def test_upload_umlaute_und_utf8_unverbogen(ergebnis):
    a = _nr(ergebnis["dateien"]["dn4"])
    assert a["3002"]["name"] == "Rohrschelle Straße verzinkt"
    assert a["3004"]["name"] == "Dübel 8 mm"
    # UTF-8 mit „“ und á: _fixCp850 darf hier NICHT raten (sonst „->ä, á->ß)
    assert _nr(ergebnis["dateien"]["utf8"])["4001"]["name"] == "Größe „Spezial“ Cafá"


def test_umkehrprobe_ohne_cp850_tafel(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace('const hoch=zs==="cp850"?', 'const hoch=false&&zs==="cp850"?', 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    assert r["zs"]["cp850"]["text"] != "A;N;1;00;Straße;\r\n"
    assert _nr(r["dateien"]["dn4"])["3002"]["name"] != "Rohrschelle Straße verzinkt"


def test_umkehrprobe_utf8_ohne_dekodiert_flag(index_html, node_exe, tmp_path):
    q = _quelle(index_html)
    alt = q.replace("if(!dekodiert&&/", "if(/", 1)
    assert alt != q
    r = _lauf(node_exe, tmp_path, alt)
    assert _nr(r["dateien"]["utf8"])["4001"]["name"] != "Größe „Spezial“ Cafá"


def test_server_tafel_identisch_falls_vorhanden(index_html, repo_root):
    """Gleichlauf mit dem Server-Parser, sobald feature/datanorm-sync gemergt ist."""
    pfad = os.path.join(repo_root, "supabase", "functions", "supplier-sync", "datanorm.ts")
    if not os.path.exists(pfad):
        pytest.skip("Server-Parser (feature/datanorm-sync) noch nicht in diesem Stand")
    import re
    ts = open(pfad, encoding="utf-8").read()
    m = re.search(r'export const CP850_HIGH =\s*((?:"[^"]*"\s*\+?\s*)+);', ts)
    assert "".join(re.findall(r'"([^"]*)"', m.group(1))) == bytes(range(128, 256)).decode("cp850")
