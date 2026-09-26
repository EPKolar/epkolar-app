# -*- coding: utf-8 -*-
"""v3.9.938 Phase A, Punkt 2 - Datenfrische fuer Projekte und Mitarbeiter.

DAS PROBLEM
───────────
`projects` und `monteure` wurden NUR im Boot-Effekt vom Server gelesen. Blieb
der Tab offen, arbeitete man eine ganze Sitzung auf dem Stand vom Anmelden -
die Aenderung des Kollegen kam nie an. Selbst ein perfekter Merge hilft dann
nicht: es gibt nichts zu mergen.

WAS GEBAUT IST - UND WARUM GENAU SO
───────────────────────────────────
Nachgeladen wird, indem DERSELBE Boot-Effekt erneut laeuft: sein
Abhaengigkeitsfeld traegt jetzt `_frischeZaehler`, und ein
visibilitychange-Lauscher erhoeht ihn.

Der Grund gegen einen eigenen Abrufpfad: `API.getProjects()` und
`API.getWorkers()` stehen im Promise.all dieses Effekts, und der Pending-Merge
aus v3.9.847/848 (die Mengen `_v848PendingProjPosts` und ihre Zwillinge)
steckt INLINE in ihm. Ihn herauszuloesen waere ein Umbau genau an der Stelle,
die lokale Bearbeitungen vor dem Ueberschreiben schuetzt. So bleibt es EIN
Ladepfad und EIN Merge - keine zweite Wahrheit, die driften kann.

Ob nachgeladen wird, entscheidet `_dispoRefreshEntscheidung` aus v3.9.761 -
woertlich dieselbe reine Funktion, die die Dispo benutzt.

WAS DIESE RIEGEL NICHT KOENNEN
──────────────────────────────
Sie messen den Quelltext. Dass wirklich genau EINMAL nachgeladen wird und
NICHT ohne Sichtbarkeitswechsel, misst `scripts/frische_probe.py` am
laufenden Programm - dort werden die Aufrufe gezaehlt. Gemessen (26.09.):

    Start                                   2 Listenladungen
    35 s Ruhe                              +0   -> kein Poll
    sichtbar werden                        +2   -> projects + workers
    sofort noch einmal                     +0   -> die 60-s-Schranke
    mit Fokus im Feld, Schranke abgelaufen +0   -> 'defer'
    ohne Fokus, gleiche Bedingungen        +2   -> Gegenprobe

Die letzte Zeile ist die wichtigste: ohne sie koennte das +0 darueber auch
bedeuten, dass ueberhaupt nichts mehr laedt.
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def roh():
    return io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()


# ── Der Lauscher ──────────────────────────────────────────────────────────

def test_es_gibt_genau_einen_frische_lauscher(roh):
    assert roh.count("setFrischeZaehler(n=>n+1)") == 1, (
        "Der Zaehler wird %dx erhoeht - mehr als eine Stelle heisst mehr als "
        "ein Nachlauf." % roh.count("setFrischeZaehler(n=>n+1)"))
    assert roh.count("const [_frischeZaehler,setFrischeZaehler]") == 1


def test_der_lauscher_haengt_an_visibilitychange_und_nicht_an_einem_timer(roh):
    """Kein zweiter Poll - das war eine ausdrueckliche Auflage."""
    i = roh.find("const _was=_dispoRefreshEntscheidung(_sichtbar")
    assert i > 0, "Die Entscheidung im Lauscher wurde nicht gefunden."
    block = roh[max(0, i - 900):i + 700]
    assert 'addEventListener("visibilitychange",_onVis)' in block, (
        "Der Lauscher haengt nicht an visibilitychange.")
    for timer in ("setInterval", "setTimeout"):
        assert timer not in block, (
            "Im Frische-Lauscher steht ein %s - das waere der zweite Poll, den "
            "es nicht geben soll." % timer)


def test_der_lauscher_raeumt_sich_wieder_ab(roh):
    i = roh.find('addEventListener("visibilitychange",_onVis)')
    assert i > 0
    assert 'removeEventListener("visibilitychange",_onVis)' in roh[i:i + 260], (
        "Der Lauscher wird nicht abgeraeumt - bei jedem Neuaufbau kaeme einer "
        "dazu, und dann laedt ein Sichtbarkeitswechsel mehrfach nach.")


# ── Die Entscheidung kommt aus der bestehenden Funktion ───────────────────

def test_die_entscheidung_nimmt_die_funktion_aus_v3_9_761(roh):
    """Keine neue Schwelle, kein zweites Regelwerk."""
    assert "function _dispoRefreshEntscheidung(visible,lastMs,nowMs," \
           "gestureActive,minAgeMs){" in roh, (
        "Die Entscheidungsfunktion aus v3.9.761 ist veraendert oder weg.")
    assert "_dispoRefreshEntscheidung(_sichtbar,_frischeStand.current," in roh, (
        "Der Frische-Lauscher benutzt eine andere Entscheidung.")


def test_die_funktion_steht_vor_ihrer_verwendung_und_im_selben_block(roh):
    """node_check PARST die <script>-Bloecke und fuehrt sie nicht aus. Eine
    Funktion aus einem anderen Block waere syntaktisch tadellos und zur
    Laufzeit ein ReferenceError - bei gruenem Tor. Dieselbe Falle wie die
    TDZ-Faelle in ProjList."""
    bloecke = []
    for m in re.finditer(r"<script\b[^>]*>", roh, re.I):
        e = roh.find("</script>", m.end())
        bloecke.append((m.end(), e if e > 0 else len(roh)))

    def block_von(p):
        for nr, (a, b) in enumerate(bloecke):
            if a <= p < b:
                return nr
        return None

    d = roh.find("function _dispoRefreshEntscheidung")
    v = roh.find("_dispoRefreshEntscheidung(_sichtbar")
    assert d > 0 and v > 0
    assert block_von(d) == block_von(v), (
        "Definition in Block %s, Verwendung in Block %s - zur Laufzeit ein "
        "ReferenceError." % (block_von(d), block_von(v)))
    assert d < v, "Die Funktion steht hinter ihrer Verwendung."


def test_die_altersschranke_ist_benannt_und_nicht_null(roh):
    m = re.search(r"_dispoRefreshEntscheidung\(_sichtbar,_frischeStand\.current,"
                  r"Date\.now\(\),_tipptGrad\(\),(\d+)\)", roh)
    assert m, "Der Aufruf der Entscheidung sieht anders aus als erwartet."
    assert int(m.group(1)) >= 30000, (
        "Die Altersschranke ist nur %s ms - dann kann ein schneller "
        "Tab-Wechsel einen Nachlauf-Sturm ausloesen." % m.group(1))


# ── Der Merge bleibt unangetastet ─────────────────────────────────────────

MERGE_MENGEN = ["_v848PendingProjPosts", "_v848PendingProjPuts",
                "_v847PendingFzgPosts", "_v842PendingWzgPuts"]


@pytest.mark.parametrize("menge", MERGE_MENGEN)
def test_der_reload_merge_ist_unberuehrt(roh, menge):
    """Er ist der Grund, warum ein Nachladen keine lokalen Bearbeitungen
    wegwirft. Der Auftrag sagt ausdruecklich: unangetastet."""
    assert menge in roh, (
        "Die Pending-Menge %s ist weg - dann springt ein noch nicht "
        "gedrainter PUT beim Nachladen auf den Serverstand zurueck." % menge)


def test_der_boot_effekt_laedt_weiterhin_projekte_und_mitarbeiter(roh):
    assert "API.getProjects().catch(()=>null)" in roh, (
        "Der Projektabruf im Boot-Effekt ist veraendert.")
    assert "API.getWorkers().catch(" in roh, (
        "Der Mitarbeiterabruf im Boot-Effekt ist veraendert.")


def test_der_zaehler_haengt_in_der_abhaengigkeitsliste(roh):
    """DER Riegel dieser Stufe: ohne den Eintrag laeuft der Effekt nie erneut,
    und der ganze Lauscher waere wirkungslos - ein Bauteil ohne Weg dorthin."""
    assert "},[curUser,_frischeZaehler]);" in roh, (
        "Der Boot-Effekt haengt nicht an _frischeZaehler - ihn zu erhoehen "
        "bewirkt dann gar nichts.")


def test_es_gibt_genau_eine_stelle_die_den_effekt_neu_ausloest(roh):
    assert roh.count("},[curUser,_frischeZaehler]);") == 1, (
        "%d Effekte haengen am Zaehler - dann loest ein Sichtbarkeitswechsel "
        "mehrere Laeufe aus." % roh.count("},[curUser,_frischeZaehler]);"))


# ── Beim Tippen wird nicht nachgeladen ────────────────────────────────────

def test_beim_tippen_wird_nicht_nachgeladen(roh):
    """Ein Nachlauf mitten im Tippen koennte ein halb gefuelltes Formular neu
    zeichnen. Die Dispo holt das nach dem Gestenende nach; hier wird auf den
    naechsten Sichtbarkeitswechsel gewartet - die vorsichtigere Seite."""
    i = roh.find("const _tipptGrad=()=>")
    assert i > 0, "Die Tipp-Erkennung im Lauscher fehlt."
    block = roh[i:i + 220]
    for tag in ("INPUT", "TEXTAREA", "SELECT"):
        assert tag in block, (
            "Die Tipp-Erkennung sieht %s nicht - dort wird getippt." % tag)
