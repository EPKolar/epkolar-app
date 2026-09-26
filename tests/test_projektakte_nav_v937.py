# -*- coding: utf-8 -*-
"""v3.9.937 Stufe 3 - die Navigation der Projektakte.

DER BEFUND
──────────
Die Projektakte hatte zwei Leisten, und beide am falschen Platz:

  .tab-bar        OBEN, die HAUPTNAVIGATION der App - das ist die
                  "Desktop-Topnav auf Mobil" aus dem Befund.
  .mob-shell-nav  UNTEN, fix, die 13 Unterseiten als REINE Emoji-Knoepfe,
                  mit flex-wrap zweireihig (~94 px). Die Bedeutung stand nur
                  im title-Attribut - und ein title sieht niemand, der mit
                  dem Finger bedient.

Mitten in der App wechselte damit das Navigationsmodell.

WAS DIESE RIEGEL SICHERN
────────────────────────
1. Keine der 13 Unterseiten ist verschwunden, umbenannt oder zusammengelegt.
2. Jede traegt ihre Berechtigung (`pm`) unveraendert - hasPerm entscheidet
   weiter, OB sie erscheint.
3. Die fuenf taeglichen stehen vorne, dahinter genau EINE Trennlinie.
4. Die Reiterzeile traegt TEXT, nicht nur Zeichen.
5. Der Maengel-Zaehler nimmt die Formel aus ProjList woertlich.
6. Die Emoji-Leiste unten ist weg, die Hauptnavigation sitzt dort.

WAS DIESE RIEGEL NICHT KOENNEN
──────────────────────────────
Sie messen den Quelltext. Dass man alle 13 Ziele auch ERREICHT, misst
`scripts/projektakte_nav_probe.py` am gerenderten Schirm - dort wird jedes
Ziel einzeln angetippt. Diese Trennung ist Absicht: zweimal in diesem Umbau
war der Quelltext richtig und das Ergebnis falsch (eine TDZ-Verletzung und
eine Schrift, die nirgends benutzt wurde).
"""
import io
import re

import pytest

from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]

import sys
sys.path.insert(0, str(WURZEL / "tests"))
from conftest import _extract_fn  # noqa: E402

DIE_DREIZEHN = [
    ("dashboard", "Dashboard"), ("zeit", "Zeiterfassung"),
    ("berichte", "Berichte"), ("plaene", "Pläne"),
    ("formulare", "Formulare"), ("checklisten", "Checklisten"),
    ("maengel", "Mängel"), ("bautagebuch", "Bautagebuch"),
    ("fotos", "Fotos"), ("material", "Material"),
    ("dokumente", "Dokumente"), ("offa", "OFFA"), ("export", "Export"),
]

TAEGLICH = ["dashboard", "plaene", "maengel", "fotos", "zeit"]


@pytest.fixture(scope="module")
def rumpf():
    s = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    b = _extract_fn(s, "ProjectShell")
    assert b, "ProjectShell nicht gefunden - das ist rot, nicht gruen."
    return b


@pytest.fixture(scope="module")
def nav_liste(rumpf):
    i = rumpf.index("const _allNav=[")
    j = rumpf.index("];", i)
    return rumpf[i:j + 2]


# ── 1. Keine Seite ist verschwunden ───────────────────────────────────────

@pytest.mark.parametrize("kennung,titel", DIE_DREIZEHN)
def test_jede_der_dreizehn_unterseiten_ist_noch_da(nav_liste, kennung, titel):
    assert 'id:"%s"' % kennung in nav_liste, (
        "Die Unterseite %s (%s) ist aus der Navigation verschwunden."
        % (kennung, titel))
    assert 'l:"%s"' % titel in nav_liste, (
        "Die Unterseite %s heisst nicht mehr %r." % (kennung, titel))


def test_es_sind_genau_dreizehn(nav_liste):
    ids = re.findall(r'id:"([^"]+)"', nav_liste)
    assert len(ids) == 13, "%d Unterseiten statt 13: %s" % (len(ids), ids)
    assert len(set(ids)) == 13, "doppelte Kennungen: %s" % ids


# ── 2. Die Berechtigungen sind unveraendert ───────────────────────────────

BERECHTIGUNGEN = ["zeiterfassung", "plaene", "formulare", "maengel",
                  "bautagebuch", "material", "offa", "export"]


@pytest.mark.parametrize("pm", BERECHTIGUNGEN)
def test_jede_berechtigung_haengt_noch_an_ihrer_seite(nav_liste, pm):
    """hasPerm entscheidet, OB eine Seite erscheint. Solche Bedingungen sind
    Tabu - geaendert wird nur das WIE."""
    assert 'pm:"%s"' % pm in nav_liste, (
        "Die Berechtigung %r haengt an keiner Unterseite mehr." % pm)


def test_der_berechtigungsfilter_ist_unberuehrt(rumpf):
    assert "hasPerm(curUser,n.pm)" in rumpf, (
        "Der Berechtigungsfilter ueber die Navigation ist weg.")


# ── 3. Reihenfolge und Trennlinie ─────────────────────────────────────────

def test_die_fuenf_taeglichen_stehen_vorne(nav_liste):
    ids = re.findall(r'id:"([^"]+)"', nav_liste)
    assert ids[:5] == TAEGLICH, (
        "Die ersten fuenf sind %s, erwartet %s. Aus dieser Liste entsteht auch "
        "die Reihenfolge, in der ein WISCH blaettert - sie soll der "
        "Reiterzeile entsprechen." % (ids[:5], TAEGLICH))


def test_genau_eine_trennlinie_und_zwar_nach_den_fuenf(nav_liste):
    stuecke = re.split(r",(?=\{|null)", nav_liste[len("const _allNav=["):-2])
    nulls = [k for k, t in enumerate(stuecke) if t.strip() == "null"]
    assert len(nulls) == 1, "%d Trennlinien statt einer" % len(nulls)
    assert nulls[0] == 5, (
        "Die Trennlinie steht an Position %d statt hinter den fuenf "
        "taeglichen." % nulls[0])


# ── 4. Die Reiterzeile traegt Text ────────────────────────────────────────

def test_die_reiterzeile_hat_fuenf_beschriftete_reiter(rumpf):
    i = rumpf.find("const _pfReiter=[")
    assert i > 0, "Die Reiterliste _pfReiter fehlt."
    block = rumpf[i:rumpf.index("];", i)]
    paare = re.findall(r'\["([^"]+)","([^"]+)"\]', block)
    assert len(paare) == 5, "%d Reiter statt fuenf: %s" % (len(paare), paare)
    assert [p[0] for p in paare] == TAEGLICH, (
        "Die Reiter zeigen auf %s, erwartet %s" % ([p[0] for p in paare], TAEGLICH))
    for _id, l in paare:
        assert l and not re.match(r"^[\W_]+$", l), (
            "Der Reiter %s hat keine Beschriftung." % _id)


def test_mehr_traegt_alles_was_nicht_unter_die_fuenf_faellt(rumpf):
    """Nichts faellt weg - das ist der Kern des Bestandsschutzes hier."""
    assert "const _pfMehr=navItems.filter(n=>_pfHauptIds.indexOf(n.id)<0)" in rumpf, (
        "Die Mehr-Liste wird nicht aus dem Rest gebildet - dann koennte etwas "
        "durchfallen.")


def test_die_mehr_liste_zeigt_ikone_und_text(rumpf):
    i = rumpf.find("_pfMehr.map(n=>React.createElement('button'")
    assert i > 0, "Die Mehr-Liste wird nicht gerendert."
    block = rumpf[i:i + 900]
    assert "n.i" in block and "n.l" in block, (
        "Die Mehr-Eintraege tragen nicht Ikone UND Text.")


# ── 5. Der Maengel-Zaehler ────────────────────────────────────────────────

def test_der_maengel_zaehler_nimmt_die_formel_aus_projlist(rumpf):
    """Keine neue Berechnung, kein zweites Praedikat."""
    assert ('(forms&&forms.maengel||[]).filter(x=>x.pid===p.id&&'
            'x.status==="offen").length') in rumpf, (
        "Der Maengel-Zaehler rechnet anders als ProjList.")


# ── 6. Die Leisten haben Platz getauscht ──────────────────────────────────

def test_die_emoji_leiste_unten_ist_weg(rumpf):
    assert 'className: "mob-shell-nav"' not in rumpf, (
        "Die Emoji-Leiste wird noch gerendert - 13 unbeschriftete Zeichen in "
        "zwei Reihen.")


def test_die_hauptnavigation_sitzt_auf_mobil_unten(rumpf):
    i = rumpf.find('className: "tab-bar"')
    assert i > 0, "Die Hauptnavigationsleiste wurde nicht gefunden."
    assert 'className: "tab-bar"+(isMob?" pf-hauptnav":"")' in rumpf, (
        "Die Leiste traegt auf Mobil keine eigene Klasse - dann kann sie nicht "
        "nach unten wandern.")


def test_die_regel_fuer_unten_existiert_wirklich():
    """DER Riegel, den ich gebraucht haette.

    Beim Bauen habe ich die Klasse `pf-hauptnav` gesetzt und die CSS-Regel
    dazu NICHT geschrieben. Der Quelltext sah richtig aus, die Leiste stand
    weiter oben - gefunden hat es erst die Browserprobe (Mitte y=187 von 860).
    Eine Klasse ohne Regel ist eine Absicht ohne Wirkung.
    """
    roh = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    # Die ${...}-Einsetzungen VORHER entfernen. Ein naives [^}]* bricht am
    # geschweiften Klammerpaar von ${V.sb} ab und liefert eine abgeschnittene
    # Regel - der erste Anlauf dieses Riegels meldete dadurch einen Fehler,
    # den es nicht gab. Dieselbe Falle wie beim Kommentarzaehler: ein Zeichen
    # mit zwei Bedeutungen.
    ohne = re.sub(r"\$\{[^}]*\}", "X", roh)
    m = re.search(r"\.pf-hauptnav\{([^}]*)\}", ohne)
    assert m, ("Es gibt keine CSS-Regel fuer .pf-hauptnav - die Klasse waere "
               "wirkungslos.")
    regel = m.group(1)
    assert "position:fixed" in regel, "Die Leiste ist nicht fixiert: %s" % regel
    assert "bottom:0" in regel, "Die Leiste klebt nicht unten: %s" % regel
    assert "var(--epk-bar-h" in regel, (
        "Die Hoehe kommt nicht aus --epk-bar-h - dann laufen Leiste und "
        "Endreserve auseinander: %s" % regel)


# ── 7. Die zwei Abschneidefehler ──────────────────────────────────────────

def test_die_material_unterreiter_schrumpfen_nicht(rumpf):
    """Die Leiste hatte overflowX:auto UND nowrap - und war doch beschnitten.

    Ohne flexShrink:0 schrumpfen Flex-Kinder, statt ueberzulaufen. Der Text
    kann dann nicht umbrechen und wird abgeschnitten, waehrend der Rollbalken
    nie entsteht: nicht der Text sprengt seine Box, die Box wird kleiner als
    der Text.
    """
    roh = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    i = roh.find('const tabs=[{id:"warenkorb"')
    assert i > 0, "Die Material-Unterreiter wurden nicht gefunden."
    block = roh[i:i + 2600]
    assert "flexShrink:0" in block, (
        "Den Material-Unterreitern fehlt flexShrink:0.")


def test_die_summenspalte_des_wochenberichts_hat_platz():
    roh = io.open(str(WURZEL / "index.html"), encoding="utf-8", newline="").read()
    m = re.search(r"width:window\.innerWidth<600\?(\d+):", roh)
    assert m, "Die Tabellenbreite des Wochenberichts wurde nicht gefunden."
    assert int(m.group(1)) >= 700, (
        "Die Tabelle ist auf dem Handy nur %s px breit. Bei neun Spalten "
        "blieben der Summe rund 55 px, und \"18,0\" erschien als \"18.\"."
        % m.group(1))
    assert 'color:V.acTx,whiteSpace:"nowrap"' in roh, (
        "Die Summenzelle darf umbrechen - dann bricht die Zahl.")
