"""v3.9.700 — PZE-Tagesschleife DST-fest + Doppel-Kommen erkannt (Bug-Hunt Befund 3 + 5).

BEFUND 3 war die teuerste Sorte Kommentar-Lüge: die Schleife trug „Basis 12:00 -> DST-sicher",
war es aber nicht. Nach der Frühjahrsumstellung (Wien: So 29.03.) verschluckte sie den letzten
Tag des Monats — der 31.03. fehlte in Tabelle, Monatssumme, Excel UND PDF. Dieser Test BEWEIST
die Behauptung jetzt (Hausregel v3.9.699): er fährt Node explizit in Europe/Vienna und zeigt,
dass die neue (kalendarische) Schleife 31 Tage liefert und die alte (ms-basierte) nur 30 —
also dass der Test die Regression auch wirklich fangen würde.
"""
import os
import subprocess

import pytest
from conftest import node_exe  # noqa: F401  (fixture)


# Die exakte Iterationslogik aus PZEView (Z. ~9720). _iso ist wortgleich zur Komponente.
_NODE = r"""
const p2=n=>String(n).padStart(2,'0');
const _iso=d=>d.getFullYear()+'-'+p2(d.getMonth()+1)+'-'+p2(d.getDate());
function neu(von,bis){  // v3.9.700: kalendarisch, ISO-Abbruch
  const out=[]; let d=new Date(von+'T12:00:00'); const endK=bis; let g=0;
  while(_iso(d)<=endK && g<400){ out.push(_iso(d)); d.setDate(d.getDate()+1); g++; }
  return out;
}
function alt(von,bis){  // Vorzustand: ms-basiert, Zeitstempel-Vergleich
  const TIME_DAY=24*60*60*1000;
  const out=[]; let d=new Date(von+'T12:00:00'); const end=new Date(bis+'T12:00:00'); let g=0;
  while(d<=end && g<400){ out.push(_iso(d)); d=new Date(d.getTime()+TIME_DAY); g++; }
  return out;
}
const nMaerz=neu('2026-03-01','2026-03-31');
const aMaerz=alt('2026-03-01','2026-03-31');
const nOkt=neu('2026-10-01','2026-10-31');
process.stdout.write(JSON.stringify({
  neu_maerz: nMaerz.length,
  neu_hat_31: nMaerz.includes('2026-03-31'),
  alt_maerz: aMaerz.length,
  neu_okt: nOkt.length,
  neu_okt_dupe: nOkt.length !== new Set(nOkt).size
}));
"""


@pytest.fixture(scope="module")
def dst_result(node_exe):  # noqa: F811
    env = dict(os.environ, TZ="Europe/Vienna")
    r = subprocess.run([node_exe, "-e", _NODE], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    import json
    return json.loads(r.stdout.strip())


def test_neue_schleife_liefert_alle_31_maerztage(dst_result):
    assert dst_result["neu_maerz"] == 31, "Die DST-feste Schleife verliert weiterhin einen Tag im März"
    assert dst_result["neu_hat_31"] is True, "Der 31.03. fehlt — genau der Befund-3-Fehler"


def test_alte_schleife_beweist_die_regression(dst_result):
    """Kontrolle: die alte ms-basierte Schleife liefert unter Europe/Vienna nur 30 Tage.
    Zeigt, dass dieser Test die Regression tatsächlich fängt und nicht in UTC blind wäre."""
    assert dst_result["alt_maerz"] == 30, \
        "Die alte Schleife liefert 31 — dann läuft der Test nicht in einer DST-Zone und beweist nichts"


def test_oktober_rueckstellung_ohne_duplikat(dst_result):
    assert dst_result["neu_okt"] == 31
    assert dst_result["neu_okt_dupe"] is False, "Rückstellung im Oktober erzeugt einen doppelten Tag"


def test_source_iteriert_kalendarisch(index_html):
    """Die Behauptung im Code muss zum Code passen (Hausregel v3.9.699)."""
    assert "d.setDate(d.getDate()+1);guard++;/* v3.9.700" in index_html
    assert "while(_iso(d)<=endK&&guard<400){" in index_html
    # Der alte, driftende Ausdruck darf in der PZE-Schleife nicht mehr stehen:
    assert "d=new Date(d.getTime()+TIME_DAY);guard++;/* Basis 12:00" not in index_html
