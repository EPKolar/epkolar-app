# -*- coding: utf-8 -*-
"""v3.9.744 — Register #24 (P1): km-Wahrheit bei Verwalter-Kunden — PLZ aus dem Arbeitstext.

Sebastian/Chat-Claude (DB-bewiesen): Bei Verwalter-Kunden (NÖ Siedlungswerk u.ä.) sind kund_plz, arbeitsort
UND AK_BAUADR_* ALLE die Rechnungsadresse (z.B. 1100 Wien) — die echte Baustelle steht nur im Text
(arbeitsanweisungen). Die Rechnungs-PLZ verfaelscht km/Fahrzeit/Score. Neue PLZ-Ermittlung je Schein:
  1. arbeitsort enthaelt eine PLZ != kund_plz -> arbeitsort gewinnt (exakt).
  2. sonst Text-Extraktion aus (arbeitsanweisungen + arbeitsort):
     a) PLZ+Ortswort-Muster \\b(\\d{4})\\s+[A-ZAEOEUE][a-z...] (1000-9999) -> PLZ (Schaetzung).
     b) Ortsnamen-Match gegen plz_geo.ort (umlaut-fold + " am/an der ..." abschneiden, wortweise,
        laengster/eindeutiger Treffer) -> PLZ (Schaetzung).
  3. sonst kund_plz. 4. sonst "" (-> "? km").
Text-Treffer sind SCHAETZUNGEN (estimate=true -> "~" + Tooltip "Ort aus Arbeitstext: <Treffer>").

PURER Kern (node-eval): _dispoScheinPlz(arbeitsort, kundPlz, arbeitstext, ortIndex)
  -> {plz, estimate, ort}. ortIndex = [{ort, plz}] aus plz_geo.
"""
import subprocess


def _block(index_html):
    start = index_html.index("var DISPO_RESERVE_MIN=60;")
    end = index_html.index("if(typeof window!=='undefined'){window._dispoAdrKey", start)
    return index_html[start:end]


_OK = u"\nfunction ok(c,n){ if(!c){ console.error('FAIL '+n); process.exit(1);} }\n"
_IDX = u"var IDX=[{ort:'Kirchberg am Wagram',plz:'3470'},{ort:'Zwentendorf',plz:'3435'},{ort:'Fels am Wagram',plz:'3481'},{ort:'Muehlbach Am Manhartsberg',plz:'3472'},{ort:'Krems an der Donau',plz:'3500'}];\n"


def _run(node_exe, tmp_path, js):
    f = tmp_path / "textplz744.js"
    f.write_text(js, encoding="utf-8")
    r = subprocess.run([node_exe, str(f)], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    assert "OK" in r.stdout


def test_s075331_alles_1100_text_kirchberg(index_html, node_exe, tmp_path):
    """S075331: alles 1100, Text '... Kremser Straße 11/3/8, Kirchberg ...' -> Ort-Match Kirchberg -> 3470, Schaetzung."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('1100 Wien','1100','Kremser Straße 11/3/8, Kirchberg — Sicherung defekt',IDX);
ok(r.plz==='3470','Kirchberg aus Text -> 3470 (war '+r.plz+')');
ok(r.estimate===true,'Text-Treffer ist Schaetzung');
ok(/Kirchberg/.test(r.ort||''),'Tooltip-Ort nennt Kirchberg');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_plz_ortwort_muster(index_html, node_exe, tmp_path):
    """'... in 3435 Zwentendorf ...' im Text -> PLZ 3435 (Regex-Stufe 2a), Schaetzung."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('','1100','Anlage in 3435 Zwentendorf pruefen',IDX);
ok(r.plz==='3435','3435 aus PLZ+Ortswort-Muster (war '+r.plz+')');
ok(r.estimate===true,'Schaetzung');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_kein_ortstreffer_faellt_auf_kundplz(index_html, node_exe, tmp_path):
    """'Anlage 2026 kaputt' -> keine PLZ, kein Ortswort -> kund_plz (exakt)."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('','1100','Anlage 2026 kaputt',IDX);
ok(r.plz==='1100','faellt auf kund_plz zurueck (war '+r.plz+')');
ok(r.estimate===false,'kund_plz ist kein Schaetzwert');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_arbeitsort_plz_gewinnt_ohne_tilde(index_html, node_exe, tmp_path):
    """arbeitsort '3481 Fels' + kund_plz 1100 -> 3481 (exakt, keine Tilde)."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('3481 Fels am Wagram','1100','egal',IDX);
ok(r.plz==='3481','arbeitsort-PLZ gewinnt (war '+r.plz+')');
ok(r.estimate===false,'gepflegte arbeitsort-PLZ ist exakt (keine Tilde)');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_umlaut_fold_muehlbach(index_html, node_exe, tmp_path):
    """'Mühlbach'-fold matcht 'Muehlbach Am Manhartsberg' (Umlaut-Fold + ' Am ...' abschneiden)."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('','1100','Störung in Mühlbach beim Trafo',IDX);
ok(r.plz==='3472','Muehlbach-Fold-Match -> 3472 (war '+r.plz+')');
ok(r.estimate===true,'Schaetzung');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)


def test_arbeitsort_gleich_kundplz_kein_gewinn(index_html, node_exe, tmp_path):
    """arbeitsort-PLZ == kund_plz -> KEIN arbeitsort-Gewinn, weiter zu Text/kund_plz."""
    js = _block(index_html) + _IDX + _OK + u"""
var r=_dispoScheinPlz('1100 Wien','1100','nichts Verwertbares hier',IDX);
ok(r.plz==='1100' && r.estimate===false,'arbeitsort==kund -> kund_plz exakt');
console.log('OK');
"""
    _run(node_exe, tmp_path, js)
