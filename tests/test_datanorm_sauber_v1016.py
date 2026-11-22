# -*- coding: utf-8 -*-
"""v3.9.1016 - DATANORM sauber.

GF: "datanorm import funktioniert nicht, denke es scheitert an den
zugangsdaten" -> "fix das sauber".

Was aus dem Code belegt war:
  * saveSupplier schickte IMMER username:data.username||"" und
    password:data.password||"". Seit dem Lockdown v3105 koennen die
    Zugangsdaten beim Laden fehlen oder NULL sein - dann loeschte JEDES
    Bearbeiten (z. B. nur Skonto) die hinterlegten Zugangsdaten.
  * "DATANORM herunterladen" war ein window.open ohne Zugangsdaten; ein
    automatischer Download existiert nicht. Jetzt: "Im Haendlerportal
    anmelden" + Anleitung in drei Schritten + Upload.
  * supplier-sync meldete "success" mit 0 Artikeln (Platzhalter).

Die Riegel hier:
  1. Parser-Nachweis in node mit synthetischen DATANORM-4- (CP850) und
     DATANORM-5-Dateien (Latin1), A/B-Saetze, DATPREIS, WRG; Umlaute samt
     Grossumlauten und ss. Umkehrprobe: ohne die v1016-Ergaenzung in
     _fixCp850/Erkennung faellt der Grossumlaut-/ss-Fall durch.
  2. Leer-Ueberschreib-Riegel: _supplierSaveBody laeuft in node - ohne
     Eingabe stehen username/password NICHT im Rumpf. Umkehrprobe mit dem
     alten Rumpf.
  3. Ehrlicher Stand: NULL = nicht lesbar, '' = nicht hinterlegt.
  4. Status ohne Emoji, Farbe ueber dnUploadArt (nicht startsWith("❌")).
  5. supplier-sync: keine Erfolgsmeldung ohne Download.
"""
import json
import os
import re
import subprocess

import pytest

from conftest import EPK_TEST_TIMEOUT

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(HIER)


def _funktion(src, name):
    i = src.find("\nfunction " + name + "(")
    if i < 0:
        i = src.index("\nasync function " + name + "(")
    a = i + 1
    e = src.index("\n}\n", a) + 2
    return src[a:e]


def _helfer_quelle(src):
    return "\n".join(_funktion(src, n) for n in (
        "_fixCp850", "_dnZeichensatz", "_dnDekodieren", "_dnBytesZuText",
        "_parseDatanorm", "_parseDatanormFiles",
        "_supplierSaveBody", "_supplierCredStand",
        # v3.9.1093: _supplierSaveBody liest Skonto/Bonus/Intervall jetzt ueber die echten Leser aus index.html
        "_fzZahl", "_ganzZahl"))


# ── synthetische Dateien ────────────────────────────────────────────────────
def _cp850(s):
    return s.encode("cp850")


DN4 = _cp850("\r\n".join([
    "V 161126Holter Testdaten                           EUR",
    "A;N;1001;00;Kugelhahn Messing;für Trinkwasser;1;0;Stk;2450;R12;WG1;",
    "B;N;1001;KUGELHAHN;;;;;;4001234567890;;",
    "A;N;1002;00;Übergangsstück Größe;Maße ½ Zoll;1;0;Stk;990;R12;WG1;",
    "A;N;1003;00;ÖLFILTER ÄUSSERST;ÜBERWURF;1;0;Stk;0;R5;WG1;",
    "B;N;1003;OELFILTER;;;;;;4001234567891;;",
    "",
]).replace("½", "1/2"))
DATPREIS = _cp850("\r\n".join(["P;N;1003;1;12345;1;R5", ""]))
WRG = _cp850("\r\n".join(["S;N;WG1;Armaturen für Wasser", ""]))
DN5 = "\r\n".join([
    "V;1;Testfirma;DATANORM;5.0;20261116",
    "A;5001;;Heizkörper Typ 22;Weiß lackiert;;Stk",
    "A;5002;;Thermostatkopf;;;Stk",
    "P;5001;1;15990;1",
    "P;5002;1;2500;1",
    "",
]).encode("latin-1")

NUR_GROSS = _cp850("\r\n".join([
    "A;N;2001;00;ÖLWANNE ÜBERLAUF;ÄUSSERE;1;0;Stk;100;;",
    "",
]))

NODE_PARSER = r"""
const fs=require('fs');
const src=fs.readFileSync(process.argv[2],'utf8');
const dateien=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
class FileReader{readAsArrayBuffer(f){const b=Buffer.from(f.b64,'base64');this.result=b.buffer.slice(b.byteOffset,b.byteOffset+b.length);setTimeout(()=>this.onload&&this.onload(),0);}readAsText(f,enc){try{this.result=new TextDecoder(enc).decode(Buffer.from(f.b64,'base64'));setTimeout(()=>this.onload&&this.onload(),0);}catch(e){setTimeout(()=>this.onerror&&this.onerror(e),0);}}}
global.FileReader=FileReader;
eval(src+"\n;global._parseDatanormFiles=_parseDatanormFiles;");
(async()=>{
  const aus={};
  for(const k of Object.keys(dateien)){
    const r=await _parseDatanormFiles(dateien[k],0);
    aus[k]={arts:r.map(a=>({artNr:a.artNr,name:a.name,kt2:a.kt2,me:a.me,preis:a.preis,rabGrp:a.rabGrp})),detVer:r.detVer,stats:r.stats};
  }
  process.stdout.write(JSON.stringify(aus));
})().catch(e=>{process.stdout.write("FEHLER "+e.stack);process.exit(1);});
"""


def _b64(b):
    import base64
    return base64.b64encode(b).decode("ascii")


def _parser_lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "quelle.js"
    q.write_text(quelle, encoding="utf-8")
    d = tmp_path / "dateien.json"
    d.write_text(json.dumps({
        "dn4": [{"name": "DATANORM.001", "b64": _b64(DN4)},
                {"name": "DATPREIS.001", "b64": _b64(DATPREIS)},
                {"name": "DATANORM.WRG", "b64": _b64(WRG)}],
        "dn5": [{"name": "DN5.001", "b64": _b64(DN5)}],
        "gross": [{"name": "GROSS.001", "b64": _b64(NUR_GROSS)}],
        "leer": [{"name": "DATPREIS.001", "b64": _b64(DATPREIS)}],
    }), encoding="utf-8")
    s = tmp_path / "lauf.js"
    s.write_text(NODE_PARSER, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q), str(d)], capture_output=True,
                       timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return json.loads(out)


def _nach_nr(arts):
    return {a["artNr"]: a for a in arts}


def test_parser_datanorm4_cp850_mit_datpreis_und_wrg(index_html, node_exe, tmp_path):
    r = _parser_lauf(node_exe, tmp_path, _helfer_quelle(index_html))
    dn4 = r["dn4"]
    a = _nach_nr(dn4["arts"])
    assert sorted(a) == ["1001", "1002", "1003"], "B-Saetze duerfen keine Artikel werden: %r" % sorted(a)
    assert dn4["detVer"] == "v4ext"
    assert a["1001"]["name"] == "Kugelhahn Messing für Trinkwasser"
    assert a["1002"]["name"] == "Übergangsstück Größe Maße 1/2 Zoll", a["1002"]["name"]
    assert a["1003"]["name"] == "ÖLFILTER ÄUSSERST ÜBERWURF"
    assert a["1001"]["preis"] == pytest.approx(24.50)
    assert a["1002"]["preis"] == pytest.approx(9.90)
    # 1003 hat im A-Satz keinen Preis -> DATPREIS fuellt ihn
    assert a["1003"]["preis"] == pytest.approx(123.45)
    assert dn4["stats"] == {"files": 3, "articles": 3, "prices": 1, "groups": 1}


def test_parser_datanorm5_latin1(index_html, node_exe, tmp_path):
    r = _parser_lauf(node_exe, tmp_path, _helfer_quelle(index_html))
    dn5 = r["dn5"]
    assert dn5["detVer"] == "v5"
    a = _nach_nr(dn5["arts"])
    assert a["5001"]["name"] == "Heizkörper Typ 22 Weiß lackiert"
    assert a["5001"]["preis"] == pytest.approx(159.90)
    assert a["5002"]["preis"] == pytest.approx(25.00)
    assert a["5002"]["me"] == "Stk"


def test_parser_nur_grossumlaute_und_nur_preise(index_html, node_exe, tmp_path):
    r = _parser_lauf(node_exe, tmp_path, _helfer_quelle(index_html))
    assert r["gross"]["arts"][0]["name"] == "ÖLWANNE ÜBERLAUF ÄUSSERE"
    # nur DATPREIS ohne Artikeldatei -> 0 Artikel (die App meldet dann "Keine Artikel gefunden")
    assert r["leer"]["arts"] == []


# Datanorm-Client (16.11.2026): der Haendler-Upload dekodiert jetzt BYTEWEISE (_dnBytesZuText) und
# braucht _fixCp850 nicht mehr. _fixCp850 bleibt fuer den Textpfad (Material-Katalog, readAsText
# 'ISO-8859-1' = windows-1252 -> _parseDatanorm ohne dekodiert-Flag). Die v1016-Umkehrprobe laeuft
# deshalb auf genau diesem Textpfad weiter; die Umkehrprobe des Bytepfads steht in
# test_datanorm_client_upload.py.
NODE_TEXTPFAD = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8')+"\n;global._parseDatanorm=_parseDatanorm;");
const d=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const aus={};
for(const k of Object.keys(d)){const t=new TextDecoder('iso-8859-1').decode(Buffer.from(d[k],'base64'));aus[k]=_parseDatanorm(t,0).map(a=>({artNr:a.artNr,name:a.name}));}
process.stdout.write(JSON.stringify(aus));
"""


def _textpfad_lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "tq.js"
    q.write_text(quelle, encoding="utf-8")
    d = tmp_path / "td.json"
    d.write_text(json.dumps({"dn4": _b64(DN4), "gross": _b64(NUR_GROSS)}), encoding="utf-8")
    s = tmp_path / "tl.js"
    s.write_text(NODE_TEXTPFAD, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q), str(d)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return json.loads(out)


def test_umkehrprobe_parser_ohne_v1016_ergaenzung(index_html, node_exe, tmp_path):
    q = _helfer_quelle(index_html)
    r = _textpfad_lauf(node_exe, tmp_path, q)
    assert r["gross"][0]["name"] == "ÖLWANNE ÜBERLAUF ÄUSSERE"
    assert _nach_nr(r["dn4"])["1002"]["name"] == "Übergangsstück Größe Maße 1/2 Zoll"
    alt = q.replace("|\\u017D|\\u2122|\\u0161", "", 1).replace(".replace(/\\u00E1/g,'ß')", "", 1)
    assert alt != q
    r = _textpfad_lauf(node_exe, tmp_path, alt)
    assert r["gross"][0]["name"] != "ÖLWANNE ÜBERLAUF ÄUSSERE"
    assert _nach_nr(r["dn4"])["1002"]["name"] != "Übergangsstück Größe Maße 1/2 Zoll"


# ── Leer-Ueberschreib-Riegel ────────────────────────────────────────────────
NODE_BODY = r"""
const fs=require('fs');
eval(fs.readFileSync(process.argv[2],'utf8')+"\n;global._supplierSaveBody=_supplierSaveBody;global._supplierCredStand=_supplierCredStand;");
const basis={id:"x",name:"Holter",skonto_prozent:"3",username:null,kunde_nr:"1"};
const f=(d,n)=>{const b=_supplierSaveBody(d,n);return {hatU:"username" in b,hatP:"password" in b,u:b.username,p:b.password,skonto:b.skonto_prozent};};
process.stdout.write(JSON.stringify({
  nurSkonto:f({...basis},false),
  geladenMitKennwort:f({...basis,username:"alt",password:"geheim"},false),
  neuesKennwort:f({...basis,_passwortNeu:"neu!"},false),
  leeresKennwort:f({...basis,_passwortNeu:"   "},false),
  userGeleert:f({...basis,_usernameGeaendert:true,_usernameNeu:""},false),
  userNeu:f({...basis,_usernameGeaendert:true,_usernameNeu:" kolar "},false),
  anlegen:f({name:"Neu"},true),
  anlegenMit:f({name:"Neu",_usernameGeaendert:true,_usernameNeu:"u",_passwortNeu:"p"},true),
  stand:[_supplierCredStand({username:null,password:null}),_supplierCredStand({name:"x"}),_supplierCredStand({username:"",password:""}),_supplierCredStand({username:"u",password:"p"}),_supplierCredStand({username:"u",password:""})]
}));
"""


def _body_lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "b.js"
    q.write_text(quelle, encoding="utf-8")
    s = tmp_path / "blauf.js"
    s.write_text(NODE_BODY, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    return json.loads(p.stdout.decode("utf-8"))


def _verstoss(r):
    v = []
    for fall in ("nurSkonto", "geladenMitKennwort", "leeresKennwort"):
        if r[fall]["hatU"] or r[fall]["hatP"]:
            v.append(fall)
    if r["userGeleert"]["hatU"]:
        v.append("userGeleert")
    return v


def test_zugangsdaten_werden_nie_leer_ueberschrieben(index_html, node_exe, tmp_path):
    r = _body_lauf(node_exe, tmp_path, _helfer_quelle(index_html))
    assert not _verstoss(r), r
    assert r["nurSkonto"]["skonto"] == 3
    assert r["neuesKennwort"] == {"hatU": False, "hatP": True, "p": "neu!", "skonto": 3}
    assert r["userNeu"]["u"] == "kolar" and not r["userNeu"]["hatP"]
    # Anlegen: '' = nicht hinterlegt (nicht NULL = nicht lesbar)
    assert r["anlegen"]["u"] == "" and r["anlegen"]["p"] == ""
    assert r["anlegenMit"]["u"] == "u" and r["anlegenMit"]["p"] == "p"
    assert r["stand"] == ["unlesbar", "unlesbar", "fehlt", "hinterlegt", "unvollstaendig"]


def test_umkehrprobe_alter_rumpf_wird_erkannt(index_html, node_exe, tmp_path):
    q = _helfer_quelle(index_html)
    alt = q.replace('kunde_nr:data.kunde_nr||"",',
                    'kunde_nr:data.kunde_nr||"",username:data.username||"",password:data.password||"",', 1)
    assert alt != q
    assert _verstoss(_body_lauf(node_exe, tmp_path, alt))


def _haendler(src):
    a = src.index('adminTab==="haendler"&&(')
    e = src.index("/* ═══ TAB: EINSTELLUNGEN ═══ */", a)
    return src[a:e]


def _panel_logik(src):
    a = src.index("  // ═══ Händler State ═══")
    e = src.index('_react.useEffect.call(void 0, ()=>{if(adminTab==="haendler")fetchSuppliers();},[adminTab]);', a)
    return src[a:e]


def test_save_nutzt_den_helfer_und_formular_zeigt_kein_kennwort(index_html):
    lo = _panel_logik(index_html)
    assert "const body=_supplierSaveBody(data,isNew);" in lo
    assert 'password:data.password||""' not in index_html
    ui = _haendler(index_html)
    assert "value: suppEdit.password" not in ui, "das geladene Kennwort darf nicht ins Feld"
    assert "value: suppEdit._passwortNeu" in ui
    assert ui.count('"leer lassen = unverändert"') >= 2
    assert "delete o.password" in lo, "_suppEditStart muss das geladene Kennwort aus dem Zustand nehmen"
    assert "setSuppEdit(_suppEditStart(s))" in ui
    assert "setSuppEdit({...s})" not in ui


def test_haendlerkarte_portal_anleitung_und_kopieren(index_html):
    ui = _haendler(index_html)
    assert "DATANORM herunterladen" not in ui
    assert "Im Händlerportal anmelden" in ui
    for s in ("DATANORM-Dateien herunterladen", "Hier hochladen", "DATPREIS", "WRG", "DATANORM.001"):
        assert s in ui, s
    assert '_suppKopieren(s.kunde_nr,"Kundennummer")' in ui
    assert '_suppKopieren(s.username,"Benutzername")' in ui
    lo = _panel_logik(index_html)
    k = lo[lo.index("const _suppKopieren="):]
    k = k[:k.index("};") + 2]
    assert "try{" in k and "catch(e)" in k, "Clipboard-Fehler muss abgefangen werden"
    for s in ("Gelesen: ", "Nach EP-Filter: ", "Gespeichert: ", '"Fehler: "+dnErgebnis.fehler'):
        assert s in ui, s


def test_status_ohne_emoji_farbe_ueber_art(index_html):
    ui = _haendler(index_html)
    lo = _panel_logik(index_html)
    assert "dnUploadStatus.startsWith(" not in ui
    assert 'dnUploadArt==="fehler"?UI.fehler' in ui
    h = lo[lo.index("const handleDnUpload="):]
    for m in re.finditer(r'(?:_dnSet|setDnUploadStatus)\((.{0,80})', h):
        assert not re.search("[✅❌⚠⛔]", m.group(1)), m.group(0)
    assert "setDnUploadStatus(\"❌" not in h and "setDnUploadStatus(\"✅" not in h


def test_ci_farben_der_haendlerseite_neutral(index_html):
    ui = _haendler(index_html)
    lo = _panel_logik(index_html)
    iface = lo[lo.index("const SUPP_IFACE="):]
    iface = iface[:iface.index("};") + 2]
    for f in ("#22c55e", "#0ea5e9", "#f97316", "#8b5cf6"):
        assert f not in iface, f
    for f in ("#22c55e", "#0ea5e9", "#059669", "rgba(14,165,233", "rgba(245,158,11", "rgba(59,130,246", "rgba(34,197,94"):
        assert f not in ui, f
    assert 'border:"2px solid "+UI.marke' in ui


def test_umkehrprobe_ci_riegel(index_html):
    ui = _haendler(index_html)
    kaputt = ui.replace('border:"2px solid "+UI.marke', 'border:"2px solid #22c55e"', 1)
    assert "#22c55e" in kaputt and "#22c55e" not in ui


def _sync_verstoss(ts):
    s = ts[ts.index('if (body.action === "sync")'):]
    v = []
    if "const rows: Array<Record<string, unknown>> = [];" in s:
        v.append("Platzhalter rows=[] wieder da")
    if "not_implemented" not in s:
        v.append("kein not_implemented")
    i_null = s.find("if (rows === null)")
    i_ok = s.find('last_sync_status: "success"')
    if i_null < 0 or i_ok < i_null:
        v.append("success ohne Download-Pruefung")
    return v


def test_supplier_sync_meldet_keinen_scheinerfolg():
    ts = open(os.path.join(WURZEL, "supabase", "functions", "supplier-sync", "index.ts"),
              encoding="utf-8").read()
    assert not _sync_verstoss(ts), _sync_verstoss(ts)
    assert "return null;" in ts[ts.index("async function downloadArticles("):][:300]
    doku = open(os.path.join(WURZEL, "sql", "DEPLOY_sync_supplier_v3.md"), encoding="utf-8").read()
    assert "v3.9.1016" in doku and "not_implemented" in doku
    # Umkehrprobe
    kaputt = ts.replace("const rows = await downloadArticles(cfg);",
                        "const rows: Array<Record<string, unknown>> = [];", 1)
    assert _sync_verstoss(kaputt)


# v3.9.1016 Hauptlauf: DATANORM-4-Preiseinheit steht in parts[7] (Code 0/1/2/3 = 1/10/100/1000),
# parts[6] ist das Preiskennzeichen (1 brutto / 2 netto) und darf den Preis NICHT teilen.
DN4_PE = _cp850("\r\n".join([
    "V 161126Holter Testdaten                           EUR",
    "A;N;2001;00;Kabelbinder;schwarz;2;2;Stk;1234;R1;WG1;",
    "A;N;2002;00;Rohrschelle;verzinkt;2;0;Stk;990;R1;WG1;",
    "A;N;2003;00;Schraube;M6;1;1;Stk;450;R1;WG1;",
    "",
]))


def _pe_lauf(node_exe, tmp_path, quelle):
    q = tmp_path / "quelle.js"
    q.write_text(quelle, encoding="utf-8")
    d = tmp_path / "dateien.json"
    d.write_text(json.dumps({"pe": [{"name": "DATANORM.001", "b64": _b64(DN4_PE)}]}), encoding="utf-8")
    s = tmp_path / "lauf.js"
    s.write_text(NODE_PARSER, encoding="utf-8")
    p = subprocess.run([node_exe, str(s), str(q), str(d)], capture_output=True, timeout=EPK_TEST_TIMEOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, out + p.stderr.decode("utf-8", "replace")
    return _nach_nr(json.loads(out)["pe"]["arts"])


def test_datanorm4_preiseinheit_aus_code_nicht_aus_preiskennzeichen(index_html, node_exe, tmp_path):
    a = _pe_lauf(node_exe, tmp_path, _helfer_quelle(index_html))
    assert a["2001"]["preis"] == pytest.approx(0.1234), a["2001"]  # 12,34 je 100 Stk
    assert a["2002"]["preis"] == pytest.approx(9.90), a["2002"]    # netto, je 1 Stk - nicht halbiert
    assert a["2003"]["preis"] == pytest.approx(0.45), a["2003"]    # 4,50 je 10 Stk


def test_umkehrprobe_alte_preiseinheit_wird_erkannt(index_html, node_exe, tmp_path):
    alt = index_html.replace('pe=({"0":1,"1":10,"2":100,"3":1000})[(parts[7]||"").trim()]||1;', "pe=parseInt(parts[6])||1;", 1)
    assert alt != index_html
    a = _pe_lauf(node_exe, tmp_path, _helfer_quelle(alt))
    assert a["2002"]["preis"] != pytest.approx(9.90)
