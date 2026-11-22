# -*- coding: utf-8 -*-
"""PROJ-HANDY - Befunde vom echten Handy (Samsung A55, live v3.9.1003).

P4   Fortschritts-Regler in der Projektliste hat beim Scrollen Daten geaendert.
PR8  "Letzte Eintraege" zeigte die AELTESTEN Buchungen (date.desc + slice(-6)).
PR11 Maengel: Verantwortlich still monteure[0], Frist = heute, Formular zuerst.
PR9  Plaene: Abzeichen 7 = Zahl konfigurierter Ebenen; Unterreiter nur Emoji.
PR2  Reiter "Uebersicht".
PR6  Stunden einheitlich mit Komma (nur Anzeige).

Jeder Riegel hat eine Umkehrprobe: der alte Wortlaut muss ihn rot machen.
"""
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn  # noqa: E402


@pytest.fixture(scope="module")
def src():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


def _fn(src, name, code_only=False):
    b = _extract_fn(src, name)
    assert b, "%s nicht gefunden - das ist rot, nicht gruen." % name
    if code_only:
        # Die Aenderungskommentare zitieren den alten Wortlaut absichtlich -
        # ein Abwesenheits-Riegel darf nur den CODE lesen.
        b = re.sub(r"/\*.*?\*/", "", b, flags=re.S)
    return b


# ── P4 ────────────────────────────────────────────────────────────────────

def _liste_aendert_fortschritt(rumpf):
    """True, wenn die Projektliste ausserhalb von saveProject einen
    Fortschritt schreibt oder einen Regler traegt."""
    if re.search(r"type:\s*\"range\"", rumpf):
        return True
    return bool(re.search(r"body:\{fortschritt:", rumpf))


def test_p4_liste_hat_keinen_regler_und_schreibt_keinen_fortschritt(src):
    rumpf = _fn(src, "ProjList", code_only=True)
    assert not _liste_aendert_fortschritt(rumpf), (
        "Die Projektliste kann wieder per Regler/Wisch den Fortschritt aendern.")


def test_p4_umkehrprobe_alter_regler_wird_erkannt():
    alt = ("React.createElement('input', { type: \"range\", min: 0, max: 100, "
           "onTouchEnd: e=>{SQ.push({url:\"/api/projects/\"+p.id,method:\"PUT\","
           "body:{fortschritt:v}})}})")
    assert _liste_aendert_fortschritt(alt)


def test_p4_genau_ein_weg_bleibt_das_formular(src):
    rumpf = _fn(src, "ProjList")
    assert '"Fortschritt %"' in rumpf, "Das Bearbeiten-Feld fuer den Fortschritt fehlt."
    # Render-Funde 1096: ZahlEingabe + _ganzZahl statt parseInt je Tastendruck ("12,5" wurde 100); die Begrenzung 0..100 bleibt
    assert "Math.min(100,Math.max(0,_ganzZahl(e.target.value)||0))" in rumpf
    assert "parseInt(e.target.value)" not in rumpf
    # Kein anderer Ort der App schreibt projects.fortschritt per PUT.
    assert len(re.findall(r"body:\{fortschritt:", src)) == 0


def test_p4_balken_mit_prozent_bleibt_als_anzeige(src):
    rumpf = _fn(src, "ProjList")
    assert 'width:fPct+"%"' in rumpf


# ── P6 / P8 ───────────────────────────────────────────────────────────────

def test_p6_suchfeld_laesst_der_lupe_platz(src):
    rumpf = _fn(src, "ProjList")
    # v3.9.1006: paddingLeft:34 wirkte am Geraet NIE - die Handy-Regel
    # input:not([type=checkbox]):not([type=radio]){padding:8px !important} schlug es.
    # Jetzt traegt das Feld das Suchfeld-Muster epk-suche (Lupe als Hintergrund, 38 px,
    # Selektor 0,3,1); gemessen 360/412 px: Lupe endet 11 px vor dem Text.
    assert "React.createElement('input', { className: \"epk-suche\", value: q," in rumpf
    assert 'input.epk-suche:not([type="checkbox"]):not([type="radio"]){padding-left:38px !important}' in src


def test_p8_kennzahlen_nur_einmal(src):
    rumpf = _fn(src, "ProjList")
    assert '"Stunden gesamt: "' not in rumpf, "Der doppelte Kennzahlen-Kasten ist zurueck."
    assert 'fmt$(_kz.betrag)' in rumpf, "Die Kopfzeile ist weg."


# ── PR8 ───────────────────────────────────────────────────────────────────

def test_pr8_letzte_eintraege_sortiert_absteigend(src):
    rumpf = _fn(src, "VDash", code_only=True)
    assert "pe.slice(-6).reverse()" not in rumpf, (
        "slice(-6) setzt aufsteigende Reihenfolge voraus - geladen wird date.desc.")
    assert ".slice(0,6).map(x=>{" in rumpf
    assert 'return _da<_db?1:-1' in rumpf


def test_pr8_ladereihenfolge_ist_absteigend(src):
    """Die Ursache: wird hier je auf asc umgestellt, waere der alte Code
    zufaellig richtig gewesen - der neue bleibt in beiden Faellen richtig."""
    assert 'getEntries: function() { return _sbGetOrder("time_entries","date.desc"); }' in src


NODE = shutil.which("node")


@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_pr8_sortierung_im_lauf(src):
    rumpf = _fn(src, "VDash")
    m = re.search(r"pe\.slice\(\)\.sort\((\(a,b\)=>\{.*?\})\)\.slice\(0,6\)", rumpf)
    assert m
    js = (
        "const cmp=" + m.group(1) + ";"
        "const pe=[{date:'2026-03-10',von:'07:00',id:'alt1'},{date:'2026-11-12',von:'07:00',id:'n2'},"
        "{date:'2026-03-11',von:'07:00',id:'alt2'},{date:'2026-11-12',von:'12:30',id:'n1'},"
        "{date:'2026-11-10',von:'',id:'n3'}];"
        "console.log(pe.slice().sort(cmp).slice(0,3).map(x=>x.id).join(','));"
        # Umkehrprobe: der alte Ausdruck auf date.desc-Daten liefert die aeltesten.
        "const desc=pe.slice().sort(cmp);"
        "console.log(desc.slice(-2).reverse().map(x=>x.id).join(','));"
    )
    out = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    neu, alt = out.stdout.strip().splitlines()
    assert neu == "n1,n2,n3"
    assert alt == "alt1,alt2", "Umkehrprobe: der alte Ausdruck muesste die aeltesten zeigen."


# ── PR6 ───────────────────────────────────────────────────────────────────

@pytest.mark.skipif(not NODE, reason="node fehlt")
def test_pr6_stunden_mit_komma(src):
    m = re.search(r"function _projStdDE\(v,d\)\{.*?\}\}", src)
    assert m
    js = m.group(0) + ";console.log([_projStdDE(617.4),_projStdDE(617),_projStdDE('x'),_projStdDE(7.75,2)].join('|'));"
    out = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "617,4|617,0|0,0|7,75"


def test_pr6_projektansicht_ohne_punkt_stunden(src):
    rumpf = _fn(src, "VDash")
    assert not re.search(r"_n\([^;]*?\)\s*(\+\s*)?,?\s*\"h\"", rumpf), (
        "In der Uebersicht steht wieder eine Stundenzahl mit _n (Punkt).")
    # Der Excel-Export behaelt seine Zahl (Exporte sind ausgenommen).
    assert "_n((parseFloat(x.hours||x.stunden)||0),2),p.nr,p.kunde,p.matchcode]" in _fn(src, "VExport")


# ── PR11 ──────────────────────────────────────────────────────────────────

def test_pr11_keine_stille_vorbelegung(src):
    rumpf = _fn(src, "VMang", code_only=True)
    assert "(monteure[0]||{}).id" not in rumpf, (
        "Verantwortlich ist wieder still mit dem ersten Listeneintrag vorbelegt.")
    assert "const [worker,setWorker]=_react.useState.call(void 0, \"\");" in rumpf
    assert '"— wählen —"' in rumpf
    assert "useState.call(void 0, td2());const [prio" not in rumpf, "Frist ist wieder heute."
    assert "_mgFristVorschlag()" in rumpf


def test_pr11_umkehrprobe():
    alt = 'const [worker,setWorker]=_react.useState.call(void 0, (monteure[0]||{}).id||"");'
    assert "(monteure[0]||{}).id" in alt


def test_pr11_formular_erst_nach_plus_mangel(src):
    rumpf = _fn(src, "VMang")
    i_knopf = rumpf.find('"+ Mangel")')
    i_form = rumpf.find("mgFormAuf&&React.createElement('div'")
    assert i_knopf > 0 and i_form > 0
    assert rumpf.find("setMgFormAuf(true)") > 0
    assert rumpf.find("setMgFormAuf(false);if(window.__toast)") > 0, "Nach dem Anlegen schliesst das Formular nicht."


def test_pr11_review_verlangt_wahl(src):
    rumpf = _fn(src, "VMang")
    assert "if(!reviewWorker){" in rumpf


# ── PR9 / PR2 ─────────────────────────────────────────────────────────────

def test_pr9_unterreiter_beschriftet_und_ebenen_ohne_zaehler(src):
    rumpf = _fn(src, "VPlan", code_only=True)
    assert 'c:layers.length' not in rumpf, "Ebenen-Reiter zaehlt wieder die konfigurierten Ebenen."
    # Plaene Stufe 1 NACHGEZOGEN: Unterreiter-Leiste und Ebenen-Chips ueber dem Plan sind auf Auftrag weg
    # ("Plan zuerst": eine Kopfzeile, Ebenen im Menue). Die PR9-Zusagen bleiben geprueft: die Wege haben
    # Worte (Menuepunkte mit Text) und Ebenen zaehlen nur, was dort liegt (Tickets je Ebene), nie die Zahl
    # der konfigurierten Ebenen.
    assert 'isMob?t.k:t.l' not in rumpf
    assert '_mPunkt("liste","Alle Tickets (Liste)"' in rumpf and '_mPunkt("ordner","Planverwaltung"' in rumpf
    assert '_mPunkt("ebenen","Ebenen verwalten"' in rumpf
    assert "const cnt=allTickets.filter(t=>(t.gewerk||t.layer)===l.id).length" in rumpf
    assert 'plans.length>0&&layers.map(' in rumpf, "Ebenen ohne Plan anzubieten waere wieder der PR9-Fehler."


def test_pr2_reiter_heisst_uebersicht_mit_umlaut(src):
    assert '["dashboard","Uebersicht"]' not in src
    assert '["dashboard","Übersicht"]' in src
