# -*- coding: utf-8 -*-
"""v3.9.1015 - CI Display (Kiosk-Tafeln) und Stoerungsanzeige.

Die drei Wandtafeln (?screen=planung -> WochenplanTafel, ?screen=stempel ->
StempelTafel, ?screen=monteure -> MonteurTafel) trugen Emoji in Titeln,
Knoepfen und Zeilenkoepfen, feste Excel-/Terminal-Flaechen (#ffffff bzw.
#0f172a) gegen das Thema, Monospace-Ziffern und Fremdfarben (Indigo-, Amber-,
Himmelblau-Flaechen, Blau als Knopffarbe). Jetzt: Linien-Ikonen aus IKON,
Flaechen aus V/UI, gleich breite Ziffern, Markengruen als einzige Aktivfarbe.

Riegel auf die EIGENSCHAFT (jeder mit Umkehrprobe):
  * Emoji in den drei Tafeln: 0 ausser der benannten Restmenge
    (Schriftzeichen Haken/Kreuz und die Anlern-Meldung setAnlernMsg, die wie
    ein Toast ein Meldungstext ist). Gezaehlt im Code ohne Kommentare.
    Die zwei Warn-Schilder "Mitarbeiterliste nicht geladen" (v3.9.1000) und
    "Wochenplan konnte NICHT geladen werden" (v3.9.1001) bleiben samt
    Hausfarbe #B4530A und Warnzeichen - test_wand_ohne_falsche_namen_1000
    haelt das als Barrierefreiheits-Riegel fest (Text UND Farbe).
  * color-scheme-Kopplung: keine Tafel und keine Kiosk-Huelle setzt eine
    feste Seitenflaeche; die Wurzeln lesen V.bg. color-scheme selbst kommt
    weiter EINMAL vom Thema (only light / only dark, v3.9.1006) - keine Tafel
    ueberschreibt es.
  * Kiosk-Logik unberuehrt: stand (letzter ERFOLGREICHER Abruf) und jetzt
    (Uhr) sind weiter getrennt, setStand steht je Tafel genau einmal und nur
    hinter dem Erfolg, und die Zahl der Abrufwege je Tafel ist unveraendert.
  * Stoerungsanzeige auf der Tafel: Auftragstyp als Wort aus AS_ART (nicht der
    Rohwert 'stoerung'), AS_ART selbst und die Formular-Anzeige bleiben.
  * Kontrast: die neu gesetzten Paare erreichen WCAG AA in Hell UND Dunkel.
"""
import re

import pytest

from _hilfen import nur_code

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿⌀-⏿️]")
SCHRIFTZEICHEN = set("✓✕")  # Haken / Kreuz - typografisch, kein Bild-Emoji
ERLAUBT = ("setAnlernMsg('",)

TAFELN = {
    "WochenplanTafel": ("function WochenplanTafel(props){", "// Read-only Wand-Tafel"),
    "StempelTafel": ("function StempelTafel(props){", "function MonteurTafel(props){"),
    "MonteurTafel": ("function MonteurTafel(props){", "// ═══════════ MAIN APP"),
}


def _roh(code, name):
    a, e = TAFELN[name]
    i = code.index(a)
    return code[i:code.index(e, i)]


def _tafel(code, name):
    return nur_code(_roh(code, name))


def _verboten(teil):
    aus = []
    for m in EMOJI.finditer(teil):
        z = m.group()
        if z == "️" or z in SCHRIFTZEICHEN:
            continue
        anf = teil.rfind("\n", 0, m.start()) + 1
        vor = teil[max(anf, m.start() - 160):m.start()]
        if any(k in vor for k in ERLAUBT):
            continue
        aus.append(vor[-60:] + z)
    return aus


def _ikon_schluessel(code):
    i = code.index("const IKON={")
    j = code.index("};function _ik(", i)
    return set(re.findall(r'(?:[{,]|\*/)([a-z]+):\[', code[i:j]))


# ── Emoji ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", sorted(TAFELN))
def test_kein_emoji_auf_den_tafeln(index_html, name):
    verb = _verboten(_tafel(index_html, name))
    assert not verb, "%s: Emoji ausserhalb der Restmenge:\n%s" % (
        name, "\n".join(repr(v) for v in verb))


def test_restmenge_ist_benannt_und_klein(index_html):
    st = _tafel(index_html, "StempelTafel")
    treffer = [m.group() for m in EMOJI.finditer(st)
               if m.group() not in SCHRIFTZEICHEN and m.group() != "️"]
    # genau EIN Warnzeichen in der Anlern-Meldung
    assert treffer == ["⚠"], treffer
    assert "setAnlernMsg('⚠ UID bereits vergeben an '" in st


def test_umkehrprobe_emoji_wird_erkannt(index_html):
    t = _tafel(index_html, "MonteurTafel")
    kaputt = t.replace('"Monteur-Tafel"', '"\U0001F4CB Monteur-Tafel"', 1)
    assert kaputt != t
    assert _verboten(kaputt), "Ein eingesetztes Emoji im Titel faellt nicht auf"
    knopf = t.replace("\"Abmelden\"):null", "\"⎋ Abmelden\"):null", 1)
    assert knopf != t and _verboten(knopf)


@pytest.mark.parametrize("name", sorted(TAFELN))
def test_jede_tafel_ikone_hat_eine_zeichnung(index_html, name):
    t = _tafel(index_html, name)
    namen = set(re.findall(r"_ik\('([a-z]+)'", t)) | set(re.findall(r"_tfEt\('([a-z]+)'", t))
    namen |= set(re.findall(r"_absRow\('[^']+',_[a-zA-Z]+,'([a-z]+)'\)", t))
    assert namen, "%s: keine Ikone gefunden - Bereich falsch abgegrenzt?" % name
    fehlt = sorted(namen - _ikon_schluessel(index_html))
    assert not fehlt, "%s: Ikone ohne Zeichnung (leeres SVG): %s" % (name, fehlt)


def test_umkehrprobe_unbekannte_ikone(index_html):
    assert "gibtsnicht" not in _ikon_schluessel(index_html)
    t = _tafel(index_html, "WochenplanTafel").replace("_ik('vollbild',18)", "_ik('gibtsnicht',18)", 1)
    assert "gibtsnicht" in set(re.findall(r"_ik\('([a-z]+)'", t))


# ── Farben / color-scheme ─────────────────────────────────────────────────

FESTE_FLAECHEN = ("'#ffffff'", "\"#ffffff\"", "#0f172a", "#111827", "#1f2937",
                  "#eef2ff", "#fffbeb", "#b45309", "#1e293b", "rgba(255,255,255,")
FREMD = ("#0ea5e9", "COLORS.INFO", "COLORS.SUCCESS", "COLORS.WARNING",
         "COLORS.ERROR", "COLORS.EP_GREEN", "#f59e0b", "fontFamily:mono")


@pytest.mark.parametrize("name", sorted(TAFELN))
def test_keine_feste_flaeche_und_keine_fremdfarbe(index_html, name):
    t = _tafel(index_html, name)
    gef = [f for f in FESTE_FLAECHEN + FREMD if f in t]
    assert not gef, "%s: feste Flaeche/Fremdfarbe zurueck: %s" % (name, gef)


def test_wurzeln_und_huellen_folgen_dem_thema(index_html):
    wp = _tafel(index_html, "WochenplanTafel")
    assert "height:'100vh',width:'100vw',background:V.bg,color:V.tx" in wp
    mt = _tafel(index_html, "MonteurTafel")
    assert "height:'100vh',width:'100vw',background:V.bg,color:V.tx" in mt
    st = _tafel(index_html, "StempelTafel")
    assert st.count("background:V.bg,color:V.tx,") == 2  # Bereit-Schirm + Antragsrahmen
    code = nur_code(index_html)
    for tafel in ("StempelTafel", "WochenplanTafel"):
        m = re.search(r"overflow:\"hidden\",background:([^}]+)}},React\.createElement\('style',\{\},GCSS\(\)\),React\.createElement\(" + tafel, code)
        assert m, "Kiosk-Huelle fuer %s nicht gefunden" % tafel
        assert m.group(1) == "V.bg", "Huelle %s traegt feste Flaeche %s" % (tafel, m.group(1))


def test_color_scheme_kommt_einmal_vom_thema(index_html):
    code = nur_code(index_html)
    assert 'document.documentElement.style.colorScheme=dark?"only dark":"only light";' in code
    for name in TAFELN:
        t = _tafel(index_html, name)
        assert "colorScheme" not in t and "color-scheme" not in t, (
            "%s setzt ein eigenes color-scheme - dann stuende die Tafel wieder "
            "gegen das Thema" % name)


def test_umkehrprobe_feste_flaeche(index_html):
    t = _tafel(index_html, "WochenplanTafel").replace("background:V.bg,color:V.tx", "background:'#ffffff',color:'#111827'", 1)
    assert any(f in t for f in FESTE_FLAECHEN)


def test_logo_schild_auf_allen_tafeln(index_html):
    code = nur_code(index_html)
    i = code.index("function _kioskLogo(")
    rumpf = code[i:i + 400]
    assert "src:LOGO_SM" in rumpf and 'padding:_dark?"3px 6px":0' in rumpf
    for name in TAFELN:
        assert "_kioskLogo(" in _tafel(index_html, name), "%s ohne Logo" % name


def test_rot_nur_fuer_abmelden_und_gefahr(index_html):
    code = nur_code(index_html)
    i = code.index("function _kioskKnopf(")
    rumpf = code[i:i + 500]
    assert 'art==="gefahr"?UI.fehler:V.bdK' in rumpf
    for name in ("WochenplanTafel", "MonteurTafel"):
        t = _tafel(index_html, name)
        assert "_kioskKnopf('gefahr')" in t and "\"Abmelden\"" in t
        assert t.count("_kioskKnopf('gefahr')") == 1, "%s: Gefahr-Knopf ausser Abmelden" % name


# ── Kiosk-Logik bleibt ────────────────────────────────────────────────────

ABRUFWEGE = {  # gezaehlt an der Basis v3.9.1013 - ein neuer Weg waere Logik, keine Darstellung
    "WochenplanTafel": {"fetch(": 1},
    "StempelTafel": {"fetch(": 3},
    "MonteurTafel": {"fetch(": 0, "API.request(": 1, "_kioskWeekArbeitsscheine()": 1},
}


@pytest.mark.parametrize("name", ["WochenplanTafel", "MonteurTafel"])
def test_stand_und_jetzt_bleiben_getrennt(index_html, name):
    t = _tafel(index_html, name)
    assert "const [jetzt,setJetzt]=_react.useState.call(void 0, Date.now());" in t
    assert "setJetzt(Date.now())" in t
    assert t.count("setStand(new Date())") == 1, (
        "%s: setStand %d-mal - der Stand darf sich nur nach einem erfolgreichen "
        "Abruf bewegen" % (name, t.count("setStand(new Date())")))
    if name == "WochenplanTafel":
        assert "if(alive&&Array.isArray(j)){setAbsRows(j);setStand(new Date());" in t
        assert "_wpTafelAlter(stand,jetzt)" in t
    else:
        i_pruef = t.index("if(Array.isArray(raw)){")
        assert i_pruef < t.index("setStand(new Date())")
        assert "Math.max(0,jetzt-stand.getTime())" in t


@pytest.mark.parametrize("name", sorted(TAFELN))
def test_kein_neuer_abrufweg(index_html, name):
    t = _tafel(index_html, name)
    for k, soll in ABRUFWEGE[name].items():
        assert t.count(k) == soll, "%s: %s %d-mal statt %d" % (name, k, t.count(k), soll)


def test_umkehrprobe_stand_ohne_erfolg_faellt_auf(index_html):
    t = _tafel(index_html, "MonteurTafel")
    kaputt = t.replace("setJetzt(Date.now()); (async", "setJetzt(Date.now());setStand(new Date()); (async", 1)
    assert kaputt != t and kaputt.count("setStand(new Date())") == 2


def test_kiosk_eingabefelder_regel_unberuehrt(index_html):
    # Das 14-px-!important an Kiosk-Inputs ist ein eigener Befund - hier nicht angefasst.
    assert "html[data-kiosk]" in index_html


# ── Stoerungsanzeige ──────────────────────────────────────────────────────

def test_tafel_zeigt_auftragstyp_als_wort(index_html):
    t = _tafel(index_html, "MonteurTafel")
    assert "const meta=[a.scheinart,a.prioritaet]" not in t, "Rohwert 'stoerung' steht wieder auf der Tafel"
    assert "AS_ART[a.scheinart].l" in t
    assert "a.scheinart!=='kein'" in t
    # Stoerung hebt sich durch Gewicht und volle Textfarbe ab - nicht durch Farbe allein.
    assert "_istSt=a.scheinart==='stoerung'" in t and "color:_istSt?V.tx:V.mt,fontWeight:_istSt?700:400" in t


def test_as_art_und_formular_bleiben(index_html):
    # Datenkarte und Formular-Anzeige sind Vertrag (test_scheinart_push_v797,
    # test_as_formular_kein_dropdown_v803) und liegen neben _asEskalierbar.
    assert 'const AS_ART={kein:{l:"kein",i:"—"},stoerung:{l:"Störung",i:"⚡"}' in index_html
    assert '(AS_ART[form.scheinart]?(AS_ART[form.scheinart].i+" "+AS_ART[form.scheinart].l):"—")' in index_html


# ── Kontrast (WCAG 2.1) ───────────────────────────────────────────────────

def _lum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _kr(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


HELL = {"bg": "#F2F4F2", "cd": "#FFFFFF", "tx": "#141A16", "dm": "#5B6660", "mt": "#646E68", "bdK": "#7F8983",
        "neutralBg": "#EEF1EF", "markeTxt": "#00722F", "acTx": "#006e30", "fehler": "#B91C1C"}
DUNKEL = {"bg": "#121513", "cd": "#1E2320", "tx": "#EEF1EF", "dm": "#B3BCB6", "mt": "#949D97", "bdK": "#6E7872",
          "neutralBg": "#2A302C", "markeTxt": "#00B050", "acTx": "#00b050", "fehler": "#FF6B6B"}
ROLLE = {"hell": ["#dc2626", "#2563eb", "#15803d", "#c2410c"], "dunkel": ["#f87171", "#60a5fa", "#4ade80", "#fb923c"]}


def test_token_werte_stimmen_mit_der_quelle(index_html):
    for k, v in (("bg", "#F2F4F2"), ("bdK", "#7F8983"), ("mt", "#646E68")):
        assert '%s:"%s"' % (k, v) in index_html
    for k, v in (("bg", "#121513"), ("bdK", "#6E7872"), ("mt", "#949D97")):
        assert '%s:"%s"' % (k, v) in index_html
    i = index_html.index("function _kioskRolle(")
    rumpf = index_html[i:i + 400]
    for h, d in zip(ROLLE["hell"], ROLLE["dunkel"]):
        assert "(d?'%s':'%s')" % (d, h) in rumpf


@pytest.mark.parametrize("thema,T", [("hell", HELL), ("dunkel", DUNKEL)])
def test_kontrast_text(thema, T):
    paare = [  # (Vordergrund, Hintergrund, Schwelle, Bedeutung)
        (T["tx"], T["cd"], 4.5, "Name/Text auf Karte"),
        (T["tx"], T["neutralBg"], 4.5, "Name-Chip / Etikett"),
        (T["dm"], T["neutralBg"], 4.5, "Kennzeichen-Chip"),
        (T["dm"], T["cd"], 4.5, "Meta auf Karte"),
        (T["mt"], T["cd"], 4.5, "Fusszeile read-only"),
        (T["dm"], T["bg"], 4.5, "Datumszeile auf Seite"),
        (T["fehler"], T["cd"], 4.5, "Abmelden-Knopf"),
        (T["acTx"], T["cd"], 4.5, "naechste-Woche-Abzeichen"),
        ("#FFFFFF", "#00843A", 4.5, "Weiss auf UI.knopf (aktiv/primaer)"),
        ("#FFFFFF", "#B4530A", 4.5, "Stempel GEHEN"),
        ("#FFFFFF", "#B91C1C", 4.5, "Stempel Fehler / ueberfaellig"),
        ("#FFFFFF", "#414B45", 4.5, "Stempel Doppel-Scan"),
    ]
    for r in ROLLE[thema]:
        paare.append((r, T["bg"], 3.0, "Rollenname 22px fett auf Seite"))
        paare.append((r, T["cd"], 4.5, "Rollenname 16px fett im Tag-Kopf (Karte) - keine Grossschrift"))
    schlecht = ["%s %.2f < %.1f (%s auf %s)" % (b, _kr(v, h), s, v, h) for v, h, s, b in paare if _kr(v, h) < s]
    assert not schlecht, thema + ":\n" + "\n".join(schlecht)


@pytest.mark.parametrize("thema,T", [("hell", HELL), ("dunkel", DUNKEL)])
def test_kontrast_kontur(thema, T):
    assert _kr(T["bdK"], T["cd"]) >= 3.0 and _kr(T["bdK"], T["bg"]) >= 3.0


def test_umkehrprobe_kontrast():
    assert _kr("#FFFFFF", "#22c55e") < 4.5  # das alte KOMMEN-Gruen
    assert _kr("#FFFFFF", "#f97316") < 4.5  # das alte GEHEN-Orange
    assert _kr("#FFFFFF", "#eab308") < 4.5  # Weiss auf Status gelb (alte Tag-Plakette)
