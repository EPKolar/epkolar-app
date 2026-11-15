"""v3.9.483 — KW-Nav: benannter _getMaxKW(year)-Helper (52/53) statt hartem Min in allen ▶-Buttons."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_getmaxkw_helper_present():
    # benannter, wiederverwendbarer Helper (28.12. liegt immer in der letzten ISO-Woche → 52 oder 53)
    assert "const _getMaxKW=(year)=>{const d=new Date(year,11,28);" in HTML, "_getMaxKW(year)-Helper fehlt"


def test_kw_nav_buttons_use_getmaxkw():
    # v3.9.1012 Jahreswechsel: der ▶ der Planung klemmt nicht mehr selbst; switchKw rollt ueber
    # _kwZiel, und _kwZiel klemmt gegen _getMaxKW des ZIELjahres (kein hartes 52/53).
    assert "onClick: ()=>switchKw(kw+1)" in HTML, "Wochenplanung-▶ ruft switchKw nicht"
    assert "const _z=_kwZiel(yr,newKw,newYr);const _tYr=_z[0];newKw=_z[1];" in HTML, "Wochenplanung-switchKw nutzt _kwZiel nicht"
    assert "if(k>_getMaxKW(y)){return [y+1,1];}" in HTML and "Math.max(1,Math.min(_getMaxKW(ny),k))" in HTML, "_kwZiel nutzt nicht _getMaxKW"
    assert "setKw(k=>Math.min(_getMaxKW(yr),k+1))" in HTML, "Wochenbericht-▶ nutzt nicht _getMaxKW"
    assert "const _z=_kwZiel(calYr,calKw+1);setCalYr(_z[0]);setCalKw(_z[1]);" in HTML, "Zeiterfassung-KW-▶ nutzt nicht _kwZiel/_getMaxKW"


def test_no_hardcoded_kw_nav_cap():
    assert "Math.min(52,kw+1)" not in HTML, "hartes Math.min(52,kw+1) noch vorhanden"
    assert "Math.min(53,k+1)" not in HTML, "hartes Math.min(53,k+1) noch vorhanden"
