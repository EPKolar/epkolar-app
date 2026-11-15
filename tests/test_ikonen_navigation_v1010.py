# -*- coding: utf-8 -*-
"""v3.9.1010 - EIN Ikonen-Satz fuer die Navigation statt Emoji.

Vorher trug jeder Reiter, jeder Fussleisten-Knopf, jeder Eintrag der
Projekt-Seitenleiste und jeder Seitentitel ein Emoji. Emoji sind auf jedem
Geraet eine andere Zeichnung, haben keine Strichstaerke, nehmen die Farbe des
Umfelds nicht an (aktiv Markengruen ging also nur am Text) und werden von
Vorlesehilfen als Satz gelesen.

Jetzt: IKON (seit v3.9.934) ist die EINE Quelle, erweitert um den
Navigationssatz (Lucide, ISC). Reiter, Gruppen und Projektnavigation tragen
einen Schluessel `ik`, gezeichnet wird ueber `_ik` / `_ikT`.

Die Riegel halten die EIGENSCHAFT fest:
  * jeder Schluessel existiert in IKON (sonst zeichnet _ik ein leeres SVG -
    das waere ein unsichtbarer Knopf ohne Fehlermeldung),
  * in den Navigationslisten steht kein Emoji mehr,
  * kein Seitentitel (UI.fSeiteMob/fSeite und die isMob?18:22-Titel) beginnt
    mit einem Emoji,
  * _ik bleibt aria-hidden und currentColor,
  * der Titel einer Ansicht traegt dieselbe Ikone wie ihr Reiter.
Jeder Riegel hat eine Umkehrprobe: mit dem alten Emoji zurueck schlaegt er an.
"""
import re

import pytest

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    rumpf = code[i:j]
    return set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', rumpf))


def _liste(code, anfang, ende):
    i = code.index(anfang)
    j = code.index(ende, i)
    return code[i:j]


def _all_tabs(code):
    return _liste(code, "const _allTabs=[", "\n  ];")


def _all_nav(code):
    return _liste(code, "const _allNav=[", "];")


def _gruppen(code):
    i = code.index('[{ik:"haus",l:"Home",g:0')
    return code[i:code.index("]", i) + 1]


def _ohne_kommentare(text):
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def _ik_werte(text):
    return re.findall(r'ik:"([a-z]+)"', text)


def test_ikon_ist_die_eine_quelle_und_traegt_den_lizenzhinweis(index_html):
    sch = _ikon_schluessel(index_html)
    # die 13 Projektlisten-Ikonen von v3.9.934 sind noch da
    for alt in ["menue", "suche", "plus", "stift", "kiste", "eimer", "pfeil",
                "warnung", "bericht", "abnahme", "raster", "liste", "kreuz"]:
        assert alt in sch, "IKON hat %s verloren" % alt
    assert len(sch) >= 40, "IKON hat nur %d Eintraege" % len(sch)
    assert index_html.count("const IKON=") == 1, "zweite Ikonenquelle"
    kopf = _liste(index_html, "const IKON={", "};function _ik(")
    assert "Lucide" in kopf and "ISC" in kopf, "Lizenzhinweis fehlt"


def test_ik_bleibt_aria_hidden_und_currentcolor(index_html):
    i = index_html.index("function _ik(name,gr)")
    rumpf = index_html[i:i + 600]
    assert "'aria-hidden':\"true\"" in rumpf
    assert 'stroke:"currentColor"' in rumpf
    assert 'fill:"none"' in rumpf
    assert "strokeWidth:1.8" in rumpf


@pytest.mark.parametrize("name,schneider,mindest", [
    ("Reiter", _all_tabs, 18),
    ("Fussleiste", _gruppen, 5),
    ("Projekt-Seitenleiste", _all_nav, 13),
])
def test_navigation_traegt_ikonen_schluessel_statt_emoji(index_html, name, schneider, mindest):
    teil = _ohne_kommentare(schneider(index_html))
    werte = _ik_werte(teil)
    assert len(werte) >= mindest, "%s: nur %d ik-Schluessel" % (name, len(werte))
    fehlt = [w for w in werte if w not in _ikon_schluessel(index_html)]
    assert not fehlt, "%s: Schluessel ohne Zeichnung in IKON: %s" % (name, fehlt)
    assert not EMOJI.search(teil), "%s: Emoji in der Navigationsliste: %r" % (
        name, EMOJI.findall(teil))
    assert not re.search(r'\bi:"', teil), "%s: altes i:-Feld zurueck" % name


def test_umkehrprobe_emoji_und_unbekannter_schluessel_fallen_auf(index_html):
    teil = _ohne_kommentare(_all_tabs(index_html))
    kaputt = teil.replace('ik:"haus"', 'i:"\U0001F3E0"', 1)
    assert EMOJI.search(kaputt) and re.search(r'\bi:"', kaputt)
    falsch = teil.replace('ik:"haus"', 'ik:"gibtsnicht"', 1)
    assert "gibtsnicht" not in _ikon_schluessel(index_html)
    assert "gibtsnicht" in _ik_werte(falsch)


TITEL_RE = re.compile(
    r"fontSize:(?:window\.innerWidth<BP_MOB\?UI\.fSeiteMob:UI\.fSeite|isMob\?UI\.fSeiteMob:UI\.fSeite|isMob\?18:22)"
    r",fontWeight:800[^}]*\}(?:/\*.*?\*/)?\}\s*,\s*(.{0,60})", re.S)


def _titel_anfaenge(code):
    return [m.group(1) for m in TITEL_RE.finditer(code)]


def test_kein_seitentitel_beginnt_mit_emoji(index_html):
    anf = _titel_anfaenge(index_html)
    assert len(anf) >= 25, "nur %d Seitentitel gefunden - Muster pruefen" % len(anf)
    mit_emoji = [a for a in anf if EMOJI.search(a[:6])]
    assert not mit_emoji, "Seitentitel mit Emoji: %r" % mit_emoji
    mit_ikone = [a for a in anf if a.startswith("_ikT(") or "?_ikT(" in a]
    assert len(mit_ikone) >= 25, "nur %d Titel mit _ikT" % len(mit_ikone)


def test_umkehrprobe_titel_mit_emoji_wird_erkannt(index_html):
    kaputt = index_html.replace('_ikT("sonne","Abwesenheiten")', '"\U0001F3D6️ Abwesenheiten"', 1)
    assert kaputt != index_html
    assert [a for a in _titel_anfaenge(kaputt) if EMOJI.search(a[:6])]


@pytest.mark.parametrize("reiter,titel", [
    ("Abwesenheiten", "Abwesenheiten"),
    ("Einstellungen", "Einstellungen"),
    ("Chef", "Chef-Portal"),
    ("Mitarbeiter", "Mitarbeiter & Zuweisungen"),
    ("Arbeitsscheine", "Arbeitsscheine / Störungen"),
    ("Auswertungen", "Auswertungen & Dashboards"),
    ("Bauprovisorien", "Bauprovisorien"),
    ("Werkzeuge", "Werkzeuge & Geräte"),
    ("Gefahrenstoffe", "Gefahrenstoffe — Sicherheitsdatenblätter"),
    ("Monatsabrechnung", "Monatsabrechnung"),
    ("Fahrzeuge", "Fahrzeugverwaltung"),
    ("Admin", "Administration"),
])
def test_titel_traegt_die_ikone_seines_reiters(index_html, reiter, titel):
    m = re.search(r'\{l:"%s",ik:"([a-z]+)"' % re.escape(reiter), index_html)
    assert m, "Reiter %s ohne ik" % reiter
    assert '_ikT("%s","%s")' % (m.group(1), titel) in index_html, (
        "Titel %r traegt nicht die Ikone seines Reiters (%s)" % (titel, m.group(1)))


def test_titel_ikone_ist_aria_hidden_und_skaliert_mit_der_schrift(index_html):
    i = index_html.index("function _ikT(name,txt)")
    rumpf = index_html[i:i + 500]
    assert "'aria-hidden':\"true\"" in rumpf
    assert '_ik(name,"1em")' in rumpf
    assert "UI.markeTxt" in rumpf


def test_aktiv_ist_markengruen_in_reitern_und_mehr_menue(index_html):
    """Die Ikone erbt die Knopffarbe. Aktiv war oben und im Mehr-Menue je Reiter
    eine eigene Farbe (Home orange) - jetzt Markengruen wie die Fussleiste."""
    assert "color:_isActive?c.c:V.dm" not in index_html
    assert "color:safeKat===ri?c.c:V.tx" not in index_html
    assert "color:_isActive?V.acTx:V.dm" in index_html
    assert "color:safeKat===ri?V.acTx:V.tx" in index_html
    assert 'background:view===n.id?"rgba(249,115,22,.15)"' not in index_html
