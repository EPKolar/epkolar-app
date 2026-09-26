# -*- coding: utf-8 -*-
"""v3.9.950 - drei Schreibweisen fuer denselben Austritt, und eine widerspricht.

DER BEFUND, HIER GEMESSEN STATT GELESEN
───────────────────────────────────────
`.austritt` wird im Code an 24 Stellen gelesen, in DREI Schreibweisen:

  (1) `_maIstEhemalig(m,h)`  ->  `m.austritt && slice(0,10) < h`
      Die kanonische Form. Eine der sieben byte-identisch zu haltenden
      Funktionen.

  (2) `(!m.austritt || String(m.austritt).slice(0,10) >= heute)`
      Die Umkehrung von (1), ausgeschrieben. Fuenf Stellen. Gleichwertig.

  (3) `!String(m.austritt||'').trim()`
      Zwei Stellen. Sie schliesst JEDEN mit einem Austrittsdatum aus - auch
      einen, der erst NAECHSTEN MONAT geht.

Fuer einen Austritt in der ZUKUNFT widersprechen sich (2) und (3): (2) sagt
"noch da", (3) sagt "weg". Diese Datei fuehrt die drei Praedikate unter Node
AUS und zeigt den Widerspruch an Zahlen, statt ihn zu behaupten.

WARUM DAS NICHT NUR KOSMETIK IST
Die beiden Stellen mit (3) sind keine Randnotiz:
  * die Spaltenquelle fuer Inline-Anzeige, Modal UND Excel im Stundenzettel
  * `_kapMont`, die Kapazitaetsliste im ChefDashboard
Wer am 20. eines Monats zum Monatsletzten kuendigt, fehlt dort ab sofort -
in der Kapazitaetsplanung fuer die naechsten zehn Arbeitstage, die er noch
arbeitet.

GEPRUEFT WIRD DURCH AUSFUEHREN
Der Rumpf von `_maIstEhemalig` wird woertlich aus index.html geschnitten und
unter Node gegen die beiden anderen Schreibweisen gefahren. Ein Riegel, der
nur Zeichenketten vergleicht, koennte nicht zeigen, DASS sie sich
unterscheiden - nur, dass sie anders geschrieben sind.
"""
import io
import json
import subprocess
import tempfile
import os

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8",
                   newline="").read()


@pytest.fixture(scope="module")
def urteile(roh):
    """Faehrt die drei Schreibweisen unter Node gegen fuenf Faelle."""
    i = roh.index("function _maIstEhemalig(m,heute){")
    j = roh.index("}", roh.index("return !!(m&&m.austritt", i)) + 1
    fn = roh[i:j]
    assert "m.austritt" in fn and len(fn) < 400, len(fn)

    prog = """
function _ezHeuteISO(){ return "2026-09-26"; }
__FN__
// (2) die ausgeschriebene Umkehrung, wie an fuenf Stellen im Code
function nochAktiv2(m){
  const h = _ezHeuteISO();
  return (!m.austritt || String(m.austritt).slice(0,10) >= h);
}
// (3) die dritte Schreibweise, wie an zwei Stellen im Code
function nochAktiv3(m){
  return !String(m.austritt||'').trim();
}
const FAELLE = {
  kein_datum:        {austritt: ""},
  austritt_gestern:  {austritt: "2026-09-25"},
  austritt_heute:    {austritt: "2026-09-26"},
  austritt_morgen:   {austritt: "2026-09-27"},
  austritt_naechster_monat: {austritt: "2026-10-31"}
};
const aus = {};
for (const [name, m] of Object.entries(FAELLE)) {
  aus[name] = {ehemalig1: _maIstEhemalig(m),
               aktiv2: nochAktiv2(m),
               aktiv3: nochAktiv3(m)};
}
process.stdout.write(JSON.stringify(aus));
""".replace("__FN__", fn)

    tmp = tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w",
                                      encoding="utf-8")
    try:
        tmp.write(prog)
        tmp.close()
        r = subprocess.run(["node", tmp.name], capture_output=True, text=True,
                           timeout=60)
        assert r.returncode == 0, "Node: %s" % (r.stderr[-800:],)
        return json.loads(r.stdout)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def test_koeder_die_kanonische_form_unterscheidet_ueberhaupt(urteile):
    """Wenn `_maIstEhemalig` fuer alle fuenf Faelle dasselbe sagt, misst
    diese Datei nichts."""
    werte = {k: v["ehemalig1"] for k, v in urteile.items()}
    assert len(set(werte.values())) == 2, (
        "KOEDER STUMM: _maIstEhemalig liefert fuer alle Faelle %r - dann sagt "
        "keine Zeile hier etwas." % werte)
    assert urteile["austritt_gestern"]["ehemalig1"] is True
    assert urteile["kein_datum"]["ehemalig1"] is False


def test_die_zweite_schreibweise_ist_die_umkehrung_der_ersten(urteile):
    """Fuenf Stellen im Code benutzen sie. Sie darf sich von (1) nicht
    unterscheiden, sonst gibt es nicht drei Schreibweisen, sondern drei
    Regeln."""
    abweichend = {k: v for k, v in urteile.items()
                  if v["aktiv2"] == v["ehemalig1"]}
    assert not abweichend, (
        "Die ausgeschriebene Umkehrung stimmt nicht mit _maIstEhemalig "
        "ueberein: %r" % abweichend)


def test_die_dritte_schreibweise_widerspricht_bei_zukuenftigem_austritt(urteile):
    """DER BEFUND, an Zahlen - und er bleibt hier stehen, auch nachdem die
    zwei Stellen behoben sind.

    Fuer einen Austritt in der Zukunft sagt (2) "noch da" und (3) "weg". Diese
    Prueffunktion definiert (3) SELBST und zeigt damit die Arithmetik, nicht
    den Stand des Codes - dass die Schreibweise aus index.html verschwunden
    ist, prueft `test_es_gibt_die_dritte_schreibweise_nicht_mehr_im_code`.
    Beides zusammen ist der Beleg: die eine Zeile sagt, WARUM es falsch war,
    die andere, DASS es weg ist. Ohne die erste steht in einem Jahr niemand
    mehr davor und versteht, warum die Vereinheitlichung wichtig war.
    """
    for fall in ("austritt_morgen", "austritt_naechster_monat"):
        d = urteile[fall]
        assert d["aktiv2"] is True, (
            "%s: die kanonische Regel sagt nicht 'noch da' - dann ist der "
            "ganze Befund anders als beschrieben." % fall)
        assert d["aktiv3"] is False, (
            "%s: `!String(m.austritt||'').trim()` sagt jetzt 'noch da'. Das "
            "kann eigentlich nicht sein - dieses Praedikat ist in DIESER "
            "Datei definiert, nicht in index.html. Schlaegt es hier an, ist "
            "der Pruefstand kaputt, nicht die App." % fall)


def test_es_gibt_die_dritte_schreibweise_nicht_mehr_im_code(roh):
    """Die zwei Stellen sind auf `_maIstEhemalig` gezogen.

    Es sind keine Randnotizen: die Spaltenquelle fuer Inline, Modal UND Excel
    im Stundenzettel, und die Kapazitaetsliste im ChefDashboard. Wer am 20.
    zum Monatsletzten kuendigt, fehlte dort ab sofort - in der Planung fuer
    die zehn Arbeitstage, die er noch arbeitet.
    """
    import re
    import sys
    sys.path.insert(0, str(WURZEL / "scripts"))
    from code_scan import ist_code, eichen
    ok, gefunden, erwartet = eichen(roh)
    assert ok, "Eichung gescheitert (%d von %d)" % (gefunden, erwartet)
    feld = ist_code(roh)
    treffer = [roh.count("\n", 0, m.start()) + 1
               for m in re.finditer(r"!String\(m\.austritt\|\|['\"]{2}\)\.trim\(\)",
                                    roh)
               if feld[m.start()]]
    assert not treffer, (
        "Die dritte Schreibweise steht wieder im Code (Zeilen %s). Sie "
        "schliesst jeden mit Austrittsdatum aus, auch einen zukuenftigen - "
        "und widerspricht damit den anderen 22 Stellen." % treffer)


def test_die_kanonische_funktion_ist_unveraendert(roh):
    """Sie ist eine der sieben byte-identisch zu haltenden Funktionen; das
    haelt scripts/md5_geschuetzt.py fest. Hier nur der Rumpf als Koeder."""
    assert "return !!(m&&m.austritt&&String(m.austritt).slice(0,10)<h);" in roh, (
        "Der Rumpf von _maIstEhemalig hat sich geaendert.")
