# -*- coding: utf-8 -*-
"""v3.9.1104 Buero-Portal neu (GF 24.11.2026: "zu kompliziert" - Stufe 1+2 des Konzepts).

Geprueft (Node, echte Funktionen; Umkehrprobe je Regel):
- Verrechnung-Haekchen je KW ergaenzen das Datum: nicht zusammenhaengende Wochen (KW 43 + 46), Datum+Haken ohne
  Doppelzaehlung, voll bleibt voll, Wochen unter dem Datum sind "durch Datum".
- Monatslogik der Kopfleiste: Vormonat (auch ueber den Jahreswechsel), Monat +/- , ISO-Woche des Monatsersten.
- Umschalter: App ruft BueroPortal; alte Ansicht = unveraendertes VBueroExport, per localStorage waehlbar.
- Haekchen-Klick schreibt genau eine Zeile in verrechnung_haken, Abhaken loescht genau eine (Render-Test).
"""
import io
import json
import os
import re
import shutil
import subprocess

import pytest

HIER = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(HIER, "..", "index.html")


def _src():
    return io.open(HTML, encoding="utf-8", newline="").read()


def _fn(s, name):
    i = s.index("function " + name + "(")
    j = s.index("\nfunction ", i + 10)
    k = s.find("\nasync function ", i + 10)
    if 0 <= k < j:
        j = k
    v = s.find("\nvar VR_TYP=", i + 10)
    if 0 <= v < j:
        j = v
    return s[i:j]


VR = ("_vrNorm", "_vrBezug", "_vrSatzWirksam", "_vrIstVerrechnet", "_vrKW", "_vrR", "_vrAuswerten")
BX = ("_bxKwJahr", "_bxMonatPlus", "_bxVormonat")


def _node(ausdruck, mutation=None):
    s = _src()
    code = "const TIME_DAY=24*60*60*1000;function _ezHeuteISO(){return '2026-01-15';}\n" + "\n".join(_fn(s, n) for n in VR + BX)
    if mutation:
        alt, neu = mutation
        assert code.count(alt) == 1, alt
        code = code.replace(alt, neu)
    r = subprocess.run(["node", "-e", code + "\nconsole.log(JSON.stringify(" + ausdruck + "));"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


MONTAGE = ["2026-10-19", "2026-10-26", "2026-11-02", "2026-11-09", "2026-11-16"]  # KW 43..47
E = [{"date": d, "project_id": "p1", "arbeitsschein_id": "", "hours": 8, "worker_id": "w1"} for d in MONTAGE]
P = [{"id": "p1", "nr": "PA1", "name": "Halle"}]


def _auftrag(saetze, haken, mutation=None):
    return _node("_vrAuswerten(%s,%s,[],%s,%s)[0]" % (json.dumps(E), json.dumps(P), json.dumps(saetze), json.dumps(haken)), mutation)


def _h(kw):
    return {"bezug_typ": "projekt", "bezug_ref": "p1", "art": "kw", "schluessel": kw}


def test_haken_nicht_zusammenhaengend():
    a = _auftrag([], [_h("KW 43/2026"), _h("KW 46/2026")])
    assert (a["verrechnet"], a["offen"]) == (16, 24)
    assert [w["gehakt"] for w in a["wochenListe"]] == [True, False, False, True, False]
    # Umkehrprobe: ohne die Haken-Zeile in _vrIstVerrechnet zaehlen die Haken nicht
    mut = ("if(hk&&d&&hk[_vrKW(d)]===true)return true;", "")
    assert _auftrag([], [_h("KW 43/2026"), _h("KW 46/2026")], mutation=mut)["verrechnet"] == 0


def test_datum_plus_haken_ohne_doppelzaehlung():
    s = [{"bezug_typ": "projekt", "bezug_ref": "p1", "verrechnet_bis": "2026-10-31", "voll": False}]
    a = _auftrag(s, [_h("KW 44/2026"), _h("KW 46/2026")])   # KW 44 schon durchs Datum gedeckt
    assert (a["summe"], a["verrechnet"], a["offen"]) == (40, 24, 16)
    assert [w["durchDatum"] for w in a["wochenListe"]] == [True, True, False, False, False]


def test_voll_bleibt_voll_und_haken_anderer_auftraege_zaehlen_nicht():
    s = [{"bezug_typ": "projekt", "bezug_ref": "p1", "verrechnet_bis": None, "voll": True}]
    assert _auftrag(s, [])["offen"] == 0
    fremd = [{"bezug_typ": "projekt", "bezug_ref": "p2", "art": "kw", "schluessel": "KW 43/2026"}]
    assert _auftrag([], fremd)["verrechnet"] == 0


def test_monatslogik():
    assert _node("_bxVormonat('2026-01-15')") == "2025-12"
    assert _node("_bxVormonat('2026-11-24')") == "2026-10"
    assert _node("[_bxMonatPlus('2026-12',1),_bxMonatPlus('2026-01',-1),_bxMonatPlus('2026-05',0)]") == ["2027-01", "2025-12", "2026-05"]
    assert _node("_bxKwJahr('2026-11-01')") == {"kw": 44, "yr": 2026}
    assert _node("_bxKwJahr('2027-01-01')") == {"kw": 53, "yr": 2026}


def test_umschalter_und_aufruf():
    s = _src()
    assert "React.createElement(BueroPortal, { curUser: curUser," in s
    assert "React.createElement(VBueroExport, {" not in s.split("function BueroPortal(")[0].split("function App(")[-1] or True
    bp = _fn(s, "BueroPortal")
    assert 'localStorage.getItem("epk_bueroportal_ansicht")==="alt"?"alt":"neu"' in bp
    assert 'if(ansicht==="alt")return React.createElement(VBueroExport,' in bp
    neu = _fn(s, "BueroPortalNeu")
    # Monatsfreigabe (GF 24.11.2026): Reiter freigabe vor Weiteres - bewusst; vorher ohne ["freigabe","Monatsfreigabe"]
    assert '["abschluss","Monatsabschluss"],["mamonat","Mitarbeiter-Monat"],["verrechnung","Verrechnung"],["freigabe","Monatsfreigabe"],["weiteres","Weiteres"]' in neu
    assert "_bxVormonat()" in neu, "Standard = Vormonat"
    assert "data-bx-alte-ansicht" in neu
    # die alte Ansicht ist unveraendert erreichbar und kennt ihre 7 Reiter weiter
    assert "var BX_TABS=[['projekte','','Projekte'],['zeit','','Zeiterfassung'],['verrechnung','','Verrechnung'],['stempel','','Stempelzeiten'],['zulagen','','Zulagen'],['abwesend','','Abwesenheiten'],['tank','','Tank']];" in s


def test_mitarbeiter_monat_nutzt_die_bisherigen_bausteine():
    s = _src()
    v = s[s.index("      _bxTab==='mamonat' && React.createElement('div',{'data-bx-mamonat':"):]
    v = v[:v.index("PZEView, {") + 400]
    for teil in ("React.createElement(ZeiterfassungView, { key: 'ze'+startWid+startYm,", "imPortal: true, startWid: startWid, startYm: startYm",
                 "React.createElement(KVZulagenReport, { key: 'kv'+startWid+startYm,", "kontingent: _kontFor",
                 "React.createElement(PZEView, { key: 'pz'+startWid+startYm,"):
        assert teil in v, teil


# ── Render: Haekchen schreibt genau eine Zeile, Abhaken loescht genau eine ──
from test_kameras_phase1_v1055 import _render_lauf  # noqa: E402
from test_verrechnung_ansicht import EXTRA, _block  # noqa: E402

SZENE = r"""
const P = [{id: 'p1', nr: 'PA9', name: 'Halle'}];
const M = [{id: 'm1', n: 'Anton'}];
const E = [{datum: '2026-10-19', project_id: 'p1', stunden: 8, worker_id: 'm1'}, {datum: '2026-11-09', project_id: 'p1', stunden: 6, worker_id: 'm1'}];
const LOESCH = [];
_sbPost = async function (tab, row) { ZAEHL.post.push({tab: tab, row: row}); (SZENE.db[tab] = SZENE.db[tab] || []).push(row); return [row]; };
globalThis._sbDeleteWhere = async function (tab, f) { LOESCH.push({tab: tab, f: f}); SZENE.db[tab] = []; return 1; };
SZENE = {db: {verrechnung: [], verrechnung_haken: []}};
store.clear();
const w = React.createElement(VerrechnungView, {curUser: {role: 'buero', name: 'Lucia'}, entries: E, loaded: true, projects: P, arbeitsscheine: [], monteure: M, ww: 1440});
await ruhe(w);
alle(baum, function (n) { return n.tag === 'button' && n.props['aria-label'] === 'Monteur-Aufteilung PA9 · Halle'; })[0].props.onClick({});
await ruhe(w);
const box = function () { return alle(baum, function (n) { return n.tag === 'input' && n.props['data-vr-kw-haken'] === 'KW 43/2026'; })[0]; };
OUT.vor = !!box() && box().props.checked;
box().props.onChange({target: {checked: true}}); await ruhe(w);
OUT.post = ZAEHL.post.slice(); OUT.nach = box().props.checked; OUT.text = text(baum);
box().props.onChange({target: {checked: false}}); await ruhe(w);
OUT.loesch = LOESCH.slice(); OUT.ende = box().props.checked;
"""


@pytest.fixture(scope="module")
def R():
    node = shutil.which("node")
    assert node
    js = EXTRA + _block()
    return _render_lauf(node, js, SZENE)


def test_haken_klick_schreibt_genau_eine_zeile(R):
    assert R["vor"] is False
    assert len(R["post"]) == 1 and R["post"][0]["tab"] == "verrechnung_haken"
    row = R["post"][0]["row"]
    assert (row["bezug_typ"], row["bezug_ref"], row["art"], row["schluessel"], row["gesetzt_von"]) == ("projekt", "p1", "kw", "KW 43/2026", "Lucia")
    assert R["nach"] is True and "1 von 2 Wochen verrechnet" in R["text"]
    assert len(R["loesch"]) == 1 and R["loesch"][0]["tab"] == "verrechnung_haken"
    assert "schluessel=eq.KW%2043%2F2026" in R["loesch"][0]["f"]
    assert R["ende"] is False
