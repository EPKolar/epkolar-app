"""v3.9.483 — KW-Nav: benannter _getMaxKW(year)-Helper (52/53) statt hartem Min in allen ▶-Buttons."""
import pathlib

SRC = pathlib.Path(__file__).resolve().parent.parent / "index.html"
HTML = SRC.read_text(encoding="utf-8")


def test_getmaxkw_helper_present():
    # benannter, wiederverwendbarer Helper (28.12. liegt immer in der letzten ISO-Woche → 52 oder 53)
    assert "const _getMaxKW=(year)=>{const d=new Date(year,11,28);" in HTML, "_getMaxKW(year)-Helper fehlt"


def test_kw_nav_buttons_use_getmaxkw():
    assert "switchKw(Math.min(_getMaxKW(yr),kw+1))" in HTML, "Wochenplanung-▶ nutzt nicht _getMaxKW"
    assert "setKw(k=>Math.min(_getMaxKW(yr),k+1))" in HTML, "Wochenbericht-▶ nutzt nicht _getMaxKW"
    assert "setCalKw(k=>Math.min(_getMaxKW(isoWY()),k+1))" in HTML, "Zeiterfassung-KW-▶ nutzt nicht _getMaxKW"


def test_no_hardcoded_kw_nav_cap():
    assert "Math.min(52,kw+1)" not in HTML, "hartes Math.min(52,kw+1) noch vorhanden"
    assert "Math.min(53,k+1)" not in HTML, "hartes Math.min(53,k+1) noch vorhanden"
